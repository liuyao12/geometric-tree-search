"""Execute the newly discovered conditional proof on the frozen literal core."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
import propositional_wang_compiler as C
from serialized_kernel import canonical
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-factored-wang-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,b):
    p=DOC/name;p.write_bytes(gzip.compress(b,mtime=0));return dict(name=name,sha256=digest(p),bytes=p.stat().st_size,uncompressed_bytes=len(b))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);data=json.loads((DOC/'factored-receptors-001.json').read_text());case=next(c for c in data['cases'] if c['id']=='double-negation-premise')
    spec=dict(proof=case['runs']['factored']['proof'],target=case['target'],hypotheses=case['hypotheses'],atoms=None,signature=None)
    compiled=C.compile_request(**spec);request=compiled['request']
    if request!=case['compiled']['request']:raise ValueError('actual discovered source')
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));shared=json.loads(gzip.decompress((DOC/'shared-wang-001.json.gz').read_bytes()))
    raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());inv=Inventory(raw)
    if hashlib.sha256(raw).hexdigest()!=PINNED_TABLE or hashlib.sha256(canonical(micro)).hexdigest()!=PINNED_MICRO:raise ValueError('fixed machine')
    sources={n:digest(HERE/n) for n in ('run_factored_wang.py','propositional_wang_compiler.py','micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp','proof_boundary.py','micro_cert.py','tape_binary.py','shared_wang_inventory.py')}
    for n,p in shared['sources'].items():
        if digest(HERE/n)!=p:raise ValueError('unchanged native source '+n)
    (TMP/'code.bin').write_bytes(code_bytes(micro));(TMP/'literal.bin').write_bytes(raw);write_cuts(cuts(micro),TMP/'cuts.bin')
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,0,1,2,3,7,9,8))
    for n,exe in (('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/n),'-o',str(TMP/exe)],check=True)
    fixed,free=boundary_words(request);old=json.loads((DOC/'proof-boundary-001.json').read_text());initial=copy.deepcopy(old['cases'][0]['initial'])
    for band,w in ((micro['boundary']['problem'],fixed),(micro['boundary']['certificate'],free)):initial['words'][band]=w+':';initial['capacities'][band]=len(w)+3
    (TMP/'input.bin').write_bytes(input_bytes(initial));print('new conditional proof starts',flush=True)
    built=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**10,6000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
    if built['status']!='accepted':raise ValueError(built)
    output=read_micro_output(TMP/'output.bin');events=[json.loads(s) for s in (TMP/'events.jsonl').read_text().splitlines()];write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin')
    checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'checked.bin',10**10,1500000000,TMP/'root.json',TMP/'observed.bin'))
    if checked['status']!='checked_response' or checked['result']!='accepted' or digest(TMP/'output.bin')!=digest(TMP/'checked.bin'):raise ValueError('response derivation')
    literal=dict(alphabet=shared['inventory']['alphabet'],space=inv.space);write_input(literal,initial,TMP/'literal-input.bin')
    actual=run(TMP/'literal',(TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16));lo=read_output(literal,initial,TMP/'literal-output.bin')
    for k in ('status','micro_steps','physical_steps'):
        if actual[k]!=built[k]:raise ValueError('literal execution '+k)
    if any(lo[k]!=output[k] for k in ('heads','words')):raise ValueError('all final register bands')
    row=dict(name='double-negation-premise',source=spec,compiler=compiled,request=request,initial=initial,expected={k:built[k] for k in ('status','micro_steps','physical_steps')},
        input_sha256=digest(TMP/'input.bin'),problem_pin=compiled['statement_pin'],output=output,output_sha256=digest(TMP/'output.bin'),builder=built,checker=checked,literal=actual,header=header(TMP/'grammar.bin'),
        grammar=save('factored-wang-001.bin.gz',(TMP/'grammar.bin').read_bytes()),events=save('factored-wang-events-001.jsonl.gz',(TMP/'events.jsonl').read_bytes()),responses=save('factored-wang-responses-001.json.gz',(TMP/'root.json').read_bytes()))
    out=dict(version='factored-wang-001',sources=sources,search_sha256=digest(DOC/'factored-receptors-001.json'),program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,inventory_fingerprint=inv.fingerprint,cases=[row],seconds=time.perf_counter()-began)
    if any(digest(HERE/n)!=p for n,p in sources.items()):raise ValueError('measured source changed')
    save('factored-wang-001.json.gz',canonical(out)+b'\n');print('native complete',out['seconds'],flush=True)
if __name__=='__main__':main()
