"""Independent completeness audit of the bounded grammar and streamed guards.

No imports from the new catalog/preflight producer. This audits a prospective
grammar, not native admission or a searched theorem. Logical checks remain
explicitly separate from native authority.
"""
import collections,gzip,hashlib,itertools,json,resource,signal,time
from pathlib import Path
import induction_receptors_audit as A
from audit_first_order import subst,free

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def need(t,m):
    if not t:raise ValueError(m)
def budget(plan,began):
    if time.perf_counter()-began>plan['ceilings']['seconds']:raise TimeoutError('unknown_preparation_audit_time_budget')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_preparation_audit_memory_budget')
def deadline(signum,frame):raise TimeoutError('unknown_preparation_audit_time_budget')
def close(f,names):
    for x in reversed(names):f=['all',x,f]
    return f
def schema(body,x):
    return close(['imp',['and',subst(body,x,['fun','zero',[]]),['all',x,['imp',body,subst(body,x,['fun','succ',[['var',x]]])]]],['all',x,body]],sorted(free(body)-{x}))
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());transfer=json.loads((OUT/'transfer.json').read_text());audit_plan=json.loads((OUT/'audit-plan.json').read_text())
    signal.signal(signal.SIGALRM,deadline);signal.alarm(audit_plan['ceilings']['seconds'])
    need(summary['status']=='complete_preflight_not_native_admitted' and summary['native_queries']==0,'preparation-only gate')
    for path,h in {**plan['source_sha256'],**audit_plan['source_sha256']}.items():need(A.sha(ROOT/path)==h,'frozen source '+path)
    spec=plan['case'];body=spec['target'];names=[]
    while body[0]=='all':names.append(body[1]);body=body[2]
    pool=A.terms(spec['theory']['functions'],names,spec['term_bound']);plain_pool=A.plain(pool);equations=[]
    for name,raw in sorted(spec['theory']['axioms'].items()):
        f=A.frozen(raw);vs=[];b=f
        while b[0]=='all':vs.append(b[1]);b=b[2]
        if b[0]=='eq':equations.append(dict(name=name,formula=f,variables=vs,body=b,origin='axiom'))
    base=A.independent_moves(pool,equations);f=A.frozen(transfer['conclusion']);vs=[];b=f
    while b[0]=='all':vs.append(b[1]);b=b[2]
    learned=A.independent_moves(pool,[dict(name=transfer['name'],formula=f,variables=vs,body=b,origin='discovered-lemma')]);result=dict(status='checking',variants=[],native_queries=0)
    budget(audit_plan,began)
    wanted=[dict(original=body[1],hypothesis=None,goal=body,closure=names,kind='direct',variable=None)]
    for x in names:
        params=[v for v in names if v!=x];base_body=subst(body,x,['fun','zero',[]]);step_body=subst(body,x,['fun','succ',[['var',x]]]);wanted += [dict(original=base_body[1],hypothesis=None,goal=base_body,closure=params,kind='base',variable=x),dict(original=step_body[1],hypothesis=body,goal=['imp',body,step_body],closure=params+[x],kind='step',variable=x)]
    for lane,observed in zip(plan['variants'],summary['variants']):
        c=load(OUT/(lane+'-core.json.gz'));need(c['terms']==plain_pool and c['variables']==names and c['spec']==spec,'entire complete term/signature grammar');definitions={d['name']:d for d in c['definitions']};need(len(definitions)==len(c['definitions']),'unique definitions');need(len(c['contexts'])==len(wanted),'all induction alternatives');expected_basis={};expected_generalizations=[];move_counts=[]
        for actual,ctx in zip(c['contexts'],wanted):
            need({k:actual[k] for k in ctx}==ctx,'context input/goal/scope');H=ctx['hypothesis'];moves=base+(learned if lane=='with-searched-zero-left' else [])
            if H is not None:moves=moves+A.independent_moves(pool,[dict(name='induction-hypothesis',formula=A.frozen(H),variables=[],body=A.frozen(H),origin='assumption')])
            got=[r for r in c['rules'] if r['description']['operation'] in ('rewrite','conditional-rewrite') and r['description']['context']==ctx]
            need(sorted(packed(r['description']['move']) for r in got)==sorted(map(packed,moves)),'every occurrence/direction/missing substitution/IH/learned edge');need(actual['move_count']==len(moves),'complete move count')
            def wrap(t):
                q=['eq',ctx['original'],t];return ['imp',H,q] if H is not None else q
            wanted_interfaces=[]
            for m in moves:
                premises=[wrap(m['before'])]
                if m['rule']['origin']=='discovered-lemma':premises.append(m['rule']['formula'])
                wanted_interfaces.append([premises,wrap(m['after'])])
            need(sorted(packed([r['premises'],r['conclusion']]) for r in got)==sorted(map(packed,wanted_interfaces)),'all exact ordinary/conditional/two-input interfaces')
            seed=[r for r in c['rules'] if r['description']['operation'] in ('reflexivity','conditional-reflexivity') and r['description']['context']==ctx];need(len(seed)==1 and seed[0]['premises']==[] and seed[0]['conclusion']==wrap(ctx['original']),'every generic seed')
            for t in plain_pool:
                q=wrap(t);expected_basis[packed(q)]=q
                for x in reversed(ctx['closure']):
                    allq=['all',x,q];expected_generalizations.append([[q],allq,dict(rule='generalize',formula=allq,variable=x)]);expected_basis[packed(allq)]=allq;q=allq
            move_counts.append(dict(kind=ctx['kind'],variable=ctx['variable'],moves=len(moves)))
        generalizations=[[r['premises'],r['conclusion'],r['command']] for r in c['rules'] if r['command']['rule']=='generalize'];need(sorted(map(packed,generalizations))==sorted(map(packed,expected_generalizations)),'every contextual generalization guard')
        for x in names:
            params=[v for v in names if v!=x];premises=[close(subst(body,x,['fun','zero',[]]),params),close(['all',x,['imp',body,subst(body,x,['fun','succ',[['var',x]]])]],params)];got=[r for r in c['rules'] if r['description']['operation']=='induction' and r['description']['variable']==x];need(len(got)==1 and got[0]['premises']==premises and got[0]['conclusion']==spec['target'],'each generic induction interface')
        transferred=[r for r in c['rules'] if r['description']['operation']=='transferred-searched-theorem'];need(len(transferred)==int(lane=='with-searched-zero-left'),'explicit transferred inventory difference')
        if transferred:
            r=transferred[0];need(r['premises']==[] and r['conclusion']==transfer['conclusion'] and definitions[r['command']['name']]['proof']==transfer['proof'],'actual searched theorem exactly transferred');expected_basis[packed(transfer['conclusion'])]=transfer['conclusion']
        for r in c['rules']:
            command=r['command'];need(command['formula']==r['conclusion'],'all output identities')
            if command['rule']=='block':need(definitions[command['name']]['premises']==r['premises'] and definitions[command['name']]['conclusion']==r['conclusion'],'native definition interface identity')
        need(set(map(packed,c['basis']))==set(expected_basis),'complete finite contextual formula basis')
        basis={packed(f):i for i,f in enumerate(c['basis'])};terms={packed(t):i for i,t in enumerate(c['terms'])};seen=set();counts=collections.Counter();digest=hashlib.sha256();byte_count=0
        for j,word in enumerate(gzip.open(OUT/(lane+'-primitive.jsonl.gz'),'rb')):
            if j%1024==0:budget(audit_plan,began)
            digest.update(word);byte_count+=len(word);command=json.loads(word);rule=command['rule'];counts[rule]+=1
            if rule=='instantiate':
                u=command['universal'];t=command['term'];need(packed(u) in basis and u[0]=='all' and packed(t) in terms,'complete declared instantiation operands');key=(rule,basis[packed(u)],terms[packed(t)]);expected=dict(rule=rule,formula=['imp',u,subst(u[2],u[1],t)],universal=u,term=t)
            elif rule=='distribute':
                x=command['variable'];a=command['antecedent'];b=command['consequent'];u=['imp',a,b];need(packed(u) in basis and x in names and x not in free(a),'guarded distribution operands');key=(rule,basis[packed(u)],x);expected=dict(rule=rule,formula=['imp',['all',x,u],['imp',a,['all',x,b]]],variable=x,antecedent=a,consequent=b)
            elif rule=='induction':
                x=command['variable'];need(x in names and command['template']==body,'all declared induction templates');key=(rule,x);expected=dict(rule=rule,formula=schema(body,x),variable=x,template=body)
            else:raise ValueError('undeclared primitive scheme')
            need(command==expected and key not in seen,'every primitive exact formula and unique operands');seen.add(key)
        expected_counts=dict(instantiate=sum(f[0]=='all' for f in c['basis'])*len(pool),distribute=sum(x not in free(f[1]) for f in c['basis'] if f[0]=='imp' for x in names),induction=len(names));need(all(counts[k]==n for k,n in expected_counts.items()),'complete Cartesian guarded primitive catalog');need(dict(counts)==observed['primitive_counts'] and digest.hexdigest()==observed['primitive_stream_sha256'] and byte_count==observed['primitive_uncompressed_bytes'],'full primitive stream fingerprint/count/cost binding')
        for obs in observed['prospective_point_counts']:
            length=obs['length'];total=0;rows=len(c['rules']);last=sum(r['conclusion']==spec['target'] for r in c['rules'])
            for j in range(length):
                total += 2*(last if j==length-1 else rows)+2
                for r in c['rules']:
                    if r['premises']:total+=sum(j if role<len(r['premises']) else 1 for role in range(2))
            need(obs['placements']==total and obs['roots']==4*length and obs['complete_words']==pow(rows,length-1)*last,'every prospective command/guard/prior-input placement count')
        result['variants'].append(dict(lane=lane,terms=len(pool),contexts=move_counts,definitions=len(definitions),interfaces=len(c['rules']),primitive_counts=dict(counts),primitive_bytes=byte_count,prospective_points='independently counted; not a native-authorized/search model'))
        result['seconds']=time.perf_counter()-began;(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('left successor preflight audit',lane,counts,flush=True)
    budget(audit_plan,began);signal.alarm(0)
    result.update(status='passed_preparation_audit_only',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Complete five-node grammar, all equation occurrences/directions/substitutions, all context/generalization/induction/reuse interfaces, every streamed primitive instance and prospective placement counts independently reconstructed. No native admission, target search, learned66-interface claim or speed claim.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('LEFT SUCCESSOR PREFLIGHT AUDIT PASSED',result['seconds'],flush=True)
if __name__=='__main__':
    try:main()
    except (TimeoutError,MemoryError,ValueError) as e:
        signal.alarm(0);p=OUT/'audit.json';r=json.loads(p.read_text()) if p.exists() else dict(variants=[],native_queries=0);r.update(status=str(e),failure_type=type(e).__name__,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);p.write_text(json.dumps(r,indent=2)+'\n');raise
