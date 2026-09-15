"""Deterministic registration and periodic-lifting controls; no chemical rules."""
import importlib.util
from pathlib import Path
import numpy as np

spec = importlib.util.spec_from_file_location('junctions', Path(__file__).with_name('ice-junction-clouds.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rng = np.random.default_rng(38192)
groups = [['A', 'B', 'B']] * 3
perms = m.permutations(groups)
assert len(perms) == 16
for _ in range(100):
    x = rng.normal(size=(9, 3)); x -= x[:3].mean(axis=0)
    u, _, vt = np.linalg.svd(rng.normal(size=(3, 3)))
    fix = np.eye(3); fix[-1, -1] = np.linalg.det(u @ vt); r = u @ fix @ vt
    y = (x @ r + rng.uniform(-.001, .001, size=x.shape))[perms[rng.integers(len(perms))]]
    f = m.fit(x, y, perms, .004)
    assert f is not None
    rr = np.array(f['rotationRow']); p = f['permutation']
    assert abs(np.linalg.det(rr) - 1) < 1e-8
    assert np.max(np.linalg.norm(x @ rr - y[p], axis=1)) <= .004 + 1e-10
    assert m.fit(x, x * [-1, 1, 1], perms, 1e-7) is None
    assert m.fit(x, x + [3, 4, 5], perms, 1e-7) is None  # origin is fixed

cell = np.array([[20., 0, 0], [2., 19., 0], [1., 2., 18.]])
points = np.vstack([rng.normal(scale=.2, size=(3, 3)) + center for center in [[0, 0, 0], [2, 0, 0], [1, 2, 0]]])
c = {'positions': points.tolist(), 'species': sum(groups, []), 'cell': cell.tolist()}
cover = {'components': [[0, 1, 2], [3, 4, 5], [6, 7, 8]], 'componentPairs': [[0, 1], [1, 2], [0, 2]]}
base = list(m.junctions(c, cover, [0, 1, 2]))
for _ in range(20):
    moved = points + rng.uniform(-30, 30, size=3)
    moved = (moved @ np.linalg.inv(cell) % 1) @ cell
    cc = dict(c, positions=moved.tolist())
    other = list(m.junctions(cc, cover, [0, 1, 2]))
    for a, b in zip(base, other):
        assert np.allclose(a['vectors'], b['vectors'], atol=1e-9)
print('PASS: 100 proper-rotation/permutation/noise cases, reflection and origin negatives, 60 triclinic wrapped junctions')
