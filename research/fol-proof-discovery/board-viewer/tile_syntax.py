"""Derive read/write tile syntax marks from the checked search data."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys


CATEGORIES = (
    ('quantifier', 'Quantifier', '#704598'),
    ('variable', 'Variable', '#1b508d'),
    ('predicate', 'Predicate', '#166353'),
    ('negation', 'Negation', '#a03733'),
    ('connective', 'And / or', '#715489'),
    ('witness', 'Witness symbol', '#884361'),
    ('arithmetic', 'Arithmetic', '#825015'),
    ('empty', 'Empty clause', '#29313d'),
)
BITS = {name: 1 << i for i, (name, _, _) in enumerate(CATEGORIES)}


def term_mask(value):
    if isinstance(value, str):
        if value.startswith(('?', '@')):
            return BITS['variable']
        if value.startswith('_sk'):
            return BITS['witness']
        return BITS['arithmetic']
    name, *args = value
    mask = BITS['witness' if name.startswith('_sk') else 'arithmetic']
    for arg in args:
        mask |= term_mask(arg)
    return mask


def clause_mask(clause):
    if not clause:
        return BITS['empty']
    mask = BITS['predicate']
    if len(clause) > 1:
        mask |= BITS['connective']
    for sign, _, args in clause:
        if not sign:
            mask |= BITS['negation']
        for arg in args:
            mask |= term_mask(arg)
    return mask | BITS['quantifier'] if mask & BITS['variable'] else mask


def export(tape, output):
    from kernel import normalize
    from prime_run import tuple_tree
    from prime_tiling import infer_write

    masks = bytearray()
    stages = json.loads(tape.read_text())
    for stage in stages:
        for attempt in stage['attempts']:
            sources = tuple_tree(attempt['sources'])
            frontier = [normalize(sources[i])[0] for i in attempt['inputs']]
            masks.extend(map(clause_mask,frontier))
            counts = Counter()
            for left, first, right, second, factor in attempt['rows']:
                result = infer_write('factor' if factor else 'resolve', frontier[left],
                                     frontier[right], (first,second), counts, lambda: None)
                if result is None:
                    raise ValueError('Tile syntax export found an invalid deduction')
                clause = normalize(result[0])[0]
                frontier.append(clause)
                masks.append(clause_mask(clause))
            serialized = json.dumps(frontier,separators=(',',':'))
            if sha256(serialized.encode()).hexdigest()!=attempt['digest']:
                raise ValueError('Tile syntax export does not match the recorded board')
    output.write_bytes(masks)
    print(f'Verified syntax masks for {len(masks):,} clauses across all search attempts.',flush=True)


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
    export(Path(sys.argv[1]),Path(sys.argv[2]))
