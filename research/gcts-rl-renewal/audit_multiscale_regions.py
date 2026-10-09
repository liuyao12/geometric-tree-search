"""Saved multi-level palettes, base failure trees and larger boundary replay."""
import copy,dataclasses,hashlib,json,time
from collections import Counter
from pathlib import Path
from turtle import Model,SYMMETRIES,add,sub,transform,compose,verify_patch,VERTICES
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState
from cluster_learning import check_corona_positive,check_corona_failure,exact_keys
from multiscale_learning import Palette,seeds,decorate,unpack_markings,disagreements
from run_multiscale_regions import HERE,DOCS,initial_types,make_parent,problems
from region_tiles import verify_region,unpack_state,check_failure
from audit_geometry import audit as geometry_audit

def normal(value):return json.loads(json.dumps(value))
def contact(value):
    a,b,o,tr=value;tr=tuple(tr)
    if not isinstance(a,str) or not isinstance(b,str) or type(o) is not int or not 0<=o<12 or len(tr)!=3 or any(type(x) is not int for x in tr) or sum(tr)!=0:
        raise ValueError('invalid contact')
    return a,b,o,tr

def literal_catalog(types):
    """No ClusterModel legal/alignment cache and no stored contact catalog."""
    base=Model();result=set()
    for a in types:
        for b in types:
            for o,g in enumerate(SYMMETRIES):
                for tr in {sub(p,transform(q,g)) for p,v in a.occupancy for q,w in b.occupancy}:
                    right=moved(b.expansion,g,tr)
                    if not set(a.expansion)&set(right) and verify_patch(base,a.expansion+right):result.add((a.identity,b.identity,o,tr))
    return tuple(sorted(result))

def audit_stage(stage,types):
    start=time.monotonic();expected=literal_catalog(types);samples=stage['samples']
    if normal([dataclasses.asdict(t) for t in types])!=stage['prototypes']:raise ValueError('changed externally reconstructed prototype')
    actual=tuple(contact(s['contact']) for s in samples)
    if actual!=expected or len(actual)!=stage['catalog_count']:raise ValueError('incomplete or altered contact catalog')
    palette=Palette(types);negative_nodes=positive=0;tampers=0
    for i,(k,s) in enumerate(zip(expected,samples)):
        fixed=seeds(types,k)
        if exact_keys(s['seed_expansion'])!=fixed:raise ValueError('changed fixed constituents')
        if s['status']=='negative':
            ok,n=check_corona_failure(Model(),fixed,s['certificate'])
            if not ok:raise ValueError('invalid base failure')
            negative_nodes+=n
        elif s['status']=='positive':
            if not check_corona_positive(Model(),fixed,s['witness']):raise ValueError('invalid base completion')
            positive+=1
        elif s['status']!='unresolved':raise ValueError('bad label status')
        palette.add(dict(s,contact=k))
        if (i+1)%200==0:print(stage['id'],'saved audit',i+1,'/',len(samples),'nodes',negative_nodes,flush=True)
    markings,statistics=palette.finish()
    if normal(statistics)!=stage['statistics'] or markings!=unpack_markings(stage):raise ValueError('altered palette values or classification')
    if normal(palette.history)!=stage['history']:raise ValueError('altered learning history')
    exclusions=disagreements(types,markings);by_key=dict(zip(expected,samples))
    if normal(sorted(exclusions))!=stage['disagreements'] or not exclusions<=by_key.keys() or any(by_key[k]['status']!='negative' for k in exclusions):raise ValueError('uncertified exclusion')
    # Actual scalar covariance on every root pose, including cross-type pairs.
    # Inspect own values only; inherited channels are verified separately by
    # the parent's descending child-map construction and prior-level lemma.
    symmetry=0
    for root,o,k in ((a,i,k) for a in types for i in range(12) for k in expected if k[0]==a.identity):
        g=SYMMETRIES[o];_,b,other,tr=k;second_g=compose(g,SYMMETRIES[other]);offset=transform(tr,g)
        left={add(transform(p,g),(0,0,0)):v for p,v in markings[root.identity].items()}
        right={add(transform(p,second_g),offset):v for p,v in markings[b].items()}
        rejects=any(left[p]!=v for p,v in right.items() if p in left)
        if rejects!=(k in exclusions):raise ValueError('incorrect scalar symmetry transfer')
        symmetry+=1
    counts=statistics['counts'];gate=(not counts.get('unresolved',0) and statistics['positive_accepted']==counts.get('positive',0)
           and (not counts.get('negative',0) or statistics['negative_rejected']>counts['negative']/2))
    if stage['activation_gate_passed']!=gate:raise ValueError('incorrect activation gate')
    neg=next((s for s in samples if s['status']=='negative' and 'children' in s['certificate']),None)
    if neg:
        bad=copy.deepcopy(neg['certificate']);bad['children'].pop()
        if check_corona_failure(Model(),neg['seed_expansion'],bad)[0]:raise ValueError('omitted branch accepted')
        tampers+=1
    pos=next((s for s in samples if s['status']=='positive'),None)
    if pos:
        bad=copy.deepcopy(pos['witness']);bad[0][0]=True
        if check_corona_positive(Model(),pos['seed_expansion'],bad):raise ValueError('boolean placement accepted')
        tampers+=1
    return {'catalog':len(samples),'positive':positive,'negative_nodes':negative_nodes,'exclusions':len(exclusions),
            'scalar_symmetry_checks':symmetry,'tampered_certificates_rejected':tampers,'seconds':time.monotonic()-start}

def audit(path=DOCS/'multiscale-regions-001.json'):
    start=time.monotonic();d=json.loads(Path(path).read_text())
    for name,sha in d['sources'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=sha:raise ValueError('changed source '+name)
    if hashlib.sha256((DOCS/d['reuse']['shape_artifact']).read_bytes()).hexdigest()!=d['reuse']['sha256']:raise ValueError('changed shape input')
    stages=[]
    for declaration in d['stages']:
        file=DOCS/declaration['artifact']
        if hashlib.sha256(file.read_bytes()).hexdigest()!=declaration['sha256']:raise ValueError('changed stage artifact')
        stages.append(json.loads(file.read_text()))
    single,a,b=initial_types();children=(a,b);first,second=stages
    first_audit=audit_stage(first,children);m1=unpack_markings(first)
    marked_children=tuple(decorate(t,m1[t.identity]) for t in children) if first['activation_gate_passed'] else children
    parent,child_map=make_parent(marked_children,first);bare_parent,_=make_parent(children,first)
    if normal(child_map)!=d['parent_children']:raise ValueError('changed parent assembly')
    second_audit=audit_stage(second,(parent,));m2=unpack_markings(second)
    marked_parent=decorate(parent,m2[parent.identity]) if second['activation_gate_passed'] else parent
    raw=(single,*children,bare_parent);inherited=(single,*marked_children,parent);marked=(single,*marked_children,marked_parent)
    inventories={'singletons':(single,),'unmarked hierarchy':raw,'inherited GCTS':inherited,'GCTS hierarchy':marked,'RL hierarchy':raw,'GCTS+RL hierarchy':marked}
    if normal({n:[dataclasses.asdict(t) for t in ts] for n,ts in inventories.items()})!=d['inventories']:raise ValueError('changed inventory')
    if normal([b.packed() for b in problems()])!=d['problems'] or normal([b.packed() for b in problems(True)])!=d['training']['boundaries']:raise ValueError('changed boundary problem')
    boundaries={b.identity:b for b in problems()+problems(True)};models={n:ClusterModel(ts) for n,ts in inventories.items()}
    models['cold unmarked hierarchy']=models['unmarked hierarchy'];states=complete=base=negative_nodes=tampers=0;patches=[]
    for r in d['training']['episodes']+d['evaluation']+d['representation_controls']:
        lane=r.get('lane','unmarked hierarchy');model=models[lane];boundary=boundaries[r['problem']]
        s=unpack_state(model,boundary,r['state']);exact=r['status']=='finite_exact_region'
        if not verify_region(model,boundary,s,exact):raise ValueError('invalid expanded boundary certificate')
        if r['accepted_base_tiles']!=len(s.owned_base-set(boundary.owned)) or r['accepted_cluster_tiles']!=len(s.order):raise ValueError('altered placement counts')
        if r['coverage_fraction']!=sum(s.totals.get(p,0)==12 for p in s.required)/len(s.required):raise ValueError('altered coverage')
        if r['status']=='exhausted_finite_region':
            ok,n=check_failure(model,boundary,r['certificate'])
            if not ok:raise ValueError('invalid finite-region failure tree')
            negative_nodes+=n
        elif r['certificate'] is not None:raise ValueError('cutoff has a spurious failure proof')
        states+=1;complete+=exact;base+=r['accepted_base_tiles']
        if exact:
            patches.append({'lane':lane+'/'+boundary.identity,'seed':r['seed'],'placements':r['state']['base_expansion']})
            bad=copy.deepcopy(r['state']);bad['base_expansion']=[]
            try:unpack_state(model,boundary,bad)
            except ValueError:tampers+=1
            else:raise ValueError('omitted base expansion accepted')
    paired=0
    for cold in d['representation_controls']:
        resident=next(r for r in d['evaluation'] if r['lane']=='unmarked hierarchy' and r['problem']==cold['problem'] and r['seed']==cold['seed'])
        if cold['status']==resident['status']=='finite_exact_region':
            for field in ('state','nodes','branches','forced','backtracks','attempted_base_placements'):
                if cold[field]!=resident[field]:raise ValueError('resident optimization changed reference trace')
            paired+=1
    # Count genuinely new parent-channel disagreements beyond inherited colors.
    inherited_model=ClusterModel(inherited);inherited_exclusions=set()
    for sample in second['samples']:
        k=contact(sample['contact']);s=ClusterState();s.place(inherited_model.placement((parent.identity,0,(0,0,0))),seed=True)
        if not s.legal(inherited_model.placement((k[1],k[2],k[3]))):inherited_exclusions.add(k)
    own_exclusions={contact(k) for k in second['disagreements']}
    parent_obstruction=None
    if len(second['samples'])==second_audit['catalog'] and all(s['status']=='negative' for s in second['samples']):
        partial=next(((p,v) for p,v in parent.occupancy if 0<v<12),None)
        if partial is None:raise ValueError('a standalone saturated parent cannot have this obstruction')
        # The base capacity model is covariant under the entire declared group.
        # A complete all-parent tiling needs another parent at this partial
        # point. Normalize the first pose: the pair is one of the exhausted
        # catalog contexts, contradicting its complete unmarked base tree.
        group_checks=0
        for g in SYMMETRIES:
            for h in SYMMETRIES:
                gh=compose(g,h)
                if gh not in SYMMETRIES:raise ValueError('transform group is not closed')
                for p,v in Model().placement((0,(0,0,0))).occupancy:
                    if transform(transform(p,h),g)!=transform(p,gh):raise ValueError('noncovariant base support')
                    group_checks+=1
        parent_obstruction={'type':parent.identity,'partial_point':partial[0],'contribution':partial[1],
             'exhausted_contact_contexts':second_audit['catalog'],'checked_base_failure_nodes':second_audit['negative_nodes'],
             'base_group_support_checks':group_checks,
             'statement':'no complete point tiling by disjoint occurrences of this parent alone exists',
             'argument':'a partial root support point needs another parent; their normalized capacity-legal contact belongs to the complete catalog; every such pair has a checked unmarked base failure tree',
             'scope':'analytic lifting of machine-checked finite base failure trees; parent-only inventory on A2; mixed hierarchy and base turtle plane existence remain open'}
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    return {'stages':[first_audit,second_audit],'states_replayed':states,'complete_states':complete,'base_placements_replayed':base,
            'region_failure_nodes':negative_nodes,'region_tampers_rejected':tampers,'identical_completed_resident_traces':paired,
            'parent_inherited_exclusions':len(inherited_exclusions),'parent_new_own_exclusions':len(own_exclusions-inherited_exclusions),
            'parent_combined_exclusions':len(own_exclusions|inherited_exclusions),'geometry':geometry,'seconds':time.monotonic()-start,
            'parent_only_obstruction':parent_obstruction,
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'all possible scalar exclusions at both levels have independent unmarked base failures; saved finite point regions and expansions; no plane or geometric faithfulness theorem'}

if __name__=='__main__':
    output=audit();print(json.dumps({k:v for k,v in output.items() if k!='geometry'},indent=2),flush=True)
    (HERE/'results/multiscale-serialization-audit.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
