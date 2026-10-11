"""Freeze authored static expansion sources/inputs before production."""
import ast
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ROLES = {
    'master_contract': 'docs/basic-tiling-algorithm.md',
    'transport_certificate': '.gcts-active/hilbert-constant-certificates-20261011/certificate-v3.json.gz',
    'transport_audit': '.gcts-active/hilbert-constant-certificates-20261011/audit-v3.json',
    'row_catalog': '.gcts-active/hilbert-transport-catalog-20261011/catalog-v1.json.gz',
    'row_catalog_audit': '.gcts-active/hilbert-transport-catalog-20261011/audit-v2.json',
    'source_schemas': '.gcts-active/hilbert-chain-composition-plan-20261011/source-schemas-v1.json',
    'source_native_receipt': 'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_native.json.gz',
    'source_native_replay': 'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_audit.json',
    'source_argument': 'docs/research/gcts-rl-renewal/constant-transport-argument.html',
    'source_argument_review': 'docs/research/gcts-rl-renewal/constant-transport-review.json',
    'authored_design': '.gcts-active/hilbert-aggregate-design-20261011/design-v1.json',
    'authored_example': '.gcts-active/hilbert-aggregate-design-20261011/example-v1.json',
    'authored_design_generator': '.gcts-active/hilbert-aggregate-design-20261011/hilbert_aggregate_note_v1.py',
    'authored_design_manifest': '.gcts-active/hilbert-aggregate-design-20261011/manifest-v1.json',
}
EXPECTED = {
    'master_contract': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9',
    'transport_certificate': '8f27361e9301e3fb651757f5c7d50d7625667dd64a6ff09884205d62c8e10141',
    'transport_audit': '03a0cac547da1b3634ce0c1535098ca3883077ca46bad18e8bf8a68dc8eaca2f',
    'row_catalog': '4109d05399941b4e0adcf2832430fd540ff4ba0fb696c1cb29e8ca30ab257c04',
    'row_catalog_audit': '13cdaa136ba4593cc16d95b68fbcdb525542ca0c94ea0bfec84d53fe3b04d21c',
    'source_schemas': 'f4555f17e5a6fb779f036b8d694d72b4ce155c3d3ff002656de544e668ce0d66',
    'source_native_receipt': '20f4f2c607891dd37ac5acc32a91538a3e3bfc3e36bc7e09a439c09a27895877',
    'source_native_replay': 'ca1bcbd09e364ee869d3572fb5be786d3ae673566ce4f6fde0762897e1554187',
    'source_argument': 'bd0708aefb105de6ffac0e4a0b097b7d99ce295ed790535f52d0678efa76504b',
    'source_argument_review': '43e2bb727943c7ba0f66b4d139e47b507228016c12392e17f500065fa16173f6',
    'authored_design': '6493f5ff9be11daa2d856500af4210d76a483a4a74b6754a2ca58694ee1c4f28',
    'authored_example': '2d48019ec7df7afd76b099cefaac221ed20bb2edb8793b9cfc639415987cf105',
    'authored_design_generator': 'ce9551f7dcd512cb4343fb8f4e72ed26a44c703d9f2e484312b5ba4161f8af03',
    'authored_design_manifest': '47d0e1e0731bbc02c25024bd49c67f28c1398dcd5217fdc72175966561c16d5d',
}
MANIFESTS = [
    '.gcts-active/hilbert-promotion-family-20261011/export-v3.json',
    '.gcts-active/hilbert-expanded-control-20261011/export.json',
    '.gcts-active/hilbert-boundary-transfer-20261011/export.json',
    '.gcts-active/hilbert-chain-composition-plan-20261011/manifest-v1.json',
    '.gcts-active/hilbert-constant-certificates-20261011/export-v3.json',
    '.gcts-active/hilbert-transport-catalog-20261011/export-v2.json',
    '.gcts-active/hilbert-aggregate-design-20261011/manifest-v1.json',
]


def pin(path):
    p = ROOT / path
    data = p.read_bytes()
    return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def main():
    start = time.perf_counter()
    path = HERE / 'plan-v1.json'
    if path.exists():
        raise ValueError('plan already frozen')
    inputs = []
    for role, name in ROLES.items():
        binding = pin(name)
        assert binding['sha256'] == EXPECTED[role], 'unexpected input bytes ' + role
        inputs.append({'role': role, **binding})
    preserved = {}
    for name in MANIFESTS:
        p = ROOT / name
        d = json.loads(p.read_text())
        for binding in d.get('files', d.get('artifacts', [])):
            original = binding['path']
            if '/' not in original:
                original = 'docs/research/gcts-rl-renewal/' + original
            measured = pin(original)
            assert measured['sha256'] == binding['sha256'] and measured['bytes'] == binding['bytes'], original
            preserved[original] = measured
        preserved[name] = pin(name)
    # Full reviewed argument source/ledger are evidence, not imported algorithms.
    review = json.loads((ROOT / ROLES['source_argument_review']).read_text())
    argument_closure = []
    for binding in review['files']:
        measured = pin(binding['path'])
        assert measured == binding
        argument_closure.append(measured)
    sources = []
    for name in ('hilbert_aggregate_expand_v1.py', 'hilbert_aggregate_static_run_v1.py', 'hilbert_aggregate_freeze_v1.py'):
        ast.parse((HERE / name).read_text(), filename=name)
        sources.append(pin(str((HERE / name).relative_to(ROOT))))
    plan = {
        'version': 'hilbert-aggregate-static-plan-v1', 'status': 'frozen_before_production',
        'inputs': inputs, 'sources': sources, 'preserved_files': [preserved[k] for k in sorted(preserved)],
        'argument_source_closure': argument_closure,
        'research_question': 'Can every one of the 171 finite transported proof interfaces be expanded to a logically valid primitive row DAG with exact sum/union cluster data and projected ordered receptors?',
        'scope': 'Static expansion/model data and independent finite logical/point audit only. No native query, compiler execution, target search, policy, complete placement graph, engine adapter or authority activation.',
        'production_gate': {'seconds': 180, 'host_ceiling_bytes': 512 * 1024 * 1024,
                            'enforcement': 'fail-closed task-owned external RSS/time watchdog, child SIGALRM, conservative final kernel peak sum',
                            'OS_soft_limit_claim': 'none', 'overflow_or_unobserved_work': 'unknown; preserve terminal evidence and do not retry'},
        'independent_audit_gate': {'seconds': 180, 'host_ceiling_bytes': 512 * 1024 * 1024,
                                   'owner': '/root/external_prover_control', 'implementation': 'separate code; no producer import'},
        'predictions_not_measurements': {'definitions': 171, 'families': {'universal-uniqueness': [36, 10],
                                      'incidence-equality-transport': [27, 3], 'searched-incidence-transport': [108, 13]},
                                      'primitive_leaf_occurrences': 1845, 'zero_input_primitive_recipes': 82,
                                      'ordered_mp_recipes': 144, 'recipient_seed_recipes': 3,
                                      'total_recipes': 229, 'formula_registry_values': 217,
                                      'raw_alignment_counts': {'24': 1830264, '65': 38344085},
                                      'declared_authored_example': {'rows': 24, 'cluster_units': [13, 13],
                                                                  'shared_units': 5, 'union_derived_units': 21}},
        'finite_grammar': {'primitive_rules': ['axiom', 'instantiate', 'eq_subst', 'mp'],
                           'ordered_alias_rule': 'assumption', 'recursive_expansion_rule': 'block',
                           'term_images': 'closed zero-arity constants only, already frozen certificate',
                           'signature': {'functions': {'P': 0, 'Q': 0, 'R': 0, 'l': 0, 'm': 0, 'n': 0},
                                         'predicates': {'Point': 1, 'Line': 1, 'Incident': 2}},
                           'theory': 'Only guarded I.2 uniqueness, with exact source AST retained',
                           'formula_values': 'Preserve 71 authored codes exactly, append all new AST values injectively in canonical order',
                           'marking_support': 'conclusion at (1,row), ordered MP premise formulas at actual referenced rows, signed relative offsets at (2+k,row)',
                           'point_capacity': 'integer unit occupancy at (0,row), no fractional tolerance',
                           'transforms': 'identity orientation, vertical integer translations only',
                           'two_declared_models': [24, 65], 'all_required_roots_generation': 0,
                           'input_alias_occupancy': 0, 'duplicate_ports': 'retain their order and multiplicity even when references agree',
                           'macro_boundary_equivalence': False, '65_row_lift': 'conditional one-way control; not a proved bijection'},
        'identity_contract': {'named_definition_merging': False,
                              'primitive_recipe_aliasing': 'new model types have exact witness plus ordered formula interface identity; record all donor occurrence preimages',
                              'decorated_placement': ['exact recipe/witness/interface', 'orientation', 'relative port offsets', 'vertical transform',
                                                     'exact t/m', 'registry hash', 'recipient context', 'frozen authority epoch'],
                              'legacy_example_labels': 'check separately; do not upgrade missing historical authority fields'},
        'independent_obligations': ['reconstruct all 171 definitions and full dependency/alias DAG',
                                   'check guarded I.2, capture-free instantiation, equality templates and literal ordered MP at every leaf',
                                   'reconstruct all canonical aggregates and projected receptor occurrences',
                                   'reconstruct authored 24 row example including shared placements and ordered chained input',
                                   'check all complete decorated identity preimages and recipe occurrence aliases',
                                   'check finite grammar census without claiming complete graph enumeration',
                                   'adversarial noninjective map, duplicate premise/port, altered equality template, same formula/different reference and stale authority controls'],
        'remaining_correspondence': ['complete primitive placement universe and graph', 'complete aggregate embedding family domain',
                                    'reference scheduler/rollback/base fallback implementation', 'conditional padding lift',
                                    'formal native/compiler correspondence and fresh whole request acceptance'],
        'preparation_cost': {'freeze_input_hashing_and_syntax_seconds_before_plan_write': time.perf_counter() - start,
                             'source_authorship_wall': 'not separately instrumented; no execution credited',
                             'prior_native_admission_and_replay': 'preserved exact source receipts, not erased or relabeled fresh'},
    }
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'plan_pin': pin(str(path.relative_to(ROOT))), 'preserved_files': len(preserved),
                      'freeze_seconds_before_plan_write': plan['preparation_cost']['freeze_input_hashing_and_syntax_seconds_before_plan_write']}))


if __name__ == '__main__':
    main()
