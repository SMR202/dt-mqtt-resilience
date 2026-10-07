"""Actual MQTT 3.1.1 loopback evaluation with application-controlled uplink.

This delays submissions at the edge, not TCP packets; it never maps MQTT QoS 0
to arbitrary packet loss. All transport failures cause the run to fail.
"""
import argparse
import csv
import gzip
import importlib.metadata
import json
import math
import os
import platform
import random
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import psutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.policies import EdgeQueue, TwinState


def start_broker(out):
    # Never reuse a pre-existing service on this port.
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',18884)) == 0:
            raise RuntimeError('Research broker port 18884 already occupied')
    logfile=(out/'broker.log').open('w')
    proc=subprocess.Popen([sys.executable,str(ROOT/'scripts/broker.py')],stdout=logfile,stderr=subprocess.STDOUT)
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError('Broker exited; inspect broker.log')
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1',18884)) == 0:
                return proc,logfile
        time.sleep(.1)
    proc.terminate()
    raise RuntimeError('Broker startup timed out')


def run(cfg,seed,qos,policy,scenario,out,broker,writer):
    identifier=f'{scenario}-{policy}-q{qos}-s{seed}'
    db=EdgeQueue(out/'queues'/f'{identifier}.sqlite',policy)
    if db.audit_count():
        raise RuntimeError('Existing queue artifact; use a fresh output directory')
    twin=TwinState(cfg['devices'])
    received, samples, latencies, seen = [],[],[],set()
    pending=[]
    lock=threading.Lock()
    subscribed=threading.Event()
    topic='research/'+identifier
    start=[None]

    def on_connect(client,userdata,flags,reason,properties):
        if reason.is_failure:
            return
        client.subscribe(topic,qos=qos)

    def on_subscribe(client,userdata,mid,reason_codes,properties):
        if any(r.is_failure for r in reason_codes):
            return
        subscribed.set()

    def on_message(client,userdata,msg):
        m=json.loads(msg.payload)
        at=time.perf_counter()-start[0]
        with lock:
            accepted=twin.accept(m)
            received.append((at,m,accepted))
            seen.add((m['device'],m['seq']))
            latencies.append(at-m['generated'])

    sub=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='sub-'+identifier,protocol=mqtt.MQTTv311)
    sub.on_connect,sub.on_message,sub.on_subscribe=on_connect,on_message,on_subscribe
    sub.connect('127.0.0.1',18884)
    sub.loop_start()
    if not subscribed.wait(5):
        raise RuntimeError('Subscription was not acknowledged')
    pub=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='pub-'+identifier,protocol=mqtt.MQTTv311)
    pub.connect('127.0.0.1',18884)
    pub.loop_start()
    process=psutil.Process()
    cpu0=time.process_time()
    generated=sent=payload_bytes=0
    qmax=0
    max_rss=max_broker_rss=0
    s=cfg['scenarios'][scenario]
    duration=cfg['duration']
    next_generate=next_send=next_sample=0.
    seqs=[0]*cfg['devices']
    start[0]=time.perf_counter()
    recovery=None
    inflight=[]
    try:
        while (now:=time.perf_counter()-start[0]) < duration:
            outage=s['outage'] and s['outage'][0]<=now<s['outage'][1]
            while next_generate <= now:
                if policy=='no_buffer':
                    # Retain at most the current sampling epoch in RAM-like
                    # transient staging; never replay prior epochs.
                    db.discard_outbox()
                epoch=int(round(next_generate*cfg['rate']))
                order=[(epoch+i)%cfg['devices'] for i in range(cfg['devices'])]
                for d in order:
                    m={'device':d,'seq':seqs[d],'generated':next_generate,'value':math.sin(next_generate*.3+d)}
                    seqs[d]+=1
                    generated+=1
                    db.enqueue(m)
                    writer.writerow([identifier,'generate',next_generate,d,m['seq'],next_generate,m['value'],1])
                next_generate += 1/cfg['rate']
            qmax=max(qmax,db.size())
            if not outage and now >= next_send:
                row=db.peek(now,exclude=[r for _,r,_ in pending])
                if row:
                    row_id,m=row
                    delay=max(0.,s['delay']+random.Random(seed*100000000+m['device']*100000+m['seq']).uniform(-s['jitter'],s['jitter']))
                    pending.append((now+delay,row_id,m))
                    db.served(m['device'])
                next_send=now+1/s['capacity']
            if outage:
                # This test disconnects the modeled uplink, not the broker process.
                next_send=now
            if policy=='no_buffer' and outage:
                db.discard_outbox()
            for ready,row_id,m in list(pending):
                if ready <= now:
                    payload=json.dumps(m,separators=(',',':'))
                    info=pub.publish(topic,payload,qos=qos)
                    if info.rc != mqtt.MQTT_ERR_SUCCESS:
                        raise RuntimeError('MQTT publish rejected')
                    info.wait_for_publish(timeout=5)
                    if not info.is_published():
                        raise RuntimeError('MQTT transport acceptance timeout')
                    db.acknowledge(row_id)
                    inflight.append(info)
                    sent+=1
                    payload_bytes+=len(payload.encode())
                    pending.remove((ready,row_id,m))
            if now>=next_sample:
                with lock:
                    ages=[max(0.,now-v['generated']) for v in twin.states.values()]
                    errors=[abs(math.sin(now*.3+d)-twin.states[d]['value']) for d in range(cfg['devices'])]
                if now>=cfg['warmup']:
                    samples.extend((a,e) for a,e in zip(ages,errors))
                if s['outage'] and now>=s['outage'][1] and recovery is None and max(ages)<=1.:
                    recovery=now-s['outage'][1]
                next_sample=now+.02
                max_rss=max(max_rss,process.memory_info().rss)
                max_broker_rss=max(max_broker_rss,psutil.Process(broker.pid).memory_info().rss)
            time.sleep(.001)
        measured=time.perf_counter()-start[0]
        cpu=time.process_time()-cpu0
        # Allow already-published packets to finish; never drain unsent outbox.
        for info in inflight:
            info.wait_for_publish(timeout=5)
            if not info.is_published():
                raise RuntimeError('MQTT publish acknowledgement timeout')
        deadline=time.perf_counter()+2
        while len(received)<sent and time.perf_counter()<deadline:
            time.sleep(.005)
        with lock:
            events=list(received)
        for at,m,accepted in events:
            writer.writerow([identifier,'receive',at,m['device'],m['seq'],m['generated'],m['value'],int(accepted)])
        ages=sorted(a for a,e in samples)
        result=dict(run=identifier,scenario=scenario,policy=policy,qos=qos,seed=seed,
            devices=cfg['devices'],rate=cfg['rate'],generated=generated,sent=sent,delivered=len(events),
            delivery_ratio=len(seen)/generated,mean_aoi=sum(ages)/len(ages),p95_aoi=ages[int(.95*(len(ages)-1))],
            stale_fraction=sum(a>1 for a in ages)/len(ages),mae=sum(e for a,e in samples)/len(samples),
            mean_latency=sum(latencies)/len(latencies) if latencies else None,
            duplicates=len(events)-len(seen),rejections=twin.rejections,regressions=twin.regressions,
            max_queue=qmax,remaining=db.size()+len(pending),coalesced=db.coalesced,
            audit_count=db.audit_count(),payload_bytes=payload_bytes,
            recovery_seconds=recovery,wall_seconds=measured,cpu_seconds=cpu,
            peak_runner_rss_bytes=max_rss,peak_broker_rss_bytes=max_broker_rss)
        if result['delivered']!=sent:
            raise RuntimeError(f'MQTT delivery mismatch {result}')
        return result
    finally:
        pub.disconnect();pub.loop_stop()
        sub.disconnect();sub.loop_stop()
        db.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',default='configs/live.json')
    p.add_argument('--output',default='results/live')
    args=p.parse_args()
    cfg=json.loads((ROOT/args.config).read_text())
    out=ROOT/args.output
    (out/'queues').mkdir(parents=True,exist_ok=True)
    broker,log=start_broker(out)
    rows=[]
    try:
        with gzip.open(out/'events.csv.gz','wt',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['run','event','time','device','seq','generated','value','accepted'])
            # Randomize run order, save it, and pair identical workloads/seeds.
            design=[(seed,qos,policy,scenario) for seed in cfg['seeds'] for qos in cfg['qos'] for policy in cfg['policies'] for scenario in cfg['scenarios']]
            random.Random(20261007).shuffle(design)
            (out/'order.json').write_text(json.dumps(design,indent=2))
            for seed,qos,policy,scenario in design:
                r=run(cfg,seed,qos,policy,scenario,out,broker,writer)
                rows.append(r)
                with (out/'runs.csv').open('w',newline='') as g:
                    w=csv.DictWriter(g,fieldnames=list(r));w.writeheader();w.writerows(rows)
                print(len(rows),'/',len(design),r['run'],'AoI',round(r['mean_aoi'],3),'delivery',round(r['delivery_ratio'],3),flush=True)
    finally:
        broker.terminate();broker.wait(timeout=10);log.close()
    versions={x:importlib.metadata.version(x) for x in ['paho-mqtt','amqtt','numpy','pandas','matplotlib','psutil']}
    (out/'config.json').write_text(json.dumps(cfg,indent=2))
    (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),
        'cpu':platform.processor(),'logical_cpus':psutil.cpu_count(),'physical_cpus':psutil.cpu_count(logical=False),
        'ram_bytes':psutil.virtual_memory().total,'versions':versions,
        'label':'real MQTT loopback, application-shaped uplink; not cloud WAN or packet loss'},indent=2))
    # Databases are raw durability evidence; compress after closing them.
    for db in (out/'queues').glob('*.sqlite'):
        with db.open('rb') as source,gzip.open(str(db)+'.gz','wb') as dest:
            import shutil
            shutil.copyfileobj(source,dest)
        db.unlink()


if __name__=='__main__':
    main()
