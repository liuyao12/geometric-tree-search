"""Prospective ROOT-owned PURE synthetic fixture worker. No actual model loads.

Expected keys/ports/supports/type/binding census are explicit in the hand-written
corpus. The fixture-only decorated identity is reconstructed here from literal
recipe witnesses and ordered reference rows, independently of producer code.
Equal-port recipe is intentionally nonlogical. Passing these tests never grants
engine conformance, inference validity, lemma admission or proof acceptance.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

import family_binding_oracle_v1 as binding
import family_embedding_oracle_v1 as embedding


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def independent_fixture_identity(key, inventory, formulas, height):
    """Literal test-only independent point/identity function, no supplied IDs.

The context/authority below are synthetic constants. They are not substitutes
for the actual model's separately checked registry/authority/epoch preimages.
"""
    if type(key) is not tuple or len(key) != 3 or type(key[2]) is not tuple:
        raise ValueError('literal tuple key')
    index, row, refs = key
    if type(index) is not int or type(row) is not int or any(type(v) is not int for v in refs):
        raise ValueError('exact integers')
    if not 0 <= index < len(inventory) or not 0 <= row < height:
        raise ValueError('finite synthetic key')
    recipe = inventory[index]
    if len(refs) != len(recipe['inputs']) or any(not 0 <= v < row for v in refs):
        raise ValueError('exact ordered strict-prior ports')
    markings = {(1, row): recipe['output']}
    for port, (ref, code) in enumerate(zip(refs, recipe['inputs'])):
        if (1, ref) in markings and markings[(1, ref)] != code:
            raise ValueError('literal remote marking conflict')
        markings[(1, ref)] = code
        markings[(2 + port, row)] = ref - row
    t = [[0, row, 1]]
    m = [[p[0], p[1], code] for p, code in sorted(markings.items())]
    command = copy.deepcopy(recipe['witness'])
    if command['rule'] == 'mp':
        command['antecedent'], command['implication'] = refs
    elif refs:
        command['ordered_fixture_refs'] = list(refs)
    preimage = dict(schema='pure-fixture-primitive-identity-v1', recipe_index=index,
                    recipe_id=recipe['id'], recipe_witness=copy.deepcopy(recipe['witness']),
                    ordered_premise_formula_values=[copy.deepcopy(formulas[c]) for c in recipe['inputs']],
                    placed_row=row, ordered_reference_rows=list(refs),
                    context='synthetic-closed-context', authority_epoch='synthetic-fixed-authority',
                    registry_sha256=fingerprint(dict(inventory=inventory, formulas=formulas)),
                    orientation='identity', transform=dict(output_row=row, port_offsets=[v-row for v in refs]),
                    primitive_command=command, t=t, m=m)
    return dict(key=[index, row, list(refs)], id='aggregate-primitive-' + fingerprint(preimage),
                identity_preimage=preimage, command=command, t=t, m=m)


def fixture_interface(body, *, conclusion_member_index=None):
    """Literal test projection, never a production registry factory."""
    source = copy.deepcopy(body)
    source['source_body_sha256'] = 'synthetic-source-body-' + source['name']
    source['mapped_body_sha256'] = 'synthetic-mapped-body-' + source['name']
    index = len(source['primitive_members']) - 1 if conclusion_member_index is None else conclusion_member_index
    member = source['primitive_members'][index]
    projection = dict(name=source['name'], canonical_input_rows=source['canonical_input_rows'],
                      premise_codes=source['premise_codes'], primitive_members=copy.deepcopy(source['primitive_members']),
                      source_body_sha256=source['source_body_sha256'], mapped_body_sha256=source['mapped_body_sha256'],
                      canonical_conclusion_row=member['row'], conclusion_code=member['formula_code'],
                      fixture_extra_provenance='bound by whole projection hash')
    source['full_frozen_definition_sha256'] = fingerprint(projection)
    return source, projection


def run(corpus):
    inventory, formulas, height = corpus['inventory'], corpus['formula_values'], corpus['height']
    bodies, expected, receipts = corpus['bodies'], corpus['expected'], []
    original = fingerprint(corpus)
    identity = lambda key: independent_fixture_identity(key, inventory, formulas, height)

    def positive(name, action):
        value = action()
        receipts.append(dict(name=name, expected='pass', actual='pass', evidence_sha256=fingerprint(value)))
        return value

    def negative(name, action, contains=None):
        try:
            action()
        except ValueError as exc:
            if contains is not None and contains not in str(exc):
                raise AssertionError((name, 'wrong rejection', str(exc), contains))
            receipts.append(dict(name=name, expected='reject', actual='reject', reason=str(exc)))
            return
        raise AssertionError((name, 'unexpected acceptance'))

    def equal(value, reference):
        if value != reference:
            raise AssertionError(dict(actual=value, expected=reference))
        return value

    def project(which, inputs, rows, **changes):
        body = copy.deepcopy(bodies[which]); body.update(changes)
        return binding.project_binding(body, inputs, rows, inventory, height)

    def assert_fields(value, reference, fields):
        for field in fields:
            equal(value[field], reference[field])
        return value

    c = positive('conditional-explicit-keys-ports-offsets', lambda: assert_fields(project('conditional', [1], [3, 8]), expected['conditional_binding'],
        ('members', 'ordered_receptor_ports', 'receptor_only_assignments', 'conclusion_row', 'conclusion_formula_code')))
    u = positive('conditional-explicit-point-union-assigned-zero', lambda: assert_fields(binding.composed_union([c], identity), expected['conditional_binding'], ('aggregate_t', 'aggregate_m')))
    equal([v for v in u['aggregate_m'] if v[:2] == [1, 1]], [[1, 1, 0]])
    aliases = positive('equal-code-noninjective-aliases-ordered-readers', lambda: assert_fields(project('equal_aliases', [0, 0], [4]), expected['equal_alias_binding'],
        ('members', 'ordered_receptor_ports', 'receptor_only_assignments')))
    positive('equal-code-ports-point-union', lambda: assert_fields(binding.composed_union([aliases], identity), expected['equal_alias_binding'], ('aggregate_t', 'aggregate_m')))
    negative('unequal-code-alias-collision', lambda: project('different_aliases', [0, 0], [4]), 'noninjective receptor formula conflict')
    negative('reused-output-row', lambda: project('conditional', [1], [3, 3]), 'strictly ordered')
    negative('descending-member-rows', lambda: project('conditional', [1], [8, 3]), 'strictly ordered')
    negative('forward-receptor-read', lambda: project('conditional', [9], [3, 8]), 'strict-prior')
    negative('bool-receptor-row', lambda: project('conditional', [True], [3, 8]), 'exact integer')
    negative('bool-output-row', lambda: project('conditional', [1], [3, True]), 'exact integer')
    negative('bool-source-premise-code', lambda: project('conditional', [1], [3, 8], premise_codes=[False]), 'exact integer')
    wrong = copy.deepcopy(bodies['conditional']['primitive_members']); wrong[1]['formula_code'] = True
    negative('bool-source-output-code', lambda: project('conditional', [1], [3, 8], primitive_members=wrong), 'exact integer')
    wrong = copy.deepcopy(bodies['conditional']['primitive_members']); wrong[1]['ordered_inputs'] = [1, 0]
    negative('ordered-source-ports-swapped', lambda: project('conditional', [1], [3, 8], primitive_members=wrong), 'source body exact')
    wrong = copy.deepcopy(bodies['conditional']['primitive_members']); wrong[1]['ordered_inputs'] = [0, 2]
    negative('cyclic-source-reference', lambda: project('conditional', [1], [3, 8], primitive_members=wrong), 'source body exact')
    wrong = copy.deepcopy(bodies['conditional']['primitive_members']); wrong[0]['recipe_id'] = 'not-registered'
    negative('unknown-recipe', lambda: project('conditional', [1], [3, 8], primitive_members=wrong), 'original checked primitive palette')
    negative('receptor-output-mark-conflict', lambda: project('conditional', [3], [3, 8]), 'output collision')

    shared = positive('identical-body-shared-identities-provenance', lambda: binding.composed_union([c, copy.deepcopy(c)], identity))
    e = expected['identical_composition']
    equal(shared['distinct_members'], e['distinct_members']); equal(shared['aggregate_t'], e['aggregate_t'])
    equal(len(shared['occurrence_provenance']), e['occurrence_provenance_count'])
    equal([[a['component_occurrence'], a['member_occurrence']] for a in shared['occurrence_provenance']], e['component_member_occurrences'])
    for index in (0, 1):
        equal(shared['occurrence_provenance'][index]['full_identity'], shared['occurrence_provenance'][index+2]['full_identity'])
    positive('selected-all-shared-zero-additional-occupancy', lambda: equal(binding.composed_union([c, c], identity,
        [(0, 3, ()), (1, 8, (1, 3))])['additional_t'], e['additional_t_selected_all']))
    positive('receptor-no-new-t-seed', lambda: equal([v for v in u['aggregate_t'] if v[1] == 1], []))

    other = copy.deepcopy(bodies['conditional']); other['name'] = 'fixture-copy-identity'
    other['primitive_members'][0]['recipe_id'] = 'fixture-imp-copy'
    other_projected = binding.project_binding(other, [1], [3, 8], inventory, height)
    negative('same-formula-different-recipe-cannot-share-occupancy', lambda: binding.composed_union([c, other_projected], identity), 'overfill')
    alternative_refs = project('conditional', [0], [3, 8])
    positive('same-formula-different-ordered-refs-different-full-identity', lambda: equal(
        identity((1, 8, (0, 3)))['id'] == identity((1, 8, (1, 3)))['id'], False))
    negative('same-formula-different-refs-cannot-share-occupancy', lambda: binding.composed_union([c, alternative_refs], identity), 'overfill')
    unused = project('unused_receptor', [1], [9])
    negative('hidden-receptor-assigned-zero-conflict', lambda: binding.composed_union([c, unused], identity), 'receptor formula conflict')
    altered = copy.deepcopy(c); altered['receptor_only_assignments'] = [[1, 3, 0]]
    negative('receptor-primitive-remote-mark-conflict', lambda: binding.composed_union([altered], identity), 'aggregate marking conflict')

    def corrupt(kind):
        def callback(key):
            record = identity(key)
            if kind == 'hash': record['id'] = 'aggregate-primitive-' + '0'*64
            elif kind == 'key': record['key'][1] += 1
            elif kind == 'support': record['t'] = [[0, record['key'][1], 0]]
            elif kind == 'command': record['command'] = {'rule': 'not-the-preimage-command'}
            elif kind == 'bool-mark':
                record['m'] = copy.deepcopy(record['m']); record['m'][0][2] = False
                record['identity_preimage'] = copy.deepcopy(record['identity_preimage'])
                record['identity_preimage']['m'] = record['m']
                record['id'] = 'aggregate-primitive-' + fingerprint(record['identity_preimage'])
            return record
        return callback
    for kind, reason in [('hash', 'full identity hash'), ('key', 'preserves exact member key'), ('support', 'support binding'), ('command', 'logical command binding')]:
        negative('identity-mutant-' + kind, lambda kind=kind: binding.composed_union([c], corrupt(kind)), reason)
    negative('assigned-bool-mark-with-fresh-self-hash', lambda: binding.composed_union([c], corrupt('bool-mark')), 'exact integer')
    invocation = [0]
    def varying_authority(key):
        record = identity(key)
        if invocation[0] >= 2:
            record['identity_preimage']['authority_epoch'] = 'different-synthetic-epoch'
            record['id'] = 'aggregate-primitive-' + fingerprint(record['identity_preimage'])
        invocation[0] += 1
        return record
    negative('shared-key-different-full-authority-preimage', lambda: binding.composed_union([c, c], varying_authority), 'exact full decorated identity')
    def collapsing_identity(key):
        record = identity((0, 3, ()))
        record['key'] = [key[0], key[1], list(key[2])]
        return record
    negative('different-member-keys-cannot-share-claimed-id', lambda: binding.composed_union([c], collapsing_identity), 'different keys may not share')

    body, projection = fixture_interface(bodies['conditional'], conclusion_member_index=0)
    declared = positive('full-projection-nonlast-declared-interface', lambda: embedding.declared_interface(body, projection))
    positive('nonlast-conclusion-transport-no-default-leak', lambda: assert_fields(embedding.transported_interface(declared, [1], [3, 8], inventory, height),
        expected['nonlast_declared_conclusion'], ('conclusion_row', 'conclusion_formula_code', 'declared_conclusion_member_index')))
    changed = copy.deepcopy(projection); changed['fixture_extra_provenance'] = 'altered-hidden-provenance'
    negative('whole-projection-digest-not-just-conclusion', lambda: embedding.declared_interface(body, changed), 'complete declared projection binding')
    changed = copy.deepcopy(projection); changed['conclusion_code'] = 1
    changed_body = copy.deepcopy(body); changed_body['full_frozen_definition_sha256'] = fingerprint(changed)
    negative('fresh-self-hash-wrong-declared-output', lambda: embedding.declared_interface(changed_body, changed), 'declared member output')
    changed = copy.deepcopy(projection); changed['canonical_conclusion_row'] = 0
    changed_body = copy.deepcopy(body); changed_body['full_frozen_definition_sha256'] = fingerprint(changed)
    negative('fresh-self-hash-conclusion-is-receptor-not-member', lambda: embedding.declared_interface(changed_body, changed), 'one actual source member')
    changed = copy.deepcopy(projection); changed['conclusion_code'] = False
    changed_body = copy.deepcopy(body); changed_body['full_frozen_definition_sha256'] = fingerprint(changed)
    negative('bool-declared-conclusion-code', lambda: embedding.declared_interface(changed_body, changed), 'exact integer')
    changed = copy.deepcopy(projection); changed['primitive_members'][1]['ordered_inputs'] = [1, 0]
    changed_body = copy.deepcopy(body); changed_body['full_frozen_definition_sha256'] = fingerprint(changed)
    negative('fresh-self-hash-valid-member-change-not-registered-body', lambda: embedding.declared_interface(changed_body, changed), 'exact projection/body member')
    changed = copy.deepcopy(projection); changed['primitive_members'][0]['recipe_id'] = 'fixture-imp-copy'
    changed_body = copy.deepcopy(body); changed_body['full_frozen_definition_sha256'] = fingerprint(changed)
    negative('fresh-self-hash-alternative-valid-recipe-not-source-body', lambda: embedding.declared_interface(changed_body, changed), 'exact projection/body member')

    def interface(which):
        b, p = fixture_interface(bodies[which]); return embedding.declared_interface(b, p)
    conditional, return_p = interface('conditional'), interface('return_p')
    roots = [dict(key=[2, 1, []], formula_code=0, generation=0, selected=True)]
    positive('canonical-earliest-available-embedding', lambda: assert_fields(embedding.canonical_embedding(conditional, [1], inventory, height, [r['key'] for r in roots]),
        expected['canonical_conditional'], ('ordered_member_rows', 'members')))
    positive('canonical-exact-recipe-reference-reuse', lambda: assert_fields(embedding.canonical_embedding(conditional, [1], inventory, height, [[2, 1, []], [0, 3, []], [1, 8, [1, 3]]]),
        expected['canonical_reuse'], ('ordered_member_rows', 'members')))
    positive('canonical-earliest-of-two-exact-reuses', lambda: assert_fields(embedding.canonical_embedding(conditional, [1], inventory, height, [[2, 1, []], [0, 6, []], [0, 3, []]]),
        expected['canonical_earliest_reuse'], ('ordered_member_rows', 'members')))
    repeated_body = copy.deepcopy(bodies['closed_imp']); repeated_body['name'] = 'fixture-repeat-within-body'
    repeated_body['primitive_members'].append(dict(row=1, recipe_id='fixture-imp', formula_code=2, ordered_inputs=[]))
    rb, rp = fixture_interface(repeated_body); repeated_interface = embedding.declared_interface(rb, rp)
    positive('within-component-later-occurrence-not-erased', lambda: assert_fields(embedding.canonical_embedding(repeated_interface, [], inventory, height, [[0, 3, []]]),
        expected['canonical_occurrence_preserved'], ('ordered_member_rows', 'members')))
    negative('canonical-boundary-exhaustion', lambda: embedding.canonical_embedding(conditional, [1], inventory, 2, [[2, 1, []]]), 'row exhaustion')
    negative('same-formula-different-root-full-key-no-reuse', lambda: embedding.canonical_embedding(conditional, [1], inventory, 4,
        [[2, 1, []], [4, 0, []], [2, 2, []], [2, 3, []]]), 'row exhaustion')

    grammar = positive('complete-single-pair-binding-grammar', lambda: embedding.enumerate_binding_grammar([conditional, return_p], roots, inventory, height))
    ge = expected['grammar_conditional_return_p']
    assert_fields(grammar, ge, ('ordered_single_types', 'ordered_pair_types'))
    equal(len(grammar['bindings']), ge['binding_count'])
    equal([[r['kind'], r['interface_indices']] for r in grammar['bindings']], ge['binding_kind_indices'])
    single, pair = grammar['bindings']; equal(single['embedding_accepted'], True); equal(pair['embedding_accepted'], True)
    equal(single['components'][0]['members'], ge['single_members']); equal(pair['second_inputs'], ge['pair_second_inputs'])
    equal(pair['components'][1]['members'], ge['pair_second_members']); equal(pair['components'][1]['conclusion_row'], ge['pair_second_conclusion_row'])
    union = binding.composed_union(pair['components'], identity, [(2, 1, ())])
    equal(union['aggregate_t'], ge['pair_joint_t']); equal(union['additional_t'], ge['pair_additional_t_selected_root'])
    equal(union['proof_accepted'], False); equal(union['native_accepted'], False)

    equal_roots = [dict(key=[2, 0, []], formula_code=0, generation=0, selected=True), dict(key=[2, 1, []], formula_code=0, generation=0, selected=True)]
    repeated = positive('all-repeated-ordered-Cartesian-bindings', lambda: embedding.enumerate_binding_grammar([interface('equal_aliases')], equal_roots, inventory, height))
    re = expected['grammar_repeated_roots']; assert_fields(repeated, re, ('ordered_single_types', 'ordered_pair_types'))
    equal(len(repeated['bindings']), re['binding_count'])
    equal([[b['row'] for b in r['first_inputs']] for r in repeated['bindings']], re['ordered_input_rows'])
    equal([len(r['first_inputs']) for r in repeated['bindings']], [2, 2, 2, 2])
    for record in repeated['bindings']:
        equal(len(record['components'][0]['ordered_receptor_ports']), 2)
    positive('synthetic-root-full-key-order-normalization', lambda: equal(
        embedding.enumerate_binding_grammar([interface('equal_aliases')], list(reversed(equal_roots)), inventory, height), repeated))
    closed = positive('empty-Cartesian-product-no-unlinked-pair', lambda: embedding.enumerate_binding_grammar([interface('closed_imp')], [], inventory, height))
    ce = expected['grammar_closed_body']; assert_fields(closed, ce, ('ordered_single_types', 'ordered_pair_types'))
    equal(len(closed['bindings']), ce['binding_count']); equal(closed['bindings'][0]['components'][0]['members'], ce['member_keys'])
    negative('unselected-marked-row-not-anchor', lambda: embedding.enumerate_binding_grammar([conditional],
        [dict(key=[2, 1, []], formula_code=0, generation=0, selected=False)], inventory, height), 'selected root only')
    negative('bool-anchor-generation', lambda: embedding.enumerate_binding_grammar([conditional],
        [dict(key=[2, 1, []], formula_code=0, generation=False, selected=True)], inventory, height), 'exact integer')
    negative('root-code-differs-from-full-key', lambda: embedding.enumerate_binding_grammar([conditional],
        [dict(key=[2, 1, []], formula_code=1, generation=0, selected=True)], inventory, height), 'formula identity')
    equal(fingerprint(corpus), original)
    return dict(status='passed_pure_synthetic_family_binding_controls', controls=receipts,
                control_count=len(receipts), positive_count=sum(r['expected']=='pass' for r in receipts),
                negative_count=sum(r['expected']=='reject' for r in receipts),
                corpus_unchanged_sha256=original, fixed_type_binding_census=dict(two_interface_single_types=2,
                two_interface_pair_types=4, two_interface_bindings=2, repeated_equal_port_bindings=4, zero_input_bindings=1),
                all_expected_values_hand_declared=True, fixture_identity_scope='independently reconstructed synthetic full witnesses/ordered refs/t/m/context/authority only',
                root_ordering_scope='Synthetic oracle sorts full (recipe,row,refs) keys. It does not assert equality of producer graph.order indices; actual correspondence must preserve producer insertion order or independently normalize tokens by full keys.',
                engine_conformance=False, logical_proof_accepted=False, actual_model_loaded=False,
                producer_imports=False, scheduler_executed=False, native_queries=0, training_updates=0,
                scope=corpus['scope'])


def main():
    plan = json.loads(Path(sys.argv[1]).read_text())
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('fixture child deadline')))
    signal.alarm(plan['limits']['child_seconds'])
    for pin in plan['sources'] + plan['inputs'] + plan['preserved']:
        data = Path(pin['path']).read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('frozen pin mismatch: ' + pin['path'])
    start = time.monotonic()
    result = run(json.loads(Path(plan['corpus_path']).read_text()))
    result['fixture_seconds_including_result_preparation'] = time.monotonic() - start
    result['kernel_peak_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['plan_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
    target = Path(plan['outputs']['result'])
    with target.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')
    signal.alarm(0)


if __name__ == '__main__':
    main()
