"""Fresh Peano induction searches with full immutable compressed search traces.

Inputs are external statements, arithmetic axioms and finite bounds. There are
no imported proofs, policies or cluster libraries. Every lane rebuilds and
validates the same complete goal-derived grammar before its timed search.
"""
import gzip,hashlib,json,resource,time
from pathlib import Path
import induction_proof_catalogs as C
import induction_proof_problems as P
import induction_proof_tiles as T
import coarse_proof_tiles as M
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-induction-proofs-001')
LANES=('gcts','depth-marked','support-marked','csp')
SOURCES=('induction_proof_catalogs.py','induction_proof_problems.py',
 'induction_proof_tiles.py','run_induction_proofs.py','audit_induction_proofs.py',
 'test_induction_proofs.py','coarse_proof_tiles.py','audit_coarse_proofs.py',
 'audit_proof_policy.py','audit_proof_clusters.py','audit_semantic_proofs.py',
 'audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py',
 'proof_clusters.py','semantic_proof_tiles.py','semantic_proof_catalogs.py',
 'semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py',
 'turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py',
 'tree_machine.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def sha(blob):return hashlib.sha256(blob).hexdigest()

def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);folder=DOCS/'induction-proof-cases-001';folder.mkdir(exist_ok=True)
    pins={n:sha((HERE/n).read_bytes()) for n in SOURCES};code=program()
    data=dict(sources=pins,program_sha256=sha(canonical(code)),initial_library=[],policy=None,cases=[],
      configuration=dict(seconds=15,base_attempts=50000,native_steps=100000000,lanes=LANES),
      scope='Fresh bounded contextual-equation induction search. All quantified target variables are induction alternatives; every bounded term, axiom instance, rewrite occurrence/direction, fixed-hypothesis rewrite, closure and copy type is retained. Base/conditional step/induction are ordinary searched cells. No supplied proof sequence, chosen induction variable, imported proof, policy or cluster library. Compiled inference tiles expand to the checked primitive language. This is not unrestricted Peano proof search or a uniform finite four-edge Wang inventory.',
      comparison='Four lanes share the original theory, target, term grammar, original candidate universe and cell bound. Each search has a 15-second wall including representation/mark construction and trace instrumentation; catalog construction/validation and native checking are additionally included in cold request time. Point attempts are placements; CSP attempts are explicit assignments after arc consistency and do not have the same unit. The fixed CSP control uses MRV and binary support propagation. One run per case/lane, with rotated lane order; timings are exploratory, not a replicated speedup result. Resource markings are certified redundant constraints, not learned markings or RL. Full closed/open traces are stored losslessly in compressed per-case shards; no cropping or omitted failed prefixes.')
    data['compile_seconds']=tree_native.compile_tool(TMP)
    for i,p in enumerate(P.problems()):
        row=dict(problem=p,runs=[]);binding=None;shift=i%len(LANES)
        for lane in LANES[shift:]+LANES[:shift]:
            start=time.perf_counter();c=C.catalog(p['theory'],p['target'],p['term_bound'],p['enable_induction']);declared=declaration(c);pin=sha(canonical(declared))
            if binding is None:row.update(catalog=declared,catalog_sha256=pin);binding=pin
            if pin!=binding:raise ValueError('matched finite language changed between lanes')
            r=M.csp_search(c,p['length'],seconds=15,attempt_limit=50000) if lane=='csp' else T.search(c,p['length'],marked=lane=='depth-marked',support=lane=='support-marked',seconds=15,attempt_limit=50000)
            run=dict(lane=lane,catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r)
            if 'decoded' in r:
                expected=problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
                request=r['decoded']['request'];native=tree_native.check(canonical(request),code,TMP,expected,steps=100000000)
                if native['status']!='accepted':raise ValueError('complete native acceptance gate: '+str(native))
                run['native']=native
            run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run)
            print('search',p['id'],lane,r['status'],r['nodes'],r['base_attempts'],round(run['cold_seconds'],4),flush=True)
        payload=json.dumps(row,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n'
        blob=gzip.compress(payload,compresslevel=6,mtime=0);file='induction-proof-cases-001/'+p['id']+'.json.gz'
        if len(blob)>=90000000:raise ValueError('compressed publication shard too large')
        (DOCS/file).write_bytes(blob);descriptor=dict(problem=p,file=file,sha256=sha(blob),bytes=len(blob),raw_sha256=sha(payload),raw_bytes=len(payload));data['cases'].append(descriptor)
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
        print('shard',p['id'],len(payload),len(blob),flush=True)
    if any(sha((HERE/n).read_bytes())!=pin for n,pin in pins.items()):raise ValueError('measured source changed during experiment')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    target=DOCS/'induction-proofs-001.json';target.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('complete',round(data['total_seconds'],4),sum(x['bytes'] for x in data['cases']),flush=True)

if __name__=='__main__':main()
