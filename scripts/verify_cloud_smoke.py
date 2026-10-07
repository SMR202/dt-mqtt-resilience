"""Local integration verification only; this is explicitly not WAN evidence."""
import json
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'work/cloud-smoke';out.mkdir(exist_ok=False)
    brokerlog=(out/'broker.txt').open('w')
    broker=subprocess.Popen([sys.executable,str(ROOT/'scripts/broker.py'),'18885'],stdout=brokerlog,stderr=subprocess.STDOUT)
    checks=[]
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1',18885))==0:break
            time.sleep(.1)
        for qos in [0,1,2]:
            for policy in ['fifo','latest']:
                name=f'smoke-{policy}-q{qos}'; logfile=out/(name+'.txt');f=logfile.open('w')
                receiver=subprocess.Popen([sys.executable,str(ROOT/'scripts/cloud_endpoint.py'),'--run',name,'--port','18885','--output',str(out/(name+'.sqlite'))],stdout=f,stderr=subprocess.STDOUT)
                try:
                    for _ in range(100):
                        if 'SUBSCRIBED' in logfile.read_text():break
                        if receiver.poll() is not None:raise RuntimeError(logfile.read_text())
                        time.sleep(.1)
                    else:raise RuntimeError('Receiver subscription timed out')
                    subprocess.run([sys.executable,str(ROOT/'scripts/cloud_edge.py'),'--run',name,'--policy',policy,'--qos',str(qos),'--port','18885','--duration','2','--outage-start','.6','--outage-end','1.2','--output',str(out/name)],check=True,timeout=20)
                    time.sleep(.5)
                finally:receiver.terminate();receiver.wait(timeout=10);f.close()
                summary=json.loads((out/name/'summary.json').read_text())
                with sqlite3.connect(out/(name+'.sqlite')) as db:
                    received=db.execute('SELECT COUNT(*) FROM received').fetchone()[0]
                    rejected=db.execute('SELECT COUNT(*) FROM received WHERE accepted=0').fetchone()[0]
                assert received==summary['published'] and not rejected and not summary['failures'],name
                checks.append({'run':name,'generated':summary['generated'],'published':summary['published'],'received':received,'rejected':rejected})
    finally:broker.terminate();broker.wait(timeout=10);brokerlog.close()
    result={'scope':'local loopback integration smoke test of prepared cloud scripts; not remote cloud/WAN or physical evidence','checks':checks}
    (ROOT/'results/processed/cloud_smoke_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
if __name__=='__main__':main()
