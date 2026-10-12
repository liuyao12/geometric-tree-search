"""Prospective structural family features, no engine/model imports or dispatch.

Inputs are pinned graph/recipe/descriptor records supplied by a future audited
adapter. This is advice only: it neither establishes a proof nor tests legality.
Formula/recipe/descriptor codes serve exact matching and provenance, never
feature names or learned coefficients. Pending output marks are not facts.
"""
from __future__ import annotations

VERSION = 'family-graph-receptor-features-v1'
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
    'pending_by_frontier', 'completed_by_frontier', 'branch_degree_inverse',
)


def integer(value):
    if type(value) is not int:
        raise ValueError('literal integer, including assigned zero; bool rejected')
    return value


def key(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError('complete primitive key triple required')
    if not isinstance(value[2], (tuple, list)):
        raise ValueError('ordered source list required')
    return integer(value[0]), integer(value[1]), tuple(integer(r) for r in value[2])


def ratio(numerator, denominator):
    return numerator / max(1, denominator)


def available_rows(graph, recipes):
    """Read-only strict-prior dependency closure of physically selected keys.

    A zero-port witness is usable only under the future compiler's independently
    accepted primitive license/context. This routine does not admit it. Selected
    MP outputs with a missing earlier selected source remain pending constraints.
    Every repeated source port is checked in its declared order.
    """
    height = integer(graph['height'])
    selected = [key(k) for k in graph['selected_keys']]
    if len(set(selected)) != len(selected):
        raise ValueError('distinct selected placement identities required')
    by_row = {}
    for k in selected:
        i, row, refs = k
        if not 0 <= i < len(recipes) or not 0 <= row < height or row in by_row:
            raise ValueError('distinct legal row occupancy in supplied graph required')
        recipe = recipes[i]
        inputs = tuple(integer(c) for c in recipe['inputs'])
        integer(recipe['output'])
        if len(refs) != len(inputs) or any(not 0 <= r < row for r in refs):
            raise ValueError('exact strict-prior ordered primitive sources required')
        by_row[row] = (k, recipe)
    complete = {}
    for row in sorted(by_row):
        k, recipe = by_row[row]
        if all(r in complete and complete[r] == c for r, c in zip(k[2], recipe['inputs'])):
            complete[row] = recipe['output']
    roots = [key(k) for k in graph['initial_selected_keys']]
    if any(k not in selected for k in roots):
        raise ValueError('original selected roots retained')
    root_codes = {recipes[k[0]]['output'] for k in roots}
    distinct_nonroot = set(complete.values()) - root_codes
    return dict(complete=complete, selected_by_row=by_row,
                distinct_nonroot_codes=distinct_nonroot, root_codes=root_codes)


def feature_state(graph, recipes):
    height = integer(graph['height'])
    if height < 1 or len(graph['totals']) != height:
        raise ValueError('full declared row boundary required')
    totals = tuple(integer(v) for v in graph['totals'])
    if any(v not in (0, 1) for v in totals):
        raise ValueError('unit integer occupancy only in this interface')
    marks = {}
    for record in graph['marks']:
        if len(record) != 4:
            raise ValueError('every assigned point/value/refcount retained')
        x, y, value, references = (integer(v) for v in record)
        if references < 1 or (x, y) in marks:
            raise ValueError('literal distinct assigned marking and positive refcount')
        marks[x, y] = value
    availability = available_rows(graph, recipes)
    if any(totals[r] != 1 for r in availability['selected_by_row']):
        raise ValueError('selected key occupancy agrees with full graph')
    if sum(totals) != len(availability['selected_by_row']):
        raise ValueError('every occupied row has its exact selected key')
    return dict(height=height, totals=totals, marks=marks,
                frontier=sum(v == 0 for v in totals), **availability)


def feature_vector(descriptor, hint, decision, state, recipes, formulas):
    """Bounded name-free vector for NULL or one exact registered whole union.

    Only equality of formula codes, AST root constructors, point assignments and
    source/row relations are read. No whole target argument, semantic symbol,
    theory/lemma/recipe name, descriptor identity, proof position sequence or
    saved successful word is a feature. All aggregate markings are considered,
    including distant constraints and explicit assigned zero.
    """
    result = {name: 0.0 for name in FEATURE_NAMES}
    if descriptor is None:
        result['null'] = 1.0
        return result
    if hint['status'] not in ('ready', 'waiting'):
        raise ValueError('active menu includes all and only pending valid hints')
    members = [key(k) for k in descriptor['members']]
    if not members or len(set(members)) != len(members):
        raise ValueError('complete distinct whole-union members required')
    complete, selected = state['complete'], state['selected_by_row']
    pending = [k for k in members if k[1] not in selected]
    selected_members = [k for k in members if k[1] in selected]
    if any(selected[k[1]][0] != k for k in selected_members):
        raise ValueError('full key sharing, never formula-only row sharing')
    eligible = [key(k) for k in hint['eligible']]
    if any(k not in pending or k[1] != decision[1] for k in eligible):
        raise ValueError('eligible is a pending constituent at selected graph row')
    components = descriptor['components']
    ports = [port for component in components for port in component['ordered_receptor_ports']]
    bindings = [token for component in components for token in component['ordered_input_bindings']]
    if len(ports) != len(bindings):
        raise ValueError('ordered receptor multiplicity retained')
    receptor_rows, receptor_codes, heads = [], [], []
    for port in ports:
        row, code = integer(port['input_row']), integer(port['formula_code'])
        if not 0 <= row < state['height'] or not 0 <= code < len(formulas):
            raise ValueError('registered receptor row/formula required')
        receptor_rows.append(row); receptor_codes.append(code)
        heads.append(formulas[code][0])
    gaps = [row - r for _, row, refs in members for r in refs]
    if any(gap < 1 or gap >= state['height'] for gap in gaps):
        raise ValueError('declared strict-prior source offsets required')
    aggregate = descriptor['aggregate_m']
    assigned = remote = 0
    for x, y, value in aggregate:
        integer(x); integer(y); integer(value)
        if (x, y) in state['marks']:
            if state['marks'][x, y] != value:
                raise ValueError('retired aggregate conflict cannot enter the policy menu')
            assigned += 1
        if y not in {k[1] for k in members}:
            remote += 1
    h = state['height']; count = len(members); receptor_count = len(ports)
    complete_receptors = sum(r in complete and complete[r] == c
                            for r, c in zip(receptor_rows, receptor_codes))
    occurrence_count = integer(descriptor['component_member_occurrences'])
    shared_count = integer(descriptor['shared_member_count'])
    if occurrence_count < count or shared_count != occurrence_count - count:
        raise ValueError('exact distinct/occurrence sharing counts required')
    conclusions = [integer(component['conclusion_code']) for component in components]
    all_complete_codes = set(complete.values())
    mark_rows = [integer(m[1]) for m in aggregate]
    result.update(bias=1.0, ready=float(hint['status'] == 'ready'),
        waiting=float(hint['status'] == 'waiting'), pair=float(len(components) == 2),
        member_fraction=ratio(count, h), pending_member_fraction=ratio(len(pending), count),
        selected_member_fraction=ratio(len(selected_members), count),
        completed_selected_member_fraction=ratio(sum(k[1] in complete for k in selected_members), count),
        shared_occurrence_fraction=ratio(shared_count, occurrence_count),
        eligible_domain_fraction=ratio(len(eligible), integer(decision[2])),
        receptor_fraction=ratio(receptor_count, 2 * h),
        completed_receptor_fraction=ratio(complete_receptors, receptor_count),
        pending_receptor_fraction=ratio(receptor_count - complete_receptors, receptor_count),
        repeated_receptor_fraction=ratio(receptor_count - len(set(receptor_rows)), receptor_count),
        earlier_component_receptor_fraction=ratio(sum(t['kind'] == 'earlier_component_output' for t in bindings), receptor_count),
        source_gap_mean=ratio(sum(gaps), len(gaps) * h),
        source_gap_max=ratio(max(gaps, default=0), h),
        assigned_aggregate_mark_fraction=ratio(assigned, len(aggregate)),
        free_aggregate_mark_fraction=ratio(len(aggregate) - assigned, len(aggregate)),
        remote_aggregate_mark_fraction=ratio(remote, len(aggregate)),
        aggregate_span_fraction=ratio(max(mark_rows, default=0) - min(mark_rows, default=0), 2 * h),
        constrained_pending_output_fraction=ratio(sum((1, k[1]) in state['marks'] for k in pending), max(1, len(pending))),
        novel_component_output_fraction=ratio(sum(c not in all_complete_codes for c in conclusions), len(conclusions)),
        receptor_head_eq_fraction=ratio(heads.count('eq'), receptor_count),
        receptor_head_and_fraction=ratio(heads.count('and'), receptor_count),
        receptor_head_pred_fraction=ratio(heads.count('pred'), receptor_count),
        receptor_head_all_fraction=ratio(heads.count('all'), receptor_count),
        pending_by_frontier=ratio(len(pending), count) * ratio(state['frontier'], h),
        completed_by_frontier=ratio(complete_receptors, receptor_count) * ratio(state['frontier'], h),
        branch_degree_inverse=1.0 / (1.0 + integer(decision[2])))
    if any(not 0.0 <= v <= 1.0 for v in result.values()):
        raise ValueError('declared bounded feature contract')
    return result


def menu_features(graph, recipes, formulas, descriptors, hints, decision):
    """One complete feature pass; no graph legality/exhaustion inference here."""
    if decision[0] != 'branch':
        raise ValueError('policy may only advise after the global branch decision')
    state = feature_state(graph, recipes)
    records = {record['descriptor_id']: record for record in descriptors}
    if len(records) != len(descriptors):
        raise ValueError('immutable unique whole descriptor IDs')
    aligned = {record['descriptor_id']: hint for record, hint in zip(descriptors, hints)}
    if len(descriptors) != len(hints):
        raise ValueError('every whole hint retained')
    ids = sorted(['NULL'] + [identifier for identifier, hint in aligned.items()
                            if hint['status'] in ('ready', 'waiting')])
    if len(ids) != len(set(ids)):
        raise ValueError('NULL is a distinct explicit action')
    vectors = [feature_vector(None, None, decision, state, recipes, formulas) if identifier == 'NULL'
               else feature_vector(records[identifier], aligned[identifier], decision, state, recipes, formulas)
               for identifier in ids]
    return dict(action_ids=ids, feature_vectors=vectors,
                available_rows=sorted(state['complete']),
                maximum_fact_potential=len(state['distinct_nonroot_codes']),
                features_version=VERSION)
