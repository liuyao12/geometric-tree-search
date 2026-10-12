"""Independent signed-ribbon certificate replay; standard library only.

Checks expansions by the inverse disk deletion, without using the JS catalog,
policy, marking learner, or forward insertion generator.
"""
import json
import re
import sys


def parse(text):
    result = []
    for token in text.split():
        m = re.fullmatch(r'([OU])(\d+)([+-])', token)
        if not m:
            raise ValueError('Malformed Gauss token')
        result.append((int(m[2]), m[1] == 'O', 1 if m[3] == '+' else -1))
    return result


def key(word):
    if not word:
        return ''
    keys = []
    for seq in (word, list(reversed(word))):
        for shift in range(len(seq)):
            labels = {}
            tokens = []
            for ident, over, sign in seq[shift:] + seq[:shift]:
                labels.setdefault(ident, len(labels) + 1)
                tokens.append(f'{"O" if over else "U"}{labels[ident]}{"+" if sign > 0 else "-"}')
            keys.append(' '.join(tokens))
    return min(keys)


def faces(word):
    if not word:
        return []
    locations = {}
    for i, x in enumerate(word):
        locations.setdefault(x[0], []).append(i)
    rotation = {}
    for indexes in locations.values():
        if len(indexes) != 2:
            raise ValueError('Crossing multiplicity')
        a, b = indexes
        if word[a][1] == word[b][1] or word[a][2] != word[b][2]:
            raise ValueError('Invalid crossing decoration')
        o, u = (a, b) if word[a][1] else (b, a)
        order = [2*o+1, 2*u+1, 2*o, 2*u] if word[a][2] > 0 else [2*o+1, 2*u, 2*o, 2*u+1]
        rotation.update(zip(order, order[1:] + order[:1]))
    size = len(word)
    def mate(d):
        return 2*((d//2+1) % size) if d % 2 else 2*((d//2-1) % size)+1
    unseen = set(range(2*size))
    result = []
    while unseen:
        start = min(unseen)
        d = start
        face = []
        while True:
            unseen.remove(d)
            face.append((d//2, mate(d)//2))
            d = rotation[mate(d)]
            if d == start:
                break
        result.append(face)
    if len(locations) - 2*len(locations) + len(result) != 2:
        raise ValueError('Nonplanar ribbon diagram')
    return result


def deletions(word, kind):
    for face in faces(word):
        ids = {word[p][0] for pair in face for p in pair}
        if kind == 'I−' and len(face) == len(ids) == 1:
            yield [x for x in word if x[0] not in ids]
        if kind == 'II−' and len(face) == len(ids) == 2:
            signs = {word[p][2] for pair in face for p in pair}
            if len(signs) == 2 and all(word[a][1] == word[b][1] for a, b in face):
                yield [x for x in word if x[0] not in ids]
        if kind == 'III' and len(face) == len(ids) == 3:
            positions = [p for pair in face for p in pair]
            levels = {int(word[a][1])+int(word[b][1]) for a, b in face}
            if len(set(positions)) == 6 and levels == {0, 1, 2}:
                after = list(word)
                for a, b in face:
                    after[a], after[b] = after[b], after[a]
                yield after


def verify(certificate):
    if certificate['version'] != 'reidemeister-seams-v1':
        raise ValueError('Certificate version')
    current = parse(certificate['source'])
    faces(current)
    cap = certificate['crossingCap']
    if len(current)//2 > cap:
        raise ValueError('Source exceeds crossing cap')
    for tile in certificate['steps']:
        after = parse(tile['after'])
        faces(after)
        if len(after)//2 > cap:
            raise ValueError('Crossing cap')
        kind = tile['kind']
        if kind in ('I+', 'II+'):
            inverse = 'I−' if kind == 'I+' else 'II−'
            valid = any(key(w) == key(current) for w in deletions(after, inverse))
        elif kind in ('I−', 'II−', 'III'):
            valid = any(key(w) == key(after) for w in deletions(current, kind))
        else:
            valid = False
        if not valid:
            raise ValueError(f'Illegal Reidemeister tile: {kind}')
        current = after
    if key(current) != key(parse(certificate['target'])):
        raise ValueError('Endpoint mismatch')
    return {'verified': True, 'tiles': len(certificate['steps'])}


if __name__ == '__main__':
    if sys.argv[1] == '-':
        data = json.load(sys.stdin)
    else:
        with open(sys.argv[1], encoding='utf-8') as stream:
            data = json.load(stream)
    if isinstance(data, list):
        print(json.dumps([verify(c) for c in data]))
    else:
        print(json.dumps(verify(data.get('certificate', data))))
