# Executed Linux validation

## Scope and observed evidence

Ubuntu/WSL2 is present. Docker Desktop could not start its engine. Official Ubuntu packages were downloaded and extracted to `/var/lib/dt-research-runtime` without installing a system Docker service. A separate Docker 29.1.3 daemon used `/var/lib/dt-research-engine/docker.sock` and a dedicated data directory. Attack containers used an internal private bridge, no host port mappings, resource limits and explicit host entries. Initial DNS failure is preserved in `results/linux_attacks_attempt1/`; the successful run is `results/linux_attacks_attempt2/`.

The official Python method bodies and Dockerfiles were not edited. Current dependencies differ from the paper and are recorded. Original calibration completed. HTTP injection produced three device shutdowns; the command-modifying proxy produced one modification and one device shutdown. A single-worker five-second HTTP flood produced 1,033 logged command receipts and 14 rate alerts; maximum monitor-reported rate was 237 application messages/s. These are fresh bounded-experiment observations, not the paper's 60-minute healthy baseline, full flood defaults, wire-packet metrics or exact Table 2 numbers.

The additional netem study has 36 completed runs: three seeds × three QoS levels × FIFO/latest × healthy/delay-loss, with four devices at a nominal 5Hz and a common 12/s application dispatch cap. Linux qdisc on isolated loopback applies 100ms delay, 20ms jitter and 2% configured loss to both MQTT connections. Raw PCAP and qdisc logs are retained. Actual qdisc drops total 87. All 4,248 generated samples match SQLite audit histories; all 1,527 published messages were received. TCP retransmission/finite-horizon edge suppression separate packet loss from application receipt ratio.

**Use `results/processed/linux_netem_verified.csv` and `linux_netem_summary.csv` for age comparisons.** Blocking acknowledgement waits made in-loop samples irregular; sampled means differ from event-integral means by up to 0.504s. The independent calculation integrates actual held generation times across all four devices over seconds 1–6. This is real packet impairment in a single local namespace, not actual Internet/WAN or physical-device validation.

## Repeat on a normal Linux Docker host

First fetch the official pinned source with `scripts/fetch_baseline.py`. Use a new output directory; scripts reject reusing evidence. Python 3 and Docker Compose are required.

```bash
python3 scripts/run_linux_baseline.py --upstream work/upstream-digital-twin --out work/new-linux-attacks --compose docker-compose
docker build --network host -f configs/Dockerfile.netem -t dt-research-netem .
docker run --rm --name dt-research-netem --network none --cap-add NET_ADMIN --cap-add NET_RAW -e DT_PRIVATE_NETNS=1 --cpus 2 --memory 1g -v "$PWD:/research" dt-research-netem
```

The netem script deliberately uses `results/linux_netem` and refuses to overwrite existing evidence. Run from a fresh clone/output workspace or alter its output path before repetition. `run_linux_baseline.py` expects the standalone `docker-compose` executable; with the modern plugin use its executable path or a small local wrapper forwarding to `docker compose`. Fixed subnet/project name requires no concurrent baseline run. Inspect the generated compose configuration before execution; it exposes no ports. End with the runner's normal cleanup. Never direct these scenarios at public or third-party services.

`scripts/analyze_extensions.py` checks retained raw evidence and regenerates summaries. Early Docker builds/attacks shared the PC with part of the netem sweep; CPU limits and resource timings are descriptive, not isolated hardware benchmarks. Six cloud-script smoke tests remain in `results/processed/cloud_smoke_checks.json` and are local functional verification only.
