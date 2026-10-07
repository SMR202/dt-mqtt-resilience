> Historical initial audit. Later Linux and AWS execution supersedes availability notes below; see `paper/INITIAL_REPRODUCTION_REPORT.md` and `docs/AWS_WAN_VALIDATION.md` for current evidence.

# Initial reproduction report and feasibility audit

Audit date: 7 October 2026. This report precedes final analysis and distinguishes published methods, official code and our extension.

## Selection decision

Rodrigues et al., **A Data Rate Monitoring Approach for Cyberattack Detection in Digital Twin Communication**, *Sensors* 25(24), 7476, published 9 December 2025, DOI [10.3390/s25247476](https://doi.org/10.3390/s25247476), is the selected reference baseline. Its publication is independently verified by [PubMed](https://pubmed.ncbi.nlm.nih.gov/41471470/). It is a recent peer-reviewed journal article, not claimed to be a top-tier systems venue. The [official repository](https://github.com/woliveira1728/digital-twin) is linked in the article's data-availability statement and identifies the same article in its README. It fits the existing topic through MQTT-mediated physical/virtual telemetry and communication resilience. Its security focus differs from our recovery/freshness contribution; we retain that distinction.

## Published-method summary

The reference monitors communication rates using a mean-plus-three-standard-deviations threshold. Its Docker topology connects a synthetic device, MQTT broker, twin, monitor and controlled attack components. Reported observables are PPS/BPS; the healthy recording is described as 60 minutes. The paper specifies Ubuntu 24.04.3, Docker 28.4.0, Compose 2.39.4, Python 3.12, Paho 1.6.1, Requests 2.32.3, OPC-UA 0.98.13 and aiocoap 0.4.3. It evaluates DoS, active MiTM and intrusion; Table 2 provides scenario statistics. A precise CPU/RAM specification, original packet captures and repeat-run seeds were not located. The publicly readable [article record](https://pmc.ncbi.nlm.nih.gov/articles/PMC12736672/) and the Europe PMC full-text XML were checked. The containerized twin is a deployable service; the published evaluation is not evidence of deployment on a public cloud.

## Official-artifact audit (findings from code inspection)

Pinned commit: `43346f60a9f41392611242ff3cb7589d7a758aa7`.

| Check | Finding | Consequence |
|---|---|---|
| Source provenance | Article data-availability link matches repository/README | Official research artifact verified |
| License | No project-level LICENSE found; only bundled dependency licenses | Fetch privately; do not redistribute/relicense author code |
| Data | Synthetic device generator; no separate author CSV/PCAP found outside committed venv | Generate our own traces; Table 2 cannot be exactly recomputed |
| Dependencies | Dockerfiles use Python 3.10-slim and mostly unpinned pip installs | Different from paper's Python 3.12; native adapter pins packages |
| Paho | Source uses CallbackAPIVersion, unavailable in paper's specified 1.6.1 | Use 2.1.0; document discrepancy |
| Detection rule | `stats_monitor` compares rates to calibration maxima | Preserve code behavior; independent paper-rule implementation alongside it |
| Capture boundary | MQTT callbacks increment message counts and payload bytes | These are application messages/s and payload bytes/s, not all wire packets/bytes |
| Calibration | Device sleeps 15 + 3×(15+2) = 66 seconds, disabling sensors in turn | Different from healthy 60-minute recording |
| Completion signal | Native attempt did not receive final calibration message before publisher disconnect | Failed log retained; adapter resends only this message with network loop/QoS1 |
| Native log encoding | Unicode arrows fail with default Windows file encoding | Adapter writes UTF-8 logs |
| State storage | Receiver prints payloads; timestamp/sequence ordering is absent | Extension explicitly adds timestamped current-state semantics |

## Candidate comparison

| Candidate | Advantages | Reason not selected as executable primary |
|---|---|---|
| [An et al., ICT Express 2025](https://www.sciencedirect.com/science/article/pii/S2405959525000013) | Direct MQTT/UAV digital-twin topic and recent journal | Official code/dataset not located; publisher full-text request returned 403 |
| [Cakir et al., IEEE CAMAD 2023](https://doi.org/10.1109/CAMAD59638.2023.10478422) | Direct synchronization study and alignment metric | Older; no official simulation code found in checked sources; ns-3 topology not equivalent to MQTT buffering |
| [Dizdarevic et al., 2023 preprint](https://arxiv.org/abs/2305.13893) | Author-linked [MQTT broker testbed](https://github.com/michalke-it/benchmarking_os_mqtt_brokers_2023), useful impairment methodology | Peer-reviewed venue not verified; KVM/Nebula/JMeter/hardware requirements; README inherited BenchFaaS content |
| [ComBench, VALUETOOLS 2021](https://doi.org/10.1007/978-3-030-92511-6_5) | Official [code](https://github.com/DescartesResearch/ComBench), configurable workloads | Older and protocol benchmarking rather than a recent twin application |
| [Neagu et al., Future Internet 2026](https://doi.org/10.3390/fi18030137) | Recent operational-twin resilience | Node failover rather than MQTT current-state replay; official executable repository not located in checked sources |

These searches establish feasibility within inspected sources, not proof that no unpublished code exists. Newer IEEE freshness literature informs the contribution even though its optimization algorithms are not the executable baseline.

## Reproduction scope

Run original sensor, MQTT receiver, MQTT monitor and rate-monitor functions with a native adapter, retaining original bodies and calibration timing. Replace the broker with loopback AMQTT and omit unrelated multiprotocol servers. Exercise a benign high-rate sensor burst. Record code hashes, observer events, monitor logs and adaptation details. Implement the paper's statistical rule independently and compare it with the source's maximum rule.

**Do not claim:** exact Table 2 reproduction, attack-detection accuracy, public-cloud performance, real packet-loss experiments, physical PLC tests, Raspberry Pi energy measurements or all upstream protocols. Docker engine was unavailable initially and remained unresponsive after a launch attempt. Linux tc/netem is not available for this Windows native test. No measured value is copied from the paper as a result of our runs.

## Contribution hypothesis

A rate-only monitor and FIFO replay can treat many old updates as successful communication while the current state remains stale. Test a latest-state outbox with fair service and a monotonic receiver against FIFO, epoch-only staging and expiry. Retain all generated updates in a separate local audit log; count intentional live-update suppression transparently. This is a scoped systems evaluation built on known freshness ideas, not a claim to have invented Age of Information or last-generated-first-served scheduling.
