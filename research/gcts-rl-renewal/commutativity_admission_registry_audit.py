"""Independent request partition, definitions, native tapes and replay bindings."""
import gzip,hashlib,json,time
from pathlib import Path
from audit_certificate_boundary import pin

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'native-complete'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'registry-audit-plan.json').read_text());value=load(OUT/'registry.json.gz');requirements=load(PARENT/'attempt-02/admission-requirements.json.gz');need(value['status']=='complete_exact94_admission_registry_pending_independent_audit','producer complete')
    for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'independent registry freeze '+p)
    case=json.loads((PARENT/'attempt-02/plan.json').read_text())['case'];need(value['theory']==case['theory'] and value['target']==case['target'] and value['program_sha256']==plan['program_sha256'] and value['micro_sha256']==plan['micro_sha256'] and value['target_searches']==0,'originaltheory/target/checker');declared={q['name']:q for q in requirements};actual={q['name']:q for q in value['definitions']};need(len(declared)==len(actual)==len(value['definitions'])==94 and set(declared)==set(actual),'complete exactname registry');native={};spent=0;replayed=0
    for label,directory,total in (('native-pilot',PARENT/'native-pilot',8),('chunk-43',OUT/'chunk-43',43),('chunk-42',OUT/'chunk-42',42)):
        rs=load(directory/'native.json.gz');audit=json.loads((directory/'audit.json').read_text());need(len(rs)==total==len(audit['observations'])==audit['native_admissions'] and audit['status'] in ('passed_complete_frozen_eight_native_pilot_replay','passed_complete_accepted_chunk_native_replay'),'full passed native group');spent+=sum(q['result']['micro_steps'] for q in rs);replayed+=audit['micro_steps']
        for rec,obs in zip(rs,audit['observations']):
            need(rec['id']==obs['query'] and rec['result']['status']==obs['status']=='accepted' and rec['request_sha256']==obs['request_sha256'] and rec['result']['start']==88986 and obs['all_input_output_matched'] and not obs['out_of_frame_bands'],'full native observation binding')
            for k in ('micro_steps','physical_steps','micro_fnv64'):need(str(rec['result'][k])==str(obs[k]),'all native fingerprint '+k)
            for suffix,h in (('input',rec['input_sha256']),('output',rec['output_sha256'])):need(hashlib.sha256(gzip.decompress((directory/('query-%03d-%s.bin.gz'%(rec['id'],suffix))).read_bytes())).hexdigest()==h,'entire preserved native tape '+suffix)
            need(rec['request_sha256'] not in native,'unique fresh request');native[rec['request_sha256']]=(label,rec)
    olddir=ROOT/'.gcts-active/left-successor-20261011';old=load(olddir/'pilot-native.json.gz');oldaudit=json.loads((olddir/'pilot-audit.json').read_text());need(oldaudit['status']=='passed_preparation_native_replay_only','historical prioraudit');credit=0
    for name,item in declared.items():
        row=actual[name];tautology=['imp',['bot'],['bot']];expected={'target':tautology,'proof':[{'formula':tautology,'rule':'tautology'}],'blocks':[item['definition']],'theory':case['theory'],'protocol':'gcts-fol-1'};h=pin(expected);need(h==item['request_sha256']==row['request_sha256'] and row['definition']==item['definition'] and row['definition_sha256']==pin(item['definition']) and row['status']=='native_accepted','complete definitions and independently constructed request')
        if item['exact_prior_request'] is None:label,rec=native[h]
        else:
            credit+=1;label='historical-exact-reuse';rec=old[item['exact_prior_request']['query']];obs=next(x for x in oldaudit['queries'] if x['query']==rec['id']);need(rec['result']['status']==obs['status']=='accepted' and obs['complete_input_output_sha256_matched'] and rec['result']['micro_steps']==obs['micro_steps'] and rec['result']['start']==88986,'prior accepted exactnative replay')
            for suffix,sha in (('input',rec['input_sha256']),('output',rec['output_sha256'])):need(hashlib.sha256(gzip.decompress((olddir/('pilot-query-%03d-%s.bin.gz'%(rec['id'],suffix))).read_bytes())).hexdigest()==sha,'full original priorinput/output')
        need(rec['request']==expected and row['evidence']==label and row['query']==rec['id'] and row['input_sha256']==rec['input_sha256'] and row['output_sha256']==rec['output_sha256'] and row['native_micro_steps']==rec['result']['micro_steps'],'registry exactwhole request evidence')
    need(credit==1 and len(native)==93 and spent==replayed,'93fresh+1credit exact accounting');result=dict(status='passed_complete_exact94_native_admission_registry',definitions=94,fresh_native_admissions=93,historical_exact_request_reuses=1,fresh_micro_steps=spent,independent_fresh_replay_micro_steps=replayed,target_searches=0,commutativity_proof_discovered=False,program_sha256=plan['program_sha256'],micro_sha256=plan['micro_sha256'],registry_sha256=hashlib.sha256((OUT/'registry.json.gz').read_bytes()).hexdigest(),seconds=time.perf_counter()-began,scope='Complete finite localinterface inventory only. Every exactdefinition/theory/premise/whole request and fresh/prioraccepted native binding reconciled independently; all actual native tapes preservedandhashmatched. No targetproofsequence/search, fullPA completeness, combinedwholecertificate acceptance or RL claim.');(OUT/'registry-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
