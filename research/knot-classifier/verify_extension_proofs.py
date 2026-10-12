"""Independent face alphabet and bounded set-cover proof replay (stdlib only)."""
import json
import sys
from functools import lru_cache

popcount = getattr(int, "bit_count", lambda value: bin(value).count("1"))


def replay_event(event):
    edges = [[tuple(p) for p in e] for e in json.loads(event['signature'])]
    index = {frozenset(e): i for i, e in enumerate(edges)}
    if len(index) != len(edges):
        raise ValueError('Repeated discrepancy edge')
    masks = set()
    for a, b in edges:
        if any(not isinstance(x, int) for p in (a, b) for x in p) or sum(abs(x-y) for x, y in zip(a, b)) != 1:
            raise ValueError('Not an integer unit edge')
        axis = next(i for i in range(3) if a[i] != b[i])
        for j in range(3):
            if j == axis:
                continue
            for sign in (-1, 1):
                c = tuple(x + (sign if i == j else 0) for i, x in enumerate(b))
                d = tuple(x + (sign if i == j else 0) for i, x in enumerate(a))
                corners = [a, b, c, d]
                mask = 0
                for u, v in zip(corners, corners[1:]+corners[:1]):
                    k = index.get(frozenset((u, v)))
                    if k is not None:
                        mask |= 1 << k
                masks.add(mask)
    supplied = {int(x, 16) for x in event['masks']}
    if supplied != masks:
        raise ValueError('Local alphabet is incomplete or contains invented faces')
    full = (1 << len(edges))-1
    full_maximum = max((popcount(mask) for mask in masks), default=0)
    incident = [[m for m in masks if m & (1 << i)] for i in range(len(edges))]

    @lru_cache(None)
    def extend(uncovered, remaining):
        if not uncovered:
            return True
        if not remaining:
            return False
        # Independent union-capacity certificate over the verified complete
        # alphabet. Wide wrong-reference windows need not branch exponentially.
        maximum=full_maximum if uncovered==full else max((popcount(uncovered & mask) for mask in masks), default=0)
        if not maximum or popcount(uncovered)>remaining*maximum:
            return False
        # Independent exhaustive recursion over the first uncovered bit.
        point = (uncovered & -uncovered).bit_length()-1
        return any(extend(uncovered & ~m, remaining-1) for m in incident[point])

    negative = []
    labels = 0
    for sample in event['samples']:
        if sample['outcome'] == 'unresolved':
            continue
        positive = extend(full, sample['horizon'])
        if positive != (sample['outcome'] == 'positive'):
            raise ValueError('Extension label fails independent replay')
        labels += 1
        if not positive:
            negative.append(sample['horizon'])
        else:
            union = 0
            for i in sample['witness']:
                union |= int(event['masks'][i], 16)
            if union != full or len(sample['witness']) > sample['horizon']:
                raise ValueError('Invalid positive cover witness')
    expected_values = [[h, 1] for h in negative]
    if event['values'] != expected_values or event['lower'] != (max(negative)+1 if negative else 0):
        raise ValueError('Failed-budget marking stencil is not supported by labels')
    return labels


def verify_report(report):
    cache = {}
    events = labels = 0
    all_lanes = report.get('lanes', [report]) + report.get('additionalDeeperTrials', [])
    for lane in all_lanes:
        for run in lane['runs']:
            for event in (run.get('extensions') or {}).get('eventsThisRun', []):
                key = event['signature'] + json.dumps(event['masks']) + json.dumps(event['samples'])
                if key not in cache:
                    cache[key] = replay_event(event)
                # Check stencils on duplicate observations too.
                negative = [s['horizon'] for s in event['samples'] if s['outcome'] == 'negative']
                if event['values'] != [[h, 1] for h in negative] or event['lower'] != (max(negative)+1 if negative else 0):
                    raise ValueError('Altered reused stencil')
                events += 1
                labels += cache[key]
    return {'verified': True, 'events': events, 'resolvedLabels': labels, 'independentCatalogs': len(cache)}


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as stream:
        data = json.load(stream)
    print(json.dumps(verify_report(data)))
