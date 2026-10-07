"""Independent raw evidence checks, including on-disk audit history."""
import csv
import gzip
import json
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def main():
    live=pd.read_csv(ROOT/'results/live/runs.csv').set_index('run')
    counts=defaultdict(lambda:{'generate':0,'receive':0,'seen':set()})
    with gzip.open(ROOT/'results/live/events.csv.gz','rt',encoding='utf-8') as f:
        for e in csv.DictReader(f):
            c=counts[e['run']];c[e['event']]+=1
            if e['event']=='receive': c['seen'].add((int(e['device']),int(e['seq'])))
    checked=[]
    with tempfile.TemporaryDirectory() as td:
        for name,c in counts.items():
            r=live.loc[name]
            assert c['generate']==r.generated and c['receive']==r.delivered
            assert len(c['seen'])/c['generate']==r.delivery_ratio or abs(len(c['seen'])/c['generate']-r.delivery_ratio)<1e-12
            path=Path(td)/'audit.sqlite'
            path.write_bytes(gzip.open(ROOT/'results/live/queues'/(name+'.sqlite.gz'),'rb').read())
            db=sqlite3.connect(path)
            audit=db.execute('SELECT COUNT(*), COUNT(DISTINCT device || ":" || json_extract(payload,"$.seq")) FROM audit').fetchone()
            assert audit==(int(r.generated),int(r.generated)),(name,audit)
            db.close()
            checked.append(name)
    assert len(checked)==108
    core=json.loads((ROOT/'results/baseline_core/summary.json').read_text())
    assert core['observed_burst_messages']==200 and core['original_calibration_complete']
    checks={'live_runs_raw_and_sqlite_verified':len(checked),'baseline_burst_messages_verified':200,
        'live_generated':int(live.generated.sum()),'live_published':int(live.sent.sum()),'live_received':int(live.delivered.sum()),
        'claim_scope':'application events and local SQLite evidence; not original PCAP reproduction'}
    (ROOT/'results/processed/raw_evidence_checks.json').write_text(json.dumps(checks,indent=2))
    print(checks)

if __name__=='__main__':main()
