# External requirements and experiments not claimed as completed

## Research experiments

| Item | Status | Why it is external/unavailable | Prepared route |
|---|---|---|---|
| Exact reference Table 2 / Figures 4–6 | Not reproduced | No original CSV/PCAP found; source calibration/rule differs from paper; executed bounded scenarios are not exact numerical replication | Official-source Docker topology now runs; raw logs and differences are retained |
| Official Docker attack scenarios | Executed with disclosed adaptations | HTTP injection, command-modifying proxy and bounded single-worker HTTP flood completed in a private internal network | `results/linux_attacks_attempt2/`, `scripts/run_linux_baseline.py` and independent checks |
| TCP loss/jitter with netem | Executed locally | 36 real-MQTT runs with Linux packet delay/loss, raw PCAP and qdisc counters; not a real WAN | `results/linux_netem/` and independent event-integral analysis |
| AWS cloud WAN | Access/setup pending | User has an AWS account; no authenticated console/remote VM access verified yet | AWS sign-in handoff; bootstrap, SSH-tunnel receiver/publisher and setup guide prepared; six local integration checks passed |
| Physical IoT hardware | Optional future validation | No sensor available; simulated edge workload is sufficient for scoped synchronization study | Prepared ESP32/DHT22 firmware; do not claim physical measurements or require purchase absent an instructor requirement |
| Cloud archive completeness | Not implemented/evaluated | All updates retained locally only; remote audit delivery is separate | Add an independently acknowledged, bandwidth-budgeted archive channel |
| Power/energy measurement | Not measured | CPU/RSS are not watts/joules | Add a calibrated power meter/hardware counter before energy claims |
| Production restart/end-to-end exactly-once | Not established | Source state and scheduler pointer are in memory; publisher acceptance differs from twin commit | Add persistent device epochs and receiver acknowledgements and inject real process crashes |

## Course and human responsibilities

The recovered instructor guide requires topic approval, a shared Overleaf project using the official template, registered group/student identifiers, appropriate instructor access, instructor review and eventual scholarly submission. Their completion cannot be inferred from a repository or from this AI-assisted research package.

- Mentor approval is confirmed by the user on 7 October 2026. This records team-reported approval, not final manuscript acceptance or verification of a mentor message.
- Enter the official group number, both student IDs, institutional details and status in the instructor's Google Sheet. No Sheet URL or verified registration was provided in this execution.
- Import `paper/overleaf_upload.zip` into Overleaf. It contains complete LaTeX, references and four figures; see `docs/OVERLEAF_UPLOAD.md`. Built-in compilation failed with a platform error; verify Overleaf compilation and official-template compatibility. Verify both student and instructor access. No Overleaf project was shared by this execution.
- Review and correct authorship, affiliations and each student's substantive contribution. The contribution log records AI assistance transparently and does not assign unperformed student work.
- Read and defend the code, assumptions, observed trade-offs and unavailable experiments. A defense guide is included.
- Complete any further experiments required by instructor feedback before claiming publication readiness. Select a suitable journal, verify its current requirements and obtain instructor review before submission. No manuscript was submitted and no acceptance is claimed.
- Final course poster, oral presentation, final-template PDF and submission evidence belong to the later formal submission workflow; the PDFs produced here are initial/final research-phase reports.

This task completes the feasible research-phase implementation/evaluation package, with these explicit limits. It does not certify the entire 100-day course or reproduce unavailable original-paper numerical evidence.
