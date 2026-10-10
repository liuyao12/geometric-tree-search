"""Fresh hierarchy mining, complete metatiles, capacity contraction and CSP control."""
import hashlib,json,resource,time
from pathlib import Path
import coarse_proof_tiles as M,proof_clusters as H,proof_cluster_problems as P
import semantic_proof_catalogs as C
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-coarse-proofs')
SOURCES=('coarse_proof_tiles.py','run_coarse_proofs.py','audit_coarse_proofs.py','audit_proof_policy.py','audit_proof_clusters.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py','proof_clusters.py','proof_cluster_problems.py','semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py','turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def complete(c,p,r,library,code):
    if 'decoded' not in r:return {}
    h=H.hierarchical_certificate(c,r,p['length'],library);return dict(hierarchy=h,native=tree_native.check(canonical(h['request']),code,TMP,problem_hash(r['decoded']['request']),steps=100000000))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);code=program();library=[];data=dict(sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},initial_library=[],donors=[],evaluation=[],
        configuration=dict(seconds=5,base_attempts=50000,index_instances=1000000,replicas=2,native_steps=100000000,lanes=M.LANES),
        scope='Fresh searches of two nominated donor statements, followed by checked fragment mining. Complete finite metatile inventory; all primitive types retained. Coarse capacity plus unique owner markings is solution-equivalent to the original finite envelope. No imported proofs, fragments or policy. Identity transforms, bounded contextual equations; not induction/general PA or a uniform adjacency-only Wang system.',
        comparison='Six operational controls share the original theory, target, grammar and cell count. Each has a five-second search wall including representation construction and trace instrumentation. Trial caps both have value 50000, but point trials charge expanded primitive placement attempts whereas classical trials count explicit variable assignments after propagation; units differ. CSP support tests and removed values are counted and timed separately. Point contraction changes graph degrees and scheduling; authored goal/length/level macro ordering is fixed. CSP uses classical binary arc consistency and MRV. Cold requests include catalog validation, search, expansion, hierarchical compilation and native checking. Reuse lanes also owe fresh library discovery. No new RL or learned failure markings.')
    data['compile_seconds']=tree_native.compile_tool(TMP);start=time.perf_counter()
    for p in P.donors():
        t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],library);row=dict(problem=p,catalog=declaration(c),input_library=[x['name'] for x in library],result=r,catalog_build_seconds=c['build_seconds'],**complete(c,p,r,library,code))
        if row.get('native',{}).get('status')!='accepted':raise ValueError('fresh donor native gate')
        row['promotion']=H.promote(c,r,p['length'],library,p['id']);library+=row['promotion']['templates'];row['library_check']=H.validate_library(p['theory'],library);row['cold_seconds']=time.perf_counter()-t;data['donors'].append(row);print('donor',p['id'],len(library),flush=True)
    probe=dict(protocol='gcts-fol-1',theory=P.donors()[0]['theory'],target=['imp',['bot'],['bot']],blocks=H.definitions(library),proof=[dict(rule='tautology',formula=['imp',['bot'],['bot']])]);data['whole_library_native']=dict(request=probe,result=tree_native.check(canonical(probe),code,TMP,problem_hash(probe),steps=100000000));data['library_seconds']=time.perf_counter()-start;data['library']=library
    if data['whole_library_native']['result']['status']!='accepted':raise ValueError('whole library native gate')
    for i,p in enumerate(P.evaluation()):
        row=dict(problem=p,runs=[]);expected=None
        for replica in range(2):
            shift=(i+replica)%len(M.LANES)
            for lane in M.LANES[shift:]+M.LANES[:shift]:
                selected=library if lane in ('fine-meta','coarse2-meta','coarse3-meta') else ();t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);binding=H.digest(declaration(c))
                if expected is None:row.update(catalog=declaration(c),catalog_sha256=binding);expected=binding
                if binding!=expected:raise ValueError('matched original finite catalog changed')
                r=M.csp_search(c,p['length']) if lane=='csp' else M.search(c,p['length'],3 if lane=='coarse3-meta' else 2 if lane.startswith('coarse2') else 1,selected)
                run=dict(lane=lane,replica=replica,library=[x['name'] for x in selected],catalog_sha256=binding,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r,**complete(c,p,r,selected,code));run['cold_seconds']=time.perf_counter()-t;row['runs'].append(run);print('eval',p['id'],replica,lane,r['status'],r['base_attempts'],round(run['cold_seconds'],4),flush=True)
        data['evaluation'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=H.digest(code));target=DOCS/'coarse-proofs-001.json';target.write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',round(data['total_seconds'],4),target.stat().st_size,flush=True)
if __name__=='__main__':main()
