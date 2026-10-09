"""Independent primitive replay of PA and Euclid-style searched examples.

Externally pinned theories and statements, earlier-only block provenance,
independent normalization graphs, equality rewrite interfaces and native input
heaps. No producer, theorem generator or proof-search imports.
"""
import copy,hashlib,json,resource,time
from pathlib import Path
from audit_proof_compaction import audit_pair,native_binding,pin
from audit_proof_blocks import rules,offers,decision_key,frozen
from audit_serialized_kernel import replay
from audit_tree_kernel import packed,sha,need

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
PA_THEORY='d58a57a4855a41f78f3f660d8cc9b805c88fd22cca944ae5b514c9db6c46e36d'
EUCLID_THEORY='31b2f664c92fc0ae8988137cbfadf1526d50a8cdfc7624b515f5f91da75aa5e2'
TARGETS={
 'add-one':'f0434957355c68f305283152a342d44943e177d34d16a376edfff0e78fab5d6f',
 'add-left-zero':'a79295791cd08435bfb80be2ed4d2c87f23cc1d0f4fa6435b697e1ed190b75c3',
 'add-left-successor':'7d79dc0d62dbdaa9d0ce09875b1f21d63e783aec72d402aa6afa1254ee5d874d',
 'add-commutative':'ebfc6332fb0e88213748124fa70fb130effb395fe8173e68642ad6ee9b39166d',
 'add-associative':'3ae9f0a1941b0c20292663ac002ac1018c3e4c567fb6801ac662e74bbf1eed8a',
 'mul-left-zero':'2a87f2d4000ac986cfd9612e275881d38e76c12a3c7459ba9dfd86c79942de9e',
 'mul-right-one':'3b9d1af0f1bcbf54aba51ce32f1fb615975e99249603dd3cf7438f4cc9671625',
 'mul-left-one':'719036cc4dfbba895807f85a371c6b44072e690d0581ec3d463308dff14053ab',
 'mul-distributes':'d0c4a12a169c41132ebfaf13aeecd5f64494df2d678d443beeda5ca7750125f1',
 'mul-left-successor':'cc39f86a3dc91b123cfae176b8a67c89dd66c459cbad78132b911d1b8bd175f2',
 'mul-commutative':'af4a3b634c6eab528c33fdcbb96daa399a7baa0250cedf88a974dc427d860a7b',
 'mul-associative':'38509af9a1683a8d42f118897889d1a73a0b6e0a3a94c384d6ecfa1a432fd397',
 'euclid-I1':'ce6f9bd21ebf82e64d0685b63bce5e5ea0ccce3c231e3cc07617e08d83640873',
 'euclid-I5':'bdd02ef8ada946f930dcc18847497d4661c71c92d14567bea498430f7c20afa7',
 'equilateral-base-angles':'083d44d0deba05bb3943f3d2e54ef4a55057de4c0a7d9dc89b4d1aae338d0d34',
 'euclid-I10-verification':'7b6cdb521bfc5b859bb5aa17a3868dbc2021a327875d8a80bbe3b655b5146df9'}
def audit(data,expected_theory,code,pa):
    need(sha(data['theory'])==expected_theory,'externally fixed theory')
    need(data['initial_library']==[],'cold empty theorem library')
    for n,h in data['sources'].items():need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,'source '+n)
    available={};results=[];expanded=0;path_moves=0;reversed_tree_edges=0
    for row in data['cases']:
        p=row['problem'];need(sha(p['target'])==TARGETS[p['id']],'external theorem statement '+p['id']);found=row['proposal']
        if found['status']!='accepted_proposal':results.append(dict(id=p['id'],status='unknown'));continue
        d=found['request'];need(d['theory']==data['theory'] and d['target']==p['target'],'exact theorem input')
        for b in d['blocks']:need(b['name'] in available and b==available[b['name']],'earlier searched lemma only')
        result=audit_pair(d,row['compaction'],pin(d));expanded+=result['compact_expanded_lines']
        r=replay(packed(row['compaction']['request']),pin(d));used_axioms=sorted({l['name'] for l in r['proof'] if l['rule']=='axiom' and not l['name'].startswith('@oracle')})
        if pa:
            context=dict(theory=data['theory'],library=[b for b in data['library'] if b['name'] in available])
            for record in found['records']:
                if 'path' not in record:continue
                goal=frozen(record['goal']);current=goal[1];rs=rules(context,record['assumptions'])
                for a in record['path']:
                    chosen=dict(a,rule=a['rule']['name'],origin=a['rule']['origin']);key=decision_key(chosen)
                    forward=any(decision_key(o)==key for o in offers(current,rs,record['term_limit']))
                    # Bidirectional BFS reverses an edge found from the other
                    # endpoint. For variable-erasing equations (x*0=0), that
                    # inverse is sound with its saved instance, even when x
                    # cannot be inferred from the local zero term alone.
                    reverse=dict(chosen,before=chosen['after'],after=chosen['before'],direction=-chosen['direction'])
                    backward=any(decision_key(o)==decision_key(reverse) for o in offers(frozen(reverse['before']),rs,record['term_limit']))
                    need(forward or backward,'independent contextual edge or reversed backward-tree edge')
                    reversed_tree_edges+=int(not forward)
                    current=frozen(a['after']);path_moves+=1
                need(current==goal[2],'searched path endpoint')
        native_binding(code,row['compaction']['request'],row['native'])
        if row.get('promoted'):
            need(row['native']['status']=='accepted','promotion requires full native acceptance')
            block=next(b for b in data['library'] if b['name']==row['promoted']);definition={k:block[k] for k in ('name','premises','conclusion','proof')}
            need(definition['proof']==d['proof'] and definition['conclusion']==d['target'] and definition['premises']==[],'actual searched proof provenance')
            probe=dict(d,blocks=d['blocks']+[definition],proof=[dict(rule='block',formula=d['target'],name=definition['name'],inputs=[])])
            checked=replay(packed(probe),pin(d));need(checked['status']=='accepted','independent promoted definition')
            available[block['name']]=definition
        results.append(dict(id=p['id'],status='independently_checked',native_status=row['native']['status'],axioms_used=used_axioms,dependencies=[b['name'] for b in d['blocks']],**result))
    need(set(available)=={b['name'] for b in data['library']},'library coverage')
    mutations=[];base=data['cases'][0]['compaction']['request'];fixed=pin(base)
    for n,mutate in [('theorem',lambda d:d.update(target=['bot'])),('axiom-injection',lambda d:d['theory']['axioms'].update(invented=d['target'])),('last-formula',lambda d:d['proof'][-1].update(formula=['bot'])),('forward-reference',lambda d:d['proof'][-1].update(source=len(d['proof'])+1)),('function-arity',lambda d:d['theory']['functions'].update(invented=0))]:
        wrong=copy.deepcopy(base);mutate(wrong);need(replay(packed(wrong),fixed)['status']=='rejected','mutation '+n);mutations.append(n)
    return dict(cases=results,expanded_primitive_lines=expanded,independent_rewrite_moves=path_moves,reversed_backward_tree_edges=reversed_tree_edges,mutations_rejected=mutations,scope='Every actual root and lemma independently expanded in the frozen Hilbert kernel, normalization checked, external theorem/theory and native input heaps bound. PA paths independently reconstructed, including inversions of actual backward-tree edges. Geometry search saturation and full native instruction traces are not independently reconstructed; logical soundness and toolchain formalization remain open.')
def audit_pilots(data,code):
    out=[]
    for n,h in data['previous_pilot'].items():need(hashlib.sha256((DOCS/n).read_bytes()).hexdigest()==h,'preserved pilot '+n)
    for stem in ('euclid-pilot','euclid-interface-pilot'):
        d=json.loads((DOCS/(stem+'-001.json')).read_text());snapshot=json.loads((DOCS/(stem+'-source-001.json')).read_text())
        for n,h in d['sources'].items():
            raw=snapshot[n].encode() if n in snapshot else (HERE/n).read_bytes();need(hashlib.sha256(raw).hexdigest()==h,'archived pilot source')
        for row in d['cases']:
            req=row['proposal']['request'];need(req['theory']==d['theory'] and req['target']==row['problem']['target'],'pilot actual theorem')
            audit_pair(req,row['compaction'],pin(req));native_binding(code,row['compaction']['request'],row['native'])
        out.append(dict(id=stem,theory_sha256=sha(d['theory']),cases=len(d['cases']),native_accepted=sum(r['native']['status']=='accepted' for r in d['cases']),unknown=sum(r['native']['status']!='accepted' for r in d['cases']),total_seconds=d['total_seconds'],scope='Preserved prototype theory/statement representation; not the same exact pinned theory as final interface experiment. Resource cutoffs remain unknown.'))
    return out
def main():
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program']
    for stem,expected,pa in [('peano-theorems',PA_THEORY,True),('euclid-theorems',EUCLID_THEORY,False)]:
        began=time.perf_counter();path=DOCS/(stem+'-001.json');data=json.loads(path.read_text());a=audit(data,expected,code,pa)
        if not pa:a['preserved_pilots']=audit_pilots(data,code)
        a.update(seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());data['independent_audit']=a
        path.write_text(json.dumps(data,separators=(',',':'))+'\n');print(stem,len(a['cases']),a['seconds'],flush=True)
if __name__=='__main__':main()
