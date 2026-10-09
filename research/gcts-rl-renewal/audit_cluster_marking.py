"""Independent cold cluster-label, scalar-exclusion and finite-region replay."""
import copy,dataclasses,hashlib,json,time
from collections import Counter
from pathlib import Path
from turtle import Model,State,SYMMETRIES,transform,compose,verify_patch,sub,add
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState,compose_type,verify_state
from cluster_learning import catalog,pair_expansion,seeded,Encoder,decorated,exact_keys,check_corona_failure,check_corona_positive
from region_tiles import RegionModel,unpack_state,verify_region
from run_regions import HERE,DOCS,problems
from run_cluster_marking import selected_types
from audit_geometry import audit as geometry_audit
from turtle import VERTICES

def normalized(x):return json.dumps(x,sort_keys=True,separators=(',',':'))

def main():
    start=time.monotonic();path=DOCS/'cluster-marking-001.json';d=json.loads(path.read_text());single,proto=selected_types()
    assert hashlib.sha256((DOCS/d['reuse']['artifact']).read_bytes()).hexdigest()==d['reuse']['sha256']
    assert normalized(dataclasses.asdict(proto))==normalized(d['configuration']['prototype'])
    for name,sha in d['source_sha256'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha
    plain=ClusterModel([proto]);keys=catalog(proto);base=Model();encoder=Encoder(proto,0);nodes=positive=rejected_tampers=0
    samples=d['labels']['samples'];sample_keys=[(s['second'][0],s['second'][1],tuple(s['second'][2])) for s in samples]
    assert sample_keys==keys and len(keys)==len(set(keys))
    for i,(key,s) in enumerate(zip(keys,samples)):
        seeds=pair_expansion(plain,key);assert exact_keys(s['seed_expansion'])==seeds
        if s['status']=='negative':
            ok,n=check_corona_failure(base,seeds,s['certificate']);assert ok,key;nodes+=n
        elif s['status']=='positive':
            assert check_corona_positive(base,seeds,s['witness']),key;positive+=1
            state=seeded(base,seeds)
            for k in exact_keys(s['witness'])[len(seeds):]:state.place(base.placement(k))
            assert state.tile_generations==s['tile_generations']
        else:assert s['status']=='unresolved'
        # The independent proof checker never uses these provisional values.
        encoder.add(dict(s,second=key))
        if (i+1)%30==0:print('independent cluster labels',i+1,'of',len(samples),'proof nodes',nodes,flush=True)
    marking,stats=encoder.finish()
    assert normalized(sorted(marking.items()))==normalized(d['marking_for_inspection_only'])
    for name in ['assigned','free','colors','positive_accepted','negative_rejected','unresolved_rejected','history']:
        assert normalized(stats[name])==normalized(d['marking'][name])
    # Independent enumeration of every possible scalar disagreement. Neither
    # the capacity-contact catalog nor the marked placement cache supplies it.
    root=set(proto.expansion);universe={(proto.identity,o,sub(p,transform(q,g))) for p in marking for o,g in enumerate(SYMMETRIES) for q in marking}
    disagreements=set()
    for key in universe:
        name,o,tr=key;expansion=moved(proto.expansion,SYMMETRIES[o],tr)
        if root&set(expansion) or not verify_patch(base,tuple(proto.expansion)+tuple(expansion)):continue
        if any((world:=add(transform(p,SYMMETRIES[o]),tr)) in marking and marking[world]!=v for p,v in marking.items()):disagreements.add(key)
    assert normalized(sorted(disagreements))==normalized(d['canonical_disagreements'])
    by_key=dict(zip(sample_keys,samples));assert disagreements<=by_key.keys();assert all(by_key[k]['status']=='negative' for k in disagreements)
    marked=decorated(proto,marking);mm=ClusterModel([marked]);symmetry_checks=0
    for o,g in enumerate(SYMMETRIES):
        r=ClusterState();r.place(mm.placement((proto.identity,o,(0,0,0))),seed=True)
        for key in keys:
            transformed=(proto.identity,SYMMETRIES.index(compose(g,SYMMETRIES[key[1]])),transform(key[2],g))
            assert r.legal(mm.placement(transformed))==(key not in disagreements);symmetry_checks+=1
    # Every exclusion has a checked complete base failure tree. Scalar action
    # transfers it to every root pose and translation. This does not assert
    # existence of a plane tiling or extension of every finite marked patch.
    models={};completed_states=base_placements=0;region_patches=[];training,evals=problems();boundaries={b.identity:b for b,m in training+evals}
    def replay(r,learned):
        nonlocal completed_states,base_placements,rejected_tampers
        boundary=boundaries[r['problem']];k=boundary,learned
        if k not in models:models[k]=RegionModel([single,marked if learned else proto],boundary)
        model=models[k];s=unpack_state(model,boundary,r['state']);complete=r['status']=='finite_exact_region'
        assert verify_region(model,boundary,s,complete);completed_states+=complete;base_placements+=r['accepted_base_tiles']
        if complete:
            for field in ['totals','tile_generations','base_expansion']:
                bad=copy.deepcopy(r['state']);bad[field]=[]
                try:unpack_state(model,boundary,bad)
                except ValueError:rejected_tampers+=1
                else:raise AssertionError('altered region certificate accepted')
    for r in d['training']['episodes']:replay(r,False)
    assert normalized(d['problems'])==normalized([{'boundary':b.packed(),'construction':m} for b,m in evals])
    for r in d['evaluation']:
        replay(r,r['lane'] in ('GCTS','GCTS+RL'))
        if r['status']=='finite_exact_region':region_patches.append({'seed':r['seed'],'lane':r['lane']+'/'+r['problem'],'placements':r['state']['base_expansion']})
    pos=next(s for s in samples if s['status']=='positive');key=(pos['second'][0],pos['second'][1],tuple(pos['second'][2]))
    parent=compose_type(mm,'marked-cluster-parent',[(proto.identity,0,(0,0,0)),key])
    assert normalized(dataclasses.asdict(parent))==normalized(d['parent']);pm=ClusterModel([marked,parent])
    for o in range(12):
        s=ClusterState();s.place(pm.placement((parent.identity,o,(0,0,0))),seed=True);assert verify_state(pm,s)
    branched=next(s for s in samples if s['status']=='negative' and 'children' in s['certificate'])
    bad=copy.deepcopy(branched['certificate']);bad['children'].pop()
    assert not check_corona_failure(base,branched['seed_expansion'],bad)[0];rejected_tampers+=1
    bad=copy.deepcopy(pos['witness']);bad[0][0]=True
    assert not check_corona_positive(base,pos['seed_expansion'],bad);rejected_tampers+=1
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':region_patches})
    audit={'all_contact_labels_checked':len(samples),'positive_witnesses_checked':positive,'negative_proof_nodes_checked':nodes,
        'canonical_exclusions_checked':len(disagreements),'scalar_symmetry_contact_checks':symmetry_checks,
        'finite_states_replayed':len(d['training']['episodes'])+len(d['evaluation']),'completed_states':completed_states,
        'new_base_placements_replayed':base_placements,'tampered_certificates_rejected':rejected_tampers,
        'parent_transformed_expansions_checked':12,'geometry':geometry,'seconds':time.monotonic()-start,
        'conditional_lemma':'every complete unmarked base point-model tiling, decorated by disjoint occurrences of this cluster, satisfies the scalar own-level marking',
        'scope':'all possible scalar disagreements for one cluster type; unmarked complete-base proof trees; no plane existence or finite-prefix preservation theorem',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    d['independent_audit']=audit;d['marking']['status']='certified redundant for disjoint cluster decorations of complete unmarked base point tilings'
    d['scope']='independently checked own-level cluster marking; conditional complete-point-tiling redundancy; finite region experiments'
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in audit.items() if k!='geometry'},indent=2),flush=True)

if __name__=='__main__':main()
