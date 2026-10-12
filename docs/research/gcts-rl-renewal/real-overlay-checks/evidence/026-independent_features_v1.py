"""SOURCE ONLY independent structural feature reconstruction.

No producer feature/engine/controller/policy imports. Callers must first obtain
independent complete point-state and whole-body acceptance. A vector is advice,
never a proof or source-license admission. ROOT alone may activate a future run.
"""
import hashlib
import json
import math

FEATURE_NAMES = (
    'bias', 'null', 'ready', 'waiting', 'pair', 'member_fraction',
    'pending_member_fraction', 'selected_member_fraction',
    'completed_selected_member_fraction', 'shared_occurrence_fraction',
    'eligible_domain_fraction', 'receptor_fraction', 'completed_receptor_fraction',
    'pending_receptor_fraction', 'repeated_receptor_fraction',
    'earlier_component_receptor_fraction', 'source_gap_mean', 'source_gap_max',
    'assigned_aggregate_mark_fraction', 'free_aggregate_mark_fraction',
    'remote_aggregate_mark_fraction', 'aggregate_span_fraction',
    'constrained_pending_output_fraction', 'novel_component_output_fraction',
    'receptor_head_eq_fraction', 'receptor_head_and_fraction',
    'receptor_head_pred_fraction', 'receptor_head_all_fraction',
    'pending_by_frontier', 'completed_by_frontier', 'branch_degree_inverse')


def need(condition, label):
    if not condition:
        raise ValueError(label)


def integer(value):
    need(type(value) is int, 'literal integer; bool is not a point value')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def key(value):
    need(type(value) in (list, tuple) and len(value) == 3 and
         type(value[2]) in (list, tuple), 'complete primitive key and ordered sources')
    return integer(value[0]), integer(value[1]), tuple(integer(r) for r in value[2])


def same(actual, expected, label):
    need(canonical(actual) == canonical(expected), label)


def numeric(actual, expected, label):
    """Narrow floating arithmetic tolerance; all structural fields stay exact."""
    if type(expected) is float:
        need(type(actual) in (int, float) and math.isfinite(actual) and
             math.isclose(actual, expected, rel_tol=2e-12, abs_tol=2e-12), label)
    elif type(expected) is dict:
        need(type(actual) is dict and set(actual) == set(expected), label + ': fields')
        for name in expected:
            numeric(actual[name], expected[name], label + ':' + name)
    elif type(expected) in (list, tuple):
        need(type(actual) in (list, tuple) and len(actual) == len(expected), label + ': length')
        for index, (a, b) in enumerate(zip(actual, expected)):
            numeric(a, b, label + ':' + str(index))
    else:
        same(actual, expected, label)


def facts(graph, recipes, original_roots):
    """Strict prior closure from selected placements, never assigned m alone.

    License admission is a prior independent gate. Every ordered repeated source
    remains an occurrence. Fact potential is distinct per state, excluding the
    complete set of original root formula codes, even after rollback/repetition.
    """
    chosen = {}
    for raw in graph['order']:
        i, row, refs = key(raw)
        need(0 <= i < len(recipes) and 0 <= row < len(graph['totals']) and row not in chosen,
             'one physically selected exact placement per row')
        recipe = recipes[i]
        need(len(refs) == len(recipe['inputs']) and all(0 <= r < row for r in refs),
             'every ordered source is strict prior')
        need(graph['totals'][row] == 1, 'selected placement physically occupies the row')
        chosen[row] = (i, row, refs)
    need(sum(graph['totals']) == len(chosen), 'every occupied row has a selected key')
    original = [key(k) for k in original_roots]
    need(all(k in chosen.values() for k in original), 'initial roots retained in full identity')
    complete = {}
    for row, placement in sorted(chosen.items()):
        recipe = recipes[placement[0]]
        if all(source in complete and complete[source] == expected
               for source, expected in zip(placement[2], recipe['inputs'])):
            complete[row] = recipe['output']
    root_codes = {recipes[k[0]]['output'] for k in original}
    return chosen, complete, len(set(complete.values()).difference(root_codes))


def reconstruct_menu(graph, recipes, formulas, original_roots, records, hints, choice):
    """Reconstruct every action and vector from independently rederived inputs.

    No formula numeric value, name, saved proof word, target backward cone or
    producer feature field is an authority. Registry IDs supply sorting only.
    """
    need(choice[0] == 'branch' and integer(choice[2]) > 1, 'global branch before menu')
    height = len(graph['totals'])
    need(height > 0 and all(type(t) is int and t in (0, 1) for t in graph['totals']),
         'exact declared finite unit occupancy')
    chosen, complete, potential = facts(graph, recipes, original_roots)
    marks = {}
    for x, y, value, references in graph['marks']:
        integer(x); integer(y); integer(value); integer(references)
        need(references > 0 and (x, y) not in marks, 'distinct assigned point/refcount')
        marks[x, y] = value
    need(len(records) == len(hints), 'complete immutable descriptor/hint registry')
    by_id = {record['descriptor_id']: (record, hint) for record, hint in zip(records, hints)}
    need(len(by_id) == len(records) and 'NULL' not in by_id, 'distinct exact action identities')
    ids = sorted(['NULL'] + [name for name, (_, hint) in by_id.items()
                            if hint['status'] in ('ready', 'waiting')])
    vectors = []
    frontier = sum(t == 0 for t in graph['totals'])
    frac = lambda numerator, denominator: numerator / max(1, denominator)
    for name in ids:
        f = dict.fromkeys(FEATURE_NAMES, 0.0)
        if name == 'NULL':
            f['null'] = 1.0
            vectors.append(f)
            continue
        record, hint = by_id[name]
        members = [key(k) for k in record['members']]
        need(members and len(set(members)) == len(members), 'whole distinct union')
        pending = [k for k in members if k[1] not in chosen]
        selected = [k for k in members if k[1] in chosen]
        need(all(chosen[k[1]] == k for k in selected), 'share full key, never formula only')
        eligible = [key(k) for k in hint['eligible']]
        need(all(k in pending and k[1] == choice[1] for k in eligible),
             'eligible exact pending key at selected row')
        components = record['components']
        ports = [p for c in components for p in c['ordered_receptor_ports']]
        bindings = [b for c in components for b in c['ordered_input_bindings']]
        need(len(ports) == len(bindings), 'receptor/binding multiplicity')
        receptor_rows = [integer(p['input_row']) for p in ports]
        codes = [integer(p['formula_code']) for p in ports]
        need(all(0 <= r < height for r in receptor_rows) and
             all(0 <= c < len(formulas) for c in codes), 'receptor boundary and registry')
        completed = sum(complete.get(r) == c for r, c in zip(receptor_rows, codes))
        aggregate = record['aggregate_m']
        need(all((x, y) not in marks or marks[x, y] == value for x, y, value in aggregate),
             'conflicting aggregate is not a selectable hint')
        assigned = sum((x, y) in marks for x, y, _ in aggregate)
        remote = sum(y not in {k[1] for k in members} for _, y, _ in aggregate)
        mark_rows = [integer(y) for _, y, _ in aggregate]
        gaps = [row - source for _, row, refs in members for source in refs]
        need(all(0 < gap < height for gap in gaps), 'literal source offsets')
        occurrences = integer(record['component_member_occurrences'])
        shared = integer(record['shared_member_count'])
        need(occurrences >= len(members) and shared == occurrences - len(members),
             'distinct union and component occurrences kept separate')
        heads = [formulas[c][0] for c in codes]
        n, receptor_count = len(members), len(ports)
        f.update(bias=1.0, ready=float(hint['status'] == 'ready'),
            waiting=float(hint['status'] == 'waiting'), pair=float(len(components) == 2),
            member_fraction=frac(n, height), pending_member_fraction=frac(len(pending), n),
            selected_member_fraction=frac(len(selected), n),
            completed_selected_member_fraction=frac(sum(k[1] in complete for k in selected), n),
            shared_occurrence_fraction=frac(shared, occurrences),
            eligible_domain_fraction=frac(len(eligible), choice[2]),
            receptor_fraction=frac(receptor_count, 2 * height),
            completed_receptor_fraction=frac(completed, receptor_count),
            pending_receptor_fraction=frac(receptor_count - completed, receptor_count),
            repeated_receptor_fraction=frac(receptor_count - len(set(receptor_rows)), receptor_count),
            earlier_component_receptor_fraction=frac(sum(b['kind'] == 'earlier_component_output'
                                                        for b in bindings), receptor_count),
            source_gap_mean=frac(sum(gaps), len(gaps) * height),
            source_gap_max=frac(max(gaps, default=0), height),
            assigned_aggregate_mark_fraction=frac(assigned, len(aggregate)),
            free_aggregate_mark_fraction=frac(len(aggregate) - assigned, len(aggregate)),
            remote_aggregate_mark_fraction=frac(remote, len(aggregate)),
            aggregate_span_fraction=frac(max(mark_rows, default=0) - min(mark_rows, default=0), 2 * height),
            constrained_pending_output_fraction=frac(sum((1, k[1]) in marks for k in pending), len(pending)),
            novel_component_output_fraction=frac(sum(c['conclusion_code'] not in set(complete.values())
                                                    for c in components), len(components)),
            pending_by_frontier=frac(len(pending), n) * frac(frontier, height),
            completed_by_frontier=frac(completed, receptor_count) * frac(frontier, height),
            branch_degree_inverse=1.0 / (1.0 + choice[2]))
        for head in ('eq', 'and', 'pred', 'all'):
            f['receptor_head_' + head + '_fraction'] = frac(heads.count(head), receptor_count)
        need(all(type(v) is float and math.isfinite(v) and 0 <= v <= 1 for v in f.values()),
             'all 31 bounded structural coefficients')
        vectors.append(f)
    return dict(action_ids=ids, feature_vectors=vectors, available_rows=sorted(complete),
                maximum_fact_potential=potential, features_version='family-graph-receptor-features-v1')


def audit_preparation(prepared, graph, recipes, formulas, original_roots, records, hints,
                      choice, active_id, semantic_sha, pool_epoch, weight_sha, base_keys):
    """Exact mutated preparation rejection independent of a caller-supplied hash."""
    need(choice[0] in ('branch', 'forced'), 'global dead/complete cannot prepare advice')
    menu = (reconstruct_menu(graph, recipes, formulas, original_roots, records, hints, choice)
            if choice[0] == 'branch' and active_id is None else None)
    same(prepared['decision'], choice, 'current global decision')
    same(prepared['base'], base_keys, 'complete original primitive domain')
    same(prepared['menu'], menu, 'rederived exact canonical menu; changed features/IDs rejected')
    same(prepared['needs_one_draw'], menu is not None, 'draw requirement rederived from state')
    same(prepared['prepared_state_sha256'], semantic_sha, 'current complete paired state')
    same(prepared['pool_epoch'], pool_epoch, 'source-authorized whole registry epoch')
    same(prepared['weight_sha256'], weight_sha, 'frozen episode weights')
    return menu
