"""Counterbalanced original/compacted validation of all actual searched proofs."""
import copy,hashlib,json,resource,time
from pathlib import Path
from proof_compaction import compact
from serialized_kernel import canonical,problem_hash
from tree_kernel import program,check as reference
import tree_native

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-compaction')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);old_path=DOCS/'learned-proof-blocks-001.json';old=json.loads(old_path.read_text());requests={r['problem']['id']:r['result']['request'] for r in old['discovery']}
    requests.update({r['problem']+'/'+r['lane']:r['result']['request'] for r in old['evaluation']['runs'] if r['result']['status']=='accepted_proposal'})
    data=dict(sources={n:digest(HERE/n) for n in ('proof_compaction.py','run_proof_compaction.py','tree_native.py','tree_runner.cpp','serialized_kernel.py','tree_kernel.py','fol_checker.tree')},
        reused_artifacts={'learned-proof-blocks-001.json':digest(old_path)},compile_seconds=tree_native.compile_tool(TMP),cases=[],reference_controls=[],
        program_sha256=old['tree_program_sha256'],method='exact same frozen theory, target, learned definitions and found search paths; only validated proof-data representation changes; counterbalanced original/compacted execution order',
        conformance='semantic certificate adaptation; all GCTS point graph, scheduling, generation, rollback, marking and RL semantics unchanged',
        scope='generic exact-formula reuse and dependency compaction after whole-input checking; no alpha-equivalence, new inference rule, learned abstraction or altered mathematical interface',
        limits=dict(steps=50000000,heap_nodes=2000000,host_work=2000000));code=program()
    for i,prior in enumerate(old['native_tree_replay']['cases']):
        name=prior['id'];request=requests[name];pin=problem_hash(request);c=compact(canonical(request),pin)
        if c['status']!='accepted_compaction':raise ValueError('compaction '+name+' '+c['status'])
        results={};order=('original','compact') if i%2==0 else ('compact','original')
        for lane in order:
            payload=canonical(request if lane=='original' else c['request']);r=tree_native.check(payload,code,TMP,pin,steps=50000000)
            if r['status']!='accepted':raise ValueError('native '+lane+' '+name)
            results[lane]=r
        for key in ('steps','event_sha256','profile','peak_frames','heap_nodes','value'): 
            if results['original'][key]!=prior['result'][key]:raise ValueError('original trace binding '+name+' '+key)
        row=dict(id=name,original_certificate_sha256=hashlib.sha256(canonical(request)).hexdigest(),problem_pin=pin,compaction=c,order=order,native=results)
        data['cases'].append(row);print(name,results['original']['steps'],results['compact']['steps'],flush=True)
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    for name in ('evaluation-0/blocks','bracketing-4'):
        row=next(r for r in data['cases'] if r['id']==name);payload=canonical(row['compaction']['request']);before=time.perf_counter()
        checked=reference(payload,code,expected_problem_sha256=row['problem_pin'],steps=50000000,keep_input=True)
        if checked['status']!='accepted':raise ValueError('complete Python reference')
        for k in ('steps','event_sha256','profile','peak_frames','heap_nodes','value'):
            if checked['result'][k]!=row['native']['compact'][k]:raise ValueError('compact reference '+k)
        data['reference_controls'].append(dict(id=name,check=checked,wall_seconds=time.perf_counter()-before));print('reference',name,checked['result']['steps'],flush=True)
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'proof-compaction-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
