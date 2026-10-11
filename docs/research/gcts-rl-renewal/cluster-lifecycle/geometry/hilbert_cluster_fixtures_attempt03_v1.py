"""Authored synthetic lifecycle probes only. No actual geometry model is loaded.

The raw iterator constructs t/m directly from recipe witnesses and offsets, not
through the production graph's factors, candidates, point_data or decorate.
"""
import argparse
import copy
import itertools
import json
import signal
import time
from pathlib import Path
import hilbert_cluster_lifecycle_v1 as life

core = life.core
HERE = Path(__file__).resolve().parent
EXPECTED_OUTPUT = HERE / 'attempt-03'
P, Q, R = ['pred', 'P', []], ['pred', 'Q', []], ['pred', 'R', []]
IMP = ['imp', P, Q]
FORMULAS = [P, Q, IMP, R]


def recipe(name, formula, premises=(), rule='fixture_zero'):
    return {'id': 'synthetic-' + name,
            'primitive_witness': {'rule': rule, 'formula': copy.deepcopy(formula), 'fixture_name': name},
            'ordered_premise_formulas': copy.deepcopy(list(premises))}

RECIPES = [recipe('p-first', P), recipe('q', Q), recipe('imp', IMP), recipe('p-second', P),
           recipe('literal-mp', Q, [P, IMP], 'mp'),
           recipe('equal-ordered-port-fixture', Q, [P, P], 'opaque_pair')]


def graph(height=3, *, recipes=RECIPES, marks=(), roots=None):
    authority = {'label': 'synthetic_point_fixture_not_logic', 'activated': False, 'native_accepted': False}
    authority['epoch'] = core.digest(authority)
    return core.PointGraph(height=height, formulas=FORMULAS, recipe_data=recipes,
                           context={'ordered_local_premises': [], 'fixture': True}, authority=authority,
                           fixed_marks=[(1, r, -1) for r in range(1-height, 0)] + list(marks),
                           roots=roots, fixture=True)


def raw_domain(g, row):
    if g.totals[row]: return {}
    out, codes = {}, {core.canonical(f): i for i, f in enumerate(g.formulas)}
    for index, r in enumerate(g.recipes):
        witness, premises = r.witness, r.formulas
        offsets = itertools.product(range(1-g.height, 0), repeat=len(premises)) if premises else [()]
        for values in offsets:
            refs = tuple(row + v for v in values)
            m = {(1, row): codes[core.canonical(witness['formula'])]}; consistent = True
            for port, (source, value, formula) in enumerate(zip(refs, values, premises)):
                point, code = (1, source), codes[core.canonical(formula)]
                if point in m and m[point] != code: consistent = False; break
                m[point] = code; m[2+port, row] = value
            if not consistent: continue
            if any(p in g.marks and g.marks[p] != v for p, v in m.items()): continue
            key = core.Key(index, row, refs)
            if key not in g.excluded[row]:
                out[key] = ([[0, row, 1]], [[*p, v] for p, v in sorted(m.items())])
    return out


def compare(control):
    g = control.graph; count = 0
    for row in range(g.height):
        raw = raw_domain(g, row); keys = list(g.candidates(row))
        assert keys == sorted(raw) and len(keys) == g.domains[row].count
        for key in keys:
            assert g.point_data(key) == raw[key]; count += 1
    d = g.decision()
    if d.kind in ('branch', 'forced'):
        base = list(g.candidates(d.row)); preferred = list(control.ordered(d))
        assert len(preferred) == len(base) and set(preferred) == set(base)
        if d.kind == 'forced': assert preferred == base
    return count


def authority(g, named_members):
    bodies = [life.primitive_body(g, name, members) for name, members in named_members]
    source = [{'path': '.gcts-active/hilbert-cluster-lifecycle-20261011/plan-v1.json',
               'sha256': core.pin(HERE / 'plan-v1.json')['sha256'],
               'bytes': core.pin(HERE / 'plan-v1.json')['bytes']},
              {'path': str(Path(__file__).resolve().relative_to(life.ROOT)),
               **core.pin(__file__)}]
    return life.BodyAuthority.build(g, source, bodies)


def control(g, named_members):
    a = authority(g, named_members)
    proposals = [a.expected(g, name, a.body(name)['canonical_input_rows'],
                            [m['row'] for m in a.body(name)['primitive_members']], index)
                 for index, (name, _) in enumerate(named_members)]
    return life.Controller(g, a, proposals)


def must_reject(call):
    try: call()
    except (ValueError, TypeError, KeyError, IndexError): return
    raise AssertionError('adversarial input was accepted')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-directory',required=True)
    output=Path(parser.parse_args().output_directory).resolve()
    if output!=EXPECTED_OUTPUT.resolve():raise ValueError('only isolated attempt-03 output allowed')
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('tiny lifecycle child alarm')))
    signal.alarm(50)
    records, states, authorities, domain_comparisons, operations, dfs_traces = [], [], {}, 0, [], []

    def transaction(c, name, payload, call):
        before = c.semantic_state(); call()
        operations.append({'kind': name, 'payload': payload,
                           'before': before, 'after': c.semantic_state()})

    def snapshot(name, c):
        nonlocal domain_comparisons
        domain_comparisons += compare(c)
        authorities[c.authority.epoch] = {'graph_binding': json.loads(c.authority.graph_text),
            'source_bindings': json.loads(c.authority.source_text),
            'bodies': [[n, json.loads(b)] for n, b in c.authority.bodies], 'epoch': c.authority.epoch}
        states.append({'name': name, 'state': c.semantic_state(),
                       'descriptors': [json.loads(d.text) for d in c.descriptors],
                       'complete_domains': [[k.data() for k in c.graph.candidates(r)]
                                            for r in range(c.graph.height)],
                       'recipes': [{'id': r.identifier, 'primitive_witness': r.witness,
                                    'ordered_premise_formulas': r.formulas} for r in c.graph.recipes],
                       'formulas': c.graph.formulas, 'initial_marks': [[*p, v] for p,v in sorted(c.graph.initial_marks.items())]})

    def passed(name, **data): records.append({'name': name, 'status': 'passed', **data})

    # Waiting hints never influence point choice or remove ordinary base alternatives.
    g = graph(); c = control(g, [('later-p', [core.Key(0, 2)])]); e = life.Executor(c)
    snapshot('waiting-root', c); before = c.semantic_state(); cp = c.checkpoint()
    assert c.states[0].status == 'waiting' and g.decision().row == 0
    transaction(c, 'scheduler-step', core.Key(1,0).data(), lambda: e.step(core.Key(1,0)))
    snapshot('waiting-after-other-earlier-row', c)
    assert c.states[0].status == 'waiting'
    transaction(c, 'paired-rollback', list(cp), lambda: c.rollback(cp)); assert c.semantic_state() == before
    passed('waiting_complete_fallback_and_paired_rollback')

    # One invalid constituent retires its whole cluster despite a legal sibling.
    g = graph(); c = control(g, [('two-p', [core.Key(0, 1), core.Key(0, 2)])])
    before = c.semantic_state(); cp = c.checkpoint()
    transaction(c, 'catalog-controlled-step-and-resync', core.Key(3,1).data(),
                lambda: (g._apply_legal(core.Key(3,1)), c.resync())); snapshot('same-formula-different-key-whole-retirement', c)
    assert c.states[0].status == 'retired' and g.legal(core.Key(0, 2))
    transaction(c, 'catalog-controlled-step-and-resync', core.Key(1,0).data(),
                lambda: (g._apply_legal(core.Key(1,0)), c.resync()))
    assert list(c.ordered(g.decision())) == list(g.candidates(2))
    transaction(c, 'paired-rollback', list(cp), lambda: c.rollback(cp)); assert c.semantic_state() == before
    snapshot('revived-after-child-rollback', c)
    passed('whole_retirement_same_formula_different_identity_legal_sibling_and_revival')

    # A global forced action outside the hint invalidates a distant input marking.
    g = graph(); c = control(g, [('mp-continuation', [core.Key(2, 1), core.Key(4, 2, (0, 1))])])
    e = life.Executor(c); before = c.semantic_state(); cp = c.checkpoint()
    # Controlled exclusions are fixtures of scheduler interaction, not invented subtree proofs.
    for key in list(g.candidates(0)):
        if key != core.Key(1,0):
            transaction(c, 'fixture-controlled-exclusion-not-proof', key.data(),
                        lambda key=key: g.exclude_failed_child(key))
    transaction(c, 'whole-resync', {}, c.resync); snapshot('outside-forced-before-action', c)
    assert g.decision().kind == 'forced' and c.states[0].status == 'waiting'
    must_reject(lambda: e.step(core.Key(2, 1)))
    transaction(c, 'scheduler-forced-step', core.Key(1,0).data(), lambda: e.step(core.Key(1,0)))
    snapshot('outside-forced-remote-invalidation', c)
    assert c.states[0].status == 'retired' and g.legal(core.Key(2, 1))
    transaction(c, 'paired-rollback', list(cp), lambda: c.rollback(cp)); assert c.semantic_state() == before
    passed('forced_first_resynchronization_retires_whole_remote_hint')

    # Exact shared key is occupied once; independent hints retain their other members.
    g = graph(); common = core.Key(0, 0)
    c = control(g, [('first', [common, core.Key(0, 1)]), ('second', [common, core.Key(2, 2)])])
    e = life.Executor(c); snapshot('shared-member-before', c); cp = c.checkpoint(); before = c.semantic_state()
    assert c.states[0].status == c.states[1].status == 'ready'
    assert list(c.ordered(g.decision())).count(common) == 1
    transaction(c, 'scheduler-shared-step', common.data(), lambda: e.step(common)); snapshot('shared-member-selected-once', c)
    assert g.totals[0] == 1 and len([k for k in g.selected if k == common]) == 1
    assert all(s.status != 'retired' for s in c.states)
    transaction(c, 'catalog-controlled-step-and-resync', core.Key(3,1).data(),
                lambda: (g._apply_legal(core.Key(3,1)), c.resync())); snapshot('one-shared-hint-retires-independently', c)
    assert c.states[0].status == 'retired' and c.states[1].status != 'retired'
    transaction(c, 'catalog-controlled-step-and-resync', core.Key(2,2).data(),
                lambda: (g._apply_legal(core.Key(2,2)), c.resync())); snapshot('second-shared-hint-consumed', c)
    assert c.states[1].status == 'consumed'
    transaction(c, 'paired-rollback', list(cp), lambda: c.rollback(cp)); assert c.semantic_state() == before
    passed('exact_sharing_consumed_state_independent_retirement_and_nested_revival')

    # Noninjective receptor binding preserves two ordered ports, even one m value.
    g = graph(); body = life.primitive_body(g, 'repeated-ports', [core.Key(5, 2, (0, 1))])
    a = life.BodyAuthority.build(g, json.loads(authority(g, [('unused', [core.Key(0, 0)])]).source_text), [body])
    descriptor = a.expected(g, 'repeated-ports', (0, 0), (2,), 0)
    c = life.Controller(g, a, [descriptor]); snapshot('ordered-noninjective-receptor-ports', c)
    assert c.descriptors[0].members[0].refs == (0, 0)
    assert len(descriptor['ordered_receptor_ports']) == 2
    assert [2, 2, -2] in descriptor['aggregate_m'] and [3, 2, -2] in descriptor['aggregate_m']
    bad = copy.deepcopy(descriptor); changed = core.Key(5,2,(1,0)); decorated = g.decorate(changed)
    bad['members'] = [changed.data()]; bad['full_member_ids'] = [decorated['id']]
    bad['full_identity_preimages'] = [decorated['identity_preimage']]
    bad['aggregate_t'], bad['aggregate_m'] = decorated['t'], decorated['m']
    bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    must_reject(lambda: a.compile(g, bad))
    passed('noninjective_equal_receptors_keep_ordered_duplicate_premise_ports_and_altered_refs_rejected')

    # Descriptor self-hashing cannot replace the registered source body.
    g = graph(); a = authority(g, [('p-body', [core.Key(0, 1)])])
    good = a.expected(g, 'p-body', (), (1,), 0); rejected = []
    for field in ('model_epoch', 'context_id', 'formula_registry_sha256', 'authority_epoch',
                  'primitive_palette_sha256', 'boundary_sha256', 'source_bindings_sha256'):
        bad = copy.deepcopy(good); bad['graph_binding'][field] = 'stale'
        bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
        must_reject(lambda bad=bad: a.compile(g, bad)); rejected.append('stale-'+field)
    for field in ('source_body_sha256', 'mapped_body_sha256', 'body_sha256', 'body_authority_epoch'):
        bad = copy.deepcopy(good); bad[field] = '0' * 64
        bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
        must_reject(lambda bad=bad: a.compile(g, bad)); rejected.append('altered-'+field)
    # All edited primitive values/IDs are fresh and individually valid, but recipe is outside body.
    bad = copy.deepcopy(good); changed = core.Key(3, 1); decorated = g.decorate(changed)
    bad['members'] = [changed.data()]; bad['full_member_ids'] = [decorated['id']]
    bad['full_identity_preimages'] = [decorated['identity_preimage']]
    bad['aggregate_t'], bad['aggregate_m'] = decorated['t'], decorated['m']
    bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    must_reject(lambda: a.compile(g, bad)); rejected.append('valid-altered-recipe-with-fresh-identity')
    # Valid alternative row with self-consistent identity cannot mismatch advertised body binding.
    bad = copy.deepcopy(good); changed = core.Key(0, 2); decorated = g.decorate(changed)
    bad['members'] = [changed.data()]; bad['full_member_ids'] = [decorated['id']]
    bad['full_identity_preimages'] = [decorated['identity_preimage']]
    bad['aggregate_t'], bad['aggregate_m'] = decorated['t'], decorated['m']
    bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    must_reject(lambda: a.compile(g, bad)); rejected.append('valid-altered-row-with-fresh-identity')
    bad = copy.deepcopy(good); bad['full_identity_preimages'][0]['primitive_command']['template'] = ['pred','forged',[]]
    bad['descriptor_id'] = 'whole-cluster-' + core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    must_reject(lambda: a.compile(g, bad)); rejected.append('altered-equality-template-command')
    bad = copy.deepcopy(good); bad['body_name'] = 'missing-body'
    must_reject(lambda: a.compile(g, bad)); rejected.append('missing-body')
    bad = copy.deepcopy(good); bad['dependency_bindings'] = [{'name':'missing', 'body_sha256':'0'*64}]
    must_reject(lambda: a.compile(g, bad)); rejected.append('missing-earlier-dependency')
    c = life.Controller(g, a, [bad, good, good]); snapshot('invalid-and-duplicate-root-descriptors', c)
    assert c.metrics['root_rejections'] == 2 and len(c.descriptors) == 1
    passed('immutable_whole_descriptor_authority_and_valid_altered_embedding_rejected', rejected=rejected)

    # Invalid same-formula MP and boolean exact values cannot enter even synthetic metadata.
    corrupt = copy.deepcopy(RECIPES); corrupt[4]['ordered_premise_formulas'][1] = ['imp', Q, Q]
    must_reject(lambda: graph(recipes=corrupt))
    b = life.primitive_body(g, 'bool-code', [core.Key(0, 1)]); b['primitive_members'][0]['formula_code'] = False
    must_reject(lambda: life.BodyAuthority.build(g, json.loads(a.source_text), [b]))
    b = life.primitive_body(g, 'missing-dependency', [core.Key(0, 1)])
    b['dependency_bindings'] = [{'name':'absent','body_sha256':'0'*64}]
    must_reject(lambda: life.BodyAuthority.build(g, json.loads(a.source_text), [b]))
    c = control(graph(), [('finite', [core.Key(0, 1)])]); e = life.Executor(c)
    for seconds in (float('nan'), float('inf'), -1, True):
        must_reject(lambda seconds=seconds: e.solve(max_attempts=0, seconds=seconds))
    passed('point_consistent_invalid_logic_boolean_formula_missing_dependency_nonfinite_budget')

    # Explicit zero versus absent remote offset constrains cluster legality.
    g = graph(marks=[(2, 2, 0)]); a = authority(g, [('mp', [core.Key(4, 2, (0, 1))])])
    descriptor = a.expected(g, 'mp', (0, 1), (2,), 0); c = life.Controller(g, a, [descriptor])
    snapshot('assigned-zero-remote-offset', c); assert c.states[0].status == 'retired'
    c = control(graph(), [('mp', [core.Key(4, 2, (0, 1))])]); snapshot('absent-remote-offset', c)
    assert c.states[0].status == 'waiting'
    passed('assigned_zero_is_value_absence_unconstrained')

    # Whole metadata changes fail closed; old graph metadata may not silently version-shift.
    g = graph(); c = control(g, [('p', [core.Key(0, 1)])]); g.authority['label'] = 'untracked-change'
    c.resync(); assert c.states[0].status == 'retired'
    passed('untracked_public_authority_metadata_mutation_detected')

    # Complete synthetic DFS truly exhausts children; unknown never manufactures exclusions.
    tinyrecipes = [recipe('irrelevant-r-first', R), recipe('p', P), recipe('imp', IMP),
                   recipe('mp', Q, [P, IMP], 'mp')]
    g = graph(4, recipes=tinyrecipes, marks=[(1,3,1)], roots=(0,0,0,5))
    c = control(g, [('r-control', [core.Key(0, 0), core.Key(0, 1)])]); e = life.Executor(c)
    initial = c.semantic_state(); unknown = e.solve(max_attempts=0, seconds=1)
    assert unknown['status'] == 'unknown_budget' and c.semantic_state() == initial
    snapshot('zero-budget-no-exclusion', c)
    # Inspection above resynchronizes the hint revision: save its ACTUAL next-call baseline.
    initial = c.semantic_state()
    # One attempted child becomes unknown; complete rollback of hint resync/graph trail.
    unknown = e.solve(max_attempts=1, seconds=1)
    status_ok = unknown['status'] == 'unknown_budget'
    restoration_ok = c.semantic_state() == initial
    if not status_ok or not restoration_ok:
        diagnostic={'status':'failed_unknown_fixture_diagnostic', 'result':unknown,
                    'expected_parent':initial, 'actual_parent':c.semantic_state(),
                    'status_ok':status_ok,'restoration_ok':restoration_ok,'events':e.events}
        (output/'fixture-failure-diagnostic-v1.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    assert status_ok, 'one-child cutoff was not unknown'
    assert restoration_ok, 'one-child cutoff failed actual call-entry paired restoration'
    snapshot('child-budget-unknown-no-parent-exclusion', c)
    solved = e.solve(max_attempts=100, seconds=2)
    assert solved['status'] == 'finite_exact_point_tiling' and g.metrics['backtracks'] > 0
    assert solved['certificate']['native_accepted'] is False
    snapshot('exhausted-children-then-synthetic-solution', c)
    dfs_traces.append({'name':'bounded_synthetic_unknown_and_exhaustion', 'events':e.events})
    passed('full_child_exhaustion_parent_exclusion_and_child_unknown_exact_rollback',
           backtracks=g.metrics['backtracks'], solution_status=solved['status'])

    # Direct all-recipe domains remain unchanged for every bounded tiny mark assignment.
    state_count = 0
    for values in itertools.product((None,0,1,2), repeat=3):
        marks = [(1,row,value) for row,value in enumerate(values) if value is not None]
        g = graph(marks=marks); c = control(g, [('late-p', [core.Key(0, 2)])])
        snapshot('exhaustive-formula-state-' + str(state_count), c); state_count += 1
    passed('complete_tiny_formula_states_domains_and_preference_fallback_permutations', states=state_count)

    outcome = {'status':'passed_authored_synthetic_whole_cluster_lifecycle_pending_independent_gate',
        'version':life.VERSION, 'records':records, 'states':states, 'authorities':authorities,
        'controlled_operations':operations, 'synthetic_dfs_traces':dfs_traces,
        'complete_raw_candidate_comparisons':domain_comparisons,
        'controlled_states':len(states), 'fixture_groups':len(records),
        'worker_seconds_before_receipt_write':time.perf_counter()-started,
        'actual_geometry_model_execution':False, 'geometry_target_searches':0, 'native_queries':0,
        'new_RL_training':False, 'native_authority_activated':False,
        'scope':'synthetic fixed ordering conformance; no actual full-language lifecycle execution'}
    path = output/'fixtures-outcome-v1.json'
    if path.exists(): raise ValueError('immutable tiny outcome exists')
    path.write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps({k:v for k,v in outcome.items() if k not in ('records','states','authorities','controlled_operations','synthetic_dfs_traces')}),flush=True)

if __name__ == '__main__': main()
