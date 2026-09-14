"""Prespecified first-25-frame pilot per author split and phase; no outcome selection."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir()
raw=(source/'coordinates.json').read_bytes();praw=(source/'provenance.json').read_bytes()
d=json.loads(raw);p=json.loads(praw)
metadata=[c for c in p['configurations'] if c['sourceFrame']<25]
ids={c['id'] for c in metadata}
assert len(ids)==200
(out/'coordinates.json').write_text(json.dumps({'configurations':[c for c in d['configurations'] if c['id'] in ids]}))
(out/'provenance.json').write_text(json.dumps({'configurations':metadata}))
(out/'selection.json').write_text(json.dumps({'rule':'First 25 frames of each phase and author split, chosen before cluster evaluation.',
 'sourceCoordinatesSha256':hashlib.sha256(raw).hexdigest(),'sourceProvenanceSha256':hashlib.sha256(praw).hexdigest(),
 'ids':sorted(ids),'independentTrajectoryHoldout':False},indent=2))
subprocess.run([sys.executable,str(Path(__file__).with_name('ice-geometric-components.py')),
 str(out/'coordinates.json'),str(out/'provenance.json'),str(out/'components.json')],check=True)
