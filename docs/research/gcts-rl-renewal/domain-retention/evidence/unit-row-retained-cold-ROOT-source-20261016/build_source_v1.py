"""Source/AST metadata assembly only. No project code/functions executed."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PARENT=BASE/'unit-row-search-failure-diagnostic-cold-source-20261015/unit_row_search_failure_diagnostic_cold_v2.py'
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(name,x):
    p=HERE/name
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
parent=PARENT.read_bytes();assert pin(PARENT)['sha256']=='0b6c980f2310cac5788876e6837b9213305482bb838dfca47f63f8ae34771db4'
text=parent.decode();tree=ast.parse(parent)
values={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('FIXED','FIXED_INPUTS','LIMITS')}
fixed=values['FIXED'];inputs=values['FIXED_INPUTS'];limits=values['LIMITS']
e=read(BASE/'unit-row-retained-domain-engine-source-20261015/handoff-v2.json')
c=read(BASE/'unit-row-retained-domain-controls-source-20261015/handoff-v2.json')
assert e['source']['sha256']=='ca6151724b61e4fc3f8a2ba9ffa4a77c03e516898d7970eb275a6fc70a435c6f'
assert e['checker_source']['sha256']=='2e2d66c3c5843ef086f073df09e2eda7a50d3972fa1900a8ecf33f5c92ab3491'
assert c['source']['sha256']=='d1dcdfa9230ab1653c601ee2d769c64722d9ab0d0f292682bda214d8984488eb'
fixed.update(engine=e['source'],transition=e['checker_source'],retained_controls=c['source'])
def replace(old,new):
    global text
    assert text.count(old)==1,old[:120]
    text=text.replace(old,new,1)
replace("VERSION='unit-row-search-failure-diagnostic-cold-v2'","VERSION='unit-row-retained-domain-cold-v1'")
replace("SCOPE='unit-row-search-failure-diagnostic-cold-Source'","SCOPE='unit-row-retained-domain-cold-Source'")
oldfixed=next(line for line in text.splitlines() if line.startswith('FIXED='))
replace(oldfixed,'FIXED='+repr(fixed))
replace("plan['purpose'] in ('unit-row-global-engine-controls','unit-row-global-engine-search')",
        "plan['purpose'] in ('unit-row-retained-original-controls','unit-row-retained-domain-controls','unit-row-retained-target-search')")
replace("contract['schema'] == 'unit-row-search-failure-diagnostic-cold-Source-contract-v1'",
        "contract['schema'] == 'unit-row-retained-domain-cold-Source-contract-v1'")
replace("review['author_identity'] == '/root/hilbert_advice_controls'","review['author_identity'] == '/root'")
replace("review['reviewer_identity'] not in ('/root','/root/hilbert_advice_controls')","review['reviewer_identity'] != '/root'")
replace("degree_proposer=degree_proposer,semantics=modules['degree_checker'],\n            fallback=fallback,certify_fallback=certify_fallback,tick=step,",
        "degree_proposer=degree_proposer,semantics=modules['degree_checker'],\n            transition_checker=modules['transition'],\n            fallback=fallback,certify_fallback=certify_fallback,tick=step,")
adapters='''    def transition_adapter(*,before,after,rows,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original transition authority')
        snapshot = invoke_fn(modules['transition'].authority_snapshot,(),{
            'language':private,'semantics':modules['degree_checker'],'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        return invoke_fn(modules['transition'].check_transition,(),{
            'language':private,'semantics':modules['degree_checker'],
            'before':copy.deepcopy(before),'after':copy.deepcopy(after),'rows':copy.deepcopy(rows),
            'authority':canonical(snapshot).decode('utf8'),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def refresh_adapter(*,state,candidates,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original known-packet refresh authority')
        return invoke_fn(modules['transition'].refresh_candidates,(),{
            'language':private,'semantics':modules['degree_checker'],
            'state':copy.deepcopy(state),'candidates':copy.deepcopy(candidates),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
'''
replace('    def scheduler_adapter(*,evidence,generations,tick):',adapters+'    def scheduler_adapter(*,evidence,generations,tick):')
start=text.index("    is_controls = plan['purpose'] == 'unit-row-global-engine-controls'")
end=text.index('    else:\n        diagnostic_run =',start)
oldblock=text[start:end]
newblock='''    is_controls = plan['purpose'] != 'unit-row-retained-target-search'
    if is_controls:
        is_original = plan['purpose'] == 'unit-row-retained-original-controls'
        selected_controls = modules['controls'] if is_original else modules['retained_controls']
        control_kwargs = {'language':fixture_language,'engine_factory':engine_factory,
            'degree_proposer':proposer_adapter,'fallback':fallback_adapter,
            'certify_fallback':certify_adapter,'tick':tick}
        if is_original:
            control_kwargs['scheduler'] = scheduler_adapter
        else:
            control_kwargs.update(transition=transition_adapter,refresh=refresh_adapter)
        payload = invoke_fn(selected_controls.run_controls,(),control_kwargs,
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        expected_schema = ('unit-row-lazy-global-controls-v1' if is_original
                           else 'unit-row-retained-domain-controls-v1')
        need(type(payload) is dict and payload['schema'] == expected_schema
            and payload['all_declared_cases_completed'] is True and type(payload['cases']) is list,
            'complete selected original or retained control record; scopes remain distinct')
'''
replace(oldblock,newblock)
source=HERE/'unit_row_retained_domain_cold_v1.py'
with source.open('xb') as f:f.write(text.encode())
selected=source.read_bytes();st=ast.parse(selected);compile(st,str(source),'exec')
source_pin=pin(source);sources=dict(fixed,intake=source_pin)
parent_contract=read(BASE/'unit-row-search-failure-diagnostic-cold-source-20261015/Source-contract-v1.json')
helpers=parent_contract['provenance']['unchanged15_helpers']
od={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};nd={n.name:n for n in st.body if isinstance(n,ast.FunctionDef)}
for name in helpers:
    assert ast.dump(od[name],include_attributes=False)==ast.dump(nd[name],include_attributes=False)
    assert ast.get_source_segment(parent.decode(),od[name])==ast.get_source_segment(text,nd[name])
assert ast.get_source_segment(parent.decode(),od['save_failure_diagnostic'])==ast.get_source_segment(text,nd['save_failure_diagnostic'])
tail=b"    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1',"
assert parent[parent.index(tail):]==selected[selected.index(tail):]
for ref in [*sources.values(),*inputs.values()]:assert pin(Path(ref['path']))==ref
contract={'schema':'unit-row-retained-domain-cold-Source-contract-v1','scope':'unit-row-retained-domain-cold-Source',
 'author_identity':'/root','source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'sources':sources,'inputs':inputs,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1',
 'parent_source':pin(PARENT),'parent_contract':pin(BASE/'unit-row-search-failure-diagnostic-cold-source-20261015/Source-contract-v1.json'),
 'Review_ABI':{'schema':'unit-row-retained-domain-cold-typed-Source-review-v1','scope':'unit-row-retained-domain-cold-Source',
  'author_identity':'/root','source':source_pin,'sources':sources,'source_contract':'Exact current raw contract capsule.',
  'source_only':True,'scientific_calls':0,'scientific_acceptance':False},
 'purposes':{'unit-row-retained-original-controls':'Original17 controls, unchanged Source, now current retained engine.',
  'unit-row-retained-domain-controls':'Current17 retention/archive/refresh controls, no target search.',
  'unit-row-retained-target-search':'Separate fresh original right-two root, only after both distinct control actuals qualify.'},
 'endpoint_separation':'Each purpose owns a distinct once actual and full original20s/512MiB gate. Controls separate to keep complete raw snapshot output under unchanged4MiB cap. Target search is one unsplit original-root actual; no combined34case-stage or cross-run cache claim.',
 'authority':'Original full fixed inputs reconstructed per proposer/cursor/certifier/transition/refresh call and private per-engine semantics. Transition snapshot and current two whole states checked in fresh original authority. Refresh premise is previously checked known candidate packets, not arbitrary supplied old metadata.',
 'guards':'All11 Sources authenticated and covered by existing surrounding CodeSeal/function anchors and original native tick before injected callback. No per-method/yield seal or hostile concurrent Python/OS claim. No new custody framework.',
 'retention':'Exact sufficient all-possible support and global preimage ledger comparison, owner-held evidence transfer with full original receipt, freshly rebuilt known packets, genuine current cursor replay and flat context archive. Current engine/checker Source reviews and new runtime controls remain separate.',
 'diagnostics':'Exact inherited bounded failure-only55 raw returned-payload writer. Original success20/exit0 tail and failureexit2 unchanged. No late scientific callback or proof/trajectory/restore/resource success admission.',
 'search':'Original target/theory/emptyGamma/parameters/bounded six-rule inventory/24roots; initial_stateNone, max128nodes/2000events. No word/donor/library/route/rank/learned/RL input.',
 'gaps':['No full reference incremental conformance or minimal retention oracle; conservative collision-ledger invalidation.',
  'No independent arbitrary all-six EOF/exhaustion authority beyond current completed covers.',
  'Fixed unit rows only; fractional/shared positive support, growing targets, universal physical palette/fullFOL/fullPA outside scope.',
  'No runtime fit, accepted search trajectory/proof, learned marking/RL or advantage established by Source.'],
 'unchanged15_helpers':helpers,'unchanged_failure_writer':True,'unchanged_positive_output_exit_tail':True}
cr=save('Source-contract-v1.json',contract)
save('static-evidence-v1.json',{'schema':'ROOT-retained-caller-static-evidence-v1','source':source_pin,
 'source_contract':cr,'all15_helpers_raw_AST_exact':True,'failure_writer_raw_exact':True,'positive_tail_raw_exact':True,
 'source_count':11,'input_count':2,'compile_only':True,'scientific_execution':False})
handoff=save('handoff-v1.json',{'schema':'ROOT-retained-cold-Source-handoff-v1','source':source_pin,'source_contract':cr,
 'sources':sources,'inputs':inputs,'limits':limits,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'actual_execution_authorized':False,'independent_review_pending':True})
print(json.dumps({'source':source_pin,'source_contract':cr,'handoff':handoff}))
