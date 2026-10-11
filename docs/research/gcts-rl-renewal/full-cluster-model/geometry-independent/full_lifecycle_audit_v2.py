"""Prospective independent full-language lifecycle artifact audit.

Root must first review an exact source/input/output freeze and explicitly
dispatch its owner. No engine, producer, search, solver or native import.
"""
import copy
import importlib.util
import json
import resource
import signal
import sys
import time
from pathlib import Path
from full_point_oracle_v1 import State, canonical, digest, pin, read, need, points, decorate, validate_model
from full_family_registry_v1 import (
    VERSION, equal, key, key_data, graph_binding, family_bodies, receptor_ports, authored_body, descriptor,
)
from full_lifecycle_state_v1 import SnapshotController, graph_decision, legal, check_snapshot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check_pins(plan):
    for group in ('sources', 'libraries', 'inputs', 'preserved_files'):
        for e in plan.get(group, []):
            equal(pin(ROOT/e['path']), {k:e[k] for k in ('sha256','bytes')}, 'exact frozen '+e['path'])


def independent_libraries(plan):
    paths = {e['role']: ROOT/e['path'] for e in plan['libraries']}
    symbolic_path = paths['symbolic_checker']
    # Both modules are our previously frozen independent audit sources. The
    # expansion library's ordinary import is constrained to this pinned folder.
    sys.path.insert(0, str(symbolic_path.parent))
    modules = {}
    for role, name in (('symbolic_checker','independent_aggregate_audit_v1'),
                       ('expansion_checker','full_lifecycle_independent_expansion_library')):
        spec = importlib.util.spec_from_file_location(name, paths[role])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module; spec.loader.exec_module(module); modules[role] = module
    return modules['symbolic_checker'], modules['expansion_checker']


def point_model(data, prior_plan, symbolic):
    model, inventory, checker, seeds, counts = validate_model(data, symbolic)
    boundary = model['boundary']; fixed = sorted(boundary['fixed_exterior_m']+boundary['fixed_target_m'])
    sources = {e['role']:{k:e[k] for k in ('path','sha256','bytes')} for e in prior_plan['inputs']}
    roots = [r[2] for r in boundary['root_generations']]
    epoch = digest(dict(height=24, context=model['context'], registry=digest(data['formula_codes']),
        authority=data['authority']['epoch'], recipes=[r['id'] for r in inventory], fixed_marks=fixed,
        roots=roots, seed_keys=[key_data(k) for k in seeds],
        marking_version='injective-formula-ordered-mp-offset-v1', fixture=False, source_bindings=sources))
    state = State(24, inventory, fixed, roots, epoch)
    for k in seeds:
        state.apply(k, generation=0)
    binding = graph_binding(state, model['context'], data['authority'], data['formula_codes'], sources, seeds, fixed)
    return state, binding, model, checker, counts


def build_authority(state, binding, data, producer_plan, certificate, schemas, projected, expansion_checker):
    bodies, counts, source_receipts = family_bodies(certificate, schemas, projected, data, expansion_checker)
    for b in bodies:
        b['ordered_receptor_ports'] = receptor_ports(b, state.recipes)
    axiom = next(i for i,r in enumerate(state.recipes) if r['witness']['rule']=='axiom')
    need(state.recipes[axiom]['output']==0, 'assigned zero control is exact')
    ax3, ax4, ax8 = [(axiom,r,()) for r in (3,4,8)]
    name = next(b['name'] for b in bodies if b['premise_codes']==[state.marks[1,0]]
                and len(b['primitive_members'])==10)
    eligible = (k for k,_,_ in state.raw_candidates(22) if k[2] and min(k[2])>=13)
    distant = next(eligible)
    other = next(k for k,_,_ in state.raw_candidates(22) if k[0]==distant[0] and k!=distant and min(k[2])>=13)
    fixed = [authored_body('fixed-shared-single-axiom',[ax3],state),
             authored_body('fixed-shared-two-axioms',[ax3,ax4],state),
             authored_body('fixed-waiting-later-axiom',[ax8],state),
             authored_body('fixed-distant-mp-and-legal-sibling',[ax4,distant],state)]
    bodies.extend(fixed)
    need(len({b['name'] for b in bodies})==len(bodies)==175, 'distinct complete family and fixed body declarations')
    sources = [{k:e[k] for k in ('path','sha256','bytes')} for e in producer_plan['inputs']]
    registry = dict(graph_binding=binding, source_bindings=sources, bodies=[[b['name'],b] for b in bodies])
    registry['epoch'] = digest(dict(graph=binding, sources=sources,
        bodies=[[b['name'],digest(b)] for b in bodies], version=VERSION))
    specs = [('fixed-shared-single-axiom',[],[3],0),('fixed-shared-two-axioms',[],[3,4],1),
        (name,[0],list(range(3,13)),2),('fixed-waiting-later-axiom',[],[8],3),
        ('fixed-distant-mp-and-legal-sibling',fixed[3]['canonical_input_rows'],[4,22],4)]
    descriptors = [descriptor(dict(registry['bodies'])[n],ins,rows,priority,binding,sources,registry['epoch'],
        state,next(m['context'] for m in data['models'] if m['height']==24),
        data['authority']['epoch'],digest(data['formula_codes'])) for n,ins,rows,priority in specs]
    return registry, descriptors, counts, source_receipts, distant, other


def checked_descriptor(supplied, registry, state, context, authority, formula_registry):
    need(supplied['body_name'] in dict(registry['bodies']), 'registered body name')
    wanted = descriptor(dict(registry['bodies'])[supplied['body_name']],
        supplied['ordered_input_rows'],supplied['ordered_member_rows'],supplied['fixed_priority'],
        registry['graph_binding'],registry['source_bindings'],registry['epoch'],state,context,authority,formula_registry)
    # Check the literal transport first. A separately valid replacement primitive
    # plus fresh full IDs cannot redefine the registered source body.
    equal(supplied['members'],wanted['members'],'members instantiate registered source body')
    equal(supplied,wanted,'every descriptor body/epoch/receptor/aggregate/cache field')
    return wanted


def corruptions(registry, descriptors, state, context, authority, formula_registry):
    receipts = []
    def reject(label, supplied):
        try:
            checked_descriptor(supplied,registry,state,context,authority,formula_registry)
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            receipts.append(dict(name=label,rejected=True,reason=str(exc)))
            return
        raise ValueError('corruption accepted: '+label)
    for field in ('model_epoch','context_id','authority_epoch','formula_registry_sha256',
                  'primitive_palette_sha256','boundary_sha256','source_bindings_sha256'):
        bad=copy.deepcopy(descriptors[2]);bad['graph_binding'][field]='stale';reject('stale-'+field,bad)
    for field in ('body_sha256','source_body_sha256','mapped_body_sha256','body_authority_epoch'):
        bad=copy.deepcopy(descriptors[2]);bad[field]='stale';reject('stale-'+field,bad)
    bad=copy.deepcopy(descriptors[2]);bad['source_bindings']=bad['source_bindings'][:-1];reject('missing-source-closure',bad)
    axiom=next(i for i,r in enumerate(state.recipes) if r['witness']['rule']=='axiom')
    bad=copy.deepcopy(descriptors[2]);keys=[(axiom,k[1],()) for k in map(key,bad['members'])]
    decorated=[decorate(k,*points(state.recipes[k[0]],k[1],k[2],24),state.recipes,context,authority,formula_registry) for k in keys]
    bad['members']=[key_data(k) for k in keys]
    bad['full_member_ids']=[p['id'] for p in decorated];bad['full_identity_preimages']=[p['identity_preimage'] for p in decorated]
    bad['aggregate_t']=[[0,k[1],1] for k in keys]
    bad['aggregate_m']=[[1,k[1],0] for k in keys]+[[1,bad['ordered_input_rows'][0],
        dict(registry['bodies'])[bad['body_name']]['premise_codes'][0]]]
    bad['aggregate_m'].sort()
    bad['descriptor_id']='whole-cluster-'+digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    reject('point-consistent-fresh-valid-primitives-cannot-replace-source-body',bad)
    bad=copy.deepcopy(descriptors[2]);bad['full_member_ids'][0]=bad['full_member_ids'][1];reject('false-sharing-by-output',bad)
    bad=copy.deepcopy(descriptors[4]);bad['members'][-1][2].reverse();reject('altered-ordered-reference-ports',bad)
    bad=copy.deepcopy(descriptors[2]);bad['aggregate_t'][0][2]=2;reject('aggregate-t-overcount',bad)
    bad=copy.deepcopy(descriptors[0]);bad['aggregate_m'][0][2]=False;reject('assigned-bool-is-not-zero',bad)
    bad=copy.deepcopy(descriptors[2]);bad['aggregate_m'].append([1,0,-1]);reject('hidden-distant-mark-conflict',bad)
    return receipts


def replay(outcome, state, registry, descriptors):
    controller = SnapshotController(state,descriptors,registry['epoch'])
    operations=outcome['controlled_operations']; observations=outcome['states']; comparisons=outcome['comparisons']
    need(len(observations)==len(comparisons)==11 and len(operations)==9,'exact predeclared controlled sequence')
    answers=[]; op=0
    def snap(index):
        answers.append(check_snapshot(controller,observations[index],comparisons[index]))
    def transaction(expected_name,scheduler=True,rollback=False):
        nonlocal op
        r=operations[op];need(r['name']==expected_name,'ordered declared transaction name')
        equal(r['before'],controller.semantic(),'exact operation parent state')
        if rollback:controller.rollback(r['payload'])
        else:controller.apply(r['payload'],scheduler=scheduler)
        equal(r['after'],controller.semantic(),'exact operation child/rollback state');op+=1
    snap(0);controller.checkpoint()
    transaction('scheduler-fixed-first-axiom');snap(1)
    transaction('scheduler-fixed-next-axiom');snap(2)
    transaction('paired-full-parent-rollback',rollback=True);snap(3)
    controller.checkpoint()
    transaction('catalog-remote-mark-forced-control',scheduler=False);snap(4)
    transaction('scheduler-forced-shared-axiom');snap(5)
    transaction('scheduler-forced-instantiation');snap(6)
    transaction('paired-remote-forced-control-rollback',rollback=True);snap(7)
    controller.checkpoint()
    transaction('catalog-same-output-different-identity',scheduler=False);snap(8)
    transaction('paired-distant-catalog-rollback',rollback=True);snap(9)
    snap(10)
    need(op==len(operations),'all controlled transactions checked')
    return answers


def recorded_state_corruptions(outcome, state, registry, descriptors):
    """Saved-state/fallback counterexamples checked against the separate oracle."""
    results=[]
    def reject(label, actual, expected):
        try:equal(actual,expected,'independent counterexample '+label)
        except ValueError:
            results.append(dict(name=label,rejected=True,corrupted_payload_sha256=digest(actual)))
            return
        raise ValueError('artifact corruption not rejected '+label)
    c=SnapshotController(state,descriptors,registry['epoch'])
    # Initial producer snapshot resynchronizes through complete ordering once.
    order=[key_data(k) for k in c.ordering()]
    root=c.semantic();equal(root,outcome['states'][0]['state'],'negative control exact root')
    bad=copy.deepcopy(root);bad['graph']['selected_generations'][0][1]=1
    reject('generation-zero-hypothesis-mutant',bad,root)
    bad=copy.deepcopy(root);bad['graph']['marks'][0][3]=True
    reject('boolean-mark-reference-count-mutant',bad,root)
    bad=copy.deepcopy(root);bad['graph']['domains'][3]['count']-=1
    reject('omitted-complete-domain-candidate',bad,root)
    reject('dropped-mandatory-base-fallback-key',order[:-1],order)
    c.apply(outcome['controlled_operations'][0]['payload']);list(c.ordering())
    after=c.semantic();equal(after,outcome['states'][1]['state'],'negative control exact assigned-zero state')
    bad=copy.deepcopy(after)
    zero=next(v for v in bad['graph']['marks'] if v[0:2]==[1,3])
    need(zero[2]==0,'zero is actually assigned in negative control')
    zero[2]=False;reject('boolean-is-not-assigned-zero',bad,after)
    need(c.state.totals[3]==1,'shared selected member has one unit occupancy')
    bad=copy.deepcopy(after);bad['graph']['totals'][3]=2
    reject('shared-member-counted-twice',bad,after)
    return results


def run(plan):
    check_pins(plan);symbolic,expansion=independent_libraries(plan)
    roles={e['role']:ROOT/e['path'] for e in plan['inputs']}
    producer_plan=read(roles['producer_plan']);prior_plan=read(roles['prior_point_plan'])
    for p in producer_plan['sources']+producer_plan['inputs']+producer_plan['preserved_files']:
        equal(pin(ROOT/p['path']),{k:p[k] for k in ('sha256','bytes')},'producer full closure')
    outcome=read(roles['producer_outcome']);data=read(roles['primitive_model']);projected=read(roles['family_projection'])
    need(outcome['status']=='passed_authored_full_language_lifecycle_controls_pending_independent_audit',
         'producer must be terminal passed before independent actual acceptance')
    supervision=read(roles['producer_supervision']);lifetime=read(roles['producer_lifetime'])
    need(supervision['status']=='passed_bounded_authored_full_language_lifecycle' and
         supervision['exit_code']==0 and supervision['owned_child_terminal_wait_reaped'] is True,
         'exact terminal reaped producer prerequisite')
    need(lifetime['status']=='passed_authored_full_language_lifecycle_full_lifetime' and
         lifetime['supervisor_wait_reaped'] is True and lifetime['process_return_code']==0,
         'complete producer lifetime prerequisite')
    equal(supervision['plan_sha256'],pin(roles['producer_plan'])['sha256'],'producer supervision plan binding')
    equal(lifetime['plan_sha256'],pin(roles['producer_plan'])['sha256'],'producer lifetime plan binding')
    equal(lifetime['supervision_sha256'],pin(roles['producer_supervision'])['sha256'],'producer exact supervision binding')
    projected.pop('example',None) # never supplies an input word or proposal
    state,binding,model,checker,rules=point_model(data,prior_plan,symbolic)
    equal(state.epoch,outcome['exact_prior_point_model_epoch'],'unchanged complete point model epoch')
    registry,descriptors,census,source_receipts,distant,other=build_authority(state,binding,data,producer_plan,
        read(roles['transport_certificate']),read(roles['source_schemas']),projected,expansion)
    equal(registry,outcome['authority_registry'],'every full registered literal body and source epoch')
    equal(descriptors,outcome['descriptors'],'all fixed independently declared descriptor transports')
    for d in descriptors:checked_descriptor(d,registry,state,model['context'],data['authority']['epoch'],digest(data['formula_codes']))
    comparisons=replay(outcome,state,registry,descriptors)
    identities=[]
    for k in (distant,other):
        p=decorate(k,*points(state.recipes[k[0]],k[1],k[2],24),state.recipes,model['context'],data['authority']['epoch'],digest(data['formula_codes']))
        identities.append(dict(key=key_data(k),id=p['id'],preimage_sha256=digest(p['identity_preimage'])))
    equal(identities,outcome['identities'],'same output and recipe with different ordered refs has distinct full identities')
    need(identities[0]['id']!=identities[1]['id'],'no formula-only identity merging')
    mutants=corruptions(registry,descriptors,state,model['context'],data['authority']['epoch'],digest(data['formula_codes']))
    mutants.extend(recorded_state_corruptions(outcome,state,registry,descriptors))
    equal(outcome['actual_target_DFS_searches'],0,'no target proof search')
    equal(outcome['authored24_words_used_as_hints'],0,'authored word never supplies hints')
    equal(outcome['native_queries'],0,'no native authority')
    need(all(c['frontier_points'] for c in comparisons),'controlled phase does not complete the proof region')
    check_pins(plan)
    return dict(status='passed_independent_full_language_lifecycle_controlled_artifact_audit',
        model_epoch=state.epoch,inventory=dict(recipes=229,formulas=217,required_rows=24,source_bodies=171,fixed_extra_bodies=4),
        independent_source_expansion_census=census,source_logical_receipts=source_receipts,
        independently_checked_recipe_rules=rules,complete_state_count=len(comparisons),controlled_transactions=9,
        complete_comparisons=comparisons,every_key_t_m_comparisons=sum(c['candidate_nodes'] for c in comparisons),
        body_authority_epoch=registry['epoch'],full_descriptor_ids=[d['descriptor_id'] for d in descriptors],
        exact_distinct_ordered_reference_identities=identities,independent_actual_corruptions=mutants,
        limitations=['Only eleven controlled recorded states/transactions, not all reachable states or a target DFS.',
            'All source families and literal primitive recipes checked in the guarded Hilbert incidence fragment; ordered inputs are marks, not newly added recipient hypotheses.',
            'Global dead/exhaustion/unknown adversaries remain the accepted tiny gate; full controlled phase has no exhausted-child exclusion.',
            'Producer rejection records and timings are read-only evidence; no claim of independently repeating every unsaved call or exact wall timer.',
            'Native/compiler/Wang correspondence, mathematical proof discovery and RL search gain remain open.'],
        native_queries=0,target_searches=0,solver_calls=0,training_episodes=0,authored24_words_used_as_hints=0,actual_geometry_model_loads=1)


def main():
    began=time.perf_counter();path=HERE/'audit-plan-v2.json';plan=read(path);out=ROOT/plan['result_path']
    need(not out.exists(),'immutable independent output')
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('independent lifecycle full child ceiling')))
    signal.setitimer(signal.ITIMER_REAL,plan['child_seconds'])
    result=dict(status='unknown_or_failed_independent_full_lifecycle_audit')
    try:result=run(plan)
    except Exception as exc:result.update(failure_type=type(exc).__name__,failure=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        elapsed=time.perf_counter()-began
        result.update(plan_sha256=pin(path)['sha256'],child_seconds_before_receipt_write=elapsed,
            child_kernel_peak_bytes=peak,source_authoring_cost='not instrumented; not zero')
        if elapsed>plan['child_seconds'] or peak>plan['peak_bytes']:
            result['status']='unknown_independent_full_lifecycle_resource_budget'
        with out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        print(json.dumps({k:result[k] for k in ('status','child_seconds_before_receipt_write','child_kernel_peak_bytes')}),flush=True)


if __name__=='__main__':main()
