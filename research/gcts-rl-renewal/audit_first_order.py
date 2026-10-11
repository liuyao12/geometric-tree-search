"""Independent first-order syntax, full point inventory, trees and native replay.

Does not import the new producer, compiler, case registry, worker or search.
Capture-avoiding substitution is implemented here separately. Existing literal
point/domain and policy auditors verify every search node and fallback choice.
"""
import copy,gzip,hashlib,itertools,json,math,subprocess,time
from pathlib import Path
from audit_tree_kernel import need,packed
from audit_semantic_inventory import same,verify_model,encode,replay_native
from audit_prefix_failure_markings import extended_tree
from audit_certificate_boundary import pin,sha
from audit_proof_boundary import code_bytes,PINNED_PROGRAM,PINNED_MICRO

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/first-order-20261011';TMP=Path('/private/tmp/gcts-first-order-audit-20261011')

def term_vars(t):
    out=set();pending=[t]
    while pending:
        a=pending.pop()
        if a[0]=='var':out.add(a[1])
        else:pending.extend(a[2])
    return out
def free(a,all_names=False):
    if a[0]=='all':return free(a[2],all_names)|{a[1]} if all_names else free(a[2])- {a[1]}
    if a[0]=='pred':return set().union(*(term_vars(t) for t in a[2]))
    if a[0]=='eq':return term_vars(a[1])|term_vars(a[2])
    if a[0]=='bot':return set()
    return set().union(*(free(b,all_names) for b in a[1:]))
def subst(a,x,t):
    def replace(s):return copy.deepcopy(t) if s==['var',x] else s if s[0]=='var' else ['fun',s[1],[replace(u) for u in s[2]]]
    k=a[0]
    if k=='pred':return [k,a[1],[replace(s) for s in a[2]]]
    if k=='eq':return [k,replace(a[1]),replace(a[2])]
    if k=='bot':return a
    if k=='all':
        y,b=a[1:]
        if x==y or x not in free(b):return a
        if y in term_vars(t):
            used=free(b,True)|term_vars(t)|{x,y};n=0
            while 'fresh'+str(n) in used:n+=1
            z='fresh'+str(n);b=subst(b,y,['var',z]);y=z
        return [k,y,subst(b,x,t)]
    return [k,*[subst(b,x,t) for b in a[1:]]]

def syntax(spec):
    formulas={};terms={};names=set();pending=list(spec['theory']['axioms'].values())+[spec['target']]
    while pending:
        a=pending.pop();formulas[packed(a)]=a;names.update(free(a,True))
        if a[0]=='all':pending.append(a[2])
        elif a[0] in ('imp','and','or','not'):pending.extend(a[1:])
        elif a[0] in ('pred','eq'):
            ts=list(a[2] if a[0]=='pred' else a[1:])
            while ts:
                t=ts.pop();terms[packed(t)]=t
                if t[0]=='fun':ts.extend(t[2])
    pool=[terms[k] for k in sorted(terms) if term_vars(terms[k])<=free(spec['target'])]
    closed=[t for t in pool if not term_vars(t)];schemes={}
    def add(a):
        queue=[a]
        while queue:
            p=queue.pop();formulas[packed(p)]=p;names.update(free(p,True))
            if p[0]=='all':queue.append(p[2])
            elif p[0] in ('imp','and','or','not'):queue.extend(p[1:])
    for _ in range(spec.get('instantiation_rounds',2)):
        universals=[a for _,a in sorted(formulas.items()) if a[0]=='all']
        for u,t in itertools.product(universals,pool):
            c=dict(rule='instantiate',formula=['imp',u,subst(u[2],u[1],t)],universal=u,term=t)
            schemes[packed(c)]=c;add(c['formula'])
    n=0
    while 'hole'+str(n) in names:n+=1
    hole='hole'+str(n);templates={};closed_keys={packed(t) for t in closed}
    pairs={packed(a[1:]):a[1:] for a in formulas.values() if a[0]=='eq' and all(packed(t) in closed_keys for t in a[1:])}
    for a in list(formulas.values()):
        if a[0] not in ('pred','eq'):continue
        args=a[2] if a[0]=='pred' else a[1:]
        for t in closed:
            replaced=False
            def abstract(u):
                nonlocal replaced
                if u==t:replaced=True;return ['var',hole]
                return u if u[0]=='var' else ['fun',u[1],[abstract(v) for v in u[2]]]
            result=[abstract(u) for u in args]
            if replaced:
                p=['pred',a[1],result] if a[0]=='pred' else ['eq',*result]
                templates[packed(p)]=p
    for _,p in sorted(templates.items()):
        for _,(s,t) in sorted(pairs.items()):
            c=dict(rule='eq_subst',formula=['imp',['eq',s,t],['imp',subst(p,hole,s),subst(p,hole,t)]],variable=hole,template=p,left=s,right=t)
            schemes[packed(c)]=c;add(c['formula'])
    return dict(basis=[formulas[k] for k in sorted(formulas)],variables=sorted(names),terms=pool,
        equality_terms=closed,equality_pairs=[pairs[k] for k in sorted(pairs)],template_variable=hole,
        templates=[templates[k] for k in sorted(templates)],schemes=[schemes[k] for k in sorted(schemes)],rounds=spec.get('instantiation_rounds',2))

def domains(spec,catalog,j):
    rows=[]
    for f in [spec['target']] if j+1==spec['length'] else catalog['basis']:
        rows.extend(dict(rule='axiom',formula=f,name=n) for n in sorted(spec['theory']['axioms']))
        rows.extend(dict(rule='generalize',formula=f,variable=x,source=i) for x in catalog['variables'] for i in range(j))
        rows.extend(dict(rule='mp',formula=f,antecedent=i,implication=k) for i,k in itertools.product(range(j),repeat=2))
        rows.extend(dict(rule=r,formula=f) for r in ('refl','tautology'))
    rows.extend(c for c in catalog['schemes'] if j+1<spec['length'] or c['formula']==spec['target'])
    return sorted(rows,key=lambda c:(c['rule'],packed(c['formula']),packed(c)))

def compilation(spec,compiled,records):
    catalog=syntax(spec);need(same(compiled['catalog'],catalog),'independent finite first-order syntax closure')
    commands=[(dict(rule='tautology',formula=['imp',['bot'],['bot']]),'first_order_theory_admission')]
    commands += [(dict(rule='tautology',formula=f),'first_order_tautology') for f in catalog['basis']]
    commands += [(c,'first_order_scheme') for c in catalog['schemes']]
    taut=[];schemes=[];requests={}
    for k,q in enumerate(compiled['queries']):
        c,purpose=commands[k];rec=records[q]
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[c],target=c['formula'])
        need(same(request,rec['request']) and rec['purpose']==purpose,'exact native compiler query')
        requests[q]=request;status=rec['result']['status']
        if k==0:need(q==compiled['theory_query'],'theory admission binding')
        if status=='accepted' and k:
            (taut if purpose=='first_order_tautology' else schemes).append(c['formula'] if purpose=='first_order_tautology' else c)
    if compiled['status']=='complete':
        need(len(commands)==len(compiled['queries']) and all(records[q]['result']['status'] in ('accepted','rejected') for q in compiled['queries']) and records[compiled['theory_query']]['result']['status']=='accepted','complete resolved compiler domain')
        need(same(compiled['basis'],catalog['basis']) and compiled['variables']==catalog['variables'] and same(compiled['tautologies'],taut) and same(compiled['admitted_schemes'],schemes),'all and only native-admitted guards')
    return requests

def rebuild(spec,compiled):
    catalog=syntax(spec);need(same(catalog,compiled['catalog']),'new syntax identity')
    ps=[];bad=[];ds=[];tauts={packed(f) for f in compiled['tautologies']};schemes={packed(c) for c in compiled['admitted_schemes']}
    def add(k,c,req):
        j,role=k[:2];entries=encode(j,'command',c)+encode(j,'formula',c['formula'])+[((4*j+2,90),0)]+[e for i,a in req for e in encode(i,'formula',a)];marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:bad.append(dict(key=k,reason='internally unequal markings'));return
            marks[p]=v
        ps.append(dict(key=k,occupancy=[((4*j,role),12)],marks=sorted(marks.items()),slot=j,kind='command' if role==0 else 'guard',command=c,requirements=req))
    for j in range(spec['length']):
        rows=domains(spec,catalog,j);ds.append(rows)
        for k,c in enumerate(rows):
            add((j,0,k,0),c,[]);f=c['formula'];r=c['rule']
            if r=='mp':
                for v,imp in enumerate(catalog['basis']):
                    if imp[0]=='imp' and imp[2]==f:add((j,1,k,v),c,[(c['antecedent'],imp[1]),(c['implication'],imp)])
            elif r=='generalize':
                if f[0]=='all' and f[1]==c['variable']:add((j,1,k,0),c,[(c['source'],f[2])])
            elif (r=='axiom' and spec['theory']['axioms'][c['name']]==f or
                  r=='refl' and f[0]=='eq' and f[1]==f[2] or
                  r=='tautology' and packed(f) in tauts or r in ('instantiate','eq_subst') and packed(c) in schemes):add((j,1,k,0),c,[])
    return dict(domains=ds,command_counts=list(map(len,ds)),arity=0,mode_ids={},complete_words=math.prod(map(len,ds)),
        placements=sorted(ps,key=lambda c:c['key']),conflicts=bad,roots=[(4*j,r) for j in range(spec['length']) for r in (0,1)],
        initial_marks=encode(spec['length']-1,'formula',spec['target']))

def model_binding(spec,compiled,record):
    rebuilt=rebuild(spec,compiled);verify_model(record,rebuilt)
    for k in ('complete_words','initial_marks'):need(same(record[k],rebuilt[k]),'complete model '+k)
    return rebuilt

def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());policy_bytes=(DOC/'semantic-inventory-policy-001.json').read_bytes();need(hashlib.sha256(policy_bytes).hexdigest()==plan['policy_sha256'],'frozen reused policy');policy=json.loads(policy_bytes)
    for f,h in plan['source_sha256'].items():need(sha(ROOT/f)==h,'predeclared frozen source '+f)
    records=json.loads(gzip.decompress((OUT/'native-records.json.gz').read_bytes()));requests={};totals=dict(nodes=0,events=0,hints=0,proofs=0);cache={};cases=[]
    for spec in plan['cases']:
        raw=json.loads(gzip.decompress((OUT/(spec['id']+'.json.gz')).read_bytes()));need(same(raw['case'],spec),'predeclared assertion and boundary')
        requests.update(compilation(spec,raw['compiled'],records));need(raw['compiled']['status']=='complete','this pilot requires complete compilation')
        rebuilt=model_binding(spec,raw['compiled'],raw['model']);seen=set()
        for obs in raw['observations']:
            need((obs['mode'],obs['repetition']) not in seen,'fresh observation uniqueness');seen.add((obs['mode'],obs['repetition']))
            checked=extended_tree(spec,rebuilt,obs['search'],[],policy['weights'] if obs['mode']=='learned' else None,rebuilt['initial_marks'])
            for k in ('nodes','events','hints'):totals[k]+=checked[k]
            proof=obs['search']['proof'];qid=obs['native_query']
            if proof is None:need(qid is None and not obs['cached_native_acceptance'],'unknown has no proof acceptance');continue
            request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=proof,target=spec['target']);key=pin(request)
            need(qid is not None and same(records[qid]['request'],request) and records[qid]['result']['status']=='accepted','marking-erased whole native proof')
            if obs['cached_native_acceptance']:need(cache.get(key)==qid,'only earlier exact whole acceptance reused')
            else:need(qid not in requests and key not in cache and records[qid]['purpose']=='first_order_final','fresh distinct native proof');requests[qid]=request;cache[key]=qid
            totals['proofs']+=1
        need(seen=={(m,r) for m in plan['modes'] for r in plan['repetitions']},'all predeclared fresh process lanes')
        cases.append(dict(id=spec['id'],syntax_formulas=len(raw['compiled']['basis']),schemes=len(raw['compiled']['admitted_schemes']),placements=len(rebuilt['placements'])))
    need(set(requests)==set(range(len(records))),'every native computation bound')
    TMP.mkdir(parents=True,exist_ok=True)
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));old=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and old['program_sha256']==PINNED_PROGRAM,'unchanged primitive checker')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro))
    import audit_semantic_inventory as native_audit
    native_audit.TMP=TMP;steps,accepted=replay_native(records,requests,micro,old['cases'][0]['initial'])
    result=dict(status='passed',version='first-order-audit-001',cases=cases,observations=len(plan['cases'])*len(plan['modes'])*len(plan['repetitions']),native_queries=len(records),micro_steps=steps,accepted_requests=len(accepted),seconds=time.perf_counter()-began,**totals)
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
