"""Independent entire grammar, closure, prospective graph and motif audit.

Does not import commutativity producers. Cartesian substitution enumeration
and a reverse occurrence index replace pattern-unification. A dependency
worklist replaces synchronous producer closure. No target proof is extracted.
"""
import collections,copy,gzip,hashlib,itertools,json,resource,signal,time
from pathlib import Path
import induction_receptors_audit as A
from audit_first_order import subst,free
from audit_semantic_proofs import whole_replay

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.gcts-active/commutativity-receptors-20261011';LEFT=ROOT/'.gcts-active/left-successor-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def deadline(s,f):raise TimeoutError('unknown_commutativity_independent_audit_time_budget')
def moves(pool,equations):
    occ=collections.defaultdict(list)
    for before in pool:
        for path,sub in A.positions(before):occ[sub].append((before,path))
    allowed=set(pool);out={}
    for rule in equations:
        for values in itertools.product(pool,repeat=len(rule['variables'])):
            env=dict(zip(rule['variables'],values));a,b=[A.substitute_term(t,env) for t in rule['body'][1:]]
            for direction,left,right in [(1,a,b),(-1,b,a)]:
                for before,path in occ[left]:
                    after=A.at(before,path,right)
                    if after not in allowed or after==before:continue
                    m=A.plain(dict(before=before,after=after,path=path,bindings=env,direction=direction,rule=rule));out[A.packed(m)]=m
    return [out[k] for k in sorted(out)]
def eq(name,f,origin):
    f=A.frozen(f);vs=[];body=f
    while body[0]=='all':vs.append(body[1]);body=body[2]
    return dict(name=name,formula=f,variables=vs,body=body,origin=origin)
def close(f,names):
    for x in reversed(names):f=['all',x,f]
    return f
def ranks(c):
    ids={A.packed(f):i for i,f in enumerate(c['basis'])};edges=[dict(rule=i,inputs=[ids[A.packed(p)] for p in r['premises']],output=ids[A.packed(r['conclusion'])]) for i,r in enumerate(c['rules'])];known={};watch=collections.defaultdict(list);left=[];q=collections.deque()
    for e in edges:
        ins=set(e['inputs']);left.append(len(ins))
        for p in ins:watch[p].append(e['rule'])
        if not ins and e['output'] not in known:known[e['output']]=0;q.append(e['output'])
    while q:
        p=q.popleft()
        for i in watch[p]:
            left[i]-=1;e=edges[i]
            if not left[i]:
                rank=1+max(known[a] for a in e['inputs'])
                if e['output'] not in known:known[e['output']]=rank;q.append(e['output'])
                else:need(known[e['output']]<=rank,'FIFO layers compute minimal rank')
    for e in edges:e.update(unreachable_inputs=sorted(set(p for p in e['inputs'] if p not in known)),eligible=all(p in known for p in e['inputs']))
    return dict(formula_ranks=[known.get(i) for i in range(len(c['basis']))],layers=[sorted(i for i,r in known.items() if r==n) for n in range(max(known.values())+1)],edges=edges,retained_rules=[e['rule'] for e in edges if e['eligible']],removed_rules=[e['rule'] for e in edges if not e['eligible']],rounds=max(known.values()))
def native_request(theory,d):
    taut=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
def union(placements,keys):
    occ={};mark={}
    for key in set(map(tuple,keys)):
        p=placements[key]
        for point,v in p['occupancy']:
            point=tuple(point);occ[point]=occ.get(point,0)+v
            if occ[point]>12:return None
        for point,v in p['marks']:
            point=tuple(point)
            if point in mark and mark[point]!=v:return None
            mark[point]=v
    return dict(occupancy=sorted(occ.items()),marks=sorted(mark.items()))
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());ap=json.loads((OUT/'audit-plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());signal.signal(signal.SIGALRM,deadline);signal.alarm(ap['ceilings']['seconds'])
    for p,h in {**plan['source_sha256'],**plan['input_sha256'],**ap['source_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen preparation/audit '+p)
    need(summary['status']=='complete_bounded_feasibility_pending_independent_audit' and summary['native_queries']==summary['target_searches']==summary['RL_training_runs']==0,'no admission/search/learner');inventory=json.loads((OUT/'inventory.json').read_text());spec=plan['case'];body=spec['target'];names=[]
    while body[0]=='all':names.append(body[1]);body=body[2]
    pool=A.terms(spec['theory']['functions'],names,spec['term_bound']);base_moves=moves(pool,[eq(n,f,'axiom') for n,f in sorted(spec['theory']['axioms'].items())]);lemma_moves=[moves(pool,[eq(d['name'],d['conclusion'],'discovered-lemma')]) for d in inventory];contexts=[dict(original=body[1],hypothesis=None,goal=body,closure=names,kind='direct',variable=None)]
    for x in names:
        params=[v for v in names if v!=x];b=subst(body,x,['fun','zero',[]]);s=subst(body,x,['fun','succ',[['var',x]]]);contexts.extend([dict(original=b[1],hypothesis=None,goal=b,closure=params,kind='base',variable=x),dict(original=s[1],hypothesis=body,goal=['imp',body,s],closure=params+[x],kind='step',variable=x)])
    union_defs={};result=dict(status='checking',native_queries=0,target_searches=0,lanes=[])
    for lane,stats in zip(plan['lanes'],summary['lanes']):
        c=load(OUT/(lane['id']+'-full-core.json.gz'));cc=load(OUT/(lane['id']+'-compact-core.json.gz'));w=load(OUT/(lane['id']+'-closure.json.gz'));ret=load(OUT/(lane['id']+'-retained-core.json.gz'));need(c['spec']==spec and c['terms']==A.plain(pool) and c['variables']==names,'entire term/signature grammar');need(len(c['contexts'])==len(contexts),'all five contexts');expected_basis={};expected_generals=[];expected_rule_count=0
        for actual,ctx in zip(c['contexts'],contexts):
            need({k:actual[k] for k in ctx}==ctx,'each context and quantifier closure');allmoves=base_moves+sum(lemma_moves[:lane['inventory_count']],[])
            if ctx['hypothesis'] is not None:allmoves+=moves(pool,[eq('induction-hypothesis',ctx['hypothesis'],'assumption')])
            got=[r for r in c['rules'] if r['description']['operation'] in ('rewrite','conditional-rewrite') and r['description']['context']==ctx];need(sorted(A.packed(r['description']['move']) for r in got)==sorted(map(A.packed,allmoves)) and actual['move_count']==len(allmoves),'every direction, occurrence and complete missing substitution')
            def wrap(t):
                f=['eq',ctx['original'],t];return ['imp',ctx['hypothesis'],f] if ctx['hypothesis'] is not None else f
            interfaces=[]
            for m in allmoves:interfaces.append([[wrap(m['before'])]+([m['rule']['formula']] if m['rule']['origin']=='discovered-lemma' else []),wrap(m['after'])])
            need(sorted(A.packed([r['premises'],r['conclusion']]) for r in got)==sorted(map(A.packed,interfaces)),'all exact ordinary/conditional/two-input interfaces');seeds=[r for r in c['rules'] if r['description']['operation'] in ('reflexivity','conditional-reflexivity') and r['description']['context']==ctx];need(len(seeds)==1 and not seeds[0]['premises'] and seeds[0]['conclusion']==wrap(ctx['original']),'all generic seeds');expected_rule_count+=len(got)+1
            for t in A.plain(pool):
                f=wrap(t);expected_basis[A.packed(f)]=f
                for x in reversed(ctx['closure']):q=['all',x,f];expected_generals.append([[f],q,dict(rule='generalize',formula=q,variable=x)]);expected_basis[A.packed(q)]=q;f=q
        got=[ [r['premises'],r['conclusion'],r['command']] for r in c['rules'] if r['command']['rule']=='generalize'];need(sorted(map(A.packed,got))==sorted(map(A.packed,expected_generals)),'all contextual generalizations');expected_rule_count+=len(got)
        for x in names:
            params=[v for v in names if v!=x];premises=[close(subst(body,x,['fun','zero',[]]),params),close(['all',x,['imp',body,subst(body,x,['fun','succ',[['var',x]]])]],params)];got=[r for r in c['rules'] if r['description']['operation']=='induction' and r['description']['variable']==x];need(len(got)==1 and got[0]['premises']==premises and got[0]['conclusion']==spec['target'],'both variable induction alternatives');expected_rule_count+=1
        roots=[r for r in c['rules'] if r['description']['operation']=='transferred-searched-theorem'];need(len(roots)==lane['inventory_count'],'actual inventory cardinality')
        for entry in inventory[:lane['inventory_count']]:
            r=next(r for r in roots if r['command']['name']==entry['name']);d=next(d for d in c['definitions'] if d['name']==entry['name']);need(r['premises']==[] and r['conclusion']==entry['conclusion'] and d['proof']==entry['proof'] and d['premises']==[],'exact actual proved certificate promotion');expected_basis[A.packed(entry['conclusion'])]=entry['conclusion'];expected_rule_count+=1
        need(set(map(A.packed,c['basis']))==set(expected_basis) and len(c['rules'])==expected_rule_count,'complete basis/rules and no hidden alternatives');need(c['rules']==cc['rules'] and c['basis']==cc['basis'],'compaction does not change grammar');defs={d['name']:d for d in cc['definitions']}
        for d in cc['definitions']:need(whole_replay(native_request(spec['theory'],d))['status']=='accepted','independent whole local host logical check')
        for d in c['definitions']:need({k:v for k,v in d.items() if k!='proof'}=={k:v for k,v in defs[d['name']].items() if k!='proof'},'each exact fixed premise/interface retained')
        for r in c['rules']:
            need(r['command']['formula']==r['conclusion'],'output formula identity')
            if r['command']['rule']=='block':need(defs[r['command']['name']]['premises']==r['premises'] and defs[r['command']['name']]['conclusion']==r['conclusion'],'every declared local native interface')
        expected=ranks(cc);need(w==expected,'complete independent least fixed-point ranks/layers/edges');need(ret['rules']==[cc['rules'][i] for i in expected['retained_rules']],'all reachable alternatives retained; no selected path');used={r['command']['name'] for r in ret['rules'] if r['command']['rule']=='block'};need(ret['definitions']==[d for d in cc['definitions'] if d['name'] in used],'exact complete retained-definition dependency registry')
        for d in ret['definitions']:need(d['name'] not in union_defs or union_defs[d['name']]==d,'identical union bytes');union_defs[d['name']]=d
        roots={A.packed(r['conclusion']):i for i,r in enumerate(ret['rules']) if r['description']['operation']=='transferred-searched-theorem'};families=[dict(root_rule=roots[A.packed(r['premises'][1])],rewrite_rule=i,lemma_premise=1,external_premise=0,scope='Proof-backed deterministic cluster family, not RL or a learned exclusion.') for i,r in enumerate(ret['rules']) if len(r['premises'])==2 and r['description']['operation'] in ('rewrite','conditional-rewrite') and A.packed(r['premises'][1]) in roots]
        for obs in stats['point_counts']:
            n=obs['full']['length']
            for key,cat in [('full',cc),('retained',ret)]:
                last=sum(r['conclusion']==spec['target'] for r in cat['rules']);total=sum(2*(last if j+1==n else len(cat['rules']))+2+sum(sum(j if role<len(r['premises']) else 1 for role in range(2)) for r in cat['rules'] if r['premises']) for j in range(n));need(obs[key]['placements']==total and obs[key]['roots']==4*n,'complete candidate counts independent row-role enumeration')
            count=sum(j*(j-1) for j in range(n) for f in families if j+1<n or ret['rules'][f['rewrite_rule']]['conclusion']==spec['target']);need(obs['motifs']['families']==len(families) and obs['motifs']['internally_consistent_instances']==count,'all variable-shape motif counts')
        for n in plan['materialized_lengths']:
            raw=load(OUT/(lane['id']+'-points-%d.json.gz'%n));A.model_binding(raw['case'],ret,raw['model']);tiles={tuple(p['key']):p for p in raw['model']['placements']};samples=load(OUT/(lane['id']+'-motif-pilot-%d.json.gz'%n));need([s['family'] for s in samples]==families,'every complete eligible family independently piloted')
            def keys(row,rule,sources):
                idx=next(k for k,d in enumerate(raw['model']['domains'][row]) if d['rule']==rule);r=ret['rules'][rule];mode=rule+1 if r['premises'] else 0;return [(row,0,idx,0),(row,1,idx,0)]+[(row,2+role,mode,sources[role]+1 if role<len(sources) else 0) for role in range(2)]
            for sample in samples:
                f=sample['family'];wanted=keys(1,f['root_rule'],[])+keys(2,f['rewrite_rule'],[0,1]);need(sample['aggregate']['keys']==[list(k) for k in wanted],'all eight exact original placements');a=union(tiles,wanted);need(a is not None and A.packed(a['occupancy'])==A.packed(sample['aggregate']['occupancy']) and A.packed(a['marks'])==A.packed(sample['aggregate']['marks']),'literal aggregate occupancy/mark agreement');need(union(tiles,keys(1,f['root_rule'],[])+keys(2,f['rewrite_rule'],[1,1])) is None,'actual conflicting external receptor rejected')
            del raw,tiles,samples
        result['lanes'].append(dict(lane=lane['id'],complete_terms=len(pool),full_interfaces=len(c['rules']),full_definitions=len(c['definitions']),retained_interfaces=len(ret['rules']),retained_definitions=len(ret['definitions']),all_motif_families=len(families),whole_native_authority=False));del c,cc,ret,w;__import__('gc').collect()
        need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=ap['ceilings']['rss_bytes'],'unknown_commutativity_independent_audit_memory_budget')
    requirements=load(OUT/'admission-requirements.json.gz');need([q['definition'] for q in requirements]==[union_defs[n] for n in sorted(union_defs)],'entire exact union admission requirements');prior={A.packed(q['request']):q for p in ['pilot-native.json.gz','admission-native.json.gz'] for q in load(LEFT/p) if q['result']['status']=='accepted'}
    for q in requirements:
        req=native_request(spec['theory'],q['definition']);need(hashlib.sha256(A.packed(req)).hexdigest()==q['request_sha256'],'every whole native admission request binding');need((A.packed(req) in prior)==(q['exact_prior_request'] is not None),'all and only byte-identical prior full requests reusable')
    for p,h in plan['preserved_export_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'preserved previous milestone '+p)
    signal.alarm(0);result.update(status='passed_complete_bounded_feasibility_audit',native_admission_union=len(requirements),native_queries=0,target_searches=0,RL_training_runs=0,seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Independent complete finite term/rewrite/quantifier/induction/inventory grammar, exact ranks and all alternatives, complete prospective point universes, literal eight-placement family pilots and whole native-admission request requirements. This is not native admission, a target proof or a GCTS/RL outcome.');(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('COMMUTATIVITY COMPLETE FEASIBILITY AUDIT PASSED',json.dumps(result),flush=True)
if __name__=='__main__':main()
