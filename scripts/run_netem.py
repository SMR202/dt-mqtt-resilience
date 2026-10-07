"""Real Linux packet impairment in a disposable network namespace/container.

Requires --network none, NET_ADMIN and NET_RAW; never modify host qdiscs.
The same edge queue and real-MQTT implementation are used. Event-integral AoI
is calculated separately because synchronous QoS waits affect sample cadence.
"""
import csv
import gzip
import importlib.metadata
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from live import start_broker,run
def main():
    if os.environ.get('DT_PRIVATE_NETNS')!='1': raise RuntimeError('Run only inside the documented isolated Docker network namespace')
    out=ROOT/'results/linux_netem'
    out.mkdir(exist_ok=False);(out/'queues').mkdir()
    cfg={'devices':4,'rate':5,'duration':6,'warmup':1,'seeds':[0,1,2],'qos':[0,1,2],'policies':['fifo','latest'],'scenarios':{name:{'capacity':12,'delay':0,'jitter':0,'outage':None} for name in ['healthy','delay_loss']}}
    (out/'config.json').write_text(json.dumps(cfg,indent=2))
    design=[(seed,qos,pol,s) for seed in cfg['seeds'] for qos in cfg['qos'] for pol in cfg['policies'] for s in cfg['scenarios']]
    random.Random(20261007).shuffle(design);(out/'order.json').write_text(json.dumps(design))
    broker,log=start_broker(out);rows=[];failures=[];capture=None
    try:
        capture=subprocess.Popen(['tcpdump','-U','-i','lo','-w',str(out/'mqtt.pcap'),'tcp','port','18884'],stdout=subprocess.DEVNULL,stderr=(out/'capture.txt').open('w'))
        with gzip.open(out/'events.csv.gz','wt',newline='') as f:
            writer=csv.writer(f);writer.writerow(['run','event','time','device','seq','generated','value','accepted'])
            for seed,qos,pol,scenario in design:
                subprocess.run(['tc','qdisc','del','dev','lo','root'],capture_output=True)
                if scenario=='delay_loss': subprocess.run(['tc','qdisc','add','dev','lo','root','netem','delay','100ms','20ms','loss','2%','seed',str(seed+1)],check=True)
                try:
                    r=run(cfg,seed,qos,pol,scenario,out,broker,writer);rows.append(r)
                except Exception as e: failures.append({'seed':seed,'qos':qos,'policy':pol,'scenario':scenario,'error':repr(e)})
                stats=subprocess.check_output(['tc','-s','qdisc','show','dev','lo'],text=True)
                with (out/'qdisc.txt').open('a') as q:q.write(f'{scenario}-{pol}-q{qos}-s{seed}\n{stats}\n')
                if rows:
                    with (out/'runs.csv').open('w',newline='') as g:
                        w=csv.DictWriter(g,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
                (out/'failures.json').write_text(json.dumps(failures,indent=2))
                print(len(rows)+len(failures),'/',len(design),scenario,pol,'QoS',qos,flush=True)
    finally:
        subprocess.run(['tc','qdisc','del','dev','lo','root'],capture_output=True)
        if capture: capture.terminate();capture.wait(timeout=10)
        broker.terminate();broker.wait(timeout=10);log.close()
    versions={x:importlib.metadata.version(x) for x in ['paho-mqtt','amqtt','numpy','pandas','matplotlib','psutil']}
    (out/'environment.json').write_text(json.dumps({'platform':platform.platform(),'python':sys.version,'versions':versions,'executed_runs':len(rows),'failed_runs':len(failures),'label':'actual Linux tc/netem loopback TCP packet delay/loss; isolated Docker namespace; not a real WAN'},indent=2))
    for db in (out/'queues').glob('*.sqlite'):
        with db.open('rb') as s,gzip.open(str(db)+'.gz','wb') as d:shutil.copyfileobj(s,d)
        db.unlink()
    with (out/'mqtt.pcap').open('rb') as s,gzip.open(out/'mqtt.pcap.gz','wb') as d:shutil.copyfileobj(s,d)
    (out/'mqtt.pcap').unlink()
    print('Completed',len(rows),'successful runs;',len(failures),'failures retained')
if __name__=='__main__': main()
