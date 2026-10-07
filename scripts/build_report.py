"""Build research reports exclusively from delivered experimental evidence."""
import html
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x) for x in row)+' |' for row in rows])

def report():
    live=pd.read_csv(ROOT/'results/live/runs.csv')
    sim=pd.read_csv(ROOT/'results/simulation/runs.csv')
    overview=pd.read_csv(ROOT/'results/processed/live_overview.csv')
    core=json.loads((ROOT/'results/baseline_core/summary.json').read_text())
    checks=json.loads((ROOT/'results/processed/raw_evidence_checks.json').read_text())
    validation=json.loads((ROOT/'results/processed/validation.json').read_text())
    meta=json.loads((ROOT/'docs/literature_metadata.json').read_text(encoding='utf-8'))
    fifo=overview[(overview.scenario=='outage')&(overview.policy=='fifo')].iloc[0]
    latest=overview[(overview.scenario=='outage')&(overview.policy=='latest')].iloc[0]
    improvement=100*(1-latest.mean_aoi/fifo.mean_aoi)
    observed=table(['Scenario','Policy','Mean age (s)','p95 age (s)','Delivery (%)','MAE'],[[r.scenario,r.policy,f'{r.mean_aoi:.3f}',f'{r.p95_aoi:.3f}',f'{100*r.delivery_ratio:.2f}',f'{r.mae:.3f}'] for r in overview.itertuples()])
    high=sim[(sim.devices==16)&(sim.rate==10)].groupby(['scenario','policy'])[['mean_aoi','delivery_ratio','max_queue']].mean().reset_index()
    simtable=table(['Scenario','Policy','Mean age (s)','Delivery (%)','Max queue'],[[r.scenario,r.policy,f'{r.mean_aoi:.3f}',f'{100*r.delivery_ratio:.2f}',f'{r.max_queue:.0f}'] for r in high.itertuples() if r.policy in ('fifo','ttl','latest')])
    costs=live.groupby('policy')[['cpu_seconds','peak_runner_rss_bytes','peak_broker_rss_bytes','payload_bytes']].mean()
    costtable=table(['Policy','CPU seconds/run','Runner RSS (MiB)','Broker RSS (MiB)','Payload bytes/run'],[[idx,f'{r.cpu_seconds:.3f}',f'{r.peak_runner_rss_bytes/1048576:.2f}',f'{r.peak_broker_rss_bytes/1048576:.2f}',f'{r.payload_bytes:.0f}'] for idx,r in costs.iterrows()])
    references=[]
    for i,m in enumerate(meta,1):
        names=', '.join(a.get('family','') for a in m['authors'])
        yr=m['published']['date-parts'][0][0]
        references.append(f'{i}. {names}. {m["title"]}. {"; ".join(m["venue"])} ({yr}). [DOI](https://doi.org/{m["doi"]}).')
    text=f'''# Freshness-aware edge replay for MQTT digital-twin synchronization

## Final research-phase reproduction and methodology report

Prepared 7 October 2026 • Cloud Computing research project • Muhammad Sameer and Humayun Bilal (proposal team names; authorship/contributions require human confirmation).

**Status:** executed local research package and preliminary manuscript material. Exact original-paper numerical reproduction, remote cloud validation and instructor approval remain open. This PDF is not the final instructor-template Overleaf manuscript.

## Abstract

Buffered telemetry can preserve a replay opportunity while leaving a digital twin's current state stale. We audit and execute the feasible MQTT core of a recent communication-monitoring study, then evaluate fair latest-state coalescing with a sequence-checked receiver and separate durable local history. The empirical package contains 108 actual MQTT loopback runs across three QoS levels and four application-shaped uplink conditions, plus 1,200 application-simulation executions across load, scale and policy variations. In the live outage condition, mean Age of Information decreases from {fifo.mean_aoi:.3f} s with FIFO to {latest.mean_aoi:.3f} s with the proposed policy ({improvement:.1f}%); finite-horizon delivery remains approximately {100*latest.delivery_ratio:.1f}%. A fair epoch-only baseline reaches similar freshness in short live tests, so universal superiority is not claimed. Every generated live sample is preserved locally; intermediate updates are not all delivered remotely. Removing the receiver guard causes {validation['unguarded_simulation_regressions']:,} regressions across the unguarded simulation runs. The results support distinguishing current-state freshness from traffic rate and history completeness. They do not establish packet-loss resilience, production durability, attack-classification accuracy or public-cloud performance.

Reproducibility: The code and reproducibility materials for this study are publicly available at: https://github.com/SMR202/dt-mqtt-resilience

## 1. Problem, motivation and contribution

A twin receiving old updates can appear active while its state is obsolete. For a current-state service, replay order and per-device coverage matter in addition to communication reliability. We investigate this application-layer trade-off within the existing Digital Twin + cloud/MQTT project. The cloud component is an independently deployable MQTT subscriber/current-state service; the executed benchmark co-locates it with the edge and broker. Physical measurements, cloud WAN deployment and billing are not part of the evidence.

Our contribution is a reproducible systems experiment combining committed local audit history, per-device latest-state coalescing, round-robin dispatch and a monotonic receiver. These elements are established techniques. We claim a scoped implementation/evaluation contribution and a paper/code reproducibility audit; no theoretical novelty or globally optimal scheduling result is asserted.

## 2. Reference selection and initial reproduction

The selected reference is Rodrigues et al., *A Data Rate Monitoring Approach for Cyberattack Detection in Digital Twin Communication*, Sensors 25(24), 7476 (2025), DOI 10.3390/s25247476. The official artifact is pinned to commit `43346f60a9f41392611242ff3cb7589d7a758aa7`. The full selection rationale, original environment/settings and rejected alternatives are in the initial audit. That audit is part of this report package and avoids treating paper descriptions as executed results.

The native adapter runs original MQTT sensor, receiver and monitor function bodies, retains original calibration timing, and replaces Docker addressing and the broker. A benign telemetry burst exercises the communication-rate monitor. It is not a reproduction of the reference's attacks or packet-level numerical figures.

Measured native evidence: {core['events']} observed MQTT events, {core['observed_burst_messages']} deliberately generated benign-burst messages, and {core['elapsed']:.2f} s elapsed. The observed burst is {core['observed_burst_messages_per_second']:.2f} application messages/s. The independent paper-rule implementation, calibrated on this run's observed sensor-message bins, yields {core['thresholds_from_observer_sensor_messages']['paper_3sigma']:.3f} messages/s; the observer maximum is {core['thresholds_from_observer_sensor_messages']['upstream_maximum']}. The original monitor's own device-to-twin calibration maximum is {core['original_min_max']['device_to_twin']['max']}. Observer and monitor windows/capture boundaries differ, so their thresholds need not match.

The first native attempt failed to activate calibration because its completion message did not arrive. The repaired adapter resends only that missing control message using a running network loop and QoS1; this was required in the successful run as well. UTF-8 logging is another native adaptation. Failed logs, successful logs, source hashes and message events remain inspectable. Code inspection also found the maximum-threshold rule, unpinned dependencies, Paho API/version disagreement and the difference between application counters and wire PPS/BPS. None of the published Table 2 values is presented as a measurement of this run.

## 3. Literature-grounded gap and research question

The 16-paper literature matrix covers platform integration, cloud processing, network-aware twins, operational resilience, synchronization budgets, AoI/AoDT, scheduling and reproducible benchmarks. It explicitly includes prior freshness optimization. A statement that digital-twin research has ignored freshness would be indefensible. The selected rate-oriented artifact, however, lacks generation-age-aware current-state application and a fair recovery outbox. Whether its traffic-rate signals reflect useful current-state recovery is therefore untested in that implementation.

RQ: Under constrained edge dispatch and temporary disconnection, how does fair latest-state coalescing with monotonic application compare with FIFO replay and expiry in state age, error, delivery completeness and resource cost?

Objectives are to reproduce the feasible core with an honest audit; implement and preserve matched baseline/proposed policies; quantify freshness/completeness/recovery/resources; and test expiry and receiver-guard ablations. The complete thematic synthesis, review-depth labels and citations are in `docs/LITERATURE_REVIEW.md`.

## 4. Methodology

Messages contain device ID, increasing sequence number, nominal generation time and an analytically known state value. Current state is `sin(0.3*t+device)`. No learned model or physical process prediction is used. The receiver's held value and generation time are compared with current analytical ground truth.

AoI is time since the latest applied update was generated. Mean and p95 AoI use device-time observations after warm-up. Stale fraction uses a one-second threshold chosen for this experiment. MAE is unitless held-state error. Delivery ratio divides unique received updates by all generated updates, including intentionally suppressed ones. Synchronization latency includes edge waiting. Recovery requires every device's age to return to at most one second; unrecovered runs are censored rather than silently omitted.

FIFO preserves queued updates in order. Epoch-only staging drops old eligible work and rotates live sensor emission priority. Expiry drops queued updates older than one second in the simulation. The proposal persists all samples in a local audit table and retains only each device's newest queued live update. Round-robin service avoids permanent device priority. A sequence guard rejects duplicate/older application updates. The guard ablation changes only receiver acceptance.

SQLite uses WAL/FULL synchronization and non-reused outbox IDs. Publication-complete acknowledgement precedes deletion, preventing an old acknowledgement from deleting a new replacement. MQTT publisher completion is not a cloud-state commit acknowledgement. The local audit is not delivered to a cloud archive. Commands/events requiring lossless history are outside latest-value coalescing semantics.

![Architecture](../figures/architecture.png)

## 5. Experimental design and environment

The live design contains 108 runs: three seeds × QoS 0/1/2 × healthy/degraded/overloaded/outage × epoch-only/FIFO/latest. Each runs six measured seconds after subscriber setup; one second is excluded from freshness metrics. Four devices generate 20 Hz each. Nominal dispatch caps are 160, 60, 30 and 120 messages/s; configured application delay/jitter and a no-dispatch interval from 1.5 to 3.5 seconds complete the scenarios. Already-published messages may drain after the finite horizon; unsent outbox backlog does not. Nominal service caps do not guarantee achieved throughput because disk commits, acknowledgement waits and Windows scheduling consume time.

The simulation contains 1,200 runs: four/sixteen devices × 2/5/10 Hz × four conditions × ten seeds × five policies. Duration is 60 virtual seconds with five seconds excluded. Its synthetic delay/jitter is keyed by message ID and seed for matched randomness. This model does not implement TCP or MQTT handshakes and is never used to infer simulated QoS packet-loss behavior. Seed-zero raw events are retained for every condition, with per-run records for all repetitions.

Executed host: Windows build 26200, AMD64 family 23/model 8, six physical/twelve logical CPUs, approximately 15.93 GiB RAM; Python 3.10.9, Paho 2.1.0, AMQTT 0.11.3. The package/environment snapshots contain all versions. Broker/subscriber/edge use loopback. During the early live sweep, background native-core/simulation jobs ran on the shared desktop; randomized order reduces systematic policy grouping but does not eliminate host-load confounding. Costs are descriptive measurements, not isolated broker benchmark claims.

## 6. Actual MQTT results

The following table averages QoS within each seed before summarizing seeds. Full QoS-specific tables and paired differences are included in the processed results.

{observed}

![Actual MQTT comparison](../figures/live_comparison.png)

The proposed policy reduces outage mean age by {improvement:.1f}% against FIFO. It restores the all-device one-second age criterion in about {live[(live.scenario=='outage')&(live.policy=='latest')].recovery_seconds.mean():.3f} s after reconnection; all nine FIFO outage runs remain unrecovered at the measurement horizon. This is recovery of held current state, not backlog clearance or complete remote history.

The fair epoch-only baseline matches or slightly exceeds latest-state freshness in the outage/overloaded conditions. Its lack of historical replay is acceptable for this short current-state workload but cannot satisfy a cloud history-completeness requirement. The proposal adds local history and persistence of queued latest state; the current experiment does not demonstrate improved remote archive completeness over that baseline. Differences between QoS levels on this local path do not establish WAN reliability advantages.

Even the nominal healthy condition does not transmit every generated update within the finite horizon. The actual native service rate is limited by desktop scheduling/storage and implementation overhead. The FIFO age gap in healthy runs therefore reflects a measured end-to-end application bottleneck, not intrinsic healthy-network MQTT latency.

## 7. Simulation sensitivity and ablation

At the largest offered load (16 devices × 10 Hz), the complete policy comparison is:

{simtable}

![Simulation comparison](../figures/simulation_comparison.png)

![Load sensitivity](../figures/load_sensitivity.png)

Higher load produces large FIFO age/backlog even when its receipt ratio resembles the proposal's. Expiry reduces queue size but does not reliably preserve per-device freshness in these periodic workloads. Source/service timing aliasing can select a persistent subset of devices, particularly for simulation epoch-only and expiry controls; conclusions against FIFO are stronger than comparisons to those secondary controls.

Removing the sequence guard produces {validation['unguarded_simulation_regressions']:,} regressions across the 240 unguarded runs. The guarded proposal has none. Some conditions show zero guard benefit because they do not reorder same-device updates; all conditions, including these null cases, are retained. The count is an application-model outcome, not an MQTT protocol-violation count. Only current-state queue entries are bounded by device count; local audit storage grows with generated history.

## 8. Runtime, resource and communication costs

{costtable}

Values average all final live runs for each policy. CPU seconds include runner threads/SQLite/sampling, but exclude broker CPU and setup/drain. RSS values are means of sampled per-run peaks. Payload bytes exclude protocol headers/acknowledgements and cannot be called wire bandwidth. The simulation consumes {sim.cpu_seconds.sum():.2f} measured process CPU seconds and {sim.wall_seconds.sum():.2f} wall seconds across its 1,200 runs; each run advances 60 virtual seconds.

The proposal's live queue maximum is four rows; FIFO reaches {int(live[live.policy=='fifo'].max_queue.max())} rows. Comparable average runner RSS/CPU are measured on this host, not evidence of negligible overhead on embedded hardware. Every method uses the common audit path, so the epoch-only baseline is not a minimal publisher implementation. No watts, joules, cloud spend or disk-lifetime claim is made.

## 9. Verification, integrity and evidence

Raw-event and compressed-database checks independently verify {checks['live_generated']:,} generated updates, {checks['live_published']:,} published updates and {checks['live_received']:,} received updates. All 108 database histories contain the expected unique device/sequence pairs. Independent event-integral mean age differs from sampled means by at most {pd.read_csv(ROOT/'results/processed/aoi_verification.csv').absolute_difference.max():.6f} s. Six correctness tests pass for restart persistence, FIFO/TTL semantics, replacement IDs, late-ack safety, fair dispatch, receiver monotonicity and threshold differences.

Paired bootstrap intervals resample whole seed pairs, with 10,000 draws. The three-seed live intervals are exploratory, not population confidence about industrial deployment; no device-time pseudoreplication or global significance claim is used. Pilots with unfair service or earlier dispatch acknowledgement logic are excluded and explicitly labeled. Source/config/evidence SHA-256 manifests, raw traces, dependency pins and regeneration scripts accompany this report.

## 10. Limitations and remaining external work

The reference core is an adapted method reproduction, not exact numerical replication. Its original captures and full Linux/Docker attacks were not reproduced. The native source remains separately fetched because no project-level license was verified. Our application impairment is not TCP loss or a physical outage. The signal/workload is synthetic, clocks are co-located, runs are short, QoS handshakes are local, and desktop sleep resolution/storage alter service capacity. Timing/resource values vary across hosts.

Latest-value coalescing sacrifices intermediate live deliveries. A separate local audit preserves them but does not deliver them remotely. The audit currently has no retention policy. Receiver state and scheduling pointer are not persistent across processes; device epochs and end-to-end application acknowledgements are required for production restart guarantees. SQLite restart unit tests do not constitute physical power-loss tests. Overflow caps were not reached; differing live/model overflow choices are not evaluated.

Instructor/mentor confirmation, official Overleaf integration/access, group registration, human authorship/contribution review and defense remain external. Future Linux netem, actual edge/cloud deployment, archive delivery and hardware/power experiments are explicitly unexecuted. The course's final poster/presentation/submission workflow is separate from this phase report. No paper was submitted and no acceptance is implied.

## 11. Conclusion

This research-phase package reproduces a feasible official MQTT communication core, exposes important paper/code differences, and implements a measurable current-state recovery extension. Under the executed constrained conditions, coalescing materially improves freshness over FIFO while leaving remote completeness as a separate concern. A fair unbuffered policy remains competitive, and established AoI/scheduling literature limits novelty claims. The defensible outcome is a transparent, reproducible evaluation and methodology foundation for instructor review and stronger external validation.

## References

'''+'\n\n'.join(references)+'\n'
    (ROOT/'paper/FINAL_RESEARCH_REPORT.md').write_text(text,encoding='utf-8')

def architecture():
    fig,ax=plt.subplots(figsize=(10,3.6),layout='constrained');ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
    labels=['Synthetic\nphysical state','Edge outbox\nFIFO / latest','MQTT broker\nQoS 0 / 1 / 2','Twin state service\nsequence guard']
    centers=[1.15,3.65,6.15,8.65]
    for x,label in zip(centers,labels):
        ax.text(x,2.8,label,ha='center',va='center',fontsize=11,bbox=dict(boxstyle='round,pad=.65',fc='#edf4f3',ec='#147a79',lw=1.5))
    for a,b in zip(centers[:-1],centers[1:]):ax.annotate('',xy=(b-1.,2.8),xytext=(a+1.,2.8),arrowprops=dict(arrowstyle='->',color='#147a79',lw=1.7))
    ax.text(3.65,1.,'Durable local audit\nEvery generated sample',ha='center',va='center',fontsize=11,bbox=dict(boxstyle='round,pad=.6',fc='#fbf0e8',ec='#cb7848'))
    ax.annotate('',xy=(3.65,1.65),xytext=(3.65,2.2),arrowprops=dict(arrowstyle='->',color='#cb7848',lw=1.5))
    ax.text(7.4,.9,'Measured: age, error, receipts,\nqueue, recovery, CPU and RSS',ha='center',va='center',fontsize=10,color='#344452')
    ax.text(5,3.9,'Deployable edge–cloud roles • executed locally on loopback',ha='center',fontsize=12,color='#147a79')
    fig.savefig(ROOT/'figures/architecture.png',dpi=180);plt.close(fig)

def pdf(source,target):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,Preformatted,KeepTogether
    for name,file in [('Research','arial.ttf'),('ResearchBold','arialbd.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
    pdfmetrics.registerFontFamily('Research',normal='Research',bold='ResearchBold',italic='Research',boldItalic='ResearchBold')
    styles=getSampleStyleSheet()
    body=ParagraphStyle('ResearchBody',fontName='Research',fontSize=9.7,leading=14.2,spaceAfter=8,textColor=colors.HexColor('#263849'))
    head=ParagraphStyle('ResearchHeading',parent=body,fontName='ResearchBold',fontSize=14,leading=18,spaceBefore=14,spaceAfter=8,textColor=colors.HexColor('#147a79'))
    title=ParagraphStyle('ResearchTitle',parent=head,fontSize=23,leading=28,spaceBefore=0,spaceAfter=18)
    small=ParagraphStyle('ResearchTable',parent=body,fontSize=7.8,leading=10.5,spaceAfter=0,wordWrap='CJK')
    def rich(text):
        text=html.escape(text)
        text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:'<link href="'+m.group(2)+'" color="#147a79">'+m.group(1)+'</link>',text)
        text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
        text=re.sub(r'`([^`]+)`',r'<font size="9">\1</font>',text)
        text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',text)
        return text
    lines=source.read_text(encoding='utf-8').splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('!['):
            match=re.search(r'\]\(([^)]+)\)',line)
            path=(source.parent/match.group(1)).resolve()
            im=Image(str(path));scale=490/im.imageWidth;im.drawWidth=490;im.drawHeight=im.imageHeight*scale
            story.extend([Spacer(1,8),im,Spacer(1,10)]);i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.match(r'^:?-+:?$',c) for c in cells):rows.append([Paragraph(rich(c),small) for c in cells])
                i+=1
            n=len(rows[0]);tab=Table(rows,colWidths=[490/n]*n,repeatRows=1,hAlign='LEFT')
            tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceceb')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#147a79')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f7')])]))
            story.extend([tab,Spacer(1,10)]);continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));story.append(Paragraph(rich(line.lstrip('#').strip()),title if level==1 else head));i+=1;continue
        if line.startswith('```'):
            i+=1;code=[]
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            story.append(Preformatted('\n'.join(code),ParagraphStyle('Code',fontName='Courier',fontSize=7.5,leading=10)));i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![','```')):
            paragraph.append(lines[i].strip());i+=1
        story.append(Paragraph(rich(' '.join(paragraph)),body))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#d0dadf'));canvas.line(48,40,A4[0]-48,40)
        canvas.setFont('Research',8);canvas.setFillColor(colors.HexColor('#657580'))
        canvas.drawString(48,27,'DT–MQTT resilience | research-phase evidence | 7 October 2026')
        canvas.drawRightString(A4[0]-48,27,str(doc.page))
    SimpleDocTemplate(str(target),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=45,bottomMargin=53,title=source.stem.replace('_',' '),author='DT-MQTT research project').build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    architecture();report()
    pdf(ROOT/'paper/FINAL_RESEARCH_REPORT.md',ROOT/'paper/FINAL_RESEARCH_REPORT.pdf')
    pdf(ROOT/'docs/INITIAL_REPRODUCTION_AUDIT.md',ROOT/'paper/INITIAL_REPRODUCTION_AUDIT.pdf')
    print('Created initial audit and final research-phase report')
