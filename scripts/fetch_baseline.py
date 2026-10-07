"""Fetch only relevant files at a pinned commit; never import upstream venv."""
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'baseline/manifest.json').read_text())
target=ROOT/'work/upstream-digital-twin'
if not (target/'.git').exists():
    target.parent.mkdir(exist_ok=True)
    subprocess.run(['git','clone','--no-checkout',manifest['repository'],str(target)],check=True)
subprocess.run(['git','-C',str(target),'sparse-checkout','set','digital_twin','device','sniffer','mosquitto','sensors'],check=True)
subprocess.run(['git','-C',str(target),'checkout',manifest['commit']],check=True)
print(target)
