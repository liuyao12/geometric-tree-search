"""Freeze a training-95th-percentile substitution hypothesis before target checks.

Substitution radius is not the overlap marking radius, which remains unchanged.
The choice of percentile is a developmental modeling choice, not a calibrated
probability guarantee or a claim of complete configuration preservation.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
source,calibration_path,check_path,output=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
library,calibration,check=[json.loads(p.read_text()) for p in [source,calibration_path,check_path]]
assert calibration['libraryHash']==check['libraryHash']==sha(source)
assert check['reportHash']==sha(calibration_path)
assert check['summary']==calibration['summary']
radius=calibration['summary']['quantilesAngstrom']['0.95']
spec=importlib.util.spec_from_file_location('learner',Path(__file__).with_name('learn-ice-context-substitutions.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
start=time.monotonic();result=m.learn(library,radius)
result.update(scope=__doc__,libraryHash=sha(source),codeHash=sha(Path(__file__)),learnerHash=sha(Path(m.__file__)),
              calibration=dict(reportHash=sha(calibration_path),checkHash=sha(check_path),quantile=.95),
              markingRadiusAngstrom=library['markingRadiusAngstrom'],seconds=time.monotonic()-start,
              limits='Restricted empirical substitution hypothesis. Threshold fitted from existing training dictionary, not independently refitted folds. Original paired observations retained. No target-answer, physics or phase inputs; no negative-connection guarantee, complete pose universe or growth claim.')
with output.open('x') as f:json.dump(result,f)
print(json.dumps(dict(**result['summary'],substitutionRadius=radius,markingRadius=result['markingRadiusAngstrom'],seconds=result['seconds'])))
