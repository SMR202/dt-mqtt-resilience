"""Bounded official-source attack reproduction in a private internal Docker network.

Never exposes service ports. Upstream source is fetched separately, not vendored.
Actual paper figures remain distinct from these execution measurements.
"""
import argparse
import gzip
import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--compose',default='docker-compose');a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    services={}
    for name in ['device','digital_twin','sniffer','attacker','mitm_proxy']:
        services[name]={'build':{'context':str((a.upstream/name).resolve()),'network':'host'},'networks':['lab'],'environment':{'PYTHONUNBUFFERED':'1'},'cpus':0.5,'mem_limit':'256m'}
    services['sniffer']['volumes']=[str((a.out/'sniffer').resolve())+':/logs']
    (a.out/'sniffer').mkdir()
    services['attacker']['command']=['python','-c','import time; time.sleep(36000)']
    services['mqtt_broker']={'image':'eclipse-mosquitto:2','networks':['lab'],'volumes':[str((a.upstream/'mosquitto/mosquitto.conf').resolve())+':/mosquitto/config/mosquitto.conf:ro'],'cpus':0.5,'mem_limit':'128m'}
    hosts={name:'172.30.91.'+str(10+i) for i,name in enumerate(services)}
    for name,s in services.items():
        s['networks']={'lab':{'ipv4_address':hosts[name]}}
        s['extra_hosts']=hosts
    config={'services':services,'networks':{'lab':{'internal':True,'ipam':{'config':[{'subnet':'172.30.91.0/24'}]}}}}
    compose=a.out/'compose.json';compose.write_text(json.dumps(config,indent=2))
    base=[a.compose,'-p','dt_research_attacks','-f',str(compose)]
    steps=[]
    def call(args,limit=120,check=True):
        begin=time.time();r=subprocess.run(base+args,capture_output=True,text=True,timeout=limit)
        steps.append({'args':args,'returncode':r.returncode,'elapsed':time.time()-begin,'stdout':r.stdout,'stderr':r.stderr})
        (a.out/'execution.json').write_text(json.dumps(steps,indent=2))
        if check and r.returncode: raise RuntimeError(r.stderr[-3000:])
        return r.stdout+r.stderr
    summary={'executed':False,'platform':platform.platform(),'adaptations':['internal private bridge; no host port exposure','explicit private addresses and extra_hosts because temporary daemon embedded DNS did not resolve','resource caps 0.5CPU/256MiB per Python service','broker starts before clients','unmodified official Dockerfiles install unpinned current dependencies','bounded 5-second single-worker HTTP flood instead of uncontrolled 50 workers'],'source_commit':subprocess.check_output(['git','-c','safe.directory='+str(a.upstream.resolve()),'-C',str(a.upstream),'rev-parse','HEAD'],text=True).strip(),'source_sha256':{str(f.relative_to(a.upstream)):hashlib.sha256(f.read_bytes()).hexdigest() for f in a.upstream.rglob('*.py') if 'venv' not in f.parts}}
    try:
        call(['build'],limit=900)
        call(['up','-d','mqtt_broker']);time.sleep(3)
        call(['up','-d','sniffer','device','digital_twin','mitm_proxy','attacker'])
        time.sleep(85)
        calibration=call(['logs','--no-color','--timestamps'])
        (a.out/'calibration.txt').write_text(calibration)
        summary['original_calibration_completed']='Teste inicial finalizado' in calibration
        # Preserve failure instead of repairing the source silently.
        if not summary['original_calibration_completed']: raise RuntimeError('Original calibration completion absent; inspect logs before any attack interpretation')
        results=[]
        for attack in ['exploit','mitm-proxy']:
            before=call(['logs','--no-color','--timestamps'])
            result=call(['exec','-T','attacker','python','attacker.py',attack],limit=20)
            time.sleep(8)
            after=call(['logs','--no-color','--timestamps'])
            with gzip.open(a.out/(attack+'-services.txt.gz'),'wt') as f:f.write(after)
            results.append({'scenario':attack,'attacker_output':result,'new_service_log':after[len(before):] if after.startswith(before) else 'Full timestamped service log retained; stream ordering prevents prefix subtraction'})
            call(['exec','-T','attacker','python','-c',"import paho.mqtt.publish as p; p.multiple([('device/commands',c,1,False) for c in ['liga_temp','liga_umid','liga_arm']],hostname='mqtt_broker',port=1884)"])
            time.sleep(5)
        # Official function, bounded by process lifetime, on only this private lab.
        result=call(['exec','-T','attacker','python','-c',"import attacker,time; import threading; threading.Thread(target=attacker.attack_dos_http,kwargs={'num_threads':1},daemon=True).start(); time.sleep(5)"],limit=15)
        time.sleep(5)
        log=call(['logs','--no-color','--timestamps'])
        with gzip.open(a.out/'final-services.txt.gz','wt') as f:f.write(log)
        results.append({'scenario':'dos-http','duration_seconds':5,'workers':1,'attacker_output':result})
        summary['scenarios']=results;summary['executed']=True
        summary['images']=call(['images','--format','json'])
        summary['freeze']=call(['exec','-T','sniffer','python','-m','pip','freeze'])
    except Exception as e: summary['failure']=repr(e)
    finally:
        call(['down','--remove-orphans'],check=False)
        (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({'executed':summary['executed'],'failure':summary.get('failure'),'out':str(a.out)}))
    return 0 if summary['executed'] else 1
if __name__=='__main__': raise SystemExit(main())
