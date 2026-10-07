"""Receive UTC-stamped research telemetry through a local SSH-forwarded broker.

Use a unique run ID per session. Cloud/edge clocks must be checked separately;
UTC differences are raw observations, not verified one-way latency/AoI.
"""
import argparse
import json
import sqlite3
import time
import signal
import platform
import sys
from pathlib import Path
import paho.mqtt.client as mqtt
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=18886);a=p.parse_args()
    if a.output.exists(): raise RuntimeError('Use a fresh receiver database')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(a.output,check_same_thread=False)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE received(device INTEGER,seq INTEGER,generated_utc REAL,received_utc REAL,accepted INTEGER,payload TEXT,UNIQUE(device,seq))')
    latest={};counts={'callbacks':0,'accepted':0,'rejected':0};cpu0=time.process_time();started=time.time()
    def connected(c,u,f,r,pr):
        if r.is_failure: raise RuntimeError(str(r))
        c.subscribe('research/'+a.run,qos=2)
    def incoming(c,u,m):
        v=json.loads(m.payload);d=int(v['device']);seq=int(v['seq']);at=time.time()
        if v['run']!=a.run:return
        accepted=seq>latest.get(d,-1)
        counts['callbacks']+=1;counts['accepted' if accepted else 'rejected']+=1
        with db:db.execute('INSERT OR IGNORE INTO received VALUES (?,?,?,?,?,?)',(d,seq,v['generated_utc'],at,int(accepted),json.dumps(v)))
        if accepted:latest[d]=seq
        print(json.dumps({'device':d,'seq':seq,'accepted':accepted,'raw_clock_difference_seconds':at-v['generated_utc']}),flush=True)
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2);c.on_connect=connected;c.on_message=incoming
    c.on_subscribe=lambda *args:print('SUBSCRIBED',flush=True)
    c.connect('127.0.0.1',a.port);c.loop_start()
    def stopping(signum,frame):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stopping)
    try:
        while True:time.sleep(1)
    except KeyboardInterrupt:pass
    finally:
        c.disconnect();c.loop_stop();db.close()
        try:
            import resource
            rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        except ImportError:rss=None
        a.output.with_suffix('.metrics.json').write_text(json.dumps({'run':a.run,'cpu_seconds':time.process_time()-cpu0,'peak_rss_bytes':rss,'started_utc':started,'ended_utc':time.time(),'platform':platform.platform(),'python':sys.version,'counts':counts},indent=2))
if __name__=='__main__':main()
