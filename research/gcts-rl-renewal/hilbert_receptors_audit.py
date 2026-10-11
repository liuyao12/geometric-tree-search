"""Independent sorted catalog, all point candidates/trees, and native replay.

Imports no Hilbert producer, case registry, worker, runner or search. Prior
literal audit routines check the complete graph and point-word correspondence.
Logical replay is confined to this audit, never used by the search.
"""
import collections,copy,gzip,itertools,json,math,subprocess,time
from pathlib import Path
from audit_first_order import domains,subst
from audit_semantic_inventory import need,packed,same,encode,closure
import audit_semantic_inventory as N
from audit_catalog_receptors import correspondence,check_tree
from audit_certificate_boundary import pin,sha
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';OUT=ROOT/'.gcts-active/hilbert-receptors-20261011';TMP=Path('/private/tmp/gcts-hilbert-receptors-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def catalog(spec):
    """Reconstruct each rule directly from independent universal substitution."""
    fs={packed(f):f for f in [spec['target'],*spec['theory']['axioms'].values()]};ds=[]
    def save(ps,q,proof,kind,args):
        d=dict(premises=ps,conclusion=q,proof=proof);name='hilbert-'+pin(d)
        ds.append(dict(name=name,level=1,family=kind,arguments=args,definition=dict(name=name,**d)))
    def pred(n,*a):return ['pred',n,list(a)]
    def const(x):return ['fun',x,[]]
    def imp(a,b):return ['imp',a,b]
    # Rebuild the guarded axiom literally, independent of its producer.
    a,b,u,v=[['var',x] for x in ['point0','point1','line0','line1']]
    pieces=[pred('Point',a),pred('Point',b),pred('Line',u),pred('Line',v),['not',['eq',a,b]],pred('Incident',a,u),pred('Incident',b,u),pred('Incident',a,v),pred('Incident',b,v)]
    h=pieces[-1]
    for p in reversed(pieces[:-1]):h=['and',p,h]
    universal=imp(h,['eq',u,v])
    for x in reversed(['point0','point1','line0','line1']):universal=['all',x,universal]
    if 'I.2-uniqueness' in spec['theory']['axioms']:need(spec['theory']['axioms']['I.2-uniqueness']==universal,'declared Hilbert I.2 guard presentation')
    for names in itertools.product(spec['uniqueness_points'],spec['uniqueness_points'],spec['sorts']['line'],spec['sorts']['line']):
        current=universal;steps=[];last=1
        for name in names:
            t=const(name);nxt=subst(current[2],current[1],t)
            steps.append(dict(rule='instantiate',formula=imp(current,nxt),universal=current,term=t));q=2+len(steps)-1
            steps.append(dict(rule='mp',formula=nxt,antecedent=last,implication=q));last=2+len(steps)-1;current=nxt
        premise,goal=current[1:];fs[packed(premise)]=premise;fs[packed(goal)]=goal
        if 'I.2-uniqueness' in spec['theory']['axioms']:
            proof=[dict(rule='assumption',formula=premise,index=0),dict(rule='axiom',formula=universal,name='I.2-uniqueness')]+steps+[dict(rule='mp',formula=goal,antecedent=0,implication=last)]
            save([premise],goal,proof,'universal-uniqueness',list(names))
    for point,left,right in itertools.product(spec['sorts']['point'],spec['sorts']['line'],spec['sorts']['line']):
        s,t=const(left),const(right);template=pred('Incident',const(point),['var','incidenceHole']);eq=['eq',s,t];before=pred('Incident',const(point),s);after=pred('Incident',const(point),t)
        for f in [eq,before,after]:fs[packed(f)]=f
        ps=[eq,before];proof=[dict(rule='assumption',formula=p,index=i) for i,p in enumerate(ps)]
        proof += [dict(rule='eq_subst',formula=imp(eq,imp(before,after)),variable='incidenceHole',template=template,left=s,right=t),dict(rule='mp',formula=imp(before,after),antecedent=0,implication=2),dict(rule='mp',formula=after,antecedent=1,implication=3)]
        save(ps,after,proof,'incidence-equality-transport',[point,left,right])
    return [fs[k] for k in sorted(fs)],ds
def literal_model(spec,c,inv):
    """Enumerate every full-word command, guard and strict-earlier input."""
    basis=c['basis'];interfaces=inv['definitions'];defs={d['name']:d for d in interfaces};modes={d['name']:i+1 for i,d in enumerate(interfaces)};arity=2;ps=[];bad=[];ds=[];tauts={packed(f) for f in c['tautologies']}
    def add(key,entries,command,req,kind,**extra):
        marks={}
        for p,v in entries:
            if p in marks and marks[p]!=v:bad.append(dict(key=key,reason='internally unequal markings'));return
            marks[p]=v
        ps.append(dict(key=key,occupancy=[((4*key[0],key[1]),12)],marks=sorted(marks.items()),slot=key[0],kind=kind,command=command,requirements=req,**extra))
    for j in range(spec['length']):
        fs=[spec['target']] if j+1==spec['length'] else basis;rows=domains(spec,c['catalog'],j)+[dict(rule='block',formula=f,name=d['name']) for f in fs for d in interfaces]
        rows.sort(key=lambda v:(v['rule'],packed(v['formula']),packed(v)));ds.append(rows)
        for k,cmd in enumerate(rows):
            f=cmd['formula'];r=cmd['rule'];mode=modes[cmd['name']] if r=='block' else 0;entries=encode(j,'command',cmd)+encode(j,'formula',f)+[((4*j+2,90),mode)];add((j,0,k,0),entries,cmd,[],'command');req=[]
            if r=='mp':
                for v,a in enumerate(basis):
                    if a[0]=='imp' and a[2]==f:
                        req=[(cmd['antecedent'],a[1]),(cmd['implication'],a)];add((j,1,k,v),entries+[e for i,p in req for e in encode(i,'formula',p)],cmd,req,'guard')
                continue
            if r=='axiom':valid=spec['theory']['axioms'][cmd['name']]==f
            elif r=='refl':valid=f[0]=='eq' and f[1]==f[2]
            elif r=='tautology':valid=packed(f) in tauts
            elif r=='generalize':
                valid=f[0]=='all' and f[1]==cmd['variable']
                if valid:req=[(cmd['source'],f[2])]
            elif r=='block':valid=defs[cmd['name']]['definition']['conclusion']==f
            else:valid=False
            if valid:add((j,1,k,0),entries+[e for i,p in req for e in encode(i,'formula',p)],cmd,req,'guard')
        for r in range(arity):
            add((j,2+r,0,0),[((4*j+2,90),0),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=0,source=None)
            for d in interfaces:
                mode=modes[d['name']];prem=d['definition']['premises']
                if r>=len(prem):add((j,2+r,mode,0),[((4*j+2,90),mode),((4*j+2,100+r),-1)],None,[],'unused_input',input=r,mode=mode,source=None)
                else:
                    for source in range(j):
                        req=[(source,prem[r])];add((j,2+r,mode,source+1),[((4*j+2,90),mode),((4*j+2,100+r),source)]+encode(source,'formula',prem[r]),None,req,'lemma_input',input=r,mode=mode,source=source)
    return dict(domains=ds,command_counts=list(map(len,ds)),arity=arity,mode_ids=modes,placements=sorted(ps,key=lambda v:v['key']),conflicts=bad,roots=[(4*j,r) for j in range(spec['length']) for r in range(4)],complete_words=math.prod(map(len,ds)),initial_marks=encode(spec['length']-1,'formula',spec['target']),families_enabled=True)
def countermodel(spec):
    """Audit-only object interpretation for the removed-uniqueness control."""
    domain=range(5);constants={'A':0,'B':1,'C':2,'u':3,'v':4};points={0,1,2};lines={3,4};inc={(0,3),(1,3),(0,4),(1,4),(2,3)}
    def term(t,env):return env[t[1]] if t[0]=='var' else constants[t[1]]
    def truth(f,env):
        k=f[0]
        if k=='all':return all(truth(f[2],{**env,f[1]:x}) for x in domain)
        if k=='eq':return term(f[1],env)==term(f[2],env)
        if k=='pred':
            args=tuple(term(t,env) for t in f[2]);return args[0] in points if f[1]=='Point' else args[0] in lines if f[1]=='Line' else args in inc
        if k=='not':return not truth(f[1],env)
        if k=='and':return truth(f[1],env) and truth(f[2],env)
        if k=='imp':return not truth(f[1],env) or truth(f[2],env)
        raise ValueError('unsupported countermodel formula')
    values={name:truth(f,{}) for name,f in spec['theory']['axioms'].items()};target=truth(spec['target'],{});need(all(values.values()) and not target,'negative theory has a genuine independent countermodel')
    return dict(status='passed',domain=list(domain),constants=constants,Point=sorted(points),Line=sorted(lines),Incident=sorted(inc),axioms=values,target=target,scope='Used only by independent audit. Not read by candidate generation or search.')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());records=load(OUT/'native.json.gz');requests={};cache={};totals=collections.Counter();reports=[]
    for f,h in plan['sources'].items():need(sha(ROOT/f)==h,'frozen measured source '+f)
    for f,d in plan['data_dependencies'].items():need(sha(ROOT/f)==d['sha256'] and (ROOT/f).stat().st_size==d['bytes'],'frozen native/policy dependency '+f)
    taut=['imp',['bot'],['bot']]
    for spec in plan['cases']:
        raw=load(OUT/(spec['id']+'.json.gz'));need(raw['case']==spec,'predeclared assertion/theory');c=raw['compiled'];inv=raw['inventory'];basis,definitions=catalog(spec)
        need(c['basis']==basis and c['catalog']['basis']==basis and c['variables']==[] and c['catalog']['schemes']==[] and c['admitted_schemes']==[],'entire declared formula envelope and ordinary schema scope')
        need(same(inv['definitions'],definitions) and inv['interfaces']==[d['name'] for d in definitions] and inv['native_blocks']==[d['definition'] for d in definitions] and inv['status']=='native_accepted','all 28 or 12 sorted ground types')
        expected_tauts=[];compile_ids=c['queries'];need(len(compile_ids)==1+len(basis),'complete tautology guard enumeration')
        for i,q in enumerate(compile_ids):
            f=taut if i==0 else basis[i-1];req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[dict(rule='tautology',formula=f)],target=f);rec=records[q]
            need(rec['request']==req and rec['purpose']==('hilbert_theory_admission' if i==0 else 'hilbert_tautology_guard'),'each native guard request bound');need(rec['result']['status'] in ('accepted','rejected'),'unknown cannot grant guards');requests[q]=req
            if i==0:need(rec['result']['status']=='accepted' and c['theory_query']==q,'theory accepted')
            elif rec['result']['status']=='accepted':expected_tauts.append(f)
        need(c['tautologies']==expected_tauts,'native-admitted tautologies exactly')
        need(len(inv['admissions'])==len(definitions),'every complete type native admitted')
        for d,a in zip(definitions,inv['admissions']):
            need(d['name']==a['name'],'complete admission order');q=a['query'];req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d['definition']],proof=[dict(rule='tautology',formula=taut)],target=taut)
            need(records[q]['request']==req and records[q]['purpose']=='hilbert_definition_admission' and records[q]['result']['status']=='accepted','unchanged native ground type acceptance');requests[q]=req
        counts=[];expected=[(r,l) for r in plan['repetitions'] for l in plan['schedules'][str(r)]];need(len(raw['observations'])==len(expected),'complete predeclared matrix');full=literal_model(spec,c,inv)
        for o,(rep,lane) in zip(raw['observations'],expected):
            method=plan['lanes'][lane];r=o['search'];need(o['lane']==lane and o['repetition']==rep and r['mode']==method['mode'] and r['feature_semantics']==method['feature_semantics'] and r['seed']==plan['seed'] and r['limits']==plan['limits'] and not r['stochastic'],'frozen budgets/policy/schedule')
            model=correspondence(full,o['model']);checked=check_tree(spec,o['model'],r,inv,plan['weights'] if method['mode']=='learned' else None);totals.update(checked)
            proof=r['proof'];q=o['native_query']
            if proof is None:need(q is None and not o['cached_native_acceptance'],'no certificate for unknown/exhausted')
            else:
                req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=closure(inv,proof),proof=proof,target=spec['target']);key=pin(req);need(records[q]['request']==req and records[q]['result']['status']=='accepted','whole actual theorem certificate')
                if o['cached_native_acceptance']:need(cache.get(key)==q,'exact disclosed earlier acceptance reuse')
                else:need(q not in requests and key not in cache and records[q]['purpose']=='hilbert_discovered_whole','fresh native theorem check');requests[q]=req;cache[key]=q
                totals['accepted_observations']+=1
            counts.append(dict(lane=lane,repetition=rep,model=model,tree=checked))
        reports.append(dict(id=spec['id'],types=len(definitions),formulas=len(basis),observations=counts));print('full independent model/tree audit',spec['id'],flush=True)
    need(set(requests)==set(range(len(records))),'all native queries accounted');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged computational palette')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));N.TMP=TMP
    steps,accepted=N.replay_native(records,requests,micro,boundary['cases'][0]['initial'],plan['native_steps']);model=countermodel(next(c for c in plan['cases'] if c['id']=='transport-no-uniqueness'))
    result=dict(status='passed',cases=reports,seconds=time.perf_counter()-began,native_queries=len(records),native_micro_steps=steps,distinct_native_acceptances=len(accepted),countermodel=model,**dict(totals));(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('cases','countermodel')}),flush=True)
if __name__=='__main__':main()
