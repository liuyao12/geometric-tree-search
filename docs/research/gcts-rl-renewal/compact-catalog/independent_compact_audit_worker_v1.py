"""SOURCE ONLY: ROOT-owned complete independent catalog/static leaf audit.

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
SOURCE = ROOT / '.gcts-active/cluster-transfer-compact-independent-source-20261012'
PROGRESS = ROOT / '.gcts-active/cluster-transfer-compact-progress-20261012'
PLAN_SCHEMA = 'ROOT-fresh-ground-compact-independent-audit-plan-v1'
EVIDENCE_SCHEMA = 'independent-complete-compact-catalog-static-evidence-v1'
RECEIPT_SCHEMA = 'independent-complete-compact-catalog-static-worker-receipt-v1'
METADATA_LIMIT = 64 * 1024 * 1024
SOURCE_PATHS = {
    'grammar': SOURCE / 'independent_compact_grammar_v1.py',
    'catalog_audit': SOURCE / 'independent_compact_catalog_audit_v1.py',
    'domains': SOURCE / 'independent_compact_domains_v1.py',
    'worker': SOURCE / 'independent_compact_audit_worker_v1.py',
    'logical_oracle': ROOT / '.gcts-active/cluster-transfer-independent-review-20261012/fresh_catalog_oracle_v1.py',
    'master': ROOT / 'docs/basic-tiling-algorithm.md'}
ORACLE_SHA = 'a9c960735f0f132933dd8e6c3aa44fa9c1b36efd44ecdcb24279929690dc773e'
FIXTURE_SHA = 'b17ba2cea0dd5d595e39c7c38f3d7cefce2d2c040ba1f3fd4a4aa10418bd99f8'
INPUT_KEYS = frozenset(('fixture', 'producer_plan', 'producer_receipt',
    'preparation_evidence', 'catalog', 'preparation_ROOT_decision'))


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
    spec = importlib.util.spec_from_file_location(name, path_for(pin))
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
            'source_review', 'limits', 'ROOT_owned_once_only'}
         and producer['schema'] == 'ROOT-fresh-ground-compact-preparation-plan-v1'
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
    decision = read_json(path_for(inputs['preparation_ROOT_decision']), expected_pin=inputs['preparation_ROOT_decision'])
    need(decision['schema'] == 'ROOT-fresh-catalog-stage-final-decision-v1'
         and decision['stage'] == 'preparation' and decision['ROOT_final_accepted'] is True
         and decision['status'] == 'accepted_complete_owned_stage'
         and type(decision['predicates']) is dict and len(decision['predicates']) == 14
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
    receipt = read_json(path_for(inputs['producer_receipt']), expected_pin=inputs['producer_receipt'])
    need(receipt['schema'] == 'fresh-ground-compact-preparation-worker-receipt-v1'
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


def main():
    began = time.perf_counter()
    need(len(sys.argv) == 3 and sys.argv[1] == 'ROOT-audit-only', 'ROOT-audit-only exact prospective audit plan')
    plan_path = Path(sys.argv[2]).resolve(); plan_pin = raw_pin(plan_path)
    plan = read_json(plan_path, expected_pin=plan_pin)
    need(type(plan) is dict and set(plan) == {'schema', 'selector', 'output_directory', 'inputs',
         'sources', 'source_review', 'limits', 'ROOT_owned_once_only'}
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
         'unchanged independent five-rule logical checker and original complete fixture')
    review = read_json(path_for(plan['source_review']), expected_pin=plan['source_review'])
    need(review['source_only'] is True and review['source_ready'] is True
         and review['scientific_acceptance'] is False, 'independent source readiness only')
    same(review['sources'], sources, 'closed exact independent audit source review')
    same(review['inputs'], {'fixture': inputs['fixture']}, 'same reviewed original complete fixture')
    output = Path(plan['output_directory']).resolve()
    need(output.parent == PROGRESS.resolve() and not output.exists(), 'fresh independent once-only output')
    producer, bindings, producer_receipt, decision = prerequisite(inputs, plan['selector'])
    pins.extend(bindings); pins.extend([decision['plan'], decision['actual_tool'], decision['owner'], decision['post_write']])
    for pin in pins:
        verify(pin)
    evidence = read_json(path_for(inputs['preparation_evidence']), compressed=True,
                         expected_pin=inputs['preparation_evidence'])
    need(evidence['schema'] == 'fresh-ground-compact-preparation-evidence-v1'
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
    output.mkdir(); receipt_path = output / 'audit-result-v1.json'
    try:
        old = load('independent_fresh_ground_logical_oracle_v1', sources['logical_oracle'])
        grammar_module = load('independent_complete_compact_grammar_v1', sources['grammar'])
        catalog_module = load('independent_complete_compact_catalog_audit_v1', sources['catalog_audit'])
        domains_module = load('independent_complete_compact_domains_v1', sources['domains'])
        fixture = read_json(path_for(inputs['fixture']), expected_pin=inputs['fixture'])
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
        full = dict(schema=EVIDENCE_SCHEMA, status='accepted_complete_semantics_pending_ROOT_resources',
            plan=plan_pin, inputs=inputs, sources=sources, source_review=plan['source_review'],
            instance_id=plan['selector'], preparation_ROOT_decision=inputs['preparation_ROOT_decision'],
            catalog=inputs['catalog'], catalog_streams=header['streams'],
            dimensions=grammar.dimensions, formula_registry_sha256=grammar.registry_sha,
            authority_epoch=grammar.authority['epoch'], context_id=grammar.context_id,
            declaration_binding=grammar.declaration_binding, logical_rule_counts=logical_counts,
            complete_licenses=raw_pin(license_path), primitive_license_checks=len(grammar.records),
            all_formulas_checked=True, all_licenses_checked=True, all_DAG_nodes_checked=True,
            original_canonical_order_and_preimages_checked=True,
            point_audit=point_audit, initial_graph_small_state=state,
            all_three_ordered_seed_identities_checked=True,
            source_body_count=0, complete_pool_count=0, logical_accepted=True,
            initial_static_point_accepted=True, static_resource_qualified=False,
            dynamic_search_conformance=False, all_five_qualification=False,
            target_searches=0, point_certificates=0, proof_certificates=0, native_queries=0,
            RNG_draws=0, new_RL_training=False,
            scope='Independent complete original declared finite catalog/primitive licensing and all24 '
                'initial point-domain streams. No producer compiler/decoder/graph imported. '
                'No proof discovery, dynamic Controller/DFS conformance, native or RL acceptance. '
                'ROOT must separately close unchanged60s/512MiB owned resources and90s caller scope.')
        full_path = output / 'complete-independent-static-evidence-v1.json.gz'
        write_json(full_path, full, compressed=True)
        for pin in pins:
            verify(pin)
        receipt = dict(schema=RECEIPT_SCHEMA, stage='replay', stage_completed=True,
            status='complete_catalog_static_semantic_audit_pending_ROOT_resources',
            audit_kind='catalog_primitive_license_and_initial_point_domain_not_proof_replay',
            plan=plan_pin, selector=plan['selector'], full_result=raw_pin(full_path),
            complete_licenses=raw_pin(license_path), dimensions=grammar.dimensions,
            primitive_license_checks=len(grammar.records),
            complete_initial_candidate_count=point_audit['complete_initial_candidate_count'],
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
