# Research progress — 7 October 2026

## Completed in this execution

1. Recovered the original instructor DOCX and mapped the research-phase plan to its literature/methodology/reproducibility/integrity requirements before implementing code.
2. Inspected the initially proposal-only repository and preserved that proposal history.
3. Verified a recent peer-reviewed reference, official artifact link, pinned source version, dataset generator, dependencies, license absence and feasibility constraints. Documented rejected alternatives.
4. Executed original MQTT function bodies through a native adapter, retained a failed run, repaired a missing calibration signal and recorded 283 observed events plus a 200-message benign burst. Exact original attack/PPS figures remain unexecuted.
5. Built a verified 16-paper thematic matrix; refined the RQ and 4 objectives without claiming freshness/coalescing as new ideas.
6. Implemented FIFO, epoch-only staging, expiry, fair latest-state coalescing, local durable audit and a monotonic receiver. Added non-reused row IDs and transport-completion acknowledgement safeguards.
7. Detected unfair service in pilots, preserved exclusions and reran the final comparison. Fixed live emission priority to rotate among sensors.
8. Completed 1,200 seeded 60-second application simulations and 108 six-second actual MQTT runs across QoS 0/1/2, workloads and conditions.
9. Produced complete raw records, seed-zero simulation events, all live events, compressed SQLite histories, environment/configuration/order snapshots, processed comparison/ablation/paired/resource tables and publication-style plots.
10. Independently verified every live database/event count and event-based mean AoI. Six meaningful correctness tests pass. Guard ablation demonstrates 5,945 simulation regressions; null conditions remain reported.
11. Prepared initial and final PDF/Markdown research reports, standalone methodology, verified BibTeX, reproduction instructions, defense notes, citation metadata and honest contribution records.

## Principal findings

Latest-state replay improves mean state age over FIFO under our measured backlog conditions. In the live outage, age is 0.503 s versus 1.852 s, while finite-horizon delivery is approximately 54% for both. All latest/epoch-only runs recover the all-device age threshold quickly; no FIFO outage run recovers before run end. The fair epoch-only baseline can match latest-state freshness. Audit completeness is local; remote history is not complete. This is a measured trade-off, not a universal improvement.

The actual live generator writes 51,840 samples to audit histories; 26,247 are published and all arrive. Low delivered/generated ratios represent unsent backlog or intentional suppression, not observed MQTT transport loss. Resource costs are measured on a shared desktop with scheduling/storage limits, not a controlled edge hardware benchmark.

## Publication boundaries

Only final `results/live` and `results/simulation` feed headline analysis. Interrupted pilots are labeled and excluded. Original source is fetched privately; no unlicensed author code is placed under our MIT license. Logs are included as text. SHA-256 manifests identify final artifacts. A review branch/PR carries the package, preserving the original main proposal until human review.

## Outstanding external items

See `EXTERNAL_REQUIREMENTS.md`: original Linux/Docker numerical/attack experiments, netem packet impairment, actual edge/cloud WAN/hardware/power tests, end-to-end archive/restart guarantees and instructor/Overleaf/registration/submission responsibilities. These are not silently marked done.
