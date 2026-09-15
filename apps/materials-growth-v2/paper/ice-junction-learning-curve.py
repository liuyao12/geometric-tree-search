"""Prespecified training-size diagnostic; metadata select cohorts, not features.

Run 1, 5, and 10 source frames per author training phase, keeping the same
100 developmental configurations. The full existing 25-frame result is separate.
No tolerance selection, independent-test claim, or new growth result. This is
a junction-library-only ablation: upstream component discovery, pair dictionary
and selected covers stay fixed from the existing 100-training-frame pilot.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]); output = Path(sys.argv[2]); output.mkdir()
files = {'coordinates': 'coordinates.json', 'cover': 'overlap-broad.json',
         'dictionary': 'thermal-dictionary-e015.json', 'selection': 'thermal-selection-k2.json'}
data = {key: json.loads((source / file).read_text()) for key, file in files.items()}
provenance = json.loads((source / 'provenance.json').read_text())
rows = []
for size in [1, 5, 10]:
    folder = output / str(size); folder.mkdir()
    ids = {c['id'] for c in provenance['configurations'] if c['split'] != 'train' or c['sourceFrame'] < size}
    subset = {key: dict(value) for key, value in data.items()}
    for key, value in subset.items():
        field = 'configurations' if key in ['coordinates', 'dictionary'] else 'results'
        value[field] = [r for r in value[field] if r['id'] in ids]
    # Only filter IDs in already verified data; regenerate byte-binding hashes.
    subset['cover']['trainingIds'] = [i for i in subset['cover']['trainingIds'] if i in ids]
    for key in ['coordinates', 'cover', 'dictionary', 'selection']:
        if key == 'cover': subset[key]['coordinateHash'] = hashlib.sha256((folder / 'coordinates.json').read_bytes()).hexdigest()
        if key == 'dictionary':
            subset[key]['coordinateHash'] = hashlib.sha256((folder / 'coordinates.json').read_bytes()).hexdigest()
            subset[key]['coverHash'] = hashlib.sha256((folder / 'cover.json').read_bytes()).hexdigest()
        (folder / (key + '.json')).write_text(json.dumps(subset[key]))
    (folder / 'provenance.json').write_text(json.dumps({'configurations': [r for r in provenance['configurations'] if r['id'] in ids]}))
    args = [str(folder / (key + '.json')) for key in ['coordinates', 'cover', 'dictionary', 'selection']]
    learned = folder / 'learned.json'; check = folder / 'check.json'
    subprocess.run([sys.executable, str(Path(__file__).with_name('ice-junction-clouds.py')), *args, '0.15', str(learned)], check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name('verify-ice-junction-clouds.py')), *args, str(learned), str(folder / 'provenance.json'), str(check)], check=True)
    rows.append({'sourceTrainingFramesPerPhase': size, 'summary': json.loads(learned.read_text())['summary'],
                 'checkHash': hashlib.sha256(check.read_bytes()).hexdigest()})
(output / 'summary.json').write_text(json.dumps({'scope': __doc__, 'results': rows}, indent=2))
