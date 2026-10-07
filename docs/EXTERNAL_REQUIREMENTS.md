# External requirements and experiments not claimed as completed

## Research experiments

| Item | Status | Why it is external/unavailable | Prepared route |
|---|---|---|---|
| Exact reference Table 2 / Figures 4–6 | Not reproduced | No original CSV/PCAP found; official code differs from stated method; original Linux/Docker topology not executed | Pinned fetch script, dependency audit and native core evidence provided |
| Original multiprotocol attacks | Not executed | Native run exercises MQTT only; Docker engine was unavailable/unresponsive | Official repository retains authors' topology; isolate a future Linux deployment |
| TCP loss/jitter with netem | Not executed | Windows host has no Linux network emulator available | Repeat on Linux with per-hop tc/netem and recorded captures; do not interpret application delay as packet loss |
| Paid-cloud WAN / physical IoT hardware | Not executed | No authorized remote instance, physical devices or measured WAN path | Deploy subscriber/broker independently and repeat configurations on real edge/cloud hosts |
| Cloud archive completeness | Not implemented/evaluated | All updates retained locally only; remote audit delivery is separate | Add an independently acknowledged, bandwidth-budgeted archive channel |
| Power/energy measurement | Not measured | CPU/RSS are not watts/joules | Add a calibrated power meter/hardware counter before energy claims |
| Production restart/end-to-end exactly-once | Not established | Source state and scheduler pointer are in memory; publisher acceptance differs from twin commit | Add persistent device epochs and receiver acknowledgements and inject real process crashes |

## Course and human responsibilities

The recovered instructor guide requires topic approval, a shared Overleaf project using the official template, registered group/student identifiers, appropriate instructor access, instructor review and eventual scholarly submission. Their completion cannot be inferred from a repository or from this AI-assisted research package.

- Confirm the revised RQ and baseline with the instructor/mentor. No approval is asserted.
- Enter the official group number, both student IDs, institutional details and status in the instructor's Google Sheet. No Sheet URL or verified registration was provided in this execution.
- Import the review-ready report and methodology into the existing shared Overleaf manuscript and official template. Verify both student and instructor access. This run does not create, modify or share an Overleaf project.
- Review and correct authorship, affiliations and each student's substantive contribution. The contribution log records AI assistance transparently and does not assign unperformed student work.
- Read and defend the code, assumptions, observed trade-offs and unavailable experiments. A defense guide is included.
- Complete any further experiments required by instructor feedback before claiming publication readiness. Select a suitable journal, verify its current requirements and obtain instructor review before submission. No manuscript was submitted and no acceptance is claimed.
- Final course poster, oral presentation, final-template PDF and submission evidence belong to the later formal submission workflow; the PDFs produced here are initial/final research-phase reports.

This task completes the feasible research-phase implementation/evaluation package, with these explicit limits. It does not certify the entire 100-day course or reproduce unavailable original-paper numerical evidence.
