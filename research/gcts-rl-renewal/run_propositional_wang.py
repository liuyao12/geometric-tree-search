"""Compile discovered parametric proofs into one unchanged literal Wang core."""
import copy,gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
import propositional_receptors as R
import check_propositional_receptors as A
import propositional_wang_compiler as C
from serialized_kernel import canonical
from proof_boundary import boundary_words
from audit_proof_boundary import code_bytes,input_bytes,PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE
from micro_cert import cuts,write_cuts,run,header
from tape_binary import write_input,read_micro_output,read_output
from shared_wang_inventory import Inventory

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-propositional-wang-001')
SOURCES=('run_propositional_wang.py','propositional_wang_compiler.py','test_propositional_wang_compiler.py',
         'micro_line_builder.cpp','micro_line_check.cpp','tape_runner.cpp','proof_boundary.py','tape_binary.py','micro_cert.py','shared_wang_inventory.py')
ARTIFACTS=('propositional-receptors-001.json','propositional-receptors-audit-001.json','shared-wang-001.json.gz',
           'proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,raw):
    p=DOCS/name;p.write_bytes(gzip.compress(raw,mtime=0))
    return dict(name=name,sha256=digest(p),bytes=p.stat().st_size,uncompressed_bytes=len(raw))
def discover(base,library,target,length,weights=None):
    began=time.perf_counter();cat=R.catalog(dict(base,rules=list(base['rules'])),library);m=R.Model(cat,target,length);build=time.perf_counter()-began
    r=R.search(m,node_limit=6000,seconds=5,policy_weights=weights);r['build_seconds']=build
    if r['proof'] is None:raise ValueError('fresh receptor search did not find a proof')
    r['point_tiles']=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in r['placements']]
    r['independent']=A.certificate(cat,target,length,(),r['placements'],r['point_tiles'],library)
    return dict(target=target,length=length,result=r)
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);pins={n:digest(HERE/n) for n in SOURCES}
    artifacts={n:digest(DOCS/n) for n in ARTIFACTS};prior=json.loads((DOCS/ARTIFACTS[0]).read_text())
    audit=json.loads((DOCS/ARTIFACTS[1]).read_text())
    if audit['producer_sha256']!=artifacts[ARTIFACTS[0]]:raise ValueError('prior independent proof audit')
    shared=json.loads(gzip.decompress((DOCS/'shared-wang-001.json.gz').read_bytes()))
    for n,pin in shared['sources'].items():
        if digest(HERE/n)!=pin:raise ValueError('unchanged shared source '+n)
    for n,pin in prior['sources'].items():
        if digest(HERE/n)!=pin:raise ValueError('unchanged receptor source '+n)
    old=json.loads((DOCS/'proof-boundary-001.json').read_text());micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    if hashlib.sha256(canonical(micro)).hexdigest()!=PINNED_MICRO or old['program_sha256']!=PINNED_PROGRAM:raise ValueError('fixed machine')
    raw=gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes());inv=Inventory(raw)
    if hashlib.sha256(raw).hexdigest()!=PINNED_TABLE or inv.fingerprint!=shared['inventory']['fingerprint']:raise ValueError('fixed palette')
    (TMP/'literal.bin').write_bytes(raw);(TMP/'code.bin').write_bytes(code_bytes(micro));write_cuts(cuts(micro),TMP/'cuts.bin')
    bands=[micro['allocation'][66]['slots'][r] for r in (1,2,3,4,19,29,20)]
    if micro['entries'][66][36]!=1688 or bands!=[0,1,2,3,7,9,8]:raise ValueError('frozen observation site')
    (TMP/'focus.bin').write_bytes(struct.pack('<11I',0x474c4631,1688,micro['heap'],7,*bands))
    started=time.perf_counter()
    for source,name in (('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker'),('tape_runner.cpp','literal')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    data=dict(version='propositional-wang-001',sources=pins,reused_artifacts=artifacts,reused_source_pins=shared['sources']|prior['sources'],
        program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,literal_table_sha256=PINNED_TABLE,
        inventory_fingerprint=inv.fingerprint,inventory=shared['inventory'],compile_seconds=time.perf_counter()-started,
        cases=[],controls=[],searches={},limits=dict(steps=10**10,nodes=6000000,intervals=1500000000,literal_steps=10**16),
        scope='Generic family-to-boundary compiler, unchanged literal palette, concrete accepting rectangles and independently derivable per-line fragments. Semantic receptor search is separate; no literal-tile search or universal compiler proof is claimed.')
    prior=A.frozen(prior);family=prior['discovered_family'];library=(family,)
    target=R.imp(R.Q,R.imp(R.P,R.P))
    for lane,weights in (('point',None),('point-rl',prior['training']['weights'])):
        data['searches'][lane]=discover(prior['basis'],library,target,3,weights)
    data['searches']['template']=discover(prior['basis'],library,R.imp(R.P,R.P),1)
    template=data['searches']['template']['result']['proof']
    cases=[dict(name='fresh-hierarchy',source='fresh point-rl search',proof=data['searches']['point-rl']['result']['proof'],target=target,hypotheses=(),atoms=None,signature=None),
           dict(name='primitive-identity',source='reused Notebook 42 donor',proof=prior['donor']['proof'],target=R.imp(R.P,R.P),hypotheses=(),atoms=None,signature=None)]
    compound=next(c for c in prior['cases'] if c['id']=='family-composite')
    cases.append(dict(name='compound-family',source='reused Notebook 42 family-composite',proof=compound['runs']['point']['proof'],target=compound['target'],hypotheses=(),atoms=None,signature=None))
    for kind in ('arithmetic','geometry'):
        cases.append(dict(name=kind+'-syntax-family',source='fresh one-slot identity template, symbolic formula embedding',
            proof=template,target=R.imp(R.P,R.P),hypotheses=(),**C.embedding(kind)))
    literal=dict(alphabet=shared['inventory']['alphabet'],space=inv.space)
    def execute_case(spec,control=None):
        t=time.perf_counter();compiled=C.compile_request(spec['proof'],spec['target'],spec['hypotheses'],spec['atoms'],spec['signature'])
        compilation=time.perf_counter()-t;request=copy.deepcopy(compiled['request'])
        if control=='invalid-unused-definition':request['blocks'][0]['proof'][0]['formula']=['pred','P',[]]
        if control=='wrong-fixed-target':request['target']=['bot']
        fixed,free=boundary_words(request);initial=copy.deepcopy(old['cases'][0]['initial'])
        for band,w in ((micro['boundary']['problem'],fixed),(micro['boundary']['certificate'],free)):
            initial['words'][band]=w+':';initial['capacities'][band]=len(w)+3
        (TMP/'input.bin').write_bytes(input_bytes(initial))
        name=control or spec['name'];print(name,'observed computation starts',flush=True)
        built=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**10,6000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
        expected='rejected' if control else 'accepted'
        if built['status']!=expected:raise ValueError('operational result '+name+' '+str(built))
        output=read_micro_output(TMP/'output.bin');events=[json.loads(s) for s in (TMP/'events.jsonl').read_text().splitlines()]
        write_cuts([e['node'] for e in events if e['kind']=='fragment'],TMP/'observed.bin')
        checked=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'checked-output.bin',10**10,1500000000,TMP/'root.json',TMP/'observed.bin'))
        if checked['status']!='checked_response' or checked['result']!=expected or digest(TMP/'output.bin')!=digest(TMP/'checked-output.bin'):raise ValueError('whole response derivation '+name)
        write_input(literal,initial,TMP/'literal-input.bin')
        literal_result=run(TMP/'literal',(TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16))
        literal_output=read_output(literal,initial,TMP/'literal-output.bin')
        for k in ('micro_steps','physical_steps','status'):
            if literal_result[k]!=built[k]:raise ValueError('literal/builder '+name+' '+k)
        if any(literal_output[k]!=output[k] for k in ('heads','words')):raise ValueError('all literal bands '+name)
        row=dict(name=name,source=spec,compiler=compiled,compiler_seconds=compilation,request=request,
            expected=dict(status=expected,micro_steps=built['micro_steps'],physical_steps=built['physical_steps']),
            initial=initial,input_sha256=digest(TMP/'input.bin'),problem_pin=hashlib.sha256(canonical({k:request[k] for k in ('protocol','theory','target')})).hexdigest(),
            builder=built,checker=checked,literal=literal_result,output=output,output_sha256=digest(TMP/'output.bin'),
            literal_output_sha256=digest(TMP/'literal-output.bin'),header=header(TMP/'grammar.bin'),
            grammar=save('propositional-wang-001-'+name+'.bin.gz',(TMP/'grammar.bin').read_bytes()),
            events=save('propositional-wang-001-'+name+'-events.jsonl.gz',(TMP/'events.jsonl').read_bytes()),
            responses=save('propositional-wang-001-'+name+'-responses.json.gz',(TMP/'root.json').read_bytes()))
        print(name,'checked',built['nodes'],'nodes, literal height',built['physical_steps'],'seconds',round(built['wall_seconds']+checked['wall_seconds']+literal_result['wall_seconds'],3),flush=True)
        return row
    for spec in cases:
        data['cases'].append(execute_case(spec));(TMP/'progress.json').write_bytes(canonical(data)+b'\n')
    for control in ('invalid-unused-definition','wrong-fixed-target'):
        data['controls'].append(execute_case(cases[0],control));(TMP/'progress.json').write_bytes(canonical(data)+b'\n')
    if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured sources changed')
    data['total_seconds']=time.perf_counter()-began;save('propositional-wang-001.json.gz',canonical(data)+b'\n')
    print('complete',round(data['total_seconds'],3),flush=True)

if __name__=='__main__':main()
