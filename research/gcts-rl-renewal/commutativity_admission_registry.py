"""Reconcile exact independently replayed local admissions; no target search."""
import gzip,hashlib,json,time
from pathlib import Path
from audit_certificate_boundary import pin

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011';OUT=PARENT/'native-complete'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'registry-plan.json').read_text())
    for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen registry producer '+p)
    required=load(PARENT/'attempt-02/admission-requirements.json.gz');sources={};audits={}
    for label,directory,expected in (('native-pilot',PARENT/'native-pilot',8),('chunk-43',OUT/'chunk-43',43),('chunk-42',OUT/'chunk-42',42)):
        a=json.loads((directory/'audit.json').read_text());need(a['status'] in ('passed_complete_frozen_eight_native_pilot_replay','passed_complete_accepted_chunk_native_replay') and a['native_admissions']==expected,'complete native replay '+label);audits[label]=a
        for q in load(directory/'native.json.gz'):need(q['result']['status']=='accepted' and q['request_sha256'] not in sources,'unique accepted fresh request');sources[q['request_sha256']]=(label,q)
    old=load(ROOT/'.gcts-active/left-successor-20261011/pilot-native.json.gz');prioraudit=json.loads((ROOT/'.gcts-active/left-successor-20261011/pilot-audit.json').read_text());need(prioraudit['status']=='passed_preparation_native_replay_only','exact prior full replay');rows=[];theory=json.loads((PARENT/'attempt-02/plan.json').read_text())['case']['theory']
    for item in sorted(required,key=lambda q:q['name']):
        if item['exact_prior_request'] is None:label,q=sources[item['request_sha256']];obs=next(a for a in audits[label]['observations'] if a['query']==q['id']);need(obs['status']=='accepted' and obs['request_sha256']==item['request_sha256'] and obs['all_input_output_matched'],'individual replay binding')
        else:
            q=old[item['exact_prior_request']['query']];label='historical-exact-reuse';obs=next(a for a in prioraudit['queries'] if a['query']==q['id']);need(q['result']['status']==obs['status']=='accepted' and obs['complete_input_output_sha256_matched'],'historical accepted whole replay')
        taut=['imp',['bot'],['bot']];req=dict(protocol='gcts-fol-1',theory=theory,blocks=[item['definition']],proof=[dict(rule='tautology',formula=taut)],target=taut);need(q['request']==req and q['request_sha256']==item['request_sha256']==pin(req),'byte-identical whole request and original theory');rows.append(dict(name=item['name'],definition=item['definition'],definition_sha256=pin(item['definition']),request_sha256=pin(req),status='native_accepted',evidence=label,query=q['id'],input_sha256=q['input_sha256'],output_sha256=q['output_sha256'],native_micro_steps=q['result']['micro_steps'],native_seconds=q['seconds']))
    need(len(rows)==94 and len(sources)==93,'entire94registry');value=dict(status='complete_exact94_admission_registry_pending_independent_audit',theory=theory,target=json.loads((PARENT/'attempt-02/plan.json').read_text())['case']['target'],program_sha256=plan['program_sha256'],micro_sha256=plan['micro_sha256'],definitions=rows,fresh_admissions=93,historical_exact_reuses=1,target_searches=0,scope='Individual generic localdefinitions admitted under exactoriginaltheory/premises. Not a commutativityproof, combinedwholecertificate acceptance or targetsearch.',seconds=time.perf_counter()-began);(OUT/'registry.json.gz').write_bytes(gzip.compress(json.dumps(value,separators=(',',':')).encode(),mtime=0));print(json.dumps(dict(status=value['status'],definitions=94,seconds=value['seconds'])))
if __name__=='__main__':main()
