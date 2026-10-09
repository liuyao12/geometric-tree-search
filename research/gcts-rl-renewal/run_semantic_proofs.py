"""Cold, witness-free direct GCTS proof-tile searches and a symbolic control."""
import hashlib,json,resource,time
from pathlib import Path
import semantic_proof_catalogs as C
import semantic_proof_problems as P
import semantic_proof_tiles as S
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-semantic-proofs')
SOURCE_NAMES=('semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','turtle.py','kernel_machine.py','logic.py','proof_block_search.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def declaration(c):return {k:v for k,v in c.items() if k not in ('build_seconds','validation_seconds','inventory_check')}
def build(p):return C.equational(p['theory'],p['target'],**p['configuration']) if p['kind']=='equational' else C.fol(p['theory'],p['target'],**p['configuration'])
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);code=program()
    data=dict(sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCE_NAMES},cases=[],
              configuration=dict(nodes=50000,seconds=5,native_steps=100000000),initial_library=[],policy=None,
              scope='Direct positional semantic point tiles with identity transforms. Formula IDs are exact scalar markings. Every finite slot/reference type is offered. No proof witness, theorem-specific skeleton, trained policy or stored lemma is input. Distant markings define the problem; no new learned redundant pruning. Not a uniform adjacency-only Wang inventory or a complete PA prover.',
              control='Chronological symbolic DFS of the same declared logical certificates, with a different scheduler and representation. Not an unmarked version of the point graph. Cold catalogs rebuilt separately; all compilation, search, decoding and checking costs recorded.')
    data['compile_seconds']=tree_native.compile_tool(TMP)
    for i,p in enumerate(P.statements()):
        row=dict(problem=p,runs=[],order=['gcts','symbolic'] if i%2==0 else ['symbolic','gcts']);catalog_sha=None
        for lane in row['order']:
            start=time.perf_counter();c=build(p);decl=declaration(c);h=hashlib.sha256(canonical(decl)).hexdigest()
            if catalog_sha is not None and h!=catalog_sha:raise ValueError('lane catalog mismatch')
            if catalog_sha is None:row.update(catalog=decl,catalog_sha256=h);catalog_sha=h
            result=(S.search if lane=='gcts' else S.symbolic_search)(c,p['length'],node_limit=50000,seconds=5)
            run=dict(lane=lane,result=result,catalog_sha256=h,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c.get('validation_seconds',0),catalog_inventory_check=c.get('inventory_check'))
            if 'decoded' in result:
                request=result['decoded']['request'];run['native']=tree_native.check(canonical(request),code,TMP,problem_hash(request),steps=100000000)
            run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run)
            print(p['id'],lane,result['status'],result['nodes'],round(run['cold_seconds'],6),run.get('native',{}).get('status'),flush=True)
        data['cases'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=hashlib.sha256(canonical(code)).hexdigest())
    (DOCS/'semantic-proofs-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
