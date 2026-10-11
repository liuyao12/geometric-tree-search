"""Fresh exact commutativity union; only accepted closed theorem transfers."""
import copy,gzip,json
from pathlib import Path
from external_prover_inputs import canonical,sha,Symbols
from external_left_successor_inputs import schema,target_body,validate_theory,free

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/external-commutativity-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def build():
    plan=load(DOC/'commutativity_plan.json');spec=plan['case'];validate_theory(spec['theory'])
    variables,body=target_body(spec['target']);schemas={};occurrences=[]
    def collect(c,where):
        f=schema(c['template'],c['variable'])
        if f!=c['formula']:raise ValueError('explicit induction/parameter closure mismatch')
        key=canonical(f)
        schemas.setdefault(key,dict(variable=c['variable'],template=c['template'],formula=f,parameters=sorted(free(c['template'])-{c['variable']}),origins=[]))['origins'].append(where)
        occurrences.append(dict(variable=c['variable'],origin=where,formula_sha256=sha(canonical(f))))
    # Complete new target alternatives and every induction occurrence in every
    # full lane, not a selected target proof, retained path, or preferred variable.
    for lane in plan['lanes']:
        core=load(DOC/('commutativity_'+lane['id'].replace('-','_')+'_full_core.json.gz'))
        if core['spec']!=spec or core['variables']!=variables:raise ValueError('exact complete target grammar')
        declared=[r for r in core['rules'] if r['description']['operation']=='induction']
        if sorted(r['description']['variable'] for r in declared)!=sorted(variables):raise ValueError('all target-variable induction alternatives')
        for d in core['definitions']:
            for i,c in enumerate(d['proof']):
                if c['rule']=='induction':collect(c,dict(kind='complete-commutativity-definition',lane=lane['id'],name=d['name'],line=i))
    # Retain the whole earlier declared union, including the unused alternative
    # left-successor variable; no source winning path chooses this union.
    prior=load(ROOT/'.gcts-active/external-left-successor-20261011/inventory.json')
    if prior['spec']['theory']!=spec['theory'] or len(prior['schemas'])!=3:raise ValueError('exact prior declared union')
    for c in prior['schemas']:collect(c,dict(kind='complete-earlier-declared-union',id=c['id'],origins=c['origins']))
    sources=[ROOT/'.gcts-active/induction-receptors-20261011/compaction-native.json.gz',ROOT/'.gcts-active/left-successor-20261011/workspace-native/native.json.gz']
    lemmas=[]
    for i,(s,p) in enumerate(zip(plan['lemma_sources'],sources)):
        q=load(p)[1];r=q['request']
        if q['result']['status']!='accepted' or q['request_sha256']!=s['request_sha256'] or sha(canonical(r))!=s['request_sha256'] or r['theory']!=spec['theory'] or r['blocks']:raise ValueError('exact accepted primitive theorem transfer')
        for j,c in enumerate(r['proof']):
            if c['rule']=='induction':collect(c,dict(kind='accepted-primitive-theorem',request_sha256=s['request_sha256'],line=j))
        deps=sorted({sha(canonical(c['formula'])) for c in r['proof'] if c['rule']=='induction'})
        lemmas.append(dict(id='l'+str(i),original_name=s['name'],formula=r['target'],native_request=r,native_record=q,native_source_path=str(p.relative_to(ROOT)),discovery=s['discovery'],induction_dependencies=deps))
    if len(schemas)!=5:raise ValueError('complete target plus prior declared union must have five instances')
    ordered=[dict(id='ind'+str(i),**schemas[k],formula_sha256=sha(k)) for i,k in enumerate(sorted(schemas))]
    return dict(spec=spec,schemas=ordered,lemmas=lemmas,induction_occurrences=occurrences,
        scope='Five-instance union in every target lane: two complete commutativity templates, two complete earlier left-successor templates, and zero-left. This exceeds each native no-transfer finite grammar. Only two already accepted primitive theorem conclusions are optional lemma inputs. No unadmitted local interface or target proof path is supplied.')
def encode(bundle,kind):
    spec=bundle['spec'];sy=Symbols(spec['theory']);entries=[]
    for i,(n,f) in enumerate(sorted(spec['theory']['axioms'].items())):entries.append(dict(name='a'+str(i),role='axiom',original_name=n,formula=f))
    instances=bundle['schemas']
    if kind.startswith('setup-'):
        lemma=bundle['lemmas'][int(kind.split('-')[1])]
        instances=[s for s in instances if s['formula_sha256'] in lemma['induction_dependencies']]
    for s in instances:entries.append(dict(name=s['id'],role='axiom',original_name='explicit finite induction '+s['variable'],formula=s['formula']))
    if kind in ('zero-left','both'):
        for e in bundle['lemmas'][:1 if kind=='zero-left' else 2]:entries.append(dict(name=e['id'],role='lemma',original_name=e['original_name'],formula=e['formula'],native_request_sha256=sha(canonical(e['native_request']))))
    target=lemma['formula'] if kind.startswith('setup-') else spec['target']
    entries.append(dict(name='goal',role='conjecture',original_name='transferred lemma setup' if kind.startswith('setup-') else 'unchanged commutativity target',formula=target))
    text='% Exact finite induction export; no target proof sequence.\n'+'\n'.join('fof('+e['name']+','+e['role']+','+sy.formula(e['formula'])+').' for e in entries)+'\n'
    mapping=dict(case=spec['id'],lane=kind,functions=sy.functions,predicates=sy.predicates,function_arities={sy.functions[n]:a for n,a in spec['theory']['functions'].items()},predicate_arities={},entries=entries)
    return text,mapping
