"""Independent exact segment-intersection audit; no JS lattice validator."""
import json
import sys
from pathlib import Path

def overlap(a, b, c, d):
    axis_a = [k for k in range(3) if a[k] != b[k]]
    axis_b = [k for k in range(3) if c[k] != d[k]]
    assert len(axis_a) == len(axis_b) == 1
    i, j = axis_a[0], axis_b[0]
    if i == j:
        return all(a[k] == c[k] for k in range(3) if k != i) and max(min(a[i], b[i]), min(c[i], d[i])) <= min(max(a[i], b[i]), max(c[i], d[i]))
    q = a.copy()
    q[i] = c[i]
    return all(a[k] == c[k] for k in range(3) if k not in (i, j)) and min(a[i], b[i]) <= q[i] <= max(a[i], b[i]) and min(c[j], d[j]) <= q[j] <= max(c[j], d[j])

data = json.loads(Path(sys.argv[1]).read_text())
total = 0
for r in data['records']:
    v = r['vertices']
    assert len(v) >= 4 and all(len(p) == 3 and all(isinstance(x, int) for x in p) for p in v)
    n = len(v)
    length = 0
    for i, a in enumerate(v):
        b = v[(i + 1) % n]
        assert sum(x != y for x, y in zip(a, b)) == 1
        length += sum(abs(x - y) for x, y in zip(a, b))
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            assert not overlap(a, b, v[j], v[(j + 1) % n]), (r['id'], i, j)
    assert length == r['unitEdges']
    total += length
print(json.dumps({'verified': True, 'references': len(data['records']), 'unitEdgesAudited': total, 'method': 'Exact intersections of all nonadjacent long-axis segments'}))
