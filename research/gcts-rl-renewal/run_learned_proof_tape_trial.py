"""A searched, reused mathematical lemma through the unchanged tape checker."""
import copy,gzip,json,resource,subprocess,time
from pathlib import Path
import proof_block_search as search
import proof_block_problems as problems
from proof_boundary import boundary_words
from serialized_kernel import problem_hash,canonical
from micro_cert import HERE,DOCS,digest,compile_tools,run,cuts,write_cuts,header
from tape_binary import write_micro,write_micro_input
from audit_proof_boundary import expected_constructor

TMP=Path('/private/tmp/gcts-learned-proof-tape')
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);prior=json.loads((DOCS/'proof-boundary-001.json').read_text())
    proposals=json.loads((DOCS/'learned-proof-blocks-001.json').read_text());library=[];before=time.perf_counter()
    for p in problems.discovery():
        r=search.prove(problems.theory(),p['target'],library,node_limit=1200,slack=3)
        if r['status']!='accepted_proposal':raise ValueError('cold discovery')
        search.promote(r,library)
    problem=problems.family(2702,18,True)[0];found=search.prove(problems.theory(),problem['target'],library,node_limit=1200,slack=3)
    old=next(r for r in proposals['evaluation']['runs'] if r['problem']=='evaluation-0' and r['lane']=='blocks')
    request=found['request']
    if canonical(request)!=canonical(old['result']['request']):raise ValueError('new cold search changed selected witness')
    search_seconds=time.perf_counter()-before
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    initial=copy.deepcopy(next(r for r in prior['cases'] if r['name']=='reflexivity')['initial']);fixed,free=boundary_words(request)
    for t,w in ((29,fixed),(30,free)):
        initial['words'][t]=w+':';initial['capacities'][t]=len(w)+3;initial['heads'][t]=1
    # Space is declared before execution, identically for replay/build/check.
    initial['capacities'][26]=len(initial['words'][26])+1+131072
    expected_constructor(micro,initial,request)
    compile_seconds=compile_tools(TMP);before=time.perf_counter()
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'selected')],check=True)
    selected_compile_seconds=time.perf_counter()-before;write_micro(micro,TMP/'code.bin');write_micro_input(initial,TMP/'input.bin');write_cuts(cuts(micro),TMP/'cuts.bin')
    sources=('run_learned_proof_tape.py','proof_block_search.py','proof_block_problems.py','proof_boundary.py','audit_tape_micro.cpp','micro_cert_builder.cpp','micro_response_check.cpp','micro_cert.py','tape_binary.py')
    data=dict(name='searched-left-zero-in-new-context',proposal_id='evaluation-0/blocks',request=request,problem_pin=problem_hash(request),
        initial=initial,search_seconds=search_seconds,compile_seconds=compile_seconds,selected_compile_seconds=selected_compile_seconds,
        sources={n:digest(HERE/n) for n in sources},program_sha256=prior['program_sha256'],micro_sha256=prior['machine']['micro_sha256'],literal_binary_sha256=prior['machine']['literal_binary_sha256'],
        reused_artifacts={n:digest(DOCS/n) for n in ('proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')},
        limits=dict(nodes=9000000,micro_steps=10**12,derived_intervals=2000000000),
        grouping='unchanged authored instruction/parser-token/heap-record cuts; learned mathematical block is proof data, not an automatically learned tape segmentation',
        scope='one actual learned closed induction lemma reused under a new universally quantified context; unchanged fixed tape grammar and Wang expansion law; no dense rectangle or Wang candidate search',
        conformance='proof-validation control; no new GCTS pruning, frontier bookkeeping, scheduler, generation, marking or rollback changes')
    selected=run(TMP/'selected',[TMP/'code.bin',TMP/'input.bin',TMP/'selected-output.bin',10**12]);data['selected']=selected
    print('selected',selected,flush=True)
    if selected['status']!='accepted':raise ValueError('searched proof tape cutoff/rejection')
    selected_sha=digest(TMP/'selected-output.bin')
    built=run(TMP/'builder',[TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'built-output.bin',10**12,9000000,TMP/'cuts.bin']);data['builder']=built
    print('built',built,flush=True)
    if built['status']!='accepted':raise ValueError('searched proof certificate cutoff/rejection')
    for k in ('micro_steps','physical_steps'): 
        if built[k]!=selected[k]:raise ValueError('builder count '+k)
    if digest(TMP/'built-output.bin')!=selected_sha:raise ValueError('whole builder output')
    checked=run(TMP/'checker',[TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'derived-output.bin',10**12,2000000000,TMP/'root.json']);data['checker']=checked
    print('checked',checked,flush=True)
    if checked['status']!='checked_response' or checked['result']!='accepted':raise ValueError('searched proof derived cutoff/rejection')
    if digest(TMP/'derived-output.bin')!=selected_sha:raise ValueError('whole derived output')
    artifact=DOCS/'learned-proof-response-001.bin.gz';before=time.perf_counter();artifact.write_bytes(gzip.compress((TMP/'grammar.bin').read_bytes(),mtime=0))
    data.update(compression_seconds=time.perf_counter()-before,root=json.loads((TMP/'root.json').read_text()),grammar_header=header(TMP/'grammar.bin'),
        artifact=dict(name=artifact.name,sha256=digest(artifact),bytes=artifact.stat().st_size,uncompressed_bytes=(TMP/'grammar.bin').stat().st_size),
        input_sha256=digest(TMP/'input.bin'),output_sha256=selected_sha,total_seconds=time.perf_counter()-began,
        peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'learned-proof-tape-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
