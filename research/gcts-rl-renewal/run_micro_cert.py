"""Export accepting/rejecting whole-checker response certificates and costs."""
import gzip,json,resource,time
from pathlib import Path
from micro_cert import HERE,DOCS,digest,compile_tools,run,cuts,write_cuts,header
from tape_binary import write_micro,write_micro_input

TMP=Path('/private/tmp/gcts-micro-cert-official')
SOURCES=('micro_cert_builder.cpp','micro_response_check.cpp','micro_cert.py','run_micro_cert.py',
    'tape_binary.py','tape_tree_machine.py','computation_blocks.py')
def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True);compile_seconds=compile_tools(TMP)
    prior=json.loads((DOCS/'proof-boundary-001.json').read_text())
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    write_micro(micro,TMP/'code.bin');grouping=cuts(micro);write_cuts(grouping,TMP/'cuts.bin')
    data=dict(sources={n:digest(HERE/n) for n in SOURCES},reused_artifacts={n:digest(DOCS/n) for n in
        ('proof-boundary-001.json','proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')},
        program_sha256=prior['program_sha256'],micro_sha256=prior['machine']['micro_sha256'],literal_binary_sha256=prior['machine']['literal_binary_sha256'],
        compile_seconds=compile_seconds,grouping=dict(states=grouping,count=len(grouping),method='authored instruction, parser-token and heap-record boundaries; binary composition within and between groups; structural interning'),
        limits=dict(nodes=6000000,micro_steps=10**12,derived_intervals=1500000000),cases=[],controls=[],
        method='derive every DAG response from finite symbol actions, repeated copy moves, descending composition and unchanged frame; root expansion is not replayed',
        conformance='certificate verification adaptation; no tiling graph, scheduler, generation, markings, policy or RL changes',
        scope='full checker plus free-input constructor on finite authored cases; symbolic selected-tape certificate plus independently checked literal lowering law; dense Wang rectangle, formal logical soundness, compiler equivalence and useful learned search remain open')
    for name in ('addition-induction','reflexivity','captured-instantiation'):
        old=next(r for r in prior['cases'] if r['name']==name);stem='micro-response-'+name+'-001'
        write_micro_input(old['initial'],TMP/'input.bin');before=time.perf_counter()
        built=run(TMP/'builder',[TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'output.bin',10**12,6000000,TMP/'cuts.bin'])
        for key in ('status','micro_steps','physical_steps'):
            if built[key]!=old['selected'][key]:raise ValueError(name+' builder '+key)
        if digest(TMP/'output.bin')!=old['output_sha256']:raise ValueError('builder whole output')
        checked=run(TMP/'checker',[TMP/'code.bin',TMP/'input.bin',TMP/'grammar.bin',TMP/'derived.bin',10**12,1500000000,TMP/'root.json'])
        if checked['status']!='checked_response' or checked['result']!=built['status']:raise ValueError('response not certified')
        if digest(TMP/'derived.bin')!=old['output_sha256']:raise ValueError('derived whole output')
        artifact=DOCS/(stem+'.bin.gz');artifact.write_bytes(gzip.compress((TMP/'grammar.bin').read_bytes(),mtime=0));root=json.loads((TMP/'root.json').read_text())
        record=dict(name=name,problem_pin=old['problem_pin'],request=old['request'],initial=old['initial'],
            prior_selected=old['selected'],prior_literal=old['native'],builder=built,checker=checked,root=root,
            artifact=dict(name=artifact.name,sha256=digest(artifact),bytes=artifact.stat().st_size,uncompressed_bytes=(TMP/'grammar.bin').stat().st_size),
            grammar_header=header(TMP/'grammar.bin'),input_sha256=digest(TMP/'input.bin'),output_sha256=digest(TMP/'derived.bin'),
            seconds_including_compression=time.perf_counter()-before)
        data['cases'].append(record);print(name,built,checked,artifact.stat().st_size,flush=True)
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    # These controls limit proof construction/verification, not logical truth.
    small=next(r for r in data['cases'] if r['name']=='reflexivity');write_micro_input(small['initial'],TMP/'input.bin')
    for bound in (1,100):
        result=run(TMP/'builder',[TMP/'code.bin',TMP/'input.bin',TMP/'limited.bin',TMP/'limited-output.bin',10**12,bound,TMP/'cuts.bin'])
        if result['status']!='unknown_certificate_budget':raise ValueError('node resource not unknown')
        data['controls'].append(dict(name='node-limit-'+str(bound),result=result))
    raw=gzip.decompress((DOCS/small['artifact']['name']).read_bytes());(TMP/'small.bin').write_bytes(raw)
    for bound in (0,1000):
        result=run(TMP/'checker',[TMP/'code.bin',TMP/'input.bin',TMP/'small.bin',TMP/'limited-derived.bin',10**12,bound,TMP/'limited-root.json'])
        if result['status']!='unknown_certificate_budget':raise ValueError('interface resource not unknown')
        data['controls'].append(dict(name='interface-limit-'+str(bound),result=result))
    data.update(total_seconds=time.perf_counter()-start,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    history=Path('/private/tmp/gcts-r26-pilot-history.json')
    if history.exists():data['pilots']=json.loads(history.read_text())
    (DOCS/'micro-responses-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
