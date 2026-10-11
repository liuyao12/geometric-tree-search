"""Independent exact assertion/input/native provenance and complete replay."""
import argparse,json,time,gzip,hashlib,sys
from pathlib import Path
from external_prover_inputs import sha,canonical
from external_induction_tstp_audit import exact_input
from external_left_successor_focus import check_output
from audit_certificate_boundary import initial_for
from audit_proof_boundary import input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_inventory import packed
from hilbert_boundary_transfer_audit import recipients,request

ROOT=Path(__file__).resolve().parents[2];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/external-hilbert-transfer-20261011'
SOURCE=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes())) if p.suffix=='.gz' else json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def need(v,message):
    if not v:raise ValueError(message)
def binding():
    began=time.perf_counter();plan=load(OUT/'plan.json');bundle=load(OUT/'inventory.json');native_plan=load(SOURCE/'plan.json');audit=load(SOURCE/'audit.json');native=load(SOURCE/'native.json.gz');specs=recipients()
    for n,h in plan['source_sha256'].items():need(sha((ROOT/n).read_bytes())==h,'frozen source '+n)
    for n,e in plan['data_dependencies'].items():need(sha((ROOT/n).read_bytes())==e['sha256'] and (ROOT/n).stat().st_size==e['bytes'],'frozen input '+n)
    for e in plan['preserved_exports']:need(sha((ROOT/e['path']).read_bytes())==e['sha256'],'immutable prior export')
    need(sha((OUT/'inventory.json').read_bytes())==plan['inventory_sha256'],'bundle digest')
    need(audit['status']=='passed' and audit['production_outcome']=='complete' and audit['fresh_native_queries']==len(native)==64 and audit['complete_guard_queries']==61,'full native authority')
    need(audit['plan_sha256']==sha((SOURCE/'plan.json').read_bytes())==bundle['native_plan_sha256'] and sha((SOURCE/'audit.json').read_bytes())==bundle['native_audit_sha256'],'native exact audit/plan')
    need(len(specs)==len(native_plan['cases'])==4 and all(all(s[k]==v for k,v in t.items()) for s,t in zip(native_plan['cases'],specs)),'independent literal guarded assertions')
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=load(DOC/'proof-boundary-001.json');need(sha(packed(micro))==PINNED_MICRO and sha(packed(boundary['program']))==PINNED_PROGRAM,'unchanged native authority code')
    inventory=load(SOURCE/'inventories.json.gz');native_bindings=[]
    for case,e in zip(bundle['cases'],plan['inputs']):
        group=case['group'];variants=[s for s in specs if s['group']==group];need(case['spec']['theory']==variants[0]['theory']==variants[1]['theory'] and case['spec']['target']==variants[0]['target']==variants[1]['target'],'exact assertion and equal row variants')
        need(case['native_variants']==[c for c in native_plan['cases'] if c['group']==group],'all native variants')
        path=OUT/e['name'];mapping=load(path.with_suffix('.mapping.json'));text=path.read_text();theory=variants[0]['theory']
        need(sha(path.read_bytes())==e['input_sha256'] and sha(path.with_suffix('.mapping.json').read_bytes())==e['mapping_sha256'] and exact_input(text,mapping)==5,'complete independent AST round trip')
        fs={n:'f'+str(i) for i,n in enumerate(sorted(theory['functions']))};ps={n:'p'+str(i) for i,n in enumerate(sorted(theory['predicates']))}
        need(mapping['functions']==fs and mapping['predicates']==ps and mapping['function_arities']=={fs[n]:a for n,a in theory['functions'].items()} and mapping['predicate_arities']=={ps[n]:a for n,a in theory['predicates'].items()},'injective exact signatures')
        expected=[dict(name='a'+str(i),role='axiom',original_name=n,formula=f) for i,(n,f) in enumerate(sorted(theory['axioms'].items()))]+[dict(name='goal',role='conjecture',original_name='unchanged target',formula=variants[0]['target'])]
        need(mapping['entries']==expected and all(x['role']!='lemma' for x in mapping['entries']) and mapping['native_row_boundaries']==[s['length'] for s in variants] and mapping['external_row_boundary'] is None,'all and only exact axioms/target; no library')
        seen=set()
        for obs in audit['observations']:
            if not obs['case_id'].startswith('transfer-'+group+'-') or obs['certification']!='accepted':continue
            tag=obs['tag'];o=load(SOURCE/(tag+'-final.json.gz'));bind=o['native_binding'];q=native[bind['query']];spec=next(s for s in specs if s['id']==o['case_id'])
            need(bind['origin']=='fresh' and q['request']==request(spec,inventory[o['language']],o['search']['proof']) and sha(packed(q['request']))==q['request_sha256']==bind['request_sha256'] and q['request']['theory']==theory and q['request']['target']==variants[0]['target'],'same assertion actual searched native proof')
            need(q['result']['status']=='accepted','native whole acceptance');boot=initial_for(micro,boundary['cases'][0]['initial'],q['request']);need(sha(input_bytes(boot))==q['input_sha256'] and q['result']['start']==88986,'full native boundary input')
            need(q['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'native tagged words')
            need(sha((SOURCE/(tag+'.json.gz')).read_bytes())==o['pre_certification_checkpoint_sha256'],'pre-native searched checkpoint')
            if q['id'] not in seen:native_bindings.append(dict(group=group,query=q['id'],request_sha256=q['request_sha256'],input_sha256=q['input_sha256'],output_sha256=q['output_sha256'],micro_steps=q['result']['micro_steps'],native_seconds=q['seconds']));seen.add(q['id'])
        need(seen,'at least one actual same-assertion native proof')
    return dict(status='passed_exact_two_assertion_input_native_binding',seconds=time.perf_counter()-began,plan_sha256=sha((OUT/'plan.json').read_bytes()),native_audit_sha256=sha((SOURCE/'audit.json').read_bytes()),native_bindings=native_bindings,source_paths=len(plan['source_sha256']),data_paths=len(plan['data_dependencies']),inputs=2,input_entries=[5,5],lemma_inputs=0,native_execution_rerun=False)
def after():
    began=time.perf_counter();gate=binding();plan=load(OUT/'plan.json');summary=load(OUT/'summary.json');checked=[];unknown=[]
    need(summary['plan_sha256']==sha((OUT/'plan.json').read_bytes()) and summary['seconds']<=180.5,'exact capped producer')
    need(len(summary['observations'])+len(summary['unexecuted'])==4,'all scheduled outcomes')
    need([dict(kind=o['kind'],repetition=o['repetition']) for o in summary['observations']]==plan['target_order'][:len(summary['observations'])],'declared interleaved order')
    for o in summary['observations']:
        stem=o['stem'];path=OUT/('hilbert-'+o['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(stem+'.tstp')).read_text()
        need(sha(text)==o['output_sha256'] and text==o['e_measurement']['stdout'] and load(OUT/(stem+'.process.json'))==o['e_measurement'],'returned output/process binding')
        for suffix in ('check','replay'):
            answer=o['proof_'+suffix]
            if answer is None:continue
            req=load(OUT/(stem+'-'+suffix+'.request.json'));need(sha((OUT/(stem+'-'+suffix+'.request.json')).read_bytes())==answer['request_sha256'] and req['output']==text and req['mapping']==mapping and req['input_path']==str(path) and load(OUT/(stem+'-'+suffix+'.result.json'))==answer,'original complete worker inputs/results')
        if o['certificate_status']=='checked_complete_derivation':
            need(o['proof_check']['status']==o['proof_replay']['status']=='complete','check and serialized replay')
            again=check_output(text,mapping,str(path),saved=o['proof_check']['result']);need(again['status']=='checked_complete_derivation' and again['steps']==o['proof_steps'] and not again.get('used_lemma_inputs') and not o['used_lemma_inputs'],'every line full context revalidated')
            checked.append(dict(kind=o['kind'],repetition=o['repetition'],steps=again['steps'],output_sha256=sha(text),used_lemma_inputs=[]))
        else:unknown.append(dict(kind=o['kind'],repetition=o['repetition'],status='unknown',error=o['proof_check']['result'].get('error')))
    result=dict(status='passed_complete_result_source_input_replay_audit',binding=gate,producer_status=summary['status'],checked_replays=checked,unknowns=unknown,unexecuted=summary['unexecuted'],seconds=time.perf_counter()-began,scope='Every actual returned line independently replayed under the unchanged external first-order adapter. Same native assertions/resources are provenance; no native Wang or GCTS acceptance claim for E outputs.')
    dump(OUT/'audit.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['binding','after']);a=p.parse_args();dump(OUT/'input-audit.json',binding()) if a.phase=='binding' else after()
