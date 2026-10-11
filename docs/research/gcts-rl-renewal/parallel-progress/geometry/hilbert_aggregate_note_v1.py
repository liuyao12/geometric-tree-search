"""Author a static aggregate-cluster construction from frozen source data.

This is a design witness, not a search, experiment, authority adapter, logical
checker, or native computation. It does not import any project implementation.
"""
import copy
import gzip
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
INPUTS = {
    'docs/basic-tiling-algorithm.md': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9',
    '.gcts-active/hilbert-constant-certificates-20261011/certificate-v3.json.gz': '8f27361e9301e3fb651757f5c7d50d7625667dd64a6ff09884205d62c8e10141',
    '.gcts-active/hilbert-constant-certificates-20261011/audit-v3.json': '03a0cac547da1b3634ce0c1535098ca3883077ca46bad18e8bf8a68dc8eaca2f',
    '.gcts-active/hilbert-transport-catalog-20261011/catalog-v1.json.gz': '4109d05399941b4e0adcf2832430fd540ff4ba0fb696c1cb29e8ca30ab257c04',
    '.gcts-active/hilbert-transport-catalog-20261011/audit-v2.json': '13cdaa136ba4593cc16d95b68fbcdb525542ca0c94ea0bfec84d53fe3b04d21c',
    '.gcts-active/hilbert-chain-composition-plan-20261011/source-schemas-v1.json': 'f4555f17e5a6fb779f036b8d694d72b4ce155c3d3ff002656de544e668ce0d66',
    'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_native.json.gz': '20f4f2c607891dd37ac5acc32a91538a3e3bfc3e36bc7e09a439c09a27895877',
    'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_audit.json': 'ca1bcbd09e364ee869d3572fb5be786d3ae673566ce4f6fde0762897e1554187',
    'docs/research/gcts-rl-renewal/constant-transport-argument.html': 'bd0708aefb105de6ffac0e4a0b097b7d99ce295ed790535f52d0678efa76504b',
    'docs/research/gcts-rl-renewal/constant-transport-review.json': '43e2bb727943c7ba0f66b4d139e47b507228016c12392e17f500065fa16173f6',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path):
    raw = (ROOT / path).read_bytes()
    return json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)


def binding(path):
    p = ROOT / path
    return dict(path=path, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)


def main():
    began = time.perf_counter()
    for path, expected in INPUTS.items():
        assert binding(path)['sha256'] == expected, path
    cert = load('.gcts-active/hilbert-constant-certificates-20261011/certificate-v3.json.gz')
    catalog = load('.gcts-active/hilbert-transport-catalog-20261011/catalog-v1.json.gz')
    records = {r['definition']['name']: r for r in cert['records']}

    def selected(u, v):
        mapping = {k: ['fun', n, []] for k, n in zip(('A', 'B', 'C', 'u', 'v'), ('P', 'Q', 'R', u, v))}
        matches = [r for r in cert['records'] if r['family'] == 'searched-incidence-transport' and r['constant_map'] == mapping]
        assert len(matches) == 1
        return matches[0]

    first, second = selected('l', 'm'), selected('m', 'n')
    premises = [first['definition']['premises'][0], second['definition']['premises'][0], first['definition']['premises'][1]]
    context = dict(theory=cert['recipient_theory'], ordered_local_premises=premises)
    context_id = digest(context)
    commands = [dict(rule='assumption', index=i, formula=copy.deepcopy(a)) for i, a in enumerate(premises)]
    owners = {i: [] for i in range(3)}
    provenance = {i: [dict(kind='external_local_premise', index=i)] for i in range(3)}
    reusable = {}
    traces = []

    def expand(name, inputs, cluster, path):
        """Literal body traversal with assumption aliases and exact-body reuse.

        Reuse compares the entire instantiated primitive command including its
        ordered global references in the single unchanged recipient context.
        It does not compare formulas alone or invent a target-directed rule.
        """
        d = records[name]['definition']
        assert len(inputs) == len(d['premises'])
        assert [commands[i]['formula'] for i in inputs] == d['premises']
        local = []
        members = set()
        for i, source in enumerate(d['proof']):
            item = dict(cluster=cluster, source_definition=name, source_command=i, call_path=path)
            if source['rule'] == 'assumption':
                row = inputs[source['index']]
                assert commands[row]['formula'] == source['formula']
                item.update(kind='assumption_alias', premise_index=source['index'], global_row=row)
            elif source['rule'] == 'block':
                refs = [local[j] for j in source['inputs']]
                row, descendants = expand(source['name'], refs, cluster, path + [i])
                assert commands[row]['formula'] == source['formula']
                members.update(descendants)
                item.update(kind='expanded_block_call', ordered_inputs=refs, global_row=row)
            else:
                command = copy.deepcopy(source)
                assert source['rule'] in ('axiom', 'instantiate', 'eq_subst', 'mp')
                if source['rule'] == 'mp':
                    command['antecedent'] = local[source['antecedent']]
                    command['implication'] = local[source['implication']]
                key = canonical(command)
                reused = key in reusable
                if reused:
                    row = reusable[key]
                else:
                    row = len(commands)
                    commands.append(command)
                    reusable[key] = row
                    provenance[row] = []
                    owners[row] = []
                item.update(kind='reused_exact_primitive_placement' if reused else 'primitive_body_row', global_row=row)
                provenance[row].append(copy.deepcopy(item))
                if cluster not in owners[row]:
                    owners[row].append(cluster)
                members.add(row)
            local.append(row)
            traces.append(item)
        assert commands[local[-1]]['formula'] == d['conclusion']
        return local[-1], members

    out1, members1 = expand(first['definition']['name'], [0, 2], 'l-to-m', [])
    out2, members2 = expand(second['definition']['name'], [1, out1], 'm-to-n', [])
    assert out1 == 15 and out2 == 23 and len(commands) == 24
    assert members1 == set(range(3, 16))
    assert members2 == set(range(3, 8)) | set(range(16, 24))
    shared = sorted(members1 & members2)
    assert shared == list(range(3, 8))

    # Retain the prior 55 codes unchanged; new intermediate formula values are
    # a declared extension, not a mutation of the old reader/catalog.
    formulas = copy.deepcopy(catalog['formula_codes'])
    used = {canonical(a) for a in formulas}
    extras = {canonical(c['formula']): c['formula'] for c in commands if canonical(c['formula']) not in used}
    formulas.extend(copy.deepcopy(extras[k]) for k in sorted(extras))
    code = {canonical(a): i for i, a in enumerate(formulas)}
    assert len(code) == len(formulas)
    placements = []
    for row, command in enumerate(commands):
        refs = [command['antecedent'], command['implication']] if command['rule'] == 'mp' else []
        marks = {(1, row): code[canonical(command['formula'])]}
        for k, source in enumerate(refs):
            assert 0 <= source < row
            value = code[canonical(commands[source]['formula'])]
            assert (1, source) not in marks or marks[(1, source)] == value
            marks[(1, source)] = value
            marks[(2 + k, row)] = source - row
        if command['rule'] == 'mp':
            assert commands[refs[1]]['formula'] == ['imp', commands[refs[0]]['formula'], command['formula']]
        recipe = dict(command=command, context_id=context_id)
        placements.append(dict(id='primitive-' + digest(recipe) + '@' + str(row), row=row,
                               command=command, ordered_inputs=refs, t=[[0, row, 1]],
                               m=[[x, y, v] for (x, y), v in sorted(marks.items())],
                               cluster_owners=owners[row], source_provenance=provenance[row]))

    def aggregate(rows):
        marks = {}
        for row in sorted(rows):
            for x, y, value in placements[row]['m']:
                assert (x, y) not in marks or marks[(x, y)] == value
                marks[(x, y)] = value
        return dict(constituent_ids=[placements[row]['id'] for row in sorted(rows)],
                    distinct_rows=sorted(rows), t=[[0, row, 1] for row in sorted(rows)],
                    m=[[x, y, value] for (x, y), value in sorted(marks.items())])

    # Ordered high-level ports project onto real primitive reader ports. They
    # add no new point markings to the aggregate.
    ports1 = [dict(high_level_port=0, input_row=0, reader_row=12, primitive_input_port=0),
              dict(high_level_port=1, input_row=2, reader_row=15, primitive_input_port=0)]
    ports2 = [dict(high_level_port=0, input_row=1, reader_row=20, primitive_input_port=0),
              dict(high_level_port=1, input_row=15, reader_row=23, primitive_input_port=0)]
    for ports in (ports1, ports2):
        for p in ports:
            assert placements[p['reader_row']]['ordered_inputs'][p['primitive_input_port']] == p['input_row']
            p.update(formula_code=code[canonical(commands[p['input_row']]['formula'])],
                     receptor_mark_point=[1, p['input_row']],
                     reader_port_point=[2 + p['primitive_input_port'], p['reader_row']],
                     reader_port_value=p['input_row'] - p['reader_row'])

    dependencies = sorted(set(first['dependencies'] + second['dependencies']))
    bodies = [dict(name=n, family=records[n]['family'], definition_sha256=digest(records[n]['definition']),
                   body_sha256=records[n]['body_sha256'], constant_map=records[n]['constant_map'],
                   definition=records[n]['definition']) for n in dependencies + [first['definition']['name'], second['definition']['name']]]
    example = dict(status='authored_static_geometry_design_witness_not_discovered_theorem',
        input_bindings=[binding(p) for p in INPUTS],
        source_native_binding=cert['source_native_binding'],
        authority='No activation; source mapped bodies remain finite_structural_preservation_only.',
        context=context, context_id=context_id,
        sequent_latex=r' H(P,Q,l,m),\ H(P,Q,m,n),\ \operatorname{Incident}(R,l)\ \vdash\ \operatorname{Incident}(R,n)',
        formula_codes=formulas, original_code_prefix_count=55, new_intermediate_codes=len(formulas) - 55,
        source_bodies=bodies, expansion_trace=traces, primitive_placements=placements,
        clusters=[dict(name='l-to-m', source_definition=first['definition']['name'], ordered_inputs=[0, 2],
                       conclusion_row=out1, ordered_receptor_ports=ports1, **aggregate(members1)),
                  dict(name='m-to-n', source_definition=second['definition']['name'], ordered_inputs=[1, out1],
                       conclusion_row=out2, ordered_receptor_ports=ports2, **aggregate(members2))],
        composition=dict(shared_rows=shared, shared_constituent_ids=[placements[i]['id'] for i in shared],
                         first_output_is_second_input=True, second_incidence_port_uses_row=out1,
                         derived_aggregate=aggregate(members1 | members2),
                         first_cluster_units=13, second_cluster_units=13, naive_addition_units=26,
                         distinct_union_units=21, second_new_units_after_first=8,
                         full_with_premise_seeds=aggregate(set(range(24)))),
        declared_example_boundary=dict(rows=24, required=[[0, i] for i in range(24)],
            root_generations=[[0, i, 0] for i in range(24)], orientation='identity',
            transforms='vertical integer translations only; each embedded member supplies its own exact relative geometry',
            initially_selected_premise_placements=[placements[i]['id'] for i in range(3)],
            premise_seed_generation=0, fixed_target_m=[[1, 23, code[canonical(commands[23]['formula'])]]],
            future_complete_base_catalog_not_constructed_here=True,
            not_equivalent_to_old_five_unit_macro_row_boundary=True),
        claims=dict(all_t_values_are_exact_unit_integers=True, all_m_values_exact_integers=True,
            absent_is_not_zero=True, ordered_premise_multiplicity_preserved=True,
            internal_point_union_compatible=True, existing_experiments_rerun=0,
            native_queries=0, searches=0, point_models_executed=0,
            formal_native_compiler_correspondence='open', independent_audit='not performed in this design phase'),
        static_construction_seconds_before_write=time.perf_counter() - began)
    (OUT / 'example-v1.json').write_text(json.dumps(example, indent=2) + '\n')
    print(json.dumps(dict(status=example['status'], primitive_rows=len(commands),
        cluster_members=[len(members1), len(members2)], shared_rows=shared,
        derived_units=len(members1 | members2), added_formula_codes=example['new_intermediate_codes'],
        static_construction_seconds_before_write=example['static_construction_seconds_before_write'])))


if __name__ == '__main__':
    main()
