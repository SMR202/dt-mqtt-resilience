"""Application-level discrete-event model, NOT a TCP/MQTT packet simulator."""
import argparse
import csv
import gzip
import hashlib
import heapq
import json
import math
import platform
import random
import statistics
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.policies import TwinState


def run(cfg, devices, rate, seed, policy, scenario, writer=None):
    started, cpu = time.perf_counter(), time.process_time()
    s = cfg['scenarios'][scenario]
    duration, dt, warmup = cfg['duration'], cfg['dt'], cfg['warmup']
    twin = TwinState(devices, guard=policy != 'latest_no_guard')
    fifo, latest, arrivals = deque(), {}, []
    sent = delivered = generated = coalesced = expired = overflow = 0
    maximum_queue = 0
    sample_aoi, sample_error, latency, receipt_ids = [], [], [], set()
    recovery = None
    counter, next_gen = 0, [d / (devices * rate) for d in range(devices)]
    sequences = [0] * devices
    tokens = 0.
    last_device = -1
    for step in range(round(duration / dt) + 1):
        now = step * dt
        outage = s['outage'] and s['outage'][0] <= now < s['outage'][1]
        while arrivals and arrivals[0][0] <= now:
            at, _, m = heapq.heappop(arrivals)
            delivered += 1
            receipt_ids.add((m['device'],m['seq']))
            accepted = twin.accept(m)
            latency.append(at - m['generated'])
            if writer:
                writer.writerow([devices,rate,seed,policy,scenario,'receive',at,m['device'],m['seq'],m['generated'],m['value'],int(accepted)])
        for d in range(devices):
            while next_gen[d] <= now + 1e-9:
                g = next_gen[d]
                m = {'device': d, 'seq': sequences[d], 'generated': g, 'value': math.sin(g*.3+d)}
                sequences[d] += 1
                generated += 1
                next_gen[d] += 1 / rate
                if writer:
                    writer.writerow([devices,rate,seed,policy,scenario,'generate',g,d,m['seq'],g,m['value'],1])
                if policy.startswith('latest'):
                    coalesced += int(d in latest)
                    latest[d] = m
                elif policy == 'no_buffer':
                    if not outage and not fifo:
                        fifo.append(m)
                else:
                    if len(fifo) >= cfg['queue_limit']:
                        overflow += 1
                    else:
                        fifo.append(m)
        if policy == 'ttl':
            while fifo and now-fifo[0]['generated'] > cfg['ttl']:
                fifo.popleft()
                expired += 1
        maximum_queue = max(maximum_queue, len(latest) if policy.startswith('latest') else len(fifo))
        # No burst credit accumulates during disconnection; service has finite capacity.
        tokens = min(1., tokens + s['capacity']*dt) if outage else tokens + s['capacity']*dt
        if not outage:
            while tokens >= 1:
                if policy.startswith('latest'):
                    if not latest:
                        tokens = min(tokens,1.)
                        break
                    key = min(latest, key=lambda d: ((d-last_device-1)%devices))
                    m = latest.pop(key)
                    last_device = key
                else:
                    if not fifo:
                        tokens = min(tokens,1.)
                        break
                    m = fifo.popleft()
                tokens -= 1
                sent += 1
                counter += 1
                # Common random numbers keyed by message, independent of policy order.
                rng = random.Random(seed*100000000 + m['device']*100000 + m['seq'])
                delay = max(0., s['delay'] + rng.uniform(-s['jitter'],s['jitter']))
                heapq.heappush(arrivals,(now+delay,counter,m))
        if policy == 'no_buffer':
            fifo.clear()
        ages = [max(0., now-v['generated']) for v in twin.states.values()]
        if now >= warmup:
            sample_aoi.extend(ages)
            sample_error.extend(abs(math.sin(now*.3+d)-twin.states[d]['value']) for d in range(devices))
        if s['outage'] and now >= s['outage'][1] and recovery is None and max(ages) <= 1.:
            recovery = now-s['outage'][1]
    return dict(devices=devices,rate=rate,seed=seed,policy=policy,scenario=scenario,
        generated=generated,sent=sent,delivered=delivered,delivery_ratio=len(receipt_ids)/generated,
        mean_aoi=statistics.mean(sample_aoi),p95_aoi=sorted(sample_aoi)[int(.95*(len(sample_aoi)-1))],
        stale_fraction=sum(a>1 for a in sample_aoi)/len(sample_aoi),mae=statistics.mean(sample_error),
        mean_latency=statistics.mean(latency) if latency else None,max_queue=maximum_queue,
        coalesced=coalesced,expired=expired,overflow=overflow,rejections=twin.rejections,
        regressions=twin.regressions,recovery_seconds=recovery,
        remaining=(len(latest) if policy.startswith('latest') else len(fifo))+len(arrivals),
        wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',default='configs/simulation.json')
    p.add_argument('--output',default='results/simulation')
    args=p.parse_args()
    cfg=json.loads((ROOT/args.config).read_text())
    out=ROOT/args.output
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    with gzip.open(out/'events.csv.gz','wt',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['devices','rate','seed','policy','scenario','event','time','device','seq','generated','value','accepted'])
        for devices in cfg['devices']:
            for rate in cfg['rates']:
                for scenario in cfg['scenarios']:
                    for seed in cfg['seeds']:
                        for policy in cfg['policies']:
                            # Seed-zero raw events anchor every condition; all
                            # repetitions retain raw per-run metric records.
                            rows.append(run(cfg,devices,rate,seed,policy,scenario,writer if seed==0 else None))
                    print(devices,rate,scenario,'complete',flush=True)
    with (out/'runs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'config.json').write_text(json.dumps(cfg,indent=2))
    (out/'environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'label':'executed application simulation; no MQTT wire protocol'},indent=2))
    print(len(rows),'runs executed')


if __name__=='__main__':
    main()
