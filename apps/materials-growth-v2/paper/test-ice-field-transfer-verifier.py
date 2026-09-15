"""Corrupt saved claims and require the independent verifier to reject them."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

# Same six input paths as the verifier, excluding its output path.
arguments=list(sys.argv[1:]);assert len(arguments)==6
original=json.loads(Path(arguments[-1]).read_text())
def wrong_distance(r):r['results'][0]['matches'][0]['endpointDistances'][0]+=.5
def missing_occurrence(r):r['results'][0]['matches'].pop()
def altered_split(r):r['fitFrames'].pop()
def wrong_radius(r):r['results'][0]['matches'][0]['radius']+=.5
for corrupt in [wrong_distance,missing_occurrence,altered_split,wrong_radius]:
    with tempfile.TemporaryDirectory(prefix='ice-field-verifier-test-') as folder:
        r=copy.deepcopy(original);corrupt(r);path=Path(folder)/'corrupt.json';path.write_text(json.dumps(r))
        command=[sys.executable,str(Path(__file__).with_name('verify-ice-field-transfer.py')),*arguments[:-1],str(path),str(Path(folder)/'unexpected.json')]
        result=subprocess.run(command,capture_output=True,text=True,timeout=90)
        assert result.returncode!=0 and 'AssertionError' in result.stderr, result.stderr[-2000:]
        assert not (Path(folder)/'unexpected.json').exists()
        print(corrupt.__name__+': rejected')
