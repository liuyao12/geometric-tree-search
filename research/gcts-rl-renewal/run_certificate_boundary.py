"""Cold native certificate discovery, then checked literal accepting expansions.

No authored proof is passed to the search. Certificates are generated only
from the discovered commands, after every search observation has been saved.
"""
import copy,gzip,hashlib,json,struct,subprocess,sys,time
from pathlib import Path
from certificate_boundary_cases import cases
from certificate_boundary_search import canonical,digest,Oracle
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-certificate-boundary-20261010/formal')
SOURCES=('boundary_oracle.cpp','certificate_boundary_cases.py','certificate_boundary_search.py','certificate_boundary_worker.py','run_certificate_boundary.py')
REUSED=('proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz','shared-wang-reader-001.json')
REUSED_SOURCES=('proof_boundary.py','tape_binary.py','micro_cert.py','shared_wang_inventory.py','audit_proof_boundary.py','micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp','audit_logical_wang_clusters.py','audit_tape_micro.cpp','fol_checker.tree')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,raw):
    p=DOCS/name;p.write_bytes(gzip.compress(raw,mtime=0));return dict(name=name,sha256=sha(p),bytes=p.stat().st_size,uncompressed_bytes=len(raw))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True,parents=True);pins={n:sha(HERE/n) for n in SOURCES};reused={n:sha(DOCS/n) for n in REUSED};rs={n:sha(HERE/n) for n in REUSED_SOURCES}
    micro=json.loads(gzip.decompress((DOCS/REUSED[1]).read_bytes()));old=json.loads((DOCS/REUSED[0]).read_text());raw=gzip.decompress((DOCS/REUSED[2]).read_bytes());inv=Inventory(raw)
    if digest(micro)!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM or hashlib.sha256(raw).hexdigest()!=PINNED_TABLE:raise ValueError('pinned native palette')
    (TMP/'literal.bin').write_bytes(raw);(TMP/'code.bin').write_bytes(code_bytes(micro));write_cuts(cuts(micro),TMP/'cuts.bin');bands=[micro['allocation'][66]['slots'][r] for r in (1,2,3,4,19,29,20)]
    if micro['entries'][66][36]!=1688 or bands!=[0,1,2,3,7,9,8]:raise ValueError('frozen observation site')
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,*bands));compile_start=time.perf_counter()
    for source,name in (('boundary_oracle.cpp','oracle'),('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    data=dict(version='certificate-boundary-001',sources=pins,reused_inputs=reused,reused_sources=rs,program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,inventory=json.loads((DOCS/REUSED[3]).read_text())['inventory'],compile_seconds=time.perf_counter()-compile_start,limits=dict(queries=128,seconds=120,micro_steps=10**9),cases=cases(),observations=[],certificates=[],repetitions=2,scope='Chronological bounded certificate-word controls, not the reference primitive-square GCTS scheduler or new RL training. Prefix queries have their last formula as an intermediate target; final acceptance always binds the externally fixed assertion. Finite exact-length five-command grammar only.')
    winners={}
    for repetition in range(2):
        order=['prefix','flat'] if repetition==0 else ['flat','prefix']
        for spec in cases():
            for mode in order:
                label=f"{spec['id']}-{mode}-r{repetition+1}";directory=TMP/label;job=dict(case=spec,mode=mode,repetition=repetition+1,method_order=order,limits=data['limits'],directory=str(directory),executable=str(TMP/'oracle'));(TMP/'job.json').write_bytes(canonical(job));stage=time.perf_counter()
                subprocess.run([sys.executable,str(HERE/'certificate_boundary_worker.py'),str(TMP/'job.json'),str(TMP/'worker.json')],check=True)
                r=json.loads((TMP/'worker.json').read_text());artifact=save('certificate-boundary-001-'+label+'.json.gz',canonical(r));row=dict(case=spec['id'],mode=mode,repetition=repetition+1,status=r['status'],queries=r['queries'],nodes=r['nodes'],seconds=r['seconds'],cold_seconds=r['cold_seconds'],worker_stage_seconds=time.perf_counter()-stage,artifact=artifact,found=r['found']);data['observations'].append(row)
                if r['found']:
                    request=r['records'][r['found']['query']]['request'];key=digest(request);winners.setdefault(key,dict(request=request,selected=r['records'][r['found']['query']]['result'],output_sha256=r['records'][r['found']['query']]['output_sha256'],sources=[]))['sources'].append(label)
                (TMP/'progress.json').write_bytes(canonical(data));print(label,r['status'],r['queries'],round(r['cold_seconds'],3),flush=True)
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
            row=dict(name=name,request=request,request_sha256=key,sources=spec['sources'],initial=initial,input_sha256=sha(TMP/'input.bin'),expected=dict(status='accepted',micro_steps=built['micro_steps'],physical_steps=built['physical_steps']),builder=built,checker=checked,literal=lr,output_sha256=sha(TMP/'output.bin'),output=out,header=header(TMP/'grammar.bin'),grammar=save('certificate-boundary-001-'+name+'.bin.gz',(TMP/'grammar.bin').read_bytes()),events=save('certificate-boundary-001-'+name+'-events.jsonl.gz',(TMP/'events.jsonl').read_bytes()),responses=save('certificate-boundary-001-'+name+'-responses.json.gz',(TMP/'root.json').read_bytes()))
            data['certificates'].append(row);(TMP/'progress.json').write_bytes(canonical(data));print(name,'fully checked',built['nodes'],'nodes',flush=True)
    finally:oracle.close()
    if any(sha(HERE/n)!=p for n,p in pins.items()):raise ValueError('measured source changed')
    data['total_seconds']=time.perf_counter()-began;save('certificate-boundary-001.json.gz',canonical(data));print('complete',round(data['total_seconds'],3),flush=True)
if __name__=='__main__':main()
