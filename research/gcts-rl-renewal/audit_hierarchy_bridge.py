"""Independent case-cover, refinement, scheduler and logical rectangle checks."""
import copy,dataclasses,hashlib,json,resource,time
from turtle import Model,SYMMETRIES,compose,transform,add,sub,VERTICES
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState,verify_state
from cluster_learning import check_corona_failure,check_corona_positive,exact_point,exact_keys
from coarse_continuation import LiteralOracle,root_state,exact_key,check_failure
from hierarchy_bridge import HERE,DOCS,PARENT,definitions,next_family,normal,proof_catalog
from kernel_machine import KernelMachine,immutable
from audit_kernel_machine import audit_catalog
from audit_geometry import audit as geometry_audit
import kernel_search,proof_search,lazy_wang

def check_point_lemma(free,marked,stage,lemma):
    """The marked graph does not supply this checker's unmarked case universe."""
    count=0
    try:
        p=tuple(lemma['point']);s=root_state(free,PARENT);ms=root_state(marked,PARENT)
        if not exact_point(p) or lemma['root']!=PARENT or normal(lemma['active_types'])!=[PARENT]:return False,count
        if type(lemma['root_units']) is not int or type(lemma['capacity']) is not int or lemma['capacity']!=12 or s.totals.get(p,0)!=lemma['root_units'] or not 0<s.totals[p]<12:return False,count
        oracle=LiteralOracle(free,(PARENT,));keys=oracle.domain(s,p)
        actual=[exact_key(r['placement'],(PARENT,)) for r in lemma['cases']]
        if not keys or len(actual)!=len(set(actual)) or set(actual)!=keys:return False,count
        if normal(lemma['marked_root_certificate'])!={'dead':list(p)} or LiteralOracle(marked,(PARENT,)).domain(ms,p):return False,count
        marked_model=ClusterModel(marked)
        for case,k in zip(lemma['cases'],actual):
            i=case['source_sample']
            if type(i) is not int or not 0<=i<len(stage['samples']):return False,count
            r=stage['samples'][i];c=marked_model.placement(k);fixed=tuple(sorted(s.owned_base|set(c.expansion)))
            if normal(r['contact'])!=normal((PARENT,PARENT,k[1],k[2])) or r['status']!='negative' or fixed!=exact_keys(r['seed_expansion']):return False,count
            ok,n=check_corona_failure(Model(),fixed,r['certificate']);count+=n
            if not ok or type(case['base_failure_nodes']) is not int or case['base_failure_nodes']!=n:return False,count
            disputes=[(q,ms.marks[q],v) for q,v in c.marks if q in ms.marks and ms.marks[q]!=v]
            if not disputes or normal(disputes)!=normal(case['disagreements']):return False,count
        return type(lemma['base_failure_nodes']) is int and count==lemma['base_failure_nodes'],count
    except (KeyError,ValueError,TypeError,IndexError):return False,count

def replay_coarse(defs,r):
    try:
        active=tuple(r['active_types']);s=root_state(defs,r['root']);model=ClusterModel(defs);oracle=LiteralOracle(defs,active)
        required=set(s.totals)
        if normal(sorted(required))!=r['required']:return False
        order=[exact_key(k,active) for k in r['placements']]
        if order[0]!=(r['root'],0,(0,0,0)) or len(r['execution'])!=len(order)-1:return False
        for step,key in zip(r['execution'],order[1:]):
            domains=oracle.domains(s)
            if not domains or any(not cs for cs in domains.values()):return False
            forced=sorted(p for p,cs in domains.items() if len(cs)==1)
            p=forced[0] if forced else min(domains,key=lambda p:(s.generations[p],len(domains[p]),p))
            if normal(step['point'])!=normal(p) or step['kind']!=('forced' if forced else 'branch') or exact_key(step['placement'],active)!=key or key not in domains[p]:return False
            s.place(model.placement(key))
        if normal(sorted(s.owned_base))!=r['base_expansion'] or s.tile_generations!=r['tile_generations'] or not verify_state(model,s):return False
        if r['covered']!=sum(s.totals.get(p,0)==12 for p in required):return False
        if r['status']=='positive':return verify_state(model,s,required) and all(oracle.domains(s).values()) and r['certificate'] is None
        if r['status']=='negative':return check_failure(defs,active,r['root'],r['certificate'])[0]
        return r['status']=='unresolved' and r['certificate'] is None
    except (KeyError,ValueError,TypeError,IndexError):return False

def main():
    start=time.monotonic();path=DOCS/'hierarchy-bridge-001.json';d=json.loads(path.read_text());reuse=d['reuse']
    for n,h in d['sources'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,n
    raw=(DOCS/reuse['artifact']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reuse['sha256'];previous=json.loads(raw)
    raw=(DOCS/reuse['stage_artifact']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reuse['stage_sha256'];stage=json.loads(raw)
    free=definitions(previous,'aggregate unmarked');marked=definitions(previous,'aggregate GCTS')
    free_ten,provenance=next_family(free,stage);marked_ten,mp=next_family(marked,stage)
    defs={'free':free+free_ten,'marked':marked+marked_ten}
    assert normal(provenance)==d['promotion']==normal(mp)
    assert d['inventories']==normal({n:[dataclasses.asdict(t) for t in ts] for n,ts in defs.items()})
    assert d['ten_types']==[t.identity for t in free_ten]
    positive_indices={i for i,s in enumerate(stage['samples']) if s['status']=='positive'};aliases=set();positives=0
    shape_by_index={i:t for t,p in zip(free_ten,provenance) for i in p['samples']}
    parent=next(t for t in free if t.identity==PARENT)
    for i in positive_indices:
        s=stage['samples'][i];a,b,o,tr=s['contact'];assert a==b==PARENT
        fixed=tuple(sorted(parent.expansion+moved(parent.expansion,SYMMETRIES[o],tuple(tr))))
        assert fixed==exact_keys(s['seed_expansion']) and check_corona_positive(Model(),fixed,s['witness']);positives+=1
        target=shape_by_index[i].expansion;valid=False
        for g in SYMMETRIES:
            moved_shape=moved(fixed,g)
            if any(tuple(sorted((o,sub(tr,origin)) for o,tr in moved_shape))==target for origin in {tr for o,tr in moved_shape}):valid=True;break
        assert valid;aliases.add(i)
    assert aliases==positive_indices
    for t in marked_ten:
        cm=ClusterModel(defs['marked']);cs=[cm.placement(k) for k in t.children]
        assert len(cs)==2 and all(c.key[0]==PARENT for c in cs) and not set(cs[0].expansion)&set(cs[1].expansion)
        assert tuple(sorted(cs[0].expansion+cs[1].expansion))==t.expansion
    ok,n=check_point_lemma(free,marked,stage,d['point_lemma']);assert ok
    tampers=0
    for mode in ('omit','pose','point','premise'):
        bad=copy.deepcopy(d['point_lemma'])
        if mode=='omit':bad['cases'].pop()
        elif mode=='pose':bad['cases'][0]['placement'][1]=True
        elif mode=='point':bad['point']=[999,-400,-599]
        else:bad['cases'][0]['source_sample']=next(i for i,s in enumerate(stage['samples']) if s['status']=='positive')
        assert not check_point_lemma(free,marked,stage,bad)[0];tampers+=1
    # All transformed roots have the same exhaustive seventeen-case cover.
    p=tuple(d['point_lemma']['point']);original={tuple((k['placement'][0],k['placement'][1],tuple(k['placement'][2]))) for k in d['point_lemma']['cases']};covariance=0
    for o,g in enumerate(SYMMETRIES):
        tr=(3,-5,2);s=ClusterState();s.place(ClusterModel(free).placement((PARENT,o,tr)),seed=True);q=add(transform(p,g),tr)
        expected={(name,SYMMETRIES.index(compose(g,SYMMETRIES[other])),add(transform(offset,g),tr)) for name,other,offset in original}
        assert LiteralOracle(free,(PARENT,)).domain(s,q)==expected
        ms=ClusterState();ms.place(ClusterModel(marked).placement((PARENT,o,tr)),seed=True);assert not LiteralOracle(marked,(PARENT,)).domain(ms,q);covariance+=1
    transformed=0
    for ts in defs.values():
        cm=ClusterModel(ts)
        for t in ts:
            for o in range(12):
                s=ClusterState();s.place(cm.placement((t.identity,o,(0,0,0))),seed=True);assert verify_state(cm,s);transformed+=1
    patches=[];coarse_nodes=scheduled=positive=0
    for r in d['coarse_runs']:
        ts=defs['free' if r['lane']=='free coarse' else 'marked'];assert replay_coarse(ts,r)
        scheduled+=len(r['execution']);positive+=r['status']=='positive'
        expected=(PARENT,) if r['root']==PARENT else tuple(d['ten_types'])
        if r['lane']=='marked + singleton refinement':expected=('base',)+expected
        assert normal(expected)==r['active_types']
        if r['status']=='negative':ok,ns=check_failure(ts,expected,r['root'],r['certificate']);assert ok;coarse_nodes+=ns
        if r['execution']:
            bad=copy.deepcopy(r);bad['execution'][0]['point']=[999,-400,-599];assert not replay_coarse(ts,bad);tampers+=1
        if r['status']=='positive':patches.append({'lane':r['lane']+'/'+r['root'],'seed':0,'placements':r['base_expansion']})
    fine=d['fine_only_refinement'];assert hashlib.sha256(json.dumps(d['inventories'],separators=(',',':')).encode()).hexdigest()==fine['inventory_sha256']
    fine_moves=fine_positive=fine_negative_nodes=0
    assert [r['root'] for r in fine['rows']]==[PARENT]+d['ten_types']
    for r in fine['rows']:
        t=next(t for t in defs['free'] if t.identity==r['root']);assert exact_keys(r['seed_expansion'])==t.expansion
        if r['status']=='positive':
            assert check_corona_positive(Model(),t.expansion,r['witness']);fine_positive+=1
            # Reapply the new base moves with the exact original marked root.
            s=root_state(defs['marked'],r['root']);cm=ClusterModel(defs['marked']);oracle=LiteralOracle(defs['marked'],('base',))
            keys=exact_keys(r['witness']);assert keys[:len(t.expansion)]==t.expansion
            for o,tr in keys[len(t.expansion):]:
                domains=oracle.domains(s);assert domains and all(domains.values())
                forced=sorted(p for p,cs in domains.items() if len(cs)==1)
                p=forced[0] if forced else min(domains,key=lambda p:(s.generations[p],len(domains[p]),p))
                key=('base',o,tr);assert key in domains[p];s.place(cm.placement(key));fine_moves+=1
            assert verify_state(cm,s,set(root_state(defs['marked'],r['root']).totals)) and all(oracle.domains(s).values())
            patches.append({'lane':'fine-only/'+r['root'],'seed':0,'placements':r['witness']})
        elif r['status']=='negative':
            ok,ns=check_corona_failure(Model(),t.expansion,r['certificate']);assert ok;fine_negative_nodes+=ns
        else:assert r['status']=='unresolved' and r['certificate'] is None
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    c,targets=proof_catalog();assert immutable(d['logical_declaration'])==c.declaration();catalog=audit_catalog(c)
    assert d['logical_training']['initial_weights']=={};machines={name:KernelMachine(c,target) for name,target in targets.items()}
    training_proofs=0
    for e in d['logical_training']['episodes']:
        m=machines[e['target']];r=m.run(m.tokens(tuple(e['commands'])));assert (r['status']=='accept')==e['verified']
        if e['verified']:c.proof(tuple(e['commands']),targets[e['target']]);training_proofs+=1
    rectangles=cells=0
    for r in d['logical_runs']:
        assert r['target'] in targets and r['length']==12 and r['height']==1536
        if not r.get('verified'):continue
        target=targets[r['target']];m=machines[r['target']];cert=r['certificate'];rows,tiles=proof_search.unpack(cert)
        assert kernel_search.replay(c,target,12,1536,cert);offset=len(c.formulas)+4;commands=m.parse(rows[0][offset:offset+12]);proof=c.proof(commands,target)
        assert immutable(r['kernel_proof'])==immutable(proof) and tuple(r['commands'])==commands
        assert c.kernel.check(proof,target);rectangles+=1;cells+=len(tiles)
        bad=copy.deepcopy(proof);bad[-1]['formula']=('bot',);assert not c.kernel.check(bad,('bot',));tampers+=1
        pattern=list(m.pattern(12));pattern[3]=('1',)
        assert not lazy_wang.independent_check(m.compiler,tuple(pattern),m.accepting_row(len(pattern)),rows,tiles,extended=cert['marking']=='redundant-neighbor-values');tampers+=1
    d['independent_audit']={'point_cases':len(original),'base_case_failure_nodes':n,'positive_source_contacts':positives,
        'refinement_types':len(free_ten),'case_cover_symmetries':covariance,'transformed_expansions':transformed,
        'coarse_states':len(d['coarse_runs']),'positive_coarse_states':positive,'coarse_failure_nodes':coarse_nodes,'scheduled_coarse_moves':scheduled,
        'fine_only_states':len(fine['rows']),'fine_only_positive':fine_positive,'fine_only_scheduled_new_moves':fine_moves,'fine_only_failure_nodes':fine_negative_nodes,
        'catalog':catalog,'training_sequences':len(d['logical_training']['episodes']),'training_proofs':training_proofs,
        'checked_rectangles':rectangles,'checked_wang_cells':cells,'tampered_certificates_rejected':tampers,'geometry':geometry,
        'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256((HERE/'audit_hierarchy_bridge.py').read_bytes()).hexdigest(),
        'helper_source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_geometry.py','audit_kernel_machine.py')},
        'scope':'finite case coverage and base proofs checked directly; whole-plane and refinement lifting are explicit analytic arguments; logical/Wang proofs are conditional on these externally checked geometry lemmas, not an internal formalization of infinite tilings'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k!='geometry'},indent=2),flush=True)

if __name__=='__main__':main()
