"""Preserve/audit the prior unknown and prepare exact root-owned integration."""
import gzip,hashlib,json,shutil,subprocess,time,zipfile
from pathlib import Path
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/induction-receptors-20261011';OLD=OUT/'attempt-01';DOC=ROOT/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-induction-prior-audit-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def prior():
    began=time.perf_counter();plan=json.loads((OLD/'plan.json').read_text());records=load(OLD/'native-records.json.gz');micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());TMP.mkdir(parents=True,exist_ok=True)
    if pin(micro)!=PINNED_MICRO:raise ValueError('changed checker')
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));steps=0
    for rec in records:
        initial=initial_for(micro,boundary['cases'][0]['initial'],rec['request']);(TMP/'input.bin').write_bytes(input_bytes(initial))
        if sha(TMP/'input.bin')!=rec['input_sha256']:raise ValueError('prior true-parser input')
        response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',plan['native_steps']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):
            if str(response[k])!=str(rec['result'][k]):raise ValueError('prior native replay '+k)
        if sha(TMP/'output.bin')!=rec['output_sha256'] or rec['result']['start']!=88986:raise ValueError('prior full output and start')
        if response['status']=='accepted' and whole_replay(rec['request'])['status']!='accepted':raise ValueError('prior logical cross-check')
        steps+=response['micro_steps'];print('prior native replay',rec['id'],response['status'],flush=True)
        if response['status'].startswith('unknown'):
            for name in ('input.bin','output.bin'):(OLD/('unknown-'+name+'.gz')).write_bytes(gzip.compress((TMP/name).read_bytes(),mtime=0))
    result=dict(status='passed',queries=len(records),native_micro_steps=steps,seconds=time.perf_counter()-began,true_parser_start=88986,unknown_replayed=True)
    (OLD/'audit.json').write_text(json.dumps(result,indent=2)+'\n');return result
def integrate():
    audit=json.loads((OUT/'audit.json').read_text());old_audit=json.loads((OLD/'audit.json').read_text())
    if audit['status']!='passed' or old_audit['status']!='passed':raise ValueError('required completed independent audits')
    subprocess.run(['python3',str(HERE/'induction_receptors_export.py')],check=True)
    old=json.loads((OLD/'cost-summary.json').read_text());path=DOC/'induction_receptors.html';text=path.read_text()
    paragraph='<section id="prior-unknown"><h2>Preserved preparation failure</h2><p>The first frozen admission attempt accepted 14 local definitions, then reached its five-billion-step ceiling on the next definition. It consumed '+str(round(old['native_seconds'],3))+' s before any target search. This unknown was retained; it was not converted into rejection or proof failure. A target-independent dependency analysis then reduced the generated local commands from 1,077 to 853 across the same 66 interfaces by preserving independent facts and lifting them only when needed. The second source freeze uses a disclosed twenty-billion-step ceiling. Admission still validates every new definition natively.</p><p>The prior attempt was independently replayed in full, including its unfinished output tape: '+str(round(old_audit['seconds'],3))+' s and '+str(old_audit['native_micro_steps'])+' micro steps. <a href="induction_receptors_prior.json.gz">Prior native requests/results</a> · <a href="induction_receptors_prior_audit.json">Prior independent replay</a> · <a href="induction_receptors_prior_sources.zip">Prior frozen sources, plan and unknown input/output tapes</a>.</p></section>'
    text=text.replace('<h2>Independent evidence</h2>',paragraph+'<h2>Independent evidence</h2>');path.write_text(text)
    shutil.copyfile(OLD/'native-records.json.gz',DOC/'induction_receptors_prior.json.gz');shutil.copyfile(OLD/'audit.json',DOC/'induction_receptors_prior_audit.json')
    with zipfile.ZipFile(DOC/'induction_receptors_prior_sources.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OLD/'source-snapshot').rglob('*')):
            if p.is_file():z.write(p,str(p.relative_to(OLD)))
        for name in ('plan.json','cost-summary.json','unknown-input.bin.gz','unknown-output.bin.gz'):z.write(OLD/name,name)
    manifest=json.loads((OUT/'integration.json').read_text());files=[v['path'] for v in manifest['files']]+['docs/research/gcts-rl-renewal/induction_receptors_prior.json.gz','docs/research/gcts-rl-renewal/induction_receptors_prior_audit.json','docs/research/gcts-rl-renewal/induction_receptors_prior_sources.zip']
    manifest['files']=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files];manifest['prior_attempt_audit']=old_audit;manifest['current_audit']=audit
    (OUT/'integration.json').write_text(json.dumps(manifest,indent=2)+'\n');print('integration prepared',len(files),'files')
if __name__=='__main__':
    import sys
    prior() if len(sys.argv)>1 and sys.argv[1]=='prior' else integrate()
