"""Independent entire point-tree and whole-certificate native audit.

No new model/search/producer imports. Full finite grammar and proved pruning,
local compaction and all native admissions have separate completed gates.
This audit reconstructs every retained placement, every tree domain/decision,
the selected explicit proof, generic expansion/sharing and every unique whole
native computation. Unknown whole outcomes remain unknown.
"""
import copy,gzip,json,subprocess,time
from pathlib import Path
import induction_receptors_audit as A
from induction_receptors_compaction_audit import expanded,shared
from left_successor_pilot_audit import overflowing
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-search-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'search-audit-plan.json').read_text());producer=json.loads((OUT/'search-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'search-summary.json').read_text());records=load(OUT/'search-native.json.gz');need(summary['status']=='complete_search_and_native_observations_pending_independent_audit','complete search checkpoints')
    for p,h in plan['source_sha256'].items():need(sha(ROOT/p)==h,'frozen audit source '+p)
    need(json.loads((OUT/'audit.json').read_text())['status']=='passed_preparation_audit_only' and json.loads((OUT/'reachability-audit.json').read_text())['status']=='passed_finite_grammar_structural_pruning' and json.loads((OUT/'admission-audit.json').read_text())['status']=='passed_complete_reachable_native_admission','whole independent preparation/admission chain');result=dict(status='checking',observations=[],native_replays=[],micro_steps=0);requests={};trees={};first_by_lane={}
    for obs in producer['observations']:
        raw=load(OUT/(obs['id']+'.json.gz'));c=load(OUT/(obs['lane']+'-reachable-core.json.gz'));spec=copy.deepcopy(base['case']);spec.update(id=obs['id'],length=obs['length']);need(raw['case']==spec and raw['lane']==obs['lane'] and raw['rep']==obs['rep'],'predeclared observation identity');A.model_binding(spec,c,raw['model']);need(raw['model']['inference_rules']==c['rules'] and raw['model']['structural_pruning']==c['structural_pruning'],'exact retained grammar/pruning model');metrics=A.tree_binding(raw);result['observations'].append(dict(id=obs['id'],status=raw['search']['status'],metrics=metrics,complete_placements=len(raw['model']['placements'])))
        image=dict(tree_pin=pin(raw['search']['tree']),proof_pin=pin(raw['search']['proof']),status=raw['search']['status'])
        if obs['lane'] in first_by_lane:
            first=first_by_lane[obs['lane']];same=image['tree_pin']==first['tree_pin'] and image['proof_pin']==first['proof_pin'];finished=all(status!='unknown_search_budget' for status in (image['status'],first['status']));need(not finished or same,'completed same-inventory deterministic fresh graph correspondence');result['observations'][-1]['same_inventory_correspondence']=dict(equal_full_tree_and_proof=same,both_finished=finished,scope='Wall-budget cutoffs may truncate at different prefixes; both full recorded prefixes are audited independently.')
        else:first_by_lane[obs['lane']]=image
        if raw['search']['proof'] is not None:
            names={r['name'] for r in raw['search']['proof'] if r['rule']=='block'};original=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=raw['search']['proof'],target=spec['target']);need(original==raw['original_request'],'whole selected request reconstruction');full=expanded(original);primitive=copy.deepcopy(original);primitive.update(blocks=[],proof=shared(full));need(len(full)==raw['expanded_commands'] and primitive==raw['primitive_request'],'generic compaction independently reconstructed, unchanged theory/target');need(whole_replay(original)['status']==whole_replay(primitive)['status']=='accepted','separate host whole acceptance')
            for item,mode in zip(raw['whole_variants'],producer['whole_variants']):
                expected=original if mode=='selected-high-level' else primitive;need(item['mode']==mode and item['request_sha256']==pin(expected),'exact requested whole variant');q=item['query'];need(records[q]['request']==expected and records[q]['result']['status']==item['native_status'],'actual whole outcome including unknown');requests[q]=expected
        else:need(not raw['whole_variants'],'no whole result without selected proof')
        (OUT/'search-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('whole point-tree audit',obs['id'],metrics,flush=True)
    need(set(requests)==set(range(len(records))),'every unique whole native computation accounted');DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native checker');TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro))
    for j,rec in enumerate(records):
        expected=requests[j];initial=initial_for(micro,boundary['cases'][0]['initial'],expected);raw=input_bytes(initial);need(sha_bytes(raw)==rec['input_sha256'] and gzip.decompress((OUT/('search-query-%03d-input.bin.gz'%j)).read_bytes())==raw,'whole real parser input');(TMP/'input.bin').write_bytes(raw);response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']));output=(TMP/'output.bin').read_bytes()
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'whole native replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'] and gzip.decompress((OUT/('search-query-%03d-output.bin.gz'%j)).read_bytes())==output,'whole output and actual parser start');result['native_replays'].append(dict(query=j,status=response['status'],seconds=response['seconds'],micro_steps=response['micro_steps'],whole_input_output_matched=True,out_of_frame_bands=overflowing(output)));result.update(micro_steps=result['micro_steps']+response['micro_steps'],seconds=time.perf_counter()-began);(OUT/'search-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('searched whole native replay',j,response['status'],flush=True)
    result.update(status='passed_all_recorded_search_and_native_outcomes',seconds=time.perf_counter()-began,scope='Complete independently proved finite-grammar projection, all retained scalar point placements, every full search-tree node/census/dead/forced/earliest-generation/fallback/rollback, exact selected source-explicit requests, independent generic expansion/compaction and every unique whole native replay with full parser input/output/execution fingerprint. Same-inventory fresh repetitions matched. Native unknowns remain unknown; no RL or cross-inventory speed claim.')
    (OUT/'search-audit.json').write_text(json.dumps(result,indent=2)+'\n')
def sha_bytes(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
