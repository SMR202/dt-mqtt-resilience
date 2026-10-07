"""Receive UTC-stamped research telemetry through a local SSH-forwarded broker.

Use a unique run ID per session. Cloud/edge clocks must be checked separately;
UTC differences are raw observations, not verified one-way latency/AoI.
"""
import argparse
import json
import sqlite3
import time
from pathlib import Path
import paho.mqtt.client as mqtt
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=18886);a=p.parse_args()
    if a.output.exists(): raise RuntimeError('Use a fresh receiver database')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(a.output,check_same_thread=False)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE received(device INTEGER,seq INTEGER,generated_utc REAL,received_utc REAL,accepted INTEGER,payload TEXT,UNIQUE(device,seq))')
    latest={}
    def connected(c,u,f,r,pr):
        if r.is_failure: raise RuntimeError(str(r))
        c.subscribe('research/'+a.run,qos=2)
    def incoming(c,u,m):
        v=json.loads(m.payload);d=int(v['device']);seq=int(v['seq']);at=time.time()
        if v['run']!=a.run:return
        accepted=seq>latest.get(d,-1)
        with db:db.execute('INSERT OR IGNORE INTO received VALUES (?,?,?,?,?,?)',(d,seq,v['generated_utc'],at,int(accepted),json.dumps(v)))
        if accepted:latest[d]=seq
        print(json.dumps({'device':d,'seq':seq,'accepted':accepted,'raw_clock_difference_seconds':at-v['generated_utc']}),flush=True)
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2);c.on_connect=connected;c.on_message=incoming
    c.on_subscribe=lambda *args:print('SUBSCRIBED',flush=True)
    c.connect('127.0.0.1',a.port);c.loop_start()
    try:
        while True:time.sleep(1)
    except KeyboardInterrupt:pass
    finally:c.disconnect();c.loop_stop();db.close()
if __name__=='__main__':main()
