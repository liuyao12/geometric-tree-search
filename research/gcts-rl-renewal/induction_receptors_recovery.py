"""Explicit recovery after the frozen attempt-2 checkpoint bug.

This does not change the admitted grammar, seed, search scheduler or checker.
It repeats the original seven-row point search and saves its complete trace
before inspecting the already-recorded unknown native outcome. The nine-row
observation was never attempted and is not silently replaced by a new run.
"""
import copy,gzip,hashlib,json,resource,struct,subprocess,sys,time
from pathlib import Path
from induction_receptors_points import Model
from native_receptor_points import search
import induction_receptors_audit as A
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/induction-receptors-20261011';OLD=OUT/'attempt-02'
TMP=Path('/private/tmp/gcts-induction-recovery-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def frozen_sources():
    p=json.loads((OLD/'plan.json').read_text())
    for name,h in p['source_sha256'].items():
        need(sha(ROOT/name)==h and sha(OLD/'source-snapshot'/name)==h,'attempt-2 frozen source '+name)
    declaration=json.loads((OUT/'recovery-plan.json').read_text())
    need(sha(Path(__file__))==declaration['recovery_source_sha256'],'recovery freeze')
    return p,declaration
def recover():
    began=time.perf_counter();plan,declaration=frozen_sources();c=load(OLD/'catalog.json.gz');admission=load(OLD/'admission.json.gz');records=load(OLD/'native-records.json.gz')
    observed=plan['observations'][0];spec=copy.deepcopy(plan['case']);spec.update(id=observed['id'],length=observed['length'])
    model=Model(spec,c,admission);r=search(model,**plan['search_limits']);r['command_skeleton']=r['proof']
    if r['proof'] is not None:r['proof']=model.decode(r['placements'])
    raw=dict(case=spec,search=r,model=model.record(),native_query=74,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,recovery=dict(source='recovery-plan.json',repeat_cost=True,original_search_seconds='not saved; unknown'))
    save(OUT/'recovered-left-zero-seven.json.gz',raw)
    q=records[74];need(r['proof']==q['request']['proof'],'deterministic recovered proof equals original whole query 74')
    names={row['name'] for row in r['proof'] if row['rule']=='block'};request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=r['proof'],target=spec['target'])
    need(request==q['request'],'entire original whole request identity')
    summary=dict(status='recovered_point_trace_whole_native_unknown',point_status=r['status'],whole_native_status=q['result']['status'],native_query=74,attempts=r['metrics']['attempts'],search_seconds=r['seconds'],model_setup_seconds=model.compile_seconds,recovery_seconds=time.perf_counter()-began,placements=len(model.cache),rows=len(r['proof']),proof_request_sha256=q['request_sha256'],peak_rss_bytes=raw['peak_rss_bytes'],nine_row_status='not run; runner terminated on first whole native unknown',original_search_seconds='not saved; unknown')
    (OUT/'recovery-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
def diagnosis(data):
    words=iter(struct.unpack('<'+'I'*(len(data)//4),data));need(next(words)==0x47544d34,'output magic');state=next(words);bands=next(words);bad=[]
    for i in range(bands):
        head=next(words);capacity=next(words)
        if head>=capacity:bad.append(dict(band=i,head=head,capacity=capacity))
        for _ in range(capacity):next(words)
    return dict(state=state,out_of_frame_bands=bad)
def audit():
    began=time.perf_counter();plan,declaration=frozen_sources();c=load(OLD/'catalog.json.gz');admission=load(OLD/'admission.json.gz');records=load(OLD/'native-records.json.gz');raw=load(OUT/'recovered-left-zero-seven.json.gz')
    result=dict(status='checking',catalog=A.catalog_binding(c,plan['case']),tree={},native_replays=[])
    A.model_binding(raw['case'],c,raw['model']);need(raw['model']['inference_rules']==c['rules'],'complete inference rule identity');result['tree']=A.tree_binding(raw)
    need(raw['search']['proof']==records[74]['request']['proof'],'recovered certificate exact query 74')
    taut=['imp',['bot'],['bot']];requests={}
    for d,item in zip(c['definitions'],admission['definitions']):
        q=item['query'];r=dict(protocol='gcts-fol-1',theory=plan['case']['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
        need(item['name']==d['name'] and records[q]['request']==r and records[q]['result']['status']=='accepted','native local admission exact');requests[q]=r
    need(len(admission['definitions'])==len(c['definitions']) and admission['status']=='native_accepted','complete local admission')
    for item,command in zip(admission['primitive'],c['primitive_schemes']):
        q=item['query'];r=dict(protocol='gcts-fol-1',theory=plan['case']['theory'],blocks=[],proof=[command],target=command['formula']);need(records[q]['request']==r and item['command']==command,'primitive diagnostic provenance');requests[q]=r
    need(len(admission['primitive'])==plan['primitive_query_budget'] and admission['primitive_status']=='unknown_compile_budget','primitive admission limitation')
    summary=json.loads((OLD/'summary.json').read_text())
    for item in summary['probes']:
        q=item['query'];need(records[q]['result']['status']==item['expected'],'scope probe');requests[q]=records[q]['request']
    names={row['name'] for row in raw['search']['proof'] if row['rule']=='block'};requests[74]=dict(protocol='gcts-fol-1',theory=raw['case']['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=raw['search']['proof'],target=raw['case']['target'])
    need(set(requests)==set(range(len(records))) and requests[74]==records[74]['request'],'every computation accounted')
    DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native checker')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));steps=0
    # Diagnose the actual failed whole request first, then independently replay
    # the complete admission/probe ledger. Every result is checkpointed.
    for q in [74]+list(range(74)):
        rec=records[q];r=requests[q];need(rec['request_sha256']==pin(r) and rec['query_target']=='fixed_assertion','full request digest')
        initial=initial_for(micro,boundary['cases'][0]['initial'],r);(TMP/'input.bin').write_bytes(input_bytes(initial));need(sha(TMP/'input.bin')==rec['input_sha256'],'whole independent parser input')
        response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'native replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'],'true parser start and full output')
        try:logical=whole_replay(r)['status']
        except ValueError:logical='rejected'
        if response['status'].startswith('unknown'):need(logical=='accepted','host audit of unfinished whole certificate');result['whole_unknown_diagnosis']=diagnosis((TMP/'output.bin').read_bytes());result['whole_unknown_logical_audit_only']=logical
        else:need(logical==response['status'],'separate logical audit')
        steps+=response['micro_steps'];result['native_replays'].append(dict(query=q,status=response['status'],seconds=response['seconds'],micro_steps=response['micro_steps']));result.update(native_micro_steps=steps,seconds=time.perf_counter()-began)
        (OUT/'recovery-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('recovery audit',q,response['status'],flush=True)
    result.update(status='passed',scope='Entire finite catalog, point inventory and recovered tree independently reconstructed; all 75 original native computations independently replayed from parser start, including exact heap-budget unknown. Native theorem acceptance remains unknown; separate host logical acceptance is audit-only.')
    (OUT/'recovery-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('RECOVERY AUDIT PASSED',result['seconds'],flush=True)
if __name__=='__main__':recover() if sys.argv[1]=='recover' else audit()
