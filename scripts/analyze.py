"""Generate tables/plots and paired exploratory uncertainty from saved runs."""
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/processed'
FIG=ROOT/'figures'


def paired(frame,group):
    results=[]
    for keys,g in frame.groupby(group):
        if not isinstance(keys,tuple): keys=(keys,)
        for metric in ['mean_aoi','delivery_ratio','mae','stale_fraction']:
            pivot=g.pivot(index='seed',columns='policy',values=metric)
            for comparator in ['fifo','no_buffer','ttl','latest_no_guard']:
                if comparator not in pivot or 'latest' not in pivot: continue
                difference=(pivot['latest']-pivot[comparator]).dropna().to_numpy()
                rng=np.random.default_rng(20261007)
                draws=rng.choice(difference,(10000,len(difference)),replace=True).mean(axis=1)
                row=dict(zip(group,keys))
                row.update(metric=metric,comparator=comparator,n=len(difference),mean_delta=float(difference.mean()),
                    bootstrap_low=float(np.quantile(draws,.025)),bootstrap_high=float(np.quantile(draws,.975)))
                results.append(row)
    return pd.DataFrame(results)


def independent_live_aoi(live):
    # Exact event-based integral, independently of runner's 20ms sampling.
    cfg=json.loads((ROOT/'results/live/config.json').read_text())
    receive=defaultdict(list)
    with gzip.open(ROOT/'results/live/events.csv.gz','rt',encoding='utf-8') as f:
        for e in csv.DictReader(f):
            if e['event']=='receive' and e['accepted'] in ('1','True'):
                receive[(e['run'],int(e['device']))].append((float(e['time']),float(e['generated'])))
    records=[]
    for _,r in live.iterrows():
        total=0.
        for d in range(cfg['devices']):
            previous=0.;left=cfg['warmup'];end=cfg['duration']
            for t,g in sorted(receive[(r['run'],d)]):
                if t<=left:
                    previous=g;continue
                if t>=end: break
                total += .5*((t-previous)**2-(left-previous)**2)
                previous=g;left=t
            total += .5*((end-previous)**2-(left-previous)**2)
        exact=total/(cfg['devices']*(cfg['duration']-cfg['warmup']))
        error=abs(exact-r['mean_aoi'])
        # Finite sampling, scheduling and boundary differences; <=40ms allowed.
        assert error<.04,(r['run'],exact,r['mean_aoi'],error)
        records.append({'run':r['run'],'sampled_aoi':r['mean_aoi'],'event_integral_aoi':exact,'absolute_difference':error})
    return pd.DataFrame(records)


def main():
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(exist_ok=True)
    sim=pd.read_csv(ROOT/'results/simulation/runs.csv')
    live=pd.read_csv(ROOT/'results/live/runs.csv')
    assert len(sim)==1200 and len(live)==108,'Incomplete evaluation; no final tables allowed'
    assert (live.audit_count==live.generated).all()
    assert (live.sent==live.delivered).all()
    assert (live.regressions==0).all()
    metrics=['mean_aoi','p95_aoi','stale_fraction','mae','delivery_ratio','mean_latency','max_queue','recovery_seconds']
    sim.groupby(['devices','rate','scenario','policy'])[metrics].agg(['mean','std']).to_csv(OUT/'simulation_summary.csv')
    live.groupby(['qos','scenario','policy'])[metrics+['cpu_seconds','peak_runner_rss_bytes','peak_broker_rss_bytes','payload_bytes']].agg(['mean','std']).to_csv(OUT/'live_summary.csv')
    paired(sim,['devices','rate','scenario']).to_csv(OUT/'simulation_paired.csv',index=False)
    paired(live,['qos','scenario']).to_csv(OUT/'live_paired.csv',index=False)
    independent_live_aoi(live).to_csv(OUT/'aoi_verification.csv',index=False)
    # Collapse QoS within each seed before presenting a general overview.
    overview=live.groupby(['seed','scenario','policy'])[metrics].mean().reset_index()
    means=overview.groupby(['scenario','policy'])[metrics].mean().reset_index()
    means.to_csv(OUT/'live_overview.csv',index=False)
    sim.groupby(['devices','rate','scenario','policy'])[['regressions','rejections','expired','coalesced']].mean().to_csv(OUT/'ablations.csv')
    live.groupby('policy')[['cpu_seconds','peak_runner_rss_bytes','peak_broker_rss_bytes','payload_bytes','max_queue']].agg(['mean','max']).to_csv(OUT/'resource_costs.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    policies=['no_buffer','fifo','latest'];colors=['#7d8899','#cb7848','#147a79']
    scenarios=['healthy','degraded','overloaded','outage']
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,metric,title in zip(axes,['mean_aoi','delivery_ratio'],['Live-state freshness','Finite-horizon completeness']):
        x=np.arange(4)
        for i,policy in enumerate(policies):
            subset=means[means.policy==policy].set_index('scenario').reindex(scenarios)
            ax.bar(x+(i-1)*.24,subset[metric],.23,label=policy,color=colors[i])
        ax.set_xticks(x,scenarios);ax.set_title(title);ax.set_ylabel('Mean age (s)' if metric=='mean_aoi' else 'Unique receipts / generated');ax.grid(axis='y',alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle('Real MQTT on loopback • 4 sensors × 20 Hz • 108 six-second runs',fontsize=12)
    fig.savefig(FIG/'live_comparison.png',dpi=180);fig.savefig(FIG/'live_comparison.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    selected=sim[(sim.devices==16)&(sim.rate==10)]
    for ax,metric,title in zip(axes,['mean_aoi','max_queue'],['State age under high offered load','Maximum live outbox occupancy']):
        for policy,color in zip(['fifo','ttl','latest'],colors):
            g=selected[selected.policy==policy].groupby('scenario')[metric].mean().reindex(scenarios)
            ax.plot(scenarios,g,'o-',label=policy,color=color)
        ax.set_title(title);ax.set_ylabel('Mean age (s)' if metric=='mean_aoi' else 'Records');ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle('Application simulation • 16 sensors × 10 Hz • 60 virtual seconds',fontsize=12)
    fig.savefig(FIG/'simulation_comparison.png',dpi=180);fig.savefig(FIG/'simulation_comparison.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for policy,color in zip(['fifo','ttl','latest'],colors):
        subset=sim[(sim.devices==16)&(sim.scenario=='degraded')&(sim.policy==policy)].groupby('rate').mean_aoi.mean()
        ax.plot(subset.index,subset.values,'o-',label=policy,color=color)
    ax.set(xlabel='Per-sensor generation rate (Hz)',ylabel='Mean age (s)',title='Load sensitivity • application simulation, 16 sensors')
    ax.legend(frameon=False);ax.grid(alpha=.2)
    fig.savefig(FIG/'load_sensitivity.png',dpi=180);fig.savefig(FIG/'load_sensitivity.pdf');plt.close(fig)
    guard=sim[sim.policy=='latest_no_guard'].regressions.sum()
    (OUT/'validation.json').write_text(json.dumps({'simulation_runs':len(sim),'live_runs':len(live),
        'all_live_generated_updates_preserved_in_local_audit':True,'all_live_published_updates_received':True,
        'all_guarded_live_runs_monotonic':True,'unguarded_simulation_regressions':int(guard),
        'independent_event_integral_check':'all live runs within 40ms of sampled mean AoI',
        'bootstrap_note':'paired within seed; exploratory percentile intervals, n=3 live / n=10 simulation; not multiplicity-adjusted significance claims'},indent=2))
    print(means[['scenario','policy','mean_aoi','delivery_ratio']].round(4).to_string(index=False))
    print('Guard ablation regressions',guard)


if __name__=='__main__': main()
