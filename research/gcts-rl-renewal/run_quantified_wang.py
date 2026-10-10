"""Execute four newly discovered quantified certificates on the fixed core."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from serialized_kernel import canonical
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-quantified-wang-001')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,b):
    p=DOC/name;p.write_bytes(gzip.compress(b,mtime=0));return dict(name=name,sha256=digest(p),bytes=p.stat().st_size,uncompressed_bytes=len(b))
def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True);search=json.loads((DOC/'quantified-receptors-001.json').read_bytes());micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));shared=json.loads(gzip.decompress((DOC/'shared-wang-001.json.gz').read_bytes()))
    raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());inv=Inventory(raw)
    if hashlib.sha256(raw).hexdigest()!=PINNED_TABLE or hashlib.sha256(canonical(micro)).hexdigest()!=PINNED_MICRO:raise ValueError('frozen core')
    sources={n:digest(HERE/n) for n in ('run_quantified_wang.py','quantified_receptors.py','micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp','proof_boundary.py','micro_cert.py','tape_binary.py','shared_wang_inventory.py')}
    for n,p in shared['sources'].items():
        if digest(HERE/n)!=p:raise ValueError('unchanged native source '+n)
    (TMP/'code.bin').write_bytes(code_bytes(micro));(TMP/'literal.bin').write_bytes(raw);write_cuts(cuts(micro),TMP/'cuts.bin');(TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,0,1,2,3,7,9,8))
    compilation=time.perf_counter()
    for n,exe in (('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):subprocess.run(['clang++','-O3','-std=c++17',str(HERE/n),'-o',str(TMP/exe)],check=True)
    compile_seconds=time.perf_counter()-compilation;rows=[]
    for name in ('arithmetic','hilbert-typing','ambient-y','arithmetic-learned-6'):
        before=time.perf_counter();case=next(c for c in search['cases'] if c['spec']['id']==name);source=case['runs']['gcts'];request=source['compiled']['request'];fixed,free=boundary_words(request)
        initial=copy.deepcopy(json.loads((DOC/'proof-boundary-001.json').read_bytes())['cases'][0]['initial'])
        for band,w in ((micro['boundary']['problem'],fixed),(micro['boundary']['certificate'],free)):initial['words'][band]=w+':';initial['capacities'][band]=len(w)+3
        folder=TMP/name;folder.mkdir(exist_ok=True);(folder/'input.bin').write_bytes(input_bytes(initial));print(name,'native start',flush=True)
        built=run(TMP/'builder',(TMP/'code.bin',folder/'input.bin',folder/'grammar.bin',folder/'output.bin',10**10,6000000,TMP/'cuts.bin',TMP/'focus.bin',folder/'events.jsonl'))
        if built['status']!='accepted':raise ValueError(built)
        output=read_micro_output(folder/'output.bin');events=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()];write_cuts([e['node'] for e in events if e['kind']=='fragment'],folder/'observed.bin')
        checked=run(TMP/'checker',(TMP/'code.bin',folder/'input.bin',folder/'grammar.bin',folder/'checked.bin',10**10,1500000000,folder/'root.json',folder/'observed.bin'))
        if checked['status']!='checked_response' or checked['result']!='accepted' or digest(folder/'output.bin')!=digest(folder/'checked.bin'):raise ValueError('complete derived response')
        literal=dict(alphabet=shared['inventory']['alphabet'],space=inv.space);write_input(literal,initial,folder/'literal-input.bin')
        actual=run(TMP/'literal',(TMP/'literal.bin',folder/'literal-input.bin',folder/'literal-output.bin',10**16));lo=read_output(literal,initial,folder/'literal-output.bin')
        for k in ('status','micro_steps','physical_steps'):
            if actual[k]!=built[k]:raise ValueError('actual literal count '+k)
        if any(lo[k]!=output[k] for k in ('heads','words')):raise ValueError('all final register bands')
        rows.append(dict(name=name,source=source['proof'],spec=case['spec'],compiler=source['compiled'],request=request,initial=initial,expected={k:built[k] for k in ('status','micro_steps','physical_steps')},input_sha256=digest(folder/'input.bin'),output=output,output_sha256=digest(folder/'output.bin'),builder=built,checker=checked,literal=actual,seconds=time.perf_counter()-before,header=header(folder/'grammar.bin'),
            grammar=save('quantified-wang-001-'+name+'.bin.gz',(folder/'grammar.bin').read_bytes()),events=save('quantified-wang-events-001-'+name+'.jsonl.gz',(folder/'events.jsonl').read_bytes()),responses=save('quantified-wang-responses-001-'+name+'.json.gz',(folder/'root.json').read_bytes())))
        print(name,'native accepted',rows[-1]['seconds'],flush=True)
    out=dict(version='quantified-wang-001',sources=sources,search_sha256=digest(DOC/'quantified-receptors-001.json'),program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,inventory_fingerprint=inv.fingerprint,cases=rows,compile_seconds=compile_seconds,seconds=time.perf_counter()-start)
    if any(digest(HERE/n)!=p for n,p in sources.items()):raise ValueError('measured sources changed')
    save('quantified-wang-001.json.gz',canonical(out)+b'\n');print('native complete',out['seconds'],flush=True)
if __name__=='__main__':main()
