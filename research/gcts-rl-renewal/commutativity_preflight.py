"""Frozen bounded feasibility measurement, with no native query/target search."""
import collections,copy,gc,gzip,hashlib,json,resource,signal,time
from pathlib import Path
from certificate_boundary_search import canonical,digest
from commutativity_catalog import core,compact_core,motif_families,motif_count,prospective_points
from commutativity_points import ProspectiveModel,row_keys,aggregate
from left_successor_reachability import closure
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/commutativity-receptors-20261011';OLD=ROOT/'.gcts-active/induction-receptors-20261011';LEFT=ROOT/'.gcts-active/left-successor-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def deadline(s,f):raise TimeoutError('unknown_commutativity_preflight_time_budget')
def check(plan,began):
    if time.perf_counter()-began>plan['ceilings']['seconds']:raise TimeoutError('unknown_commutativity_preflight_time_budget')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_commutativity_preflight_memory_budget')
def native_request(theory,d):
    taut=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());signal.signal(signal.SIGALRM,deadline);signal.alarm(plan['ceilings']['seconds'])
    for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen feasibility binding '+p)
    need(json.loads((OLD/'compaction-audit.json').read_text())['status']=='passed' and json.loads((OLD/'recovery-audit.json').read_text())['status']=='passed','zero-left native/search audit');need(json.loads((LEFT/'workspace-native/audit.json').read_text())['status']=='passed_complete_larger_workspace_native_replay' and json.loads((LEFT/'forward-control/audit.json').read_text())['status']=='passed_complete_forward_control_and_native_replay','left-successor automatic discovery/native replay');need(json.loads((LEFT/'pilot-audit.json').read_text())['status']=='passed_preparation_native_replay_only' and json.loads((LEFT/'admission-audit.json').read_text())['status']=='passed_complete_reachable_native_admission','exact previous reusable interface requests independently audited')
    proofs=[load(OLD/'compaction-native.json.gz')[1],load(LEFT/'workspace-native/native.json.gz')[1]];inventory=[]
    for spec,q in zip(plan['lemma_sources'],proofs):
        need(q['result']['status']=='accepted' and q['request_sha256']==spec['request_sha256']==digest(q['request']) and q['request']['theory']==plan['case']['theory'] and not q['request']['blocks'],'exact previously automatic primitive certificate')
        inventory.append(dict(name=spec['name'],conclusion=q['request']['target'],proof=q['request']['proof'],theory=q['request']['theory'],request_sha256=q['request_sha256'],discovery=spec['discovery'],historical_native_seconds=q['seconds'],historical_micro_steps=q['result']['micro_steps'],promotion='Closed checked theorem certificate, never a theory axiom; this new block interface is not yet native admitted.'))
    (OUT/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n');summary=dict(status='preparing',native_queries=0,target_searches=0,RL_training_runs=0,lanes=[],inventory=[dict(name=q['name'],proof_commands=len(q['proof']),request_sha256=q['request_sha256'],discovery=q['discovery'],historical_native_seconds=q['historical_native_seconds']) for q in inventory]);union={};reuse={}
    oldqs=load(LEFT/'pilot-native.json.gz')+load(LEFT/'admission-native.json.gz')
    for q in oldqs:
        if q['result']['status']=='accepted':reuse[digest(q['request'])]=dict(query=q['id'],purpose=q['purpose'],historical_seconds=q['seconds'],historical_micro_steps=q['result']['micro_steps'])
    try:
        for lane in plan['lanes']:
            start=time.perf_counter();chosen=inventory[:lane['inventory_count']];c=core(plan['case'],chosen);save(OUT/(lane['id']+'-full-core.json.gz'),c);check(plan,began);cc=compact_core(c);save(OUT/(lane['id']+'-compact-core.json.gz'),cc)
            for j,d in enumerate(cc['definitions']):
                need(whole_replay(native_request(plan['case']['theory'],d))['status']=='accepted','whole local host logical audit')
                if j%32==0:check(plan,began)
            w=closure(cc['rules'],cc['basis']);save(OUT/(lane['id']+'-closure.json.gz'),w);ret=copy.deepcopy(cc);ret['rules']=[cc['rules'][i] for i in w['retained_rules']];used={r['command']['name'] for r in ret['rules'] if r['command']['rule']=='block'};ret['definitions']=[d for d in cc['definitions'] if d['name'] in used];ret['structural_pruning']=dict(full_rule_ids=w['retained_rules'],witness_sha256=hashlib.sha256((OUT/(lane['id']+'-closure.json.gz')).read_bytes()).hexdigest(),scope='Proved finite strict-prior structural overapproximation; all full unadmitted edges participate. No target backcone or selected proof.')
            save(OUT/(lane['id']+'-retained-core.json.gz'),ret)
            for d in ret['definitions']:
                need(d['name'] not in union or union[d['name']]==d,'exact shared definition bytes');union[d['name']]=d
            sizes=[len(canonical(d)) for d in cc['definitions']];stats=dict(lane=lane['id'],terms=len(c['terms']),term_size_histogram=dict(collections.Counter(__import__('induction_receptors_catalog').size(__import__('induction_receptors_catalog').freeze(t)) for t in c['terms'])),full_basis=len(c['basis']),full_interfaces=len(c['rules']),full_definitions=len(c['definitions']),full_commands=sum(len(d['proof']) for d in c['definitions']),compact_commands=sum(len(d['proof']) for d in cc['definitions']),compact_json_bytes=sum(sizes),max_compact_commands=max(map(lambda d:len(d['proof']),cc['definitions'])),max_compact_definition_bytes=max(sizes),reachable_formulas=sum(r is not None for r in w['formula_ranks']),closure_rounds=w['rounds'],retained_interfaces=len(ret['rules']),retained_definitions=len(ret['definitions']),target_structurally_reachable=w['formula_ranks'][next(i for i,f in enumerate(cc['basis']) if f==plan['case']['target'])] is not None,point_counts=[dict(full=prospective_points(cc,n),retained=prospective_points(ret,n),motifs=motif_count(ret,n)) for n in plan['prospective_lengths']],prospective_models=[],host_preparation_seconds=time.perf_counter()-start)
            for n in plan['materialized_lengths']:
                stage=time.perf_counter();spec=copy.deepcopy(plan['case']);spec['length']=n;model=ProspectiveModel(spec,ret);record=model.record();save(OUT/(lane['id']+'-points-%d.json.gz'%n),dict(case=spec,model=record));families=motif_families(ret);samples=[]
                for f in families:
                    if n<4:continue
                    keys=row_keys(model,1,f['root_rule'],[])+row_keys(model,2,f['rewrite_rule'],[0,1]);agg=aggregate(model,keys);need(agg is not None,'generic distant receiver/lemma pair internally agrees');samples.append(dict(family=f,lemma_row=1,rewrite_row=2,external_source=0,aggregate=agg))
                    bad=row_keys(model,1,f['root_rule'],[])+row_keys(model,2,f['rewrite_rule'],[1,1]);need(aggregate(model,bad) is None,'coincident distinct formula receptors correctly conflict')
                save(OUT/(lane['id']+'-motif-pilot-%d.json.gz'%n),samples);stats['prospective_models'].append(dict(length=n,complete_placements=len(model.cache),required_points=len(model.align_cache),occupancy_incidence=sum(len(t.occupancy) for t in model.cache.values()),mark_assignments=sum(len(t.marks) for t in model.cache.values()),dependency_edges=sum(len(k) for k in model.dependencies.values()),mark_or_occupancy_points=len(model.dependencies),model_seconds=time.perf_counter()-stage,motif_families_checked=len(samples),native_authority=False));del model,record,samples;gc.collect();check(plan,began)
            summary['lanes'].append(stats);summary.update(seconds=time.perf_counter()-began);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('COMMUTATIVITY FEASIBILITY CHECKPOINT',json.dumps(stats),flush=True);del c,cc,ret,w;gc.collect()
        requirements=[]
        for name,d in sorted(union.items()):
            req=native_request(plan['case']['theory'],d);h=digest(req);requirements.append(dict(name=name,definition=d,definition_sha256=digest(d),request_sha256=h,commands=len(d['proof']),request_json_bytes=len(canonical(req)),boundary_capacity='unestimated for this exact request; previous262144 capacity is not automatically sufficient',exact_prior_request=reuse.get(h),status='exact-audited-prior-request-reusable' if h in reuse else 'requires-new-native-admission'))
        save(OUT/'admission-requirements.json.gz',requirements);summary.update(status='complete_bounded_feasibility_pending_independent_audit',native_admission_union=len(requirements),exact_prior_requests_reusable=sum(q['exact_prior_request'] is not None for q in requirements),fresh_native_admissions_required=sum(q['exact_prior_request'] is None for q in requirements),native_capacity_estimates='pending separately frozen small representative pilot; no large batch authorized',scope='Complete finite contextual adaptation and prospective exact point geometry, not a native-admitted model, target proof, GCTS discovery or RL training. Structural target reachability is only an overapproximation. Inventory counts differ semantically; future equal-inventory controls must use identical two-lemma rules/points and differ only by ordering/proposals.')
    finally:
        signal.alarm(0);summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
