"""Explicitly reused hierarchy -> a new case proof -> literal Wang control."""
import dataclasses,gc,hashlib,json,resource,time
from datetime import datetime
from zoneinfo import ZoneInfo
from hierarchy_bridge import HERE,DOCS,PARENT,definitions,next_family,point_lemma,search,normal,proof_catalog
from kernel_machine import KernelMachine,latex
from audit_kernel_machine import audit_catalog
from coarse_continuation import check_failure
from turtle import Policy
import kernel_search,lazy_wang,proof_search

SOURCES=('hierarchy_bridge.py','run_hierarchy_bridge.py','coarse_continuation.py','cluster_tiles.py',
         'cluster_learning.py','spatial.py','turtle.py','kernel_machine.py','kernel_search.py',
         'audit_kernel_machine.py','logic.py','lazy_wang.py','wang.py','rewrite_machine.py','proof_search.py')

def main():
    start=time.monotonic();source=DOCS/'failure-interfaces-001.json';previous=json.loads(source.read_text())
    stage_path=DOCS/previous['stages'][1]['artifact'];stage=json.loads(stage_path.read_text())
    assert hashlib.sha256(stage_path.read_bytes()).hexdigest()==previous['stages'][1]['sha256']
    free=definitions(previous,'aggregate unmarked');marked=definitions(previous,'aggregate GCTS')
    free_ten,provenance=next_family(free,stage);marked_ten,marked_provenance=next_family(marked,stage)
    assert normal(provenance)==normal(marked_provenance)
    lemma=point_lemma(free,marked,stage);print('case proof',len(lemma['cases']),lemma['base_failure_nodes'],'nodes',flush=True)
    d={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
       'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},
       'reuse':{'artifact':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
               'stage_artifact':stage_path.name,'stage_sha256':hashlib.sha256(stage_path.read_bytes()).hexdigest(),
               'use':'explicit reuse of searched shapes and verified point palettes; seven prior positive contacts declare the next layer; no saved policy or completion supplied to any search',
               'historical_source_pipeline_seconds':previous['total_seconds'],
               'historical_saved_audit_seconds':previous['independent_audit']['seconds']},
       'inventories':{'free':[dataclasses.asdict(t) for t in free+free_ten],
                      'marked':[dataclasses.asdict(t) for t in marked+marked_ten]},
       'ten_types':[t.identity for t in free_ten],'promotion':provenance,'point_lemma':lemma,
       'configuration':{'coarse_nodes':4000,'coarse_seconds':15,'singleton_refinement_retained_in_controls':True,
                        'no_finite_support_envelope':True,'markings_frozen':True},'coarse_runs':[]}
    def save(): (DOCS/'hierarchy-bridge-001.json').write_text(json.dumps(d,separators=(',',':'))+'\n')
    for root in (PARENT,)+tuple(t.identity for t in free_ten):
        alone=(PARENT,) if root==PARENT else tuple(t.identity for t in free_ten)
        lanes=(('free coarse',free+free_ten,alone),('marked coarse',marked+marked_ten,alone),
               ('marked + singleton refinement',marked+marked_ten,('base',)+alone))
        for lane,defs,active in lanes:
            r=search(defs,active,root);r['lane']=lane
            if r['status']=='negative':
                t=time.monotonic();ok,n=check_failure(defs,active,root,r['certificate']);assert ok
                r['first_failure_replay']={'nodes':n,'seconds':time.monotonic()-t}
            d['coarse_runs'].append(r);save();print(root,lane,r['status'],r['nodes'],round(r['seconds'],3),flush=True);gc.collect()
    c,targets=proof_catalog();policy=Policy();episodes=[];t=time.monotonic()
    for i in range(48):
        name=('five','ten')[i%2];q=kernel_search.propose(c,targets[name],policy,105000+i,12,learn=True);episodes.append({'target':name,'seed':105000+i,**q})
    d['logical_training']={'initial_weights':{},'episodes':episodes,'weights':dict(policy.weights),'seconds':time.monotonic()-t,
        'scope':'zero-start practice on these same two fixed geometry-lemma assertions; distinct evaluation seeds, not held-out mathematical generalization'}
    d['logical_declaration']=c.declaration();d['catalog_audit']=audit_catalog(c);d['logical_runs']=[]
    d['axiom_binding']={'checked_refinement':'all promoted types expand into two disjoint occurrences of the declared five-turtle type',
        'checked_complete_cover':'complete-domain enumeration at the normalized root partial point',
        'checked_all_base_failures':'all enumerated root cases have independently replayed unmarked base-corona failures',
        'semantics':'Plane5/Plane10 mean existence of a complete point tiling in those explicit coarse inventories. CoveredRoot5 is the normalized complete-extension case required by any Plane5 tiling. Unused predicates are irrelevant logical control facts.'}
    for j,(name,target) in enumerate(targets.items()):
        t=time.monotonic();m=KernelMachine(c,target);compile_seconds=time.monotonic()-t
        for lane,extended,rl in (('Wang',False,False),('analytic neighbor values',True,False),
                                ('RL + Wang',False,True),('RL + analytic neighbor values',True,True)):
            t=time.monotonic();proposal=kernel_search.propose(c,target,policy,106000+j,12) if rl else None
            preferred=kernel_search.preference(m,12,1536,proposal) if proposal else None
            r=lazy_wang.search(m.compiler,m.pattern(12),1536,m.accepting_row(len(m.pattern(12))),
                               node_limit=100000,seconds=3,extended=extended,preferred=preferred)
            r.update(target=name,statement=latex(target),lane=lane,proposal=proposal,preferred=preferred is not None,
                     total_request_seconds=time.monotonic()-t,compile_seconds=compile_seconds,
                     machine={'states':len(m.compiler.states),'transitions':len(m.compiler.transitions)},
                     length=12,height=1536)
            if r.get('verified'):
                cert=proof_search.pack(r);rows,_=proof_search.unpack(cert);offset=len(c.formulas)+4
                commands=m.parse(rows[0][offset:offset+12]);proof=c.proof(commands,target)
                r.update(certificate=cert,commands=commands,kernel_proof=proof,
                         display_proof=[{'rule':l['rule'],'formula':latex(l['formula'])} for l in proof])
                for key in ('rows','placements','initial','tile_generations'):r.pop(key,None)
            d['logical_runs'].append(r);save();print(name,lane,r['status'],r['nodes'],round(r['total_request_seconds'],3),flush=True);gc.collect()
    d['total_seconds']=time.monotonic()-start;d['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    d['scope']='one certified parent-only obstruction, refinement lifting to the full promoted library, and logical/Wang controls over checked external geometry lemmas; base plane existence and a fixed general AST checker remain open'
    save();print('complete pipeline',d['total_seconds'],flush=True)

if __name__=='__main__':main()
