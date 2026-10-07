"""Same FIFO/latest outbox on a real WAN; optional USB physical sensor input."""
import argparse
import json
import math
import sys
import time
from pathlib import Path
import paho.mqtt.client as mqtt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.policies import EdgeQueue
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--policy',choices=['fifo','latest'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=18885);p.add_argument('--qos',type=int,choices=[0,1,2],default=1);p.add_argument('--duration',type=float,default=60);p.add_argument('--serial-port');p.add_argument('--outage-start',type=float,default=20);p.add_argument('--outage-end',type=float,default=30);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Use a fresh output directory and unique run ID')
    a.output.mkdir(parents=True);db=EdgeQueue(a.output/'edge.sqlite',a.policy)
    serial=None
    if a.serial_port:
        import serial as serial_module
        serial=serial_module.Serial(a.serial_port,115200,timeout=.01)
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2);c.connect('127.0.0.1',a.port);c.loop_start()
    seq={d:0 for d in range(4)};start=time.monotonic();next_generate=0;sent=0;failures=[]
    metadata={'mode':'USB physical sensor' if serial else 'synthetic real-WAN workload','physical_capture_age_verified':False,'clock_sync_verified':False,'outage':'edge application withholding; not WAN packet blackout','args':vars(a)|{'output':str(a.output)},'started_utc':time.time()}
    try:
        while time.monotonic()-start<a.duration:
            now=time.monotonic()-start;messages=[]
            if serial and serial.in_waiting:
                try:
                    reading=json.loads(serial.readline());messages=[(0,float(reading['temperature_c']),reading)]
                except (ValueError,KeyError):continue
            elif not serial and now>=next_generate:
                messages=[(d,math.sin(.3*now+d),{}) for d in range(4)];next_generate=now+.2
            for d,value,raw in messages:
                seq[d]+=1;utc=time.time();db.enqueue({'run':a.run,'device':d,'seq':seq[d],'generated':utc,'generated_utc':utc,'value':value,'source':raw,'timestamp_semantics':'PC USB arrival' if serial else 'PC generation'})
            if not a.outage_start<=now<a.outage_end:
                row=db.peek(time.time())
                if row:
                    rid,m=row;info=c.publish('research/'+a.run,json.dumps(m),qos=a.qos)
                    info.wait_for_publish(timeout=5)
                    if info.is_published():db.acknowledge(rid);db.served(m['device']);sent+=1
                    else:failures.append({'time':now,'reason':'publisher acceptance timeout'});break
            time.sleep(.002)
    finally:
        metadata.update({'generated':db.audit_count(),'published':sent,'remaining':db.size(),'failures':failures,'ended_utc':time.time()})
        (a.output/'summary.json').write_text(json.dumps(metadata,indent=2));c.disconnect();c.loop_stop();db.close()
        if serial:serial.close()
if __name__=='__main__':main()
