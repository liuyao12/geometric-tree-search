"""Execute the new discharged certificate in the frozen common Wang core."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from serialized_kernel import canonical
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-context-wang-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,raw):
    p=DOC/name;p.write_bytes(gzip.compress(raw,mtime=0))
    return dict(name=name,sha256=digest(p),bytes=p.stat().st_size,uncompressed_bytes=len(raw))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True)
    names=('run_context_wang.py','micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp',
           'proof_boundary.py','tape_binary.py','micro_cert.py','shared_wang_inventory.py')
    pins={n:digest(HERE/n) for n in names}
    artifacts=('compact-contexts-001.json','compact-contexts-audit-001.json','shared-wang-001.json.gz',
        'proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')
    inputs={n:digest(DOC/n) for n in artifacts}
    source=json.loads((DOC/artifacts[0]).read_bytes());audit=json.loads((DOC/artifacts[1]).read_bytes())
    if audit['input_sha256']!=inputs[artifacts[0]]:raise ValueError('audited exact source')
    shared=json.loads(gzip.decompress((DOC/artifacts[2]).read_bytes()))
    for n,p in shared['sources'].items():
        if digest(HERE/n)!=p:raise ValueError('fixed source '+n)
    old=json.loads((DOC/artifacts[3]).read_bytes());micro=json.loads(gzip.decompress((DOC/artifacts[4]).read_bytes()))
    raw=gzip.decompress((DOC/artifacts[5]).read_bytes());inv=Inventory(raw)
    if hashlib.sha256(canonical(micro)).hexdigest()!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM or hashlib.sha256(raw).hexdigest()!=PINNED_TABLE:raise ValueError('fixed programs')
    if inv.fingerprint!=shared['inventory']['fingerprint']:raise ValueError('fixed palette')
    (TMP/'literal.bin').write_bytes(raw);(TMP/'code.bin').write_bytes(code_bytes(micro));write_cuts(cuts(micro),TMP/'cuts.bin')
    bands=[micro['allocation'][66]['slots'][r] for r in (1,2,3,4,19,29,20)]
    if micro['entries'][66][36]!=1688 or bands!=[0,1,2,3,7,9,8]:raise ValueError('frozen observation site')
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,*bands))
    t=time.perf_counter()
    for n,exe in (('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/n),'-o',str(TMP/exe)],check=True)
    data=dict(version='context-wang-001',sources=pins,reused_source_pins=shared['sources'],reused_artifacts=inputs,
        program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,
        inventory_fingerprint=inv.fingerprint,inventory=shared['inventory'],compile_seconds=time.perf_counter()-t,cases=[],
        limits=dict(micro_steps=10**10,nodes=6000000,intervals=1500000000,literal_steps=10**16),
        scope='Actual execution of one new fully discharged propositional certificate and one invalid helper in the unchanged common literal core. '
              'No new palette, literal tile search, universal compiler proof or arithmetic/geometry native execution in this experiment.')
    donor=next(c for c in source['cases'] if c['spec']['id']=='branch-donor')
    original=donor['result']['compact']['request'];literal=dict(alphabet=shared['inventory']['alphabet'],space=inv.space)
    for name in ('branched-theorem','invalid-projection'):
        request=copy.deepcopy(original)
        if name=='invalid-projection':request['proof'][0]['formula']=['imp',donor['result']['compact']['context'],['bot']]
        expected='accepted' if name=='branched-theorem' else 'rejected'
        fixed,free=boundary_words(request);initial=copy.deepcopy(old['cases'][0]['initial'])
        for band,word in ((micro['boundary']['problem'],fixed),(micro['boundary']['certificate'],free)):
            initial['words'][band]=word+':';initial['capacities'][band]=len(word)+3
        (TMP/'input.bin').write_bytes(input_bytes(initial));print(name,'native execution starts',flush=True)
        built=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**10,6000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
        if built['status']!=expected:raise ValueError(('native outcome',built))
        output=read_micro_output(TMP/'output.bin');events=[json.loads(s) for s in (TMP/'events.jsonl').read_text().splitlines()]
        write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin')
        checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'checked-output.bin',10**10,1500000000,TMP/'root.json',TMP/'observed.bin'))
        if checked['status']!='checked_response' or checked['result']!=expected or digest(TMP/'output.bin')!=digest(TMP/'checked-output.bin'):raise ValueError('whole native response')
        write_input(literal,initial,TMP/'literal-input.bin')
        lr=run(TMP/'literal',(TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16))
        lo=read_output(literal,initial,TMP/'literal-output.bin')
        if any(lr[k]!=built[k] for k in ('micro_steps','physical_steps','status')) or any(lo[k]!=output[k] for k in ('heads','words')):raise ValueError('literal execution comparison')
        row=dict(name=name,provenance=dict(artifact=artifacts[0],case='branch-donor'),request=request,initial=initial,
            expected=dict(status=expected,micro_steps=built['micro_steps'],physical_steps=built['physical_steps']),
            input_sha256=digest(TMP/'input.bin'),builder=built,checker=checked,literal=lr,output=output,
            output_sha256=digest(TMP/'output.bin'),literal_output_sha256=digest(TMP/'literal-output.bin'),header=header(TMP/'grammar.bin'),
            grammar=save('context-wang-001-'+name+'.bin.gz',(TMP/'grammar.bin').read_bytes()),
            events=save('context-wang-001-'+name+'-events.jsonl.gz',(TMP/'events.jsonl').read_bytes()),
            responses=save('context-wang-001-'+name+'-responses.json.gz',(TMP/'root.json').read_bytes()))
        data['cases'].append(row);(TMP/'progress.json').write_bytes(canonical(data)+b'\n')
        print(name,built['nodes'],'nodes,',built['physical_steps'],'literal height,',lr['wall_seconds'],'literal seconds',flush=True)
    if any(digest(HERE/n)!=p for n,p in pins.items()):raise ValueError('measured source changed')
    data['seconds']=time.perf_counter()-began;save('context-wang-001.json.gz',canonical(data)+b'\n');print('native complete',data['seconds'],flush=True)
if __name__=='__main__':main()
