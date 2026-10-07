# dt-mqtt-resilience

## Research title
Evaluating MQTT QoS and Edge Buffering Strategies for Resilient Cloud-Based Digital Twin Synchronization Under Unstable Networks

## Research question
How do MQTT Quality of Service levels and durable edge buffering strategies affect the freshness, reliability, latency, consistency, and communication overhead of cloud-based Digital Twin synchronization under unstable network conditions?

## Status
Cloud Computing research phase: implementation and local evaluation completed on 7 October 2026. This is a preliminary research package for instructor review, with explicitly limited reproduction scope.

## Executed evidence

- Feasible MQTT core of the official 2025 Sensors reference executed with a documented native adapter; original numerical attack results are **not reproduced**.
- **108 real MQTT loopback runs** (QoS 0/1/2, four application-shaped conditions, three policies, three seeds).
- **1,200 application-simulation executions**, including load/scale sensitivity, expiry and receiver-guard ablations.
- All **51,840** live-test generated samples independently verified in local audit histories; all **26,247** published messages received.
- In the live outage condition, mean state age is **1.852 s with FIFO** and **0.503 s with latest-state replay** (72.8% reduction); delivery is approximately 54% for both within the finite horizon.
- A fair epoch-only baseline reaches similar freshness. Local history completeness, remote live completeness and state freshness are reported separately. No universal advantage is claimed.

## Start here

- [Checklist and execution plan](docs/PHASE2_CHECKLIST.md)
- [Final research-phase report (PDF)](paper/FINAL_RESEARCH_REPORT.pdf) · [editable Markdown](paper/FINAL_RESEARCH_REPORT.md)
- [Initial reproduction audit (PDF)](paper/INITIAL_REPRODUCTION_AUDIT.pdf) · [audit details](docs/INITIAL_REPRODUCTION_AUDIT.md)
- [16-paper literature comparison and research gap](docs/LITERATURE_REVIEW.md)
- [Methodology](docs/METHODOLOGY.md)
- [Reproduction instructions](docs/REPRODUCING.md)
- [Raw live evidence](results/live) · [simulation evidence](results/simulation) · [processed results](results/processed)
- [Figures](figures) · [external/unexecuted requirements](docs/EXTERNAL_REQUIREMENTS.md)

The measured cloud-side role is co-located on this host. Uplink impairments are application dispatch limits/delays, not TCP packet-loss injection or a paid-cloud WAN experiment. The selected reference has paper/code/version/capture discrepancies; read the audit before citing reproduction success. Its source is fetched separately because no project-level license was verified. Our original implementation remains MIT.

## Quick verification

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python scripts/check_integrity.py --verify
.venv\Scripts\python scripts/verify_evidence.py
.venv\Scripts\python scripts/analyze.py
```

On Linux/macOS, use `.venv/bin/python`. Full rerun commands and preservation of delivered evidence are explained in the reproduction guide. Dependencies for fetching/executing original MQTT functions and generating the PDFs are separate optional files. The predecessor proposal and its references are retained as historical material; `paper/phase2_references.bib` contains this phase's verified reference set.

## Planned architecture
Physical asset simulators → edge gateway → MQTT → cloud Digital Twin state service → metrics/results store.

## Factors
- MQTT QoS: 0, 1, 2
- Durable edge buffering: off/on
- Network: baseline, degraded, severe, outage/recovery
- Workload scale: fixed after pilot testing

## Primary metrics
- Synchronization latency
- Age of Information / twin staleness
- Delivery ratio
- State consistency / synchronization error
- Bandwidth
- Duplicate updates
- CPU/memory
- Buffer occupancy
- Recovery time
- Backlog clearance rate

## Planned repository structure
- `src/` implementation
- `configs/` experiment definitions
- `scripts/` run and analysis scripts
- `data/` dataset/trace documentation
- `results/` processed results and reproduction instructions
- `figures/` generated figures
- `docs/` proposal and research documentation
- `paper/` manuscript helpers and BibTeX; the official manuscript remains in Overleaf

## Reproducibility
All experiment parameters, seeds, software versions, scripts, and result-generation steps will be documented. Secrets, credentials, private data, and cloud tokens must never be committed.

## Authors
- Muhammad Sameer
- Humayun Bilal

## License
MIT for repository code unless the team/instructor later selects a different compatible license.

Upstream reference code is not redistributed or relicensed. AI-assisted work is documented honestly in the contribution log. Overleaf registration/access, mentor/instructor approval and scholarly submission are external and are not asserted as completed.
