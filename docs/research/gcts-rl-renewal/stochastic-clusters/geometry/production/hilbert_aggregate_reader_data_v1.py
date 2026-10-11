"""Read-only extraction of frozen static evidence into compact reader data."""
import gzip
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def load(path):
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open('rt')) as f:
        return json.load(f)


def save(path, value):
    if path.exists():
        raise ValueError('immutable reader extraction output exists')
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')


def ports(values):
    return [{'high_level_port': p['high_level_port'], 'input_node': p['input_node'], 'input_row': p['input_row'],
             'new_occupancy': p['new_occupancy'], 'adds_macro_offset_mark': p['adds_macro_offset_mark'],
             'readers': p['readers']} for p in values]


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('reader extraction ceiling')))
    signal.alarm(180)
    plan_path = HERE / 'reader-extraction-plan-v1.json'
    plan = load(plan_path)
    for p in plan['inputs'] + plan['sources']:
        assert pin(ROOT / p['path']) == {k: p[k] for k in ('path', 'sha256', 'bytes')}
    paths = {p['role']: ROOT / p['path'] for p in plan['inputs']}
    expanded = load(paths['expansions'])
    registry = expanded['formula_codes']
    codes = {canonical(f): i for i, f in enumerate(registry)}
    assert len(codes) == len(registry)
    definitions = []
    for source in expanded['records']:
        embedding = source['canonical_embedding']
        members = []
        for p in embedding['primitive_placements']:
            witness = {k: v for k, v in p['command'].items() if k not in ('formula', 'antecedent', 'implication')}
            if 'universal' in witness:
                witness['universal_formula_code'] = codes[canonical(witness.pop('universal'))]
            members.append({'row': p['row'], 'rule': p['command']['rule'], 'formula_code': codes[canonical(p['command']['formula'])],
                            'ordered_inputs': p['ordered_inputs'], 'command_witness': witness,
                            't': p['t'], 'm': p['m'], 'full_id': p['id'], 'recipe_id': p['recipe_id']})
        definitions.append({'name': source['definition_name'], 'family': source['family'],
                            'premise_ast': source['ordered_local_premises'], 'conclusion_ast': source['conclusion'],
                            'premise_codes': [codes[canonical(f)] for f in source['ordered_local_premises']],
                            'conclusion_code': codes[canonical(source['conclusion'])],
                            'primitive_member_count': len(members), 'canonical_boundary_rows': embedding['local_boundary_rows'],
                            'canonical_context_id': embedding['context_id'], 'canonical_conclusion_row': embedding['conclusion_row'],
                            'canonical_input_rows': [s['row'] for s in embedding['ordered_input_seeds']],
                            'canonical_seed_ids': [s['id'] for s in embedding['ordered_input_seeds']],
                            'ordered_receptor_ports': ports(embedding['ordered_receptor_ports']),
                            'primitive_members': members, 'aggregate_t': embedding['cluster_aggregate']['t'],
                            'aggregate_m': embedding['cluster_aggregate']['m'],
                            'assumption_alias_occurrences': len(source['assumption_aliases']),
                            'source_body_sha256': source['source_body_sha256'], 'mapped_body_sha256': source['mapped_body_sha256']})
    assert len(definitions) == 171
    counts = expanded['counts']
    authority = expanded['authority']
    registry_sha = expanded['formula_registry_sha256']
    del expanded
    example = load(paths['example'])
    ownership = {}
    for c in example['clusters']:
        for identifier in c['aggregate']['constituent_ids']:
            ownership.setdefault(identifier, []).append(c['name'])
    rows = [{'row': p['row'], 'command': p['command'], 'formula_ast': p['command']['formula'],
             'formula_code': codes[canonical(p['command']['formula'])], 'inputs': p['ordered_inputs'],
             't': p['t'], 'm': p['m'], 'full_id': p['id'], 'recipe_id': p['recipe_id'],
             'cluster_memberships': ownership.get(p['id'], []),
             'shared': len(ownership.get(p['id'], [])) > 1,
             'ordered_ports': p['ordered_ports']} for p in example['placements']]
    clusters = [{'name': c['name'], 'definition_name': c['definition_name'], 'ordered_inputs': c['ordered_inputs'],
                 'conclusion_row': c['conclusion_row'], 'ordered_receptor_ports': ports(c['ordered_receptor_ports']),
                 'aggregate': c['aggregate']} for c in example['clusters']]
    data = {'version': 'hilbert-aggregate-compact-reader-data-v1',
            'status': 'read_only_extraction_independent_finite_audit_pending_at_extraction',
            'extraction_plan_pin': pin(plan_path), 'input_pins': plan['inputs'], 'extraction_sources': plan['sources'],
            'authority_label': authority['label'], 'authority_epoch': authority['epoch'],
            'native_accepted': False, 'engine_activated': False,
            'formula_registry_sha256': registry_sha, 'formula_codes': registry,
            'counts_reported_by_producer': counts, 'definitions': definitions,
            'example': {'context': example['context'], 'context_id': example['context_id'], 'rows': rows,
                        'clusters': clusters, 'shared_rows': example['shared_rows'],
                        'first_units': example['first_units'], 'second_units': example['second_units'],
                        'distinct_derived_units': example['distinct_derived_units'], 'new_second_units': example['new_second_units'],
                        'derived_aggregate': example['derived_aggregate'],
                        'full_aggregate_with_three_seeds': example['full_aggregate_with_three_seeds'],
                        'authored_example_not_discovered_chained_proof': True},
            'scope': 'Lossless requested formula/row/port/point/identity-digest projection; long identity preimages and source chains remain in bound raw evidence. No logical admission or complete candidate/graph enumeration is performed by this reader extraction.',
            'notation': 'Render formula AST using established LaTeX renderer; integer formula values are marking data. Missing remains absent, assigned zero remains a value.',
            'native_queries': 0, 'target_searches': 0, 'new_policy': False}
    output = HERE / 'reader-data-v1.json'
    save(output, data)
    # Exact frozen input pins are checked again after extraction.
    for p in plan['inputs'] + plan['sources']:
        assert pin(ROOT / p['path']) == {k: p[k] for k in ('path', 'sha256', 'bytes')}
    elapsed = time.perf_counter() - started
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin':
        peak *= 1024
    receipt = {'status': 'compact_read_only_extraction_complete_pending_independent_audit',
               'plan_pin': pin(plan_path), 'output_pin': pin(output), 'definitions': len(definitions),
               'primitive_member_records': sum(len(d['primitive_members']) for d in definitions),
               'formula_values': len(registry), 'example_rows': len(rows),
               'before_receipt_seconds': elapsed, 'peak_rss_bytes': peak,
               'native_queries': 0, 'target_searches': 0, 'engine_or_authority_activation': False,
               'logical_audit_credit': False}
    save(HERE / 'reader-extraction-receipt-v1.json', receipt)
    signal.alarm(0)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
