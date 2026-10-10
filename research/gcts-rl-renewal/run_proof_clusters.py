"""Fresh GCTS fragment mining, a checked hierarchy, and matched base searches."""
import hashlib,json,resource,time
from pathlib import Path
import proof_clusters as H
import proof_cluster_problems as P
import semantic_proof_catalogs as C
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-clusters')
SOURCES=('proof_clusters.py','proof_cluster_problems.py','run_proof_clusters.py','semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py','turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);code=program();library=[];data=dict(sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},initial_library=[],donors=[],evaluation=[],
        configuration=dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000,min_fragment_moves=2,max_fragment_moves=4,replicas=2,native_steps=100000000),
        scope='Fresh direct GCTS discoveries in two authored parameterized donor statements; every eligible dependency-chain window is checked and promoted. No imported proof, cluster or policy. Evaluation never enters mining. A second-level template can call an actually used earlier template. Specialized contextual arithmetic, not induction/general FOL or learned pruning.',
        comparison='All four lanes rebuild the identical complete base catalog, target, cell bound, root generations and scheduler. Base: no library. Level1: level-one sequence proposals. Hierarchy: all checked sequence proposals. Rank-only: same full hierarchy, but only next-singleton ranking. Proposals never supply frontier degrees. Every base alternative remains; total cold, learning, indexing, expansion and native costs are reported.')
    data['compile_seconds']=tree_native.compile_tool(TMP)
    for p in P.donors():
        start=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);input_library=[t['name'] for t in library];r=H.search(c,p['length'],library,seconds=5);row=dict(problem=p,catalog=declaration(c),catalog_build_seconds=c['build_seconds'],input_library=input_library,result=r)
        if 'decoded' in r:
            hierarchy=H.hierarchical_certificate(c,r,p['length'],library);row['hierarchy']=hierarchy;row['native']=tree_native.check(canonical(hierarchy['request']),code,TMP,problem_hash(r['decoded']['request']),steps=100000000)
            if row['native']['status']=='accepted':
                promotion=H.promote(c,r,p['length'],library,p['id']);row['promotion']=promotion;library+=promotion['templates'];row['library_check']=H.validate_library(p['theory'],library)
        row['cold_seconds']=time.perf_counter()-start;data['donors'].append(row);print('donor',p['id'],r['status'],len(library),row.get('native',{}).get('status'),flush=True)
    data['library']=library;probe=dict(protocol='gcts-fol-1',theory=P.donors()[0]['theory'],target=['imp',['bot'],['bot']],blocks=H.definitions(library),proof=[dict(rule='tautology',formula=['imp',['bot'],['bot']])]);data['whole_library_native']=dict(request=probe,result=tree_native.check(canonical(probe),code,TMP,problem_hash(probe),steps=100000000))
    for i,p in enumerate(P.evaluation()):
        row=dict(problem=p,runs=[]);expected=None
        for replica in range(2):
            lanes=['base','level1','hierarchy','rank-only'];shift=(i+replica)%4;lanes=lanes[shift:]+lanes[:shift]
            for lane in lanes:
                selected=[] if lane=='base' else [t for t in library if t['level']==1] if lane=='level1' else library
                start=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);h=H.digest(declaration(c))
                if expected is None:row.update(catalog=declaration(c),catalog_sha256=h);expected=h
                if h!=expected:raise ValueError('matched base catalog changed')
                r=H.search(c,p['length'],selected,seconds=5,attempt_limit=50000,mode='rank' if lane=='rank-only' else 'clusters');run=dict(lane=lane,replica=replica,result=r,catalog_sha256=h,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],library=[t['name'] for t in selected])
                if 'decoded' in r:
                    hierarchy=H.hierarchical_certificate(c,r,p['length'],selected);run['hierarchy']=hierarchy;run['native']=tree_native.check(canonical(hierarchy['request']),code,TMP,problem_hash(r['decoded']['request']),steps=100000000)
                run['cold_seconds']=time.perf_counter()-start;row['runs'].append(run);print(p['id'],replica,lane,r['status'],r['nodes'],r['base_attempts'],round(run['cold_seconds'],6),run.get('native',{}).get('status'),flush=True)
        data['evaluation'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=H.digest(code))
    (DOCS/'proof-clusters-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
