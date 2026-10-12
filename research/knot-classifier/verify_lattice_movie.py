"""Independent exact lattice disk + projected Reidemeister replay (stdlib).
No JS generator, point solver, or learning state is used.
"""
import json
import sys
from fractions import Fraction
from verify_movie import key, deletions


def loop(raw):
    p = [tuple(x) for x in raw]
    if p[0] == p[-1]:
        p.pop()
    out = []
    for a, b in zip(p, p[1:] + p[:1]):
        if len(a) != 3 or any(type(x) is not int for x in a):
            raise ValueError('Integer triples required')
        axes = [k for k in range(3) if a[k] != b[k]]
        if len(axes) != 1:
            raise ValueError('Non-axis edge')
        k = axes[0]
        step = 1 if b[k] > a[k] else -1
        for j in range(abs(b[k] - a[k])):
            q = list(a)
            q[k] += j * step
            out.append(tuple(q))
    if len(out) < 4 or len(set(out)) != len(out):
        raise ValueError('Self-intersecting/degenerate loop')
    return out


def edges(p):
    return {frozenset((a, b)) for a, b in zip(p, p[1:] + p[:1])}


def projection(raw, direction):
    p = loop(raw)
    p = [b for i, b in enumerate(p) if tuple(b[k]-p[i-1][k] for k in range(3)) != tuple(p[(i+1)%len(p)][k]-b[k] for k in range(3))]
    a, b, c = direction
    u, v = (b, -a, 0), (a*c, b*c, -a*a-b*b)
    dot = lambda q, r: sum(x*y for x, y in zip(q, r))
    cross = lambda q, r: q[0]*r[1]-q[1]*r[0]
    sub = lambda q, r: tuple(x-y for x, y in zip(q, r))
    xy = [(dot(q, u), dot(q, v)) for q in p]
    depths = [dot(q, direction) for q in p]
    events, locations = [], set()
    ident = 0
    for i in range(len(p)):
        for j in range(i+1, len(p)):
            if j == i+1 or (i == 0 and j == len(p)-1):
                continue
            r, s, q = sub(xy[(i+1)%len(p)], xy[i]), sub(xy[(j+1)%len(p)], xy[j]), sub(xy[j], xy[i])
            den = cross(r, s)
            if not den:
                if not cross(q, r):
                    k = 0 if r[0] else 1
                    lo = max(min(xy[i][k], xy[(i+1)%len(p)][k]), min(xy[j][k], xy[(j+1)%len(p)][k]))
                    hi = min(max(xy[i][k], xy[(i+1)%len(p)][k]), max(xy[j][k], xy[(j+1)%len(p)][k]))
                    if lo <= hi:
                        raise ValueError('Degenerate parallel projection')
                continue
            t, w = Fraction(cross(q, s), den), Fraction(cross(q, r), den)
            if not (0 <= t <= 1 and 0 <= w <= 1):
                continue
            if t in (0, 1) or w in (0, 1):
                raise ValueError('Endpoint projection crossing')
            location = tuple(xy[i][k]+t*r[k] for k in range(2))
            if location in locations:
                raise ValueError('Multiple projected crossing')
            locations.add(location)
            height = depths[i]+t*(depths[(i+1)%len(p)]-depths[i])-depths[j]-w*(depths[(j+1)%len(p)]-depths[j])
            if not height:
                raise ValueError('Spatial crossing')
            over = height > 0
            sign = (1 if cross(r, s) > 0 else -1) * (1 if over else -1)
            ident += 1
            events.extend([(i+t, (ident, over, sign)), (j+w, (ident, not over, sign))])
    return [x for _, x in sorted(events)]


def verify(cert):
    if cert['version'] != 'lattice-face-reidemeister-v1':
        raise ValueError('Unsupported certificate')
    p = loop(cert['source'])
    options = cert['options']
    direction = options['direction']
    if len(p) > options['maxEdges'] or ('depth' in options and len(cert['steps']) > options['depth']):
        raise ValueError('Certificate exceeds bounds')
    counts = {}
    for step in cert['steps']:
        q = loop(step['vertices'])
        if len(q) > options['maxEdges']:
            raise ValueError('Edge cap')
        f = [tuple(x) for x in step['face']]
        if len(f) != 4 or len(set(f)) != 4:
            raise ValueError('Square requires four distinct corners')
        dims = [max(x[k] for x in f)-min(x[k] for x in f) for k in range(3)]
        if sorted(dims) != [0, 1, 1] or any(sum(abs(a[k]-b[k]) for k in range(3)) != 1 for a, b in zip(f, f[1:]+f[:1])):
            raise ValueError('Not a unit coordinate face')
        region = options.get('region')
        if region and any(not region['min'][k] <= x[k] <= region['max'][k] for x in f for k in range(3)):
            raise ValueError('Face outside search region')
        e, new, boundary = edges(p), edges(q), edges(f)
        if e ^ new != boundary:
            raise ValueError('Unchanged exterior or face complement violated')
        old_path, new_path = [tuple(x) for x in step['old']], [tuple(x) for x in step['replacement']]
        path_edges = lambda a: {frozenset(pair) for pair in zip(a, a[1:])}
        if any(len(a) < 2 or len(a) > 4 or len(set(a)) != len(a) for a in (old_path, new_path)):
            raise ValueError('Not a simple boundary arc')
        if path_edges(old_path) != e & boundary or path_edges(new_path) != new & boundary or old_path[0] != new_path[0] or old_path[-1] != new_path[-1]:
            raise ValueError('Arc/collar mismatch')
        # Integer transverse edges cannot pierce the relative interior of this
        # unit disk. Self-avoidance + the exact unchanged exterior above checks
        # all boundary contacts, including marking-free outside strands.
        before, after = projection(p, direction), projection(q, direction)
        if key(before) != step['beforeDiagram'] or key(after) != step['afterDiagram']:
            raise ValueError('Projection data fabricated')
        kind = step['kind']
        if kind == 'routing':
            valid = key(before) == key(after)
        elif kind in ('I+', 'II+'):
            inv = 'I−' if kind == 'I+' else 'II−'
            valid = any(key(w) == key(before) for w in deletions(after, inv))
        elif kind in ('I−', 'II−', 'III'):
            valid = any(key(w) == key(after) for w in deletions(before, kind))
        else:
            valid = False
        if not valid:
            raise ValueError('Projected endpoints are not the declared Reidemeister move')
        counts[kind] = counts.get(kind, 0)+1
        p = q
    if edges(p) != edges(loop(cert['target'])):
        raise ValueError('Wrong spatial endpoint')
    return {'verified': True, 'tiles': len(cert['steps']), 'kinds': counts, 'spatialEndpoint': True}


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as stream:
        data = json.load(stream)
    print(json.dumps([verify(x) for x in data] if isinstance(data, list) else verify(data.get('certificate', data))))
