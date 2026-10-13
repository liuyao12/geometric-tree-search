"""Prospective finite point-contract differential tests; SOURCE only until ROOT runs.

No production catalog is loaded. Synthetic __new__ shells bypass construction
only in this explicit test profile and confer no source, licensing or proof
admission. Full production 54-state/1296-row qualification remains required.
"""
from types import MappingProxyType
from struct import Struct
import hashlib

HEIGHT = 24
CODES = (0, 7, 11, 17, 19)
PROFILES = (
    (), ((1, 0, 0),),
    ((1, 0, 0), (1, 1, 7), (1, 3, 0), (1, 4, 7), (1, 22, 11), (1, 23, 11)),
    ((1, 0, 0), (1, 1, 7), (1, 23, 11)),
    ((1, 0, 7), (1, 1, 0), (1, 23, 11)),
    ((1, 20, 7), (1, 21, 11), (1, 23, 13)), ((1, 23, 11),),
)
PACK = Struct('<QQQBQ')


def need(value, message):
    if not value:
        raise AssertionError(message)


def recipe(index):
    # Literal nonlogical records. Distinct indices are distinct test licenses;
    # no matching formula or actual mathematical license is supplied.
    records = ((0, ()), (0, ()), (7, (17, 19)), (7, (17, 17)),
               (7, (0, 7)), (7, (7, 0)), (7, (0, 0)), (11, ()),
               (11, (11, 11)), (7, (17, 19)))
    need(type(index) is int and 0 <= index < 10, 'literal test recipe index')
    return records[index]


class LiteralCatalog:
    recipe_count = 10

    def recipe_meta(self, index):
        # Keep immutable literals inside this no-closure/no-default method.
        records = ((0, ()), (0, ()), (7, (17, 19)), (7, (17, 17)),
                   (7, (0, 7)), (7, (7, 0)), (7, (0, 0)), (11, ()),
                   (11, (11, 11)), (7, (17, 19)))
        if type(index) is not int or not 0 <= index < 10:
            raise ValueError('literal test recipe index')
        output, inputs = records[index]
        return {'output': output, 'inputs': inputs}


def marks_for(profile):
    marks = {(1, row): -1 for row in range(-23, 0)}
    marks.update({(x, y): value for x, y, value in profile})
    return marks


def expected_support(row, port, code, marks):
    # Independent direct set specification, with no cached mask/table calls.
    return tuple(ref for ref in range(row)
                 if ((1, ref) not in marks or marks[1, ref] == code)
                 and ((2 + port, row) not in marks
                      or marks[2 + port, row] == ref - row))


def support_mask(refs):
    return sum(1 << ref for ref in refs)


def expected_factor(row, total, index, marks):
    output, inputs = recipe(index)
    if total == 1 or ((1, row) in marks and marks[1, row] != output):
        return None
    if not inputs:
        return (index, 0, 0, False, 1)
    left = expected_support(row, 0, inputs[0], marks)
    right = expected_support(row, 1, inputs[1], marks)
    different = inputs[0] != inputs[1]
    count = sum(1 for a in left for b in right if not different or a != b)
    return (index, support_mask(left), support_mask(right), different, count) if count else None


def factor_tuple(factor):
    return (factor.recipe, factor.left, factor.right, factor.different, factor.count)


def raw_shell(module, marks, row, total):
    # Explicit synthetic scalar test profile, never a production constructor.
    obj = module.RawProductionRelation.__new__(module.RawProductionRelation)
    obj.marks = dict(marks); obj.totals = [0] * HEIGHT; obj.totals[row] = total
    def literal_record(index):
        output, inputs = recipe(index)
        return (3 if inputs else 0), output, inputs
    obj.record = literal_record
    obj.mark_refs = {point: 1 for point in marks}; obj.order = []; obj.selected = {}
    obj.excluded = [set() for _ in range(HEIGHT)]; obj.trail = []
    obj.model_epoch = 'SYNTHETIC_POINT_CONTRACT_ONLY'
    if hasattr(obj, '_seal_row_mask_state'):
        obj.formula_bytes = b'SYNTHETIC_NO_FORMULA_DECODING'
        obj.recipe_bytes = b'SYNTHETIC_NO_RECIPE_DECODING'
        obj.header_pin = {'synthetic_point_contract_only': True}
        obj._factor_authority = (obj.formula_bytes, obj.recipe_bytes, obj.model_epoch,
                                 tuple(sorted(obj.header_pin.items())))
        obj._row_mask_revision = 0; obj._seal_row_mask_state()
    return obj


def compare_mask_case(modules, row, port, code, marks, checks):
    core = modules['core']; expected = expected_support(row, port, code, marks)
    mask = support_mask(expected); assigned = frozenset(v for (x, y), v in marks.items()
                                                      if x == 1 and 0 <= y < HEIGHT)
    table = modules['raw'].literal_row_masks(row, marks)
    need(type(table.marks) is MappingProxyType and table.assigned == assigned,
         'raw own immutable snapshot/assigned codes')
    absent = tuple(key for key in table.ports[port] if key not in assigned)
    need(len(absent) == 1, 'one private absent category')
    category = code if code in assigned else absent[0]
    need(table.ports[port][category] == (mask, len(expected)), 'raw mask/cardinality versus literal set')
    for key in ('old_compact', 'compact'):
        stream = modules[key].FactorStream(core, LiteralCatalog(), row, 0, marks)
        need(stream.mask(code, port) == mask, 'actual-code graph mask versus literal set')
        need(stream.mask(code if code in assigned else None, port) == mask,
             'collapsed graph mask versus literal set')
    checks['mask_cases'] += 1


def expected_receipt(row, factors, excluded):
    h = hashlib.sha256(); base = 0
    for factor in factors:
        h.update(PACK.pack(factor[0], factor[1], factor[2], int(factor[3]), factor[4]))
        base += factor[4]
    return {'row': row, 'factor_count': len(factors), 'bytes': PACK.size * len(factors),
            'sha256': h.hexdigest(), 'base_count': base,
            'excluded_legal': [key.data() for key in excluded], 'count': base - len(excluded)}


def receipt_shell(module, core, row, total, marks, excluded=()):
    # Real captured receipt methods, with a declared test-only authority shell.
    # Its guards check this synthetic profile, not full production source origin.
    graph_type = module.make_graph_type(core)
    class TestGraph(graph_type):
        def _classification_authority(self):
            return ('SYNTHETIC_POINT_CONTRACT_ONLY',)
        def assert_classification_integrity(self):
            if self._classification_integrity_token != 'SYNTHETIC_POINT_CONTRACT_ONLY':
                raise ValueError('test-only classification guard')
        def assert_runtime_integrity(self):
            self.assert_classification_integrity()
    g = TestGraph.__new__(TestGraph)
    g.height = HEIGHT; g.catalog = LiteralCatalog()
    g.totals = [0] * HEIGHT; g.totals[row] = total
    g.marks = dict(marks); g.mark_refs = {point: 1 for point in marks}
    g.order = []; g.selected = {}; g.roots = [0] * HEIGHT
    g.excluded = [set() for _ in range(HEIGHT)]; g.excluded[row].update(excluded)
    g.model_epoch = 'SYNTHETIC_POINT_CONTRACT_ONLY'; g.trail = []
    g.metrics = {'domain_refreshes': 0}
    g.compact_metrics = {'streamed_factor_records': 0, 'streamed_factor_bytes': 0}
    g._dynamic_revision = 0
    g._classification_integrity_token = 'SYNTHETIC_POINT_CONTRACT_ONLY'
    domains = []
    for r in range(HEIGHT):
        values = tuple(value for index in range(10)
                       for value in (expected_factor(r, g.totals[r], index, marks),)
                       if value is not None)
        base = sum(value[4] for value in values)
        removed = tuple(sorted(excluded)) if r == row else ()
        domains.append(core.Domain(module.FactorStream(core, g.catalog, r,
                                  g.totals[r], marks), base, removed, base - len(removed)))
    g.domains = domains
    return g


class VisitorFault(ValueError):
    pass


def must_reject(call, message):
    try:
        call()
    except (ValueError, TypeError, AttributeError, VisitorFault):
        return
    raise AssertionError(message)


def run_controls(*, modules, tick):
    """ROOT-only prospective entry; no caller may infer production acceptance."""
    need(set(modules) >= {'core', 'old_compact', 'compact', 'old_raw', 'raw'}, 'exact required module roles')
    need(callable(tick), 'owner bounded tick callback')
    core = modules['core']; checks = {'mask_cases': 0, 'factor_cases': 0,
        'factor_stream_EOFs': 0, 'receipt_cases': 0, 'visitor_rejects': 0,
        'immutable_rejects': 0, 'signature_cases': 0, 'raw_guard_rejects': 0, 'raw_remote_restore': 0, 'descriptor_rejects': 0}
    # These two malformed classes reproduce the source-review descriptor gap.
    # The selected static recipe method remains the pinned no-closure literal.
    class HiddenDict:
        recipe_count = 10
        recipe_meta = LiteralCatalog.recipe_meta
        __dict__ = {'mutable': []}
    class HiddenWeakref:
        recipe_count = 10
        recipe_meta = LiteralCatalog.recipe_meta
        __weakref__ = {'mutable': []}
    for cls in (HiddenDict, HiddenWeakref):
        must_reject(lambda: modules['compact'].FactorStream(core, cls(), 3, 0, marks_for(())),
                    'mutable bare descriptor accepted')
        checks['descriptor_rejects'] += 1
    offsets = (None,) + tuple(range(-24, 2))
    for row in range(HEIGHT):
        tick('finite-mask-grid')
        for port in (0, 1):
            for code in CODES:
                for offset in offsets:
                    for other_offset in (None, 0):
                        marks = marks_for(PROFILES[2])
                        if offset is not None: marks[2 + port, row] = offset
                        if other_offset is not None: marks[3 - port, row] = other_offset
                        compare_mask_case(modules, row, port, code, marks, checks)
            for profile in PROFILES:
                for code in CODES:
                    compare_mask_case(modules, row, port, code, marks_for(profile), checks)
    for profile in PROFILES:
        marks = marks_for(profile); obj = raw_shell(modules['raw'], marks, 0, 0)
        expected = tuple(sorted({v for (x, y), v in marks.items() if x == 1 and 0 <= y < HEIGHT}))
        need(obj.assigned_signature() == expected, 'signature-only accessor reads own literal marks')
        checks['signature_cases'] += 1
    # Bounded raw stream prefixes deliberately REJECT after official writers;
    # they never substitute for full 119633-record natural EOF qualification.
    for action in ('apply', 'noop_rollback', 'tick_marks', 'tick_totals'):
        obj = raw_shell(modules['raw'], marks_for(()), 3, 0)
        def raw_tick(label):
            tick(label)
            if action == 'tick_marks': obj.marks[1, 0] = 19
            elif action == 'tick_totals': obj.totals[0] = 1
        obj.tick = raw_tick; iterator = iter(obj.factors(3))
        try:
            if action in ('apply', 'noop_rollback'):
                need(next(iterator) == (0, 0, 0, False, 1), 'raw initial scalar stream prefix')
                if action == 'apply': obj.apply((0, 4, ()))
                else: obj.rollback(0)
            must_reject(lambda: next(iterator), 'stale/direct-mutation raw stream accepted')
            checks['raw_guard_rejects'] += 1
        finally:
            iterator.close()
    obj = raw_shell(modules['raw'], marks_for(()), 22, 0); obj.tick = tick
    before = obj.state(); affected = obj.apply((2, 22, (20, 21)))
    need(affected == frozenset((20, 21, 22, 23)) and obj.totals[20] == obj.totals[21] == 0
         and obj.marks[1, 20] == 17 and obj.marks[1, 21] == 19
         and obj.marks[2, 22] == -2 and obj.marks[3, 22] == -1,
         'raw remote unoccupied literal marks and exact affected union')
    need(obj.rollback(0) == affected and obj.state() == before, 'raw exact remote point/refcount rollback')
    checks['raw_remote_restore'] += 1
    for row in range(HEIGHT):
        tick('finite-factor-grid')
        for profile in PROFILES:
            for total in (0, 1):
                for output_mark in (None, 0, 7, 11, 19):
                    for left_offset, right_offset in ((None, None), (-1, -2), (-2, -1), (0, None), (None, 0)):
                        marks = marks_for(profile)
                        if output_mark is not None: marks[1, row] = output_mark
                        if left_offset is not None: marks[2, row] = left_offset
                        if right_offset is not None: marks[3, row] = right_offset
                        expected = []
                        old_raw = raw_shell(modules['old_raw'], marks, row, total)
                        new_raw = raw_shell(modules['raw'], marks, row, total)
                        table = modules['raw'].literal_row_masks(row, marks)
                        for index in range(10):
                            value = expected_factor(row, total, index, marks)
                            need(old_raw.factor(row, index) == value and new_raw.factor(row, index) == value,
                                 'prior and retained raw scalar factor versus direct pair enumeration')
                            output, inputs = recipe(index)
                            fast = None if total == 1 else modules['raw'].literal_factor_from_masks(table, index, output, inputs)
                            need(fast == value, 'raw pure table factor versus direct pair enumeration')
                            if value is not None: expected.append(value)
                            checks['factor_cases'] += 1
                        for role in ('old_compact', 'compact'):
                            stream = iter(modules[role].FactorStream(core, LiteralCatalog(), row, total, marks))
                            for value in expected:
                                actual = next(stream, None)
                                need(actual is not None and factor_tuple(actual) == value,
                                     'complete ordered synthetic factor sequence')
                            need(next(stream, None) is None, 'mutual complete synthetic factor EOF')
                            checks['factor_stream_EOFs'] += 1
    # Mutation of constructor inputs cannot change the copied snapshot.
    marks = marks_for(PROFILES[2]); table = modules['raw'].literal_row_masks(5, marks)
    old_table_marks = dict(table.marks); marks[1, 0] = 19
    need(dict(table.marks) == old_table_marks, 'raw snapshot independent of caller dict mutation')
    must_reject(lambda: table.marks.__setitem__((1, 0), 19), 'raw copied marks mutable')
    checks['immutable_rejects'] += 1
    must_reject(lambda: table.ports[0].__setitem__(0, (0, 0)), 'raw port table mutable')
    checks['immutable_rejects'] += 1
    must_reject(lambda: table.counts.__setitem__((0, 0, False), 99), 'raw pair count table mutable')
    checks['immutable_rejects'] += 1
    stream = modules['compact'].FactorStream(core, LiteralCatalog(), 5, 0, old_table_marks)
    for field in ('_marks', '_row_masks', '_pair_counts'):
        proxy = getattr(stream, field)
        need(type(proxy) is MappingProxyType, 'graph owned table/marks readonly proxy')
        key = next(iter(proxy))
        must_reject(lambda: proxy.__setitem__(key, 99), 'graph proxy permits mutation')
        checks['immutable_rejects'] += 1
        must_reject(lambda: setattr(stream, field, MappingProxyType({})), 'graph table origin permits replacement')
        checks['immutable_rejects'] += 1
    for field, value in (('_absent_code', object()), ('_integrity_token', ()), ('_sealed', False)):
        must_reject(lambda: setattr(stream, field, value), 'graph sentinel/seal ordinary replacement accepted')
        checks['immutable_rejects'] += 1
    # Own copied marks survive caller mutation; complete EOF rechecks the seal.
    input_marks = marks_for(PROFILES[2])
    stream = modules['compact'].FactorStream(core, LiteralCatalog(), 5, 0, input_marks)
    snapshot = stream.snapshot(); input_marks[1, 0] = 19
    need(stream.snapshot() == snapshot, 'graph stream aliases caller marks')
    checks['immutable_rejects'] += 1
    for row, total, profile in ((0, 0, ((1, 0, 11),)), (3, 1, ()), (3, 0, ())):
        tick('finite-receipt-parity')
        marks = marks_for(profile)
        factors = tuple(value for i in range(10) for value in (expected_factor(row, total, i, marks),) if value is not None)
        for n_excluded in ((0, 1, 2) if row == 3 and total == 0 else (0,)):
            excluded = (core.Key(2, row, (0, 1)), core.Key(9, row, (1, 2)))[:n_excluded]
            expected = expected_receipt(row, factors, excluded)
            old = receipt_shell(modules['old_compact'], core, row, total, marks, excluded)
            need(old.domain_stream_receipt(row) == expected, 'actual prior receipt versus own packed syntax')
            for returned in (None, False, True, 0, 'ignored', {'ignored': True}):
                g = receipt_shell(modules['compact'], core, row, total, marks, excluded); seen = []
                def collect(factor):
                    seen.append(factor_tuple(factor)); return returned
                need(g.domain_stream_receipt(row, factor_visitor=collect) == expected and tuple(seen) == factors,
                     'actual successor receipt and ordered visitor parity')
                checks['receipt_cases'] += 1
            g = receipt_shell(modules['compact'], core, row, total, marks, excluded)
            need(g.domain_stream_receipt(row) == expected, 'successor no-visitor prior API parity')
            checks['receipt_cases'] += 1
    # Callback exceptions and persistent/revision mutations including the final factor.
    row = 3; marks = marks_for(()); length = 10
    for at in (0, length // 2, length - 1):
        for action in ('raise', 'point', 'total', 'revision', 'noop_revision', 'domain', 'other_domain', 'factor', 'excluded', 'refs', 'trail', 'token', 'metrics', 'mask_write', 'mask_replace'):
            tick('finite-visitor-reject')
            g = receipt_shell(modules['compact'], core, row, 0, marks); seen = [0]
            def visit(factor):
                ordinal = seen[0]; seen[0] += 1
                if ordinal != at: return
                if action == 'raise': raise VisitorFault('declared callback error')
                if action == 'point': g.marks[1, 0] = 19
                elif action == 'total': g.totals[0] = 1
                elif action in ('revision', 'noop_revision'): g._dynamic_revision += 1
                elif action == 'domain':
                    d = g.domains[row]; g.domains[row] = core.Domain(d.factors, d.base_count, d.excluded_legal, d.count)
                elif action == 'other_domain':
                    d = g.domains[0]; g.domains[0] = core.Domain(d.factors, d.base_count, d.excluded_legal, d.count)
                elif action == 'factor': factor.count = 99
                elif action == 'excluded': g.excluded[row].add(core.Key(2, row, (0, 1)))
                elif action == 'refs': g.mark_refs[1, -1] += 1
                elif action == 'trail': g.trail.append(('exclude', core.Key(2, row, (0, 1))))
                elif action == 'token': g._classification_integrity_token = 'tampered'
                elif action == 'metrics': g.compact_metrics['streamed_factor_records'] += 1
                elif action == 'mask_write': g.domains[row].factors._row_masks.__setitem__((0, 0), 99)
                elif action == 'mask_replace': g.domains[row].factors._row_masks = MappingProxyType({})
            must_reject(lambda: g.domain_stream_receipt(row, factor_visitor=visit), 'callback mutation/error accepted')
            checks['visitor_rejects'] += 1
    # A bounded read-only nested receipt changes diagnostic counters: the
    # final API explicitly treats that as a visitor mutation and rejects it.
    g = receipt_shell(modules['compact'], core, row, 0, marks); nested = [False]
    def reentrant(factor):
        if not nested[0]:
            nested[0] = True; g.domain_stream_receipt(row)
    must_reject(lambda: g.domain_stream_receipt(row, factor_visitor=reentrant), 'nested metric-changing receipt accepted')
    checks['visitor_rejects'] += 1
    # Test malformed actual factor validation using an explicitly test-only
    # finite subclass. This is not a production catalog or origin bypass claim.
    class MalformedStream(modules['compact'].FactorStream):
        def __init__(self, catalog, values):
            self._fixture_values = values
            super().__init__(core, catalog, row, 0, marks)
        def __iter__(self):
            yield from self._fixture_values
    normal = tuple(core.Factor(*expected_factor(row, 0, i, marks)) for i in range(10))
    malformed = (
        normal[0:1] + normal[0:1] + normal[1:],
        normal[1:2] + normal[0:1] + normal[2:],
        (core.Factor(0, 0, 0, False, 0),) + normal[1:],
        (core.Factor(0, 0, 0, 0, 1),) + normal[1:],
        (core.Factor(0, 1 << row, 0, False, 1),) + normal[1:],
    )
    for values in malformed:
        g = receipt_shell(modules['compact'], core, row, 0, marks); d = g.domains[row]
        g.domains[row] = core.Domain(MalformedStream(g.catalog, values), d.base_count, d.excluded_legal, d.count)
        must_reject(lambda: g.domain_stream_receipt(row), 'malformed actual factor tape accepted')
        checks['visitor_rejects'] += 1
    # Independent visitor comparator must consume exact order and require raw EOF.
    expected = tuple(expected_factor(row, 0, i, marks) for i in range(10))
    for bad in (expected[1:2] + expected[0:1] + expected[2:], expected[:-1], expected + expected[-1:]):
        g = receipt_shell(modules['compact'], core, row, 0, marks); iterator = iter(bad)
        def compare(factor):
            value = next(iterator, None)
            if value is None or factor_tuple(factor) != value: raise VisitorFault('ordered expected mismatch')
        try:
            g.domain_stream_receipt(row, factor_visitor=compare)
            if next(iterator, None) is not None: raise VisitorFault('expected stream missing EOF')
        except VisitorFault:
            checks['visitor_rejects'] += 1
        else:
            raise AssertionError('bad independent expected stream accepted')
    expected_checks = {'mask_cases': 24 * 2 * (5 * 27 * 2 + 7 * 5),
        'factor_cases': 24 * 7 * 2 * 5 * 5 * 10,
        'factor_stream_EOFs': 24 * 7 * 2 * 5 * 5 * 2,
        'receipt_cases': 7 + 7 + 3 * 7,
        'visitor_rejects': 3 * 15 + 1 + 5 + 3,
        'immutable_rejects': 3 + 3 * 2 + 3 + 1, 'signature_cases': 7,
        'raw_guard_rejects': 4, 'raw_remote_restore': 1, 'descriptor_rejects': 2}
    need(checks == expected_checks, 'complete finite declared census; no skipped grid/control')
    tick('finite-complete')
    return {'schema': 'row-mask-finite-point-contract-controls-v1', 'status': 'LOCAL_FINITE_CONTROLS_COMPLETED',
            'all_checks_passed': True, 'checks': checks, 'complete_declared_synthetic_grids': True,
            'production_catalog_loaded': False, 'production_source_authority_admitted': False,
            'actual_dynamic_adapter_qualified': False, 'bare_provider_generic_negative_qualified': False,
            'full_production54_1296_qualified': False,
            'production_resource_fit_qualified': False, 'candidate_key_EOF_qualified': False,
            'proof_accepted': False, 'theorem_discovered': False, 'RL_or_search_advantage': False,
            'supplied_theorem_route': False}
