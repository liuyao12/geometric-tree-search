"""Cold native certificate discovery, then checked literal accepting expansions.

No authored proof is passed to the search. Certificates are generated only
from the discovered commands, after every search observation has been saved.
"""
import copy,gzip,hashlib,json,struct,subprocess,sys,time
from pathlib import Path
from native_inventory_cases import donors,evaluation
from certificate_boundary_search import canonical,digest,Oracle
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-native-inventory-policy-20261010/formal')
SOURCES=('native_inference_inventory.py','native_inventory_policy.py','native_inventory_search.py','native_inventory_cases.py','native_inventory_worker.py','run_native_inventory_policy.py')
REUSED=('proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz','shared-wang-reader-001.json')
REUSED_SOURCES=('native_receptor_points.py','native_receptor_cases.py','turtle.py','boundary_oracle.cpp','certificate_boundary_cases.py','certificate_boundary_search.py','proof_boundary.py','tape_binary.py','micro_cert.py','shared_wang_inventory.py','audit_proof_boundary.py','micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp','audit_logical_wang_clusters.py','audit_tape_micro.cpp','fol_checker.tree')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,raw):
    p=DOCS/name;p.write_bytes(gzip.compress(raw,mtime=0));return dict(name=name,sha256=sha(p),bytes=p.stat().st_size,uncompressed_bytes=len(raw))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True,parents=True);pins={n:sha(HERE/n) for n in SOURCES};reused={n:sha(DOCS/n) for n in REUSED};rs={n:sha(HERE/n) for n in REUSED_SOURCES}
    micro=json.loads(gzip.decompress((DOCS/REUSED[1]).read_bytes()));old=json.loads((DOCS/REUSED[0]).read_text());raw=gzip.decompress((DOCS/REUSED[2]).read_bytes());inv=Inventory(raw)
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM or hashlib.sha256(raw).hexdigest()!=PINNED_TABLE:raise ValueError('pinned native palette')
    (TMP/'literal.bin').write_bytes(raw);(TMP/'code.bin').write_bytes(code_bytes(micro));write_cuts(cuts(micro),TMP/'cuts.bin');bands=[micro['allocation'][66]['slots'][r] for r in (1,2,3,4,19,29,20)]
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,*bands));compile_start=time.perf_counter()
    for source,name in (('boundary_oracle.cpp','oracle'),('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    data=dict(version='native-inventory-001',sources=pins,reused_inputs=reused,reused_sources=rs,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,inventory=json.loads((DOCS/REUSED[3]).read_text())['inventory'],compile_seconds=time.perf_counter()-compile_start,donors=donors(),cases=evaluation(),observations=[],certificates=[],repetitions=2,scope='Fresh RL selects validated, parameterized rule-cluster expansions on the unchanged reference GCTS point graph, with complete original fallback. Same grammar, scheduler, attempt/time budgets and native verification across all five cold lanes. No learned pruning or primitive-square GCTS; no competitive-prover advantage claim.')
    job=dict(kind='training',donors=donors(),directory=str(TMP/'training'),executable=str(TMP/'oracle'));(TMP/'job.json').write_bytes(canonical(job));stage=time.perf_counter();subprocess.run([sys.executable,str(HERE/'native_inventory_worker.py'),str(TMP/'job.json'),str(TMP/'worker.json')],check=True)
    training_raw=(TMP/'worker.json').read_bytes();training=json.loads(training_raw);data['training']=save('native-inventory-training-001.json.gz',training_raw);data['training_stage_seconds']=time.perf_counter()-stage
    policy=dict(version='native-inventory-policy-001',features=training['features'],weights=training['weights'],library=training['library'],training=data['training'],scope=training['scope']);policy_path=DOCS/'native-inventory-policy-001.json';policy_path.write_bytes(canonical(policy));data['policy']=dict(name=policy_path.name,sha256=sha(policy_path),bytes=policy_path.stat().st_size);winners={}
    for donor in training['donors']:
        rec=training['records'][donor['verification_query']];key=rec['request_sha256'];winners.setdefault(key,dict(request=rec['request'],selected=rec['result'],output_sha256=rec['output_sha256'],sources=['donor-'+donor['case']['id']],case_id=donor['case']['id'],role='inventory_donor'))
    methods=['base','zero','fixed','learned','no-family']
    for repetition in range(2):
        for index,spec in enumerate(evaluation()):
            rotated=methods[index%5:]+methods[:index%5];order=rotated if repetition==0 else list(reversed(rotated))
            for mode in order:
                label=spec['id']+'-'+mode+'-r'+str(repetition+1);directory=TMP/label;job=dict(kind='evaluation',case=spec,mode=mode,seed=20000+100*index+repetition,repetition=repetition+1,method_order=order,directory=str(directory),executable=str(TMP/'oracle'),policy=str(policy_path),policy_sha256=data['policy']['sha256']);(TMP/'job.json').write_bytes(canonical(job));stage=time.perf_counter()
                subprocess.run([sys.executable,str(HERE/'native_inventory_worker.py'),str(TMP/'job.json'),str(TMP/'worker.json')],check=True)
                raw_result=(TMP/'worker.json').read_bytes();r=json.loads(raw_result);artifact=save('native-inventory-001-'+label+'.json.gz',raw_result);row=dict(case=spec['id'],mode=mode,repetition=repetition+1,status=r['status'],queries=r['queries'],cold_seconds=r['cold_seconds'],worker_stage_seconds=time.perf_counter()-stage,artifact=artifact,metrics=r['search']['metrics'] if r.get('search') else None,verification_query=r.get('verification_query'));data['observations'].append(row)
                if r['status']=='native_proof_discovered' and mode=='learned':
                    record=r['records'][r['verification_query']];request=record['request'];key=digest(request);winners.setdefault(key,dict(request=request,selected=record['result'],output_sha256=record['output_sha256'],sources=[],case_id=spec['id'],role='frozen_evaluation'))['sources'].append(label)
                (TMP/'progress.json').write_bytes(canonical(data));print(label,r['status'],r['search']['metrics'].get('attempts',0),round(r['cold_seconds'],3),flush=True)
    # Only now materialize the accepting rectangles. No certificate was seeded.
    literal=dict(alphabet=data['inventory']['alphabet'],space=inv.space);oracle=Oracle(micro,old['cases'][0]['initial'],TMP/'oracle',TMP/'code.bin',TMP/'certificate-transport')
    try:
        for index,(key,spec) in enumerate(winners.items()):
            request=spec['request'];initial=oracle.initial(request);(TMP/'input.bin').write_bytes(input_bytes(initial));name='proof-'+str(index+1)
            built=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**9,6000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
            if built['status']!='accepted':raise ValueError('discovered native acceptance '+name)
            events=[json.loads(s) for s in (TMP/'events.jsonl').read_text().splitlines()];write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin')
            checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'checked-output.bin',10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
            if checked['status']!='checked_response' or checked['result']!='accepted' or sha(TMP/'output.bin')!=sha(TMP/'checked-output.bin'):raise ValueError('whole response derivation')
            write_input(literal,initial,TMP/'literal-input.bin');lr=run(TMP/'literal',(TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16));out=read_micro_output(TMP/'output.bin');lo=read_output(literal,initial,TMP/'literal-output.bin')
            for k in ('micro_steps','physical_steps','status'):
                if str(lr[k])!=str(built[k]):raise ValueError('literal/build '+k)
            if str(lr['micro_fnv64'])!=str(spec['selected']['micro_fnv64']) or sha(TMP/'output.bin')!=spec['output_sha256']:raise ValueError('discovered whole computation binding')
            if any(lo[k]!=out[k] for k in ('heads','words')):raise ValueError('all literal bands')
            row=dict(name=name,case_id=spec['case_id'],role=spec['role'],request=request,request_sha256=key,sources=spec['sources'],initial=initial,input_sha256=sha(TMP/'input.bin'),expected=dict(status='accepted',micro_steps=built['micro_steps'],physical_steps=built['physical_steps']),builder=built,checker=checked,literal=lr,output_sha256=sha(TMP/'output.bin'),output=out,header=header(TMP/'grammar.bin'),grammar=save('native-inventory-001-'+name+'.bin.gz',(TMP/'grammar.bin').read_bytes()),events=save('native-inventory-001-'+name+'-events.jsonl.gz',(TMP/'events.jsonl').read_bytes()),responses=save('native-inventory-001-'+name+'-responses.json.gz',(TMP/'root.json').read_bytes()))
            data['certificates'].append(row);(TMP/'progress.json').write_bytes(canonical(data));print(name,'fully checked',built['nodes'],'nodes',flush=True)
    finally:oracle.close()
    if any(sha(HERE/n)!=p for n,p in pins.items()):raise ValueError('measured source changed')
    data['total_seconds']=time.perf_counter()-began;save('native-inventory-001.json.gz',canonical(data));print('complete',round(data['total_seconds'],3),flush=True)
if __name__=='__main__':main()
