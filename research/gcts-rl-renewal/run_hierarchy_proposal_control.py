"""Zero-weight proposal control for the same two externally bound lemmas."""
import hashlib,json,resource,time
from hierarchy_bridge import HERE,DOCS,proof_catalog
from kernel_machine import KernelMachine,immutable
from turtle import Policy
import kernel_search,lazy_wang,proof_search

def main():
    start=time.monotonic();bridge=json.loads((DOCS/'hierarchy-bridge-001.json').read_text());c,targets=proof_catalog()
    assert immutable(bridge['logical_declaration'])==c.declaration();rows=[];cells=0;tampers=0
    for j,(name,target) in enumerate(targets.items()):
        policy=Policy();m=KernelMachine(c,target);t=time.monotonic();q=kernel_search.propose(c,target,policy,106000+j,12)
        assert not policy.updates and all(v==0 for v in policy.weights.values())
        preferred=kernel_search.preference(m,12,1536,q)
        r=lazy_wang.search(m.compiler,m.pattern(12),1536,m.accepting_row(len(m.pattern(12))),
                          node_limit=100000,seconds=3,preferred=preferred)
        r.update(target=name,lane='zero-weight proposal + Wang',proposal=q,seconds_with_proposal=time.monotonic()-t)
        if r.get('verified'):
            cert=proof_search.pack(r);rs,tiles=proof_search.unpack(cert);assert kernel_search.replay(c,target,12,1536,cert)
            commands=m.parse(rs[0][len(c.formulas)+4:len(c.formulas)+16]);proof=c.proof(commands,target);cells+=len(tiles)
            r.update(certificate=cert,commands=commands,kernel_proof=proof)
            for field in ('rows','placements','initial','tile_generations'):r.pop(field,None)
            assert not c.kernel.check(proof,('bot',));tampers+=1
        rows.append(r);print(name,r['status'],r['nodes'],round(r['seconds_with_proposal'],3),len(r.get('commands',[])),flush=True)
    output={'logical_declaration_sha256':hashlib.sha256(json.dumps(bridge['logical_declaration'],separators=(',',':')).encode()).hexdigest(),
        'point_lemma_sha256':hashlib.sha256(json.dumps(bridge['point_lemma'],separators=(',',':')).encode()).hexdigest(),
        'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('run_hierarchy_proposal_control.py','hierarchy_bridge.py','kernel_machine.py','kernel_search.py','logic.py','lazy_wang.py','wang.py','proof_search.py','turtle.py')},
        'runs':rows,'independent_checks':{'checked_rectangles':sum(r.get('verified',False) for r in rows),'wang_cells':cells,'altered_target_rejections':tampers},
        'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':'new zero-weight process, no training; same two lemma targets and evaluation seeds; a proposal-effect control, not evidence of learned policy advantage',
        'timing_provenance':'separate supplementary process; research audit may run concurrently, so wall times are not matched latency comparisons'}
    (DOCS/'hierarchy-proposal-control-001.json').write_text(json.dumps(output,separators=(',',':'))+'\n')

if __name__=='__main__':main()
