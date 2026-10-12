"""SOURCE ONLY: future ROOT-owned once-only fresh catalog preparation.

No author invocation is authorized. This worker builds the entire declared
catalog/implicit point graph and serializes full evidence; it performs no target
search, point certificate, native check, learner, RNG or child-process call.
Independent semantic/static and enclosing resource acceptance remain separate.
"""
import gzip
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRESS = ROOT / '.gcts-active/cluster-transfer-progress-20261012'
PLAN_SCHEMA = 'ROOT-fresh-ground-cluster-preparation-plan-v1'
CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def hash_pin(path, declared=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return {'path': declared if declared is not None else str(path),
            'sha256': h.hexdigest(), 'bytes': size}


def verify_pin(pin):
    if (set(pin) != {'path', 'sha256', 'bytes'} or type(pin['path']) is not str
            or type(pin['bytes']) is not int or pin['bytes'] < 0
            or type(pin['sha256']) is not str or len(pin['sha256']) != 64):
        raise ValueError('exact literal path/hash/length pin required')
    if hash_pin(pin['path'], pin['path']) != pin:
        raise ValueError('exact pinned source/input bytes changed: ' + pin['path'])


def path_for(pin):
    path = Path(pin['path'])
    return path if path.is_absolute() else ROOT / path


def load_source(name, pin):
    verify_pin(pin)
    spec = importlib.util.spec_from_file_location(name, path_for(pin))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def exclusive_json(path, data):
    with Path(path).open('xb') as stream:
        stream.write((canonical(data) + '\n').encode('utf8'))


def main():
    began = time.perf_counter()
    if len(sys.argv) != 3 or sys.argv[1] != 'ROOT-prepare-only':
        raise ValueError('ROOT-prepare-only <fresh exact pinned plan>')
    plan_path = Path(sys.argv[2]).resolve(); raw = plan_path.read_bytes(); plan = json.loads(raw)
    plan_pin = {'path': str(plan_path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    expected = {'schema', 'selector', 'output_directory', 'inputs', 'sources',
                'source_review', 'limits', 'ROOT_owned_once_only'}
    if (set(plan) != expected or plan['schema'] != PLAN_SCHEMA
            or plan['ROOT_owned_once_only'] is not True):
        raise ValueError('exact prospective ROOT plan grammar required')
    if set(plan['inputs']) != {'fixture'} or set(plan['sources']) != {'compiler', 'worker', 'point_core', 'master'}:
        raise ValueError('all four source roles and declaration fixture required')
    if plan['limits'] != {'whole_seconds': 60, 'peak_bytes': 536870912}:
        raise ValueError('unchanged bounded preparation envelope required')
    output = Path(plan['output_directory']).resolve()
    if output.parent != PROGRESS.resolve() or output.exists() or not plan_path.is_relative_to(PROGRESS.resolve()):
        raise ValueError('fresh ROOT-owned direct preparation child and plan namespace required')
    sources = plan['sources']; pins = [plan_pin, *plan['inputs'].values(), *sources.values(), plan['source_review']]
    if len({p['path'] for p in pins}) != len(pins):
        raise ValueError('unambiguous complete distinct declared source/input identities')
    for pin in pins:
        verify_pin(pin)
    if (path_for(sources['worker']).resolve() != Path(__file__).resolve()
            or sources['point_core']['sha256'] != CORE_SHA):
        raise ValueError('exact current worker and unchanged validated point core required')
    review = json.loads(path_for(plan['source_review']).read_bytes())
    if (review.get('source_only') is not True or review.get('source_ready') is not True
            or review.get('scientific_acceptance') is not False
            or review.get('sources') != sources or review.get('inputs') != plan['inputs']):
        raise ValueError('actual source-readiness review, not scientific acceptance, required')
    output.mkdir()
    receipt_path = output / 'preparation-result-v1.json'
    try:
        compiler = load_source('fresh_ground_declaration_compiler_v1', sources['compiler'])
        core = load_source('fresh_ground_unchanged_point_core_v2', sources['point_core'])
        fixture = json.loads(path_for(plan['inputs']['fixture']).read_bytes())
        stage = time.perf_counter()
        compiled = compiler.compile_declaration(fixture, plan['selector'], pins)
        compilation_seconds = time.perf_counter() - stage
        stage = time.perf_counter(); boundary = compiled['boundary']
        graph = core.PointGraph(height=24, formulas=compiled['formula_codes'], recipe_data=compiled['recipes'],
            context=compiled['context'], authority=compiled['authority'],
            fixed_marks=boundary['fixed_exterior_m'] + boundary['fixed_target_m'], roots=[0] * 24,
            seed_keys=tuple(core.Key(i, occurrence) for occurrence, i in enumerate(compiled['assumption_recipe_indices'])),
            source_bindings=compiled['source_bindings'])
        graph_setup_seconds = time.perf_counter() - stage
        if graph.context_id != compiled['context_id'] or graph.registry_sha != compiled['formula_registry_sha256']:
            raise ValueError('exact complete constructor relation mismatch')
        initial = graph.semantic_state()
        if len(graph.initial_selected) != 3 or graph.totals != [1, 1, 1] + [0] * 21:
            raise ValueError('only three declared assumption occurrence seeds placed')
        initial_candidates = sum(domain.count for domain in graph.domains)
        compiled['unchanged_model_epoch'] = graph.model_epoch
        projection = {'formula_codes': compiled['formula_codes'],
                      'formula_registry_sha256': compiled['formula_registry_sha256'],
                      'definitions': [], 'declared_source_body_count': 0,
                      'status': 'complete_empty_initial_library_pending_independent_qualification',
                      'native_accepted': False}
        result = {'schema': 'fresh-ground-catalog-preparation-evidence-v1',
                  'status': 'complete_declared_syntax_and_graph_pending_independent_gate',
                  'plan': plan_pin, 'inputs': plan['inputs'], 'sources': sources,
                  'instance_id': plan['selector'], 'compiled_context': compiled,
                  'initial_graph_semantic_state': initial,
                  'initial_selected_full_placements': [graph.decorate(k) for k in graph.initial_selected],
                  'dimensions': compiled['dimensions'], 'complete_initial_candidate_count': initial_candidates,
                  'projection': projection, 'bodies': [], 'groups': [], 'complete_pool_count': 0,
                  'pool_capacity': 64, 'pool_over_capacity': 'reject without trimming',
                  'compilation_seconds': compilation_seconds, 'graph_setup_seconds': graph_setup_seconds,
                  'target_searches': 0, 'point_certificates': 0, 'RNG_draws': 0, 'native_queries': 0,
                  'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False,
                  'all_five_qualification': False,
                  'scope': 'Entire fresh finite primitive universe and graph only; empty initial library. '
                           'No mined/advised clusters, theorem discovery or training acceptance.'}
        result_path = output / 'full-preparation-evidence-v1.json.gz'
        with result_path.open('xb') as stream:
            stream.write(gzip.compress((canonical(result) + '\n').encode('utf8'), mtime=0))
        for pin in pins:
            verify_pin(pin)
        elapsed = time.perf_counter() - began
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        receipt = {'schema': 'fresh-ground-preparation-worker-receipt-v1', 'stage': 'preparation',
                   'stage_completed': True, 'status': 'complete_pending_independent_and_ROOT_resource_gates',
                   'plan': plan_pin, 'selector': plan['selector'],
                   'full_result': hash_pin(result_path), 'dimensions': compiled['dimensions'],
                   'complete_initial_candidate_count': initial_candidates,
                   'complete_pool_count': 0, 'source_body_count': 0,
                   'worker_seconds_before_final_receipt_serialization': elapsed,
                   'self_ru_maxrss_raw': peak, 'self_ru_maxrss_platform': sys.platform,
                   'compilation_seconds': compilation_seconds, 'graph_setup_seconds': graph_setup_seconds,
                   'direct_children_peak_sum_bytes': 0, 'all_direct_children_terminal_and_reaped': True,
                   'target_searches': 0, 'point_certificates': 0, 'native_queries': 0, 'RNG_draws': 0,
                   'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False,
                   'all_five_qualification': False,
                   'resource_scope': 'No child processes; ROOT separately normalizes platform RSS and '
                                     'qualifies complete owned lifetime/serialization/reap and trusted terminal.'}
        exclusive_json(receipt_path, receipt)
        print(canonical({'stage': 'preparation', 'stage_completed': True, 'receipt': hash_pin(receipt_path),
                         'target_searches': 0, 'new_RL_training': False}))
    except Exception as error:
        if not receipt_path.exists():
            exclusive_json(receipt_path, {'schema': 'fresh-ground-preparation-worker-receipt-v1',
                'stage': 'preparation', 'stage_completed': False, 'status': 'UNKNOWN_preserved_no_retry',
                'plan': plan_pin, 'selector': plan['selector'],
                'error_type': type(error).__name__, 'error': str(error),
                'worker_seconds_before_failure_receipt': time.perf_counter() - began,
                'direct_children_peak_sum_bytes': 0, 'all_direct_children_terminal_and_reaped': True,
                'target_searches': 0, 'point_certificates': 0, 'native_queries': 0, 'RNG_draws': 0,
                'new_RL_training': False, 'logical_accepted': False, 'static_resource_qualified': False})
        raise


if __name__ == '__main__':
    main()
