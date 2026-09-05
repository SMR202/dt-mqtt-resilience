# dt-mqtt-resilience

## Research title
Evaluating MQTT QoS and Edge Buffering Strategies for Resilient Cloud-Based Digital Twin Synchronization Under Unstable Networks

## Research question
How do MQTT Quality of Service levels and durable edge buffering strategies affect the freshness, reliability, latency, consistency, and communication overhead of cloud-based Digital Twin synchronization under unstable network conditions?

## Status
Cloud Computing 100-Day Research Assignment — Cutoff 1.

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
