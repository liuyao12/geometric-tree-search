"""Assemble verified junction-only learning-curve evidence without coordinates."""
import hashlib
import json
from pathlib import Path
import sys

curve = Path(sys.argv[1]); full = Path(sys.argv[2]); full_check = Path(sys.argv[3])
rows = []
for size, learned, checked in [(n, curve / str(n) / 'learned.json', curve / str(n) / 'check.json') for n in [1, 5, 10]] + [(25, full, full_check)]:
    raw = learned.read_bytes(); d = json.loads(raw); check = json.loads(checked.read_text())
    assert check['learnedHash'] == hashlib.sha256(raw).hexdigest()
    for key in ['trainingJunctions', 'developmentJunctions', 'developmentMatched', 'developmentConfigurationsComplete']:
        assert check['counts'][key] == d['summary'][key]
    assert d['summary']['templates'] == check['templatesWithObservedTrainingSource']
    assert check['counts']['trainingConfigurationsComplete'] == 4 * size
    rows.append({'sourceTrainingFramesPerPhase': size, 'trainingConfigurations': 4 * size,
                 'summary': d['summary'], 'verification': check})
out = {'scope': __doc__, 'epsilonAngstrom': .15, 'results': rows,
       'limits': 'Junction-library-only ablation. Upstream geometry and selected covers fixed from 100-training-frame pilot. Same 100 developmental configurations; not independent holdout. No new tree search or growth result.'}
with Path(sys.argv[4]).open('x') as f: json.dump(out, f, indent=2)
