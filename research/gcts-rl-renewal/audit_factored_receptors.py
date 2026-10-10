"""Independent complete inventories, search trees, point tiles and factors."""
import collections,itertools,copy,hashlib,json,time
from pathlib import Path
import check_propositional_receptors as A
import check_factored_receptors as C
from serialized_kernel import canonical
from audit_propositional_wang import expected_compilation
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def factors(case,rules,frame):
    length=case['length'];h=len(case['hypotheses']);chosen=frame['placed']
    filled,ports=C.port_state(rules,case['target'],length,case['hypotheses'],chosen);by={}
    for rid,r in enumerate(rules):by.setdefault(r['output'],[]).append(rid)
    degrees=C.counts(rules,by,case['target'],length,case['hypotheses'],chosen)
    A.need({d['point'][0]//2 for d in frame['domains']}==set(degrees),'all frontier domain factors')
    for domain in frame['domains']:
        j=domain['point'][0]//2;A.need(domain['point']==(2*j,0),'point position');seen=set();total=0
        for start,stop,x,y in domain['blocks']:
            A.need(0<=start<stop<=len(rules),'factor range')
            for rid in range(start,stop):
                A.need(rid not in seen,'disjoint factors');seen.add(rid);r=rules[rid]
                A.need(j not in ports or r['output']==ports[j],'output receptor')
                if not r['inputs']:A.need(x is None and y is None,'schema parameters have no references');total+=1
                else:
                    A.need(stop==start+1 and x is not None and y is not None,'MP factor structure')
                    xs=[k for k in range(-h,j) if k not in ports or ports[k]==r['inputs'][0]]
                    ys=[k for k in range(-h,j) if k not in ports or ports[k]==r['inputs'][1]]
                    A.need(x==sum(2**(k+h) for k in xs) and y==sum(2**(k+h) for k in ys),'complete exact reference masks')
                    total+=sum(1 for a in xs for b in ys if a!=b)
        A.need(total==domain['count']==degrees[j],'exhaustion and singleton cardinality')
    key=frame['key'];A.need(key[0] not in filled,'unoccupied selected slot');C.port_state(rules,case['target'],length,case['hypotheses'],chosen+(key,))
    dead=sorted(j for j,n in degrees.items() if n==0);forced=sorted(j for j,n in degrees.items() if n==1)
    kind='dead' if dead else 'forced' if forced else 'branch'
    j=dead[0] if dead else forced[0] if forced else min(degrees,key=lambda j:(degrees[j],j))
    A.need(frame['kind']==kind and frame['point']==(2*j,0) and key[0]==j,'actual factor frame scheduling')
def policy_proposals(rules,target,length,hypotheses,result,weights):
    A.need(result['policy']==weights,'actual frozen policy weights');by=collections.defaultdict(list)
    for rid,r in enumerate(rules):by[r['output']].append(rid)
    checked=0
    for proposal in result['proposals']:
        chosen=proposal['incoming']
        for selected in proposal['expansion']:
            filled,ports=C.port_state(rules,target,length,hypotheses,chosen);ds=C.counts(rules,by,target,length,hypotheses,chosen)
            A.need(all(ds.values()),'no dead frontier before proposal');forced=sorted(j for j,n in ds.items() if n==1)
            slot=forced[0] if forced else min(ds,key=lambda j:(ds[j],j));best=None;best_rank=None
            for rid in by.get(ports[slot],()) if slot in ports else range(len(rules)):
                r=rules[rid];options=[[j for j in range(-len(hypotheses),slot) if j not in ports or ports[j]==a] for a in r['inputs']]
                for refs in itertools.product(*options):
                    if len(refs)==2 and refs[0]==refs[1]:continue
                    key=(slot,rid,refs);features=dict(bias=1.,target=float(r['output']==target),mp=float(r['kind']=='mp'),lemma=float(r['kind']=='lemma'),
                        known_refs=sum(j<0 or j in filled for j in refs),unfilled_refs=sum(j>=0 and j not in filled for j in refs),
                        length=len(A.word(r['output']))/40.,reach=max((slot-j for j in refs),default=0)/max(1,length))
                    rank=(sum(weights.get(k,0)*v for k,v in features.items()),(-slot,-rid))
                    if best_rank is None or rank>best_rank:best,best_rank=key,rank
            A.need(selected==best,'independently reproduced complete-domain greedy proposal');chosen+=(selected,);checked+=1
    return checked


def main():
    began=time.perf_counter();path=DOC/'factored-receptors-001.json';data=A.frozen(json.loads(path.read_text()))
    for n,pin in data['sources'].items():A.need(digest(HERE/n)==pin,'measured source '+n)
    A.need(digest(DOC/'propositional-receptors-001.json')==data['reused_policy_artifact_sha256'] and not data['authored_proofs'],'cold discovery/frozen policy provenance')
    p,q=('P',),('Q',);n=lambda a:('not',a);i=lambda a,b:('imp',a,b)
    registry={'plain-identity':('plain',i(p,p),5,(),False),'plain-exhausted':('plain',p,1,(),False),
        'double-negation-premise':('negated',i(p,q),4,(i(n(n(p)),n(n(q))),),False),
        'negated-identity':('negated',i(n(p),n(p)),5,(),False),'negated-family':('negated',i(n(p),n(p)),1,(),True),
        'negated-family-weakening':('negated',i(n(p),i(q,q)),3,(),True)}
    A.need(len(data['cases'])==len(registry) and {c['id'] for c in data['cases']}==set(registry),'external theorem registry')
    donor=data['cases'][0]['runs']['factored']['proof'];A.need(data['discovered_family']['proof']==donor,'actual fresh family donor')
    family=data['discovered_family'];rows=[];mutations=[];policy_steps=0
    prior=json.loads((DOC/'propositional-receptors-001.json').read_text())
    for case in data['cases']:
        A.need(tuple(case[k] for k in ('mode','target','length','hypotheses','family'))==registry[case['id']],'fixed statement and envelope')
        params,rules=C.inventory(case['mode'],family if case['family'] else None)
        A.need(tuple(params)==case['pool'] and len(rules)==case['rules'] and hashlib.sha256(canonical(rules)).hexdigest()==case['inventory_sha256'],'full inventory construction')
        accepted=[];checks=[]
        for lane,r in case['runs'].items():
            if r.get('proof') is not None:
                logical=A.logical(r['proof'],case['target'],case['hypotheses']);A.need(logical['primitive_lines']==r['primitive_lines'],'primitive cost')
                if lane in ('ground','factored','factored-rl'):
                    check=C.certificate(rules,case['target'],case['length'],case['hypotheses'],r['placements'],r['point_tiles'])
                    A.need(check==r['independent'] and A.frozen(C.decode(rules,r['placements'],case['length']))==r['proof'],'exact displayed point proof')
                    A.need(r['tile_generations']==(1,)*case['length'],'generation-zero root semantics')
                accepted.append(lane)
            if lane in ('factored','factored-rl','ground') and r['status']!='not_run_declared_candidate_cap':checks.append(dict(lane=lane,**C.tree(rules,case['target'],case['length'],case['hypotheses'],r)))
        ground=case['runs']['ground']
        policy_steps+=policy_proposals(rules,case['target'],case['length'],case['hypotheses'],case['runs']['factored-rl'],prior['training']['weights'])
        if ground['status']=='not_run_declared_candidate_cap':A.need(case['candidate_universe']>data['ground_candidate_cap'],'predeclared ground cap')
        else:A.need(ground['search_tree']==case['runs']['factored']['search_tree'],'identical matched terminal tree')
        for frame in case.get('frames',()):factors(case,rules,frame)
        good=case['runs']['factored']
        if good['proof']:
            for kind in ('display','mark','omit','future-reference','tree-degree','factor-count','factor-mask'):
                bad=copy.deepcopy(case);r=bad['runs']['factored']
                if kind=='display':r['proof'][0]['formula']=p
                elif kind in ('mark','omit'):
                    tiles=list(r['point_tiles']);tile=dict(tiles[0]);tiles[0]=tile;r['point_tiles']=tuple(tiles)
                    tile['marks']=tile['marks'][1:] if kind=='omit' else ((tile['marks'][0][0],'bad'),)+tile['marks'][1:]
                elif kind=='future-reference':
                    proof=list(r['proof']);line=dict(proof[-1]);proof[-1]=line;r['proof']=tuple(proof);line['refs']=(case['length']-1,case['length']-1);line['kind']='mp'
                elif kind=='tree-degree':r['samples'][0]['degree']+=1
                elif kind=='factor-count':bad['frames'][0]['domains'][0]['count']+=1
                else:
                    selected=None
                    for frame in bad['frames']:
                        for domain in frame['domains']:
                            blocks=list(domain['blocks'])
                            for j,b in enumerate(blocks):
                                if b[2] is not None:blocks[j]=(b[0],b[1],b[2]^1,b[3]);domain['blocks']=tuple(blocks);selected=frame;break
                            if selected:break
                        if selected:break
                    if selected is None:continue
                try:
                    if kind.startswith('factor-'):
                        for f in bad.get('frames',()):factors(bad,rules,f)
                        raise RuntimeError('factor mutation unexpectedly accepted')
                    A.logical(r['proof'],bad['target'],bad['hypotheses']);C.certificate(rules,bad['target'],bad['length'],bad['hypotheses'],r['placements'],r['point_tiles'])
                    A.need(A.frozen(C.decode(rules,r['placements'],bad['length']))==r['proof'],'display binding');C.tree(rules,bad['target'],bad['length'],bad['hypotheses'],r)
                    for f in bad.get('frames',()):factors(bad,rules,f)
                except (ValueError,KeyError,IndexError):mutations.append(dict(case=case['id'],kind=kind))
                else:raise ValueError('mutation accepted '+case['id']+' '+kind)
        if 'compiled' in case:
            request,bindings=expected_compilation(dict(proof=good['proof'],target=case['target'],hypotheses=case['hypotheses'],atoms=None,signature=None))
            A.need(request==json.loads(json.dumps(case['compiled']['request'])) and bindings==json.loads(json.dumps(case['compiled']['bindings'])),'independent hypothesis/compiler mapping')
            A.need(whole_replay(request)['status']=='accepted','independent common kernel check')
        rows.append(dict(id=case['id'],accepted_lanes=accepted,trees=checks,frames=len(case.get('frames',()))));print(case['id'],'audited',flush=True)
    out=dict(version='factored-receptors-audit-001',producer_sha256=digest(path),source_sha256=digest(__file__),helper_sources={n:digest(HERE/n) for n in ('check_factored_receptors.py','check_propositional_receptors.py','audit_propositional_wang.py','audit_semantic_proofs.py')},
        cases=rows,mutations_rejected=mutations,policy_proposal_steps=policy_steps,seconds=time.perf_counter()-began,scope='Independent full inventory, exact counts and terminal trees, all positive t/m certificates, real factor frames, all frozen greedy proposal choices and source/compiler bindings; budget cutoffs remain unknown.')
    (DOC/'factored-receptors-audit-001.json').write_bytes(canonical(out)+b'\n');print('complete',out['seconds'],'mutations',len(mutations),flush=True)
if __name__=='__main__':main()
