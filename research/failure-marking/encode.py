"""Encode dead GCTS branches as signed point comparisons certified by complete neighborhoods.

Usage: python3 encode.py NEIGHBORHOODS.json COLLECT.jsonl [--write]
"""
import json
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path

EXTENT = 9
EXAMPLES = {
    'hat': [('hat',0,0,0),('hat',4,4,7),('hat',10,-6,3)],
    'mixed': [('hat',6,-2,-2),('turtle',0,0,0),('turtle',0,2,2),('turtle',4,-6,9),
              ('turtle',9,-7,5),('turtle',9,-5,1),('turtle',9,5,-1),('turtle',10,2,-7)]
}

class Domain:
    def __init__(self, data):
        self.shapes = {(r['tile'],r['index']):r for r in data['geometry']}
        self.sym = {i:r['symmetry'] for (_,i),r in self.shapes.items()}
        self.perm = {i:r['permutation'] for i,r in self.sym.items()}
        self.sign = {i:(-1)**sum(a>b for a,b in combinations(p,2)) for i,p in self.perm.items()}
        code = {self.move(i,2,5):i for i in self.sym}
        self.compose = {(i,j):code[self.move(i,*self.move(j,2,5))] for i,j in product(self.sym,repeat=2)}
        self.inv = {i:next(j for j in self.sym if self.compose[i,j] == 0) for i in self.sym}
        self.band = {}
        bad = defaultdict(list)
        for s, center in data['centers'].items():
            points = [(x,y) for x,y,_ in self.shapes[s,0]['sites']]
            band = {p:0 for p in points}
            front = set(band)
            for d in range(1,EXTENT+1):
                front = {(x+u,y+v) for x,y in front for u,v in
                         [(1,0),(-1,0),(0,1),(0,-1),(1,-1),(-1,1)]} - band.keys()
                band.update(dict.fromkeys(front,d))
            self.band[s] = band
            allowed = {tuple(t) for t in center['neighbors']}
            for (t,i),shape in self.shapes.items():
                offsets = {(x-a,y-b) for x,y in points for a,b,_ in shape['sites']}
                bad[s].extend((t,i,u,v) for u,v in offsets if (t,i,u,v) not in allowed)
        # A full tiling around the root must contain one of these balls. A
        # placement absent from every ball and incompatible with a member of
        # every ball is impossible, including placements disjoint from the root.
        self.impossible = set()
        for s, center in data['centers'].items():
            members, eliminated = defaultdict(int), defaultdict(int)
            for index, ball in enumerate(center['balls']):
                for a in ball:
                    members[tuple(a)] |= 1 << index
            for (t,i,x,y), mask in members.items():
                for u,j,a,b in bad[t]:
                    dx,dy = self.move(i,a,b)
                    eliminated[u,self.compose[i,j],x+dx,y+dy] |= mask
            every = (1 << len(center['balls'])) - 1
            for t,mask in eliminated.items():
                if mask == every and t not in members:
                    key = (s,*t)
                    self.impossible.add(key)
                    self.impossible.add(self.reverse(key))

    def move(self,i,x,y):
        xyz = (x,y,-x-y)
        a,b,_ = self.perm[i]
        sign = self.sym[i]['sign']
        return sign*xyz[a], sign*xyz[b]

    def reverse(self,key):
        s,t,i,x,y = key
        j = self.inv[i]
        return (t,s,j,*self.move(j,-x,-y))

    def relative(self,a,b):
        s,i,x,y = a
        t,j,u,v = b
        h = self.inv[i]
        return (s,t,self.compose[h,j],*self.move(h,u-x,v-y))

    @lru_cache(maxsize=150000)
    def clashes(self,a,b):
        s,x,y,c,v = a
        t,u,w,k,z = b
        out = []
        for i, p in self.perm.items():
            if p[c] == k and self.sign[i]*z != v:
                dx,dy = self.move(i,u,w)
                out.append((s,t,i,x-dx,y-dy))
        return tuple(out)

    def safe(self,a,b):
        return all(k in self.impossible for k in self.clashes(a,b))

    def witnesses(self,key):
        s,t,i,dx,dy = key
        for (x,y),band in self.band[s].items():
            u,w = self.move(self.inv[i],x-dx,y-dy)
            if (u,w) not in self.band[t]:
                continue
            for c in range(3):
                for v,z in product((1,-1,0),repeat=2):
                    if v == self.sign[i]*z:
                        continue
                    a,b = (s,x,y,c,v),(t,u,w,self.perm[i][c],z)
                    yield max(band,self.band[t][u,w]),a,b

def learn(set_id, geometry, runs):
    d = Domain(geometry)
    kept, blocked, banned = set(), set(), set()
    def normalized(k):
        return min(k,d.reverse(k))

    def relations(patch):
        first = {}
        for j,b in enumerate(patch):
            for a in patch[:j]:
                k = d.relative(a,b)
                if k in d.impossible:
                    first.setdefault(normalized(k),j+1)
        return first

    examples = [relations(f['patch']) for row in runs for f in row['failures']]
    obstruction = relations(EXAMPLES[set_id])
    def add_witness(key):
        current = set(kept)
        @lru_cache(None)
        def usable(a):
            return a in current or (d.safe(a,a) and all(d.safe(a,b) for b in current))
        candidates = []
        for radius,a,b in d.witnesses(key):
            if not usable(a) or not usable(b) or not d.safe(a,b):
                continue
            additions = {a,b}-current
            # Prefer reusing an assignment, then the nearest lattice overlap.
            # At a tie use a visible signed value when one is available.
            candidates.append(((len(additions),radius,sum(v[-1]==0 for v in additions),a,b),additions))
        if not candidates:
            banned.add(key)
            return False
        _, additions = min(candidates)
        for a in sorted(additions):
            kept.add(a)
            for b in kept:
                blocked.update(normalized(k) for k in d.clashes(a,b))
        return True

    # First encode the delayed obstruction, then prioritize frequent failures
    # and the earliest move at which an observed doomed prefix can be rejected.
    for k in sorted(obstruction, key=lambda k:(-max(abs(v) for v in (*k[-2:],sum(k[-2:]))),k)):
        if add_witness(k):
            break
    while True:
        scores = Counter()
        for first in examples:
            earliest = min((depth for k,depth in first.items() if k in blocked), default=None)
            for k,depth in first.items():
                if k not in banned and (earliest is None or depth < earliest):
                    scores[k] += 1 / depth
        if not scores:
            break
        add_witness(min(scores,key=lambda k:(-scores[k],k)))

    # Remove a value only if every original rejection (at every extent where
    # it existed) still has another unequal overlap. Geometric overcapacity
    # is already rejected by the base solver.
    def all_clashes(marks):
        result = {}
        for a in marks:
            for b in marks:
                radius = max(d.band[a[0]][a[1:3]],d.band[b[0]][b[1:3]])
                for key in d.clashes(a,b):
                    assert key in d.impossible
                    s,t,i,x,y = key
                    sites = footprints[s]
                    if any(sites.get((x+u,y+v),0)+w>12 for u,v,w in d.shapes[t,i]['sites']):
                        continue
                    result[key] = min(radius,result.get(key,EXTENT+1))
        return result
    footprints = {s:{(x,y):w for x,y,w in d.shapes[s,0]['sites']} for s in d.band}
    reference = all_clashes(kept)
    for a in sorted(kept):
        if all_clashes(kept-{a}) == reference:
            kept.remove(a)
    assert all_clashes(kept) == reference
    covered = {normalized(k) for k in reference}
    support = [[s,x,y,c,v,d.band[s][x,y]] for s,x,y,c,v in sorted(kept)]
    report = dict(deadEnds=len(examples),encoded=sum(bool(covered & row.keys()) for row in examples),
                  obstruction=bool(covered & obstruction.keys()),values=len(support),
                  excludedRelativePairs=len(reference))
    assert report['encoded'] and report['obstruction']
    return support,report

if __name__ == '__main__':
    if not __debug__:
        raise SystemExit('Run with assertions enabled.')
    geometry = json.loads(Path(sys.argv[1]).read_text())
    trials = [json.loads(l) for l in Path(sys.argv[2]).read_text().splitlines()]
    tables = {}
    for set_id in ['hat','mixed']:
        tables[set_id], report = learn(set_id, geometry[set_id], [r for r in trials if r['setId']==set_id])
        print(set_id, json.dumps(report), flush=True)
    text = '// Generated by research/failure-marking/encode.py. Each row is [tile, x, y, axis, value, extent].\n'
    text += 'export const failureSupport = {\n' + ''.join('  '+s+': [\n'+''.join(
        '    '+json.dumps(row,separators=(',',':'))+',\n' for row in rows)+'  ],\n' for s,rows in tables.items())+'};\n'
    dest = Path(__file__).resolve().parents[2] / 'assets/failure-rank3-data.js'
    if '--write' in sys.argv:
        dest.write_text(text)
    else:
        assert dest.read_text() == text
