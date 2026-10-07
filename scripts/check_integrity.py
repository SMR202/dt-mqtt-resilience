"""Hash original source, configs and final evidence; verify with --verify."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'results/artifact_sha256.json'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    if args.verify:
        values=json.loads(MANIFEST.read_text())
        for name,expected in values.items():
            path=ROOT/name
            assert path.exists() and digest(path)==expected,name
        print('Verified',len(values),'artifact hashes')
    else:
        prefixes=['src','scripts','configs','baseline','docs','paper','results/simulation','results/live','results/baseline_core','results/processed','figures']
        paths=[f for pre in prefixes for f in (ROOT/pre).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.log','.sqlite','.pyc']]
        values={f.relative_to(ROOT).as_posix():digest(f) for f in sorted(paths)}
        MANIFEST.write_text(json.dumps(values,indent=2)+'\n')
        print('Recorded',len(values),'hashes')

if __name__=='__main__': main()
