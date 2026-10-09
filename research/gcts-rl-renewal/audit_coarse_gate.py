"""Independent saved-data replay and inductive coarse-library proof lifting."""
import copy,dataclasses,hashlib,json,resource,time
from collections import Counter
from pathlib import Path
from turtle import Model,SYMMETRIES,transform,compose,add,sub,verify_patch
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState,verify_state
from cluster_learning import check_corona_positive,exact_keys
from coarse_continuation import parent_library,root_state,LiteralOracle,exact_key,check_failure,HERE,DOCS
from capacity_pruning import CapacityOracle,inventory_values,reachable,check_failure as capacity_failure

def normal(v):return json.loads(json.dumps(v))

def audit(d):
    start=time.monotonic();stage_path=DOCS/'multiscale-level1-001.json';stage=json.loads(stage_path.read_text())
    children,parents,provenance=parent_library(stage);definitions=children+parents;original=tuple(t.identity for t in parents)
    if stage['prototypes']!=normal([dataclasses.asdict(t) for t in children]):raise ValueError('changed source child prototypes')
    model=ClusterModel(definitions);reference=d['reference'];capacity=d['capacity_control'];fixed=d['elimination']
    for run in (reference,capacity):
        if run['reuse']['sha256']!=hashlib.sha256(stage_path.read_bytes()).hexdigest():raise ValueError('changed shape source')
        if run['definitions']!=normal([dataclasses.asdict(t) for t in definitions]) or run['parent_provenance']!=normal(provenance):raise ValueError('forged parent library')
        if run['active_types']!=list(original) or not run['complete_catalog']:raise ValueError('missing root study')
    for n,h in d['sources'].items():
        if hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=h:raise ValueError('changed source '+n)
    if reference['source_sha256']!=d['sources']['coarse_continuation.py']:raise ValueError('changed reference source')
    if any(d['sources'][n]!=h for n,h in capacity['source_sha256'].items()):raise ValueError('changed capacity run source')
    if any(d['sources'][n]!=h for n,h in fixed['sources'].items()):raise ValueError('changed elimination source')
    positive_shapes=0;aliases=0;assigned={};child_model=ClusterModel(children)
    for t,p in zip(parents,provenance):
        for i in p['equivalent_positive_contacts']:
            if i in assigned:raise ValueError('shape contact assigned twice')
            assigned[i]=t
    for i,s in enumerate(stage['samples']):
        if s['status']=='positive':
            if not check_corona_positive(Model(),s['seed_expansion'],s['witness']):raise ValueError('invalid reused positive shape')
            positive_shapes+=1
            a,b,o,tr=s['contact'];raw=child_model.placement((a,0,(0,0,0))).expansion+child_model.placement((b,o,tuple(tr))).expansion
            if tuple(sorted(raw))!=exact_keys(s['seed_expansion']):raise ValueError('shape declaration differs from labeled seed')
            if i not in assigned:raise ValueError('omitted positive parent shape')
            target=assigned[i].expansion;congruent=False
            # Literal group/translation orbit, independently of canonical().
            for g in SYMMETRIES:
                transformed=moved(raw,g)
                for origin in {tr for o,tr in transformed}:
                    if tuple(sorted((o,sub(tr,origin)) for o,tr in transformed))==target:congruent=True;break
                if congruent:break
            if not congruent:raise ValueError('noncongruent shapes merged')
            aliases+=1
    if set(assigned)!={i for i,s in enumerate(stage['samples']) if s['status']=='positive'}:raise ValueError('invalid shape alias partition')
    states=negative_nodes=capacity_nodes=positive=tampers=0;checked_negatives=[]
    def run_check(run,active,analytic=False):
        nonlocal states,negative_nodes,capacity_nodes,positive,tampers
        if run['root'] not in active:raise ValueError('root outside active inventory')
        s=root_state(definitions,run['root']);required=set(s.totals)
        if normal(sorted(required))!=run['required']:raise ValueError('altered completion target')
        keys=[exact_key(k,active) for k in run['placements']]
        if not keys or keys[0]!=(run['root'],0,(0,0,0)):raise ValueError('changed fixed root')
        oracle=CapacityOracle(definitions,active) if analytic else LiteralOracle(definitions,active)
        for key in keys[1:]:
            c=model.placement(key)
            if not s.legal(c) or (analytic and any(12-s.totals.get(p,0)-v not in oracle.deficits for p,v in c.occupancy)):raise ValueError('illegal saved prefix')
            s.place(c)
        if run['tile_generations']!=s.tile_generations or run['base_expansion']!=normal(sorted(s.owned_base)):raise ValueError('omitted expansion or changed generations')
        if run['covered']!=sum(s.totals.get(p,0)==12 for p in required) or not verify_state(model,s):raise ValueError('changed point state')
        states+=1
        if run['status']=='positive':
            if not verify_state(model,s,required) or any(not v for v in oracle.domains(s).values()):raise ValueError('invalid finite coarse witness')
            positive+=1
        elif run['status']=='negative':
            checker=capacity_failure if analytic else check_failure
            ok,n=checker(definitions,active,run['root'],run['certificate'])
            if not ok or n!=run['independent_failure_audit']['nodes']:raise ValueError('invalid exhausted tree')
            if analytic:capacity_nodes+=n
            else:negative_nodes+=n
            checked_negatives.append((run['root'],tuple(active),analytic,n))
            bad=copy.deepcopy(run['certificate'])
            if 'children' in bad:bad['children'].pop()
            else:bad['dead']=[1000,-400,-600]
            if checker(definitions,active,run['root'],bad)[0]:raise ValueError('changed failure accepted')
            tampers+=1
        elif run['status']=='unresolved':
            if run['certificate'] is not None:raise ValueError('cutoff labeled a failure')
        else:raise ValueError('invalid result status')
        if analytic:
            if run['contribution_values']!=list(inventory_values(definitions,active)) or run['reachable_deficits']!=sorted(reachable(inventory_values(definitions,active))):raise ValueError('altered analytic premise')
    for analytic,run in ((False,reference),(True,capacity)):
        if [r['root'] for r in run['results']]!=list(original) or dict(Counter(r['status'] for r in run['results']))!=run['counts']:raise ValueError('incomplete ordered roots')
        for r in run['results']:run_check(r,original,analytic)
    if fixed['definitions']!=reference['definitions'] or fixed['parent_provenance']!=reference['parent_provenance'] or fixed['original_types']!=list(original):raise ValueError('changed fixed-point library')
    first=fixed['rounds'][0]
    if hashlib.sha256((json.dumps(reference,separators=(',',':'))+'\n').encode()).hexdigest()!=fixed['initial_reference_sha256']:
        raise ValueError('changed imported reference artifact')
    if first['results']!=reference['results'] or first['active']!=list(original) or first['round']!=0:raise ValueError('changed initial proof round')
    eliminated={r['root']:0 for r in reference['results'] if r['status']=='negative'}
    if first['eliminated']!=sorted(eliminated):raise ValueError('unproved initial exclusion')
    for level,round in enumerate(fixed['rounds'][1:],1):
        active=tuple(n for n in original if n not in eliminated)
        if round['round']!=level or round['active']!=list(active) or [r['root'] for r in round['results']]!=list(active):raise ValueError('skipped live type or wrong active premise')
        for r in round['results']:run_check(r,active)
        new=[r['root'] for r in round['results'] if r['status']=='negative']
        if round['eliminated']!=new:raise ValueError('unproved round exclusion')
        eliminated.update({n:level for n in new})
    remaining=[n for n in original if n not in eliminated]
    expected_stable=not remaining or not fixed['rounds'][-1]['eliminated']
    if fixed['eliminated_at']!=eliminated or fixed['remaining_types']!=remaining or fixed['stable']!=expected_stable:raise ValueError('altered inductive conclusion')
    # Root normalization is valid for the whole unbounded inventory. Check
    # every base expansion and the scalar capacity action in every root pose.
    covariance=0
    for t in parents:
        for i,g in enumerate(SYMMETRIES):
            c=model.placement((t.identity,i,(0,0,0)))
            if c.expansion!=moved(t.expansion,g) or dict(c.occupancy)!={transform(p,g):v for p,v in t.occupancy}:raise ValueError('invalid root symmetry')
            if not verify_patch(Model(),c.expansion):raise ValueError('invalid transformed base expansion')
            covariance+=1
    units=inventory_values(definitions,original);deficits=reachable(units)
    # Independent numerical closure: enumerate unrestricted sequences of
    # positive values up to the capacity, rather than trusting the DP helper.
    seen={0};front={0}
    while front:
        fresh={s+v for s in front for v in units if s+v<=12}-seen;seen.update(fresh);front=fresh
    if seen!=set(deficits):raise ValueError('wrong residual monoid')
    return {'positive_shape_witnesses':positive_shapes,'literal_positive_shape_orbits_checked':aliases,'states_replayed':states,'finite_coarse_witnesses':positive,
        'reference_and_elimination_failure_nodes':negative_nodes,'analytic_failure_nodes':capacity_nodes,
        'tampered_trees_rejected':tampers,'transformed_parent_expansions':covariance,'eliminated_types':len(eliminated),
        'remaining_types':remaining,'all_types_excluded':not remaining,'stable':expected_stable,
        'contribution_values':units,'reachable_deficits':sorted(deficits),'seconds':time.monotonic()-start,
        'peak_audit_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'proof_lifting':'induction: a complete original-library point tiling contains no type already ruled out by a normalized complete root failure; each new remaining-inventory tree extends that exclusion',
        'scope':'analytic lifting of finite exact trees for one declared coarse library; no base turtle non-tiling, geometric faithfulness or positive infinite continuation theorem'}

def main():
    paths=['coarse-continuation-checkpoint.json','capacity-continuation-checkpoint.json','coarse-fixed-point-checkpoint.json']
    reference,capacity,fixed=[json.loads((HERE/'results'/n).read_text()) for n in paths]
    names=('coarse_continuation.py','capacity_pruning.py','coarse_fixed_point.py','turtle.py','cluster_tiles.py','cluster_learning.py','spatial.py','run_multiscale_regions.py','run_regions.py')
    d={'reference':reference,'capacity_control':capacity,'elimination':fixed,
        'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},
        'scope':'joint coarse library selection; all earlier models are explicit reused inputs; substitution remains optional'}
    result=audit(d);result['audit_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    d['independent_audit']=result
    (DOCS/'coarse-gate-001.json').write_text(json.dumps(d,separators=(',',':'))+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
