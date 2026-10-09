"""Literal local-response laws and complete finite-inventory schedule replay."""
import copy,hashlib,json,resource,time
from collections import Counter,defaultdict
from pathlib import Path
from turtle import BASE,SYMMETRIES
from audit_boundary_macros import Oracle,exact_key
from boundary_responses import declarations
from region_tiles import Boundary

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def normal(x):return json.loads(json.dumps(x))
def sha(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def point(p):return len(p)==3 and all(type(v) is int for v in p) and sum(p)==0
def compose_pose(a,b):
    sa,pa=SYMMETRIES[a];sb,pb=SYMMETRIES[b]
    return SYMMETRIES.index((sa*sb,tuple(pb[pa[j]] for j in range(3))))
def pose(k,o,tr):
    q,p=k;sign,perm=SYMMETRIES[o]
    return compose_pose(o,q),tuple(sign*p[i]+v for i,v in zip(perm,tr))
def values(k):
    o,tr=k;sign,perm=SYMMETRIES[o]
    return {tuple(sign*p[i]+v for i,v in zip(perm,tr)):n for p,n in BASE.items()}
def points(entries):
    if any(not point(p) or type(v) is not int for p,v in entries):raise ValueError('invalid exact trace')
    d={tuple(p):v for p,v in entries}
    if len(d)!=len(entries):raise ValueError('duplicate trace point')
    return d
def expansion(seq):
    out=[]
    for o,tr in seq:
        if type(o) is not int or not 0<=o<12 or not point(tr):raise ValueError('invalid exact response pose')
        out.append((o,tuple(tr)))
    if not out or len(set(out))!=len(out):raise ValueError('duplicate or empty ownership')
    return tuple(out)

def certify(library):
    nodes={r['identity']:r for r in library['nodes']}
    if len(nodes)!=len(library['nodes']) or len(set(library['selected']))!=len(library['selected']):raise ValueError('duplicate identity')
    checked={};child_maps=0
    for name,r in nodes.items():
        seq=expansion(r['sequence']);iv=points(r['incoming']);dv=points(r['delta']);ov=points(r['outgoing']);actual=Counter()
        for key in seq:actual.update(values(key))
        if seq[0][1]!=(0,0,0) or type(r['pose'][0]) is not int or not point(r['pose'][1]) or r['pose']!=[0,[0,0,0]]:raise ValueError('unnormalized operation')
        if set(iv)!=set(actual) or dv!=dict(actual) or set(ov)!=set(iv):raise ValueError('incomplete support or altered delta')
        if any(not 0<=iv[p]<=12 or ov[p]!=iv[p]+dv[p] or ov[p]>12 for p in iv):raise ValueError('false local response')
        if name!='response-'+sha((seq,tuple(sorted(iv.items()))))[:24]:raise ValueError('false semantic identity')
        if type(r['level']) is not int or r['level']<0:raise ValueError('invalid level')
        checked[name]=(seq,iv,dv,ov)
    for name,r in nodes.items():
        seq,iv,dv,ov=checked[name]
        if len(seq)==1:
            if r['children'] or r['level']:raise ValueError('false leaf')
            continue
        if len(r['children'])!=2:raise ValueError('false composition')
        children=[]
        for child,o,tr in r['children']:
            if child not in nodes or type(o) is not int or not 0<=o<12 or not point(tr):raise ValueError('invalid child map')
            if nodes[child]['level']>=r['level']:raise ValueError('non-descending hierarchy')
            cs,ci,cd,co=checked[child];sign,perm=SYMMETRIES[o]
            def move(d):return {tuple(sign*p[i]+v for i,v in zip(perm,tr)):n for p,n in d.items()}
            children.append((tuple(pose(k,o,tr) for k in cs),move(ci),move(cd),move(co)));child_maps+=1
        a,b=children
        if set(a[0])&set(b[0]) or a[0]+b[0]!=seq:raise ValueError('overlapping or altered expansion')
        if any(a[3][p]!=b[1][p] for p in a[1].keys()&b[1].keys()):raise ValueError('incompatible response interface')
        ci=a[1]|{p:v for p,v in b[1].items() if p not in a[1]};cd=Counter(a[2]);cd.update(b[2])
        if ci!=iv or dict(cd)!=dv or r['level']!=1+max(nodes[c[0]]['level'] for c in r['children']):raise ValueError('false parent law')
    if any(name not in checked or len(checked[name][0])<2 for name in library['selected']):raise ValueError('invalid selected response')
    return checked,child_maps

def matched_execution(r,b,oracle,library,trace):
    """Verify proposed identities, prefix offsets and local preconditions."""
    nodes,_=certify(library);totals=Counter(dict(b.exterior));owned=set(b.owned);current=None;offset=0
    for step in r['execution']:
        k=exact_key(step['placement']);name=step.get('response','singleton')
        if any(type(step[f]) is not int for f in ('proposal_size','proposal_offset')):return False
        if name=='singleton':
            if step['proposal_size']!=1 or step['proposal_offset']!=0:return False
            current=None
        else:
            if name not in library['selected']:return False
            if step['proposal_offset']==0:
                seq,iv,dv,ov=nodes[name];g=next(o for o in range(12) if compose_pose(o,seq[0][0])==k[1]);tr=k[2]
                current=tuple(('base',q,p) for q,p in (pose(x,g,tr) for x in seq));offset=0
                if step['proposal_size']!=len(seq) or any(x not in oracle.values or (x[1],x[2]) in owned for x in current):return False
                sign,perm=SYMMETRIES[g]
                def move(d):return {tuple(sign*p[i]+v for i,v in zip(perm,tr)):n for p,n in d.items()}
                if trace and any(totals[p]!=v for p,v in move(iv).items()):return False
                if not trace and any(totals[p]+v>12 for p,v in move(dv).items()):return False
            if current is None or step['proposal_offset']!=offset or offset>=len(current) or k!=current[offset]:return False
            offset+=1
        totals.update(dict(oracle.values[k]));owned.add((k[1],k[2]))
    return True

def domains(oracle,b,totals,owned):
    out={p:set() for p in b.required if totals.get(p,0)<12}
    for k,occ in oracle.values.items():
        if (k[1],k[2]) in owned or any(totals.get(p,0)+v>12 for p,v in occ):continue
        for p,v in occ:
            if p in out:out[p].add(k)
    return out

def main():
    start=time.monotonic();path=DOCS/'boundary-responses-001.json';d=json.loads(path.read_text())
    for name,s in d['sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==s
    train=declarations(True);evals=declarations();bs={b.identity:b for b in (*train,*evals)}
    assert d['training_problems']==normal([b.packed() for b in train]) and d['problems']==normal([b.packed() for b in evals])
    for b in map(Boundary.unpack,d['movable_family']):bs[b.identity]=b
    assert d['movable_family']==normal([Boundary('moving-outer',train[0].allowed,train[0].allowed).packed(),
                                      Boundary('moving-inner-8',evals[2].required,train[0].allowed).packed(),
                                      Boundary('moving-inner-6',evals[1].required,train[0].allowed).packed()])
    assert d['training']['initial_weights']=={} and d['training']['initial_marking']=={} and not d['training']['imported_artifact']
    assert [r['seed'] for r in d['donors']]==list(range(110000,110016))
    assert [r['seed'] for r in d['training']['episodes']]==list(range(111000,111048))
    oracle=Oracle(train[0].allowed);assert len(oracle.values)==d['inventory']['placements']
    nodes,maps=certify(d['library']);checked=complete=moves=matched=0
    def replay(r,b,mode=None):
        nonlocal checked,complete,moves,matched
        assert oracle.replay(r,b)
        if mode is not None:assert matched_execution(r,b,oracle,d['library'],mode);matched+=1
        checked+=1;complete+=r['status']=='finite_exact_region';moves+=len(r['execution'])
    for r in d['donors']:replay(r,bs[r['problem']])
    donor_by_seed={r['seed']:r for r in d['donors']};provenance=0
    for name,occurrences in d['library']['provenance'].items():
        assert name in d['library']['selected'] and d['library']['counts'][name]==len(occurrences)
        for p in occurrences:
            donor=donor_by_seed[p['seed']];assert donor['status']=='finite_exact_region' and donor['problem']==p['problem']
            keys=tuple((o,tuple(tr)) for n,o,tr in donor['state']['placements']);begin=p['begin'];size=p['size'];seq=keys[begin:begin+size]
            assert size==len(seq) and size>=2 and type(begin) is int and begin>=0
            input_values=Counter(dict(bs[p['problem']].exterior))
            for key in keys[:begin]:input_values.update(values(key))
            origin=seq[0][1];normalized=tuple((o,tuple(a-b for a,b in zip(tr,origin))) for o,tr in seq)
            support=set().union(*(values(key) for key in seq));incoming={tuple(a-b for a,b in zip(p,origin)):input_values[p] for p in support}
            assert nodes[name][0]==normalized and nodes[name][1]==incoming;provenance+=1
    for r in d['training']['episodes']:replay(r,bs[r['problem']],True)
    for r in d['evaluation']:replay(r,bs[r['problem']],None if r['lane']=='base' else r['lane']!='geometry')
    for c in d['zero_controls']:
        assert all(c['results'][0][f]==c['results'][1][f] for f in c['fields'])
        for r in c['results']:replay(r,bs[c['problem']],True)
    for m in d['movable_evaluation']:
        for a in m['attempts']:replay(a['result'],bs[a['boundary']],None if m['lane']=='base' else m['lane']!='geometry')
        winners=[a['boundary'] for a in m['attempts'] if a['result']['status']=='finite_exact_region']
        assert m['selected']==(winners[0] if winners else None)
    # Compare literal domains with incremental indexes at exported training
    # and irregular/exterior states. Proposal records never supply degrees.
    from resident_regions import Universe
    from boundary_macros import singleton
    from turtle import Graph
    from region_tiles import unpack_state
    u=Universe((singleton(),),train[0].allowed);graph_checks=0
    for r in (*d['donors'][:4],*(r for r in d['evaluation'] if r['lane']=='trace-hierarchy+zero')):
        b=bs[r['problem']];model=u.bind(b);s=unpack_state(model,b,r['state']);g=Graph(model,s)
        assert g.domains==domains(oracle,b,s.totals,s.owned_base)
        assert all(g.edges[k]=={p for p,ks in g.domains.items() if k in ks} for k in g.edges);graph_checks+=1
    symmetry=0
    for name in d['library']['selected']:
        seq,iv,dv,ov=nodes[name]
        for o,(sign,perm) in enumerate(SYMMETRIES):
            offset=(7,-4,-3);new=Counter()
            for k in seq:new.update(values(pose(k,o,offset)))
            expected={tuple(sign*p[i]+v for i,v in zip(perm,offset)):n for p,n in dv.items()}
            assert dict(new)==expected;symmetry+=1
    bad_cases=[];root=next(n for n in d['library']['nodes'] if n['children'])
    for kind in ('missing-input','input-bool','false-output','duplicate-owner','child-offset','child-level','unknown-child','duplicate-node'):
        bad=copy.deepcopy(d['library']);r=next(n for n in bad['nodes'] if n['identity']==root['identity'])
        if kind=='missing-input':r['incoming'].pop()
        if kind=='input-bool':r['incoming'][0][1]=True
        if kind=='false-output':r['outgoing'][0][1]-=1
        if kind=='duplicate-owner':r['sequence'].append(r['sequence'][0])
        if kind=='child-offset':r['children'][1][2]=[99,-49,-50]
        if kind=='child-level':r['level']=0
        if kind=='unknown-child':r['children'][0][0]='absent'
        if kind=='duplicate-node':bad['nodes'].append(bad['nodes'][0])
        try:certify(bad)
        except (ValueError,KeyError,IndexError,TypeError):bad_cases.append(kind)
        else:raise AssertionError('accepted tamper '+kind)
    sample=next(r for r in d['evaluation'] if r['execution']);b=bs[sample['problem']]
    for kind in ('schedule','generation','ownership'):
        bad=copy.deepcopy(sample)
        if kind=='schedule':bad['execution'][0]['point']=[90,-45,-45]
        if kind=='generation':bad['state']['tile_generations'][0]=True
        if kind=='ownership':bad['state']['base_expansion']=[]
        assert not oracle.replay(bad,b);bad_cases.append(kind)
    d['independent_audit']={'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                           'helper_sha256':hashlib.sha256((HERE/'audit_boundary_macros.py').read_bytes()).hexdigest(),
                           'nodes':len(nodes),'child_maps':maps,'selected_responses':len(d['library']['selected']),
                           'donor_occurrences':provenance,'states':checked,'complete_states':complete,'scheduled_moves':moves,
                           'proposal_prefixes_checked_states':matched,'literal_graph_checks':graph_checks,'transformed_operations':symmetry,
                           'tamper_rejections':bad_cases,'seconds':time.monotonic()-start,
                           'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                           'scope':'all saved moves and local composition laws; no full global boundary relation, infinite extension, or exhausted heuristic proof'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(d['independent_audit']),flush=True)

if __name__=='__main__':main()
