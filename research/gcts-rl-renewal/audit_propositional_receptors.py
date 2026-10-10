"""Independent complete finite tree replay and numeric RL update audit."""
import collections,copy,hashlib,itertools,json,math,random,time
from pathlib import Path
import check_propositional_receptors as A

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/research/gcts-rl-renewal'
def all_keys(rules,length,hypotheses):
    out={j:[] for j in range(length)}
    for j in out:
        for rid,r in enumerate(rules):
            for refs in itertools.product(range(-len(hypotheses),j),repeat=len(r['inputs'])):
                pairs=list(zip(refs,r['inputs']))
                if any(i==k and a!=b for i,a in pairs for k,b in pairs):continue
                out[j].append((j,rid,refs))
    return out
def values(rules,target,length,hypotheses,chosen):
    seen=set();ports={length-1:target}|{j:a for j,a in enumerate(hypotheses,-len(hypotheses))}
    for j,rid,refs in chosen:
        A.need(j not in seen,'unique occupied proof point');seen.add(j);r=rules[rid]
        A.need(len(refs)==len(r['inputs']) and all(-len(hypotheses)<=i<j for i in refs),'backward interface')
        for i,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            A.need(i not in ports or ports[i]==a,'exact symbolic/word port agreement');ports[i]=a
    return seen,ports
def decision(rules,universe,target,length,hypotheses,chosen):
    seen,ports=values(rules,target,length,hypotheses,chosen);ds={}
    for j,keys in universe.items():
        if j in seen:continue
        ds[j]=[key for key in keys if all(i not in ports or ports[i]==a for i,a in [(j,rules[key[1]]['output'])]+list(zip(key[2],rules[key[1]]['inputs'])))]
    dead=[j for j,ks in ds.items() if not ks]
    forced=[j for j,ks in ds.items() if len(ks)==1]
    if dead:j=min(dead);return 'dead',(2*j,0),[],ds
    if forced:j=min(forced);return 'forced',(2*j,0),ds[j],ds
    if not ds:return 'empty',None,[],ds
    j=min(ds,key=lambda i:(len(ds[i]),i));return 'branch',(2*j,0),ds[j],ds

def tree_audit(rules,target,length,hypotheses,result,universe):
    if result['search_tree'] is None:
        A.need(result['status']=='unknown_search_budget','missing complete terminal tree');return dict(status='budget_unknown')
    counts=collections.Counter();leaf=None
    def walk(tree,chosen):
        nonlocal leaf
        counts['nodes']+=1;kind,p,keys,ds=decision(rules,universe,target,length,hypotheses,chosen)
        counts['peak_candidate_nodes']=max(counts['peak_candidate_nodes'],sum(map(len,ds.values())))
        counts['peak_incidences']=counts['peak_candidate_nodes']
        A.need(tree['kind']==kind and tree['point']==p,'global dead/forced/generation decision')
        if kind=='dead':counts['dead']+=1;return False
        if kind=='empty':leaf=chosen;return True
        counts['forced' if kind=='forced' else 'branches']+=1
        children=tree['children'];visited=[];ok=False
        for child in children:
            key=child['key'];A.need(key in keys and key not in visited and not ok,'complete shared candidate domain');visited.append(key);counts['attempts']+=1
            ok=walk(child['tree'],chosen+(key,))
            if not ok:counts['backtracks']+=1
        A.need(ok or set(visited)==set(keys),'all alternatives exhausted before negative claim')
        return ok
    ok=walk(result['search_tree'],())
    A.need(ok==(result['status']=='finite_exact_proof_tiling'),'tree/result scope')
    A.need(not ok or leaf==result['placements'],'selected exact leaf')
    for k,v in counts.items():A.need(result['metrics'].get(k,0)==v,'exact search counter '+k)
    return dict(status='complete_tree_replayed',nodes=counts['nodes'],positive=ok)

def rl_audit(data):
    rules=data['basis']['rules'];length=5;target=('imp',('Q',),('Q',));universe=all_keys(rules,length,())
    weights=collections.defaultdict(float);baseline=0.;successful=0;proposals=0
    def fs(key,chosen):
        j,rid,refs=key;r=rules[rid];occupied={k[0] for k in chosen}
        return {'bias':1.,'target':float(r['output']==target),'mp':float(r['kind']=='mp'),'lemma':float(r['kind']=='lemma'),
                'known_refs':sum(i<0 or i in occupied for i in refs),'unfilled_refs':sum(i>=0 and i not in occupied for i in refs),
                'length':len(A.word(r['output']))/40.,'reach':max((j-i for i in refs),default=0)/length}
    for row in data['training']['rollouts']:
        rng=random.Random(row['seed']);chosen=();traces=[]
        for cluster in row['clusters']:
            proposals+=1;budget=rng.randint(1,3);A.need(1<=len(cluster)<=budget,'variable continuation expansion')
            for key in cluster:
                kind,p,keys,_=decision(rules,universe,target,length,(),chosen)
                A.need(kind not in ('dead','empty') and key in keys,'training uses complete scheduled domains')
                if kind=='forced':A.need(key==keys[0],'global forced proposal')
                else:
                    features=[fs(k,chosen) for k in keys];scores=[sum(weights[k]*v for k,v in f.items()) for f in features]
                    vals=[math.exp(v-max(scores)) for v in scores];total=sum(vals);prob=[v/total for v in vals]
                    idx=rng.choices(range(len(keys)),weights=prob)[0];A.need(key==keys[idx],'recorded on-policy draw')
                    expected=collections.defaultdict(float)
                    for p,f in zip(prob,features):
                        for k,v in f.items():expected[k]+=p*v
                    traces.append({k:features[idx].get(k,0)-expected.get(k,0) for k in expected})
                chosen+=(key,)
            kind,_,_,_=decision(rules,universe,target,length,(),chosen)
            A.need(len(cluster)==budget or kind in ('dead','empty'),'no unreported proposal truncation')
        kind,_,_,_=decision(rules,universe,target,length,(),chosen)
        reward=len(chosen)/length+(1 if kind=='empty' else -1)
        A.need(kind==row['outcome'] and len(chosen)==row['placed'] and reward==row['reward'],'training reward measured in base proof cells')
        if kind=='empty':
            proof=[None]*length
            for j,rid,refs in chosen:proof[j]=dict(kind=rules[rid]['kind'],formula=rules[rid]['output'],refs=refs)
            A.logical(proof,target);successful+=1
        advantage=reward-baseline;baseline=.9*baseline+.1*reward
        for g in traces:
            for k,v in g.items():weights[k]+=.03*advantage*v/max(1,len(traces))
    A.need(abs(baseline-data['training']['baseline'])<1e-12,'policy reward baseline')
    for k,v in data['training']['weights'].items():A.need(abs(v-weights[k])<1e-10,'independently recomputed REINFORCE weight')
    return dict(episodes=len(data['training']['rollouts']),successful=successful,clusters=proposals,weights_recomputed=True)

def audit_case(data,case):
    library=(data['discovered_family'],) if case['library'] else ()
    base=data['basis'];expected=A.independent_basis()[1]
    if library:
        # Build expected family instances independently; compare in certificate().
        f=library[0]
        def subst(a,v):return v if a==('P',) else (a[0],)+tuple(subst(x,v) for x in a[1:])
        for a in A.independent_basis()[0]:expected.append(dict(kind='lemma',name=f['name'],parameter=a,inputs=(),output=subst(f['conclusion'],a),expansion=[dict(r,formula=subst(r['formula'],a)) for r in f['proof']]))
    cat=dict(base,rules=expected);A.inventory(cat,library);universe=all_keys(expected,case['length'],case['hypotheses']);checked=[]
    for lane,r in case['runs'].items():
        if r['proof'] is not None:
            logical=A.logical(r['proof'],case['target'],case['hypotheses']);A.need(logical['primitive_lines']==r['primitive_lines'],'primitive cost')
            if lane.startswith('point'):
                report=A.certificate(cat,case['target'],case['length'],case['hypotheses'],r['placements'],r['point_tiles'],library)
                A.need(report==r['independent'],'saved independent point audit')
                decoded=[]
                for slot in range(case['length']):
                    key=next(k for k in r['placements'] if k[0]==slot);rule=expected[key[1]];row=dict(kind=rule['kind'],formula=rule['output'],refs=key[2])
                    if rule['kind']=='lemma':row.update(name=rule['name'],parameter=rule['parameter'],expansion=rule['expansion'])
                    decoded.append(row)
                A.need(A.frozen(decoded)==r['proof'],'displayed proof comes from actual selected tiles')
                A.need(r['tile_generations']==(1,)*case['length'],'explicit generation-zero roots')
            checked.append(lane)
        if lane.startswith('point'):
            A.need(r['candidate_universe']==sum(map(len,universe.values())),'complete compiled candidate universe')
            tree_audit(expected,case['target'],case['length'],case['hypotheses'],r,universe)
            for s in r['samples']:
                kind,p,keys,_=decision(expected,universe,case['target'],case['length'],case['hypotheses'],s['placed'])
                A.need((s['kind'],s['point'],s['degree'])==(kind,p,len(keys)),'saved graph sample')
            for proposal in r['proposals']:
                chosen=proposal['incoming'];A.need(1<=len(proposal['expansion'])<=3,'bounded variable-length proposal')
                for key in proposal['expansion']:
                    kind,p,keys,_=decision(expected,universe,case['target'],case['length'],case['hypotheses'],chosen)
                    A.need(key in keys,'validated proposal obeys scheduler');chosen+=(key,)
    return checked

def main():
    start=time.perf_counter();raw=json.loads((DOC/'propositional-receptors-001.json').read_text());data=A.frozen(raw)
    for n,pin in data['sources'].items():A.need(hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest()==pin,'measured source pin '+n)
    A.inventory(data['basis'],());A.need(data['discovered_family']['proof']==data['donor']['proof'],'family is promoted from actual discovery')
    A.need(not data['initial_library'] and not data['authored_proofs'],'cold discovery provenance')
    p,q=('P',),('Q',);i=lambda a,b:('imp',a,b);n=lambda a:('not',a)
    targets={'identity-P':(i(p,p),5,(),False),'identity-composite':(i(i(p,q),i(p,q)),5,(),False),
        'weakening':(i(p,i(q,p)),1,(),False),'two-premise-links':(i(p,q),2,(q,i(q,p),i(p,i(p,q))),False),
        'contraposition':(i(p,q),2,(i(n(q),n(p)),),False),'family-composite':(i(i(p,q),i(p,q)),1,(),True),
        'family-weakening':(i(p,i(q,q)),3,(),True),'primitive-weakening':(i(p,i(q,q)),7,(),False),'closed-P-one-slot':(p,1,(),False)}
    A.need({c['id'] for c in data['cases']}==set(targets),'external task registry')
    rl=rl_audit(data);rows=[];mutations=0
    for case in data['cases']:
        A.need((case['target'],case['length'],case['hypotheses'],case['library'])==targets[case['id']],'fixed independent problem statement')
        checked=audit_case(data,case);rows.append(dict(id=case['id'],accepted_lanes=checked))
        good=case['runs']['point']
        if good['proof'] is not None:
            for kind in ('mark','omit','capacity','future-ref','display'):
                bad=copy.deepcopy(case);r=bad['runs']['point'];tiles=list(r['point_tiles']);tile=dict(tiles[0]);tiles[0]=tile;r['point_tiles']=tuple(tiles)
                if kind=='mark':entries=list(tile['marks']);entries[0]=(entries[0][0],'Q' if entries[0][1]!='Q' else 'P');tile['marks']=tuple(entries)
                elif kind=='omit':tile['marks']=tile['marks'][1:]
                elif kind=='capacity':tile['occupancy']=((tile['occupancy'][0][0],6),)
                elif kind=='future-ref':keys=list(r['placements']);k=keys[0];keys[0]=(k[0],k[1],(k[0],));r['placements']=tuple(keys);tile['key']=keys[0]
                else:
                    proof=list(r['proof']);proof[-1]=dict(proof[-1],formula=p);r['proof']=tuple(proof)
                try:audit_case(data,bad)
                except ValueError:mutations+=1
                else:raise ValueError('accepted mutation '+kind)
        if good['search_tree'] is not None:
            bad=copy.deepcopy(case);tree=bad['runs']['point']['search_tree'];tree['point']=(999,0)
            try:audit_case(data,bad)
            except ValueError:mutations+=1
            else:raise ValueError('accepted changed scheduling point')
    report=dict(seconds=time.perf_counter()-start,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                producer_sha256=hashlib.sha256((DOC/'propositional-receptors-001.json').read_bytes()).hexdigest(),
                cases=rows,rl=rl,mutations_rejected=mutations,scope='complete terminal point trees; exact certificates; fixed hypotheses; actual word-to-formula decoding; independent on-policy updates; budget cutoffs stay unknown')
    (DOC/'propositional-receptors-audit-001.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
