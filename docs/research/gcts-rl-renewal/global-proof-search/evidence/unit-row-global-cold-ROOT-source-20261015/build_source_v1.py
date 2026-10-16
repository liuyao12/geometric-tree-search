"""Source/AST/metadata construction only; no project functions or experiments."""
import ast
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def check(r):
    p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    return pin(p)
parent=BASE/'unit-row-missing-mark-cold-ROOT-source-20261015/missing_mark_degree_controls_cold_v1.py'
assert pin(parent)['sha256']=='cbf39e7381dda8e637e6ad1bac85a94c217937415116151d988546563a5458c3'
old=parent.read_text();parent_h=read(parent.parent/'handoff-v1.json')
fixed={k:v for k,v in parent_h['sources'].items() if k not in ('intake','controls')}
handoffs={}
for role,folder in [('fallback','unit-row-all-six-fallback-source-20261015'),
                    ('engine','unit-row-lazy-global-engine-source-20261015'),
                    ('controls','unit-row-lazy-engine-controls-source-20261015')]:
    path=BASE/folder/'handoff-v1.json';h=read(path)
    check(h['source']);check(h['source_contract']);assert h['scientific_calls']==0 and h['source_only'] is True
    fixed[role]=h['source'];handoffs[role]=pin(path)
inputs=parent_h['inputs'];limits=read(check(parent_h['source_contract']))['limits']
assert len(fixed)==8 and len(inputs)==2
for r in [*fixed.values(),*inputs.values()]:check(r)
s=old.replace('Cold local-degree controls only. Reuses existing native measurement/helpers.\nNo proof word, donor or library is an input. Not a GCTS search engine.',
 'Cold original unit-row global engine endpoints. Reuses existing native helpers.\nControls or a separate fresh target search; no supplied proof word/donor/library.')
s=s.replace("VERSION='unit-row-missing-mark-degree-controls-cold-v1'","VERSION='unit-row-global-engine-cold-v1'")
s=s.replace("SCOPE='unit-row-missing-mark-degree-controls-cold-Source'","SCOPE='unit-row-global-engine-cold-Source'")
s=re.sub(r'^FIXED=.*$', 'FIXED='+repr(fixed),s,flags=re.M)
s=s.replace("'ROOT-unit-row-degree-controls-plan-v1'","'ROOT-unit-row-global-engine-plan-v1'")
s=s.replace("plan['purpose'] == 'unit-row-local-degree-controls'", "plan['purpose'] in ('unit-row-global-engine-controls','unit-row-global-engine-search')")
s=s.replace("'unit-row-degree-controls-cold-Source-contract-v1'","'unit-row-global-engine-cold-Source-contract-v1'")
s=s.replace("'ROOT-unit-row-degree-controls-authorization-v1'","'ROOT-unit-row-global-engine-authorization-v1'")
a=s.index('    def checker_adapter(');b=s.index("    result_raw = canonical(",a)
replacement=r'''    def fallback_adapter(*,language,state,row,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original fallback epoch')
        return invoke_fn(modules['fallback'].open_fallback,(),{'language':private,
            'state':copy.deepcopy(state),'row':row,'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def certify_adapter(*,language,state,row,completion,checked_candidates,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private original completion-check epoch')
        return invoke_fn(modules['engine'].certify_by_current_cover,(),{
            'language':private,'state':copy.deepcopy(state),'row':row,
            'completion':copy.deepcopy(completion),'checked_candidates':copy.deepcopy(checked_candidates),
            'degree_proposer':proposer_adapter,'semantics':modules['degree_checker'],'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def engine_factory(*,initial_state=None,degree_proposer=proposer_adapter,
            fallback=fallback_adapter,certify_fallback=certify_adapter,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'private per-engine original semantics authority')
        # Construction/methods/cursor iteration remain inside the surrounding
        # guarded endpoint. No per-method or per-yield Source seal is claimed.
        return modules['engine'].LazyUnitRowEngine(language=private,
            degree_proposer=degree_proposer,semantics=modules['degree_checker'],
            fallback=fallback,certify_fallback=certify_fallback,tick=step,
            initial_state=copy.deepcopy(initial_state),maximum_nodes=128,maximum_events=2000)
    def scheduler_adapter(*,evidence,generations,tick):
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        return invoke_fn(modules['engine'].select_schedule,(),{
            'evidence':copy.deepcopy(evidence),'generations':copy.deepcopy(generations),'tick':step},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    def run_original_search():
        engine = engine_factory(initial_state=None,tick=tick)
        return engine.search()
    is_controls = plan['purpose'] == 'unit-row-global-engine-controls'
    if is_controls:
        payload = invoke_fn(modules['controls'].run_controls,(),{'language':fixture_language,
            'engine_factory':engine_factory,'degree_proposer':proposer_adapter,
            'fallback':fallback_adapter,'certify_fallback':certify_adapter,
            'scheduler':scheduler_adapter,'tick':tick},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        need(type(payload) is dict and payload['schema'] == 'unit-row-lazy-global-controls-v1'
            and payload['all_declared_cases_completed'] is True and type(payload['cases']) is list,
            'complete adversarial control record; scopes remain distinct')
    else:
        payload = invoke_fn(run_original_search,(),{},
            boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        need(type(payload) is dict and payload['schema'] == 'unit-row-lazy-global-search-result-v1'
            and payload['status'] in ('POINT_BOARD_PROPOSAL','EXHAUSTED','UNKNOWN')
            and payload['root_restored'] is True and payload['stack_restored'] is True,
            'fresh original-root search result, not an accepted proof')
'''
s=s[:a]+replacement+s[b:]
s=s.replace("'ROOT-unit-row-local-degree-control-result-v1'", "'ROOT-unit-row-global-engine-result-v1'")
s=s.replace("'controls':controls,'language_binding':decode(binding_raw)",
 "'purpose':plan['purpose'],'controls':payload if is_controls else None,\n        'search':None if is_controls else payload,'search_work_bounds':{'maximum_nodes':128,'maximum_events':2000},\n        'language_binding':decode(binding_raw)")
s=s.replace('degree-controls.json','engine-result.json')
s=s.replace("'ROOT-unit-row-degree-controls-response-body-v1'", "'ROOT-unit-row-global-engine-response-body-v1'")
s=s.replace("'ROOT-unit-row-degree-controls-final-observation-v1'", "'ROOT-unit-row-global-engine-final-observation-v1'")
s=s.replace('UNIT_ROW_DEGREE_CONTROLS_UNKNOWN: ','UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: ')
s=s.replace('whole bounded local control output','whole bounded global engine output')
old_ast,new_ast=ast.parse(old),ast.parse(s)
names=['need','canonical','raw_pin','unique','reject_constant','finite_float','decode','read_pinned',
 'load_module','write_new','anchor','same','invoke','cancel','all_function_anchors']
for name in names:
    first=next(n for n in old_ast.body if isinstance(n,ast.FunctionDef) and n.name==name)
    second=next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert ast.dump(first,include_attributes=False)==ast.dump(second,include_attributes=False)
out=HERE/'unit_row_global_engine_cold_v1.py'
compile(new_ast,str(out),'exec')
with out.open('x') as f:f.write(s)
sources=dict(fixed,intake=pin(out))
for ref in sources.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
review={'schema':'unit-row-global-engine-cold-typed-Source-review-v1','scope':'unit-row-global-engine-cold-Source',
 'source':sources['intake'],'sources':sources,'author_identity':'/root','reviewer_identity':'Actual distinct reviewer decides.',
 'source_contract':'Exact current raw contract capsule; no self hash.','source_only':True,'source_review_passed':'Actual reviewer decides.',
 'scientific_calls':0,'scientific_acceptance':False}
contract={'schema':'unit-row-global-engine-cold-Source-contract-v1','scope':'unit-row-global-engine-cold-Source',
 'author_identity':'/root','source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'sources':sources,'inputs':inputs,'limits':limits,'resource_rule':'single-owned-process-native-terminal-v1','Review_ABI':review,
 'endpoints':{'unit-row-global-engine-controls':'Original-language adversarial controls, labeled interrupted cursor seams and separate synthetic generation calibration.',
 'unit-row-global-engine-search':'Fresh original right-two initial state, target24/all original rules. No word/donor/library. Named ROW-TIE+ALL24 rebind variant; work128nodes/2000events, no false exhaustion from caps.'},
 'provenance':{'parent':pin(parent),'unchanged15_helpers':names,'handoffs':handoffs,'main_inverse_AST_exact':False,
 'main_changes':'Adds engine/fallback adapters and a second declared endpoint. Reuses native resource, Source guard, full data binding, wire/output and external meter/once lifecycle.'},
 'authority_scope':['Original full declaration/profile reconstructed separately for each raw proposer call, fallback cursor and completion-check call, plus a private original language per engine.',
 'Engine independent semantics uses its per-engine private original language; proposer/cursor are separate objects and cannot substitute their language objects into that authority.',
 'Same native tick precedes injected control tick. Class construction, methods and cursor iteration stay inside the surrounding guarded endpoint; no per-method/yield Source-seal claim.',
 'Known reviewed synchronous Sources, not hostile Python/OS/VM assurance. No new custody framework.',
 'All strong proof/point/trajectory/graph/RL/resource acceptance remains false; Root separately qualifies complete saved output and native gates.',
 'ALL24 context invalidation does not retain unaffected domains, an explicit master4 conformance gap. No full reference incremental-conformance or acceleration claim.'],
 'runtime_and_failure':'Same20s native launch→postprobe/512MiB, internal500MiB reserve, failure55/owned60/caller90+1. Timeout/partial output never accepted. Single owned process; B=T. External meter/once unchanged.'}
cr=save('Source-contract-v1.json',contract)
static=save('author-static-evidence-v1.json',{'schema':'ROOT-global-cold-author-static-v1','source':sources['intake'],
 'checks':{'helper_AST_exact':15,'whole_Source9_AST_compile_only':True,'original_input2_unchanged':True,
 'original_limits_unchanged':True,'two_endpoints_explicit':True,'old_carrier_and_checker_adapters_removed':True},
 'scientific_calls':0,'scientific_acceptance':False,'source_only':True})
hr=save('handoff-v1.json',{'schema':'ROOT-unit-row-global-engine-cold-handoff-v1','source':sources['intake'],
 'source_contract':cr,'static_evidence':static,'sources':sources,'inputs':inputs,'limits':limits,
 'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'scope':contract['scope']})
print(json.dumps({'source':sources['intake'],'source_contract':cr,'handoff':hr}))
