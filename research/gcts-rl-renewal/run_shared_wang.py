"""Fresh bounded proof discovery followed by one frozen literal checker.

No previous proof, library, policy or benchmark result enters either search.
The earlier boundary artifact supplies only the reviewed fixed program and
bootstrap frame. Only encoded theory, target and proposed proof data change.
"""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
import logic as L,semantic_proof_catalogs as C,semantic_proof_tiles as S
import hilbert_incidence_tiles as H
from semantic_proof_problems import addition
from serialized_kernel import canonical,problem_hash
from proof_boundary import boundary_words
from tape_binary import write_input,write_micro,write_micro_input,read_micro_output,read_output
from shared_wang_inventory import Inventory,patch,TABLE_PIN
from run_hilbert_quantified import SOURCES as BASE

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-shared-wang-001')
SOURCES=tuple(dict.fromkeys(BASE+('shared_wang_inventory.py','run_shared_wang.py','proof_boundary.py',
    'boundary_syntax.tree','tape_tree_machine.py','tape_binary.py','tape_runner.cpp','audit_boundary_micro.cpp')))
ARTIFACTS=('proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')
def sha(x):return hashlib.sha256(x).hexdigest()
def digest(path):return sha(Path(path).read_bytes())
def execute(name,*args):
    before=time.perf_counter();r=json.loads(subprocess.check_output([str(TMP/name),*map(str,args)]))
    r['wall_seconds']=time.perf_counter()-before;return r
def statements():
    a=L.V('a');z=L.F('zero');s=lambda x:L.F('succ',x);add=lambda x,y:L.F('add',x,y)
    arithmetic=dict(id='addition-by-one',label='Adding one gives the successor',theory=addition(),
        target=L.All('a',L.Eq(add(a,s(z)),s(a))),length=3,term_bound=5)
    h=H.pred('Inc','a','u');g=H.pred('Point','a')
    geometry=dict(name='incidence-point',hypothesis=h,goal=g,target=H.close(['a','u'],L.Imp(h,g)),
        variables=['a','u'],sorts=dict(point=['a','b','c'],line=['u','v']),source=H.SOURCE)
    return arithmetic,geometry
def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True)
    pins={n:digest(HERE/n) for n in SOURCES};oldpins={n:digest(DOCS/n) for n in ARTIFACTS}
    old=json.loads((DOCS/ARTIFACTS[0]).read_text())
    micro=json.loads(gzip.decompress((DOCS/ARTIFACTS[1]).read_bytes()))
    raw=gzip.decompress((DOCS/ARTIFACTS[2]).read_bytes());inventory=Inventory(raw)
    (TMP/'literal.bin').write_bytes(raw);write_micro(micro,TMP/'micro.bin')
    labels=['L',*list('B^01:,;'),'#',*['@'+s for s in list('B^01:,;')+['#']],*['S'+str(i) for i in range(micro['tapes'])]]
    literal=dict(alphabet=labels,space=inventory.space)
    template=copy.deepcopy(old['cases'][0]['initial']);boundary=micro['boundary']
    before=time.perf_counter()
    for source,name in (('tape_runner.cpp','literal'),('audit_boundary_micro.cpp','selected')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    compile_seconds=time.perf_counter()-before
    d=dict(version='shared-wang-001',sources=pins,reused_artifacts=oldpins,program_sha256=old['program_sha256'],
        literal_table_sha256=TABLE_PIN,micro_sha256=old['machine']['micro_sha256'],
        inventory=dict(fingerprint=inventory.fingerprint,alphabet=labels,states=inventory.Q,symbols=inventory.A,
            configuration_symbols=inventory.D,defined_transitions=inventory.defined,families=inventory.counts,
            tile_types=sum(inventory.counts.values()),start=inventory.start,accept=inventory.accept,
            representation='four disjoint finite triple families: no head, center head, left head, right head; fixed table lookup only'),
        boundary=dict(problem_band=boundary['problem'],certificate_band=boundary['certificate'],
            payload_alphabet=['0','1',';','B'],frame=':',template_sha256=sha(canonical(template))),
        cases=[],controls=[],compile_seconds=compile_seconds,
        limits=dict(search_seconds=10,search_nodes=50000,micro_steps=10000000000,literal_steps=10**16),
        conformance='Existing complete finite point GCTS engine is unchanged. Fresh search uses query-grounded readable macros; the fixed Wang palette is verified as an operational checker. No literal-Wang candidate search, policy, pruning or scheduler shortcut is introduced.',
        scope='One fixed finite computational palette, two fresh discovered certificates, exact local tiles and full literal/independent-selected execution agreement. This is the shared-checking gate; fixed-inventory proof search, a practical logical macro compiler, formal upstream soundness and net RL advantage remain open.')
    arithmetic,geometry=statements()
    for kind,p in (('arithmetic',arithmetic),('geometry',geometry)):
        began=time.perf_counter()
        c=C.equational(p['theory'],p['target'],p['term_bound']) if kind=='arithmetic' else H.catalog(p)
        n=p['length'] if kind=='arithmetic' else 2
        r=S.search(c,n,seconds=10,node_limit=50000)
        if r['status']!='finite_exact_proof_tiling':raise ValueError('fresh search '+kind+' '+r['status'])
        request=json.loads(canonical(r['decoded']['request']))
        row=dict(kind=kind,problem=p,length=n,catalog=c,result=r,problem_pin=problem_hash(request),
            search_cold_seconds=time.perf_counter()-began,request=request,inventory_fingerprint=inventory.fingerprint)
        print(kind,'fresh search',r['nodes'],r['attempts'],flush=True)
        fixed,free=boundary_words(request);initial=copy.deepcopy(template)
        for t,w in ((boundary['problem'],fixed),(boundary['certificate'],free)):
            initial['words'][t]=w+':';initial['capacities'][t]=len(w)+3
        row.update(initial=initial,fixed_word=fixed,free_word=free,fixed_sha256=sha(fixed.encode('ascii')),
            proof_payload_sha256=sha(free.encode('ascii')))
        write_micro_input(initial,TMP/'micro-input.bin');write_input(literal,initial,TMP/'literal-input.bin')
        print(kind,'selected checker begins',flush=True)
        selected=execute('selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**10,len(micro['rows']))
        row['selected']=selected
        if selected['status']!='accepted':raise ValueError('selected checker '+kind+' '+str(selected))
        output=read_micro_output(TMP/'micro-output.bin');row['selected_output_sha256']=digest(TMP/'micro-output.bin')
        print(kind,'literal checker begins',selected['micro_steps'],flush=True)
        native=execute('literal',TMP/'literal.bin',TMP/'literal-input.bin',TMP/'literal-output.bin',10**16)
        for key in ('status','micro_steps','physical_steps','micro_fnv64'):
            if native[key]!=selected[key]:raise ValueError('literal/selected '+key)
        other=read_output(literal,initial,TMP/'literal-output.bin')
        if any(other[k]!=output[k] for k in ('heads','words')):raise ValueError('complete physical tape disagreement')
        row.update(literal=native,output=output,literal_output_sha256=digest(TMP/'literal-output.bin'))
        row['patch']=patch(inventory,initial,labels,boundary['problem'])
        d['cases'].append(row)
        print(kind,'same table accepted',selected['micro_steps'],native['physical_steps'],round(native['wall_seconds'],3),flush=True)
        # Wrong externally fixed conclusion, keeping the discovered proof.
        bad=copy.deepcopy(request);bad['target']=['bot'];bad_fixed,_=boundary_words(bad)
        bad_initial=copy.deepcopy(initial);t=boundary['problem'];bad_initial['words'][t]=bad_fixed+':';bad_initial['capacities'][t]=len(bad_fixed)+3
        write_micro_input(bad_initial,TMP/'control-input.bin')
        control=execute('selected',TMP/'micro.bin',TMP/'control-input.bin',TMP/'control-output.bin',10**10,len(micro['rows']))
        if control['status']!='rejected':raise ValueError('wrong target '+str(control))
        d['controls'].append(dict(name=kind+'-wrong-target',initial=bad_initial,result=control,output_sha256=digest(TMP/'control-output.bin')))
        (TMP/'progress.json').write_bytes(canonical(d)+b'\n')
    write_micro_input(d['cases'][0]['initial'],TMP/'control-input.bin')
    result=execute('selected',TMP/'micro.bin',TMP/'control-input.bin',TMP/'control-output.bin',0,len(micro['rows']))
    if result['status']!='unknown_step_budget':raise ValueError('resource status')
    d['controls'].append(dict(name='zero-step-budget',initial=d['cases'][0]['initial'],result=result,limit=0,output_sha256=digest(TMP/'control-output.bin')))
    if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    d['total_seconds']=time.perf_counter()-start
    payload=canonical(d)+b'\n';file=DOCS/'shared-wang-001.json.gz';file.write_bytes(gzip.compress(payload,mtime=0))
    (TMP/'result.json').write_text(json.dumps(dict(file=file.name,sha256=digest(file),bytes=file.stat().st_size,total_seconds=d['total_seconds'])))
    print('complete',d['total_seconds'],file.stat().st_size,flush=True)
if __name__=='__main__':main()
