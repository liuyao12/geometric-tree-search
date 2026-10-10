"""Post-search symbol invariance control; no new theorem discovery is claimed."""
import hashlib,json,time
from pathlib import Path
import copy
from serialized_kernel import canonical,problem_hash,check
from audit_serialized_kernel import replay
from audit_proof_compaction import native_binding
from tree_kernel import program
import tree_native
import induction_proof_tiles as T
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-symbol-renaming-001')
NAMES=dict(Triangle='TableRelation',SegEq='ChairRelation',AngleEq='CupRelation',Congruent='FurnitureRelation')
def rename(a,axioms):
    if isinstance(a,(tuple,list)):
        if len(a)==3 and a[0]=='pred':return ('pred',NAMES.get(a[1],a[1]),tuple(rename(x,axioms) for x in a[2]))
        return tuple(rename(x,axioms) for x in a)
    if isinstance(a,dict):
        out={k:rename(v,axioms) for k,v in a.items()}
        if 'predicates' in a:out['predicates']={NAMES.get(k,k):v for k,v in a['predicates'].items()}
        if 'axioms' in a:out['axioms']={axioms[k]:rename(v,axioms) for k,v in a['axioms'].items()}
        if a.get('rule')=='axiom':out['name']=axioms[a['name']]
        if 'axiom' in a:out['axiom']=axioms[a['axiom']]
        return out
    return a
def main():
    started=time.perf_counter();raw=(DOCS/'euclidean-proofs-001.json').read_bytes();d=json.loads(raw)
    if d.get('independent_audit',{}).get('status')!='passed':raise ValueError('audited source required')
    TMP.mkdir(exist_ok=True);compile_seconds=tree_native.compile_tool(TMP);code=program();rows=[]
    for name in ('I.5','I.6','triangle-order'):
        row=next(r for r in d['runs'] if r['id']==name and 'decoded' in r['result'])
        old=row['result']['decoded']['request'];axioms={s:'Rule'+str(i) for i,s in enumerate(sorted(old['theory']['axioms']))};new=rename(old,axioms)
        host=check(canonical(new));primitive=replay(canonical(new))
        native=tree_native.check(canonical(new),code,TMP,problem_hash(new),steps=100000000)
        native_binding(code,new,native)
        if any(r['status']!='accepted' for r in (host,primitive,native)):raise ValueError('renaming acceptance')
        if primitive['expanded_lines']!=row['primitive_lines']:raise ValueError('changed primitive proof size')
        c=row['catalog'];rc=rename(c,axioms);bound=T.supports(c);rbound=T.supports(rc)
        if canonical(bound)!=canonical(rbound):raise ValueError('resource structure changed')
        a=T.Model(c,row['length'],support_certificate=bound);b=T.Model(rc,row['length'],support_certificate=rbound)
        if set(a.cache)!=set(b.cache) or any(a.cache[k].occupancy!=b.cache[k].occupancy or a.cache[k].marks!=b.cache[k].marks for k in a.cache):raise ValueError('actual point inventory changed')
        record=dict(id=name,source_lane=row['lane'],source_request_sha256=hashlib.sha256(canonical(old)).hexdigest(),request=new,host=host,native=native,primitive_lines=primitive['expanded_lines'],identical_point_candidates=len(a.cache),identical_resource_certificate=True,axiom_names=axioms)
        if name=='triangle-order':
            source=T.search(c,3,support=True,seconds=5);target=T.search(rc,3,support=True,seconds=5)
            if source['status']!='finite_exact_proof_tiling' or target['status']!=source['status'] or canonical(source['search_tree'])!=canonical(target['search_tree']) or source['placements']!=target['placements']:raise ValueError('changed GCTS search')
            record['fresh_gcts_control']=dict(status=target['status'],states=target['nodes'],attempts=target['base_attempts'],identical_full_search_tree=True,original=source,renamed=target)
        rows.append(record);print(name,'accepted',primitive['expanded_lines'],'identical point candidates',len(a.cache),flush=True)
    result=dict(version='symbol-renaming-001',scope='post-search bijective predicate and axiom-name renaming, independently expanded and natively checked; identical exact point inventories and resource certificates; fresh elementary GCTS search with identical complete tree; no new discovery or arbitrary reinterpretation of axioms',names=NAMES,source=dict(file='euclidean-proofs-001.json',sha256=hashlib.sha256(raw).hexdigest()),sources=dict(d['sources'],**{'run_symbol_renaming.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'audit_symbol_renaming.py':hashlib.sha256((HERE/'audit_symbol_renaming.py').read_bytes()).hexdigest()}),cases=rows,compile_seconds=compile_seconds,seconds=time.perf_counter()-started)
    (DOCS/'symbol-renaming-001.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
if __name__=='__main__':main()
