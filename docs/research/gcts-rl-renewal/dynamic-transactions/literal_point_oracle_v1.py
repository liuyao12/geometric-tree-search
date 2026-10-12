"""Independent literal point controls; no imports from the search implementation.

Tiny controls enumerate every ordered reference and compare whole assignments.
Large-catalog counts use a complete raw-record partition followed by literal
reference-pair enumeration per equivalence class. This is not a logical checker
or a theorem search, and does not qualify the learned-cluster pipeline.
"""
from collections import Counter
import hashlib
import json
import struct

ROW = struct.Struct('<11Q32s32s')
SENTINEL = (1 << 64) - 1


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def point_marks(recipe, row, refs):
    values = {(1, row): recipe['output']}
    if len(refs) != len(recipe['inputs']):
        raise ValueError('all literal ordered ports required')
    for port, (ref, code) in enumerate(zip(refs, recipe['inputs'])):
        if type(ref) is not int or not 0 <= ref < row:
            raise ValueError('strict prior references required')
        if (1, ref) in values and values[1, ref] != code:
            return None
        values[1, ref] = code
        values[2 + port, row] = ref - row
    return values


def literal_keys(recipes, row, total, marks, exclusions=()):
    result = []
    if total == 1:
        return result
    for index, recipe in enumerate(recipes):
        references = [()] if not recipe['inputs'] else (
            (a, b) for a in range(row) for b in range(row))
        for refs in references:
            values = point_marks(recipe, row, refs)
            if values is None or any(p in marks and marks[p] != v for p, v in values.items()):
                continue
            key = (index, row, refs)
            if key not in exclusions:
                result.append(key)
    return result


def literal_factors(recipes, row, total, marks):
    """Independent full key enumeration; masks also include admissible lone ports."""
    keys = literal_keys(recipes, row, total, marks)
    counts = Counter(key[0] for key in keys)
    factors = []
    for index, recipe in enumerate(recipes):
        if not counts[index]:
            continue
        if not recipe['inputs']:
            factors.append((index, 0, 0, False, 1))
            continue
        masks = []
        for port, code in enumerate(recipe['inputs']):
            allowed = []
            for ref in range(row):
                if ((1, ref) not in marks or marks[1, ref] == code) and (
                    (2 + port, row) not in marks or marks[2 + port, row] == ref - row):
                    allowed.append(ref)
            masks.append(sum(2 ** ref for ref in allowed))
        factors.append((index, masks[0], masks[1],
                        recipe['inputs'][0] != recipe['inputs'][1], counts[index]))
    return factors, keys


def raw_recipes(raw, expected_count, formula_count):
    if len(raw) != ROW.size * expected_count:
        raise ValueError('entire exact binary stream required')
    recipes = []
    for fields in ROW.iter_unpack(raw):
        tag, _, out, left, right = fields[:5]
        if tag not in range(5) or out >= formula_count:
            raise ValueError('complete raw catalog grammar required')
        inputs = (left, right) if tag == 3 else ()
        if ((not inputs and (left != SENTINEL or right != SENTINEL))
                or any(code >= formula_count for code in inputs)):
            raise ValueError('literal complete input codes required')
        recipes.append({'output': out, 'inputs': inputs})
    return recipes


def complete_counts(recipes, totals, marks, exclusions):
    """All recipes retained; only equivalence classes of the current marks coalesce.

    None represents a recipe code unequal to every currently assigned formula
    code. Distinctness of actual input codes is retained as its own class bit.
    Each class count is computed by enumerating every ordered prior row pair,
    rather than borrowing the producer's mask/popcount/factor/count functions.
    """
    assigned = {v for (x, y), v in marks.items() if x == 1 and 0 <= y < len(totals)}
    classes = Counter()
    for recipe in recipes:
        out = recipe['output'] if recipe['output'] in assigned else None
        inputs = recipe['inputs']
        if inputs:
            classes[(out, inputs[0] if inputs[0] in assigned else None,
                     inputs[1] if inputs[1] in assigned else None,
                     inputs[0] != inputs[1], True)] += 1
        else:
            classes[(out, None, None, False, False)] += 1
    result = []
    for row, total in enumerate(totals):
        base = 0
        if total != 1:
            for (out, left, right, different, ports), multiplicity in classes.items():
                if (1, row) in marks and marks[1, row] != out:
                    continue
                if not ports:
                    base += multiplicity
                    continue
                pairs = 0
                for a in range(row):
                    if ((1, a) in marks and marks[1, a] != left) or (
                        (2, row) in marks and marks[2, row] != a - row):
                        continue
                    for b in range(row):
                        if different and a == b:
                            continue
                        if ((1, b) in marks and marks[1, b] != right) or (
                            (3, row) in marks and marks[3, row] != b - row):
                            continue
                        pairs += 1
                base += multiplicity * pairs
        removed = []
        if total != 1:
            for index, target, refs in exclusions[row]:
                if target != row:
                    raise ValueError('exclusion in wrong row')
                values = point_marks(recipes[index], row, refs)
                if values is not None and all(p not in marks or marks[p] == v for p, v in values.items()):
                    removed.append((index, row, refs))
        result.append((base, base - len(removed)))
    return result


def global_decision(counts, totals, roots):
    frontier = [r for r, total in enumerate(totals) if total < 1]
    dead = [r for r in frontier if counts[r][1] == 0]
    forced = [r for r in frontier if counts[r][1] == 1]
    if dead:
        r = min(dead); return ('dead', r, 0, roots[r])
    if forced:
        r = min(forced); return ('forced', r, 1, roots[r])
    if not frontier:
        return ('complete', None, 0, None)
    r = min(frontier, key=lambda r: (roots[r], counts[r][1], r))
    return ('branch', r, counts[r][1], roots[r])


def reconstruct_union(recipes, height, fixed_marks, keys):
    totals = [0] * height
    marks = dict(fixed_marks)
    refs = {p: 1 for p in marks}
    for index, row, ports in keys:
        totals[row] += 1
        if totals[row] > 1:
            raise ValueError('whole union overcapacity')
        values = point_marks(recipes[index], row, ports)
        if values is None:
            raise ValueError('internally inconsistent placement')
        for p, v in values.items():
            if p in marks and marks[p] != v:
                raise ValueError('whole union mark conflict')
            marks[p] = v; refs[p] = refs.get(p, 0) + 1
    return totals, marks, refs
