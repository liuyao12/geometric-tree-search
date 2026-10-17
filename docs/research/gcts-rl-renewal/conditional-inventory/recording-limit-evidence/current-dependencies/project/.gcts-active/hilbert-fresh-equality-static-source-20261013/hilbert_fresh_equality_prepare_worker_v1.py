"""SOURCE ONLY: fresh RL donor/evaluation preparation; complete compact V3 work retained.

ROOT is the sole dispatcher. One future invocation writes the entire declared
catalog and exact initial24-row domain evidence in a fresh namespace. All work,
imports, mmap resident pages, hashing and serialization belong to the enclosing
60s/512MiB preparation phase; caller terminal gate remains separately90s. No
child, PS, checker, search, target certificate, RNG, learner or native invocation
exists in this worker. Source readiness is not semantic/resource acceptance.
"""
import gzip
import hashlib
import importlib.util
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRESS = ROOT / '.gcts-active/hilbert-fresh-equality-static-progress-20261013'
SOURCE = ROOT / '.gcts-active/hilbert-fresh-equality-static-source-20261013'
ENGINE_SOURCE = ROOT / '.gcts-active/cluster-transfer-compact-engine-source-20261012'
FROZEN_COMPILER_SOURCE = ROOT / '.gcts-active/cluster-transfer-compact-compiler-source-20261012'
COMPILER_SOURCE = ROOT / '.gcts-active/hilbert-fresh-equality-static-source-20261013'
PLAN_SCHEMA = 'ROOT-Hilbert-next-compact-preparation-plan-v1'
EVIDENCE_SCHEMA = 'Hilbert-next-compact-preparation-evidence-v1'
RECEIPT_SCHEMA = 'Hilbert-next-compact-preparation-worker-receipt-v1'
CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'
METADATA_LIMIT = 1048576
DIAGNOSTIC_SCHEMA = 'compact-preparation-producer-diagnostic-record-v1'
MAX_DIAGNOSTIC_RECORDS = 1024
MAX_DIAGNOSTIC_BYTES = 1048576
MAX_DIAGNOSTIC_RECORD_BYTES = 4096
FROZEN_SHAS = {
    'compiler': '57653bb27eaf3c4dd1e050c70ac360133f78e1f636cd1276a39a20fd64610a56',
    'master': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9',
    'point_core': CORE_SHA,
    'decoder': '46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293',
    'compact_engine': 'd638f7152ec7fa8293adbd8915b79de60f95d0756952bdc6bf0e40b15f549ca0'}
FIXTURE_SHA = 'b60869d015f5f60caa726864595a6293a4566ffdf04403c2499ade76987ef831'
SOURCE_PATHS = {
    'compiler': COMPILER_SOURCE / 'hilbert_fresh_equality_compiler_v1.py',
    'decoder': FROZEN_COMPILER_SOURCE / 'compact_catalog_decoder_v1.py',
    'compact_engine': ENGINE_SOURCE / 'compact_point_graph_v1.py',
    'worker': SOURCE / 'hilbert_fresh_equality_prepare_worker_v1.py',
    'point_core': ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py',
    'master': ROOT / 'docs/basic-tiling-algorithm.md'}

# Fresh donor/evaluation selectors; complete original12-case fixture still supplies all same-theory syntax seeds.
RECIPIENT_IDS = ('fresh-inc-point-chain-w', 'fresh-inc-reversed-line-chain')
AUTHOR_IDENTITY = "/root/hilbert_ordering_diagnosis"
UPSTREAM_REVIEW_PINS = {'compiler_person_review': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-literal-compiler-independent-source-20261013/source-review-v2.json', 'sha256': '0e782dd6207746fa95b5109f32beaf45036b9edfd6be226fa182c1d581598cf8', 'bytes': 51269}, 'oracle_person_review': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-independent-oracles-person-review-20261013/source-review-v1.json', 'sha256': '86091bf909f486ff160fad27606ffd7f8d1945737d63218d3c68ea4986a1f7ee', 'bytes': 33603}}

STATIC_PROFILE_ID = 'hilbert-first-checked-equality-cohort-static-v1'
STATIC_PROFILE_PIN = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/static-profile-plan-v1.json', 'sha256': '91ed32762629eb127319d3710b9f7fab8d05a87226b203497d346bb6104cfbc7', 'bytes': 5565}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def path_for(pin):
    path = Path(pin['path'])
    return path if path.is_absolute() else ROOT / path


def hash_pin(path, declared=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return {'path': declared if declared is not None else str(path.resolve()),
            'sha256': h.hexdigest(), 'bytes': size}


def verify_pin(pin):
    if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
            or type(pin['path']) is not str or type(pin['bytes']) is not int
            or pin['bytes'] < 0 or type(pin['sha256']) is not str
            or len(pin['sha256']) != 64
            or any(char not in '0123456789abcdef' for char in pin['sha256'])):
        raise ValueError('exact literal path/hash/length pin required')
    if hash_pin(path_for(pin), pin['path']) != pin:
        raise ValueError('exact pinned bytes changed: ' + pin['path'])


def read_metadata(path, expected_pin=None):
    with Path(path).open('rb') as stream:
        raw = stream.read(METADATA_LIMIT + 1)
        if len(raw) > METADATA_LIMIT or stream.read(1) != b'':
            raise ValueError('bounded entire plan/source-review metadata required')
    if expected_pin is not None:
        if (Path(path).resolve() != path_for(expected_pin).resolve()
                or len(raw) != expected_pin['bytes']
                or hashlib.sha256(raw).hexdigest() != expected_pin['sha256']):
            raise ValueError('metadata parsed from same authenticated full raw buffer')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate JSON key')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def load_source(name, pin):
    verify_pin(pin)
    path = path_for(pin).resolve(); raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('same authenticated source buffer before module execution')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    if Path(module.__file__).resolve() != path:
        raise ValueError('exact loaded module source origin')
    return module

VERIFY_RAW = verify_pin
READ_ROOT = read_metadata

def canonical_full_pin(pin):
    """Normalize only safe literal ROOT-relative spelling; never SHA-only aliases."""
    if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
            or type(pin['path']) is not str or not pin['path']
            or type(pin['bytes']) is not int or pin['bytes'] < 0
            or type(pin['sha256']) is not str or len(pin['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in pin['sha256'])):
        raise ValueError('exact typed full pin')
    declared = pin['path']; path = Path(declared)
    parts = declared.split('/')
    if path.is_absolute():
        if any(part in ('', '.', '..') for part in parts[1:]) or str(path.resolve()) != declared:
            raise ValueError('canonical ABS pin; no traversal or symlink alias')
    else:
        if any(part in ('', '.', '..') for part in parts) or str(path) != declared:
            raise ValueError('safe literal ROOT-relative pin only')
        path = ROOT / path
        if str(path.resolve()) != str(path) or not path.resolve().is_relative_to(ROOT):
            raise ValueError('ROOT-relative historical pin cannot escape or alias')
    return dict(path=str(path.resolve()), sha256=pin['sha256'], bytes=pin['bytes'])


def tree_pins(value):
    """Only traverse already decoded named reader roots; never decode ancestors."""
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            if set(item) == {'path', 'sha256', 'bytes'}:
                yield item
            else:
                pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)


def validate_source_review(review_pin, sources, inputs, phase):
    review = READ_ROOT(path_for(review_pin), expected_pin=review_pin)
    if (review.get('schema') != 'independent-Hilbert-next-' + phase + '-worker-source-review-v1'
            or review.get('scope') != 'Hilbert-next-' + phase + '-worker'
            or review.get('source_only') is not True or review.get('source_ready') is not True
            or review.get('scientific_calls') != 0 or type(review.get('scientific_calls')) is not int
            or review.get('scientific_acceptance') is not False
            or review.get('author_identity') != AUTHOR_IDENTITY
            or type(review.get('reviewer_identity')) is not str
            or not review['reviewer_identity'] or review['reviewer_identity'] == AUTHOR_IDENTITY
            or canonical(review.get('sources')) != canonical(sources)
            or canonical(review.get('inputs')) != canonical(inputs)
            or canonical(review.get('upstream_reviews')) != canonical(UPSTREAM_REVIEW_PINS)):
        raise ValueError('exact different-person worker source review; no scientific admission')
    if (review.get('static_profile_id') != STATIC_PROFILE_ID
            or review.get('static_profile_plan') != STATIC_PROFILE_PIN):
        raise ValueError('current source review must bind exact fresh static profile')
    profile = READ_ROOT(path_for(STATIC_PROFILE_PIN), expected_pin=STATIC_PROFILE_PIN)
    if (profile.get('profile_id') != STATIC_PROFILE_ID
            or tuple(case['id'] for case in profile['selected_cases']) != RECIPIENT_IDS
            or profile['sources']['compiler'] != sources.get('compiler', profile['sources']['compiler'])
            or any(case['rows'] != 24 or len(case['hypotheses']) != 3 for case in profile['selected_cases'])):
        raise ValueError('exact complete declared donor/evaluation static profile')
    roots = [('worker_source_review', review_pin, review),
             ('static_profile_plan', STATIC_PROFILE_PIN, profile)]
    for role, raw_pin_value in UPSTREAM_REVIEW_PINS.items():
        VERIFY_RAW(raw_pin_value)
        current = READ_ROOT(path_for(raw_pin_value), expected_pin=raw_pin_value)
        if role == 'compiler_person_review':
            if (current.get('schema') != 'SOURCE-only-independent-person-Hilbert-literal-compiler-review-v2'
                    or current.get('source_only') is not True
                    or current.get('source_ready_for_ROOT_successor_design') is not True
                    or current.get('all_nominal_source_assessments_pass') is not True
                    or current.get('scientific_acceptance') is not False):
                raise ValueError('exact upstream compiler SOURCE-only review')
        else:
            if (current.get('schema') != 'SOURCE-only-Hilbert-independent-oracles-person-review-v1'
                    or current.get('source_only') is not True or current.get('source_ready') is not True
                    or current.get('scientific_calls') != 0
                    or current.get('all_nominal_source_assessments_pass') is not True
                    or current.get('scientific_acceptance') is not False):
                raise ValueError('exact upstream independent oracle SOURCE-only review')
        roots.append((role, raw_pin_value, current))
    return review, roots


def admit_closure(plan, plan_pin, roots):
    """Complete raw closure with one exact worker-plan self exclusion only."""
    closure = plan['closure']
    if type(closure) is not list or not closure:
        raise ValueError('complete canonical raw closure required')
    by_path = {}
    for literal in closure:
        normalized = canonical_full_pin(literal)
        if literal != normalized or normalized['path'] in by_path or normalized['path'] == plan_pin['path']:
            raise ValueError('closure canonical ABS unique paths and exact self exclusion')
        VERIFY_RAW(literal); by_path[literal['path']] = literal
    for label, root_pin, root_value in [('worker_plan', plan_pin, plan), *roots]:
        normalized = canonical_full_pin(root_pin)
        if label != 'worker_plan' and by_path.get(normalized['path']) != normalized:
            raise ValueError('entire named raw reader root absent from closure: ' + label)
        for literal in tree_pins(root_value):
            normalized = canonical_full_pin(literal)
            if by_path.get(normalized['path']) != normalized:
                raise ValueError('entire named decoded value-tree pin absent from closure: ' + label)
    return dict(schema='complete-Hilbert-next-worker-raw-closure-check-v1',
        closure=closure, reader_roots=[dict(role=label, pin=root_pin) for label, root_pin, _ in roots],
        worker_plan_self_exclusion=plan_pin, full_path_hash_length_membership=True,
        arbitrary_ancestor_JSON_decoding=False, scientific_acceptance=False)


def exclusive_json(path, value):
    with Path(path).open('xb') as stream:
        encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=False, allow_nan=False)
        for chunk in encoder.iterencode(value):
            stream.write(chunk.encode('utf8'))
        stream.write(b'\n')


def exclusive_gzip_json(path, value):
    with Path(path).open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                                       ensure_ascii=False, allow_nan=False)
            for chunk in encoder.iterencode(value):
                stream.write(chunk.encode('utf8'))
            stream.write(b'\n')


class DiagnosticSink:
    """Bounded scalar producer observations, not any acceptance authority.

    One record is serialized/written/flushed at a time; no historical event list
    is retained. Every emission/close/hash remains within the enclosing phase.
    PID and elapsed use this emitter, never cross-process absolute timestamps.
    Caps fail the phase rather than dropping records. The closed trace's last
    event precedes final receipt serialization; only ROOT owns terminal scope.
    """
    def __init__(self, path, began):
        self.path = Path(path); self.began = began; self.pid = os.getpid()
        self.stream = self.path.open('xb'); self.records = 0; self.bytes = 0
        self.closed = False; self.last_elapsed = 0.0

    def __call__(self, event):
        if self.closed:
            raise ValueError('diagnostics already closed')
        if type(event) is not dict or set(event) != {'phase', 'milestone', 'counters'}:
            raise ValueError('exact scalar diagnostic event grammar required')
        for field in ('phase', 'milestone'):
            text = event[field]
            if (type(text) is not str or not 1 <= len(text) <= 80
                    or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/'
                           for char in text)):
                raise ValueError('bounded ASCII diagnostic phase/milestone required')
        counters = event['counters']
        if type(counters) is not dict or len(counters) > 12:
            raise ValueError('bounded scalar diagnostic counters required')
        for name, value in counters.items():
            if (type(name) is not str or not 1 <= len(name) <= 64
                    or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
                           for char in name)
                    or type(value) is not int or not 0 <= value < 1 << 64):
                raise ValueError('diagnostic names/exact uint64 counters only')
        elapsed = time.perf_counter() - self.began
        if not math.isfinite(elapsed) or elapsed < self.last_elapsed:
            raise ValueError('finite emitter-local monotone elapsed duration required')
        record = {'schema': DIAGNOSTIC_SCHEMA, 'index': self.records,
                  'emitter_pid': self.pid, 'worker_elapsed_seconds': elapsed,
                  'event': event}
        raw = (canonical(record) + '\n').encode('utf8')
        if (len(raw) > MAX_DIAGNOSTIC_RECORD_BYTES
                or self.records >= MAX_DIAGNOSTIC_RECORDS
                or self.bytes + len(raw) > MAX_DIAGNOSTIC_BYTES):
            raise ValueError('diagnostic cap reached; no truncation or salvage')
        written = self.stream.write(raw)
        if written != len(raw):
            raise IOError('incomplete diagnostic record write')
        self.stream.flush()
        self.records += 1; self.bytes += len(raw); self.last_elapsed = elapsed

    def close(self):
        if not self.closed:
            self.stream.close(); self.closed = True

    def summary(self):
        return {'schema': DIAGNOSTIC_SCHEMA, 'path': str(self.path.resolve()),
                'emitter_pid': self.pid, 'records': self.records, 'bytes': self.bytes,
                'last_worker_elapsed_seconds': self.last_elapsed,
                'closed': self.closed, 'complete_catalog_credit': False,
                'logical_credit': False, 'proof_credit': False,
                'resource_acceptance': False}


def main():
    began = time.perf_counter()
    if len(sys.argv) != 3 or sys.argv[1] != 'ROOT-prepare-only':
        raise ValueError('ROOT-prepare-only <fresh exact pinned compact preparation plan>')
    plan_path = Path(sys.argv[2]).resolve()
    plan_pin = hash_pin(plan_path); plan = read_metadata(plan_path, expected_pin=plan_pin)
    expected = {'schema', 'selector', 'output_directory', 'inputs', 'sources',
                'source_review', 'limits', 'ROOT_owned_once_only', 'closure'}
    if (set(plan) != expected or plan['schema'] != PLAN_SCHEMA
            or plan['ROOT_owned_once_only'] is not True):
        raise ValueError('exact prospective ROOT compact plan grammar required')
    if set(plan['inputs']) != {'fixture'} or set(plan['sources']) != set(SOURCE_PATHS):
        raise ValueError('all six exact source roles and declaration fixture required')
    if plan['limits'] != {'whole_seconds': 60, 'peak_bytes': 536870912}:
        raise ValueError('unchanged preparation60s/512MiB envelope required')
    if type(plan['selector']) is not str or plan['selector'] not in RECIPIENT_IDS:
        raise ValueError('exact fresh donor/evaluation selector only; no historical target selector')
    output = Path(plan['output_directory']).resolve()
    if (output.parent != PROGRESS.resolve() or output.exists()
            or not plan_path.is_relative_to(PROGRESS.resolve())):
        raise ValueError('fresh ROOT-owned direct compact preparation child and plan namespace required')
    sources = plan['sources']
    pins = [plan_pin, *plan['inputs'].values(), *sources.values(), plan['source_review']]
    if len({str(path_for(pin).resolve()) for pin in pins}) != len(pins):
        raise ValueError('unambiguous distinct complete source/input paths required')
    for pin in pins:
        verify_pin(pin)
    if (any(sources[role]['sha256'] != sha for role, sha in FROZEN_SHAS.items())
            or plan['inputs']['fixture']['sha256'] != FIXTURE_SHA):
        raise ValueError('unchanged exact decoder/graph/core and whole literal nine-plus-three fixture required')
    for role, path in SOURCE_PATHS.items():
        if path_for(sources[role]).resolve() != path.resolve():
            raise ValueError('exact compact source role/path binding: ' + role)
    if path_for(sources['worker']).resolve() != Path(__file__).resolve():
        raise ValueError('current exact worker identity required')
    for pin in pins:
        if canonical_full_pin(pin) != pin:
            raise ValueError('current direct plan/input/source/review pins must be canonical ABS')
    review, review_roots = validate_source_review(plan['source_review'], sources, plan['inputs'], 'preparation')
    fixture = read_metadata(path_for(plan['inputs']['fixture']), expected_pin=plan['inputs']['fixture'])
    closure_binding = admit_closure(plan, plan_pin,
        [('fixture', plan['inputs']['fixture'], fixture), *review_roots])
    output.mkdir(); receipt_path = output / 'preparation-result-v1.json'; catalog = None
    diagnostics = None
    try:
        diagnostics = DiagnosticSink(output / 'producer-diagnostics-v1.jsonl', began)
        diagnostics({'phase': 'worker', 'milestone': 'source_gate_closed',
                     'counters': {'source_roles': 6, 'fixture_cases': 14}})
        compiler = load_source('Hilbert_RL_donor_literal_compact_compiler_v2', sources['compiler'])
        decoder = load_source('complete_compact_catalog_decoder_v1', sources['decoder'])
        adapter = load_source('complete_compact_point_adapter_v1', sources['compact_engine'])
        core = load_source('complete_compact_unchanged_point_core_v2', sources['point_core'])
        if len([case for case in fixture['cases'] if case['id'] == plan['selector']]) != 1:
            raise ValueError('one exact frozen statement selector required')
        diagnostics({'phase': 'worker', 'milestone': 'imports_closed', 'counters': {}})
        diagnostics({'phase': 'worker', 'milestone': 'compiler_begin', 'counters': {}})
        stage = time.perf_counter()
        header = compiler.compile_to_directory(fixture, plan['selector'], pins,
                                              output / 'catalog-v1', telemetry=diagnostics)
        compilation_seconds = time.perf_counter() - stage
        diagnostics({'phase': 'worker', 'milestone': 'compiler_closed',
                     'counters': {'formulas': header['dimensions']['formula_count'],
                                  'recipes': header['dimensions']['primitive_license_count'],
                                  'nodes': header['codec']['node_count']}})
        catalog_path = output / 'catalog-v1/catalog-v1.json'; catalog_pin = hash_pin(catalog_path)
        stage = time.perf_counter()
        diagnostics({'phase': 'worker', 'milestone': 'decoder_begin', 'counters': {}})
        catalog = decoder.CompactCatalog(catalog_path)
        diagnostics({'phase': 'worker', 'milestone': 'decoder_ready',
                     'counters': {'formulas': catalog.formula_count, 'recipes': catalog.recipe_count}})
        diagnostics({'phase': 'worker', 'milestone': 'graph_begin', 'counters': {}})
        graph = adapter.make_graph_type(core)(catalog=catalog)
        graph_setup_seconds = time.perf_counter() - stage
        if (header != catalog.header or graph.context_id != header['context_id']
                or graph.registry_sha != header['formula_registry_sha256']
                or len(graph.initial_selected) != 3
                or graph.totals != [1, 1, 1] + [0] * 21):
            raise ValueError('exact complete catalog/initial point-model relation mismatch')
        diagnostics({'phase': 'worker', 'milestone': 'graph_ready',
                     'counters': {'rows': 24, 'seed_occurrences': 3}})
        stage = time.perf_counter()
        diagnostics({'phase': 'worker', 'milestone': 'factor_streams_begin', 'counters': {'rows': 24}})
        factor_receipts = []
        for row in range(24):
            item = graph.domain_stream_receipt(row); factor_receipts.append(item)
            diagnostics({'phase': 'worker', 'milestone': 'factor_row_closed',
                         'counters': {'row': row, 'factors': item['factor_count'],
                                      'factor_bytes': item['bytes'], 'candidates': item['count']}})
        factor_stream_seconds = time.perf_counter() - stage
        diagnostics({'phase': 'worker', 'milestone': 'factor_streams_closed', 'counters': {'rows': 24}})
        initial = graph.compact_semantic_state()
        placements = [graph.decorate(key) for key in graph.initial_selected]
        diagnostics({'phase': 'worker', 'milestone': 'seed_identities_closed', 'counters': {'occurrences': 3}})
        initial_candidates = sum(domain.count for domain in graph.domains)
        if (initial_candidates != sum(item['count'] for item in factor_receipts)
                or any(item['excluded_legal'] != [] for item in factor_receipts)
                or graph.metrics['attempts'] != 0 or graph.metrics['branches'] != 0):
            raise ValueError('full initial degrees and no-search preparation boundary required')
        evidence = {'schema': EVIDENCE_SCHEMA, 'raw_closure_binding': closure_binding,
            'status': 'complete_compact_catalog_and_initial_graph_pending_independent_gate',
            'plan': plan_pin, 'inputs': plan['inputs'], 'sources': sources,
            'static_profile_id': STATIC_PROFILE_ID, 'static_profile_plan': STATIC_PROFILE_PIN,
            'source_review': plan['source_review'], 'instance_id': plan['selector'],
            'catalog': catalog_pin, 'catalog_header': header, 'catalog_streams': header['streams'],
            'dimensions': header['dimensions'],
            'initial_graph_small_state': initial, 'initial_selected_full_placements': placements,
            'complete_initial_point_factor_streams': factor_receipts,
            'factor_codec': {'schema': adapter.FACTOR_SCHEMA, 'struct': '<QQQBQ', 'record_bytes': 33,
                'fields': ['recipe_index', 'left_mask', 'right_mask', 'different_byte', 'count'],
                'different_values': [0, 1], 'order': 'strictly increasing original canonical recipe index',
                'positive_count_records_only': True, 'hash_empty_stream': 'SHA256 of zero bytes'},
            'complete_initial_candidate_count': initial_candidates,
            'graph_metrics': dict(graph.metrics), 'compact_metrics': dict(graph.compact_metrics),
            'model_epoch': graph.model_epoch, 'bodies': [], 'groups': [], 'complete_pool_count': 0,
            'pool_capacity': 64, 'pool_over_capacity': 'reject without trimming',
            'compilation_seconds': compilation_seconds, 'graph_setup_seconds': graph_setup_seconds,
            'factor_stream_seconds': factor_stream_seconds,
            'producer_diagnostics': diagnostics.summary(),
            'target_searches': 0, 'point_certificates': 0, 'native_queries': 0, 'RNG_draws': 0,
            'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False,
            'dynamic_search_conformance': False, 'all_five_qualification': False,
            'scope': 'Entire original finite syntax/license order and complete initial24-row point domains. '
                'Implicit factors retain every canonical candidate. Empty cluster library. '
                'Independent compiler/license/initial-domain and complete owned-resource gates pending. '
                'No proof, updated search, Controller/DFS/overlay interface or RL qualification.'}
        # Explicit file/mmap close is part of the measured phase. The small
        # evidence has no borrowed expanded registry/factor/candidate arrays.
        catalog.close(); catalog = None
        diagnostics({'phase': 'worker', 'milestone': 'catalog_views_closed', 'counters': {}})
        result_path = output / 'full-preparation-evidence-v1.json.gz'
        diagnostics({'phase': 'worker', 'milestone': 'evidence_serialization_begin', 'counters': {}})
        exclusive_gzip_json(result_path, evidence)
        diagnostics({'phase': 'worker', 'milestone': 'evidence_closed',
                     'counters': {'bytes': result_path.stat().st_size}})
        for pin in pins:
            verify_pin(pin)
        verify_pin(catalog_pin)
        for pin in header['streams'].values():
            verify_pin(pin)
        result_pin = hash_pin(result_path)
        diagnostics({'phase': 'worker', 'milestone': 'artifact_pins_verified', 'counters': {}})
        diagnostics({'phase': 'worker', 'milestone': 'receipt_serialization_begin', 'counters': {}})
        diagnostics.close()
        diagnostic_pin = hash_pin(diagnostics.path)
        elapsed = time.perf_counter() - began
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        receipt = {'schema': RECEIPT_SCHEMA, 'stage': 'preparation', 'stage_completed': True,
            'raw_closure_binding': closure_binding,
            'status': 'complete_pending_independent_and_ROOT_resource_gates',
            'plan': plan_pin, 'selector': plan['selector'], 'full_result': result_pin,
            'static_profile_id': STATIC_PROFILE_ID, 'static_profile_plan': STATIC_PROFILE_PIN,
            'catalog': catalog_pin, 'catalog_streams': header['streams'],
            'dimensions': header['dimensions'], 'model_epoch': graph.model_epoch,
            'complete_initial_candidate_count': initial_candidates,
            'complete_pool_count': 0, 'source_body_count': 0,
            'worker_seconds_before_final_receipt_serialization': elapsed,
            'self_ru_maxrss_raw': peak, 'self_ru_maxrss_platform': sys.platform,
            'compilation_seconds': compilation_seconds, 'graph_setup_seconds': graph_setup_seconds,
            'factor_stream_seconds': factor_stream_seconds,
            'producer_diagnostics': {'summary': diagnostics.summary(), 'trace': diagnostic_pin,
                'last_milestone': 'receipt_serialization_begin',
                'remaining_postlude': 'positive receipt serialization/close, receipt hash/stdout serialization/close '
                    'and worker exit remain inside ROOT owned phase; trace cannot certify its own terminal'},
            'direct_children_peak_sum_bytes': 0, 'all_direct_children_terminal_and_reaped': True,
            'target_searches': 0, 'point_certificates': 0, 'native_queries': 0, 'RNG_draws': 0,
            'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False,
            'dynamic_search_conformance': False, 'all_five_qualification': False,
            'resource_scope': 'No children. SELF includes touched mmap pages, not merely Python heap. '
                'ROOT separately authenticates complete owned lifetime, final serialization/reap/tool terminal '
                'under owner-main60s/512MiB and separately cold caller90s; later ROOT finalizer charged separately; no universal OS hard-cap claim.'}
        exclusive_json(receipt_path, receipt)
        print(canonical({'stage': 'preparation', 'stage_completed': True,
            'receipt': hash_pin(receipt_path), 'target_searches': 0, 'new_RL_training': False}))
    except Exception as error:
        if catalog is not None:
            catalog.close(); catalog = None
        if diagnostics is not None:
            diagnostics.close()
        if not receipt_path.exists():
            exclusive_json(receipt_path, {'schema': RECEIPT_SCHEMA, 'stage': 'preparation',
                'stage_completed': False, 'status': 'UNKNOWN_preserved_no_retry',
                'plan': plan_pin, 'selector': plan['selector'], 'error_type': type(error).__name__,
                'error': str(error), 'worker_seconds_before_failure_receipt': time.perf_counter() - began,
                'producer_diagnostics': None if diagnostics is None else {
                    'summary': diagnostics.summary(), 'trace': hash_pin(diagnostics.path),
                    'partial_observations_only': True, 'complete_catalog_credit': False},
                'direct_children_peak_sum_bytes': 0, 'all_direct_children_terminal_and_reaped': True,
                'target_searches': 0, 'point_certificates': 0, 'native_queries': 0, 'RNG_draws': 0,
                'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False,
                'dynamic_search_conformance': False, 'all_five_qualification': False})
        raise


if __name__ == '__main__':
    main()
