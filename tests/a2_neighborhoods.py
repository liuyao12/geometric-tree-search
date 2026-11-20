"""Exhaust finite necessary neighborhoods of a full-plane A2 point tiling."""
from collections import Counter
from functools import lru_cache
from itertools import combinations


def neighborhoods(records):
    shapes = {(s['tile'],s['index']):s for s in records}
    tiles = sorted({t for t,_ in shapes})
    sym = {i:s['symmetry'] for (_,i),s in shapes.items()}

    def transform(i,x,y):
        p = x,y,-x-y
        return tuple(sym[i]['sign']*p[j] for j in sym[i]['permutation'][:2])

    codes = {transform(i,2,5):i for i in sym}
    inv = {i:next(j for j in sym if transform(j,*transform(i,2,5)) == (2,5)) for i in sym}
    rel = {(i,j):codes[transform(inv[i],*transform(j,2,5))] for i in sym for j in sym}

    def relative(a,b):
        _,i,x,y = a
        t,j,u,v = b
        return (t,rel[i,j],*transform(inv[i],u-x,v-y))

    @lru_cache(None)
    def weights(t):
        s,i,x,y = t
        return {(x+a,y+b):w for a,b,w in shapes[s,i]['sites']}

    @lru_cache(None)
    def covering(q):
        return {(s,i,q[0]-x,q[1]-y) for (s,i),shape in shapes.items() for x,y,_ in shape['sites']}

    def totals(board):
        out = Counter()
        for t in board:
            out.update(weights(t))
        return out

    def fits(total,t):
        return all(total.get(p,0)+w <= 12 for p,w in weights(t).items())

    def touches_ok(a,b,allowed):
        return (weights(a).keys().isdisjoint(weights(b)) or
                (relative(a,b) in allowed[a[0]] and relative(b,a) in allowed[b[0]]))

    # Enumerate every possible geometric neighbor of each canonical tile.
    geometric = {}
    for s in tiles:
        root = s,0,0,0
        geometric[s] = {t for q in weights(root) for t in covering(q)
                        if t != root and fits(weights(root),t)}

    # A contact in a tiling can fill each unfinished point of its two tiles.
    # Repeat that necessary check once using the first pass's certified exclusions.
    allowed = geometric
    for _ in range(2):
        survivors = {s:set() for s in tiles}

        @lru_cache(None)
        def pair_ok(a,b):
            return touches_ok(a,b,allowed)

        def fill_one(q,total,fixed):
            need = 12-total[q]
            choices = [t for t in covering(q)-fixed if weights(t)[q] <= need and fits(total,t)
                       and all(pair_ok(b,t) for b in fixed)]
            def finish(start,remaining,used,sums):
                for j in range(start,len(choices)):
                    t = choices[j]
                    w = weights(t)[q]
                    if w > remaining or not fits(sums,t) or any(not pair_ok(t,b) for b in used):
                        continue
                    if w == remaining:
                        return True
                    more = sums.copy()
                    more.update(weights(t))
                    if finish(j+1,remaining-w,used+(t,),more):
                        return True
                return False
            return finish(0,need,(),total)

        for s,others in allowed.items():
            for t in others:
                fixed = {(s,0,0,0),t}
                total = totals(fixed)
                if all(w == 12 or fill_one(q,total,fixed) for q,w in total.items()):
                    survivors[s].add(t)
        pair_ok.cache_clear()
        allowed = survivors

    # Complete *all* positive support points of selected center tiles. An actual
    # tiling supplies one of the enumerated completions at each step.
    def fill(board,centers,first_only=False):
        if any(not permitted(a,b) for a,b in combinations(board,2)):
            return set()
        total = totals(board)
        assert max(total.values()) <= 12
        targets = {q for c in centers for q in weights(c) if total[q] < 12}
        pool = {t for q in targets for t in covering(q)-board
                if fits(total,t) and all(permitted(b,t) for b in board)}
        incident = {q:pool & covering(q) for q in targets}
        neighbors = {t:{b for b in pool if b != t and permitted(t,b)} for t in pool}
        seen, result = set(), set()

        def visit(chosen,available,sums):
            if chosen in seen:
                return False
            seen.add(chosen)
            best = None
            for q,domain in incident.items():
                if sums[q] == 12:
                    continue
                choices = [t for t in domain & available if fits(sums,t)]
                if not choices:
                    return False
                if best is None or len(choices) < len(best):
                    best = choices
            if best is None:
                result.add(board | chosen)
                return first_only
            for t in best:
                more = sums.copy()
                more.update(weights(t))
                if visit(chosen|{t},available & neighbors[t],more):
                    return True
            return False
        visit(frozenset(),pool,total)
        return result

    @lru_cache(None)
    def permitted(a,b):
        return touches_ok(a,b,allowed)

    first = {}
    for s in tiles:
        root = frozenset({(s,0,0,0)})
        first[s] = fill(root,root)
    allowed = {s:set().union(*rings) for s,rings in first.items()}
    permitted.cache_clear()

    for s in tiles:
        balls = set()
        for inner in first[s]:
            for outer in fill(inner,inner):
                if fill(outer,outer-inner,first_only=True):
                    balls.add(outer)
        assert balls
        boards = [(ball,totals(ball)) for ball in balls]

        @lru_cache(None)
        def possible(t):
            return any(t in ball or (fits(total,t) and all(permitted(b,t) for b in ball))
                       for ball,total in boards)

        yield s, allowed[s], balls, possible
