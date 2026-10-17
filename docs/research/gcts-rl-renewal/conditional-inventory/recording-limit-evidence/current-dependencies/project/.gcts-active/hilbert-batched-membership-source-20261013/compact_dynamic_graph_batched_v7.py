"""SOURCE ONLY: sealed catalog and dynamic complete-domain compact graph.

No project imports or dispatcher. ROOT must separately qualify the complete
catalog, all exact sources, dynamic equivalence and the owned resource envelope.
This is the unit-occupancy ordered-proof-row specialization, not a general
fractional/shared-support tiler. No current catalog/worker qualification implies
this new runtime is admitted. No proof route, target heuristic or inventory is
created by this adapter.
"""
from __future__ import annotations
import gzip
import hashlib
import io
import json
import math
import time
from collections.abc import Sequence
from pathlib import Path

VERSION = 'compact-complete-dynamic-reversible-classification-batched-adapter-v7'
STATE_SCHEMA = 'compact-complete-dynamic-point-state-v2'
BINDING_SCHEMA = 'sealed-compact-dynamic-graph-binding-v2'
ORDER_SCHEMA = 'complete-compact-ordered-domain-descriptor-v2'
DEPENDENCY_SCHEMA = 'ordered-proof-row-full-mark-dependency-v1'
FROZEN_SOURCES = {
    'point_core': 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd',
    'compact_graph': 'c7af8a415670dd54a3177fda823a0c3fb0bbcc582e59125a974ea19de06748e6',
    'compact_decoder': '46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293',
}
RUNTIME_ROLES = frozenset((*FROZEN_SOURCES, 'dynamic_graph_adapter', 'dynamic_lifecycle_adapter'))

BATCH_BINDING_SCHEMA = 'exact-selected-domain-membership-binding-v1'
BATCH_RECEIPT_SCHEMA = 'exact-batched-selected-domain-membership-v1'
MAXIMUM_BATCH_KEYS = 64


class MembershipBudgetExceeded(Exception):
    """No Boolean prefix escapes; receipt contains only censored diagnostics."""

    def __init__(self, message, *, receipt):
        super().__init__(message)
        self.receipt = receipt


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def exact_int(value):
    if type(value) is not int:
        raise ValueError('exact integer required')
    return value


def pinned_buffer(pin):
    """Future ROOT-owned byte operation; no source-author invocation.

    Retained binary buffers are immutable bytes, not shared mutable mmap views.
    All allocation/reading/hashing/closing is inside the same owned phase.
    """
    if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
            or type(pin['path']) is not str or type(pin['sha256']) is not str
            or len(pin['sha256']) != 64 or exact_int(pin['bytes']) < 0):
        raise ValueError('exact complete immutable byte pin required')
    path = Path(pin['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise ValueError('runtime pins use canonical ABS identities')
    value = path.read_bytes()
    if len(value) != pin['bytes'] or hashlib.sha256(value).hexdigest() != pin['sha256']:
        raise ValueError('runtime/catalog bytes differ from exact closed pin')
    return value


def bind_runtime_sources(records, core, compact, decoder):
    if type(records) is not list:
        raise ValueError('all runtime source records required')
    bound = {}
    for record in records:
        if type(record) is not dict or set(record) != {'role', 'path', 'sha256', 'bytes'}:
            raise ValueError('exact role and complete runtime source pin required')
        role = record['role']
        if role in bound or role not in RUNTIME_ROLES:
            raise ValueError('duplicate or unknown runtime role')
        pin = {key: record[key] for key in ('path', 'sha256', 'bytes')}
        pinned_buffer(pin)
        if role in FROZEN_SOURCES and pin['sha256'] != FROZEN_SOURCES[role]:
            raise ValueError('unchanged borrowed runtime source required')
        bound[role] = pin
    if set(bound) != RUNTIME_ROLES:
        raise ValueError('complete source closure, including fresh lifecycle, required')
    origins = {'point_core': core.PointGraph.__init__.__code__.co_filename,
               'compact_graph': compact.make_graph_type.__code__.co_filename,
               'compact_decoder': decoder.CompactCatalog.__init__.__code__.co_filename,
               'dynamic_graph_adapter': make_dynamic_graph_type.__code__.co_filename}
    if any(str(Path(origin).resolve()) != bound[role]['path'] for role, origin in origins.items()):
        raise ValueError('provided runtime object does not originate in pinned source')
    return tuple((role, canonical(bound[role])) for role in sorted(bound))


def immutable_catalog_type(decoder):
    """Borrow only the exact decoder methods; preserve every wire record.

    The public header is a fresh small JSON value on each read; internal names,
    nodes and both full raw binary streams are immutable. No mutable mapping or
    reference to an original live decoder is retained. This seals trusted Python
    objects against ordinary mutation, not adversarial object.__setattr__ use.
    """
    class ImmutableCatalog(decoder.CompactCatalog):
        __slots__ = ()

        def __setattr__(self, name, value):
            if getattr(self, '_sealed', False):
                raise ValueError('sealed catalog requires a fresh independently admitted model')
            object.__setattr__(self, name, value)

        @property
        def header(self):
            return json.loads(self._header_text)

        def __init__(self, header_pin):
            self._sealed = False
            raw = pinned_buffer(header_pin); header = json.loads(raw)
            self._header_text = canonical(header)
            self.header_path = Path(header_pin['path'])
            self.header_pin_text = canonical(header_pin)
            codec = header['codec']; dimensions = header['dimensions']
            if (header['schema'] != decoder.WIRE or header['declaration_schema'] != decoder.DECLARATION
                    or header['height'] != 24 or header['marking_version'] != decoder.MARKING
                    or codec['formula_word_bytes'] != 8 or codec['byte_order'] != 'little'
                    or codec['recipe_row_bytes'] != decoder.ROW.size or codec['sentinel'] != decoder.SENTINEL
                    or codec['rules'] != list(decoder.RULES) or codec['recipe_fields'] != decoder.FIELDS
                    or set(header['streams']) != {'nodes', 'formulas', 'recipes'}):
                raise ValueError('exact unchanged complete compact codec required')
            self.formula_count = dimensions['formula_count']; self.recipe_count = dimensions['primitive_license_count']
            if (type(self.formula_count) is not int or self.formula_count <= 0
                    or type(self.recipe_count) is not int or self.recipe_count < 3
                    or dimensions != {'logical_rows': 24, 'formula_count': self.formula_count,
                        'primitive_license_count': self.recipe_count,
                        'non_assumption_witness_count': self.recipe_count - 3, 'source_body_count': 0}):
                raise ValueError('complete declared catalog counts required')
            for pin in header['streams'].values():
                if Path(pin['path']).parent != self.header_path.parent:
                    raise ValueError('all streams belong to exactly this closed catalog')
            self._formula_map = pinned_buffer(header['streams']['formulas'])
            self._recipe_map = pinned_buffer(header['streams']['recipes'])
            if (len(self._formula_map) != 8 * self.formula_count
                    or len(self._recipe_map) != decoder.ROW.size * self.recipe_count):
                raise ValueError('complete fixed-size stream lengths required')
            self.names = tuple(codec['names'])
            if list(self.names) != sorted(set(self.names)) or not all(type(name) is str for name in self.names):
                raise ValueError('injective sorted command-name table required')
            node_bytes = pinned_buffer(header['streams']['nodes'])
            self.nodes = []
            with gzip.GzipFile(fileobj=io.BytesIO(node_bytes), mode='rb') as stream:
                for line in stream:
                    value = json.loads(line)
                    if type(value) is not list or not value or value[0] != len(self.nodes):
                        raise ValueError('contiguous complete immutable node stream required')
                    self.nodes.append(self._node_record(value[1:]))
            if len(self.nodes) != codec['node_count']:
                raise ValueError('complete node count mismatch')
            self.nodes = tuple(self.nodes)
            self._sealed = True

        def close(self):
            # There are no open file/mmap handles. Lifetime ends when the owned
            # worker drops this immutable graph; original decoder.close is not used.
            return None

    return ImmutableCatalog


class RecipeMetadataView(Sequence):
    """Indexed exact fields required by unchanged31 features, no palette copy."""
    __slots__ = ('catalog',)

    def __init__(self, catalog):
        self.catalog = catalog

    def __len__(self):
        return self.catalog.recipe_count

    def __getitem__(self, index):
        if isinstance(index, slice):
            raise ValueError('feature recipe metadata is indexed, never expanded')
        meta = self.catalog.recipe_meta(exact_int(index))
        return {'output': meta['output'], 'inputs': list(meta['inputs']), 'rule': meta['rule']}


class FormulaHeadView(Sequence):
    """Only the top constructor used by unchanged31 features; not a formula API."""
    __slots__ = ('catalog',)

    def __init__(self, catalog):
        self.catalog = catalog

    def __len__(self):
        return self.catalog.formula_count

    def __getitem__(self, code):
        if isinstance(code, slice):
            raise ValueError('formula-head feature view is indexed only')
        node = self.catalog.node_for_formula_code(exact_int(code))
        return (self.catalog.node_record(node)[0],)


class OrderedDomain:
    """Complete preferred-plus-canonical-fallback permutation, constant per key.

    Holds only up to64 preferred exact keys and a complete compact state binding.
    Full candidate identity multiplicity and order are preserved. Counts come
    from complete qualified factor algebra; a diagnostic receipt can enumerate
    the whole stream, but no enumeration is needed to obtain its first key.
    No slicing, sampling or candidate-prefix authority is provided.
    """
    __slots__ = ('graph', 'decision', 'preferred', '_preferred_set', '_revision', '_state_sha', '_cursor')

    def __init__(self, graph, decision, preferred=()):
        if decision != graph.decision() or decision.kind not in ('branch', 'forced'):
            raise ValueError('current mandatory global decision required')
        if type(preferred) not in (tuple, list) or len(preferred) > 64:
            raise ValueError('complete bounded advice sequence required; no prefix salvage')
        keys = tuple(dict.fromkeys(preferred))
        if len(keys) > 64:
            raise ValueError('complete64-descriptor advice capacity exceeded; never trim')
        if any(key.row != decision.row or not graph.legal(key) for key in keys):
            raise ValueError('every preferred key must belong to complete current chosen domain')
        if decision.kind == 'forced' and keys:
            raise ValueError('forced singleton has no advice permutation')
        self.graph = graph; self.decision = decision; self.preferred = keys
        self._preferred_set = frozenset(keys); self._revision = graph._dynamic_revision
        self._state_sha = digest(graph.semantic_state()); self._cursor = None

    def __next__(self):
        # Retain next(control.ordered(decision)) compatibility without creating
        # a full domain. Explicit iter(self) remains a fresh sealed traversal.
        if self._cursor is None:
            self._cursor = self.__iter__()
        return next(self._cursor)

    def __len__(self):
        return self.decision.count

    def _check(self):
        self.graph.assert_runtime_integrity()
        if self._revision != self.graph._dynamic_revision:
            raise ValueError('ordered domain is stale after any placement/exclusion/rollback')

    def __iter__(self):
        self._check()
        for key in self.preferred:
            self._check(); yield key
        iterator = self.graph.candidates(self.decision.row)
        while True:
            self._check()
            try:
                key = next(iterator)
            except StopIteration:
                break
            if key not in self._preferred_set:
                yield key

    def first(self):
        return next(iter(self))

    def descriptor(self):
        self._check()
        return {'schema': ORDER_SCHEMA, 'decision': [self.decision.kind, self.decision.row,
                    self.decision.count, self.decision.generation],
                'complete_count': self.decision.count, 'preferred_keys': [key.data() for key in self.preferred],
                'canonical_fallback': 'recipe_index_then_ordered_strict_prior_refs_skipping_only_exact_preferred_and_excluded',
                'state_sha256': self._state_sha,
                'catalog_identity_sha256': self.graph.catalog_identity_sha,
                'runtime_authority_sha256': self.graph.runtime_authority_sha,
                'full_stream_hash_measured': False, 'native_accepted': False}

    def stream_receipt(self):
        """Optional whole diagnostic operation, fully charged; not a license."""
        count = 0; h = hashlib.sha256()
        for key in self:
            h.update((canonical(key.data()) + '\n').encode('utf8')); count += 1
        if count != self.decision.count:
            raise AssertionError('complete ordered stream differs from exact factor count')
        return {'schema': 'complete-compact-order-literal-stream-receipt-v1',
                'count': count, 'sha256': h.hexdigest(), 'descriptor': self.descriptor(),
                'logical_accepted': False, 'native_accepted': False}


def make_dynamic_graph_type(core, compact, decoder, *, runtime_sources):
    """Explicit source-bound factory; never loads/imports project modules here."""
    source_records = bind_runtime_sources(runtime_sources, core, compact, decoder)
    catalog_type = immutable_catalog_type(decoder)
    base_type = compact.make_graph_type(core)

    class DynamicCompactGraph(base_type):
        _bound_core = core
        MembershipBudgetExceeded = MembershipBudgetExceeded

        def __init__(self, *, header_pin):
            self._dynamic_ready = False; self._dynamic_revision = 0
            catalog = catalog_type(header_pin)
            super().__init__(catalog=catalog)
            self._runtime_source_records = source_records
            self.catalog_identity_sha = digest({'header': json.loads(catalog.header_pin_text),
                'streams': catalog.header['streams'], 'codec': catalog.header['codec']})
            self._binding_text = canonical({'schema': BINDING_SCHEMA,
                'model_epoch': self.model_epoch, 'context_id': self.context_id,
                'formula_registry_sha256': self.registry_sha, 'authority_epoch': self.authority_epoch,
                'catalog_identity_sha256': self.catalog_identity_sha,
                'catalog_header_pin': json.loads(catalog.header_pin_text),
                'complete_catalog_stream_pins': catalog.header['streams'],
                'boundary_sha256': digest({'height': self.height, 'roots': self.roots,
                    'fixed_marks': [[*point, value] for point, value in sorted(self.initial_marks.items())],
                    'initial_selected': [key.data() for key in self.initial_selected]}),
                'source_bindings_sha256': digest(self.source_bindings),
                'runtime_source_bindings': [{'role': role, **json.loads(text)} for role, text in source_records],
                'marking_version': core.MARKING_VERSION, 'orientation': 'identity',
                'primitive_identity_relation': 'exact_original_complete_recipe_preimages_and_index_order',
                'native_accepted': False, 'engine_authority_activated': False})
            self.runtime_authority_sha = digest(json.loads(self._binding_text))
            self._metadata_text = canonical(self._metadata())
            self._catalog_objects = (catalog, catalog.nodes, catalog.names,
                                     catalog._formula_map, catalog._recipe_map)
            self._view_objects = (self.formulas, self.recipes, self.recipe_index)
            self._tracked_state_text = canonical(self._mutable_state())
            self._dynamic_ready = True
            self.assert_runtime_integrity()

        def _metadata(self):
            return {'height': self.height, 'fixture': self.fixture, 'model_epoch': self.model_epoch,
                    'context_id': self.context_id, 'context': self.context,
                    'registry_sha256': self.registry_sha, 'authority_epoch': self.authority_epoch,
                    'authority': self.authority, 'source_bindings': self.source_bindings,
                    'roots': self.roots, 'initial_marks': [[*point, value] for point, value in sorted(self.initial_marks.items())],
                    'initial_selected': [key.data() for key in self.initial_selected],
                    'runtime_source_records': self._runtime_source_records,
                    'catalog_identity_sha256': self.catalog_identity_sha,
                    'runtime_authority_sha256': self.runtime_authority_sha,
                    'binding_text': self._binding_text, 'marking_version': core.MARKING_VERSION}

        def _mutable_state(self):
            # This is a small transaction-integrity guard, not a candidate list
            # or licensing claim. Metrics/classification caches are diagnostic.
            trail = []
            for entry in self.trail:
                if entry[0] == 'exclude':
                    trail.append(['exclude', entry[1].data()])
                elif entry[0] == 'place':
                    trail.append(['place', entry[1].data(), entry[2], entry[3]])
                else:
                    raise AssertionError('unknown exact primitive transaction')
            return {'totals': list(self.totals),
                'marks': [[*point, value] for point, value in sorted(self.marks.items())],
                'mark_refs': [[*point, value] for point, value in sorted(self.mark_refs.items())],
                'selected': [[key.data(), value] for key, value in sorted(self.selected.items())],
                'order': [key.data() for key in self.order],
                'excluded': [[key.data() for key in sorted(keys)] for keys in self.excluded],
                'trail': trail,
                'domain_guards': [{'row': row, 'factor_row': domain.factors.row,
                    'factor_total': domain.factors.total,
                    'base_count': domain.base_count, 'count': domain.count,
                    'excluded_legal': [key.data() for key in domain.excluded_legal],
                    'marks_used': self._dependencies(row, domain.factors._marks),
                    'marks_recorded': self._dependencies(row, dict(domain.factors._mark_items))}
                    for row, domain in enumerate(self.domains)]}

        def assert_runtime_integrity(self):
            if not self._dynamic_ready:
                return
            if canonical(self._metadata()) != self._metadata_text:
                raise ValueError('stale rule/context/boundary/source/catalog authority; continuation is UNKNOWN')
            catalog, nodes, names, formulas, recipes = self._catalog_objects
            if (self.catalog is not catalog or catalog.nodes is not nodes or catalog.names is not names
                    or catalog._formula_map is not formulas or catalog._recipe_map is not recipes
                    or any(current is not original for current, original in zip(
                        (self.formulas, self.recipes, self.recipe_index), self._view_objects))
                    or any(view.catalog is not catalog for view in self._view_objects)
                    or any(domain.factors.catalog is not catalog or domain.factors.core is not core
                           for domain in self.domains)
                    or not catalog._sealed):
                raise ValueError('sealed catalog/view identity changed; no stale continuation')
            for domain in self.domains:
                domain.factors.assert_integrity()
            if canonical(self._mutable_state()) != self._tracked_state_text:
                raise ValueError('untracked public point/domain/trail mutation; continuation is UNKNOWN')
            self.assert_classification_integrity()

        def compact_graph_binding(self):
            self.assert_runtime_integrity()
            return json.loads(self._binding_text)

        @staticmethod
        def _dependencies(row, marks):
            return [[*point, value] for point, value in sorted(marks.items())
                    if (point[0] == 1 and 0 <= point[1] <= row)
                    or (point[0] in (2, 3) and point[1] == row)]

        def semantic_state(self):
            self.assert_runtime_integrity()
            state = super().compact_semantic_state()
            domains = []
            for row, domain in enumerate(self.domains):
                factors = domain.factors
                if (factors.catalog is not self.catalog or factors.row != row
                        or factors.total != self.totals[row]
                        or self._dependencies(row, factors._marks) != self._dependencies(row, self.marks)
                        or domain.count != domain.base_count - len(domain.excluded_legal)):
                    raise AssertionError('cached complete row domain differs from current dependency state')
                domains.append({'row': row, 'base_count': domain.base_count,
                    'excluded_legal': [key.data() for key in domain.excluded_legal], 'count': domain.count,
                    'factor_relation': {'schema': DEPENDENCY_SCHEMA,
                        'catalog_identity_sha256': self.catalog_identity_sha,
                        'positive_total': self.totals[row],
                        'all_relevant_assigned_marks': self._dependencies(row, self.marks),
                        'recipe_order': 'all_original_recipe_indices',
                        'reference_order': 'all_ordered_strict_prior_row_pairs',
                        'unequal_input_codes_disallow_same_reference': True}})
            state.update({'schema': STATE_SCHEMA, 'catalog_identity_sha256': self.catalog_identity_sha,
                'runtime_authority_sha256': self.runtime_authority_sha, 'domains': domains})
            return state

        def compact_semantic_state(self):
            return self.semantic_state()

        def checkpoint(self):
            self.assert_runtime_integrity()
            return super().checkpoint()

        def point_data(self, key):
            self.assert_runtime_integrity()
            return super().point_data(key)

        def domain_stream_receipt(self, row, *, factor_visitor=None):
            self.assert_runtime_integrity(); exact_int(row)
            if not 0 <= row < self.height:
                raise ValueError('required row outside full boundary')
            revision = self._dynamic_revision; domain = self.domains[row]
            receipt = super().domain_stream_receipt(row, factor_visitor=factor_visitor)
            self.assert_runtime_integrity()
            if revision != self._dynamic_revision or self.domains[row] is not domain:
                raise ValueError('actual-factor visitor changed dynamic domain/revision; UNKNOWN')
            return receipt

        def decision(self):
            self.assert_runtime_integrity()
            return super().decision()

        def legal(self, key):
            self.assert_runtime_integrity()
            return super().legal(key)

        def _membership_binding_value(self, decision):
            # This is a value captured inside a full guard, never a cached
            # successful guard verdict. Object identities prevent cross-graph
            # token use. The tracked text covers every point/domain/trail field.
            return (BATCH_BINDING_SCHEMA, self, self.catalog_identity_sha,
                    self.runtime_authority_sha, self.model_epoch,
                    self._dynamic_revision,
                    (decision.kind, decision.row, decision.count, decision.generation),
                    self._tracked_state_text, self.domains[decision.row])

        def _check_membership_binding(self, decision, expected_binding):
            # Only exact tuple/scalar/object comparisons; no caller hooks or
            # lazy iterable is evaluated anywhere in the synchronous batch.
            if (type(expected_binding) is not tuple or len(expected_binding) != 9
                    or type(expected_binding[0]) is not str
                    or expected_binding[0] != BATCH_BINDING_SCHEMA
                    or expected_binding[1] is not self
                    or type(expected_binding[2]) is not str
                    or type(expected_binding[3]) is not str
                    or type(expected_binding[4]) is not str
                    or type(expected_binding[5]) is not int
                    or type(expected_binding[6]) is not tuple
                    or len(expected_binding[6]) != 4
                    or type(expected_binding[6][0]) is not str
                    or any(type(value) is not int for value in expected_binding[6][1:])
                    or type(expected_binding[7]) is not str):
                raise ValueError('exact graph/authority/revision/decision/state binding required')
            if (type(decision) is not core.Decision
                    or type(decision.kind) is not str
                    or any(type(value) is not int for value in (decision.row, decision.count, decision.generation))
                    or decision.kind not in ('branch', 'forced')
                    or decision != base_type.decision(self)):
                raise ValueError('current mandatory selected-domain decision required')
            current = self._membership_binding_value(decision)
            if (expected_binding[2:7] != current[2:7]
                    or expected_binding[7] is not current[7]
                    or expected_binding[8] is not current[8]):
                raise ValueError('stale membership authority/state/decision/domain; UNKNOWN')

        def membership_binding(self, decision):
            """Ephemeral immutable value for the current branch/forced domain.

            It carries full tracked point/domain/trail state identity as well
            as the explicit catalog/runtime/model/revision/decision binding.
            It authorizes no cached integrity verdict or unchecked continuation.
            """
            self.assert_runtime_integrity()
            if (type(decision) is not core.Decision
                    or type(decision.kind) is not str
                    or any(type(value) is not int for value in (decision.row, decision.count, decision.generation))
                    or decision.kind not in ('branch', 'forced')
                    or decision != base_type.decision(self)):
                raise ValueError('current mandatory selected-domain decision required')
            return self._membership_binding_value(decision)

        def legal_batch(self, decision, keys, *, expected_binding, deadline):
            """Exact membership through the unchanged bound base predicate.

            At most64 frozen Key objects in one exact tuple; duplicates retain
            order/multiplicity. Full guards run at entry and in finally, even
            for malformed/stale requests or predicate exceptions. The unchanged
            scalar legal method and OrderedDomain revalidation remain intact.
            There is no callback, iterator, yield, session or retained cache.
            Deadline expiry discards every Boolean; the exception receipt has
            diagnostic counts/times only, never a partial result or key list.
            """
            started = time.perf_counter()
            guard_seconds = 0.0; predicate_seconds = 0.0; guard_calls = 0
            completed_queries = 0; legal_count = 0; body_complete = False
            final_guard_passed = False; request_valid = False
            values = []; binding_record = None
            receipt = {'schema': BATCH_RECEIPT_SCHEMA, 'completed': False,
                'batch_key_count': len(keys) if type(keys) is tuple else None,
                'exact_predicate_queries': 0, 'legal_count': None,
                'full_guard_calls': 0, 'full_guard_seconds': 0.0,
                'exact_predicate_seconds': 0.0, 'total_seconds': 0.0,
                'binding': None, 'partial_results_returned': False}
            try:
                guard_started = time.perf_counter(); guard_calls += 1
                try:
                    self.assert_runtime_integrity()
                finally:
                    guard_seconds += time.perf_counter() - guard_started
                if (type(deadline) not in (int, float)
                        or not math.isfinite(deadline)):
                    raise ValueError('finite literal same-search-clock deadline required')
                if type(keys) is not tuple or len(keys) > MAXIMUM_BATCH_KEYS:
                    raise ValueError('exact tuple of at most64 keys required; never trim')
                self._check_membership_binding(decision, expected_binding)
                for key in keys:
                    if (type(key) is not core.Key or type(key.recipe) is not int
                            or type(key.row) is not int or key.row != decision.row
                            or type(key.refs) is not tuple
                            or any(type(ref) is not int for ref in key.refs)):
                        raise ValueError('exact chosen-row Key fields required; bool/list/subclass rejected')
                request_valid = True
                binding_record = {'catalog_identity_sha256': self.catalog_identity_sha,
                    'runtime_authority_sha256': self.runtime_authority_sha,
                    'model_epoch': self.model_epoch, 'revision': self._dynamic_revision,
                    'decision': list(expected_binding[6]),
                    'full_tracked_state_and_domain_identity_bound': True}
                if time.perf_counter() >= deadline:
                    raise MembershipBudgetExceeded('exact-membership same-search-clock budget', receipt=receipt)
                for key in keys:
                    if time.perf_counter() >= deadline:
                        raise MembershipBudgetExceeded('exact-membership same-search-clock budget', receipt=receipt)
                    predicate_started = time.perf_counter()
                    try:
                        # Explicit unchanged core/compact legality chain. This
                        # bypasses only the outer dynamic public-entry wrapper;
                        # recipe/ref validation, exclusions and all local exact
                        # FactorStream pre/post integrity checks stay unchanged.
                        value = base_type.legal(self, key)
                        if type(value) is not bool:
                            raise AssertionError('unchanged exact predicate must return bool')
                    finally:
                        predicate_seconds += time.perf_counter() - predicate_started
                    completed_queries += 1; legal_count += int(value)
                    values.append(value)
                body_complete = True
            finally:
                # No Boolean tuple can escape before this endpoint. Full guards
                # reject ordinary untracked mutations even without a revision
                # change; binding checks also reject every official rollback.
                guard_started = time.perf_counter(); guard_calls += 1
                try:
                    self.assert_runtime_integrity()
                    final_guard_passed = True
                finally:
                    guard_seconds += time.perf_counter() - guard_started
                    receipt.update(exact_predicate_queries=completed_queries,
                        full_guard_calls=guard_calls, full_guard_seconds=guard_seconds,
                        exact_predicate_seconds=predicate_seconds,
                        total_seconds=time.perf_counter()-started, binding=binding_record)
                try:
                    if request_valid:
                        self._check_membership_binding(decision, expected_binding)
                    if body_complete and final_guard_passed:
                        # Endpoint validation/timing is charged too. A late
                        # endpoint cannot salvage a result past the deadline.
                        if time.perf_counter() >= deadline:
                            raise MembershipBudgetExceeded('exact-membership same-search-clock budget', receipt=receipt)
                finally:
                    receipt['total_seconds'] = time.perf_counter() - started
            receipt.update(completed=True, legal_count=legal_count,
                           total_seconds=time.perf_counter()-started)
            return tuple(values), receipt

        def candidates(self, row):
            self.assert_runtime_integrity(); revision = self._dynamic_revision
            iterator = super().candidates(row)
            while True:
                self.assert_runtime_integrity()
                if revision != self._dynamic_revision:
                    raise ValueError('candidate stream is stale after graph mutation')
                try:
                    key = next(iterator)
                except StopIteration:
                    break
                yield key

        def _apply_legal(self, key, generation=None):
            self.assert_runtime_integrity()
            super()._apply_legal(key, generation=generation)
            self._dynamic_revision += 1
            if self._dynamic_ready:
                self._tracked_state_text = canonical(self._mutable_state())

        def exclude_failed_child(self, key):
            self.assert_runtime_integrity()
            super().exclude_failed_child(key); self._dynamic_revision += 1
            self._tracked_state_text = canonical(self._mutable_state())

        def rollback(self, checkpoint):
            self.assert_runtime_integrity()
            super().rollback(checkpoint); self._dynamic_revision += 1
            self._tracked_state_text = canonical(self._mutable_state())

        def validate_cluster(self, keys, model_epoch):
            self.assert_runtime_integrity()
            return super().validate_cluster(keys, model_epoch)

        def decorate(self, key):
            self.assert_runtime_integrity()
            return super().decorate(key)

        def point_certificate(self):
            self.assert_runtime_integrity()
            return super().point_certificate()

        def ordered_domain(self, decision, preferred=()):
            return OrderedDomain(self, decision, preferred)

        def feature_views(self):
            self.assert_runtime_integrity()
            return RecipeMetadataView(self.catalog), FormulaHeadView(self.catalog)

    return DynamicCompactGraph
