"""Fresh semantic lemma search, then complete native accepting certificates."""
import gzip,hashlib,json,struct,subprocess,sys,time
from pathlib import Path
from semantic_inventory_cases import donors,evaluation
from semantic_inventory_oracle import RequestOracle
from certificate_boundary_search import canonical,digest
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-semantic-receptor-inventory-20261010/formal')
SOURCES=('semantic_lemma_inventory.py','semantic_receptor_points.py','semantic_inventory_oracle.py',
         'semantic_inventory_guidance.py','semantic_inventory_search.py','semantic_inventory_cases.py',
         'semantic_inventory_policy.py','semantic_inventory_worker.py','semantic_point_smt.py','run_semantic_inventory.py')
REUSED=('proof-boundary-001.json','proof-boundary-microcode-001.json.gz',
        'proof-boundary-machine-001.bin.gz','shared-wang-reader-001.json')
REUSED_SOURCES=('native_receptor_points.py','native_receptor_cases.py','turtle.py','boundary_oracle.cpp',
    'certificate_boundary_cases.py','certificate_boundary_search.py','proof_boundary.py','tape_binary.py',
    'micro_cert.py','shared_wang_inventory.py','audit_proof_boundary.py','micro_line_builder.cpp',
    'micro_line_check.cpp','tape_runner.cpp','audit_logical_wang_clusters.py','audit_tape_micro.cpp',
    'fol_checker.tree','native_inventory_policy.py','native_inference_inventory.py','native_inventory_cases.py')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(name,raw):
    p=DOCS/name;p.write_bytes(gzip.compress(raw,mtime=0))
    return dict(name=name,sha256=sha(p),bytes=p.stat().st_size,uncompressed_bytes=len(raw))

def worker(job):
    (TMP/'job.json').write_bytes(canonical(job));began=time.perf_counter()
    subprocess.run([sys.executable,str(HERE/'semantic_inventory_worker.py'),
                    str(TMP/'job.json'),str(TMP/'worker.json')],check=True)
    raw=(TMP/'worker.json').read_bytes()
    return raw,json.loads(raw),time.perf_counter()-began

def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True,parents=True)
    pins={n:sha(HERE/n) for n in SOURCES};reused={n:sha(DOCS/n) for n in REUSED}
    rs={n:sha(HERE/n) for n in REUSED_SOURCES}
    micro=json.loads(gzip.decompress((DOCS/REUSED[1]).read_bytes()))
    old=json.loads((DOCS/REUSED[0]).read_text());raw=gzip.decompress((DOCS/REUSED[2]).read_bytes())
    inv=Inventory(raw)
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM or hashlib.sha256(raw).hexdigest()!=PINNED_TABLE:raise ValueError('fixed native palette')
    (TMP/'literal.bin').write_bytes(raw);(TMP/'code.bin').write_bytes(code_bytes(micro))
    write_cuts(cuts(micro),TMP/'cuts.bin')
    bands=[micro['allocation'][66]['slots'][r] for r in (1,2,3,4,19,29,20)]
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,*bands))
    stage=time.perf_counter()
    for source,name in (('boundary_oracle.cpp','oracle'),('micro_line_builder.cpp','builder'),
                        ('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    data=dict(version='semantic-inventory-001',sources=pins,reused_inputs=reused,reused_sources=rs,
        program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,
        inventory=json.loads((DOCS/REUSED[3]).read_text())['inventory'],
        compile_seconds=time.perf_counter()-stage,cases=evaluation(),observations=[],certificates=[],
        repetitions=2,methods=['base','zero','fixed','learned','no-family','z3'],
        scope='Fresh checked semantic lemma families and zero-start cluster learning. Five point-ordering lanes share a complete factored six-rule inventory and reference scheduler. Z3 is a separate algorithm on the same finite exact point constraints. Final certificates retain only the actual call dependency closure, which the unchanged native checker rechecks. No learned pruning, primitive-square GCTS, full PA/Hilbert or competitive-prover superiority claim.')
    raw_training,training,elapsed=worker(dict(kind='training',donors=donors(),
        directory=str(TMP/'training'),executable=str(TMP/'oracle')))
    data['training']=save('semantic-inventory-training-001.json.gz',raw_training)
    data['training_stage_seconds']=elapsed
    policy=dict(version='semantic-inventory-policy-001',features=training['features'],
                weights=training['weights'],library=training['library'],training=data['training'],
                scope=training['scope'])
    policy_path=DOCS/'semantic-inventory-policy-001.json';policy_path.write_bytes(canonical(policy))
    data['policy']=dict(name=policy_path.name,sha256=sha(policy_path),bytes=policy_path.stat().st_size)
    winners={}
    def select(case_id,role,record,source,priority):
        request=record['request'];key=digest(request)
        if case_id not in winners or priority>winners[case_id]['priority']:
            winners[case_id]=dict(request=request,selected=record['result'],
                output_sha256=record['output_sha256'],sources=[source],case_id=case_id,
                role=role,priority=priority,request_sha256=key)
        elif winners[case_id]['request_sha256']==key:winners[case_id]['sources'].append(source)
    for donor in training['donors']:
        select(donor['case']['id'],'primitive_inventory_donor',
               training['records'][donor['verification_query']],'donor-'+donor['case']['id'],10)
    promotion=training['promotion']
    select(promotion['case']['id'],'higher_inventory_donor',
           training['records'][promotion['verification_query']],'promotion-fixed',10)
    methods=data['methods']
    for repetition in range(2):
        for index,spec in enumerate(evaluation()):
            offset=index%len(methods);rotated=methods[offset:]+methods[:offset]
            order=rotated if repetition==0 else list(reversed(rotated))
            for mode in order:
                label=spec['id']+'-'+mode+'-r'+str(repetition+1)
                job=dict(kind='evaluation',case=spec,mode=mode,seed=64000+100*index+repetition,
                    repetition=repetition+1,method_order=order,directory=str(TMP/label),
                    executable=str(TMP/'oracle'),policy=str(policy_path),policy_sha256=data['policy']['sha256'])
                raw_result,r,elapsed=worker(job)
                artifact=save('semantic-inventory-001-'+label+'.json.gz',raw_result)
                search=r.get('search') or {}
                row=dict(case=spec['id'],mode=mode,repetition=repetition+1,status=r['status'],
                    queries=r['queries'],cold_seconds=r['cold_seconds'],worker_stage_seconds=elapsed,
                    artifact=artifact,metrics=search.get('metrics'),search_seconds=search.get('seconds'),
                    solver_encode_seconds=search.get('encode_seconds'),verification_query=r.get('verification_query'))
                data['observations'].append(row)
                if r['status']=='native_proof_discovered':
                    priority={'learned':5,'fixed':4,'z3':3,'base':2,'zero':1,'no-family':0}[mode]
                    select(spec['id'],'frozen_evaluation',r['records'][r['verification_query']],label,priority)
                (TMP/'progress.json').write_bytes(canonical(data))
                print(label,r['status'],search.get('metrics',{}).get('attempts'),
                      round(r['cold_seconds'],3),flush=True)
    # Accepting derivations are built only after the proof search observations.
    literal=dict(alphabet=data['inventory']['alphabet'],space=inv.space)
    oracle=RequestOracle(micro,old['cases'][0]['initial'],TMP/'oracle',
                         TMP/'code.bin',TMP/'certificate-transport')
    try:
        for index,spec in enumerate(winners.values()):
            request=spec['request'];initial=oracle.initial(request)
            (TMP/'input.bin').write_bytes(input_bytes(initial));name='proof-'+str(index+1)
            built=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',
                TMP/'output.bin',5*10**9,8000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
            if built['status']!='accepted':raise ValueError('accepting derivation unresolved '+name+': '+str(built))
            events=[json.loads(s) for s in (TMP/'events.jsonl').read_text().splitlines()]
            write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin')
            checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',
                TMP/'checked-output.bin',5*10**9,1500000000,TMP/'root.json',TMP/'observed.bin'))
            if checked['status']!='checked_response' or checked['result']!='accepted' or sha(TMP/'output.bin')!=sha(TMP/'checked-output.bin'):raise ValueError('whole native response derivation')
            write_input(literal,initial,TMP/'literal-input.bin')
            lr=run(TMP/'literal',(TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16))
            out=read_micro_output(TMP/'output.bin');lo=read_output(literal,initial,TMP/'literal-output.bin')
            for k in ('micro_steps','physical_steps','status'):
                if str(lr[k])!=str(built[k]):raise ValueError('literal/build '+k)
            if str(lr['micro_fnv64'])!=str(spec['selected']['micro_fnv64']) or sha(TMP/'output.bin')!=spec['output_sha256']:raise ValueError('searched computation binding')
            if any(lo[k]!=out[k] for k in ('heads','words')):raise ValueError('all literal bands')
            row=dict(name=name,case_id=spec['case_id'],role=spec['role'],request=request,
                request_sha256=spec['request_sha256'],sources=spec['sources'],initial=initial,
                input_sha256=sha(TMP/'input.bin'),expected=dict(status='accepted',
                    micro_steps=built['micro_steps'],physical_steps=built['physical_steps']),
                builder=built,checker=checked,literal=lr,output_sha256=sha(TMP/'output.bin'),
                output=out,header=header(TMP/'grammar.bin'),
                grammar=save('semantic-inventory-001-'+name+'.bin.gz',(TMP/'grammar.bin').read_bytes()),
                events=save('semantic-inventory-001-'+name+'-events.jsonl.gz',(TMP/'events.jsonl').read_bytes()),
                responses=save('semantic-inventory-001-'+name+'-responses.json.gz',(TMP/'root.json').read_bytes()))
            data['certificates'].append(row);(TMP/'progress.json').write_bytes(canonical(data))
            print(name,'fully native checked',built['nodes'],'nodes',flush=True)
    finally:oracle.close()
    if any(sha(HERE/n)!=p for n,p in pins.items()) or any(sha(HERE/n)!=p for n,p in rs.items()):raise ValueError('measured source changed')
    data['total_seconds']=time.perf_counter()-began
    save('semantic-inventory-001.json.gz',canonical(data))
    print('complete',round(data['total_seconds'],3),flush=True)

if __name__=='__main__':main()
