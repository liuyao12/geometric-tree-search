"""Cold proof-block discovery, REINFORCE and matched proposal controls."""
import copy,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime,timezone
import proof_block_search as search
import proof_block_problems as problems
from tree_kernel import program,check as tree_check
from serialized_kernel import canonical,problem_hash
from turtle import Policy

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
OUTPUT=DOCS/'learned-proof-blocks-001.json';TMP=Path('/private/tmp/gcts-proof-blocks');TMP.mkdir(exist_ok=True)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def summary(r):return {k:v for k,v in r.items() if k!='request'}
def main():
    start=time.perf_counter();theory=problems.theory();library=[];discovery=[];before=time.perf_counter()
    for problem in problems.discovery():
        r=search.prove(theory,problem['target'],library,node_limit=1200,slack=3)
        if r['status']!='accepted_proposal':raise ValueError('discovery gate '+problem['id'])
        promoted=search.promote(r,library);discovery.append(dict(problem=problem,result=r,promoted=promoted and promoted['name']))
        print('discovered',problem['id'],r['root_lines'],r['blocks'],r['seconds'],flush=True)
    discovery_seconds=time.perf_counter()-before
    policy=Policy();training=problems.family(2701,24);episodes=[];before=time.perf_counter()
    for i in range(192):
        problem=training[i%len(training)];r=search.prove(theory,problem['target'],library,policy,28000+i,node_limit=1200,slack=3,rollouts=2,learn=True)
        episodes.append(dict(episode=i,problem=problem['id'],seed=28000+i,result=summary(r),weights=dict(policy.weights),baseline=policy.baseline,updates=policy.updates))
        if i%32==31:print('trained',i+1,policy.updates,flush=True)
    training_seconds=time.perf_counter()-before
    weights=dict(policy.weights);evaluation=problems.family(2702,18,True);runs=[];before=time.perf_counter()
    lanes=[('primitive',False,None,0),('blocks',True,None,0),('blocks-random-proposals',True,Policy(),2),('blocks-RL-proposals',True,policy,2)]
    for j,problem in enumerate(evaluation):
        for lane,use_library,model,rollouts in lanes:
            r=search.prove(theory,problem['target'],library if use_library else (),model,29000+j,node_limit=1200,slack=3,rollouts=rollouts)
            runs.append(dict(problem=problem['id'],lane=lane,result=r))
        print('evaluated',problem['id'],[(r['lane'],r['result']['status']) for r in runs[-4:]],flush=True)
    evaluation_seconds=time.perf_counter()-before
    if weights!=dict(policy.weights):raise ValueError('evaluation updated policy')
    # Independently compiled complete semantic program checks every found proof.
    before=time.perf_counter();code=program();compiled=[]
    for r in discovery+[dict(problem={'id':x['problem']+'/'+x['lane']},result=x['result']) for x in runs]:
        if r['result']['status']!='accepted_proposal':continue
        request=r['result']['request'];result=tree_check(canonical(request),code,expected_problem_sha256=problem_hash(request),steps=50000000)
        if result['status']!='accepted':raise ValueError('complete tree program rejected searched proof')
        compiled.append(dict(id=r['problem']['id'],result=result))
    tree_seconds=time.perf_counter()-before
    data=dict(date=datetime.now(timezone.utc).isoformat(),sources={n:digest(HERE/n) for n in ('proof_block_search.py','proof_block_problems.py','run_proof_blocks.py','serialized_kernel.py','logic.py','turtle.py','tree_kernel.py','fol_checker.tree')},
        theory=theory,discovery=discovery,library=library,discovery_seconds=discovery_seconds,
        training=dict(problems=training,episodes=episodes,initial_weights={},weights=weights,baseline=policy.baseline,updates=policy.updates,seconds=training_seconds),
        evaluation=dict(problems=evaluation,runs=runs,seconds=evaluation_seconds,lanes=[l[0] for l in lanes]),
        tree_program_checks=compiled,tree_seconds=tree_seconds,tree_program_sha256=compiled[0]['result']['program_sha256'],
        configuration=dict(node_limit=1200,term_slack=3,rollouts=2,horizon=10,training_episodes=192,max_inductions=3),
        conformance='semantic proposal adaptation only; fixed serialized/tree/tape checker grammar and all GCTS/Wang frontier bookkeeping, scheduling, rollback and marking semantics unchanged',
        scope='searched closed equational lemmas, recursive base cases and an authored innermost-variable induction tactic; bidirectional contextual rewrite proposal fragment, not complete FOL or GCTS search; learned block definitions and policy start empty',
        total_seconds=time.perf_counter()-start,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],len(compiled),flush=True)
if __name__=='__main__':main()
