"""Independently summarize executed Linux evidence; never substitute model values."""
import collections
from contextlib import closing
import csv
import gzip
import json
import re
import sqlite3
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def age_integral(events,devices,t0,t1):
    total=0.
    for d in range(devices):
        at=0.;gen=0.
        for e in sorted((e for e in events if int(e['device'])==d and int(e['accepted'])),key=lambda e:float(e['time'])):
            nxt=min(t1,float(e['time']));left=max(t0,at)
            if nxt>left:total+=((nxt-gen)**2-(left-gen)**2)/2
            if float(e['time'])>t1:at=t1;break
            at=float(e['time']);gen=float(e['generated'])
        left=max(t0,at)
        if t1>left:total+=((t1-gen)**2-(left-gen)**2)/2
    return total/devices/(t1-t0)
def main():
    out=ROOT/'results/processed';out.mkdir(exist_ok=True)
    attack=ROOT/'results/linux_attacks_attempt2'
    summary=json.loads((attack/'summary.json').read_text())
    raw=gzip.open(attack/'final-services.txt.gz','rt').read()
    calls=json.loads((attack/'execution.json').read_text())
    checks=[]
    for i,c in enumerate(calls):
        args=c['args']
        if args[:4]==['exec','-T','attacker','python'] and (args[-1] in ['exploit','mitm-proxy'] or 'attack_dos_http' in args[-1]):
            before=next(x for x in reversed(calls[:i]) if x['args'][:1]==['logs'])
            after=next(x for x in calls[i+1:] if x['args'][:1]==['logs'])
            old=collections.Counter((before['stdout']+before['stderr']).splitlines())
            new=collections.Counter((after['stdout']+after['stderr']).splitlines())
            delta='\n'.join((new-old).elements())
            scenario=args[-1] if args[-1] in ['exploit','mitm-proxy'] else 'dos-http'
            checks.append({'scenario':scenario,'returncode':c['returncode'],'elapsed':c['elapsed'],'new_proxy_modifications':len(re.findall(r'\[PROXY\]\[ALTERADO\]',delta)),'new_device_shutdowns':len(re.findall(r'\[DEVICE\] Sensor .*desligado!',delta)),'new_device_flood_receipts':delta.count('[DEVICE] Comando recebido do Twin: dos_http_payload'),'new_rate_alerts':len(re.findall(r'\[SNIFFER\]\[ALERTA\] (?:PPS|BPS)',delta))})
    pps=[int(x) for x in re.findall(r'PPS de twin_to_device \((\d+)\)',raw)]
    result={'scope':'executed official Docker topology with isolation/resource/dependency adaptations; bounded attacks; not exact Table 2 or 60-minute healthy calibration','original_calibration_completed':summary['original_calibration_completed'],'executed':summary['executed'],'scenarios':checks,'maximum_reported_command_application_messages_per_second':max(pps),'published_attack_values_not_reproduced':True}
    assert result['executed'] and result['original_calibration_completed']
    assert any(c['new_proxy_modifications'] and c['new_device_shutdowns'] for c in checks if c['scenario']=='mitm-proxy')
    assert any(c['new_device_shutdowns']>=3 for c in checks if c['scenario']=='exploit')
    (out/'linux_attack_checks.json').write_text(json.dumps(result,indent=2))
    netem=ROOT/'results/linux_netem'
    env=json.loads((netem/'environment.json').read_text())
    rows=list(csv.DictReader((netem/'runs.csv').open()))
    events=collections.defaultdict(list)
    with gzip.open(netem/'events.csv.gz','rt') as f:
        for e in csv.DictReader(f):events[e['run']].append(e)
    calculated=[]
    for r in rows:
        ev=events[r['run']];generated=[e for e in ev if e['event']=='generate'];received=[e for e in ev if e['event']=='receive']
        assert len(generated)==int(r['generated']) and len(received)==int(r['delivered'])==int(r['sent']),r['run']
        with tempfile.NamedTemporaryFile(suffix='.sqlite',delete=False,dir=ROOT/'work') as f:
            f.write(gzip.open(netem/'queues'/(r['run']+'.sqlite.gz'),'rb').read());name=f.name
        try:
            with closing(sqlite3.connect(name)) as db:assert db.execute('SELECT COUNT(*) FROM audit').fetchone()[0]==len(generated)
        finally:Path(name).unlink()
        calculated.append({'run':r['run'],'scenario':r['scenario'],'policy':r['policy'],'qos':r['qos'],'seed':r['seed'],'event_integral_mean_aoi':age_integral(received,4,1,6),'sampled_mean_aoi':float(r['mean_aoi']),'generated':int(r['generated']),'published':int(r['sent']),'received':int(r['delivered']),'delivery_ratio':float(r['delivery_ratio']),'max_queue':int(r['max_queue']),'cpu_seconds':float(r['cpu_seconds']),'peak_runner_rss_bytes':int(r['peak_runner_rss_bytes'])})
    assert len(rows)==36 and env['failed_runs']==0
    with (out/'linux_netem_verified.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(calculated[0]));w.writeheader();w.writerows(calculated)
    groups=collections.defaultdict(list)
    for r in calculated:groups[(r['scenario'],r['policy'],r['qos'])].append(r)
    aggregated=[]
    for key,values in sorted(groups.items()):
        aggregated.append(dict(zip(['scenario','policy','qos'],key))|{'n':len(values),'event_integral_mean_aoi':sum(v['event_integral_mean_aoi'] for v in values)/len(values),'delivery_ratio':sum(v['delivery_ratio'] for v in values)/len(values),'max_queue':max(v['max_queue'] for v in values)})
    with (out/'linux_netem_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(aggregated[0]));w.writeheader();w.writerows(aggregated)
    qdisc=(netem/'qdisc.txt').read_text();drops=sum(int(x) for x in re.findall(r'dropped (\d+)',qdisc))
    verification={'scope':env['label'],'runs':len(rows),'failures':env['failed_runs'],'generated':sum(r['generated'] for r in calculated),'published':sum(r['published'] for r in calculated),'received':sum(r['received'] for r in calculated),'reported_qdisc_drops':drops,'max_sampled_vs_integral_age_difference_seconds':max(abs(r['sampled_mean_aoi']-r['event_integral_mean_aoi']) for r in calculated),'age_analysis':'event-integral is primary; synchronous QoS waits bias irregular in-loop samples','network':'100ms +/-20ms netem delay and 2% configured packet loss on isolated loopback; two MQTT connections; not a real WAN','resource_confound':'attack/build and network jobs initially overlap; Docker runner capped 2CPU/1GiB; descriptive costs only'}
    assert drops>0
    (out/'linux_netem_checks.json').write_text(json.dumps(verification,indent=2))
    print(json.dumps(result));print(json.dumps(verification))
if __name__=='__main__':main()
