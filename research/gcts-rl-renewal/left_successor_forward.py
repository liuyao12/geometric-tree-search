"""Separate ordinary forward-chaining extraction control, not GCTS.

Every native-admitted retained edge participates in synchronous closure.
For each newly reachable formula, the first ready edge in the unchanged
catalog order is retained as a witness. Only after the complete fixed point
is reached does generic DAG reconstruction inspect the query. No chosen
induction variable, rewrite path, target derivation or proof is supplied.
"""
import copy,gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from certificate_boundary_search import canonical,digest
from induction_receptors_closure import expand
from induction_receptors_compaction import formula_dag
from audit_semantic_proofs import whole_replay
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'forward-control';TMP=Path('/private/tmp/gcts-left-successor-forward-20261011')
def need(t,m):
    if not t:raise ValueError(m)
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def closure(catalog):
    words={canonical(f):i for i,f in enumerate(catalog['basis'])};edges=[dict(rule=i,inputs=[words[canonical(p)] for p in r['premises']],output=words[canonical(r['conclusion'])]) for i,r in enumerate(catalog['rules'])];witness={};layers=[];scans=0;round_index=0
    while True:
        ready={}
        for e in edges:
            scans+=1
            if e['output'] not in witness and all(p in witness for p in e['inputs']):ready.setdefault(e['output'],e['rule'])
        if not ready:break
        layers.append(sorted(ready))
        for output,rule in ready.items():witness[output]=dict(rule=rule,rank=round_index)
        round_index+=1
    return dict(edges=edges,layers=layers,witnesses=[witness.get(i) for i in range(len(catalog['basis']))],edge_scans=scans,fixed_point_reachable=len(witness),rounds=len(layers))
def word(catalog,closed,target):
    ids={canonical(f):i for i,f in enumerate(catalog['basis'])};goal=ids[canonical(target)];rows=[];sources={};selected=[]
    if closed['witnesses'][goal] is None:return None,None
    def visit(formula):
        if formula in sources:return sources[formula]
        witness=closed['witnesses'][formula];need(witness is not None,'every witness source is reached');i=witness['rule'];r=catalog['rules'][i];inputs=[visit(ids[canonical(p)]) for p in r['premises']];command=copy.deepcopy(r['command'])
        if command['rule']=='block':command['inputs']=inputs
        elif command['rule']=='generalize':need(len(inputs)==1,'one generic generalization input');command['source']=inputs[0]
        else:need(not inputs,'zero-input primitive root')
        sources[formula]=len(rows);rows.append(command);selected.append(dict(row=len(rows)-1,formula=formula,rule=i,sources=inputs));return len(rows)-1
    visit(goal);return rows,selected
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());base=json.loads((PARENT/'plan.json').read_text());need(json.loads((PARENT/'rank-search/search-audit.json').read_text())['status']=='passed_all_recorded_search_and_native_outcomes','all four fresh rank traces audited before separate control')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen forward source '+p)
    for p,h in plan['input_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact stable control input '+p)
    TMP.mkdir(parents=True,exist_ok=True);start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));summary=dict(status='running',observations=[],native_queries=0,compile_and_oracle_setup_seconds=time.perf_counter()-start);checked={}
    try:
        for lane in plan['lanes']:
            start=time.perf_counter();catalog=load(PARENT/(lane+'-reachable-core.json.gz'));admission=json.loads((PARENT/(lane+'-admission.json')).read_text());need(admission['admission_audit_status']=='passed_complete_reachable_native_admission' and admission['pilot_audit_status']=='passed_preparation_native_replay_only' and admission['status']=='native_accepted' and all(d['status']=='accepted' for d in admission['definitions']),'whole native admission for every actual definition');need({d['name']:digest(d) for d in catalog['definitions']}==admission['complete_definition_sha256'] and catalog['structural_pruning']['witness_sha256']==admission['pruning_witness_sha256'],'complete exact grammar binding')
            closed=closure(catalog);proof,selected=word(catalog,closed,base['case']['target']);raw=dict(lane=lane,theory=base['case']['theory'],target=base['case']['target'],closure=closed,proof=proof,selected_witnesses=selected,whole_variants=[],extraction_seconds=time.perf_counter()-start);metric=dict(lane=lane,retained_interfaces=len(catalog['rules']),complete_closure_formulas=closed['fixed_point_reachable'],edge_scans=closed['edge_scans'],extraction_seconds=raw['extraction_seconds'],word_length=None if proof is None else len(proof),same_12_row_boundary_fits=proof is not None and len(proof)<=plan['comparison_rows'],whole_variants=[]);summary['observations'].append(metric);save(OUT/(lane+'.json.gz'),raw);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('FORWARD EXTRACTION CHECKPOINT',json.dumps(metric),flush=True)
            if proof is not None:
                names={r['name'] for r in proof if r['rule']=='block'};request=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[d for d in catalog['definitions'] if d['name'] in names],proof=proof,target=base['case']['target']);start=time.perf_counter();expanded=expand(request);primitive=copy.deepcopy(request);primitive.update(blocks=[],proof=formula_dag(expanded));need(whole_replay(request)['status']==whole_replay(primitive)['status']=='accepted','separate host whole closure/compaction check');raw.update(original_request=request,primitive_request=primitive,expanded_commands=len(expanded),compaction_preparation_seconds=time.perf_counter()-start);metric.update(expanded_commands=len(expanded),shared_primitive_commands=len(primitive['proof']),compaction_preparation_seconds=raw['compaction_preparation_seconds']);save(OUT/(lane+'.json.gz'),raw)
                for mode in plan['whole_variants']:
                    need(time.perf_counter()-began<=plan['ceilings']['between_query_seconds'],'unknown_between_query_time_budget');request=raw['original_request'] if mode=='selected-high-level' else raw['primitive_request'];h=digest(request);cached=h in checked
                    if cached:q=checked[h]
                    else:
                        need(len(oracle.records)<plan['ceilings']['native_queries'] and sum(q['result']['micro_steps'] for q in oracle.records)<plan['ceilings']['aggregate_micro_steps'],'unknown_aggregate_native_budget');q=oracle.request(request,plan['ceilings']['per_query_micro_steps'],'left_successor_forward_'+mode);fixed,free=boundary_words(q['request']);q.update(boundary_words=dict(fixed=fixed,free=free),limit=plan['ceilings']['per_query_micro_steps']);checked[h]=q;save(OUT/'native.json.gz',oracle.records)
                        for name in ('input.bin','output.bin'):(OUT/('query-%03d-'%q['id']+name+'.gz')).write_bytes(gzip.compress((TMP/'native'/name).read_bytes(),mtime=0))
                    value=dict(mode=mode,query=q['id'],native_status=q['result']['status'],request_sha256=h,proof_commands=len(request['proof']),cached_exact_request=cached,historical_native_seconds=q['seconds'],historical_micro_steps=q['result']['micro_steps']);raw['whole_variants'].append(value);metric['whole_variants'].append(value);save(OUT/(lane+'.json.gz'),raw);summary['native_queries']=len(oracle.records);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('FORWARD WHOLE CHECKPOINT',lane,json.dumps(value),flush=True)
        summary.update(status='complete_forward_observations_pending_independent_audit',scope='Ordinary deterministic full retained hyperedge forward chaining, not GCTS, proposals or RL. No supplied target-proof path. The completed closure and automatically reconstructed DAG/word are separate from blind GCTS phases. Unknown native outcomes remain unknown.')
    finally:
        summary.update(seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_queries=len(oracle.records));(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');save(OUT/'native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
