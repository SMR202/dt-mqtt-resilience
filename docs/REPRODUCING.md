# Reproduction instructions

## Environment

Python 3.10 and Git. Core analysis dependencies are pinned in `requirements.txt`; the complete executed environment including optional baseline packages is `requirements-lock.txt`. No GPU, paid cloud account or physical device is needed for the completed local experiments. The broker binds to `127.0.0.1` on private research ports 18884/18885. Do not reuse a public/shared broker.

```text
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
# Linux/macOS: substitute .venv/bin/python for .venv\Scripts\python
```

## Verify the delivered evidence

```text
.venv\Scripts\python scripts/check_integrity.py --verify
.venv\Scripts\python scripts/verify_evidence.py
.venv\Scripts\python scripts/analyze.py
```

The first command checks delivered bytes. The second independently checks raw live counts and every compressed SQLite audit; the third regenerates processed tables, exploratory paired intervals, figures and event-based AoI checks. Hashes of analysis-generated PNG/PDF outputs may vary across matplotlib/font/library platforms; raw evidence is the reference. Install the executed lockfile on a matching Python/OS if identical rendering is important.

## Regenerate experiments without overwriting delivered evidence

```text
.venv\Scripts\python scripts/live.py --output work/replay_live
.venv\Scripts\python scripts/simulate.py --output work/replay_simulation
```

The live sweep takes at least 108×6 seconds plus broker/client setup and acknowledgements. The simulation executes 1,200×60 virtual seconds, much faster than real time; duration depends on host. Use fresh output directories. The live runner rejects databases with pre-existing audit rows. Both scripts save their configuration and environment. No cloud credentials are involved. Live timing is expected to vary; do not require identical numerical timing results across hosts.

`analyze.py` intentionally reads the delivered `results/live` and `results/simulation` paths. To analyze a rerun, edit its input-root paths to the fresh replay directories, or use a fresh checkout with empty final result directories. Keep the delivered data separately. Analysis rejects incomplete final suites.

## Execute the reference core

```text
.venv\Scripts\python scripts/fetch_baseline.py
.venv\Scripts\python -m pip install -r baseline/requirements-native.txt
# On Windows enable UTF-8 stdout before capturing logs:
# PowerShell: $env:PYTHONIOENCODING='utf-8'
.venv\Scripts\python scripts/reproduce_core.py
```

This downloads the pinned official repository into ignored `work/`, avoids its bundled virtual environment and executes original MQTT function bodies via a native adapter. The source has no verified project license; no source is copied into this public repository. The script writes its evidence under `results/baseline_core`, so use a separate checkout if preserving the delivered reference trace unchanged. Original random telemetry is unseeded, so new values vary. Source hashes, native repairs and observer counts are written to the summary.

Completed core scope is MQTT sensors/receiver/rate monitor, original calibration timing, and a benign burst. Linux/Docker packet-level attack scenarios, published PPS/BPS figures, original numerical Table 2 and all other protocols remain unexecuted. See `INITIAL_REPRODUCTION_AUDIT.md` and `EXTERNAL_REQUIREMENTS.md` before using the results in a manuscript.

## Artifact map

- `baseline/manifest.json`: provenance and source version.
- `src/policies.py`, `src/monitor.py`: original experimental policy code and independent paper-rule implementation.
- `configs/`: complete experimental design.
- `results/baseline_core/`: actual native reference events, summary and logs/failed attempt.
- `results/live/`: 108 raw run records, all event receipts/generation, run order, environment, compressed SQLite snapshots.
- `results/simulation/`: 1,200 raw per-run records and seed-zero raw events for every configuration.
- `results/processed/`: summaries, paired estimates, ablations, resource costs and independent validation.
- `figures/`: paper-ready PNG/PDF charts.
- `docs/`: initial audit, literature comparison, methodology, progress, external requirements and defense notes.
- `paper/`: phase report, verified BibTeX and predecessor proposal history.

Source/log/table checks are reproducibility evidence. They do not establish industrial safety, production durability, remote archival completeness or novel theoretical optimality.
`scripts/build_report.py` uses Windows Arial fonts for report layout; the experiment and verification scripts do not require these fonts.

For the executed Docker/netem extension, follow docs/LINUX_EXTENSION.md. For complete editable LaTeX and image upload, follow docs/OVERLEAF_UPLOAD.md. Prepared remote cloud scripts have six passing local integration checks; they are not WAN measurements.
