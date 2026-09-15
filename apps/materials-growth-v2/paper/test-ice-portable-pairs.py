"""Shared-rotation transport checks and deliberate export-corruption controls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import numpy as np

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

cloud = module('cloud', 'portable-cloud-markings.py')
verify = module('verify', 'verify-ice-portable.py')
coordinates, cover, dictionary, selection, junction, library_path, precheck_path = sys.argv[1:]
library = json.loads(Path(library_path).read_text()); precheck = json.loads(Path(precheck_path).read_text())
rng = np.random.default_rng(6321)
def rotation():
    u, _, vt = np.linalg.svd(rng.normal(size=(3, 3))); fix = np.eye(3); fix[-1, -1] = np.linalg.det(u @ vt); return u @ fix @ vt
for i in rng.choice(len(library['motifs']), size=100, replace=False):
    motif = library['motifs'][int(i)]; r = rotation(); q = rotation()
    for value in motif['cloudM']:
        sequential = cloud.transform(cloud.transform(value, r), q)
        simultaneous = cloud.transform(value, r @ q)
        assert cloud.contains(sequential, simultaneous, 1e-8) is not None
        assert cloud.contains(cloud.transform(cloud.transform(value, r), r.T), value, 1e-8) is not None
    try: cloud.transform(motif['cloudM'][1], -np.eye(3))
    except ValueError: pass
    else: raise AssertionError('Reflection accepted as proper rotation')

def mutate_mark(d): d['motifs'][0]['cloudM'][1]['vectors'][0][0] += 1.
def mutate_anchor(d): d['baseMotifs'][0]['markAnchors'][0][0] += .01
def mutate_identity(d): d['motifs'][0]['targetAtomId'] = 42
def mutate_roots(d): d['trainingRegistrations'][0]['selected'][0]['roots'].reverse()
with tempfile.TemporaryDirectory(prefix='ice-portable-mutations-') as folder:
    folder = Path(folder)
    for index, mutation in enumerate([mutate_mark, mutate_anchor, mutate_identity, mutate_roots]):
        altered = copy.deepcopy(library); mutation(altered)
        file = folder / f'{index}.json'; file.write_text(json.dumps(altered))
        check = copy.deepcopy(precheck); check['portableHash'] = hashlib.sha256(file.read_bytes()).hexdigest()
        check_file = folder / f'{index}-precheck.json'; check_file.write_text(json.dumps(check))
        try: verify.run(coordinates, cover, dictionary, selection, junction, str(file), str(check_file), str(folder / f'{index}-output.json'))
        except AssertionError: pass
        else: raise AssertionError(f'Mutation escaped verification: {mutation.__name__}')
print('PASS: 100 two-ended rotation compositions/inverses; reflections rejected; four export corruptions rejected')
