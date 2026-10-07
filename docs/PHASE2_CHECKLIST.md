# Research phase checklist — 7 October 2026

Derived from the recovered instructor guide (sections 10, 12–14, 23–27), the supplied next-phase instructions, and the user's execution brief. This is a research working package; course submission and instructor approval are separate.

- [x] Verify recent baseline paper, venue, official artifacts, licenses, dependencies and hardware.
- [x] Compare candidate papers and justify selection without overstating reproducibility.
- [x] Record architecture, cloud component, datasets/workloads, metrics and original settings.
- [x] Preserve upstream baseline and version; implement/run feasible core methodology.
- [x] Record all deviations, unavailable experiments and troubleshooting.
- [x] Build a verified thematic literature matrix (target 15–20 academic papers).
- [x] Define defensible gap, refined research question and 2–4 objectives.
- [x] Design and implement improvement; preserve baseline independently.
- [x] Run matched repeated baseline/proposed comparisons, ablations and sensitivity checks.
- [x] Retain raw events, processed tables, seeds, environment and integrity hashes.
- [x] Quantify timing, memory, communication and queue costs with clear measurement boundaries.
- [x] Generate figures and independently check reported numbers.
- [x] Provide dependency pins, runnable commands and meaningful correctness checks.
- [x] Write initial reproduction audit and final reproduction/methodology report.
- [x] Update README, research notes, progress and honest contribution log.
- [x] Publish reviewable GitHub changes and verify public artifacts.
- [x] Record external tasks: topic/mentor approval, official Overleaf template/access, registration, human understanding/defense, future scholarly submission.

## Execution plan

1. Audit: recover source instructions, inspect proposal/repository and runtime capabilities; save this checklist before implementation.
2. Selection: search primary publications and official repositories; select the most defensible recent paper, record rejected alternatives and reproducibility limitations.
3. Reproduction: pin upstream artifacts; run what can be measured locally. Do not substitute a simulation for a hardware result without labeling it.
4. Contribution: use observed limitations plus literature to formulate a narrow freshness-versus-completeness gap; implement a matched original baseline and improvement.
5. Evaluation: run repeated seeded conditions (healthy, degraded, overloaded, outage/recovery), QoS variants where real MQTT is available, ablations and resource measurements. Preserve unfavorable outcomes.
6. Analysis: compute paired uncertainty, delivery and freshness independently; save tables and figures with provenance.
7. Writing/release: compile a review-ready report with architecture, equations, methods, results, discrepancies and threats; publish code/results/docs and state remaining external requirements.

## Known constraints at audit

The original guide is available as a local DOCX; its text was recovered. Docker CLI exists but the Linux engine connection failed. No experiment code existed in the repository at start. Baseline selection is not yet complete. Missing instructor workflow text in the chat preview must not be reconstructed as invented instructions.

## Completion status

All research-package tasks above are completed within their documented scope. Recording an unavailable experiment is not performing it. Additional evidence now includes the official Linux/Docker topology with HTTP injection, command-modifying proxy and a bounded HTTP flood, plus 36 real packet-impairment MQTT runs. Mentor approval is reported by the user. Complete Overleaf LaTeX/image ZIP and cloud deployment scripts are prepared. Exact published numerical replication, optional physical hardware and official Overleaf/template/submission steps remain as detailed in `EXTERNAL_REQUIREMENTS.md`. The original 1,200 simulations, 108 local MQTT runs and native core evidence are retained.

All 36 AWS Internet runs are now completed and audited. Temporary cloud resources were deleted after local evidence transfer. The six-page initial reproduction report and final report with AWS results are delivered alongside complete Overleaf source packages.
