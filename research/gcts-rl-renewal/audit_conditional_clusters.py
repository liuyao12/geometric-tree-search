"""Independent literal capacity schemas, compiled placements and path replay."""
import copy,hashlib,json,resource,time
from collections import Counter,defaultdict
from pathlib import Path
from turtle import SYMMETRIES,VERTICES
from region_tiles import Boundary
from audit_boundary_macros import Oracle,exact_key
from audit_boundary_responses import certify,pose,points,normal
from audit_frontier_responses import literal_prefix,reconstruct_updates,check_sample as old_sample
from audit_geometry import audit as geometry_audit

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
MODES=('base','small','hierarchy')
def hex_points(r):return {(x,y,-x-y) for x in range(-r,r+1) for y in range(-r,r+1) if abs(x+y)<=r}
def shifted(ps,c):return {tuple(a+b for a,b in zip(p,c)) for p in ps}
def authored(oracle):
    allowed=frozenset(hex_points(18));train=[];evals=[];families=[]
    for i,(length,width) in enumerate(((5,3),(7,4),(9,2))):train.append(Boundary('conditional-train-strip-'+str(i),frozenset(p for p in allowed if abs(p[0])<=length and abs(2*p[1]+p[0])<=width),allowed))
    for i,(outer,inner) in enumerate(((5,2),(7,3))):train.append(Boundary('conditional-train-ring-'+str(i),frozenset(hex_points(outer)-hex_points(inner)),allowed))
    train.append(Boundary('conditional-train-lobes',frozenset(shifted(hex_points(4),(-3,2,1))|shifted(hex_points(4),(3,-2,-1))),allowed))
    train.append(Boundary('conditional-train-exterior',frozenset(shifted(hex_points(4),(-1,1,0))),allowed,tuple(oracle.values['base',2,(5,-3,-2)]),(),((2,(5,-3,-2)),)))
    evals.append(Boundary('conditional-long-strip',frozenset(p for p in allowed if abs(p[0])<=11 and abs(2*p[1]+p[0])<=6),allowed))
    evals.append(Boundary('conditional-annulus',frozenset(hex_points(9)-hex_points(4)),allowed))
    evals.append(Boundary('conditional-two-lobes',frozenset(shifted(hex_points(5),(-5,3,2))|shifted(hex_points(5),(5,-3,-2))),allowed))
    evals.append(Boundary('conditional-fixed-and-pocket',frozenset(shifted(hex_points(6),(1,0,-1))|{(-12,6,6),(-11,6,5)}),allowed,tuple(oracle.values['base',5,(7,-4,-3)]),(),((5,(7,-4,-3)),)))
    for direction in (0,1):
        families.append(tuple(Boundary('conditional-moving-'+str(direction)+'-'+str(s),frozenset(p for p in allowed if abs(p[direction])<=9 and abs(2*p[(direction+1)%3]+p[direction]-s)<=5),allowed) for s in (-2,0,2)))
    return train,evals,families

def moved_values(values,o,tr):
    sign,perm=SYMMETRIES[o];return {tuple(sign*p[i]+v for i,v in zip(perm,tr)):n for p,n in values.items()}
def placed(nodes,name,g,tr):
    seq,iv,dv,ov=nodes[name];members=tuple(('base',o,p) for o,p in (pose(k,g,tr) for k in seq))
    return members,moved_values(iv,g,tr),moved_values(dv,g,tr)

def replay_responses(r,b,oracle,nodes,selected):
    totals=Counter(dict(b.exterior));owned=set(b.owned);remaining=None;offset=0;current=None;reordered=0
    for s in r['execution']:
        k=exact_key(s['placement']);name=s['response']
        if type(s['proposal_size']) is not int or type(s['proposal_offset']) is not int:return False,0
        if r.get('condition') and (s['condition']!=r['condition'] or s['adaptive']!=r['adaptive']):return False,0
        if name=='singleton':
            if s['proposal_size']!=1 or s['proposal_offset']!=0:return False,0
            remaining=None;current=None
        else:
            if name not in selected:return False,0
            g,tr=s['proposal_pose'];tr=tuple(tr)
            if type(g) is not int or not 0<=g<12 or len(tr)!=3 or any(type(x) is not int for x in tr) or sum(tr):return False,0
            if s['proposal_offset']==0:
                members,iv,dv=placed(nodes,name,g,tr)
                if k not in members or s['proposal_size']!=len(members) or any(q not in oracle.values or (q[1],q[2]) in owned for q in members):return False,0
                if r['condition']=='trace' and any(totals[p]!=v for p,v in iv.items()):return False,0
                if r['condition']=='interval' and any(totals[p]+v>12 for p,v in dv.items()):return False,0
                remaining=[k]+[q for q in members if q!=k];offset=0;current=(name,g,tr)
            if remaining is None or current!=(name,g,tr) or s['proposal_offset']!=offset or k not in remaining:return False,0
            if not r['adaptive'] and k!=remaining[0]:return False,0
            reordered+=k!=remaining[0];remaining.remove(k);offset+=1
        totals.update(dict(oracle.values[k]));owned.add((k[1],k[2]))
    return True,reordered

def check_sample(s,b,oracle,nodes,adaptive,weights=None):
    totals,owned,gens=literal_prefix(oracle,b,s['placements']);ds={p:set() for p in b.required if totals.get(p,0)<12}
    for k,occ in oracle.values.items():
        if (k[1],k[2]) in owned or any(totals.get(p,0)+v>12 for p,v in occ):continue
        for p,v in occ:
            if p in ds:ds[p].add(k)
    if not ds or any(not v for v in ds.values()):return False
    forced=sorted(p for p,v in ds.items() if len(v)==1);p=forced[0] if forced else min(ds,key=lambda p:(gens[p],len(ds[p]),p))
    keys=[exact_key(k) for k in s['domain']];order=[exact_key(k) for k in s['ordered']]
    if tuple(s['point'])!=p or s['kind']!=('forced' if forced else 'branch') or set(keys)!=ds[p] or len(keys)!=len(ds[p]):return False
    if set(order)!=set(keys) or len(order)!=len(set(order)):return False
    if s['pending']:
        a=s['pending'];g,tr=a['pose'];members,iv,dv=placed(nodes,a['response'],g,tuple(tr));given=tuple(exact_key(k) for k in a['members']);remaining=tuple(exact_key(k) for k in a['remaining'])
        if set(given)!=set(members) or len(given)!=len(members) or given[1:]!=tuple(k for k in members if k!=given[0]):return False
        if remaining!=tuple(k for k in given if (k[1],k[2]) not in owned) or a['used']!=len(members)-len(remaining):return False
        delta=Counter()
        for k in remaining:delta.update(dict(oracle.values[k]))
        if any(totals.get(p,0)+v>12 for p,v in delta.items()):return False
        eligible=tuple(k for k in remaining if k in keys) if adaptive else remaining[:1] if remaining and remaining[0] in keys else ()
        if not eligible or (not forced and tuple(order[:len(eligible)])!=eligible):return False
    fs=s['mode_features']
    if fs is not None:
        feedback={(m,k):v for m,k,v in s['feedback']};degrees=list(map(len,ds.values()));expected=[]
        for m in MODES:
            values={'bias':1.,'remaining':1-sum(totals.get(p,0)==12 for p in b.required)/len(b.required),'domain':len(keys)/50,
                'mean_degree':sum(degrees)/len(degrees)/50,'low_degree':sum(d<=2 for d in degrees)/len(degrees),
                'frontier':len(ds)/300,'accepted':len(s['placements'])/100,'contact':sum(totals.get(p,0)>0 for p in ds)/len(ds),
                'interruption':feedback.get((m,'interrupted'),0)/max(1,feedback.get((m,'closed'),0))}
            expected.append({'mode:'+m+':'+k:v for k,v in values.items()})
        if fs!=expected:return False
        if weights is not None:
            scores=[sum(weights.get(k,0)*v for k,v in f.items()) for f in fs]
            if scores[MODES.index(s['mode'])]!=max(scores):return False
    return True

def main():
    start=time.monotonic();path=DOCS/'conditional-clusters-001.json';d=json.loads(path.read_text())
    for n,sha in d['sources'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha
    raw=(DOCS/d['source_artifact']).read_bytes();assert hashlib.sha256(raw).hexdigest()==d['source_sha256'];parent=json.loads(raw)
    nodes,maps=certify(parent['library']);source_nodes={r['identity']:r for r in parent['library']['nodes']}
    assert len(d['interfaces'])==len(nodes) and len({r['identity'] for r in d['interfaces']})==len(nodes)
    compositions=0
    for r in d['interfaces']:
        seq,iv,dv,ov=nodes[r['identity']];upper=points(r['upper']);assert points(r['delta'])==dv and upper=={p:12-v for p,v in dv.items()}
        assert all(v>=0 for v in upper.values()) and r['children']==source_nodes[r['identity']]['children'] and r['level']==source_nodes[r['identity']]['level']
        if r['children']:
            deltas=[placed(nodes,n,o,tuple(tr))[2] for n,o,tr in r['children']];a,b=deltas
            for p in dv:assert upper[p]==min(12-a.get(p,0),12-b.get(p,0)-a.get(p,0))
            compositions+=1
    oracle=Oracle(frozenset(hex_points(18)));train,evals,families=authored(oracle)
    # Sort exterior support because independent literal orientation enumeration
    # retains a different harmless point serialization order.
    def canon_boundary(b):
        x=b.packed();x['exterior']=sorted(x['exterior']);return normal(x)
    def canon_saved(x):
        x=copy.deepcopy(x);x['exterior']=sorted(x['exterior']);return x
    assert [canon_boundary(b) for b in train]==[canon_saved(x) for x in d['training_problems']]
    assert [canon_boundary(b) for b in evals]==[canon_saved(x) for x in d['problems']]
    assert normal([[b.packed() for b in f] for f in families])==d['movable_families']
    assert set(b.required for b in train).isdisjoint(b.required for b in evals)
    assert set(tuple(map(tuple,b['required'])) for b in parent['problems']).isdisjoint(tuple(sorted(b.required)) for b in evals)
    bs={b.identity:b for b in (*train,*evals,*(b for f in families for b in f))};assert len(oracle.values)==d['inventory']['placements']
    # Brute anchor-and-membership compilation, not the producer's intersections.
    by_o=defaultdict(list)
    for k in sorted(oracle.values):by_o[k[1]].append(k)
    h=hashlib.sha256();poses=incidences=0;keys=set();sizes=Counter()
    for name in sorted(parent['library']['selected']):
        for g in range(12):
            first=pose(nodes[name][0][0],g,(0,0,0))
            for key in by_o[first[0]]:
                tr=tuple(a-b for a,b in zip(key[2],first[1]));members=placed(nodes,name,g,tr)[0]
                if any(k not in oracle.values for k in members):continue
                h.update((json.dumps((name,g,tr,members),separators=(',',':'))+'\n').encode());poses+=1;incidences+=len(members);keys.update(members);sizes[len(members)]+=1
    assert d['atlas']['templates']==12*len(parent['library']['selected']) and d['atlas']['placements']==poses
    assert d['atlas']['member_incidences']==incidences and d['atlas']['indexed_base_keys']==len(keys)
    assert d['atlas']['placement_sha256']==h.hexdigest() and d['atlas']['sizes']=={str(k):v for k,v in sizes.items()}
    states=moves=samples=complete=reordered=0;patches=[]
    def replay(r,b,lane=None):
        nonlocal states,moves,samples,complete,reordered
        assert oracle.replay(r,b),'literal scheduler replay failed'
        if r.get('condition'):
            valid,n=replay_responses(r,b,oracle,nodes,set(parent['library']['selected']));assert valid,'conditional response replay failed';reordered+=n
        for s in r.get('decision_samples',[]):
            assert check_sample(s,b,oracle,nodes,r['adaptive'],d['training']['weights'] if lane=='interval-RL' else None) if r.get('condition') else old_sample(s,b,oracle)
            samples+=1
        states+=1;moves+=len(r['execution']);complete+=r['status']=='finite_exact_region'
        if lane and r['status']=='finite_exact_region':patches.append({'lane':lane+'/'+b.identity,'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['training']['episodes']+d['evaluation']:replay(r,bs[r['problem']],r.get('lane'))
    for m in d['movable_evaluation']:
        family=families[m['family']];assert [a['boundary'] for a in m['attempts']]==[b.identity for b in family[:len(m['attempts'])]]
        for a in m['attempts']:replay(a['result'],bs[a['boundary']],m['lane'])
        winner=next((a['boundary'] for a in m['attempts'] if a['result']['status']=='finite_exact_region'),None)
        assert m['selected']==winner and (m['status']=='finite_exact_movable_region')==(winner is not None)
    for c in d['controls']:
        b=Boundary.unpack(c['boundary']);a,z=c['results'];assert all(a[f]==z[f] for f in c['fields'])
        assert [(s['kind'],s['point'],s['placement']) for s in a['execution']]==[(s['kind'],s['point'],s['placement']) for s in z['execution']]
        replay(a,b);replay(z,b)
    choices=reconstruct_updates(d['training']);assert d['training']['updates']==48
    for r in d['training']['episodes']:assert r['reward']==r['coverage_fraction']+(1 if r['status']=='finite_exact_region' else -1)-.001*r['attempted_base_placements']-.01*r['reward_elapsed_seconds']
    assert len(d['evaluation'])==56 and len({(r['problem'],r['replica'],r['lane']) for r in d['evaluation']})==56 and len(d['movable_evaluation'])==14
    rejected=0;r=next(r for r in d['evaluation'] if any(s['response']!='singleton' for s in r['execution']));b=bs[r['problem']]
    for mutation in ('point','generation','offset','pose','condition','size'):
        bad=copy.deepcopy(r);i=next(i for i,s in enumerate(bad['execution']) if s['response']!='singleton')
        if mutation=='point':bad['execution'][0]['point']=[90,-45,-45]
        elif mutation=='generation':bad['state']['tile_generations'][0]+=1
        elif mutation=='offset':bad['execution'][i]['proposal_offset']=100
        elif mutation=='pose':bad['execution'][i]['proposal_pose'][1]=[90,-45,-45]
        elif mutation=='condition':bad['execution'][i]['condition']='invalid'
        else:bad['execution'][i]['proposal_size']+=1
        try:okay=oracle.replay(bad,b) and replay_responses(bad,b,oracle,nodes,set(parent['library']['selected']))[0]
        except (ValueError,KeyError,IndexError):okay=False
        assert not okay;rejected+=1
    r=next(r for r in d['evaluation'] if r['decision_samples']);b=bs[r['problem']];s=r['decision_samples'][0]
    for mutation in ('omit','duplicate','point'):
        bad=copy.deepcopy(s)
        if mutation=='omit':bad['ordered'].pop()
        elif mutation=='duplicate':bad['ordered'].append(bad['ordered'][0])
        else:bad['point']=[90,-45,-45]
        assert not check_sample(bad,b,oracle,nodes,r['adaptive']);rejected+=1
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    d['independent_audit']={'states':states,'complete_states':complete,'scheduled_moves':moves,'saved_reordered_constituents':reordered,
        'sampled_complete_domains':samples,'compiled_cluster_poses':poses,'compiled_member_incidences':incidences,
        'conditional_interfaces':len(nodes),'composition_laws':compositions,'source_child_maps':maps,'policy_updates':48,'policy_choices':choices,
        'equal_base_path_controls':len(d['controls']),'tampered_records_rejected':rejected,'geometry':geometry,
        'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_boundary_macros.py','audit_boundary_responses.py','audit_frontier_responses.py','audit_geometry.py','region_tiles.py','turtle.py')},
        'scope':'exact local capacity laws and complete sampled-atlas compilation; every saved path, sampled complete parents and policy algebra; no replay of all abandoned branches, learned marking or plane proof'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k not in ('geometry','helper_sources')},indent=2),flush=True)

if __name__=='__main__':main()
