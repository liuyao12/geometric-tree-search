"""Third-party bounded source/pin/AST review; never imports a scientific source.

JSON reads are restricted to prospective/configuration plans and manifests.
All other evidence is hashed as raw bounded chunks, never decoded or inflated.
"""
import ast
import difflib
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
NEW = ROOT / '.gcts-active/receptor-matching-geometry-source-20261011'
OLD = ROOT / '.gcts-active/shared-symbolic-geometry-search-source-v2-20261011'
SECONDS = 120
BYTES = 134217728
CHUNK = 65536


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(CHUNK), b''):
            h.update(data)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def record(entry):
    return {k: entry[k] for k in ('path', 'sha256', 'bytes')}


def read_config(path):
    # Exact files called below are plans/manifests/contracts, never result data.
    return json.loads(Path(path).read_text())


def save(name, value):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def method(tree, class_name, name):
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def ast_record(node):
    return ast.dump(node, include_attributes=False)


class NormalizeHistoricalName(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == 'proved':
            return ast.copy_location(ast.Name(id='selected_outputs', ctx=node.ctx), node)
        return node


def readiness(order):
    loop = next(n for n in order.body if isinstance(n, ast.For))
    branch = next(n for n in loop.body if isinstance(n, ast.If))
    return branch


def source_location(path, needle):
    lines = path.read_text().splitlines()
    return {'path': str(path.relative_to(ROOT)), 'line': next(i for i, line in enumerate(lines, 1) if needle in line)}


def main():
    start = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('source-only review120s')))
    signal.alarm(SECONDS)
    review_plan_path = HERE / 'review-plan-v1.json'
    local_plan = read_config(review_plan_path)
    for entry in local_plan['inputs']:
        if pin(ROOT / entry['path']) != record(entry):
            raise ValueError('source-ready review input mismatch: ' + entry['path'])
    plan = read_config(NEW / 'search-plan-v1.json')
    old = read_config(OLD / 'search-plan-v1.json')
    manifest = read_config(NEW / 'source-manifest-v1.json')
    body_entry = plan['body_authority_adapter']['exact_accepted_original_full_plan']
    body = read_config(ROOT / body_entry['path'])
    declared = plan['sources'] + plan['inputs'] + plan['preserved_files'] + manifest['files']
    unique = {}
    for entry in declared:
        plain = record(entry)
        if entry['path'] in unique and unique[entry['path']] != plain:
            raise ValueError('conflicting pin metadata: ' + entry['path'])
        unique[entry['path']] = plain
    verified = []
    for path in sorted(unique):
        actual = pin(ROOT / path)
        if actual != unique[path]:
            raise ValueError('frozen producer/evidence mismatch: ' + path)
        verified.append(actual)
    hash_seconds = time.perf_counter() - start
    if (len(plan['sources']), len(plan['inputs']), len(plan['preserved_files'])) != (11, 135, 729):
        raise ValueError('declared source/input/preservation counts differ')
    if plan['inputs'][:118] != old['inputs'] or len(old['inputs']) != 118:
        raise ValueError('old118 prerequisite roles not exact prefix')
    if len({p['role'] for p in plan['inputs']}) != 135:
        raise ValueError('source roles collide')
    if len(body['inputs']) != 56 or len({p['path'] for p in body['inputs']}) != 56:
        raise ValueError('original56 body authority changed')
    for entry in body['inputs']:
        if pin(ROOT / entry['path']) != record(entry):
            raise ValueError('original56 body source pin mismatch')
    roles = {p['role']: record(p) for p in plan['inputs']}
    if roles['passed_full_lifecycle_producer_plan'] != record(body_entry):
        raise ValueError('body factory role no longer points to original56 plan')
    old_unique = len({p['path'] for p in old['inputs']})
    if old_unique != 104:
        raise ValueError('old broader alias count changed')
    expected_limits = {'owner_seconds': 180, 'supervisor_seconds': 175,
        'child_alarm_seconds': 170, 'host_bytes': 536870912, 'maximum_searches': 2,
        'each_attempts': 128, 'each_search_seconds': 20, 'each_trace_event_ceiling': 2000,
        'independent_audit_proposal_seconds': 180, 'independent_audit_proposal_bytes': 536870912}
    if plan['limits'] != expected_limits or plan['limits'] != old['limits']:
        raise ValueError('resource gates changed')
    specs = [{'id': 'fixed-forward-reference', 'mode': 'fixed-forward', 'attempts': 128,
        'seconds': 20, 'event_ceiling': 2000},
        {'id': 'fixed-forward-receptor', 'mode': 'fixed-forward-receptor', 'attempts': 128,
        'seconds': 20, 'event_ceiling': 2000}]
    if plan['observations'] != specs:
        raise ValueError('declared two-control schedule changed')
    if plan['model_epoch'] != old['model_epoch'] or plan['model_epoch'] != '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c':
        raise ValueError('model epoch changed')
    for name in ('shared_symbolic_forward_order_v1.py', 'shared_symbolic_bridge_decode_v1.py',
                 'shared_symbolic_search_run_v1.py', 'shared_symbolic_search_outer_v1.py'):
        if (NEW / name).read_bytes() != (OLD / name).read_bytes():
            raise ValueError('unchanged caller/helper differs: ' + name)
    before = (OLD / 'shared_symbolic_geometry_search_v1.py').read_text()
    after = (NEW / 'shared_symbolic_geometry_search_v1.py').read_text()
    replacements = [
        ('from shared_symbolic_forward_order_v1 import ForwardOrder\n',
         'from shared_symbolic_forward_order_v1 import ForwardOrder\nfrom receptor_literal_match_v1 import ReceptorOrder\n'),
        ("    if mode not in ('base', 'fixed-forward'):\n", "    if mode not in ('fixed-forward', 'fixed-forward-receptor'):\n"),
        ("    ordering = ForwardOrder(graph) if mode == 'fixed-forward' else None\n",
         "    ordering = ForwardOrder(graph) if mode == 'fixed-forward' else ReceptorOrder(graph)\n"),
        ("              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode)\n",
         "              complete_count=len(keys), selected_key=ordered[0].data(), mode=mode,\n              receptor_feature_trace=(copy.deepcopy(ordering.last_trace)\n                  if mode == 'fixed-forward-receptor' and decision.kind == 'branch' else None))\n"),
        ("            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,\n",
         "            'fixed_forward_metrics': dict(ordering.metrics) if ordering is not None else None,\n            'receptor_pattern_registry': copy.deepcopy(ordering.pattern_records)\n                if mode == 'fixed-forward-receptor' else None,\n")]
    expected = before
    for needle, replacement in replacements:
        if expected.count(needle) != 1:
            raise ValueError('caller diff boundary has changed')
        expected = expected.replace(needle, replacement)
    if after != expected:
        raise ValueError('unlisted scientific worker change')
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='frozen-search-v2/shared_symbolic_geometry_search_v1.py',
        tofile='receptor-v1/shared_symbolic_geometry_search_v1.py'))
    if diff != (NEW / 'worker-v2-to-receptor-v1.diff').read_text():
        raise ValueError('frozen exact worker diff not reproduced')
    with (HERE / 'independent-worker-diff-v1.diff').open('x') as stream:
        stream.write(diff)
    parsed = {p['path']: ast.parse((ROOT / p['path']).read_text(), filename=p['path']) for p in plan['sources']}
    forward_path = str((NEW / 'shared_symbolic_forward_order_v1.py').relative_to(ROOT))
    matcher_path = str((NEW / 'receptor_literal_match_v1.py').relative_to(ROOT))
    forward = method(parsed[forward_path], 'ForwardOrder', 'order')
    receptor = method(parsed[matcher_path], 'ReceptorOrder', 'order')
    normalized = NormalizeHistoricalName().visit(readiness(forward))
    if ast_record(normalized) != ast_record(readiness(receptor)):
        raise ValueError('original readiness conditional AST differs')
    calls = [n for n in ast.walk(receptor) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == 'append'
             and isinstance(n.func.value, ast.Name) and n.func.value.id == 'scored']
    if len(calls) != 1:
        raise ValueError('score append boundary changed')
    new_score = calls[0].args[0].elts[0]
    old_calls = [n for n in ast.walk(forward) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == 'append'
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == 'scored']
    old_score = old_calls[0].args[0].elts[0]
    projected = ast.Tuple(elts=[new_score.elts[0], *new_score.elts[2:]], ctx=ast.Load())
    if ast_record(projected) != ast_record(old_score) or ast_record(new_score.elts[1]) != ast_record(ast.parse("recipe_features[key.recipe]['bucket']", mode='eval').body):
        raise ValueError('readiness/bucket/original tie score changed')
    matcher_tree = parsed[matcher_path]
    scientific_names = sorted({n.id for n in ast.walk(matcher_tree) if isinstance(n, ast.Name)})
    forbidden_names = {'target', 'target_code', 'goal', 'theory', 'hypotheses', 'proof', 'proof_word', 'example'}
    if forbidden_names.intersection(scientific_names):
        raise ValueError('matcher accesses forbidden target/proof lookup name')
    forbidden_attrs = {'target', 'target_code', 'hypotheses', 'm', 'marks', 'domains', 'required', 'excluded'}
    attrs = {n.attr for n in ast.walk(matcher_tree) if isinstance(n, ast.Attribute)}
    if attrs.intersection(forbidden_attrs):
        raise ValueError('matcher directly accesses unavailable mark/target/legality fields')
    relevant_functions = ('pattern_from_guard', 'extract_pattern', 'literal_guard_match', 'evaluate_pattern')
    corpus_binding = roles['independent_cross_domain_corpus']
    evidence = {
        'source_only': True, 'source_ASTs_parsed_without_import': len(parsed),
        'scientific_imports': 0, 'actual_models_loaded': 0, 'actual_results_decoded': 0,
        'engine_calls': 0, 'ordering_graph_calls': 0, 'searches': 0, 'native_queries': 0,
        'training': 0, 'runtime_conformance_accepted': False,
        'complete_reference_copy_byte_identical': True,
        'decoder_supervisor_owner_copies_byte_identical': True,
        'exact_worker_changes': ['matcher import', 'declared two fixed modes', 'branch ranker dispatch',
            'new per-branch feature trace', 'new per-result pattern registry'],
        'old_readiness_AST_same_after_single_local_name_normalization': True,
        'new_score': 'old readiness tier; literal bucket; exact old size/canonical-witness/recipe/ordered-reference ties',
        'complete_base_permutation_guards_unchanged': True,
        'forced_singletons_bypass_ranker': True,
        'graph_scheduler': 'Frozen global degree zero, then global singleton, then earliest generation/count/row. Decisions remain exclusively graph-defined.',
        'rollback': 'Frozen paired checkpoint restoration. Only fully exhausted child excluded in restored parent. Unknown/trace cutoff restores root; no learned pruning.',
        'body_adapter': {'original_inputs': 56, 'original_unique_paths': 56, 'old_broad_inputs': 118,
            'old_broad_unique_paths': old_unique, 'old_aliases': 118 - old_unique,
            'new_broad_inputs': 135, 'old118_exact_prefix': True, 'all171_bodies_preserved': True,
            'factory_argument': 'exact role-pinned original56-input full-language plan, never broader phase list',
            'authored_example': 'Frozen family helper discards example before extracting all171 source bodies; empty descriptors make no body into a search proposal.'},
        'ranker_scope': 'Physically selected output constraints only, not marks on unoccupied rows. Selected MP outputs with pending source dependencies are structural constraints, not established facts.',
        'pure_matching_scope': 'Literal ordered supported syntax and distinct peeled prefix slots; nullary images only, compound literal constructors recurse; unsupported neutral; no target/theory/name/proof path lookup in executable matcher.',
        'new_pruning': False, 'new_marking': False, 'new_RL': False,
        'declaration_only_counts': {'formula_codes': 217, 'recipes': 229, 'rows': 24, 'source_bodies': 171},
        'resources': expected_limits,
        'activation': 'All actual workers require exact root plan activation; this source review does not create or authorize one.',
        'failure_scope': [
            'Retrospective sampled/kernel gates are not OS-enforced allocation limits; any actual overshoot remains unknown.',
            'Outer hard cleanup of an unresponsive supervisor can leave worker terminal state unconfirmed; receipt explicitly fails that gate. Root must inspect any such failure and own cleanup.',
            'Early pin/activation exceptions can precede the supervisor receipt; outer status remains unknown if it is missing.',
            'Source review verifies bindings and intended paths, not actual complete domains, forced/exhaustion/rollback events or mathematical/native acceptance.',
            'Actual complete trace/domain/pool/matcher/score/certificate replay remains a separately owned mandatory gate.'
        ],
        'relevant_sources': [source_location(NEW / 'shared_symbolic_geometry_search_v1.py', 'def automatic_search'),
            source_location(NEW / 'shared_symbolic_geometry_search_v1.py', 'body_plan ='),
            source_location(NEW / 'receptor_literal_match_v1.py', 'class ReceptorOrder'),
            source_location(ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py', 'def decision'),
            source_location(ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011/hilbert_cluster_lifecycle_v1.py', 'def frozen_family_authority')],
        'cross_domain_corpus_pin_only': corpus_binding,
        'matcher_functions_AST_sha256': {name: hashlib.sha256(ast_record(function(matcher_tree, name)).encode()).hexdigest() for name in relevant_functions}
    }
    save('source-checks-v1.json', evidence)
    save('verified-pin-set-v1.json', {'pins': verified, 'unique_paths': len(verified),
        'declared_observations': len(declared), 'total_unique_bytes': sum(p['bytes'] for p in verified),
        'role_aliases_retained': True, 'raw_hash_only_for_models_results_and_receipts': True})
    for entry in local_plan['inputs']:
        if pin(ROOT / entry['path']) != record(entry):
            raise ValueError('source-ready inputs changed during review')
    wall = time.perf_counter() - start
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    bounded = wall <= SECONDS and rss <= BYTES
    receipt = {'status': 'passed_bounded_third_source_only_receptor_search_review' if bounded else 'unknown_source_review_resource',
        'blockers': [], 'runtime_acceptance': False, 'scope': 'read/hash/AST only; no scientific source imports or actual data/model reads',
        'plan': pin(review_plan_path), 'producer_plan': pin(NEW / 'search-plan-v1.json'),
        'producer_freeze': pin(NEW / 'source-freeze-v1.json'), 'producer_manifest': pin(NEW / 'source-manifest-v1.json'),
        'source_checks': pin(HERE / 'source-checks-v1.json'), 'verified_pin_set': pin(HERE / 'verified-pin-set-v1.json'),
        'independent_worker_diff': pin(HERE / 'independent-worker-diff-v1.diff'),
        'hash_phase_seconds': hash_seconds, 'helper_seconds_before_final_receipt_write': wall,
        'helper_kernel_peak_bytes': rss, 'seconds_ceiling': SECONDS, 'host_ceiling_bytes': BYTES,
        'own_receipt_serialization_and_process_startup': 'outside pre-write helper clock; not a whole owned lifetime claim',
        'source_authoring_seconds': None, 'source_authoring_scope': 'unmeasured text authoring; no scientific work',
        'actual_models_loaded': 0, 'actual_results_decoded': 0, 'scientific_imports': 0,
        'engine_calls': 0, 'searches': 0, 'training': 0, 'native_queries': 0,
        'scientific_execution_authorized': False}
    save('source-review-v1.json', receipt)
    signal.alarm(0)
    print(json.dumps({'status': receipt['status'], 'unique_verified_paths': len(verified),
        'source_ASTs': len(parsed), 'seconds': wall, 'rss_bytes': rss,
        'review': pin(HERE / 'source-review-v1.json')}))


if __name__ == '__main__':
    main()
