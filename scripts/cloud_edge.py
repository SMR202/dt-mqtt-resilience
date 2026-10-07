"""Same FIFO/latest outbox on a real WAN; optional USB physical sensor input."""
import argparse
import json
import math
import sys
import time
import threading
import psutil
from pathlib import Path
import paho.mqtt.client as mqtt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.policies import EdgeQueue
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--policy',choices=['fifo','latest'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=18885);p.add_argument('--qos',type=int,choices=[0,1,2],default=1);p.add_argument('--duration',type=float,default=60);p.add_argument('--serial-port');p.add_argument('--outage-start',type=float,default=20);p.add_argument('--outage-end',type=float,default=30);p.add_argument('--dispatch-cap',type=float,default=12);p.add_argument('--seed',type=int,default=0);a=p.parse_args()
    if a.output.exists():raise RuntimeError('Use a fresh output directory and unique run ID')
    a.output.mkdir(parents=True);db=EdgeQueue(a.output/'edge.sqlite',a.policy)
    serial=None
    if a.serial_port:
        import serial as serial_module
        serial=serial_module.Serial(a.serial_port,115200,timeout=.01)
    connected=threading.Event();connections=[]
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='edge-'+a.run)
    def on_connect(c,u,f,r,pr):
        connections.append({'event':'connect','utc':time.time(),'reason':str(r)})
        if not r.is_failure:connected.set()
    def on_disconnect(c,u,f,r,pr):connections.append({'event':'disconnect','utc':time.time(),'reason':str(r)})
    c.on_connect=on_connect;c.on_disconnect=on_disconnect
    c.connect('127.0.0.1',a.port);c.loop_start()
    if not connected.wait(10):raise RuntimeError('MQTT connection not established')
    seq={d:0 for d in range(4)};start=time.monotonic();next_generate=0;sent=0;failures=[];pending=None;next_send=0;max_queue=0;published=[];cpu0=time.process_time();peak_rss=0
    metadata={'mode':'USB physical sensor' if serial else 'synthetic real-WAN workload','physical_capture_age_verified':False,'clock_sync_verified':False,'outage':'edge application withholding; not WAN packet blackout','args':vars(a)|{'output':str(a.output)},'started_utc':time.time()}
    origin=a.output/'start.tmp'
    origin.write_text(json.dumps({'started_utc':metadata['started_utc']}))
    origin.replace(a.output/'start.json')
    try:
        while time.monotonic()-start<a.duration:
            now=time.monotonic()-start;messages=[]
            if serial and serial.in_waiting:
                try:
                    reading=json.loads(serial.readline());messages=[(0,float(reading['temperature_c']),reading)]
                except (ValueError,KeyError):continue
            elif not serial and now>=next_generate:
                order=[(i+sum(seq.values())//4+a.seed)%4 for i in range(4)]
                messages=[(d,math.sin(.3*now+d),{}) for d in order];next_generate=now+.2
            for d,value,raw in messages:
                seq[d]+=1;utc=time.time();db.enqueue({'run':a.run,'device':d,'seq':seq[d],'generated':utc,'generated_utc':utc,'value':value,'source':raw,'timestamp_semantics':'PC USB arrival' if serial else 'PC generation'})
            max_queue=max(max_queue,db.size())
            peak_rss=max(peak_rss,psutil.Process().memory_info().rss)
            if pending:
                rid,m,info,submitted=pending
                if info.is_published():
                    db.acknowledge(rid);db.served(m['device']);sent+=1;published.append({'device':m['device'],'seq':m['seq'],'submitted_utc':submitted,'publication_complete_utc':time.time()});pending=None
            if not pending and c.is_connected() and now>=next_send and not a.outage_start<=now<a.outage_end:
                row=db.peek(time.time())
                if row:
                    rid,m=row;info=c.publish('research/'+a.run,json.dumps(m),qos=a.qos)
                    if info.rc==mqtt.MQTT_ERR_SUCCESS:
                        pending=(rid,m,info,time.time());db.served(m['device']);next_send=now+1/a.dispatch_cap
                    else:failures.append({'time':now,'reason':'publish rc '+str(info.rc)})
            time.sleep(.002)
        measured_end=time.time()
        # Complete only the already-submitted update; never drain queued backlog.
        if pending:
            rid,m,info,submitted=pending;info.wait_for_publish(timeout=10)
            if info.is_published():
                db.acknowledge(rid);sent+=1;published.append({'device':m['device'],'seq':m['seq'],'submitted_utc':submitted,'publication_complete_utc':time.time()});pending=None
            else:failures.append({'reason':'final publisher completion timeout'})
    finally:
        metadata.update({'generated':db.audit_count(),'published':sent,'remaining':db.size(),'max_queue':max_queue,'failures':failures,'measured_end_utc':locals().get('measured_end',time.time()),'ended_utc':time.time(),'connections':connections,'published_updates':published,'generator':'nonblocking publication-completion polling; generation independent of acknowledgement waits; nominal 4 devices x 5Hz','pending':pending is not None,'cpu_seconds':time.process_time()-cpu0,'peak_rss_bytes':peak_rss})
        (a.output/'summary.json').write_text(json.dumps(metadata,indent=2));c.disconnect();c.loop_stop();db.close()
        if serial:serial.close()
if __name__=='__main__':main()
