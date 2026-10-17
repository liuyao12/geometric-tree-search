"""SOURCE ONLY: exact complete implicit domains over a fixed compact catalog.

The source author has not imported or called this adapter. ROOT must separately
qualify the decoder, complete catalog, this initial model, resource envelope and
future dynamic search before use. No legacy Controller/DFS compatibility claim
is made. Recipe identity multiplicity and canonical order are never quotiented.
"""
import copy
import hashlib
import json
import struct
from types import FunctionType, GetSetDescriptorType, MappingProxyType
from collections.abc import Mapping, Sequence

CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'
STATE_SCHEMA = 'complete-compact-point-state-v1'
FACTOR_SCHEMA = 'complete-ordered-factor-stream-u64-u64-u64-u8-u64le-v1'
FACTOR_RECORD = struct.Struct('<QQQBQ')
HEIGHT = 24


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def exact_int(value):
    if type(value) is not int:
        raise ValueError('exact integer required')
    return value


class FormulaView(Sequence):
    """Indexed AST decoding; no complete expanded registry is retained."""
    def __init__(self, catalog):
        self.catalog = catalog

    def __len__(self):
        return self.catalog.formula_count

    def __getitem__(self, code):
        if isinstance(code, slice):
            raise ValueError('full/sliced expanded registry is not a compact interface')
        exact_int(code)
        if not 0 <= code < len(self):
            raise IndexError(code)
        return self.catalog.formula(code)


class RecipeView:
    __slots__ = ('catalog', 'index', 'identifier', 'output', 'inputs')

    def __init__(self, catalog, index):
        meta = catalog.recipe_meta(index)
        self.catalog = catalog; self.index = index
        self.identifier = meta['identifier']; self.output = meta['output']
        self.inputs = tuple(meta['inputs'])

    @property
    def witness(self):
        return self.catalog.witness(self.index)

    @property
    def formulas(self):
        return self.catalog.premises(self.index)

    @property
    def witness_text(self):
        return canonical(self.witness)

    @property
    def premise_texts(self):
        return tuple(canonical(formula) for formula in self.formulas)


class RecipeSequence(Sequence):
    def __init__(self, catalog):
        self.catalog = catalog

    def __len__(self):
        return self.catalog.recipe_count

    def __getitem__(self, index):
        if isinstance(index, slice):
            raise ValueError('full/sliced expanded recipe palette is not a compact interface')
        exact_int(index)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return RecipeView(self.catalog, index)


class RecipeIndex(Mapping):
    """Exact scan lookup preserves every license without an extra identity map."""
    def __init__(self, catalog):
        self.catalog = catalog

    def __len__(self):
        return self.catalog.recipe_count

    def __iter__(self):
        for index in range(len(self)):
            yield self.catalog.recipe_meta(index)['identifier']

    def __getitem__(self, identifier):
        if type(identifier) is not str:
            raise KeyError(identifier)
        found = None
        for index in range(len(self)):
            if self.catalog.recipe_meta(index)['identifier'] == identifier:
                if found is not None:
                    raise ValueError('duplicate full recipe identity')
                found = index
        if found is None:
            raise KeyError(identifier)
        return found


class FactorStream:
    """Sealed complete recipe-index stream and own small ordered row-mask table.

    The table is derived only from this detached mark snapshot, never from an
    oracle. Assigned zero is an ordinary code; a per-stream private sentinel
    represents every code absent from assigned formula rows. Raw unequal input
    codes remain distinct for alias rejection even if their categories coincide.
    Production uses the source-bound sealed catalog. A bare immutable provider
    is retained solely for separate nonlogical FactorStream algebra controls.
    """
    __slots__ = ('core', 'catalog', 'row', 'total', '_mark_items', '_marks',
                 '_assigned_codes', '_absent_code', '_row_masks', '_pair_counts',
                 '_catalog_profile', '_catalog_objects', '_catalog_methods',
                 '_core_objects', '_integrity_token', '_sealed')

    def __setattr__(self, name, value):
        if getattr(self, '_sealed', False):
            raise ValueError('immutable factor snapshot/table requires a fresh stream; UNKNOWN')
        object.__setattr__(self, name, value)

    def __init__(self, core, catalog, row, total, marks):
        self._sealed = False
        if (not 0 <= exact_int(row) < HEIGHT or exact_int(total) not in (0, 1)
                or any(type(point) is not tuple or len(point) != 2
                       or any(type(axis) is not int for axis in point)
                       or type(value) is not int for point, value in marks.items())):
            raise ValueError('exact24-row integer mark snapshot required')
        self.core = core; self.catalog = catalog; self.row = row; self.total = total
        self._mark_items = tuple(sorted(marks.items()))
        self._marks = MappingProxyType(dict(self._mark_items))
        self._core_objects = (core.Factor, core.popcount, core.MARKING_VERSION)
        if hasattr(catalog, 'header'):
            if (getattr(catalog, '_sealed', False) is not True
                    or type(catalog.nodes) is not tuple or type(catalog.names) is not tuple
                    or type(catalog._formula_map) is not bytes
                    or type(catalog._recipe_map) is not bytes
                    or type(catalog._header_text) is not str
                    or type(catalog.header_pin_text) is not str):
                raise ValueError('production factor masks require the sealed immutable catalog')
            self._catalog_profile = 'sealed-production'
            self._catalog_objects = (catalog._header_text, catalog.header_pin_text,
                catalog.nodes, catalog.names, catalog._formula_map, catalog._recipe_map,
                catalog.formula_count, catalog.recipe_count)
            self._catalog_methods = tuple((cls, tuple(vars(cls).items()))
                for cls in type(catalog).__mro__ if cls is not object)
        else:
            # No header, AST, license, identity or production authority is implied
            # by this deliberately narrow standalone nonlogical provider profile.
            cls = type(catalog); items = vars(cls); method = items.get('recipe_meta')
            if (cls.__bases__ != (object,)
                    or type(items.get('__dict__')) is not GetSetDescriptorType
                    or type(items.get('__weakref__')) is not GetSetDescriptorType
                    or vars(catalog)
                    or set(items) - {'__module__', '__qualname__', '__doc__', '__dict__',
                                     '__weakref__', 'recipe_count', 'recipe_meta'}
                    or exact_int(items.get('recipe_count')) < 0
                    or type(method) is not FunctionType or method.__closure__ is not None
                    or method.__defaults__ is not None or method.__kwdefaults__ is not None
                    or type(items.get('__module__')) is not str
                    or items.get('__doc__') is not None and type(items['__doc__']) is not str):
                raise ValueError('bare nonlogical provider requires only a static count/method and no mutable data')
            self._catalog_profile = 'standalone-nonlogical'
            self._catalog_objects = (cls, tuple(items.items()))
            self._catalog_methods = ((cls, self._catalog_objects[1]),)
        assigned = frozenset(value for (x, y), value in self._mark_items
                             if x == 1 and 0 <= y < HEIGHT)
        if (self._catalog_profile == 'sealed-production'
                and any(not 0 <= code < catalog.formula_count for code in assigned)):
            raise ValueError('assigned formula code outside complete catalog')
        self._assigned_codes = assigned; self._absent_code = object()
        free = 0; matching = {}
        for ref in range(row):
            point = (1, ref)
            if point not in self._marks:
                free |= 1 << ref
            else:
                code = self._marks[point]
                matching[code] = matching.get(code, 0) | (1 << ref)
        port_masks = []
        for port in (0, 1):
            point = (2 + port, row); allowed = (1 << row) - 1
            if point in self._marks:
                ref = row + self._marks[point]
                allowed = (1 << ref) if 0 <= ref < row else 0
            port_masks.append(allowed)
        table = {}
        for code in (*sorted(assigned), self._absent_code):
            compatible = free | matching.get(code, 0)
            for port in (0, 1):
                table[(code, port)] = compatible & port_masks[port]
        # Neither backing dictionary escapes; only immutable proxies and scalar
        # tuples are retained. At most 2*(24+1) mask entries in this row profile.
        self._row_masks = MappingProxyType(table)
        categories = (*sorted(assigned), self._absent_code)
        cardinalities = {key: core.popcount(mask) for key, mask in table.items()}
        counts = {}
        for left in categories:
            for right in categories:
                product = cardinalities[(left, 0)] * cardinalities[(right, 1)]
                intersection = core.popcount(table[(left, 0)] & table[(right, 1)])
                counts[(left, right, False)] = product
                counts[(left, right, True)] = product - intersection
        # Actual inequality is a separate key even when both codes map to the
        # sentinel. No per-raw-code or per-recipe cache: at most 2*(24+1)^2
        # scalar entries, owned by this exact stream snapshot and fully charged.
        self._pair_counts = MappingProxyType(counts)
        self._integrity_token = (core, catalog, row, total, self._mark_items,
            self._marks, self._assigned_codes, self._absent_code, self._row_masks,
            self._pair_counts, self._catalog_profile, self._catalog_objects,
            self._catalog_methods, self._core_objects)
        self._sealed = True
        self.assert_integrity()

    def assert_integrity(self):
        # Ordinary field/table/catalog replacement is rejected; adversarial
        # rewriting of private seals, source functions or object.__setattr__ is
        # outside the same trusted synchronous writer scope as the old guards.
        token = self._integrity_token
        current = (self.core, self.catalog, self.row, self.total, self._mark_items,
            self._marks, self._assigned_codes, self._absent_code, self._row_masks,
            self._pair_counts, self._catalog_profile, self._catalog_objects,
            self._catalog_methods, self._core_objects)
        if (not self._sealed or type(token) is not tuple or len(token) != len(current)
                or any(value is not original for value, original in zip(current, token))
                or type(self._marks) is not MappingProxyType
                or type(self._row_masks) is not MappingProxyType
                or type(self._pair_counts) is not MappingProxyType
                or type(self._assigned_codes) is not frozenset
                or self.core.Factor is not self._core_objects[0]
                or self.core.popcount is not self._core_objects[1]
                or self.core.MARKING_VERSION != self._core_objects[2]
                or any(tuple(vars(cls)) != tuple(name for name, _ in items)
                       or any(vars(cls)[name] is not value for name, value in items)
                       for cls, items in self._catalog_methods)):
            raise ValueError('untracked factor authority/snapshot/mask mutation; UNKNOWN')
        if self._catalog_profile == 'sealed-production':
            catalog = self.catalog
            objects = (catalog._header_text, catalog.header_pin_text,
                catalog.nodes, catalog.names, catalog._formula_map, catalog._recipe_map,
                catalog.formula_count, catalog.recipe_count)
            if (catalog._sealed is not True
                    or any(value is not original for value, original in zip(objects, self._catalog_objects))):
                raise ValueError('sealed factor catalog authority changed; UNKNOWN')
        elif (vars(self.catalog) or type(self.catalog) is not self._catalog_objects[0]
                or tuple(vars(type(self.catalog)).items()) != self._catalog_objects[1]):
            raise ValueError('standalone nonlogical provider changed; UNKNOWN')

    def _category(self, code_class):
        if code_class is not None:
            exact_int(code_class)
        return code_class if code_class in self._assigned_codes else self._absent_code

    def _mask(self, code_class, port):
        if exact_int(port) not in (0, 1):
            raise ValueError('exact ordered input port required')
        return self._row_masks[(self._category(code_class), port)]

    def mask(self, code_class, port):
        self.assert_integrity()
        return self._mask(code_class, port)

    def _factor(self, index):
        if self.total == 1:
            return None
        meta = self.catalog.recipe_meta(index)
        point = (1, self.row)
        if point in self._marks and self._marks[point] != meta['output']:
            return None
        inputs = meta['inputs']
        if not inputs:
            return self.core.Factor(index, 0, 0, False, 1)
        # Preserve actual raw-code inequality BEFORE category/sentinel lookup.
        different = inputs[0] != inputs[1]
        left = self._mask(inputs[0], 0); right = self._mask(inputs[1], 1)
        count = self._pair_counts[(self._category(inputs[0]),
                                   self._category(inputs[1]), different)]
        return self.core.Factor(index, left, right, different, count) if count else None

    def factor(self, index):
        self.assert_integrity()
        if not 0 <= exact_int(index) < self.catalog.recipe_count:
            raise ValueError('exact recipe index outside complete catalog')
        result = self._factor(index)
        self.assert_integrity()
        return result

    def __iter__(self):
        self.assert_integrity()
        if self.total != 1:
            for index in range(self.catalog.recipe_count):
                factor = self._factor(index)
                if factor is not None:
                    yield factor
        self.assert_integrity()  # only complete natural EOF closes the stream

    def snapshot(self):
        self.assert_integrity()
        return {'row': self.row, 'total': self.total,
                'marks': [[*point, value] for point, value in self._mark_items]}


def streamed_model_epoch(core, *, height, context, registry, authority,
                         catalog, fixed_marks, roots, seed_keys, source_bindings):
    """Byte-exact legacy model-epoch canonical JSON, without a recipe-ID array."""
    payload = {'height': height, 'context': context, 'registry': registry,
               'authority': authority, 'recipes': None, 'fixed_marks': fixed_marks,
               'roots': roots, 'seed_keys': [key.data() for key in seed_keys],
               'marking_version': core.MARKING_VERSION, 'fixture': False,
               'source_bindings': source_bindings}
    hasher = hashlib.sha256(); hasher.update(b'{')
    for field_index, key in enumerate(sorted(payload)):
        if field_index:
            hasher.update(b',')
        hasher.update(canonical(key).encode('utf8')); hasher.update(b':')
        if key == 'recipes':
            hasher.update(b'[')
            for index in range(catalog.recipe_count):
                if index:
                    hasher.update(b',')
                hasher.update(canonical(catalog.recipe_meta(index)['identifier']).encode('utf8'))
            hasher.update(b']')
        else:
            hasher.update(canonical(payload[key]).encode('utf8'))
    hasher.update(b'}')
    return hasher.hexdigest()


def make_graph_type(core):
    """Bind a separately exact-pinned unchanged core, without importing it here."""
    if (core.MARKING_VERSION != 'injective-formula-ordered-mp-offset-v1'
            or FACTOR_RECORD.size != 33):
        raise ValueError('unchanged marking and exact compact factor codec required')

    class CompactPointGraph(core.PointGraph):
        def __init__(self, *, catalog):
            header = catalog.header
            if (header['schema'] != 'fresh-ground-compact-catalog-v1'
                    or header['height'] != HEIGHT or header['orientation'] != 'identity'
                    or header['marking_version'] != core.MARKING_VERSION
                    or header['bodies'] != [] or header['complete_cluster_inventory'] != []):
                raise ValueError('complete production24-row catalog and empty bootstrap inventory required')
            dimensions = header['dimensions']
            if (dimensions['logical_rows'] != HEIGHT
                    or dimensions['formula_count'] != catalog.formula_count
                    or dimensions['primitive_license_count'] != catalog.recipe_count
                    or dimensions['non_assumption_witness_count'] != catalog.recipe_count - 3
                    or dimensions['source_body_count'] != 0):
                raise ValueError('complete declared census mismatch')
            self.catalog = catalog; self.height = HEIGHT; self.fixture = False
            self.formulas = FormulaView(catalog); self.recipes = RecipeSequence(catalog)
            self.recipe_index = RecipeIndex(catalog)
            self.registry_sha = header['formula_registry_sha256']
            self.context = copy.deepcopy(header['context']); self.context_id = digest(self.context)
            if self.context_id != header['context_id']:
                raise ValueError('exact context identity mismatch')
            self.authority = copy.deepcopy(header['authority'])
            if self.authority.get('activated') is not False or self.authority.get('native_accepted') is not False:
                raise ValueError('native authority must remain inactive')
            self.authority_epoch = self.authority['epoch']
            if digest({k: v for k, v in self.authority.items() if k != 'epoch'}) != self.authority_epoch:
                raise ValueError('stale authority epoch')
            self.source_bindings = copy.deepcopy(header['source_bindings'])
            boundary = header['boundary']
            if (boundary['required'] != [[0, r] for r in range(HEIGHT)]
                    or boundary['root_generations'] != [[0, r, 0] for r in range(HEIGHT)]
                    or boundary['fixed_exterior_m'] != [[1, r, -1] for r in range(-23, 0)]
                    or boundary['fixed_target_m'] != [[1, 23, header['target_code']]]
                    or boundary['all_root_obligations_generation_zero'] is not True):
                raise ValueError('exact full boundary and translation-only production domain required')
            self.roots = tuple(0 for _ in range(HEIGHT))
            self.initial_marks = {}
            for x, y, value in boundary['fixed_exterior_m'] + boundary['fixed_target_m']:
                point = (exact_int(x), exact_int(y)); exact_int(value)
                if point in self.initial_marks and self.initial_marks[point] != value:
                    raise ValueError('inconsistent fixed marking')
                self.initial_marks[point] = value
            indices = header['assumption_recipe_indices']
            if len(indices) != 3 or len(self.context['ordered_local_premises']) != 3:
                raise ValueError('three separately licensed ordered hypothesis occurrences required')
            seed_keys = tuple(core.Key(exact_int(index), occurrence) for occurrence, index in enumerate(indices))
            expected_seeds = [{'recipe_id': self.recipes[key.recipe].identifier,
                               'row': key.row, 'generation': 0} for key in seed_keys]
            if boundary['fixed_initial_local_seeds'] != expected_seeds:
                raise ValueError('exact seed identity/order mismatch')
            # This is a compact, single full-header pass. The decoder separately
            # validates the exact DAG/payload/index/digest grammar; independent
            # static licensing must still rederive every witness and registry.
            assumption_occurrences = []
            for index in range(catalog.recipe_count):
                meta = catalog.recipe_meta(index)
                if (set(meta) != {'identifier', 'rule', 'output', 'inputs'}
                        or meta['rule'] not in ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
                        or type(meta['identifier']) is not str
                        or not 0 <= exact_int(meta['output']) < catalog.formula_count
                        or len(meta['inputs']) not in (0, 2)
                        or (meta['rule'] == 'mp') != bool(meta['inputs'])
                        or any(not 0 <= exact_int(code) < catalog.formula_count for code in meta['inputs'])):
                    raise ValueError('complete indexed zero/binary production recipe grammar required')
                if meta['inputs']:
                    out_node = catalog.node_for_formula_code(meta['output'])
                    antecedent_node = catalog.node_for_formula_code(meta['inputs'][0])
                    implication_node = catalog.node_for_formula_code(meta['inputs'][1])
                    if catalog.node_record(implication_node) != ('imp', antecedent_node, out_node):
                        raise ValueError('point-consistent but logically invalid MP interface')
                if meta['rule'] == 'assumption':
                    witness = catalog.witness(index); occurrence = exact_int(witness['index'])
                    if (not 0 <= occurrence < 3 or index != indices[occurrence]
                            or witness['formula'] != self.context['ordered_local_premises'][occurrence]
                            or meta['output'] != header['hypothesis_codes'][occurrence]):
                        raise ValueError('assumption is not exact occurrence-specific recipient premise')
                    assumption_occurrences.append(occurrence)
            if sorted(assumption_occurrences) != [0, 1, 2]:
                raise ValueError('all and only three distinct assumption occurrences required')
            self.model_epoch = streamed_model_epoch(core, height=HEIGHT, context=self.context,
                registry=self.registry_sha, authority=self.authority_epoch, catalog=catalog,
                fixed_marks=[[*point, value] for point, value in sorted(self.initial_marks.items())],
                roots=self.roots, seed_keys=seed_keys, source_bindings=self.source_bindings)
            self.totals = [0] * HEIGHT; self.marks = dict(self.initial_marks)
            self.mark_refs = {point: 1 for point in self.initial_marks}
            self.selected = {}; self.order = []; self.excluded = [set() for _ in range(HEIGHT)]
            self.trail = []; self._classes_signature = None; self._classes = None
            self._classification_parent_frames = ()
            self._classification_pending_restore = None
            self._seal_classification_cache_state()
            self.compact_metrics = {'complete_header_classification_passes': 0,
                                    'complete_headers_classified': 0,
                                    'streamed_factor_records': 0,
                                    'streamed_factor_bytes': 0}
            self.domains = [self._domain(row) for row in range(HEIGHT)]
            self.metrics = {'domain_refreshes': HEIGHT, 'placements': 0, 'forced': 0,
                'branches': 0, 'backtracks': 0, 'attempts': 0, 'lazy_id_constructions': 0,
                'proposal_validations': 0, 'proposal_rejections': 0}
            for key in seed_keys:
                if self.recipes[key.recipe].witness['rule'] != 'assumption':
                    raise ValueError('only fixed declared assumption seeds allowed')
                self._apply_legal(key, generation=0)
            self.trail.clear(); self.initial_selected = tuple(self.order)
            self._classification_parent_frames = ()
            self._seal_classification_cache_state()
            self.assert_classification_integrity()

        def _classification_authority(self):
            # The dynamic factory separately authenticates this exact source and
            # the sealed catalog. This small value binds every retained count
            # relation to that model; a filename alone is not byte authority.
            return canonical({'schema': 'complete-classification-authority-v1',
                'source_origin': make_graph_type.__code__.co_filename,
                'core_sha256': CORE_SHA, 'catalog_header': self.catalog.header,
                'height': self.height, 'model_epoch': self.model_epoch,
                'registry_sha256': self.registry_sha,
                'authority_epoch': self.authority_epoch, 'context_id': self.context_id,
                'context': self.context, 'source_bindings': self.source_bindings})

        def _seal_classification_cache_state(self):
            # Private official-writer token, just as the predecessor's private
            # tracked-state text. Never a successful-integrity-check cache.
            self._classification_integrity_token = (
                self._classification_authority(), self.catalog,
                self._classes_signature, self._classes,
                self._classification_parent_frames,
                self._classification_pending_restore)

        def _check_classification_cache_state(self, *, aligned):
            token = self._classification_integrity_token
            if (type(token) is not tuple or len(token) != 6
                    or token[0] != self._classification_authority()
                    or token[1] is not self.catalog
                    or token[2] is not self._classes_signature
                    or token[3] is not self._classes
                    or token[4] is not self._classification_parent_frames
                    or token[5] is not self._classification_pending_restore):
                raise ValueError('untracked complete classification/cache/frame mutation; UNKNOWN')
            if (type(self._classification_parent_frames) is not tuple
                    or (self._classes is None) != (self._classes_signature is None)
                    or (self._classes is not None and (
                        type(self._classes) is not MappingProxyType
                        or type(self._classes_signature) is not tuple))):
                raise ValueError('immutable complete classification state required; UNKNOWN')
            if aligned:
                if (self._classification_pending_restore is not None
                        or len(self._classification_parent_frames) != len(self.trail)):
                    raise ValueError('classification frames not at a closed primitive boundary; UNKNOWN')
                for frame, entry in zip(self._classification_parent_frames, self.trail):
                    if (type(frame) is not tuple or len(frame) != 3
                            or frame[0] != entry[0] or frame[1] != entry[1]
                            or frame[0] not in ('place', 'exclude')):
                        raise ValueError('classification frame/primitive trail mismatch; UNKNOWN')

        def assert_classification_integrity(self):
            # Appended to, never substituted for, the full original dynamic
            # metadata/catalog/point/domain/trail guard on every public entry.
            self._check_classification_cache_state(aligned=True)

        def _assigned_classification_signature(self):
            return tuple(sorted(frozenset(value for (x, y), value in self.marks.items()
                if x == 1 and 0 <= y < self.height)))

        def _validate_classification_snapshot(self, snapshot):
            if (type(snapshot) is not tuple or len(snapshot) != 4
                    or snapshot[0] != 'immutable-complete-parent-classification-v1'
                    or snapshot[1] != self._classification_authority()
                    or type(snapshot[2]) is not tuple
                    or snapshot[2] != tuple(sorted(set(snapshot[2])))
                    or any(type(code) is not int or not 0 <= code < self.catalog.formula_count
                           for code in snapshot[2])
                    or type(snapshot[3]) is not MappingProxyType):
                raise ValueError('exact immutable parent classification authority required; UNKNOWN')
            signature = frozenset(snapshot[2]); total = 0
            for key, count in snapshot[3].items():
                if (type(key) is not tuple or len(key) != 5
                        or type(key[0]) is not int or key[0] not in (0, 2)
                        or type(key[4]) is not bool
                        or any(value is not None and (type(value) is not int or value not in signature)
                               for value in key[1:4])
                        or (key[0] == 0 and (key[2:4] != (None, None) or key[4]))
                        or type(count) is not int or count <= 0):
                    raise ValueError('full exact class multiplicities/ordered roles required; UNKNOWN')
                total += count
            if total != self.catalog.recipe_count:
                raise ValueError('parent classification does not cover every recipe license; UNKNOWN')
            # This checks shape, scope and total only. Exact per-class contents
            # come from the unchanged whole scan and immutable-origin guard;
            # independent future literal comparison remains mandatory.

        def _capture_parent_classification(self):
            self.assert_classification_integrity()
            classes = self._classification()
            snapshot = ('immutable-complete-parent-classification-v1',
                self._classification_authority(), self._classes_signature, classes)
            self._validate_classification_snapshot(snapshot)
            return snapshot

        def _record_classification_parent(self, depth, kind, key, snapshot):
            if (len(self.trail) != depth + 1 or self.trail[-1][0] != kind
                    or self.trail[-1][1] != key
                    or len(self._classification_parent_frames) != depth):
                raise ValueError('exact one primitive transaction for parent frame required; UNKNOWN')
            self._classification_parent_frames += ((kind, key, snapshot),)
            self._seal_classification_cache_state()
            self.assert_classification_integrity()

        def _apply_legal(self, key, generation=None):
            depth = len(self.trail); snapshot = self._capture_parent_classification()
            super()._apply_legal(key, generation=generation)
            self._record_classification_parent(depth, 'place', key, snapshot)

        def exclude_failed_child(self, key):
            depth = len(self.trail); snapshot = self._capture_parent_classification()
            super().exclude_failed_child(key)
            self._record_classification_parent(depth, 'exclude', key, snapshot)

        def _refresh(self, rows):
            # Core.rollback has now restored marks/totals/refcounts/exclusions,
            # but has not rebuilt the original affected-row domains yet.
            self._check_classification_cache_state(aligned=False)
            snapshot = self._classification_pending_restore
            if snapshot is not None:
                self._validate_classification_snapshot(snapshot)
                if snapshot[2] != self._assigned_classification_signature():
                    raise ValueError('restored parent assigned-code signature differs; UNKNOWN')
                self._classes_signature = snapshot[2]; self._classes = snapshot[3]
                self._classification_pending_restore = None
                self._seal_classification_cache_state()
            super()._refresh(rows)  # unchanged exact affected-row set, never all rows

        def rollback(self, checkpoint):
            self.assert_classification_integrity(); exact_int(checkpoint)
            if not 0 <= checkpoint <= len(self.trail):
                raise ValueError('invalid exact classification/primitive checkpoint')
            snapshot = (self._classification_parent_frames[checkpoint][2]
                        if checkpoint < len(self.trail) else self._capture_parent_classification())
            self._validate_classification_snapshot(snapshot)
            self._classification_pending_restore = snapshot
            self._seal_classification_cache_state()
            try:
                super().rollback(checkpoint)  # original core undo and _refresh
            except BaseException:
                self._classification_pending_restore = None
                self._seal_classification_cache_state()
                raise  # partial transaction stays UNKNOWN, never salvage acceptance
            if self._classification_pending_restore is not None:
                raise AssertionError('core rollback did not close the restoration hook')
            self._classification_parent_frames = self._classification_parent_frames[:checkpoint]
            self._seal_classification_cache_state()
            self.assert_classification_integrity()

        def _classification(self):
            self._check_classification_cache_state(aligned=False)
            assigned = frozenset(value for (x, y), value in self.marks.items()
                                 if x == 1 and 0 <= y < self.height)
            signature = tuple(sorted(assigned))
            if self._classes_signature != signature:
                counts = {}
                for index in range(self.catalog.recipe_count):
                    meta = self.catalog.recipe_meta(index); inputs = meta['inputs']
                    out = meta['output'] if meta['output'] in assigned else None
                    if inputs:
                        left = inputs[0] if inputs[0] in assigned else None
                        right = inputs[1] if inputs[1] in assigned else None
                        key = (2, out, left, right, inputs[0] != inputs[1])
                    else:
                        key = (0, out, None, None, False)
                    counts[key] = counts.get(key, 0) + 1
                self._classes_signature = signature; self._classes = MappingProxyType(counts)
                self._seal_classification_cache_state()
                self.compact_metrics['complete_header_classification_passes'] += 1
                self.compact_metrics['complete_headers_classified'] += self.catalog.recipe_count
            return self._classes

        def _factors(self, row):
            return FactorStream(core, self.catalog, row, self.totals[row], self.marks)

        def _base_legal_from_factors(self, key, factors):
            recipe = self._recipe_key(key)
            if not isinstance(factors, FactorStream) or factors.row != key.row:
                raise ValueError('exact immutable complete factor snapshot required')
            factor = factors.factor(key.recipe)
            if factor is None:
                return False
            if not recipe.inputs:
                return True
            left, right = key.refs
            return bool((factor.left >> left) & 1 and (factor.right >> right) & 1
                        and (not factor.different or left != right))

        def _domain(self, row):
            factors = self._factors(row)
            base = 0
            if self.totals[row] != 1:
                point = (1, row)
                masks = {}
                for (ports, out, left, right, different), multiplicity in self._classification().items():
                    if point in self.marks and self.marks[point] != out:
                        continue
                    if not ports:
                        base += multiplicity
                        continue
                    lkey = (left, 0); rkey = (right, 1)
                    if lkey not in masks:
                        masks[lkey] = factors.mask(left, 0)
                    if rkey not in masks:
                        masks[rkey] = factors.mask(right, 1)
                    lmask, rmask = masks[lkey], masks[rkey]
                    count = core.popcount(lmask) * core.popcount(rmask)
                    if different:
                        count -= core.popcount(lmask & rmask)
                    base += multiplicity * count
            removed = tuple(sorted(key for key in self.excluded[row]
                                   if self._base_legal_from_factors(key, factors)))
            return core.Domain(factors, base, removed, base - len(removed))

        def semantic_state(self):
            raise ValueError('legacy eager semantic_state is not a compact wire; use compact_semantic_state')

        def compact_semantic_state(self):
            return {'totals': list(self.totals),
                'marks': [[*point, value, self.mark_refs[point]] for point, value in sorted(self.marks.items())],
                'order': [key.data() for key in self.order],
                'selected_generations': [[key.data(), self.selected[key]] for key in sorted(self.selected)],
                'roots': list(self.roots),
                'excluded': [[key.data() for key in sorted(keys)] for keys in self.excluded],
                'model_epoch': self.model_epoch}

        def _factor_receipt_boundary(self, row, domain):
            self.assert_classification_integrity()
            factors = domain.factors; factors.assert_integrity()
            relevant = lambda marks: tuple((point, value) for point, value in sorted(marks.items())
                if (point[0] == 1 and 0 <= point[1] <= row)
                or (point[0] in (2, 3) and point[1] == row))
            if (self.domains[row] is not domain or factors.core is not core
                    or factors.catalog is not self.catalog or factors.row != row
                    or factors.total != self.totals[row]
                    or relevant(factors._marks) != relevant(self.marks)
                    or type(domain.base_count) is not int or domain.base_count < 0
                    or type(domain.count) is not int or domain.count < 0
                    or domain.count != domain.base_count - len(domain.excluded_legal)
                    or tuple(sorted(set(domain.excluded_legal))) != domain.excluded_legal
                    or any(key.row != row or key not in self.excluded[row]
                           for key in domain.excluded_legal)):
                raise ValueError('current complete factor domain/dependencies required; UNKNOWN')
            trail = []
            for entry in self.trail:
                if entry[0] == 'exclude':
                    trail.append(['exclude', entry[1].data()])
                elif entry[0] == 'place':
                    trail.append(['place', entry[1].data(), entry[2], entry[3]])
                else:
                    raise ValueError('unknown exact primitive trail; UNKNOWN')
            # Capture the whole small point/trail state and all domain identities,
            # not merely the assigned-code signature. No factor tape is retained.
            state = canonical({'points': CompactPointGraph.compact_semantic_state(self),
                'trail': trail, 'authority': self._classification_authority(),
                'metrics': self.metrics, 'compact_metrics': self.compact_metrics})
            return (state, tuple(self.domains), self._classification_integrity_token,
                    getattr(self, '_dynamic_revision', None))

        def domain_stream_receipt(self, row, *, factor_visitor=None):
            exact_int(row)
            if not 0 <= row < self.height:
                raise ValueError('required row outside full boundary')
            if factor_visitor is not None and not callable(factor_visitor):
                raise ValueError('optional read-only actual-factor visitor must be callable')
            domain = self.domains[row]
            before = self._factor_receipt_boundary(row, domain)
            hasher = hashlib.sha256(); factors = 0; count = 0; previous = -1
            for factor in domain.factors:
                if (type(factor) is not core.Factor
                        or type(factor.recipe) is not int
                        or not previous < factor.recipe < self.catalog.recipe_count
                        or type(factor.left) is not int or not 0 <= factor.left < (1 << row)
                        or type(factor.right) is not int or not 0 <= factor.right < (1 << row)
                        or type(factor.count) is not int or factor.count <= 0
                        or type(factor.different) is not bool):
                    raise ValueError('complete ordered positive exact factors required')
                previous = factor.recipe
                # ACTUAL factor bytes/counts only; visitor returns are not data
                # authority and may neither substitute nor short-circuit EOF.
                raw = FACTOR_RECORD.pack(factor.recipe, factor.left, factor.right,
                                         int(factor.different), factor.count)
                hasher.update(raw); factors += 1; count += factor.count
                if factor_visitor is not None:
                    factor_visitor(factor)
            after = self._factor_receipt_boundary(row, domain)
            if (before[0] != after[0]
                    or len(before[1]) != len(after[1])
                    or any(current is not original for current, original in zip(after[1], before[1]))
                    or before[2] is not after[2] or before[3] != after[3]):
                raise ValueError('actual-factor visitor changed graph/revision/domain state; UNKNOWN')
            if count != domain.base_count:
                raise ValueError('aggregate exact count disagrees with complete literal factor stream')
            self.compact_metrics['streamed_factor_records'] += factors
            self.compact_metrics['streamed_factor_bytes'] += factors * FACTOR_RECORD.size
            return {'row': row, 'factor_count': factors,
                'bytes': factors * FACTOR_RECORD.size, 'sha256': hasher.hexdigest(),
                'base_count': count, 'excluded_legal': [key.data() for key in domain.excluded_legal],
                'count': domain.count}

    return CompactPointGraph
