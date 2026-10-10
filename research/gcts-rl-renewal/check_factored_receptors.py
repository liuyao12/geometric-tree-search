"""Independent explicit inventory, point certificates and finite tree audit."""
import collections,itertools
import check_propositional_receptors as A

def inventory(mode,family=None):
    p,q=('P',),('Q',);i=lambda a,b:('imp',a,b);n=lambda a:('not',a)
    atoms=[p,q] if mode=='plain' else [p,q,n(p),n(q)]
    A.need(mode in ('plain','negated'),'external pool registry')
    params=atoms+[i(a,b) for a,b in itertools.product(atoms,repeat=2)];rules=[];terms=set()
    def sub(a):
        if a in terms:return
        terms.add(a)
        for b in a[1:]:sub(b)
    for a,b in itertools.product(params,repeat=2):rules.append(dict(kind='H1',inputs=(),output=i(a,i(b,a))))
    for a,b,c in itertools.product(params,repeat=3):rules.append(dict(kind='H2',inputs=(),output=i(i(a,i(b,c)),i(i(a,b),i(a,c)))))
    for a,b in itertools.product(params,repeat=2):rules.append(dict(kind='H3',inputs=(),output=i(i(n(b),n(a)),i(a,b))))
    for r in rules:sub(r['output'])
    for f in sorted(terms,key=A.word):
        if f[0]=='imp':rules.append(dict(kind='mp',inputs=(f[1],f),output=f[2]))
    if family:
        A.need(family['parameter']==p and family['conclusion']==i(p,p) and family['name']=='identity','registered family')
        A.logical(family['proof'],i(p,p),(),False)
        def replace(a,v):return v if a==p else (a[0],)+tuple(replace(b,v) for b in a[1:])
        for a in params:rules.append(dict(kind='lemma',name='identity',parameter=a,inputs=(),output=i(a,a),expansion=[dict(r,formula=replace(r['formula'],a)) for r in family['proof']]))
    return params,rules
def decode(rules,keys,length):
    A.need(len(keys)==length and {k[0] for k in keys}==set(range(length)),'whole proof coverage')
    out=[None]*length
    for slot,rid,refs in keys:
        A.need(0<=rid<len(rules),'rule identity');r=rules[rid]
        row=dict(kind=r['kind'],formula=r['output'],refs=refs)
        if r['kind']=='lemma':row.update(name=r['name'],parameter=r['parameter'],expansion=r['expansion'])
        out[slot]=row
    return out
def certificate(rules,target,length,hypotheses,keys,tiles):
    keys=A.frozen(keys);tiles=A.frozen(tiles);target=A.frozen(target);hypotheses=A.frozen(hypotheses)
    proof=decode(rules,keys,length);checked=A.logical(proof,target,hypotheses)
    def port(j,a):return [((2*j,2+k),v) for k,v in enumerate(A.word(a)+'e')]+[((2*j,1),0)]
    initial=port(length-1,target)+[entry for j,a in enumerate(hypotheses,-len(hypotheses)) for entry in port(j,a)]
    A.need(len(tiles)==length,'point tile count')
    for key,t in zip(keys,tiles):
        j,rid,refs=key;r=rules[rid];A.need(len(refs)==len(r['inputs']) and all(-len(hypotheses)<=v<j for v in refs),'backward references')
        marks={}
        for slot,f in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            for p,v in port(slot,f):A.need(p not in marks or marks[p]==v,'single-valued rule');marks[p]=v
        A.need(t['key']==key and t['occupancy']==(((2*j,0),12),) and t['marks']==tuple(sorted(marks.items())),'all t/m point data')
    result=A.sparse(initial,tiles,length)
    return dict(status='accepted',primitive_lines=checked['primitive_lines'],commands=length,**result)
def port_state(rules,target,length,hypotheses,chosen):
    ports={length-1:target}|{j:a for j,a in enumerate(hypotheses,-len(hypotheses))};filled=set()
    for j,rid,refs in chosen:
        A.need(j not in filled and 0<=j<length and 0<=rid<len(rules),'unique legal placement identity');filled.add(j);r=rules[rid]
        A.need(len(refs)==len(r['inputs']) and all(-len(hypotheses)<=v<j for v in refs),'reference domain')
        for p,a in [(j,r['output'])]+list(zip(refs,r['inputs'])):
            A.need(p not in ports or ports[p]==a,'global point-port agreement');ports[p]=a
    return filled,ports
def counts(rules,by_output,target,length,hypotheses,chosen):
    filled,ports=port_state(rules,target,length,hypotheses,chosen);degrees={}
    for j in range(length):
        if j in filled:continue
        count=0
        for rid in by_output.get(ports[j],()) if j in ports else range(len(rules)):
            r=rules[rid]
            if not r['inputs']:count+=1;continue
            xs=[k for k in range(-len(hypotheses),j) if k not in ports or ports[k]==r['inputs'][0]]
            ys=[k for k in range(-len(hypotheses),j) if k not in ports or ports[k]==r['inputs'][1]]
            # Deliberately enumerates the short reference pairs, independently
            # of the producer's mask product and diagonal subtraction.
            count+=sum(1 for x in xs for y in ys if x!=y)
        degrees[j]=count
    return degrees
def tree(rules,target,length,hypotheses,result):
    by_output=collections.defaultdict(list)
    for rid,r in enumerate(rules):by_output[r['output']].append(rid)
    totals=collections.Counter();leaf=None
    def decide(chosen):
        ds=counts(rules,by_output,target,length,hypotheses,chosen)
        dead=sorted(j for j,n in ds.items() if n==0);forced=sorted(j for j,n in ds.items() if n==1)
        if dead:return 'dead',(2*dead[0],0),0,ds
        if forced:return 'forced',(2*forced[0],0),1,ds
        if not ds:return 'empty',None,0,ds
        j=min(ds,key=lambda j:(ds[j],j));return 'branch',(2*j,0),ds[j],ds
    def visit(t,chosen):
        nonlocal leaf
        totals['nodes']+=1;kind,p,degree,ds=decide(chosen);totals['peak_candidate_nodes']=max(totals['peak_candidate_nodes'],sum(ds.values()))
        A.need(t['kind']==kind and t['point']==p,'global complete-degree decision')
        if kind=='dead':totals['dead']+=1;return False
        if kind=='empty':leaf=chosen;return True
        totals['forced' if kind=='forced' else 'branches']+=1;seen=set();ok=False
        for child in t['children']:
            key=child['key'];A.need(not ok and key not in seen and key[0]*2==p[0],'branch domain and unique alternatives')
            port_state(rules,target,length,hypotheses,chosen+(key,));seen.add(key);totals['attempts']+=1
            ok=visit(child['tree'],chosen+(key,))
            if not ok:totals['backtracks']+=1
        A.need(ok or len(seen)==degree,'all legal alternatives before exhaustion')
        return ok
    if result['search_tree'] is not None:
        ok=visit(result['search_tree'],());A.need(ok==(result['status']=='finite_exact_proof_tiling'),'tree status')
        A.need(not ok or leaf==result['placements'],'actual positive leaf')
        for k,v in totals.items():A.need(result['metrics'].get(k,0)==v,'exact tree counter '+k)
    else:A.need(result['status']=='unknown_search_budget','missing terminal tree')
    for s in result['samples']:
        kind,p,degree,_=decide(s['placed']);A.need((s['kind'],s['point'],s['degree'])==(kind,p,degree),'sample degrees')
    for proposal in result['proposals']:
        chosen=proposal['incoming'];A.need(1<=len(proposal['expansion'])<=3,'cluster expansion length')
        for key in proposal['expansion']:
            kind,p,_,_=decide(chosen);A.need(kind not in ('dead','empty') and key[0]*2==p[0],'proposal follows scheduler');port_state(rules,target,length,hypotheses,chosen+(key,));chosen+=(key,)
    h=len(hypotheses);schema=sum(not r['inputs'] for r in rules);mp=len(rules)-schema
    A.need(result['candidate_universe']==sum(schema+mp*(j+h)*(j+h-1) for j in range(length)),'complete initial universe count')
    return dict(status='complete_tree_replayed' if result['search_tree'] is not None else 'budget_unknown_samples_replayed',nodes=totals['nodes'])
