# Research methodology and implementation

## Study design

This study evaluates the telemetry-synchronization subsystem of a cloud-enabled digital twin: generated physical-state samples → edge staging/outbox → MQTT broker → cloud-side current-state receiver. The receiver and broker are independently deployable processes; the executed experiment places both on the same Windows host. A future remote deployment is supported architecturally but not claimed as measured cloud performance.

The reference's unchanged MQTT functions establish an executable provenance baseline. Our clean implementation then defines current-state semantics absent from that source and evaluates several application buffering policies. These policy baselines are explicitly **our experimental controls**, not methods attributed to the reference article. The research is a method reproduction plus a separate systems extension; original packet-level numerical results are unavailable.

## Message and state model

Each message is `(run, device, seq, generated, value)`; run is isolated through the MQTT topic, and sequence IDs strictly increase for each device. Generation timestamps use one monotonic clock in the live test and one virtual clock in simulation. `value = sin(0.3 × generated + device)` provides continuous, unitless ground truth. This is a current-state mirror, not a physics-based or closed-loop predictive twin.

At time `t`, the receiver stores a value with generation time `u_d(t)`. The per-device Age of Information is `A_d(t) = t - u_d(t)`. Mean AoI averages over devices and equally spaced/approximately 20-ms observation times after warm-up. Stale fraction is the fraction of device-time observations with age greater than one second. That threshold is an experimental choice, not an industrial SLA. The p95 age is a pooled device-time percentile, not the percentile of run means. MAE compares held twin values with the analytical current signal.

Synchronization latency is receipt time minus nominal generation time, including edge wait and injected application delay. Delivery ratio is unique received `(device,seq)` pairs divided by all generated pairs within the finite run. Intentional coalescing/expiry counts as non-delivery. Local audit completeness is recorded separately. Duplicate count is total receipts minus unique pairs; state rejection is a sequence check and is not synonymous with a duplicate MQTT packet.

Recovery time is the first post-outage observation for which **all** device ages are at most one second, minus outage end. Missing recovery values are censored at run end; do not average only recovered runs without reporting the number censored. Maximum queue is the largest observed live outbox occupancy. Pending dispatch snapshots add volatile memory and can make total outstanding work larger than the current-state outbox bound.

## Policies

**Epoch-only staging (`no_buffer`).** A sample is eligible during its current sampling epoch; remaining staged samples are dropped at the next generation epoch and during outage. The live implementation rotates device emission order so constant device priority cannot create a permanent advantage. A SQLite audit is kept for common accounting, so this is a logical no-replay baseline, not a minimal-memory industrial publisher. The simulation uses staggered phases and a literal one-tick opportunity; its timing aliasing makes this secondary baseline less comparable than FIFO.

**FIFO (`fifo`).** Each generated update enters the durable outbox. Oldest queued updates are sent first. The same receiver guard is used as for the proposal. At a finite horizon, backlog remains undelivered. Sustained input above service capacity has no stable unbounded-FIFO regime; the 10,000-record cap uses drop-oldest in live SQLite and drop-newest in the simulation. The cap is not reached in the executed final configurations; those unexercised overflow policies must not be compared as equivalent.

**Expiry (`ttl`, simulation ablation).** FIFO entries older than one second are removed before dispatch. This distinguishes discarding stale work from retaining the newest state per device. Expiry alone does not ensure fair coverage of devices when periodic service and source schedules interact.

**Proposal (`latest`).** First persist every generated update in an append-only local audit table. Within the outbox, replace any older queued update for the same device with the newest one. A round-robin pointer chooses the next eligible device, preserving fair service under continual replacement. A receiver accepts only sequence IDs strictly larger than the stored ID. Existing delayed snapshots may still arrive out of order; the guard prevents rollback. Coalescing does not apply to commands, alarms, transactions or events where every occurrence matters.

The current outbox has at most one queued row per device. SQLite WAL and FULL synchronization provide persistence for committed rows. A transport snapshot is acknowledged/deleted only after Paho reports publication complete; QoS 0 means local send completion, and QoS 1/2 mean their publisher-to-broker handshake. These are not cloud-application acknowledgements. A crash between broker acceptance and deletion can cause retransmission; receiver sequence checks suppress repeat application. A coalesced snapshot already in flight may be obsolete, and local audit rows do not prove remote archival completeness. Receiver state and the round-robin pointer are in memory; cross-process receiver restart and session reset are limitations, not tested guarantees.

**Guard ablation (`latest_no_guard`, simulation).** Keep the same coalescing and scheduling but accept older arrival sequences. This isolates receiver monotonicity. A distinct unit test validates suppression and demonstrates rollback without the guard.

## Matched conditions and statistical analysis

Simulation: 2 device scales × 3 generation rates × 4 scenarios × 10 seeds × 5 policies = **1,200 executions**, each 60 virtual seconds. Metrics exclude the first five seconds. Per-message jitter uses a seed keyed by device/sequence so policy order does not change the underlying impairment of a shared message. Network capacities/delays/outage intervals are saved in the config. This is an application queue/arrival model, not ns-3, TCP or an MQTT protocol emulator; no QoS values are assigned to simulated packet-loss probabilities.

Live: 3 seeds × 3 actual MQTT QoS settings × 4 scenarios × 3 policies = **108 executions**, each six wall-clock seconds plus setup/drain. Four devices emit 20 Hz each; metrics exclude one second. Scenarios cap submissions at 160/60/30/120 messages per second, with configured delay/jitter and a two-second no-dispatch interval in the outage condition. Actual throughput can be lower because disk commits, acknowledgement waits and operating-system sleep resolution contribute overhead. Setup waits for the subscription acknowledgement. Published messages drain after the run; unsent outbox messages do not. Run order is randomized with a recorded shuffle seed.

Three live repetitions give exploratory evidence only. Paired differences use common seed/scenario/QoS. Percentile bootstrap intervals resample whole paired runs (10,000 draws); they do not treat device-time samples as independent observations. No hypothesis-test significance or multiplicity correction is claimed. QoS overview plots first average each seed across QoS, then summarize seeds; QoS-specific tables remain available. Deterministic signals and seed-controlled jitter restrict external validity.

## Runtime, resources and communication

Live wall time uses a monotonic clock; CPU time is process CPU consumed during the measured loop and includes publisher/subscriber threads, SQLite and sampling. Reported CPU excludes the broker process and setup/drain. RSS is sampled approximately every 20 ms for the runner and broker; it is an observed peak, not a guaranteed absolute peak. Payload bytes are actual serialized application bytes submitted to MQTT, excluding MQTT/TCP/IP headers, acknowledgements, retransmissions and storage overhead. They must not be called wire bandwidth. SQLite database size/audit rows and queue occupancy represent local storage, not remote cloud cost or power consumption.

The live sweep was randomized while the simulation/native core ran concurrently during its early portion. Hardware is a shared desktop; CPU/RSS measurements are descriptive costs under that recorded environment, not isolated broker benchmarks. The OS, CPU, RAM, package versions, execution order and configuration are retained. Linux tc/netem and original Docker attack experiments were not executed. No hardware energy, wireless loss or public-cloud billing measurement is reported.

## Verification and provenance

Correctness tests exercise restart persistence of committed outbox rows, FIFO order, replacement identity, late-ack safety, fair service under continual replacement, TTL boundary and monotonicity. Non-reused SQLite IDs prevent an old publication acknowledgement deleting a newer coalesced row. An independent event-integral calculation checks live mean AoI against the sampled result. Analysis asserts every final live generated update is in the local audit, every published update reached the subscriber and guarded state never regressed. Raw traces, per-run metrics, SQLite snapshots, pilot exclusions, source hashes and artifact checksums support inspection. Native reference logs retain original behavior and explicit adapter repairs.
