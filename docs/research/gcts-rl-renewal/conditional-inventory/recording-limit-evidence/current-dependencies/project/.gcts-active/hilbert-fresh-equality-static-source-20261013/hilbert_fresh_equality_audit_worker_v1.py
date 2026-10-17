"""SOURCE ONLY: fresh RL donor/evaluation profile with unchanged complete compact audit.

This future worker never imports the producer compiler/decoder/graph/core. All
grammar/license/domain regeneration is independent. It has no subprocess, PS,
search, RNG, training or native path. Stage='replay' denotes catalog auditing,
not theorem proof replay. Actual source/runtime/resource gates remain ROOT's.
"""
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / '.gcts-active/hilbert-fresh-equality-static-source-20261013'
FROZEN_SOURCE = ROOT / '.gcts-active/cluster-transfer-compact-independent-source-20261012'
ORACLE_SOURCE = ROOT / '.gcts-active/hilbert-next-independent-oracles-source-20261013'
PROGRESS = ROOT / '.gcts-active/hilbert-fresh-equality-static-progress-20261013'
PLAN_SCHEMA = 'ROOT-Hilbert-next-compact-independent-audit-plan-v1'
EVIDENCE_SCHEMA = 'Hilbert-next-complete-compact-catalog-static-evidence-v1'
RECEIPT_SCHEMA = 'Hilbert-next-complete-compact-catalog-static-worker-receipt-v1'
METADATA_LIMIT = 64 * 1024 * 1024
SOURCE_PATHS = {
    'grammar': ROOT / '.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_grammar_v1.py',
    'catalog_audit': FROZEN_SOURCE / 'independent_compact_catalog_audit_v1.py',
    'domains': FROZEN_SOURCE / 'independent_compact_domains_v1.py',
    'worker': SOURCE / 'hilbert_fresh_equality_audit_worker_v1.py',
    'logical_oracle': ORACLE_SOURCE / 'hilbert_fresh_catalog_oracle_v2.py',
    'master': ROOT / 'docs/basic-tiling-algorithm.md'}
ORACLE_SHA = '3b6aee8d9b0c1668f2ccf4e0d3b5e7e87dc9e0dd6579e55308e74c3992d6b3cc'
FIXTURE_SHA = 'b60869d015f5f60caa726864595a6293a4566ffdf04403c2499ade76987ef831'
INPUT_KEYS = frozenset(('fixture', 'producer_plan', 'producer_receipt',
    'preparation_evidence', 'catalog', 'preparation_ROOT_decision', 'producer_diagnostics'))
FROZEN_AUDIT_SHAS = {
    'grammar': '34322db5dc25cd3e0cc1dfa43f379f9f45107442c4f035d955b39f1e21b31db1',
    'catalog_audit': 'db4dc3b904715be3123ed1a9b22eb1ce9144c35aa00c610da94f13263e4334e8',
    'domains': '1b9d6b94c78f363ba20f48234dc1eb48ac9dcfa548e8f0fa1a7350699b059b34',
    'logical_oracle': ORACLE_SHA,
    'master': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}
PRODUCER_PATHS = {
    'compiler': ROOT / '.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_compiler_v1.py',
    'decoder': ROOT / '.gcts-active/cluster-transfer-compact-compiler-source-20261012/compact_catalog_decoder_v1.py',
    'compact_engine': ROOT / '.gcts-active/cluster-transfer-compact-engine-source-20261012/compact_point_graph_v1.py',
    'worker': SOURCE / 'hilbert_fresh_equality_prepare_worker_v1.py',
    'point_core': ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py',
    'master': ROOT / 'docs/basic-tiling-algorithm.md'}
PRODUCER_SHAS = {
    'compiler': '57653bb27eaf3c4dd1e050c70ac360133f78e1f636cd1276a39a20fd64610a56',
    'decoder': '46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293',
    'compact_engine': 'd638f7152ec7fa8293adbd8915b79de60f95d0756952bdc6bf0e40b15f549ca0',
    'worker': 'cc1f05b4b18e4f570b25745a0cf3d3f7c816e4146872f36f8d7a939894acb7e3',
    'point_core': 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd',
    'master': FROZEN_AUDIT_SHAS['master']}
RESOURCE_PREDICATES = frozenset(('actual_tool_terminal', 'caller_clock_bound',
    'owner_terminal_link_present', 'owner_gate', 'post_write_gate',
    'cancelled_at_final_print_false', 'final_print_gate', 'stage_identity',
    'worker_complete', 'all_worker_direct_children_closed',
    'all_owner_direct_children_closed', 'no_owned_leftovers',
    'complete_post_closure_unchanged', 'post_write_exact_terminal'))
DIAGNOSTIC_SCHEMA = 'compact-preparation-producer-diagnostic-record-v1'
DIAGNOSTIC_RECORD_LIMIT = 1024
DIAGNOSTIC_BYTE_LIMIT = 1048576
DIAGNOSTIC_LINE_LIMIT = 4096
COMPILER_MAJOR = [
    ('syntax', 'begin'), ('syntax', 'complete'),
    *[('instantiation', name) for _ in range(4) for name in ('round_begin', 'round_complete')],
    ('templates', 'begin'), ('templates', 'complete'),
    ('equality_product', 'begin'), ('equality_product', 'complete'),
    ('formula_registry', 'begin'), ('formula_sort', 'begin'),
    ('formula_sort', 'keys_complete'), ('formula_registry', 'complete'),
    ('recipe_identity', 'begin'), ('recipe_sort', 'begin'),
    ('recipe_sort', 'first_record_ready'), ('recipe_sort', 'complete'),
    ('recipe_identity', 'complete'), ('nodes', 'begin'), ('nodes', 'complete'),
    ('header', 'begin'), ('header', 'ready_for_serialization')]
COMPILER_PROGRESS_PHASES = frozenset(('instantiation', 'templates', 'equality_product',
    'formula_sort', 'formula_registry', 'recipe_identity', 'nodes'))

# Fresh donor/evaluation selectors; complete original12-case syntax census retained.
RECIPIENT_IDS = ('fresh-inc-point-chain-w', 'fresh-inc-reversed-line-chain')
AUTHOR_IDENTITY = "/root/hilbert_ordering_diagnosis"
UPSTREAM_REVIEW_PINS = {'compiler_person_review': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-literal-compiler-independent-source-20261013/source-review-v2.json', 'sha256': '0e782dd6207746fa95b5109f32beaf45036b9edfd6be226fa182c1d581598cf8', 'bytes': 51269}, 'oracle_person_review': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-independent-oracles-person-review-20261013/source-review-v1.json', 'sha256': '86091bf909f486ff160fad27606ffd7f8d1945737d63218d3c68ea4986a1f7ee', 'bytes': 33603}}

STATIC_PROFILE_ID = 'hilbert-first-checked-equality-cohort-static-v1'
STATIC_PROFILE_PIN = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/static-profile-plan-v1.json', 'sha256': '91ed32762629eb127319d3710b9f7fab8d05a87226b203497d346bb6104cfbc7', 'bytes': 5565}


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def same(a, b, label):
    need(canonical(a) == canonical(b), label)


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        need(name not in result, 'unique literal JSON keys')
        result[name] = value
    return result


def path_for(pin):
    path = Path(pin['path'])
    return path if path.is_absolute() else ROOT / path


def raw_pin(path, declared=None):
    path = Path(path); h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return dict(path=str(path.resolve()) if declared is None else declared,
                sha256=h.hexdigest(), bytes=size)


def verify(pin):
    need(type(pin) is dict and set(pin) == {'path', 'sha256', 'bytes'}
         and type(pin['path']) is str and type(pin['bytes']) is int and pin['bytes'] >= 0
         and type(pin['sha256']) is str and len(pin['sha256']) == 64
         and all(c in '0123456789abcdef' for c in pin['sha256']), 'typed raw pin')
    same(raw_pin(path_for(pin), pin['path']), pin, 'closed raw input/source bytes')


def identical_pin(a, b, label):
    verify(a); verify(b)
    need(path_for(a).resolve() == path_for(b).resolve()
         and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes'], label)


def read_json(path, compressed=False, expected_pin=None):
    path = Path(path)
    with path.open('rb') as stream:
        raw = stream.read(METADATA_LIMIT + 1)
        need(len(raw) <= METADATA_LIMIT and stream.read(1) == b'', 'bounded whole metadata bytes')
    if expected_pin is not None:
        need(path.resolve() == path_for(expected_pin).resolve()
             and len(raw) == expected_pin['bytes']
             and hashlib.sha256(raw).hexdigest() == expected_pin['sha256'],
             'parse and authenticate exactly the same raw bytes')
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
            raw = stream.read(METADATA_LIMIT + 1)
            need(len(raw) <= METADATA_LIMIT and stream.read(1) == b'',
                 'whole bounded compact evidence, no unread decoded tail')
    return json.loads(raw, object_pairs_hook=unique_object,
        parse_constant=lambda text: (_ for _ in ()).throw(ValueError('nonfinite JSON ' + text)))


def load(name, pin):
    verify(pin)
    path = path_for(pin).resolve(); raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('same authenticated source buffer before module execution')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
    if Path(module.__file__).resolve() != path:
        raise ValueError('exact loaded module source origin')
    return module

VERIFY_RAW = verify
READ_ROOT = read_json

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
            or profile['sources']['compiler']['sha256'] != PRODUCER_SHAS['compiler']
            or profile['sources']['independent_grammar']['sha256'] != FROZEN_AUDIT_SHAS['grammar']
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

def checker_provenance(module, pin):
    """Exact unchanged injected class origin; no alternative checker injection."""
    expected_path = path_for(pin).resolve()
    cls = module.GroundChecker
    need(cls.__module__ == module.__name__ and Path(module.__file__).resolve() == expected_path,
         'exact current pinned GroundChecker module')
    methods = ('__init__', 'term', 'formula', 'command', 'proof')
    for name in methods:
        method = getattr(cls, name)
        need(method.__module__ == module.__name__
             and Path(method.__code__.co_filename).resolve() == expected_path,
             'same authenticated GroundChecker source method ' + name)
    verify(pin)
    return dict(source=pin, class_name='GroundChecker', module_name=module.__name__,
        methods=list(methods), same_authenticated_raw_source_buffer=True,
        five_commands_only=['axiom', 'instantiate', 'eq_subst', 'mp', 'assumption'],
        native_accepted=False, proof_accepted=False)


def write_json(path, value, compressed=False):
    with Path(path).open('xb') as raw:
        if compressed:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
                for part in json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                        ensure_ascii=False, allow_nan=False).iterencode(value):
                    stream.write(part.encode('utf8'))
                stream.write(b'\n')
        else:
            for part in json.JSONEncoder(sort_keys=True, separators=(',', ':'),
                    ensure_ascii=False, allow_nan=False).iterencode(value):
                raw.write(part.encode('utf8'))
            raw.write(b'\n')


def prerequisite(inputs, selector):
    producer = read_json(path_for(inputs['producer_plan']), expected_pin=inputs['producer_plan'])
    need(set(producer) == {'schema', 'selector', 'output_directory', 'inputs', 'sources',
            'source_review', 'limits', 'ROOT_owned_once_only', 'closure'}
         and producer['schema'] == 'ROOT-Hilbert-next-compact-preparation-plan-v1'
         and producer['selector'] == selector and producer['ROOT_owned_once_only'] is True,
         'actual exact once-only preparation plan')
    same(producer['limits'], dict(whole_seconds=60, peak_bytes=536870912), 'unchanged producer envelope')
    need(set(producer['inputs']) == {'fixture'} and set(producer['sources']) == {
        'compiler', 'decoder', 'compact_engine', 'worker', 'point_core', 'master'}, 'whole preparation source roles')
    identical_pin(producer['inputs']['fixture'], inputs['fixture'], 'same exact original fixture')
    producer_plan_pin = raw_pin(path_for(inputs['producer_plan']))
    bindings = [producer_plan_pin, *producer['inputs'].values(),
                *producer['sources'].values(), producer['source_review']]
    for pin in bindings:
        verify(pin)
    for role, path in PRODUCER_PATHS.items():
        need(producer['sources'][role]['path'] == str(path.resolve())
             and producer['sources'][role]['sha256'] == PRODUCER_SHAS[role],
             'exact canonical ABS telemetry producer source role ' + role)
    producer_review, producer_review_roots = validate_source_review(producer['source_review'],
        producer['sources'], producer['inputs'], 'preparation')
    producer_fixture = read_json(path_for(producer['inputs']['fixture']), expected_pin=producer['inputs']['fixture'])
    admit_closure(producer, producer_plan_pin,
        [('fixture', producer['inputs']['fixture'], producer_fixture), *producer_review_roots])
    decision = read_json(path_for(inputs['preparation_ROOT_decision']), expected_pin=inputs['preparation_ROOT_decision'])
    need(decision['schema'] == 'ROOT-fresh-catalog-stage-final-decision-v1'
         and decision['stage'] == 'preparation' and decision['ROOT_final_accepted'] is True
         and decision['status'] == 'accepted_complete_owned_stage'
         and type(decision['predicates']) is dict and set(decision['predicates']) == RESOURCE_PREDICATES
         and all(v is True for v in decision['predicates'].values())
         and decision['mismatches'] == [] and decision['native_accepted'] is False
         and decision['all_five_qualification'] is False, 'closed ROOT preparation resources prerequisite')
    limits = decision['limits']
    need(limits['whole_seconds'] == 60 and limits['peak_bytes'] == 536870912
         and limits['caller_seconds'] == 90, 'same complete owned preparation budgets')
    elapsed = decision['caller_elapsed_seconds']
    need(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0
         and decision['caller_finish_reserve_seconds'] == 1 and elapsed + 1 <= 90,
         'actual separately observed caller scope')
    identical_pin(decision['worker'], inputs['producer_receipt'], 'ROOT accepted exact producer receipt')
    verify(decision['plan'])
    owner_plan = read_json(path_for(decision['plan']), expected_pin=decision['plan'])
    need(owner_plan['stage'] == 'preparation'
         and Path(ROOT / owner_plan['worker_receipt']).resolve() == path_for(inputs['producer_receipt']).resolve(),
         'ROOT accepted exact preparation worker scope')
    same(owner_plan['limits'], dict(whole_seconds=60, peak_bytes=536870912, caller_seconds=90),
         'ROOT whole producer/caller envelope')
    need(len(owner_plan['argv']) == 5 and owner_plan['argv'][1] == '-B'
         and Path(owner_plan['argv'][2]).resolve() == PRODUCER_PATHS['worker'].resolve()
         and owner_plan['argv'][3] == 'ROOT-prepare-only'
         and Path(owner_plan['argv'][4]).resolve() == path_for(inputs['producer_plan']).resolve(),
         'ROOT accepted exact literal telemetry worker and plan')
    for pin in owner_plan['closure']:
        verify(pin)
    receipt = read_json(path_for(inputs['producer_receipt']), expected_pin=inputs['producer_receipt'])
    need(receipt['schema'] == 'Hilbert-next-compact-preparation-worker-receipt-v1'
         and receipt['stage'] == 'preparation' and receipt['stage_completed'] is True
         and receipt['status'] == 'complete_pending_independent_and_ROOT_resource_gates'
         and receipt['selector'] == selector and receipt['direct_children_peak_sum_bytes'] == 0
         and receipt['all_direct_children_terminal_and_reaped'] is True
         and receipt['logical_accepted'] is False and receipt['static_resource_qualified'] is False,
         'completed preparation is not a primitive licensing authority')
    identical_pin(receipt['plan'], inputs['producer_plan'], 'receipt exact producer plan')
    identical_pin(receipt['full_result'], inputs['preparation_evidence'], 'receipt entire compact evidence')
    identical_pin(receipt['catalog'], inputs['catalog'], 'receipt exact whole catalog header')
    return producer, bindings, receipt, decision


def producer_diagnostics(inputs, producer, receipt, evidence, header, decision):
    """Metadata only: authenticate every closed scalar trace byte before imports.

    No diagnostic counter supplies an independent license or domain answer. The
    trusted ROOT resource decision and source-owned retained process ledger are
    provenance gates, not a new host observer or universal resource proof.
    """
    closed = receipt['producer_diagnostics']
    need(type(closed) is dict and set(closed) == {'summary', 'trace', 'last_milestone', 'remaining_postlude'}
         and closed['last_milestone'] == 'receipt_serialization_begin', 'final closed diagnostic receipt grammar')
    identical_pin(closed['trace'], inputs['producer_diagnostics'], 'entire exact closed trace')
    output = Path(producer['output_directory']).resolve()
    need(output.parent == PROGRESS.resolve()
         and path_for(inputs['producer_diagnostics']).resolve() == output / 'producer-diagnostics-v1.jsonl'
         and path_for(inputs['producer_receipt']).resolve() == output / 'preparation-result-v1.json'
         and path_for(inputs['preparation_evidence']).resolve() == output / 'full-preparation-evidence-v1.json.gz'
         and path_for(inputs['catalog']).resolve() == output / 'catalog-v1/catalog-v1.json',
         'exact common fresh producer output ownership')
    same(closed['remaining_postlude'],
         'positive receipt serialization/close, receipt hash/stdout serialization/close '
         'and worker exit remain inside ROOT owned phase; trace cannot certify its own terminal',
         'final receipt/stdout terminal remains external ROOT provenance')
    summary = closed['summary']; pid = summary['emitter_pid']
    need(type(pid) is int and pid > 0, 'exact positive producer emitter PID')
    owner = read_json(path_for(decision['owner']), expected_pin=decision['owner'])
    need(owner['schema'] == 'ROOT-guard-native-owner-terminal-v2'
         and owner['stage'] == 'preparation' and owner['resource_gate_accepted'] is True
         and owner['worker_returncode'] == 0 and owner['error'] is None
         and owner['cancelled'] is False and owner['cleanup_errors'] == []
         and owner['owned_leftovers'] == [] and owner['all_direct_children_terminal_and_reaped'] is True,
         'ROOT source-owned producer reaped without cancellation/failure')
    identical_pin(owner['plan'], decision['plan'], 'same accepted producer owner plan')
    identical_pin(owner['worker_receipt'], inputs['producer_receipt'], 'same owner closed worker receipt')
    verify(owner['ownership_ledger'])
    ledger = read_json(path_for(owner['ownership_ledger']), compressed=True, expected_pin=owner['ownership_ledger'])
    birth = ledger['final_retained_births'].get(str(pid))
    need(type(birth) is str and 0 < len(birth) <= 256, 'emitter retained as source-owned worker process identity')
    seen = 0
    for sample in ledger['samples']:
        row = sample['owned_rows'].get(str(pid))
        if row is not None:
            need(row['birth'] == birth and type(row['pgid']) is int and row['pgid'] == pid,
                 'emitter exact sampled birth and fresh worker-led group')
            seen += 1
    need(seen > 0, 'at least one source-owned retained worker observation; no invented PID binding')
    dims = header['dimensions']
    worker_major = [
        ('source_gate_closed', {'source_roles': 6, 'fixture_cases': 14}),
        ('imports_closed', {}), ('compiler_begin', {}),
        ('compiler_closed', {'formulas': dims['formula_count'],
            'recipes': dims['primitive_license_count'], 'nodes': header['codec']['node_count']}),
        ('decoder_begin', {}), ('decoder_ready', {'formulas': dims['formula_count'],
            'recipes': dims['primitive_license_count']}), ('graph_begin', {}),
        ('graph_ready', {'rows': 24, 'seed_occurrences': 3}),
        ('factor_streams_begin', {'rows': 24}),
        *[('factor_row_closed', {'row': row, 'factors': value['factor_count'],
            'factor_bytes': value['bytes'], 'candidates': value['count']})
          for row, value in enumerate(evidence['complete_initial_point_factor_streams'])],
        ('factor_streams_closed', {'rows': 24}),
        ('seed_identities_closed', {'occurrences': 3}), ('catalog_views_closed', {}),
        ('evidence_serialization_begin', {}),
        ('evidence_closed', {'bytes': inputs['preparation_evidence']['bytes']}),
        ('artifact_pins_verified', {}), ('receipt_serialization_begin', {})]
    need(len(worker_major) == 40, 'full24 point-row diagnostics and40 milestones required')
    hasher = hashlib.sha256(); size = 0; records = 0; last = 0.0
    worker_index = 0; compiler_index = 0; compiler_count = 0; progress_count = 0
    in_compiler = False; prefix = None
    def expected_summary(closed_value):
        return dict(schema=DIAGNOSTIC_SCHEMA, path=str(path_for(inputs['producer_diagnostics']).resolve()),
            emitter_pid=pid, records=records, bytes=size, last_worker_elapsed_seconds=last,
            closed=closed_value, complete_catalog_credit=False, logical_credit=False,
            proof_credit=False, resource_acceptance=False)
    with path_for(inputs['producer_diagnostics']).open('rb') as stream:
        while True:
            raw = stream.readline(DIAGNOSTIC_LINE_LIMIT + 1)
            if not raw:
                break
            need(len(raw) <= DIAGNOSTIC_LINE_LIMIT and raw.endswith(b'\n')
                 and records < DIAGNOSTIC_RECORD_LIMIT
                 and size + len(raw) <= DIAGNOSTIC_BYTE_LIMIT, 'whole bounded closed diagnostic lines')
            value = json.loads(raw, object_pairs_hook=unique_object,
                parse_constant=lambda text: (_ for _ in ()).throw(ValueError('nonfinite diagnostic ' + text)))
            need(type(value) is dict and set(value) == {'schema', 'index', 'emitter_pid',
                 'worker_elapsed_seconds', 'event'} and value['schema'] == DIAGNOSTIC_SCHEMA
                 and type(value['index']) is int and value['index'] == records
                 and type(value['emitter_pid']) is int and value['emitter_pid'] == pid,
                 'exact complete diagnostic index/emitter identity')
            elapsed = value['worker_elapsed_seconds']
            need(type(elapsed) is float and math.isfinite(elapsed) and elapsed >= last,
                 'finite nondecreasing emitter-local diagnostic duration')
            event = value['event']
            need(type(event) is dict and set(event) == {'phase', 'milestone', 'counters'},
                 'exact scalar diagnostic event')
            for field in ('phase', 'milestone'):
                text = event[field]
                need(type(text) is str and 0 < len(text) <= 80
                     and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in text),
                     'frozen bounded phase/milestone vocabulary')
            counters = event['counters']
            need(type(counters) is dict and len(counters) <= 12
                 and all(type(name) is str and 0 < len(name) <= 64
                    and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in name)
                    and type(number) is int and 0 <= number < 1 << 64
                    for name, number in counters.items()), 'bounded exact scalar uint64 diagnostic counters')
            same((canonical(value) + '\n').encode('utf8').decode('utf8'), raw.decode('utf8'),
                 'exact canonical diagnostic bytes with no unread or duplicate tail')
            hasher.update(raw); size += len(raw); records += 1; last = elapsed
            if event['phase'] == 'worker':
                need(worker_index < len(worker_major), 'no extra worker milestones')
                milestone, expected_counters = worker_major[worker_index]
                same(event, dict(phase='worker', milestone=milestone, counters=expected_counters),
                     'exact worker milestone ordering/bound artifact counts')
                if milestone == 'compiler_begin':
                    in_compiler = True
                elif milestone == 'compiler_closed':
                    need(compiler_index == len(COMPILER_MAJOR), 'all27 compiler major milestones before completion')
                    in_compiler = False
                elif milestone == 'seed_identities_closed':
                    prefix = expected_summary(False)
                worker_index += 1
            else:
                need(in_compiler and compiler_count < 512, 'compiler-only bounded event region')
                compiler_count += 1
                if event['milestone'] == 'progress':
                    need(event['phase'] in COMPILER_PROGRESS_PHASES and progress_count < 480,
                         'bounded source-listed compiler progress event')
                    progress_count += 1
                else:
                    need(compiler_index < len(COMPILER_MAJOR)
                         and (event['phase'], event['milestone']) == COMPILER_MAJOR[compiler_index],
                         'exact compiler mandatory source phase order')
                    if event['phase'] == 'instantiation':
                        same(counters['round'], (compiler_index - 2) // 2, 'exact four snapshot round diagnostic index')
                    compiler_index += 1
    need(records > 0 and worker_index == 40 and compiler_index == 27
         and compiler_count == 27 + progress_count and prefix is not None,
         'whole complete worker/compiler diagnostic stream, never a partial prefix')
    need(size == inputs['producer_diagnostics']['bytes']
         and hasher.hexdigest() == inputs['producer_diagnostics']['sha256'],
         'parse and authenticate same entire diagnostic raw buffer')
    same(summary, expected_summary(True), 'complete exact closed summary versus full raw trace')
    same(evidence['producer_diagnostics'], prefix, 'open evidence snapshot is exact observed prefix only')
    before_receipt = receipt['worker_seconds_before_final_receipt_serialization']
    need(type(before_receipt) in (float, int) and math.isfinite(before_receipt)
         and last <= before_receipt <= 60, 'emitter-local trace duration nested before receipt postlude')
    return dict(trace=inputs['producer_diagnostics'], summary=summary,
        producer_evidence_prefix=prefix, worker_milestones=40, compiler_major_milestones=27,
        compiler_progress_records=progress_count, ownership_ledger=owner['ownership_ledger'],
        source_owned_emitter_observations=seen,
        scope='Closed scalar producer diagnostics and trusted ROOT source-owned preparation provenance only. '
              'No diagnostic licensing/proof/count authority, new resource observer or dynamic search credit.'), owner['ownership_ledger']


def main():
    began = time.perf_counter()
    need(len(sys.argv) == 3 and sys.argv[1] == 'ROOT-audit-only', 'ROOT-audit-only exact prospective audit plan')
    plan_path = Path(sys.argv[2]).resolve(); plan_pin = raw_pin(plan_path)
    plan = read_json(plan_path, expected_pin=plan_pin)
    need(type(plan) is dict and set(plan) == {'schema', 'selector', 'output_directory', 'inputs',
         'sources', 'source_review', 'limits', 'ROOT_owned_once_only', 'closure'}
         and plan['schema'] == PLAN_SCHEMA and plan['ROOT_owned_once_only'] is True,
         'exact future audit plan grammar')
    need(plan_path.parent == PROGRESS.resolve(), 'owned audit plan namespace')
    same(plan['limits'], dict(whole_seconds=60, peak_bytes=536870912), 'unchanged independent60s/512MiB budget')
    need(type(plan['inputs']) is dict and set(plan['inputs']) == INPUT_KEYS
         and type(plan['sources']) is dict and set(plan['sources']) == set(SOURCE_PATHS),
         'exact complete independent sources and actual prerequisites')
    inputs, sources = plan['inputs'], plan['sources']
    pins = [plan_pin, *inputs.values(), *sources.values(), plan['source_review']]
    need(len({str(path_for(p).resolve()) for p in pins}) == len(pins), 'distinct full literal paths')
    for pin in pins:
        verify(pin)
    for role, path in SOURCE_PATHS.items():
        need(path_for(sources[role]).resolve() == path.resolve(), 'exact independent source role ' + role)
    need(sources['logical_oracle']['sha256'] == ORACLE_SHA and inputs['fixture']['sha256'] == FIXTURE_SHA,
         'exact reviewed independent five-rule checker and whole literal nine-plus-three fixture')
    need(all(sources[role]['sha256'] == sha for role, sha in FROZEN_AUDIT_SHAS.items()),
         'byte-identical independent grammar/license/domain/oracle/master sources')
    need(type(plan['selector']) is str and plan['selector'] in RECIPIENT_IDS,
         'exact fresh donor/evaluation selector only; no historical target selector')
    for pin in pins:
        same(canonical_full_pin(pin), pin, 'current direct audit pin canonical ABS')
    review, review_roots = validate_source_review(plan['source_review'], sources,
        {'fixture': inputs['fixture']}, 'audit')
    output = Path(plan['output_directory']).resolve()
    need(output.parent == PROGRESS.resolve() and not output.exists(), 'fresh independent once-only output')
    producer, bindings, producer_receipt, decision = prerequisite(inputs, plan['selector'])
    pins.extend(bindings); pins.extend([decision['plan'], decision['actual_tool'], decision['owner'], decision['post_write']])
    for pin in pins:
        verify(pin)
    evidence = read_json(path_for(inputs['preparation_evidence']), compressed=True,
                         expected_pin=inputs['preparation_evidence'])
    need(evidence['static_profile_id'] == STATIC_PROFILE_ID
         and evidence['static_profile_plan'] == STATIC_PROFILE_PIN
         and producer_receipt['static_profile_id'] == STATIC_PROFILE_ID
         and producer_receipt['static_profile_plan'] == STATIC_PROFILE_PIN,
         'actual preparation bound to same fresh static profile')
    need(evidence['schema'] == 'Hilbert-next-compact-preparation-evidence-v1'
         and evidence['status'] == 'complete_compact_catalog_and_initial_graph_pending_independent_gate'
         and evidence['instance_id'] == plan['selector'], 'exact complete source preparation evidence')
    for role in ('plan', 'inputs', 'sources', 'source_review'):
        same(evidence[role], producer[role] if role != 'plan' else raw_pin(path_for(inputs['producer_plan'])),
             'exact preparation evidence binding ' + role)
    header = read_json(path_for(inputs['catalog']), expected_pin=inputs['catalog'])
    same(evidence['catalog_header'], header, 'actual raw header versus decoded evidence')
    identical_pin(evidence['catalog'], inputs['catalog'], 'raw catalog identity binding')
    same(evidence['catalog_streams'], header['streams'], 'all raw catalog streams')
    same(producer_receipt['catalog_streams'], header['streams'], 'receipt all raw catalog streams')
    for pin in header['streams'].values():
        verify(pin); pins.append(pin)
    for value in (evidence, producer_receipt):
        for field in ('target_searches', 'point_certificates', 'native_queries', 'RNG_draws'):
            same(value[field], 0, 'no hidden proof/search/native/RNG action')
        for field in ('new_RL_training', 'logical_accepted', 'static_resource_qualified',
                      'dynamic_search_conformance', 'all_five_qualification'):
            same(value[field], False, 'pending source/static scope')
    same(evidence['bodies'], [], 'empty complete bootstrap cluster library')
    same(evidence['groups'], [], 'no hidden cluster pool')
    same(evidence['complete_pool_count'], 0, 'complete empty initial pool')
    same(evidence['pool_capacity'], 64, 'unchanged frozen pool capacity')
    same(evidence['pool_over_capacity'], 'reject without trimming', 'complete inventory no narrowing')
    diagnostic_binding, ownership_pin = producer_diagnostics(inputs, producer, producer_receipt,
                                                            evidence, header, decision)
    pins.append(ownership_pin)
    # Explicit same-buffer reader roots only; full closure includes raw ownership data,
    # but does not recursively decode arbitrary pinned ancestor files.
    producer_review = read_json(path_for(producer['source_review']), expected_pin=producer['source_review'])
    owner_plan = read_json(path_for(decision['plan']), expected_pin=decision['plan'])
    owner_terminal = read_json(path_for(decision['owner']), expected_pin=decision['owner'])
    ledger = read_json(path_for(ownership_pin), compressed=True, expected_pin=ownership_pin)
    fixture = read_json(path_for(inputs['fixture']), expected_pin=inputs['fixture'])
    closure_binding = admit_closure(plan, plan_pin, [*review_roots,
        ('fixture', inputs['fixture'], fixture), ('producer_plan', inputs['producer_plan'], producer),
        ('producer_source_review', producer['source_review'], producer_review),
        ('producer_receipt', inputs['producer_receipt'], producer_receipt),
        ('preparation_ROOT_decision', inputs['preparation_ROOT_decision'], decision),
        ('producer_owner_plan', decision['plan'], owner_plan),
        ('preparation_evidence', inputs['preparation_evidence'], evidence),
        ('catalog_header', inputs['catalog'], header),
        ('producer_owner_terminal', decision['owner'], owner_terminal),
        ('producer_ownership_ledger', ownership_pin, ledger),
        ('producer_diagnostic_raw', inputs['producer_diagnostics'], None)])
    output.mkdir(); receipt_path = output / 'audit-result-v1.json'
    try:
        old = load('Hilbert_next_independent_five_rule_logical_oracle_v2', sources['logical_oracle'])
        grammar_module = load('Hilbert_next_independent_complete_compact_grammar_v2', sources['grammar'])
        catalog_module = load('independent_complete_compact_catalog_audit_v1', sources['catalog_audit'])
        domains_module = load('independent_complete_compact_domains_v1', sources['domains'])
        checker_origin = checker_provenance(old, sources['logical_oracle'])
        grammar = grammar_module.CompleteGrammar(fixture, plan['selector'], bindings, old.GroundChecker)
        reader = catalog_module.IndependentReader(grammar, header, path_for(inputs['catalog']))
        license_path = output / 'complete-independent-licenses-v1.jsonl.gz'
        with license_path.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
                identifiers, logical_counts = reader.licenses(stream)
        reader.header_semantics(identifiers)
        state = domains_module.initial_small_state(grammar, identifiers)
        same(evidence['initial_graph_small_state'], state, 'entire exact initial point state')
        same(evidence['initial_selected_full_placements'], domains_module.seed_placements(grammar, identifiers),
             'all three full separately indexed physical seed identities')
        point_audit = domains_module.audit_factor_receipts(grammar, state,
            evidence['complete_initial_point_factor_streams'])
        same(evidence['factor_codec'], dict(schema='complete-ordered-factor-stream-u64-u64-u64-u8-u64le-v1',
            struct='<QQQBQ', record_bytes=33,
            fields=['recipe_index', 'left_mask', 'right_mask', 'different_byte', 'count'],
            different_values=[0, 1], order='strictly increasing original canonical recipe index',
            positive_count_records_only=True, hash_empty_stream='SHA256 of zero bytes'), 'exact complete factor codec')
        for value in (evidence, producer_receipt):
            same(value['dimensions'], grammar.dimensions, 'whole independent dimension census')
            same(value['model_epoch'], state['model_epoch'], 'original complete model identity')
            same(value['complete_initial_candidate_count'], point_audit['complete_initial_candidate_count'],
                 'all complete initial candidates')
            same(value['complete_pool_count'], 0, 'empty bootstrap pool')
        same(producer_receipt['source_body_count'], 0, 'no invented lemma body')
        same(evidence['graph_metrics']['attempts'], 0, 'no hidden primitive search attempts')
        same(evidence['graph_metrics']['branches'], 0, 'no hidden search branches')
        for pin in pins:
            verify(pin)
        full = dict(schema=EVIDENCE_SCHEMA, raw_closure_binding=closure_binding,
            injected_checker_provenance=checker_origin, status='accepted_complete_semantics_pending_ROOT_resources',
            plan=plan_pin, inputs=inputs, sources=sources, source_review=plan['source_review'],
            static_profile_id=STATIC_PROFILE_ID, static_profile_plan=STATIC_PROFILE_PIN,
            instance_id=plan['selector'], preparation_ROOT_decision=inputs['preparation_ROOT_decision'],
            catalog=inputs['catalog'], catalog_streams=header['streams'],
            dimensions=grammar.dimensions, formula_registry_sha256=grammar.registry_sha,
            authority_epoch=grammar.authority['epoch'], context_id=grammar.context_id,
            declaration_binding=grammar.declaration_binding, logical_rule_counts=logical_counts,
            complete_licenses=raw_pin(license_path), primitive_license_checks=len(grammar.records),
            all_formulas_checked=True, all_licenses_checked=True, all_DAG_nodes_checked=True,
            original_canonical_order_and_preimages_checked=True,
            point_audit=point_audit, initial_graph_small_state=state,
            producer_diagnostic_metadata_binding=diagnostic_binding,
            all_three_ordered_seed_identities_checked=True,
            source_body_count=0, complete_pool_count=0, logical_accepted=True,
            initial_static_point_accepted=True, static_resource_qualified=False,
            dynamic_search_conformance=False, all_five_qualification=False,
            target_searches=0, point_certificates=0, proof_certificates=0, native_queries=0,
            RNG_draws=0, new_RL_training=False,
            scope='Independent complete original declared finite catalog/primitive licensing and all24 '
                'initial point-domain streams. No producer compiler/decoder/graph imported. '
                'No proof discovery, dynamic Controller/DFS conformance, native or RL acceptance. '
                'ROOT must separately close owner-main60s/512MiB, cold caller90s and later separately charged saved-metadata finalizer; no full-cold60s claim.')
        full_path = output / 'complete-independent-static-evidence-v1.json.gz'
        write_json(full_path, full, compressed=True)
        for pin in pins:
            verify(pin)
        receipt = dict(schema=RECEIPT_SCHEMA, stage='replay', stage_completed=True,
            raw_closure_binding=closure_binding, injected_checker_provenance=checker_origin,
            status='complete_catalog_static_semantic_audit_pending_ROOT_resources',
            audit_kind='catalog_primitive_license_and_initial_point_domain_not_proof_replay',
            plan=plan_pin, selector=plan['selector'], full_result=raw_pin(full_path),
            static_profile_id=STATIC_PROFILE_ID, static_profile_plan=STATIC_PROFILE_PIN,
            complete_licenses=raw_pin(license_path), dimensions=grammar.dimensions,
            primitive_license_checks=len(grammar.records),
            complete_initial_candidate_count=point_audit['complete_initial_candidate_count'],
            producer_diagnostic_trace=inputs['producer_diagnostics'],
            logical_accepted=True, initial_static_point_accepted=True, static_resource_qualified=False,
            dynamic_search_conformance=False, all_five_qualification=False,
            worker_seconds_before_final_receipt_serialization=time.perf_counter()-began,
            self_ru_maxrss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            self_ru_maxrss_platform=sys.platform, direct_children_peak_sum_bytes=0,
            all_direct_children_terminal_and_reaped=True,
            target_searches=0, point_certificates=0, proof_certificates=0,
            native_queries=0, RNG_draws=0, new_RL_training=False)
        write_json(receipt_path, receipt)
        print(canonical(dict(stage='replay', stage_completed=True, receipt=raw_pin(receipt_path),
            audit_kind=receipt['audit_kind'], static_resource_qualified=False)), flush=True)
    except BaseException as error:
        if not receipt_path.exists():
            write_json(receipt_path, dict(schema=RECEIPT_SCHEMA, stage='replay', stage_completed=False,
                status='UNKNOWN_preserved_no_retry', plan=plan_pin, selector=plan['selector'],
                error_type=type(error).__name__, error=str(error),
                worker_seconds_before_failure_receipt=time.perf_counter()-began,
                direct_children_peak_sum_bytes=0, all_direct_children_terminal_and_reaped=True,
                logical_accepted=False, initial_static_point_accepted=False,
                static_resource_qualified=False, dynamic_search_conformance=False,
                all_five_qualification=False, target_searches=0, point_certificates=0,
                proof_certificates=0, native_queries=0, RNG_draws=0, new_RL_training=False))
        raise


if __name__ == '__main__':
    main()
