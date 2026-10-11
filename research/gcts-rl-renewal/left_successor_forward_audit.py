"""Independent full closure, deterministic DAG and native control replay.

No extraction/search/model producer import. Priority-counter closure supplies
minimal ranks; first eligible edge identities are derived from those ranks.
An explicit stack reconstructs the proof word, and all native computations
are rerun from the actual parser with exact input/output/microstep matches.
"""
import copy,gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from left_successor_reachability_audit import worklist,packed
from induction_receptors_compaction_audit import expanded,shared
from left_successor_pilot_audit import overflowing
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'forward-control';TMP=Path('/private/tmp/gcts-left-successor-forward-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def dag_word(catalog,witnesses,target):
    ids={packed(f):i for i,f in enumerate(catalog['basis'])};goal=ids[packed(target)];rows=[];source={};chosen=[];stack=[(goal,False)]
    if witnesses[goal] is None:return None,None
    while stack:
        out,post=stack.pop()
        if out in source:continue
        i=witnesses[out]['rule'];r=catalog['rules'][i];premises=[ids[packed(p)] for p in r['premises']]
        if not post:
            stack.append((out,True));stack.extend((p,False) for p in reversed(premises));continue
        need(all(p in source for p in premises),'strict prior independently reconstructed DAG');inputs=[source[p] for p in premises];command=copy.deepcopy(r['command'])
        if command['rule']=='block':command['inputs']=inputs
        elif command['rule']=='generalize':need(len(inputs)==1,'one generalization receptor');command['source']=inputs[0]
        else:need(not inputs,'zero-input primitive edge')
        source[out]=len(rows);rows.append(command);chosen.append(dict(row=len(rows)-1,formula=out,rule=i,sources=inputs))
    return rows,chosen
def main():
    began=time.perf_counter();plan=json.loads((OUT/'audit-plan.json').read_text());producer=json.loads((OUT/'plan.json').read_text());base=json.loads((PARENT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());records=load(OUT/'native.json.gz');need(summary['status']=='complete_forward_observations_pending_independent_audit','complete forward checkpoints')
    for p,h in plan['source_sha256'].items():need(sha(ROOT/p)==h,'exact frozen auditor source '+p)
    for p,h in producer['input_sha256'].items():need(sha(ROOT/p)==h,'unchanged admitted finite control inputs '+p)
    result=dict(status='checking',observations=[],native_replays=[],micro_steps=0);requests={}
    for lane in producer['lanes']:
        raw=load(OUT/(lane+'.json.gz'));c=load(PARENT/(lane+'-reachable-core.json.gz'));ids={packed(f):i for i,f in enumerate(c['basis'])};edges=[dict(rule=i,inputs=[ids[packed(p)] for p in r['premises']],output=ids[packed(r['conclusion'])]) for i,r in enumerate(c['rules'])];ranks=worklist(edges,len(ids));witnesses=[None]*len(ids)
        for e in edges:
            output=e['output'];rank=ranks[output]
            if witnesses[output] is None and rank is not None and (not e['inputs'] and rank==0 or e['inputs'] and all(ranks[p] is not None and ranks[p]<rank for p in e['inputs'])):witnesses[output]=dict(rule=e['rule'],rank=rank)
        layers=[[i for i,r in enumerate(ranks) if r==j] for j in range(max(r for r in ranks if r is not None)+1)];expected=dict(edges=edges,layers=layers,witnesses=witnesses,edge_scans=(len(layers)+1)*len(edges),fixed_point_reachable=sum(r is not None for r in ranks),rounds=len(layers));need(raw['closure']==expected,'every complete closure edge/rank/first eligible deterministic witness');proof,chosen=dag_word(c,witnesses,base['case']['target']);need(raw['theory']==base['case']['theory'] and raw['target']==base['case']['target'] and raw['proof']==proof and raw['selected_witnesses']==chosen,'independent exact full DAG/strict-prior word, original theory and target');metric=dict(lane=lane,complete_edges=len(edges),complete_closure_formulas=expected['fixed_point_reachable'],word_length=None if proof is None else len(proof),same_12_row_boundary_fits=proof is not None and len(proof)<=producer['comparison_rows']);result['observations'].append(metric)
        if proof is not None:
            names={r['name'] for r in proof if r['rule']=='block'};original=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=proof,target=base['case']['target']);need(raw['original_request']==original,'exact whole target derivation including all used local proofs');full=expanded(original);primitive=copy.deepcopy(original);primitive.update(blocks=[],proof=shared(full));need(raw['primitive_request']==primitive and raw['expanded_commands']==len(full),'independent generic whole expansion/sharing');need(whole_replay(original)['status']==whole_replay(primitive)['status']=='accepted','separate complete host logical checks');metric.update(expanded_commands=len(full),shared_primitive_commands=len(primitive['proof']))
            for item,mode in zip(raw['whole_variants'],producer['whole_variants']):
                expected_request=original if mode=='selected-high-level' else primitive;q=item['query'];need(item['mode']==mode and item['request_sha256']==pin(expected_request) and records[q]['request']==expected_request and item['native_status']==records[q]['result']['status'],'every exact native request/outcome including unknown');requests[q]=expected_request
            need(len(raw['whole_variants'])==len(producer['whole_variants']),'every declared whole variant completed')
        else:need(not raw['whole_variants'],'no native result without automatic word')
        (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('independent forward closure/word',json.dumps(metric),flush=True)
    need(set(requests)==set(range(len(records))),'every native computation accounted');DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native checker');TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro))
    for j,rec in enumerate(records):
        initial=initial_for(micro,boundary['cases'][0]['initial'],requests[j]);raw=input_bytes(initial);need(hashlib.sha256(raw).hexdigest()==rec['input_sha256'] and gzip.decompress((OUT/('query-%03d-input.bin.gz'%j)).read_bytes())==raw,'complete real parser input');(TMP/'input.bin').write_bytes(raw);response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']));output=(TMP/'output.bin').read_bytes()
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'forward native execution replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'] and gzip.decompress((OUT/('query-%03d-output.bin.gz'%j)).read_bytes())==output,'all native output and true parser start');result['native_replays'].append(dict(query=j,status=response['status'],seconds=response['seconds'],micro_steps=response['micro_steps'],whole_input_output_matched=True,out_of_frame_bands=overflowing(output)));result.update(micro_steps=result['micro_steps']+response['micro_steps'],seconds=time.perf_counter()-began);(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print('independent forward native replay',j,response['status'],flush=True)
    result.update(status='passed_complete_forward_control_and_native_replay',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Ordinary full retained-hyperedge forward control only, not GCTS or RL. Complete independently reconstructed closure/witness/DAG/word, exact original theory/target, generic expansion/sharing and every unchanged native computation independently replayed from actual parser with exact input/output/steps/FNV. Unknown native outcomes remain unknown.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
