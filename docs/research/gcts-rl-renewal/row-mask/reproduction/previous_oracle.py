"""Prospective production core oracle; SOURCE ONLY, no dispatcher or imports of project code.

ROOT must authenticate the original complete logical/static admission before
calling anything here. This literal raw-record oracle does not relicense logic.
Its factor relation certifies a full Cartesian candidate universe, without
materializing all keys or identifying distinct primitive licenses.
"""
from __future__ import annotations
import copy
import hashlib
import json
import struct
from pathlib import Path

HEIGHT = 24
FORMULAS = 113406
RECIPES = 119633
NON_ASSUMPTIONS = 119630
WORD = struct.Struct('<Q')
RECORD = struct.Struct('<11Q32s32s')
FACTOR = struct.Struct('<QQQBQ')
SENTINEL = (1 << 64) - 1
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
POINT_FIELDS = ('totals', 'marks', 'order', 'selected_generations', 'roots', 'excluded', 'model_epoch')
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_HEADER = {'path': str(ROOT / '.gcts-active/cluster-transfer-compact-identity-progress-20261012/train-pa-right-zero-preparation-v1/catalog-v1/catalog-v1.json'),
    'sha256': '633da6235551b2940bd4e5b39cba73e2c372a64e253f4851427d193f61ac027b', 'bytes': 13415}


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def closed_buffer(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}
         and type(record['path']) is str and type(record['bytes']) is int and record['bytes'] >= 0,
         'whole canonical ABS raw record')
    path = Path(record['path'])
    need(path.is_absolute() and str(path.resolve()) == record['path'], 'no lexical/symlink raw alias')
    before = path.stat()
    with path.open('rb') as stream:
        value = stream.read()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'closed immutable raw buffer')
    need(len(value) == record['bytes'] and hashlib.sha256(value).hexdigest() == record['sha256'],
         'every raw byte authenticated')
    return value


def verify_closed_stream(record, tick):
    """Full raw hashing without a nodes/gzip/AST expansion or retained buffer."""
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'whole exact stream pin')
    path = Path(record['path'])
    need(path.is_absolute() and str(path.resolve()) == record['path'], 'canonical ABS stream identity')
    before = path.stat(); h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        while True:
            value = stream.read(65536)
            if not value: break
            tick('raw_stream_hash'); h.update(value); size += len(value)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'unchanged closed stream')
    need(size == record['bytes'] and h.hexdigest() == record['sha256'], 'complete raw stream EOF/hash')


def streamed_model_epoch(header, recipe_bytes):
    seeds = [[index, row, []] for row, index in enumerate(header['assumption_recipe_indices'])]
    fixed = sorted(header['boundary']['fixed_exterior_m'] + header['boundary']['fixed_target_m'])
    value = {'height': HEIGHT, 'context': header['context'], 'registry': header['formula_registry_sha256'],
        'authority': header['authority']['epoch'], 'recipes': None, 'fixed_marks': fixed,
        'roots': [0] * HEIGHT, 'seed_keys': seeds,
        'marking_version': header['marking_version'], 'fixture': False, 'source_bindings': header['source_bindings']}
    h = hashlib.sha256(); h.update(b'{')
    for ordinal, field in enumerate(sorted(value)):
        if ordinal: h.update(b',')
        h.update(canonical(field).encode('utf8')); h.update(b':')
        if field == 'recipes':
            h.update(b'[')
            for index in range(RECIPES):
                if index: h.update(b',')
                identity = RECORD.unpack_from(recipe_bytes, index * RECORD.size)[11]
                h.update(canonical('primitive-recipe-' + identity.hex()).encode('utf8'))
            h.update(b']')
        else:
            h.update(canonical(value[field]).encode('utf8'))
    h.update(b'}')
    return h.hexdigest()


class RawProductionRelation:
    """Whole immutable binary relation + independently changed small point state.

    No decoder, graph, classifier, FactorStream, witness expansion or produced
    domain hash supplies expected multiplicities/masks. Original full logical
    acceptance is an authenticated prerequisite, not earned by this class.
    """
    def __init__(self, *, header_pin, admitted_header, tick):
        self.tick = tick; tick('raw_header')
        need(header_pin == EXPECTED_HEADER, 'only unchanged actual full train-pa-right-zero header')
        self.header_pin = copy.deepcopy(header_pin)
        self.header = json.loads(closed_buffer(header_pin))
        need(self.header == admitted_header, 'same whole independently admitted header')
        h = self.header
        need(h['schema'] == 'fresh-ground-compact-catalog-v1' and h['height'] == HEIGHT
             and h['orientation'] == 'identity' and h['marking_version'] == 'injective-formula-ordered-mp-offset-v1'
             and h['dimensions'] == {'logical_rows': HEIGHT, 'formula_count': FORMULAS,
                 'primitive_license_count': RECIPES, 'non_assumption_witness_count': NON_ASSUMPTIONS,
                 'source_body_count': 0} and h['bodies'] == [] and h['complete_cluster_inventory'] == [],
             'unchanged full production catalog and empty library')
        need(h['codec']['recipe_row_bytes'] == RECORD.size and RECORD.size == 152
             and h['codec']['formula_word_bytes'] == WORD.size and h['codec']['sentinel'] == SENTINEL
             and h['codec']['rules'] == list(RULES), 'unchanged exact binary grammar')
        self.formula_bytes = closed_buffer(h['streams']['formulas'])
        self.recipe_bytes = closed_buffer(h['streams']['recipes'])
        # Nodes are raw-hashed through the future leaf's streaming closed-pin
        # reader. Their complete AST/license authority stays with old static
        # admission; this oracle never expands a nodes JSONL or AST registry.
        verify_closed_stream(h['streams']['nodes'], tick)
        need(len(self.formula_bytes) == FORMULAS * 8 and len(self.recipe_bytes) == RECIPES * 152,
             'complete fixed-size stream EOF, no prefix catalog')
        node_count = h['codec']['node_count']
        for code in range(FORMULAS):
            if code % 4096 == 0: tick('full_formula_words')
            need(WORD.unpack_from(self.formula_bytes, code * 8)[0] < node_count, 'every complete formula word')
        occurrences = []
        for index in range(RECIPES):
            if index % 4096 == 0: tick('full_recipe_headers')
            f = RECORD.unpack_from(self.recipe_bytes, index * 152)
            tag, node, out, a, b, p0, p1, p2, p3, name, occurrence = f[:11]
            need(tag < 5 and out < FORMULAS and WORD.unpack_from(self.formula_bytes, out * 8)[0] == node,
                 'every output code/node and original rule')
            need((tag == 3 and a < FORMULAS and b < FORMULAS) or
                 (tag != 3 and a == SENTINEL and b == SENTINEL), 'complete zero/binary ports')
            if tag == 4:
                need(occurrence in (0, 1, 2) and index == h['assumption_recipe_indices'][occurrence]
                     and out == h['hypothesis_codes'][occurrence], 'separate ordered hypothesis licenses')
                occurrences.append(occurrence)
        need(sorted(occurrences) == [0, 1, 2], 'all three and only three assumption occurrences')
        self.model_epoch = streamed_model_epoch(h, self.recipe_bytes)
        self.totals = [0] * HEIGHT
        self.marks = {}; self.mark_refs = {}; self.order = []; self.selected = {}
        self.excluded = [set() for _ in range(HEIGHT)]; self.trail = []
        for x, y, value in h['boundary']['fixed_exterior_m'] + h['boundary']['fixed_target_m']:
            self.marks[x, y] = value; self.mark_refs[x, y] = 1
        for row, index in enumerate(h['assumption_recipe_indices']):
            self.apply((index, row, ()), generation=0)
        self.trail.clear()

    def record(self, index):
        need(type(index) is int and 0 <= index < RECIPES, 'full original recipe index')
        fields = RECORD.unpack_from(self.recipe_bytes, index * 152)
        return fields[0], fields[2], ((fields[3], fields[4]) if fields[0] == 3 else ())

    def state(self):
        return {'totals': list(self.totals), 'marks': [[*p, v, self.mark_refs[p]] for p, v in sorted(self.marks.items())],
            'order': [[i, r, list(refs)] for i, r, refs in self.order],
            'selected_generations': [[[i, r, list(refs)], g] for (i, r, refs), g in sorted(self.selected.items())],
            'roots': [0] * HEIGHT,
            'excluded': [[[i, r, list(refs)] for i, r, refs in sorted(keys)] for keys in self.excluded],
            'model_epoch': self.model_epoch}

    def classes(self):
        assigned = frozenset(v for (x, y), v in self.marks.items() if x == 1 and 0 <= y < HEIGHT)
        counts = {}
        for index in range(RECIPES):
            if index % 4096 == 0: self.tick('whole_classification')
            _, output, inputs = self.record(index)
            out = output if output in assigned else None
            key = ((2, out, inputs[0] if inputs[0] in assigned else None,
                    inputs[1] if inputs[1] in assigned else None, inputs[0] != inputs[1]) if inputs
                   else (0, out, None, None, False))
            counts[key] = counts.get(key, 0) + 1
        need(sum(counts.values()) == RECIPES, 'every distinct license counted exactly once')
        return tuple(sorted(assigned)), counts

    def factor(self, row, index):
        if self.totals[row] == 1: return None
        _, output, inputs = self.record(index)
        if (1, row) in self.marks and self.marks[1, row] != output: return None
        if not inputs: return (index, 0, 0, False, 1)
        masks = []
        for port, code in enumerate(inputs):
            allowed = []
            for offset in range(-23, 0):
                source = row + offset
                if ((1, source) in self.marks and self.marks[1, source] != code
                        or (2 + port, row) in self.marks and self.marks[2 + port, row] != offset):
                    continue
                need(0 <= source < row, 'negative sources rejected by original exterior m marks')
                allowed.append(source)
            masks.append(sum(1 << source for source in allowed))
        different = inputs[0] != inputs[1]
        # Ordered Cartesian pair count, with exactly the diagonal conflicts
        # removed. Raw input inequality is retained even when both classes None.
        left = [r for r in range(row) if masks[0] & (1 << r)]
        right = [r for r in range(row) if masks[1] & (1 << r)]
        count = len(left) * len(right) - (len(set(left).intersection(right)) if different else 0)
        return (index, masks[0], masks[1], different, count) if count else None

    def factors(self, row):
        need(type(row) is int and 0 <= row < HEIGHT, 'all required production rows')
        if self.totals[row] == 1: return
        for index in range(RECIPES):
            if index % 4096 == 0: self.tick('complete_factor_row')
            value = self.factor(row, index)
            if value is not None: yield value

    def legal(self, key, *, ignore_exclusion=False):
        index, row, refs = key
        if not (type(row) is int and 0 <= row < HEIGHT): return False
        _, _, inputs = self.record(index)
        if len(refs) != len(inputs) or any(type(ref) is not int or not 0 <= ref < row for ref in refs): return False
        if not ignore_exclusion and key in self.excluded[row]: return False
        f = self.factor(row, index)
        if f is None: return False
        return not inputs or bool(f[1] & (1 << refs[0]) and f[2] & (1 << refs[1]) and (not f[3] or refs[0] != refs[1]))

    def first_key(self, row):
        for index, left, right, different, _ in self.factors(row):
            inputs = self.record(index)[2]
            if not inputs:
                key = (index, row, ())
                if key not in self.excluded[row]: return key
            else:
                for a in range(row):
                    for b in range(row):
                        key = (index, row, (a, b))
                        if left & (1 << a) and right & (1 << b) and (not different or a != b) and key not in self.excluded[row]:
                            return key
        return None

    def point_values(self, key):
        index, row, refs = key; _, output, inputs = self.record(index)
        values = {(1, row): output}
        for port, (ref, code) in enumerate(zip(refs, inputs)):
            need((1, ref) not in values or values[1, ref] == code, 'literal local marking function')
            values[1, ref] = code; values[2 + port, row] = ref - row
        return values

    def apply(self, key, *, generation=1):
        need(self.legal(key) and key not in self.selected, 'actual complete literal legal catalog transaction')
        values = self.point_values(key); row = key[1]
        before = [(p, self.marks.get(p), self.mark_refs.get(p, 0)) for p in sorted(values)]
        affected = {row}
        for p, value in values.items():
            need(p not in self.marks or self.marks[p] == value, 'all literal remote marks agree')
            if p not in self.marks:
                if p[0] == 1 and 0 <= p[1] < HEIGHT: affected.update(range(p[1], HEIGHT))
                elif p[0] in (2, 3) and 0 <= p[1] < HEIGHT: affected.add(p[1])
                self.marks[p] = value
            self.mark_refs[p] = self.mark_refs.get(p, 0) + 1
        self.totals[row] += 1; self.order.append(key); self.selected[key] = generation
        self.trail.append(('place', key, before, frozenset(affected)))
        return frozenset(affected)

    def exclude(self, key):
        need(self.legal(key), 'exact restored parent literal key')
        self.excluded[key[1]].add(key); self.trail.append(('exclude', key))
        return frozenset((key[1],))

    def rollback(self, checkpoint):
        need(type(checkpoint) is int and 0 <= checkpoint <= len(self.trail), 'literal checkpoint')
        affected = set()
        while len(self.trail) > checkpoint:
            entry = self.trail.pop(); key = entry[1]
            if entry[0] == 'exclude': self.excluded[key[1]].remove(key); affected.add(key[1])
            else:
                need(self.order.pop() == key, 'literal nested primitive order')
                self.selected.pop(key); self.totals[key[1]] -= 1; affected.update(entry[3])
                for p, value, refs in entry[2]:
                    if refs: self.marks[p] = value; self.mark_refs[p] = refs
                    else: self.marks.pop(p); self.mark_refs.pop(p)
        return frozenset(affected)


def decision_from_counts(state, counts):
    frontier = [r for r in range(HEIGHT) if state['totals'][r] < 1]
    dead = [r for r in frontier if counts[r] == 0]
    if dead: return ['dead', min(dead), 0, 0]
    forced = [r for r in frontier if counts[r] == 1]
    if forced: return ['forced', min(forced), 1, 0]
    if not frontier: return ['complete', None, 0, None]
    row = min(frontier, key=lambda r: (0, counts[r], r))
    return ['branch', row, counts[row], 0]


def expected_graph_binding(reference, runtime_records):
    """Fresh runtime fields; original source/model lineage is deliberately retained."""
    h = reference.header
    fixed = sorted(h['boundary']['fixed_exterior_m'] + h['boundary']['fixed_target_m'])
    seeds = [[index, row, []] for row, index in enumerate(h['assumption_recipe_indices'])]
    return {'schema': 'sealed-compact-dynamic-graph-binding-v2', 'model_epoch': reference.model_epoch,
        'context_id': h['context_id'], 'formula_registry_sha256': h['formula_registry_sha256'],
        'authority_epoch': h['authority']['epoch'],
        'catalog_identity_sha256': digest({'header': reference.header_pin, 'streams': h['streams'], 'codec': h['codec']}),
        'catalog_header_pin': reference.header_pin, 'complete_catalog_stream_pins': h['streams'],
        'boundary_sha256': digest({'height': HEIGHT, 'roots': [0] * HEIGHT, 'fixed_marks': fixed, 'initial_selected': seeds}),
        'source_bindings_sha256': digest(h['source_bindings']),
        'runtime_source_bindings': sorted(copy.deepcopy(runtime_records), key=lambda item: item['role']),
        'marking_version': h['marking_version'], 'orientation': 'identity',
        'primitive_identity_relation': 'exact_original_complete_recipe_preimages_and_index_order',
        'native_accepted': False, 'engine_authority_activated': False}
