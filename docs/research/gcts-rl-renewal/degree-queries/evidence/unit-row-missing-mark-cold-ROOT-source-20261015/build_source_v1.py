"""Source/AST assembly only. The existing cold main gains a tiny carrier adapter."""
import ast
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def save(name,value):
    p=HERE/name
    with p.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
parent=BASE/'unit-row-degree-cold-ROOT-source-20261015/unit_row_degree_controls_cold_v1.py'
assert pin(parent)['sha256']=='212ea04d6ff212256f1b0195ead617a4e6b3eccdd775874387e0d1848a157c1d'
raw=parent.read_text();ptree=ast.parse(raw)
old_contract=read(BASE/'unit-row-degree-cold-ROOT-source-20261015/Source-contract-v1.json')
handoffs={
    'proposer':BASE/'unit-row-missing-mark-degree-source-20261015/handoff-v1.json',
    'degree_checker':BASE/'unit-row-missing-mark-checker-source-20261015/handoff-v2.json',
    'controls':BASE/'unit-row-missing-mark-controls-source-20261015/handoff-v2.json'}
fixed={k:old_contract['sources'][k] for k in ('clean_support','kernel','membership')}
for role,p in handoffs.items():fixed[role]=read(p)['source']
inputs=old_contract['inputs']
for ref in [*fixed.values(),*inputs.values()]:assert pin(Path(ref['path']))==ref
assigns={n.targets[0].id:n for n in ptree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
raw=raw.replace(ast.get_source_segment(raw,assigns['FIXED']),'FIXED='+repr(fixed),1)
raw=raw.replace("VERSION='unit-row-degree-controls-cold-v1'","VERSION='unit-row-missing-mark-degree-controls-cold-v1'",1)
raw=raw.replace("SCOPE='unit-row-degree-controls-cold-Source'","SCOPE='unit-row-missing-mark-degree-controls-cold-Source'",1)
anchor="    controls = invoke_fn(modules['controls'].run_controls,(),{'language':fixture_language,\n        'proposer':proposer_adapter,'checker':checker_adapter,'tick':tick},"
assert raw.count(anchor)==1
adapter='''    def carrier_adapter(*,language,maximum_nodes,tick):
        need(type(maximum_nodes) is int and maximum_nodes in (1,2), 'direct control carrier bounds1or2 only')
        injected_tick = tick
        def step():
            native_tick()
            injected_tick()
        private = fresh_language(step)
        need(canonical(private.binding) == binding_raw, 'fresh private control carrier epoch unchanged')
        values = []
        for formula in modules['proposer'].iter_bounded_formulas(
                language=private,maximum_nodes=maximum_nodes,tick=step):
            step()
            if len(values) >= 1000:
                raise TimeoutError('direct tiny control carrier output incomplete')
            values.append(copy.deepcopy(formula))
        return values
'''
replacement=adapter+anchor.replace("'checker':checker_adapter,'tick':tick}","'checker':checker_adapter,'carrier':carrier_adapter,'tick':tick}")
raw=raw.replace(anchor,replacement,1)
path=HERE/'missing_mark_degree_controls_cold_v1.py'
with path.open('x') as f:f.write(raw)
tree=ast.parse(raw);compile(tree,str(path),'exec')
old_defs={n.name:n for n in ptree.body if isinstance(n,ast.FunctionDef)}
new_defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
helpers=old_contract['provenance']['copied15_helpers']
for name in helpers:assert ast.dump(new_defs[name],include_attributes=False)==ast.dump(old_defs[name],include_attributes=False)
projected=copy.deepcopy(new_defs['main'])
projected.body=[n for n in projected.body if not isinstance(n,ast.FunctionDef) or n.name!='carrier_adapter']
for n in ast.walk(projected):
    if isinstance(n,ast.Dict):
        pairs=[(k,v) for k,v in zip(n.keys,n.values) if not isinstance(k,ast.Constant) or k.value!='carrier']
        n.keys=[k for k,v in pairs];n.values=[v for k,v in pairs]
assert ast.dump(projected,include_attributes=False)==ast.dump(old_defs['main'],include_attributes=False)
sources=dict(intake=pin(path),**fixed)
scope='unit-row-missing-mark-degree-controls-cold-Source'
contract={'schema':'unit-row-degree-controls-cold-Source-contract-v1','scope':scope,'author_identity':'/root',
    'sources':sources,'inputs':inputs,'limits':old_contract['limits'],'resource_rule':old_contract['resource_rule'],
    'source_only':True,'scientific_calls':0,'scientific_acceptance':False,
    'endpoint':'New missing-mark local-degree controls plus fresh rerun of retained mechanics; not proof discovery or GCTS search.',
    'provenance':{'parent_intake':pin(parent),'copied15_helpers':helpers,'main_inverse_AST_exact':True,
        'main_only_additions':'carrier_adapter nested function and carrier keyword passed to controls; operational plan/wire/native helpers unchanged.',
        'handoffs':{k:pin(p) for k,p in handoffs.items()}},
    'scope_limits':old_contract['scope_limits']+[
        'Direct public-carrier control wrapper restricts only requested test outputs to bounds1/2 and <=1000 entries; no change to full profile44 generator or checker relation.',
        'Tiny carrier EOF comparison is not a full formula registry count. Full Source/node/clock/callback errors remain UNKNOWN/failure.'],
    'Review_ABI':{'schema':'unit-row-degree-controls-cold-typed-Source-review-v1','scope':scope,'author_identity':'/root',
        'source':sources['intake'],'sources':sources,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,
        'reviewer_identity':'Actual reviewer decides; Root author disclosure separate.',
        'source_review_passed':'Actual reviewer decides.','source_contract':'Exact complete raw contract capsule; no self hash.'}}
cref=save('Source-contract-v1.json',contract)
static=save('author-static-evidence-v1.json',{'schema':'missing-mark-degree-cold-author-static-v1',
    'source':sources['intake'],'helpers_AST_exact':helpers,'main_inverse_AST_exact':True,'AST_compile_only':True,
    'scientific_calls':0,'scientific_acceptance':False,'independent_review_pending':True})
href=save('handoff-v1.json',{'schema':'missing-mark-degree-cold-Source-handoff-v1',
    'source':sources['intake'],'sources':sources,'inputs':inputs,'source_contract':cref,'static_evidence':static,
    'status':'FROZEN_SOURCE_ONLY_DISTINCT_REVIEW_PENDING'})
print(json.dumps({'handoff':href,'source':sources['intake'],'source_contract':cref},sort_keys=True))
