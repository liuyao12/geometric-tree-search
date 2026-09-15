"""Reject corrupted alternative-pose witnesses using the independent checker.

Usage: python test-ice-alternative-witness-check.py COORD COVER DICT LIBRARY
       TRANSFER RESCUE PRIOR_CHECK
Temporary mutated reports are test fixtures, never scientific result artifacts.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

paths=list(map(Path,sys.argv[1:]));assert len(paths)==7
original=json.loads(paths[5].read_text())
checker=Path(__file__).with_name('verify-ice-field-alternative-bases.py')
def first(report):
    return next(a['witness'] for r in report['results'] for a in r['repairs'] if a['witness'])
def rotation(report):first(report)['rotationRow'][0][0]+=0.25
def translation(report):first(report)['translation'][0]+=0.5
def distance(report):first(report)['endpointDistances'][0]+=0.1
def missing(report):report['results'].pop()
with tempfile.TemporaryDirectory(prefix='gcts-witness-negative-') as tmp:
    for mutate in [rotation,translation,distance,missing]:
        report=copy.deepcopy(original);mutate(report)
        path=Path(tmp)/f'{mutate.__name__}.json';path.write_text(json.dumps(report))
        args=[str(p) for p in paths];args[5]=str(path)
        result=subprocess.run([sys.executable,str(checker),*args,str(Path(tmp)/f'{mutate.__name__}-check.json')],capture_output=True,text=True)
        assert result.returncode!=0 and 'AssertionError' in result.stderr, (mutate.__name__,result.stdout,result.stderr)
        print(f'{mutate.__name__}: corrupted witness rejected',flush=True)
