"""Independently audit actual cloud receipts and bound age by measured clocks."""
import json
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def age(receipts,start,end,offset,devices=4,initial_age=3):
    area=0
    for d in range(devices):
        held=start-initial_age;last=start
        for device,seq,g,r,accepted in receipts:
            if device!=d or not accepted:continue
            at=r-offset
            if at>end:break
            if at<start:held=max(held,g);continue
            area+=(at-last)*(last-held)+(at-last)**2/2
            held=max(held,g);last=at
        area+=(end-last)*(last-held)+(end-last)**2/2
    return area/(devices*(end-start))

def main():
    folder=ROOT/'results/cloud_wan'
    runs=json.loads((folder/'executions.json').read_text());cfg=json.loads((folder/'config.json').read_text());rows=[]
    for run in runs:
        out=folder/run['run'];edge=json.loads((out/'edge/summary.json').read_text());cloud=json.loads((out/'cloud.metrics.json').read_text())
        with sqlite3.connect(out/'edge/edge.sqlite') as db:
            audit=[json.loads(x[0]) for x in db.execute('SELECT payload FROM audit')]
        with sqlite3.connect(out/'cloud.sqlite') as db:
            receipts=db.execute('SELECT device,seq,generated_utc,received_utc,accepted FROM received ORDER BY received_utc').fetchall()
        lookup={(x['device'],x['seq']):x for x in audit}
        assert len(audit)==edge['generated']
        assert all((d,s) in lookup and lookup[d,s]['generated_utc']==g for d,s,g,r,ok in receipts)
        samples=run['clock_before']+run['clock_after']
        # Broad envelope allows offsets to vary between observed probes. These
        # are conditional bounds, not a hardware synchronized clock guarantee.
        low=min(x['cloud_minus_edge_lower'] for x in samples);high=max(x['cloud_minus_edge_upper'] for x in samples)
        # A receipt cannot precede generation. With a run-constant offset this
        # supplies an additional causal upper bound; no network symmetry assumed.
        if receipts:high=min(high,min(r-g for d,s,g,r,ok in receipts))
        assert low<=high,'Clock bounds inconsistent: report timing unavailable'
        mid=(low+high)/2
        start=edge['started_utc'];end=edge['measured_end_utc']
        lo_age=age(receipts,start+cfg['warmup'],end,low)
        hi_age=age(receipts,start+cfg['warmup'],end,high)
        rows.append({**{k:run[k] for k in ['run','seed','qos','policy','scenario']},'generated':len(audit),'published':edge['published'],'received_unique':len(receipts),'accepted':sum(x[4] for x in receipts),'callbacks':cloud['counts']['callbacks'],'rejected_callbacks':cloud['counts']['rejected'],'receipt_ratio':len(receipts)/len(audit),'age_seconds_midpoint':age(receipts,start+cfg['warmup'],end,mid),'age_clock_envelope_lower':min(lo_age,hi_age),'age_clock_envelope_upper':max(lo_age,hi_age),'clock_offset_lower':low,'clock_offset_upper':high,'max_queue':edge['max_queue'],'edge_wall_seconds':edge['ended_utc']-start,'cloud_wall_seconds':cloud['ended_utc']-cloud['started_utc'],'edge_cpu_seconds':edge['cpu_seconds'],'cloud_cpu_seconds':cloud['cpu_seconds'],'edge_peak_rss_bytes':edge['peak_rss_bytes'],'cloud_peak_rss_bytes':cloud['peak_rss_bytes'],'failures':len(edge['failures'])})
    df=pd.DataFrame(rows);df.to_csv(ROOT/'results/processed/cloud_wan_verified.csv',index=False)
    df.groupby(['scenario','qos','policy']).mean(numeric_only=True).reset_index().to_csv(ROOT/'results/processed/cloud_wan_summary.csv',index=False)
    pairs=df[df.policy=='fifo'].merge(df[df.policy=='latest'],on=['seed','qos','scenario'],suffixes=('_fifo','_latest'))
    pairs['age_reduction_percent']=100*(1-pairs.age_seconds_midpoint_latest/pairs.age_seconds_midpoint_fifo)
    pairs['age_reduction_conservative_percent']=100*(1-pairs.age_clock_envelope_upper_latest/pairs.age_clock_envelope_lower_fifo)
    pairs.to_csv(ROOT/'results/processed/cloud_wan_pairs.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,scenario in zip(axes,['healthy','tunnel_break']):
        for policy,color in [('fifo','#435580'),('latest','#15947d')]:
            part=df[(df.scenario==scenario)&(df.policy==policy)].groupby('qos').mean(numeric_only=True)
            if part.empty:continue
            ax.errorbar(part.index,part.age_seconds_midpoint,yerr=[part.age_seconds_midpoint-part.age_clock_envelope_lower,part.age_clock_envelope_upper-part.age_seconds_midpoint],marker='o',label=policy,color=color,capsize=4)
        ax.set(title=scenario.replace('_',' '),xlabel='MQTT QoS',ylabel='Mean held-state age (s)',xticks=[0,1,2]);ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Actual PC-to-AWS transport; conditional clock envelopes')
    fig.savefig(ROOT/'figures/cloud_wan_comparison.png',dpi=180);plt.close(fig)
    checks={'scope':cfg['semantics'],'completed_runs':len(df),'planned_runs':len(json.loads((folder/'order.json').read_text())),'generated':int(df.generated.sum()),'received_unique':int(df.received_unique.sum()),'published':int(df.published.sum()),'rejected_callbacks':int(df.rejected_callbacks.sum()),'audit_checks':'Every unique cloud receipt maps to the matching edge audit sample and timestamp. Publication completion is not proof of cloud commit.','clock_method':'Envelope of before/after SSH time probes tightened by receipt causality; midpoint is descriptive, not certified one-way timing. A constant clock offset within each 20-second run is assumed.','physical_sensor':False}
    (ROOT/'results/processed/cloud_wan_checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
