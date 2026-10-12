"""SOURCE ONLY V2 bounded twelve-case leaf; V1 preserved unexecuted.

No author import/invocation, plan, runtime admission or actual output exists.
This worker exercises synthetic implementation interfaces only; it never calls
DFS, search, RNG, mining, certificate checking, native execution or learning.
ROOT explicitly permits the synthetic checkpoint wire exception below. That
checkpoint is NOT an actual final resource acceptance or production license.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PROGRESS = ROOT / '.gcts-active/compact-cluster-consumer-qualification-progress-20261012'
SCHEMA = 'ROOT-synthetic-twelve-case-consumer-worker-plan-v1'
LEXICAL_RUNTIME_PIN = {'path': '/Library/Developer/CommandLineTools/usr/bin/python3',
    'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 'bytes': 102352}
ROLES = {'point_core', 'compact_graph', 'compact_decoder', 'dynamic_graph_adapter',
    'dynamic_lifecycle_adapter', 'streamed_proposal', 'streamed_overlay', 'streamed_dfs',
    'features31', 'policy_math', 'eager_overlay', 'materializer', 'independent_reference',
    'qualification_harness', 'master', 'worker'}
INPUTS = {'fixture', 'helper_handoff', 'helper_contract', 'coverage_matrix',
    'prospective_qualification', 'author_metadata', 'independent_helper_source_review',
    'independent_streamed_source_review'}
RUNTIME_ROLES = ('point_core', 'compact_graph', 'compact_decoder',
                 'dynamic_graph_adapter', 'dynamic_lifecycle_adapter')
CONSUMER_ROLES = ('streamed_overlay', 'streamed_dfs', 'streamed_proposal', 'features31', 'policy_math')
FORBIDDEN_ACCEPTANCE = {'production_theorem_admission': False, 'proof_accepted': False,
    'native_accepted': False, 'new_RL_training': False, 'training_updates': 0,
    'target_searches': 0, 'proof_certificates': 0, 'scientific_RNG_draws': 0,
    'resource_accepted': False, 'complete_production_qualification': False}


def need(value, label):
    if not value: raise ValueError(label)


def pin(path):
    path = Path(path); h = hashlib.sha256(); size = 0; before = path.stat()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'immutable pinned bytes')
    return {'path': str(path), 'sha256': h.hexdigest(), 'bytes': size}


def verify(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact closed pin')
    path = Path(record['path'])
    need(path.is_absolute() and (str(path.resolve()) == str(path) or record == LEXICAL_RUNTIME_PIN),
         'canonical science pin or exact lexical runtime exception only')
    need(pin(path) == record, 'source/input/runtime closed bytes')


def load(role, record):
    verify(record)
    spec = importlib.util.spec_from_file_location('synthetic_consumer_' + role, record['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return module


def owner_record(record):
    """Preserve hash/size while resolving the owner's declared ROOT-relative path.

    The lexical runtime spelling is deliberate; no other noncanonical external
    pin is accepted. Resolving repository paths does not change their identity
    bytes and never silently converts the actual owner document on disk.
    """
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact owner closed pin')
    path = Path(record['path'])
    if record == LEXICAL_RUNTIME_PIN: return record
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    result = {'path': str(resolved), 'sha256': record['sha256'], 'bytes': record['bytes']}
    verify(result); return result


def main():
    began = time.perf_counter()
    need(len(sys.argv) == 4 and sys.argv[1] == 'ROOT-qualify-only', 'literal future owned CLI')
    plan_path = Path(sys.argv[2]); owner_path = Path(sys.argv[3])
    need(plan_path.is_absolute() and str(plan_path.resolve()) == str(plan_path)
         and owner_path.is_absolute() and str(owner_path.resolve()) == str(owner_path), 'canonical actual plan paths')
    plan_pin, owner_pin = pin(plan_path), pin(owner_path)
    plan = json.loads(plan_path.read_bytes()); owner = json.loads(owner_path.read_bytes())
    need(set(plan) == {'schema', 'ROOT_owned_once_only', 'output_directory', 'owner_plan_path',
        'sources', 'inputs', 'runtime', 'closure', 'source_review', 'limits', 'synthetic_checkpoint_exception'}, 'exact leaf plan')
    need(plan['schema'] == SCHEMA and plan['ROOT_owned_once_only'] is True, 'fresh once-only source version')
    need(plan['limits'] == {'whole_seconds': 60, 'peak_bytes': 536870912, 'caller_seconds': 90}, 'unchanged whole envelope')
    need(plan['synthetic_checkpoint_exception'] == 'ROOT-explicit-synthetic-checkpoint-wire-only-v1', 'explicit controlled contract exception')
    need(plan['owner_plan_path'] == str(owner_path) and plan_path.parent == PROGRESS
         and owner_path.parent == PROGRESS, 'ROOT-owned exact new progress namespace')
    out = Path(plan['output_directory'])
    need(out.is_absolute() and str(out.resolve()) == str(out) and out.parent == PROGRESS
         and not out.exists(), 'fresh exclusive direct child output')
    need(set(plan['sources']) == ROLES and set(plan['inputs']) == INPUTS, 'entire explicit role/input closure')
    need(plan['runtime'] == LEXICAL_RUNTIME_PIN
         and Path(sys.executable).resolve() == Path(plan['runtime']['path']).resolve(), 'declared exact interpreter')
    closed = {item['path']: item for item in plan['closure']}
    need(len(closed) == len(plan['closure']) and all(closed.get(item['path']) == item for item in
        [*plan['sources'].values(), *plan['inputs'].values(), plan['runtime'], plan['source_review']]), 'complete unique closed relation')
    for record in plan['closure']: verify(record)
    need(plan['sources']['worker']['path'] == str(Path(__file__).resolve()), 'exact executing worker source')
    need(owner.get('schema') == 'ROOT-guard-native-owned-plan-v1'
         and owner.get('stage') == 'replay' and owner.get('limits') == plan['limits'],
         'actual same-envelope enclosing owner')
    need(str((ROOT / owner['worker']).resolve()) == plan['sources']['worker']['path']
         and owner_record(owner['runtime_binary']) == plan['runtime']
         and owner.get('argv') == [plan['runtime']['path'], '-B', plan['sources']['worker']['path'],
                                  'ROOT-qualify-only', str(plan_path), str(owner_path)], 'owner actually binds exact invocation')
    normalized_owner_closure = [owner_record(item) for item in owner['closure']]
    need(plan_pin in normalized_owner_closure and plan['sources']['worker'] in normalized_owner_closure,
         'actual enclosing owner closure pins worker plan and source without hash cycle')
    need(str((ROOT / owner['worker_receipt']).resolve()) == str(out / 'qualification-result-v1.json'),
         'unchanged stage closer reads exact replay receipt')
    review = json.loads(Path(plan['source_review']['path']).read_bytes())
    need(review.get('schema') == 'ROOT-synthetic-consumer-worker-source-review-v1'
         and review.get('source_ready') is True and review.get('source_only') is True
         and review.get('scientific_calls') == 0 and review.get('sources') == plan['sources']
         and review.get('inputs') == plan['inputs']
         and review.get('synthetic_checkpoint_exception') == plan['synthetic_checkpoint_exception'], 'complete prior source review')
    handoff = json.loads(Path(plan['inputs']['helper_handoff']['path']).read_bytes())
    need(plan['inputs']['helper_handoff']['sha256'] == '928998c3a541195893240398816b900ac991133709c6458445cf172c2f83527d', 'frozen helper handoff')
    for record in handoff['payload_files']:
        need(closed.get(record['path']) == record, 'all frozen helper payloads in actual closure')
    for role, record in handoff['borrowed_sources'].items(): need(plan['sources'][role] == record, 'exact borrowed source role')
    helper_contract = json.loads(Path(plan['inputs']['helper_contract']['path']).read_bytes())
    for role, record in helper_contract['new_source_roles'].items(): need(plan['sources'][role] == record, 'exact helper source role')
    peer = json.loads(Path(plan['inputs']['independent_helper_source_review']['path']).read_bytes())
    need(peer.get('source_only') is True and peer.get('source_ready_for_ROOT_worker_design') is True
         and peer.get('activities', {}).get('scientific_functions') == 0, 'precise frozen independent helper review fields')
    streamed_review = json.loads(Path(plan['inputs']['independent_streamed_source_review']['path']).read_bytes())
    need(plan['inputs']['independent_streamed_source_review']['sha256'] == '1ab06ab3db36f57ef68b9b25e598f04ebbd37efc260ddf375e9800e81014c36d'
         and streamed_review.get('schema') == 'SOURCE-only-independent-person-streamed-consumer-review-v1'
         and streamed_review.get('source_only') is True and streamed_review.get('all_metadata_checks_pass') is True
         and streamed_review.get('no_execution', {}).get('scientific_source_functions') == 0,
         'precise actual independent streamed consumer source review')
    for role, section in (('streamed_overlay', 'overlay'), ('streamed_dfs', 'DFS'), ('streamed_proposal', 'proposal')):
        need(streamed_review['whole_source_comparisons'][section]['new'] == plan['sources'][role],
             'entire independently reviewed current consumer source pin')
    need(plan['sources']['master'] == handoff['master'] and plan['inputs']['fixture'] == handoff['fixture_pin'], 'master and full fixture')
    fixture = json.loads(Path(plan['inputs']['fixture']['path']).read_bytes())
    need(len(fixture['cases']) == 12 and [case['id'] for case in fixture['cases']] == helper_contract['case_ids'], 'all12 declared cases/order')
    source_bindings = [closed[path] for path in sorted(closed) if closed[path] != LEXICAL_RUNTIME_PIN]
    out.mkdir(); artifacts = []; events = []; case_results = []; assertions = []
    total_bytes = 0

    def peak():
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)

    def tick(label):
        need(time.perf_counter() - began < 55, 'whole leaf receipt reserve:' + label)
        need(peak() < 500 * 1024 * 1024, 'conservative SELF reserve; final owner separate')

    def save(path, value):
        nonlocal total_bytes
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()
        need(len(raw) <= 8 * 1024 * 1024 and total_bytes + len(raw) <= 64 * 1024 * 1024,
             'bounded complete mechanical receipts; never truncate')
        with Path(path).open('xb') as stream: stream.write(raw)
        total_bytes += len(raw); record = pin(path); artifacts.append(record)
        return record

    def event(kind, **data):
        tick(kind); need(len(events) < 128, 'complete bounded diagnostic event domain')
        value = {'sequence': len(events), 'kind': kind, 'worker_elapsed_seconds': time.perf_counter() - began,
                 'worker_pid': os.getpid(), **data, **FORBIDDEN_ACCEPTANCE}
        events.append(value)
        return save(out / ('event-%03d.json' % value['sequence']), value)

    try:
        modules = {role: load(role, plan['sources'][role]) for role in (
            'point_core', 'compact_graph', 'compact_decoder', 'dynamic_graph_adapter',
            'dynamic_lifecycle_adapter', 'streamed_proposal', 'streamed_overlay', 'features31',
            'policy_math', 'eager_overlay', 'materializer', 'independent_reference', 'qualification_harness')}
        core = modules['point_core']; ref = modules['independent_reference']; harness = modules['qualification_harness']
        features = modules['features31']; proposal = modules['streamed_proposal']
        runtime_sources = [{'role': role, **plan['sources'][role]} for role in RUNTIME_ROLES]
        Graph = modules['dynamic_graph_adapter'].make_dynamic_graph_type(core, modules['compact_graph'],
            modules['compact_decoder'], runtime_sources=runtime_sources)
        life = modules['dynamic_lifecycle_adapter'].make_lifecycle(core, Graph)
        weights = {name: 0.0 for name in features.FEATURE_NAMES}
        need(tuple(features.FEATURE_NAMES) == ref.FEATURES and len(weights) == 31, 'unchanged entire31 definitions')

        def checkpoint_binding(graph, audit_pin, label):
            header = graph.catalog.header
            need(header.get('synthetic_mechanism_control') is True
                 and header.get('production_theorem_admission') is False and header['split'] == 'mechanism-control',
                 'checkpoint wire NEVER permits non-synthetic header')
            raw = {'schema': 'synthetic-consumer-mechanical-resource-checkpoint-v1',
                'scope': 'synthetic_consumer_qualification_checkpoint_only',
                'worker_elapsed_seconds': time.perf_counter() - began, 'worker_pid': os.getpid(),
                'current_SELF_kernel_peak_bytes': peak(), 'limits': plan['limits'],
                'owner_plan_pin': owner_pin, 'worker_plan_pin': plan_pin, 'runtime_pin': plan['runtime'],
                'complete_entry_closure': plan['closure'], 'whole_catalog_binding': graph.compact_graph_binding(),
                'actual_independent_tiny_raw_relation_pin': audit_pin,
                'final_owned_disposition_pending': True, 'nominal_production_receipt_prerequisite_qualified': False,
                **FORBIDDEN_ACCEPTANCE}
            cp = save(out / (label + '-mechanical-checkpoint-v1.json'), raw)
            binding = graph.compact_graph_binding()
            return {'schema': 'ROOT-qualified-whole-compact-registry-binding-v1',
                'formula_registry_sha256': graph.registry_sha, 'formula_count': len(graph.formulas),
                'catalog_identity_sha256': graph.catalog_identity_sha, 'runtime_authority_sha256': graph.runtime_authority_sha,
                'catalog_header_pin': binding['catalog_header_pin'], 'complete_catalog_stream_pins': binding['complete_catalog_stream_pins'],
                'independent_complete_registry_audit_pin': audit_pin, 'ROOT_scoped_resource_disposition_pin': cp}

        def make_pool(graph, data, audit_pin, case_id, mode):
            tick('pool-' + mode)
            bodies, draft = harness.declare_mechanism_bodies(graph, life, inventory_mode=mode)
            body_relation = ref.audit_authored_mechanism_bodies(data, bodies, draft, mode)
            body_pin = save(out / (case_id + '-' + mode + '-whole-bodies-v1.json'),
                {'bodies': bodies, 'draft_projection': draft, 'independent_relation': body_relation, **FORBIDDEN_ACCEPTANCE})
            authority = life.BodyAuthority.build(graph, source_bindings + [audit_pin, body_pin], bodies)
            binding = checkpoint_binding(graph, audit_pin, case_id + '-' + mode)
            projection = copy.deepcopy(draft)
            projection['status'] = 'read_only_projection_with_bound_passed_independent_finite_audit'
            projection['complete_registry_binding'] = binding
            counters = {}; deadline = began + 55
            group_authority, groups, anchors, interfaces = harness.prepare_qualified_tiny_pool(graph, authority,
                projection, life, proposal, source_bindings + [audit_pin, body_pin], deadline, counters,
                qualified_registry_binding=binding)
            reference = ref.LiteralPointReference(data)
            complete = harness.compare_entire_tiny_pool(reference, interfaces, groups, counters, ref)
            pool_pin = save(out / (case_id + '-' + mode + '-whole-pool-v1.json'),
                {'groups': groups, 'anchors': anchors, 'interfaces': interfaces, 'counters': counters,
                 'independent_pool_observation': complete, 'mechanical_registry_binding': binding, **FORBIDDEN_ACCEPTANCE})
            tick('pool-closed-' + mode)
            return group_authority, groups, interfaces, counters, pool_pin

        feature_vectors = 0; scalar_feature_assertions = 0
        for case_index, case in enumerate(fixture['cases']):
            case_id = case['id']; event('case_begin', case_id=case_id)
            made = modules['materializer'].emit_catalog(fixture_pin=plan['inputs']['fixture'], instance_id=case_id,
                output_directory=str(out / (case_id + '-catalog-v1')), source_bindings=source_bindings)
            for record in [made['header_pin'], *made['stream_pins'].values()]:
                verify(record); artifacts.append(record); total_bytes += record['bytes']
            tick('whole-codec-' + case_id)
            data, relation = ref.audit_raw_catalog(fixture_pin=plan['inputs']['fixture'], case_id=case_id,
                header_pin=made['header_pin'], expected_source_bindings=source_bindings)
            audit_pin = save(out / (case_id + '-independent-raw-relation-v1.json'), relation)
            graph = Graph(header_pin=made['header_pin']); literal = ref.LiteralPointReference(data)
            authority, groups, interfaces, counters, pool_pin = make_pool(graph, data, audit_pin, case_id, 'ports-and-sharing')
            need(len(groups) == 7 and counters['single_types_visited'] == 3 and counters['pair_types_visited'] == 9,
                 'entire declared seven-group tiny mechanism grammar')
            control = life.Controller(graph, authority, groups)
            need(json.loads(control.root_rejected_text) == [] and len(control.descriptors) == len(groups), 'entire valid tiny registry')
            literal_life = ref.LiteralLifecycleReference(literal, groups)
            observation = harness.observe_qualified_case(graph=graph, literal=literal, controller=control,
                literal_lifecycle=literal_life, features31=features, reference_module=ref, admitted_interfaces=interfaces,
                complete_groups=groups, preparation_counters=counters)
            expected_kind = {0: 'dead', 1: 'forced', 2: 'branch'}[case['goal_axiom_count']]
            need(graph.decision().kind == expected_kind and (expected_kind == 'branch' or graph.decision().row == 23), 'far boundary decision')
            closed = {'case_id': case_id, 'case_declaration': copy.deepcopy(case),
                'independent_formula_registry': copy.deepcopy(data['formulas']),
                'raw_catalog': made, 'actual_raw_audit_pin': audit_pin,
                'whole_pool_pin': pool_pin, 'pristine': observation, 'changed_state_controls': [],
                'overlay_current_observations': [], 'ready_overlay_observations': [], **FORBIDDEN_ACCEPTANCE}
            if expected_kind == 'branch':
                feature_observation = observation['events'][2]['observation']
                feature_vectors += feature_observation['feature_vectors_observed']
                scalar_feature_assertions += 31 * feature_observation['feature_vectors_observed']
                base = literal.candidates(graph.decision().row)
                closed['changed_state_controls'].append(harness.compare_complete_order(graph, literal,
                    preferred_keys=tuple(reversed(base[:2]))))
                closed['changed_state_controls'].append(harness.require_stale_after_placement_and_rollback(graph))
                closed['changed_state_controls'].append(harness.compare_paired_transaction_roundtrip(controller=control,
                    literal_lifecycle=literal_life, features31=features, reference_module=ref, literal_key=base[0]))
                head_code, implication_code = graph.catalog.header['hypothesis_codes'][0], graph.catalog.header['hypothesis_codes'][2]
                mps = [index for index, recipe in enumerate(literal.recipes) if recipe['inputs'] == [head_code, implication_code]]
                need(len(mps) == 1, 'one genuine pending-reader mechanism rule')
                # Non-earliest low-level transaction control, NOT an executor or target proof route.
                closed['changed_state_controls'].append(harness.compare_paired_transaction_roundtrip(controller=control,
                    literal_lifecycle=literal_life, features31=features, reference_module=ref, literal_key=(mps[0], 4, (3, 2))))
                for transaction in closed['changed_state_controls']:
                    if transaction.get('schema') == 'synthetic-paired-transaction-roundtrip-v1':
                        for observed in transaction['events']:
                            count = observed['lifecycle_and_features']['feature_vectors_observed']
                            feature_vectors += count; scalar_feature_assertions += 31 * count
                records = [json.loads(d.text) for d in control.descriptors]
                single = next((d, hint.data()) for d, hint in zip(records, control.states)
                    if len(d['components']) == 1 and d['components'][0]['ordered_receptor_ports'])
                closed['scalar_only_repeated_port_control'] = harness.compare_repeated_port_feature_projection(graph=graph,
                    literal=literal, feature_module=features, reference_module=ref, admitted_single_descriptor=single[0], hint=single[1])
                feature_vectors += len(closed['scalar_only_repeated_port_control']['complete_menu']['feature_vectors'])
                scalar_feature_assertions += 31 * len(closed['scalar_only_repeated_port_control']['complete_menu']['feature_vectors'])
            if expected_kind in ('branch', 'forced'):
                # Two cold instances with identical source/catalog/pool identity; no double prepare.
                old_control = life.Controller(Graph(header_pin=made['header_pin']), authority, groups)
                new_control = life.Controller(Graph(header_pin=made['header_pin']), authority, groups)
                old = modules['eager_overlay'].LearnedFamilyOverlay(old_control, core, features, modules['policy_math'], weights)
                consumer_binding = {'schema': 'ROOT-whole-streamed-consumer-source-binding-v1',
                    'graph_binding_sha256': core.digest(new_control.graph.compact_graph_binding()),
                    'source_records': [{'role': role, **plan['sources'][role]} for role in CONSUMER_ROLES],
                    'ROOT_source_review_pin': plan['source_review'],
                    'independent_source_review_pin': plan['inputs']['independent_streamed_source_review']}
                new = modules['streamed_overlay'].LearnedFamilyOverlay(new_control, core, features,
                    modules['policy_math'], weights, consumer_binding=consumer_binding)
                closed['paired_overlay'] = harness.compare_paired_overlay_prepared(eager_overlay=old, streamed_overlay=new, literal_draw=0.0)
                for observer in (old_control, new_control):
                    lref = ref.LiteralPointReference(data); lh = ref.LiteralLifecycleReference(lref, groups); lh.resync()
                    point_seen = harness.compare_complete_graph(observer.graph, lref)
                    seen = harness.compare_lifecycle_and_features(observer, lh, features, ref)
                    which = old if observer is old_control else new
                    closed['overlay_current_observations'].append({'phase': 'root_NULL_or_forced',
                        'lane': 'eager' if observer is old_control else 'streamed',
                        'point_observation': point_seen, 'lifecycle_and_features': seen,
                        'whole_graph_state': observer.graph.semantic_state(),
                        'whole_hint_state': observer.semantic_state(), 'whole_overlay_state': which.semantic_state()})
                    feature_vectors += seen['feature_vectors_observed']; scalar_feature_assertions += 31 * seen['feature_vectors_observed']
                need(old.active_id == new.active_id is None, 'declared zero scalar NULL suppresses every preference; forced consumes no scalar')
                if expected_kind == 'branch':
                    old_cp, new_cp = old.checkpoint(), new.checkpoint()
                    ready_refs = []
                    try:
                        for overlay in (old, new):
                            chosen = overlay.graph.ordered_domain(overlay.graph.decision()).first()
                            # One scheduler-selected canonical mechanism placement; no tactic/target-search loop.
                            core.Executor(overlay.graph).step(chosen); overlay.control.resync(); overlay.after_resync()
                            lr = ref.LiteralPointReference(data); ll = ref.LiteralLifecycleReference(lr, groups)
                            ll.resync()  # Prior NULL preparation on the root copy.
                            lr.apply(chosen.data()); ll.resync()
                            point_seen = harness.compare_complete_graph(overlay.graph, lr)
                            seen = harness.compare_lifecycle_and_features(overlay.control, ll, features, ref)
                            closed['ready_overlay_observations'].append({'phase': 'canonical_step_ready_before_selection',
                                'lane': 'eager' if overlay is old else 'streamed', 'canonical_key': chosen.data(),
                                'point_observation': point_seen, 'lifecycle_and_features': seen,
                                'whole_graph_state': overlay.graph.semantic_state(),
                                'whole_hint_state': overlay.control.semantic_state(), 'whole_overlay_state': overlay.semantic_state()})
                            need(any(h['status'] == 'ready' and h['eligible'] for h in ll.hints), 'actual ready/eligible after canonical boundary transaction')
                            feature_vectors += seen['feature_vectors_observed']; scalar_feature_assertions += 31 * seen['feature_vectors_observed']
                            ready_refs.append(ll)
                        closed['ready_paired_overlay'] = harness.compare_paired_overlay_prepared(eager_overlay=old,
                            streamed_overlay=new, literal_draw=0.999999)
                        for overlay, ll in zip((old, new), ready_refs):
                            ll.resync(); seen = harness.compare_lifecycle_and_features(overlay.control, ll, features, ref)
                            closed['ready_overlay_observations'].append({'phase': 'ready_after_literal_scalar_selection',
                                'lane': 'eager' if overlay is old else 'streamed', 'lifecycle_and_features': seen,
                                'whole_graph_state': overlay.graph.semantic_state(),
                                'whole_hint_state': overlay.control.semantic_state(), 'whole_overlay_state': overlay.semantic_state()})
                            feature_vectors += seen['feature_vectors_observed']; scalar_feature_assertions += 31 * seen['feature_vectors_observed']
                        closed['overlay_whole_histories'] = {'eager': copy.deepcopy(old.history),
                            'streamed': copy.deepcopy(new.history), 'diagnostic_scalars': [0.0, 0.999999],
                            'scientific_RNG_draws': 0}
                    finally:
                        old.rollback(old_cp); new.rollback(new_cp)
                    for observer in (old_control, new_control):
                        lr = ref.LiteralPointReference(data); ll = ref.LiteralLifecycleReference(lr, groups); ll.resync()
                        point_seen = harness.compare_complete_graph(observer.graph, lr)
                        seen = harness.compare_lifecycle_and_features(observer, ll, features, ref)
                        which = old if observer is old_control else new
                        closed['overlay_current_observations'].append({'phase': 'paired_ready_rollback',
                            'lane': 'eager' if observer is old_control else 'streamed',
                            'point_observation': point_seen, 'lifecycle_and_features': seen,
                            'whole_graph_state': observer.graph.semantic_state(),
                            'whole_hint_state': observer.semantic_state(), 'whole_overlay_state': which.semantic_state()})
                        feature_vectors += seen['feature_vectors_observed']; scalar_feature_assertions += 31 * seen['feature_vectors_observed']
                    closed['paired_overlay_graph_hint_active_rollback'] = True
                else:
                    closed['overlay_whole_histories'] = {'eager': copy.deepcopy(old.history),
                        'streamed': copy.deepcopy(new.history), 'diagnostic_scalars': [], 'scientific_RNG_draws': 0}
            if case_index == 0:
                closed['capacity_controls'] = []
                for mode, count in (('capacity64', 64), ('overfull65', 65)):
                    ga, gs, ins, counts, pp = make_pool(graph, data, audit_pin, case_id, mode)
                    need(len(gs) == count and counts['single_types_visited'] == count
                         and counts['pair_types_visited'] == count * count, 'entire capacity inventory and all ordered pair types')
                    if count == 64:
                        cc = life.Controller(graph, ga, gs); lr = ref.LiteralPointReference(data)
                        ll = ref.LiteralLifecycleReference(lr, gs)
                        need(len(cc.descriptors) == 64 and json.loads(cc.root_rejected_text) == [], 'all64 accepted, no subset')
                        capacity = harness.compare_lifecycle_and_features(cc, ll, features, ref)
                        feature_vectors += capacity['feature_vectors_observed']; scalar_feature_assertions += 31 * capacity['feature_vectors_observed']
                        cp, lp = cc.checkpoint(), ll.checkpoint()
                        try:
                            chosen = graph.ordered_domain(graph.decision()).first()
                            core.Executor(graph).step(chosen); lr.apply(chosen.data()); cc.resync(); ll.resync()
                            point_seen = harness.compare_complete_graph(graph, lr)
                            seen = harness.compare_lifecycle_and_features(cc, ll, features, ref)
                            capacity['actual_ready_whole_state'] = {'canonical_key': chosen.data(),
                                'point_observation': point_seen, 'lifecycle_and_features': seen,
                                'whole_graph_state': graph.semantic_state(), 'whole_hint_state': cc.semantic_state()}
                            feature_vectors += seen['feature_vectors_observed']; scalar_feature_assertions += 31 * seen['feature_vectors_observed']
                            need(all(h['status'] == 'ready' and len(h['eligible']) == 1 for h in ll.hints), 'all64 actually compatible eligible hints')
                            order = cc.ordered(graph.decision()); expected = ll.ordered(lr.decision())
                            need([k.data() for k in order] == [ref.key_data(k) for k in expected], '64 compatible hints dedup physical preference only/full fallback')
                            capacity['all64_ready_whole_menu'] = seen
                            capacity['complete_order_descriptor'] = order.descriptor()
                        finally:
                            cc.rollback(cp); ll.rollback(lp)
                        capacity['paired_rollback_whole_state'] = {'whole_graph_state': graph.semantic_state(),
                            'whole_hint_state': cc.semantic_state(), 'literal_point_state': lr.state(),
                            'literal_hints': copy.deepcopy(ll.hints), 'literal_hint_revision': ll.revision}
                    else:
                        try: life.Controller(graph, ga, gs)
                        except ValueError as exc: refused = str(exc) == 'complete frozen64-descriptor registry required; never trim'
                        else: refused = False
                        need(refused, 'full65 refused before registry, never trimmed')
                        capacity = {'complete65_controller_refused': True, 'registered_subset': False}
                    closed['capacity_controls'].append({'mode': mode, 'whole_pool_pin': pp, 'observation': capacity, **FORBIDDEN_ACCEPTANCE})
            case_pin = save(out / (case_id + '-case-observation-v1.json'), closed)
            case_results.append({'case_id': case_id, 'observation_pin': case_pin, 'rows_checked': 24,
                                 'whole_raw_and_pool_checked': True, 'actual_feature_menu': expected_kind == 'branch'})
            assertions.append({'case_id': case_id, 'boundary_kind': expected_kind, 'whole24_pass': True})
            event('case_closed', case_id=case_id, completed_cases=len(case_results))
        need(len(case_results) == 12 and [item['case_id'] for item in case_results] == helper_contract['case_ids'], 'all12 closed without skipping')
        need(feature_vectors > 0 and scalar_feature_assertions == 31 * feature_vectors, 'all31 scalar comparisons actually made')
        matrix = json.loads(Path(plan['inputs']['coverage_matrix']['path']).read_bytes())
        for item in matrix['obligations']:
            item['actually_exercised'] = item['id'][:2] in {'01', '02', '03', '05', '07', '08', '09', '11', '12', '14', '15'}
            item['worker_exercise_status'] = ('observed_tiny_relation_only' if item['id'][:2] in {'01', '05', '09'} else
                'partial_mechanical_control_only' if item['actually_exercised'] else 'deferred_not_exercised')
            item['exercise_scope'] = 'Only completed helper controls listed in exact case records; full original obligation remains partial/deferred as source matrix states.'
            item['runtime_accepted'] = False
        for record in plan['closure']: verify(record)
        need(pin(plan_path) == plan_pin and pin(owner_path) == owner_pin, 'actual plans unchanged throughout phase')
        event('all_cases_closed', cases=12, scalar_feature_assertions=scalar_feature_assertions)
        evidence_pin = save(out / 'qualification-evidence-v1.json', {'schema': 'synthetic-twelve-case-consumer-evidence-v1',
            'cases': case_results, 'assertions': assertions, 'coverage_matrix': matrix,
            'feature_vectors_observed': feature_vectors, 'scalar_feature_assertions_executed': scalar_feature_assertions,
            'feature_counter_scope': 'Explicit independent31-menu comparator returns plus the separate repeated-port scalar reference only; redundant internal eager/streamed menu equality is excluded.',
            'event_records': copy.deepcopy(events), 'artifacts_before_evidence': copy.deepcopy(artifacts),
            'source_inputs_runtime_closure': plan['closure'], 'owner_plan_pin': owner_pin, 'worker_plan_pin': plan_pin,
            'nominal_production_receipt_prerequisite_qualified': False,
            'complete_original19_obligations_qualified': False, 'full_independent_DFS_replay_accepted': False,
            **FORBIDDEN_ACCEPTANCE})
        tick('receipt_reserve')
        result = {'schema': 'synthetic-twelve-case-consumer-worker-receipt-v1', 'stage': 'replay',
            'stage_completed': True, 'mechanical_checks_completed': True, 'completed_cases': 12,
            'evidence': evidence_pin, 'artifacts_before_receipt': copy.deepcopy(artifacts),
            'worker_elapsed_before_receipt_seconds': time.perf_counter() - began,
            'worker_SELF_peak_before_receipt_bytes': peak(), 'all_direct_children_terminal_and_reaped': True,
            'direct_children_peak_sum_bytes': 0, 'final_owned_disposition_pending': True,
            'source_inputs_runtime_closure': plan['closure'], 'owner_plan_pin': owner_pin, 'worker_plan_pin': plan_pin,
            'feature_vectors_observed': feature_vectors, 'scalar_feature_assertions_executed': scalar_feature_assertions,
            'full_independent_DFS_replay_accepted': False, 'complete_original19_obligations_qualified': False,
            **FORBIDDEN_ACCEPTANCE}
        save(out / 'qualification-result-v1.json', result)
        print(json.dumps({'stage_completed': True, 'completed_cases': 12, 'mechanical_only': True}), flush=True)
    except BaseException as exc:
        failure = {'schema': 'synthetic-twelve-case-consumer-worker-receipt-v1', 'stage': 'replay',
            'stage_completed': False, 'status': 'UNKNOWN_synthetic_consumer_qualification',
            'error': {'type': type(exc).__name__, 'message': str(exc)}, 'completed_cases': case_results,
            'completed_assertions': assertions, 'artifacts_before_failure': artifacts,
            'worker_elapsed_before_receipt_seconds': time.perf_counter() - began,
            'worker_SELF_peak_before_receipt_bytes': peak(), 'all_direct_children_terminal_and_reaped': True,
            'direct_children_peak_sum_bytes': 0, 'final_owned_disposition_pending': True,
            'complete_original19_obligations_qualified': False, **FORBIDDEN_ACCEPTANCE}
        if not (out / 'qualification-result-v1.json').exists(): save(out / 'qualification-result-v1.json', failure)
        raise


if __name__ == '__main__':
    main()
