"""Exact union-control inputs; no target proof or preferred induction variable."""
import copy,gzip,json,pathlib,time
from external_prover_inputs import canonical,sha,Symbols,lemma_formula

ROOT=pathlib.Path(__file__).resolve().parents[2]
SOURCE=ROOT/'.gcts-active/left-successor-20261011'
OUT=ROOT/'.gcts-active/external-left-successor-20261011'
LANES=('without-transfer','with-searched-zero-left')
GATES={'audit.json':'passed_preparation_audit_only','compaction-preparation-audit.json':'passed_compaction_preparation_audit_only','reachability-audit.json':'passed_finite_grammar_structural_pruning','pilot-audit.json':'passed_preparation_native_replay_only','admission-audit.json':'passed_complete_reachable_native_admission'}
PINNED={'plan.json':'203ac0401912bb62335183b44118b5ca2a821d91eee737ab8663e848bc1eb7e7','audit.json':'01868fb6c9ec1a4cecbd768e09e8b2c75aafed72c481f4662442cefc32bd8fd2','compaction-preparation-audit.json':'019598ec78d305433450aa085732184dadbbaf1e6446c25edd6f8f6cb3ae4673','reachability-audit.json':'07cc29f5f89ec71ecdcde23638703aae931930a51e85bca421f98677b2919561','pilot-audit.json':'51c732aad3e8952e804654cc403cb841d87d7e65e70e702210057f5d4bbc2c32','admission-audit.json':'0accfbfb3cfc363e4a6d2af89d86380dab1ad6937470cb609d5ab908f68c1f04','without-transfer-admission.json':'6ae77d7a918da61dd2738be23e7871065299a3ec8c93f6bf458f8090e2de537a','with-searched-zero-left-admission.json':'bd8cb18c7cdf24d9f157a686347e0dc859410fe427ea50541130310ad0076b5d','without-transfer-reachable-core.json.gz':'f3ed5ccb2086c4a9366392362827f82c4131c0552ce7fa8caa2805625ab5ef20','with-searched-zero-left-reachable-core.json.gz':'af6d97f07d0b3bcd20495e3c83836866ff873b4b7b202a603738907ae0557332','transfer.json':'bf34df323bce8870a59f7196c13f4243da96085ee3fb24e2b4ce1647f3486580'}

def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def free(f,bound=frozenset()):
    h=f[0]
    if h=='var':return set() if f[1] in bound else {f[1]}
    if h in ('fun','pred'):return set().union(*(free(a,bound) for a in f[2]))
    if h in ('all','forall','exists'):return free(f[2],bound|{f[1]})
    if h in ('top','bot'):return set()
    if h in ('eq','and','or','imp','not'):return set().union(*(free(a,bound) for a in f[1:]))
    raise ValueError('unsupported native formula')
def close(f,variables=None):
    f=copy.deepcopy(f)
    for v in reversed(sorted(free(f)) if variables is None else variables):f=['all',v,f]
    return f
def replace(f,x,t):
    # The declared template is an equation of first-order terms, with no binders.
    if f[0]=='var':return copy.deepcopy(t if f[1]==x else f)
    if f[0]=='fun':return ['fun',f[1],[replace(a,x,t) for a in f[2]]]
    if f[0]=='eq':return ['eq',replace(f[1],x,t),replace(f[2],x,t)]
    raise ValueError('only declared equational induction predicates supported')
def schema(template,x):
    if template[0]!='eq' or x not in free(template):raise ValueError('unsupported/vacuous induction template')
    p=copy.deepcopy(template);base=replace(p,x,['fun','zero',[]]);step=['all',x,['imp',p,replace(p,x,['fun','succ',[['var',x]]])]]
    return close(['imp',['and',base,step],['all',x,p]],sorted(free(p)-{x}))
def validate_theory(theory):
    if set(theory)!={'functions','predicates','axioms','schemas'} or theory['functions']!={'zero':0,'succ':1,'add':2} or theory['predicates'] or theory['schemas']!=['nat-induction']:raise ValueError('unsupported exact arithmetic theory')
    if any(type(a) is not int for a in theory['functions'].values()):raise ValueError('function arities must be integers, not booleans')
    if any(free(f) for f in theory['axioms'].values()):raise ValueError('axioms must be explicitly closed')
def target_body(target):
    variables=[];body=target
    while body[0]=='all':variables.append(body[1]);body=body[2]
    if body[0]!='eq' or len(set(variables))!=len(variables) or free(body)!=set(variables):raise ValueError('closed distinct target variables and equational predicate required')
    return variables,body

def snapshot():
    OUT.mkdir(parents=True,exist_ok=True);began=time.perf_counter();names=['plan.json','summary.json','audit.json','audit-plan.json','compaction-preparation.json','compaction-preparation-audit.json','reachability-summary.json','reachability-audit.json','transfer.json','admission-plan.json','admission-summary.json','pilot-audit.json','admission-audit.json','pilot-native.json.gz','admission-native.json.gz']
    for lane in LANES:names += [lane+suffix for suffix in ('-core.json.gz','-compact-core.json.gz','-primitive.jsonl.gz','-reachability.json.gz','-reachable-core.json.gz','-admission.json')]
    snap=OUT/'snapshot';snap.mkdir();manifest=[]
    for name in names:
        raw=(SOURCE/name).read_bytes()
        if name in PINNED and sha(raw)!=PINNED[name]:raise ValueError('stable source input changed '+name)
        (snap/name).write_bytes(raw);manifest.append(dict(name=name,sha256=sha(raw),bytes=len(raw)))
    prior=ROOT/'.gcts-active/induction-receptors-20261011';(snap/'prior-zero-left').mkdir()
    for name in ('compaction-native.json.gz','compaction-plan.json','compaction-audit.json','recovery-audit.json','attempt-01/audit.json'):
        raw=(prior/name).read_bytes();destination=snap/'prior-zero-left'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw);manifest.append(dict(name=str(destination.relative_to(snap)),sha256=sha(raw),bytes=len(raw)))
    for name,status in GATES.items():
        if load(snap/name)['status']!=status:raise ValueError('native preparation/admission replay gate incomplete '+name)
    dump(OUT/'snapshot.json',dict(status='frozen_exact_preparation_pruning_and_native_admission_inputs',files=manifest,seconds=time.perf_counter()-began));return snap

def inventory(snap):
    began=time.perf_counter();base=load(snap/'plan.json');spec=base['case'];validate_theory(spec['theory']);variables,body=target_body(spec['target']);schemas={};occurrences=[];streams=[]
    def collect(command,where):
        x=command['variable'];expected=schema(command['template'],x)
        if expected!=command['formula']:raise ValueError('mechanical schema/parameter closure differs from native command')
        key=canonical(expected)
        schemas.setdefault(key,dict(variable=x,template=command['template'],formula=expected,parameters=sorted(free(command['template'])-{x}),origins=[]))['origins'].append(where)
        occurrences.append(dict(variable=x,where=where))
    for lane in LANES:
        c=load(snap/(lane+'-core.json.gz'))
        if c['spec']!=spec or c['variables']!=variables:raise ValueError('same complete declared theory/target')
        for d in c['definitions']:
            for i,p in enumerate(d['proof']):
                if p['rule']=='induction':collect(p,dict(lane=lane,source='complete-definition',name=d['name'],line=i))
        digest=__import__('hashlib').sha256();counts={};diagnostic_ind=[]
        for i,word in enumerate(gzip.open(snap/(lane+'-primitive.jsonl.gz'),'rb')):
            digest.update(word);command=json.loads(word);counts[command['rule']]=counts.get(command['rule'],0)+1
            if command['rule']=='induction':collect(command,dict(lane=lane,source='complete-primitive-stream',line=i));diagnostic_ind.append(command['variable'])
        measured=next(r for r in load(snap/'summary.json')['variants'] if r['lane']==lane)
        if counts!=measured['primitive_counts'] or digest.hexdigest()!=measured['primitive_stream_sha256'] or sorted(diagnostic_ind)!=sorted(variables):raise ValueError('complete primitive stream census/fingerprint/all induction alternatives')
        streams.append(dict(lane=lane,counts=counts,sha256=digest.hexdigest(),full_definitions=len(c['definitions']),full_interfaces=len(c['rules'])))
    for lane in LANES:
        c=load(snap/(lane+'-reachable-core.json.gz'))
        for d in c['definitions']:
            for i,p in enumerate(d['proof']):
                if p['rule']=='induction':collect(p,dict(lane=lane,source='native-admitted-definition',name=d['name'],line=i))
    if len(schemas)!=3:raise ValueError('complete target/transfer induction union has exactly three declared predicates')
    ordered=[dict(id='ind'+str(i),**schemas[k]) for i,k in enumerate(sorted(schemas))]
    by_formula={canonical(s['formula']):s['id'] for s in ordered};core=load(snap/'with-searched-zero-left-reachable-core.json.gz');registry=load(snap/'with-searched-zero-left-admission.json');pilot=load(snap/'pilot-native.json.gz');fresh=load(snap/'admission-native.json.gz');pa=load(snap/'pilot-audit.json');aa=load(snap/'admission-audit.json')
    if registry['status']!='native_accepted' or len(core['definitions'])!=24 or len(registry['definitions'])!=24 or len(pilot)!=16 or len(fresh)!=20 or aa['complete_union_definitions']!=24 or aa['reused_exact_queries']!=4:raise ValueError('entire native admitted union/replay census')
    for records,audits in [(pilot,pa['queries']),(fresh,aa['fresh_queries'])]:
        if len(records)!=len(audits):raise ValueError('every native computation audited')
        for j,(q,a) in enumerate(zip(records,audits)):
            matched=a.get('whole_input_output_matched',a.get('complete_input_output_sha256_matched'))
            if q['id']!=j or a['query']!=j or q['result']['status']!=a['status'] or q['result']['micro_steps']!=a['micro_steps'] or not matched or sha(canonical(q['request']))!=q['request_sha256']:raise ValueError('exact whole native replay status/request/step binding')
    entries=[];by_name={d['name']:d for d in core['definitions']};summary={a['name']:a for a in registry['definitions']}
    for i,d in enumerate(core['definitions']):
        if registry['complete_definition_sha256'].get(d['name'])!=sha(canonical(d)):raise ValueError('exact actual admitted definition bytes')
        a=summary[d['name']];records=pilot if a['source']=='pilot-exact-request' else fresh
        if a['source'] not in ('pilot-exact-request','fresh-native-request'):raise ValueError('unsupported native admission provenance')
        q=records[a['query']];taut=['imp',['bot'],['bot']];request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
        if q['request']!=request or q['request_sha256']!=a['request_sha256'] or a['status']!='accepted':raise ValueError('exact admitted interface/request binding')
        deps=sorted({p['name'] for p in d['proof'] if p['rule']=='axiom'});ind=sorted({by_formula[canonical(p['formula'])] for p in d['proof'] if p['rule']=='induction'})
        if any(n not in spec['theory']['axioms'] for n in deps) or any(p['rule']=='block' for p in d['proof']):raise ValueError('unsupported hidden dependency')
        f=lemma_formula(d);closure_variables=sorted(free(f));f=close(f)
        entries.append(dict(id='l'+str(i),original_name=d['name'],formula=f,universal_closure_variables=closure_variables,axiom_dependencies=deps,induction_dependencies=ind,definition=d,native_admission=a,native_request_sha256=q['request_sha256'],native_input_sha256=q['input_sha256'],native_output_sha256=q['output_sha256']))
    transfer=load(snap/'transfer.json');td=by_name[transfer['name']]
    if td['conclusion']!=transfer['conclusion'] or td['proof']!=transfer['proof'] or transfer['theory']!=spec['theory'] or transfer['origin']!='actually-searched-and-native-checked-zero-left-theorem':raise ValueError('actual searched source theorem transfer binding')
    compact=load(snap/'prior-zero-left/compaction-native.json.gz')[1]
    audit_names={'compaction-audit.json':'715b2b2464d78083dad1372a311e92ab46fb7836d253f99a9a5d68e007534b10','recovery-audit.json':'509e12e9f39f5e2c702f02afbe8c634ccf62ab4c59e998227a0088080484bcfe','attempt-01/audit.json':'82b1736ed1c19757cd47466627abc5546c9c2eecf5ddc5dd571ab600730fea10'}
    for name,want in audit_names.items():
        if sha((snap/'prior-zero-left'/name).read_bytes())!=want or load(snap/'prior-zero-left'/name)['status']!='passed':raise ValueError('authoritative passed source-theorem audits')
    if compact['result']['status']!='accepted' or compact['request_sha256']!=transfer['request_sha256'] or compact['request']['proof']!=transfer['proof'] or compact['request']['target']!=transfer['conclusion'] or compact['request']['theory']!=spec['theory']:raise ValueError('accepted actually searched source theorem request/proof/theory')
    return dict(status='complete_declared_union_not_yet_FOL_setup_checked',spec=spec,schemas=ordered,interfaces=entries,streams=streams,induction_occurrences=occurrences,native_queries_bound=36,native_audit_seconds=pa['seconds']+aa['seconds'],native_original_seconds=sum(q['seconds'] for q in pilot+fresh),source_theorem_native_binding=dict(request_sha256=compact['request_sha256'],proof_commands=len(compact['request']['proof']),status='accepted_and_passed_full_native_replay',prior_audits=audit_names),snapshot_sha256=sha((OUT/'snapshot.json').read_bytes()),seconds=time.perf_counter()-began,comparison_scope='Both external lanes receive the complete three-instance union. The native without-transfer grammar exposes two target-variable templates; the transferred actually searched zero-left proof contributes the third predicate. This union control has broader instance/search language than that native lane and is not an RL effect. All24 admitted formula interfaces, including the transferred theorem, are supplied to the library lane; no target proof sequence or preferred induction variable is supplied.')

def inputs(bundle,library):
    spec=bundle['spec'];sy=Symbols(spec['theory']);entries=[]
    for i,(n,f) in enumerate(sorted(spec['theory']['axioms'].items())):entries.append(dict(name='a'+str(i),role='axiom',original_name=n,formula=f))
    for s in bundle['schemas']:entries.append(dict(name=s['id'],role='axiom',original_name='complete declared induction union: '+s['variable'],formula=s['formula']))
    if library:
        for e in bundle['interfaces']:entries.append(dict(name=e['id'],role='lemma',original_name=e['original_name'],formula=e['formula'],native_admission=e['native_admission'],native_request_sha256=e['native_request_sha256']))
    entries.append(dict(name='goal',role='conjecture',original_name='target',formula=spec['target']))
    text='% Complete declared three-instance induction union; no target proof sequence.\n'+'\n'.join('fof('+e['name']+','+e['role']+','+sy.formula(e['formula'])+').' for e in entries)+'\n'
    mapping=dict(case=spec['id'],lane='union-theory-and-all24-admitted-interfaces' if library else 'union-theory-only',functions=sy.functions,predicates=sy.predicates,function_arities={sy.functions[n]:a for n,a in spec['theory']['functions'].items()},predicate_arities={},entries=entries)
    return text,mapping
