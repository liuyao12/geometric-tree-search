"""Observe actual per-line fragments of the unchanged shared checker.

All certificates here are explicitly reused controls, not new proof discoveries.
Observation metadata changes compression boundaries, never machine execution.
"""
import gzip, hashlib, json, struct, subprocess, time
from pathlib import Path
from audit_proof_boundary import code_bytes, input_bytes, PINNED_PROGRAM, PINNED_MICRO, PINNED_TABLE
from micro_cert import cuts, write_cuts, run, header

HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-logical-wang-clusters-001')
SOURCES=('run_logical_wang_clusters.py','micro_line_builder.cpp','micro_line_check.cpp')
ARTIFACTS=('shared-wang-001.json.gz','shared-wang-audit-001.json','proof-boundary-001.json',
           'proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')
FIELDS=('target','assumptions','registry','theory','forbidden','proved','pending')
REGISTERS=(1,2,3,4,19,29,20)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def save_gzip(path,raw):
    path.write_bytes(gzip.compress(raw,mtime=0))
    return dict(name=path.name,sha256=digest(path),bytes=path.stat().st_size,uncompressed_bytes=len(raw))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True)
    pins={n:digest(HERE/n) for n in SOURCES};priorpins={n:digest(DOCS/n) for n in ARTIFACTS}
    shared=json.loads(gzip.decompress((DOCS/ARTIFACTS[0]).read_bytes()))
    old=json.loads((DOCS/'proof-boundary-001.json').read_text())
    for n,pin in shared['sources'].items():
        if digest(HERE/n)!=pin:raise ValueError('frozen source '+n)
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    if hashlib.sha256(packed(micro)).hexdigest()!=PINNED_MICRO:raise ValueError('micro pin')
    if old['program_sha256']!=PINNED_PROGRAM or old['machine']['literal_binary_sha256']!=PINNED_TABLE:raise ValueError('machine pins')
    focus=micro['entries'][66][36];bands=[micro['allocation'][66]['slots'][r] for r in REGISTERS]
    if focus!=1688 or bands!=[0,1,2,3,7,9,8]:raise ValueError('reviewed observation site')
    (TMP/'code.bin').write_bytes(code_bytes(micro));write_cuts(cuts(micro),TMP/'cuts.bin')
    (TMP/'focus.bin').write_bytes(struct.pack('<'+'I'*(4+len(bands)),0x474c4631,focus,micro['heap'],len(bands),*bands))
    compile_start=time.perf_counter()
    for source,name in (('micro_line_builder.cpp','builder'),('micro_line_check.cpp','checker')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    data=dict(version='logical-wang-clusters-001',sources=pins,reused_artifacts=priorpins,
        reused_source_pins=shared['sources'],program_sha256=PINNED_PROGRAM,micro_sha256=PINNED_MICRO,
        literal_table_sha256=PINNED_TABLE,inventory_fingerprint=shared['inventory']['fingerprint'],
        observation=dict(function=66,pc=36,state=focus,heap=micro['heap'],registers=list(REGISTERS),bands=bands,fields=list(FIELDS)),
        compile_seconds=time.perf_counter()-compile_start,cases=[],limits=dict(steps=10**10,nodes=6000000,intervals=1500000000),
        conformance='Generic operational cluster extraction, not a GCTS search engine or learned marking. Literal tiles and point-value contract remain unchanged. No new candidate pruning, scheduler or RL policy.',
        scope='Reused discovered arithmetic and Hilbert certificates plus authored rule/scope controls; actual ground per-line response clusters. A parametric logical compiler, direct fixed-inventory search, and net RL advantage remain open.')
    cases=[]
    for row in shared['cases']:
        cases.append((row['kind'],row,'shared-wang-001.json.gz','kind',row['kind'],row['selected_output_sha256']))
    for name in ('universal-distribution','addition-induction','generalization-of-open-premise','captured-instantiation'):
        row=next(r for r in old['cases'] if r['name']==name)
        cases.append((name,row,'proof-boundary-001.json','name',name,row['output_sha256']))
    for name,oldrow,artifact,key,value,output_pin in cases:
        initial=oldrow['initial'];(TMP/'input.bin').write_bytes(input_bytes(initial))
        print(name,'observed build starts',flush=True)
        builder=run(TMP/'builder',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**10,6000000,TMP/'cuts.bin',TMP/'focus.bin',TMP/'events.jsonl'))
        row=dict(name=name,provenance=dict(artifact=artifact,key=key,value=value,kind='reused certificate'),
            request=oldrow['request'],initial=initial,problem_pin=oldrow['problem_pin'],expected=oldrow['selected'],
            output_sha256=output_pin,input_sha256=digest(TMP/'input.bin'),builder=builder)
        if builder['status'].startswith('unknown'):
            row['status']=builder['status'];data['cases'].append(row)
            print(name,builder['status'],flush=True);continue
        if builder['status']!=oldrow['selected']['status'] or digest(TMP/'output.bin')!=output_pin:raise ValueError('whole symbol output '+name)
        for k in ('micro_steps','physical_steps'):
            if builder[k]!=oldrow['selected'][k]:raise ValueError('unchanged execution '+name+' '+k)
        events=[json.loads(line) for line in (TMP/'events.jsonl').read_text().splitlines()]
        ids=[e['node'] for e in events if e['kind']=='fragment']
        write_cuts(ids,TMP/'observed.bin')
        print(name,'derive all',builder['nodes'],'nodes,',builder['focus_events'],'receptors',flush=True)
        checker=run(TMP/'checker',(TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'checked-output.bin',10**10,1500000000,TMP/'root.json',TMP/'observed.bin'))
        if checker['status']!='checked_response' or digest(TMP/'checked-output.bin')!=output_pin:raise ValueError('whole response '+name)
        row.update(status='checked_response',checker=checker,header=header(TMP/'grammar.bin'),
            grammar=save_gzip(DOCS/('logical-cluster-001-'+name+'.bin.gz'),(TMP/'grammar.bin').read_bytes()),
            events=save_gzip(DOCS/('logical-cluster-001-'+name+'-events.jsonl.gz'),(TMP/'events.jsonl').read_bytes()),
            responses=save_gzip(DOCS/('logical-cluster-001-'+name+'-responses.json.gz'),(TMP/'root.json').read_bytes()))
        data['cases'].append(row)
        (TMP/'progress.json').write_bytes(packed(data)+b'\n')
        print(name,'checked',round(builder['wall_seconds']+checker['wall_seconds'],3),'seconds',flush=True)
    if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    data['total_seconds']=time.perf_counter()-began
    save_gzip(DOCS/'logical-wang-clusters-001.json.gz',packed(data)+b'\n')
    print('complete',round(data['total_seconds'],3),flush=True)
if __name__=='__main__':main()
