"""Execute matched WAN scenarios on an already authorized, reachable AWS VM.

Never creates cloud resources or security credentials. The SSH host key must
have been verified against EC2 console output before this runner is used.
"""
import argparse
import json
import random
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REMOTE='/opt/dt-research'
def main():
    p=argparse.ArgumentParser();p.add_argument('--host',required=True);p.add_argument('--key',type=Path,required=True);p.add_argument('--known-hosts',type=Path,required=True);p.add_argument('--output',type=Path,default=ROOT/'results/cloud_wan');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    cfg=json.loads((ROOT/'configs/cloud_wan.json').read_text())
    options=['-i',str(a.key),'-o','KexAlgorithms=curve25519-sha256','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(a.known_hosts),'-o','ConnectTimeout=10','-o','ServerAliveInterval=5']
    destination='ubuntu@'+a.host
    ssh=['ssh',*options,destination]
    def remote(cmd,timeout=30):return subprocess.check_output(ssh+[cmd],text=True,timeout=timeout)
    def clock_samples(n=7):
        values=[]
        for _ in range(n):
            lo=time.time();value=float(remote("python3 -c 'import time; print(time.time())'"));hi=time.time()
            values.append({'local_send_utc':lo,'cloud_utc':value,'local_receive_utc':hi,'rtt_seconds':hi-lo,'cloud_minus_edge_lower':value-hi,'cloud_minus_edge_upper':value-lo})
        return values
    remote('mkdir -p '+REMOTE+'/evidence')
    system=remote("uname -a; lscpu; free -b; timedatectl; chronyc tracking; /opt/dt-research/venv/bin/pip freeze",timeout=30)
    (a.output/'cloud_environment.txt').write_text(system)
    # Preserve SSH configuration separately from public evidence: no private key
    # or credential bytes are ever copied to output files.
    (a.output/'config.json').write_text(json.dumps(cfg,indent=2))
    design=[(seed,qos,policy,scenario) for seed in cfg['seeds'] for qos in cfg['qos'] for policy in cfg['policies'] for scenario in cfg['scenarios']]
    random.Random(20261007).shuffle(design);(a.output/'order.json').write_text(json.dumps(design))
    commands=[]
    for i,(seed,qos,policy,scenario) in enumerate(design,1):
        run=f'wan-{scenario}-{policy}-q{qos}-s{seed}'
        runout=a.output/run;runout.mkdir()
        clock_before=clock_samples(3)
        log=REMOTE+'/evidence/'+run+'.txt';db=REMOTE+'/evidence/'+run+'.sqlite'
        startcmd=f'nohup {REMOTE}/venv/bin/python {REMOTE}/repo/scripts/cloud_endpoint.py --run {shlex.quote(run)} --output {shlex.quote(db)} >{shlex.quote(log)} 2>&1 </dev/null & echo $!'
        pid=int(remote(startcmd).strip())
        tunnel=None;edge=None;capture=[];tunnelfile=(runout/'tunnel.txt').open('w')
        def start_tunnel():
            proc=subprocess.Popen(['ssh',*options,'-o','ExitOnForwardFailure=yes','-N','-L','18885:127.0.0.1:18886',destination],stdout=tunnelfile,stderr=subprocess.STDOUT)
            for _ in range(100):
                if proc.poll() is not None:raise RuntimeError('Tunnel failed; inspect tunnel.txt')
                with socket.socket() as s:
                    if s.connect_ex(('127.0.0.1',18885))==0:return proc
                time.sleep(.05)
            proc.terminate();raise RuntimeError('Tunnel startup timed out')
        try:
            for _ in range(30):
                if 'SUBSCRIBED' in remote('cat '+shlex.quote(log)):break
                time.sleep(.2)
            else:raise RuntimeError('Cloud receiver did not subscribe')
            tunnel=start_tunnel()
            edge=subprocess.Popen([sys.executable,str(ROOT/'scripts/cloud_edge.py'),'--run',run,'--policy',policy,'--qos',str(qos),'--port','18885','--duration',str(cfg['duration']),'--dispatch-cap',str(cfg['dispatch_cap']),'--seed',str(seed),'--outage-start','-1','--outage-end','-1','--output',str(runout/'edge')],stdout=(runout/'edge_console.txt').open('w'),stderr=subprocess.STDOUT)
            anchor=None;broken=False;restored=False
            while edge.poll() is None:
                # The edge writes its origin immediately after MQTT connects.
                origin=runout/'edge/start.json'
                if anchor is None and origin.exists():anchor=json.loads(origin.read_text())['started_utc']
                elapsed=time.time()-anchor if anchor else 0
                if scenario=='tunnel_break' and anchor and elapsed>=cfg['tunnel_break'][0] and not broken:
                    tunnel.terminate();tunnel.wait(timeout=10);tunnel=None;broken=True;capture.append({'event':'tunnel_closed','utc':time.time(),'relative_to_edge_start':elapsed})
                if scenario=='tunnel_break' and broken and not restored and elapsed>=cfg['tunnel_break'][1]:
                    tunnel=start_tunnel();restored=True;capture.append({'event':'tunnel_restored','utc':time.time(),'relative_to_edge_start':elapsed})
                if anchor and elapsed>cfg['duration']+30:raise RuntimeError('Edge run exceeded bounded duration')
                time.sleep(.02)
            if edge.returncode:raise RuntimeError('Edge runner failed')
            time.sleep(2)
            commands.append({'run':run,'seed':seed,'qos':qos,'policy':policy,'scenario':scenario,'clock_before':clock_before,'clock_after':clock_samples(3),'tunnel_events':capture,'returncode':edge.returncode})
        finally:
            if edge and edge.poll() is None:edge.terminate();edge.wait(timeout=10)
            remote('kill -TERM '+str(pid)+'; sleep 1')
            if tunnel:tunnel.terminate();tunnel.wait(timeout=10)
            tunnelfile.close()
            for suffix in ['.sqlite','.metrics.json','.txt']:
                src=REMOTE+'/evidence/'+run+suffix
                subprocess.run(['scp',*options,destination+':'+src,str(runout/('cloud'+suffix))],check=True,timeout=30)
            (a.output/'executions.json').write_text(json.dumps(commands,indent=2))
        print(i,'/',len(design),run,flush=True)
    print('Completed all',len(design),'remote WAN runs')
if __name__=='__main__':main()
