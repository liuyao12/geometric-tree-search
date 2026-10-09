"""Cold first-order proposal/search comparison; fixed external declarations."""
import hashlib,json,resource,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import logic,lazy_wang,proof_search,kernel_search
from kernel_machine import Catalog,KernelMachine,latex
from turtle import Policy
from audit_kernel_machine import audit,audit_catalog

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/'docs/research/gcts-rl-renewal/kernel-machine-001.json'
SOURCES=('kernel_machine.py','kernel_search.py','run_kernel_machine.py','audit_kernel_machine.py',
         'logic.py','wang.py','lazy_wang.py','rewrite_machine.py','proof_search.py','turtle.py','replay_proofs.py')
LANES=(('standard Wang',False,False),('analytic marking',True,False),
       ('RL + standard Wang',False,True),('RL + analytic marking',True,True))

def arithmetic_control():
    """Known kernel witness supplied only to a compiler round-trip control."""
    d=logic.demo();z=logic.F('zero');x,y=logic.V('x'),logic.V('y')
    axioms={'add_zero':logic.All('x',logic.Eq(logic.F('add',x,z),x)),
            'add_successor':logic.All('x',logic.All('y',logic.Eq(logic.F('add',x,logic.F('succ',y)),logic.F('succ',logic.F('add',x,y)))))}
    kernel=logic.Kernel({'zero':0,'succ':1,'add':2},{},axioms)
    formulas=tuple(l['formula'] for l in d['proof']);templates=tuple(l['template'] for l in d['proof'] if 'template' in l)
    terms=tuple(l['term'] for l in d['proof'] if 'term' in l)
    c=Catalog(kernel,formulas,terms,('x','y','hole'),templates);m=KernelMachine(c,d['target'])
    commands=c.commands_for_proof(d['proof'],d['target']);r=m.run(m.tokens(commands))
    if r['status']!='accept':raise ValueError('arithmetic compiler round-trip failed')
    return {'scope':'supplied kernel-proof compiler control only; proof and catalog excluded from discovery and RL',
            'statement':d['statement'],'declaration':c.declaration(),'target':d['target'],
            'original_proof':d['proof'],'commands':commands,'decoded_proof':c.proof(commands,d['target']),
            'machine_states':len(m.compiler.states),'transitions':len(m.compiler.transitions),'machine_steps':r['steps'],
            'catalog_audit':audit_catalog(c),'verified':True}

def main():
    start=time.monotonic();policy=Policy();training=kernel_search.problems(2);episodes=[];t=time.monotonic()
    for i in range(128):
        p=training[i%len(training)];q=kernel_search.propose(p['catalog'],p['target'],policy,42000+i,5,learn=True)
        episodes.append({'problem':p['id'],'seed':42000+i,**q})
    report={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
            'sources':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in SOURCES},
            'relation':'kernel derivability within externally fixed finite syntax envelopes, with an explicit fair union',
            'configuration':{'lanes':[n for n,_,_ in LANES],'training_episodes':128,'training_distractors':2,
                             'evaluation_distractors':3,'proposal_horizon':5,'nodes':100000,'seconds':3},
            'training':{'episodes':episodes,'weights':dict(policy.weights),'seconds':time.monotonic()-t,
                        'success':sum(e['verified'] for e in episodes),'cold_start':'zero weights; no proof, certificate or previously learned policy',
                        'reuse':'same six assertions; evaluation adds a third unused theory axiom. This is a same-problem distractor control, not held-out mathematical generalization.',
                        'reward':'verified kernel target minus actual inference-command cost; failed proposals receive -0.5'},
            'conformance':{'domain':'all doubled-grid rectangle centers, integer capacity one; every center root generation zero',
                           'markings':'four edge colors; optional analytically redundant neighbor values, not learned failure markings',
                           'inventory':'literal finite TM transitions; complete zero/one-head Wang triples in four exhaustive Cartesian blocks',
                           'graph':'one shared candidate per center/triple; all four colors and extended dependencies maintained',
                           'scheduler':'global dead, global forced, earliest generation; all roots zero, placed generation one',
                           'rollback':'unchanged independently tested lazy Wang trail',
                           'proposals':'valid first-order inference sequences translated to rectangle preferences; full base alternatives retained',
                           'verification':'independent rule inventory, direct TM rows and point sums/marks, decoded kernel derivation',
                           'unknown':'all finite limits are unknown; exhausted rectangle applies only to that envelope/certificate/height'},
            'limitations':['finite catalogs are compiled before search; no single fixed unbounded serialized-AST checker yet',
                           'fair syntax enumeration is expressively complete relative to Kernel but computationally expensive',
                           'finite closed axioms only; checked infinite theory schemas remain open',
                           'compiler and semantic kernel have executable checks, not a formalized correctness proof',
                           'the six assertion controls do not establish practical mathematical proof-search performance'],
            'problems':[]}
    print('cold training',report['training']['success'],'/ 128',round(report['training']['seconds'],3),'s',flush=True)
    for i,p in enumerate(kernel_search.problems(3)):
        c=p['catalog'];t=time.monotonic();m=KernelMachine(c,p['target']);compile_seconds=time.monotonic()-t
        length=8;height=384
        problem={'id':p['id'],'declaration':c.declaration(),'target':p['target'],'statement':latex(p['target']),
                 'formulas_latex':[latex(a) for a in c.formulas],
                 'inferences':[{'premises':r.premises,'conclusion':r.conclusion,'rule':r.witness['rule']} for r in c.inferences],
                 'certificate_length':length,'height':height,'compile_seconds':compile_seconds,
                 'machine':{'states':len(m.compiler.states),'alphabet':len(m.compiler.alphabet),'transitions':len(m.compiler.transitions)},
                 'catalog_audit':audit_catalog(c),'runs':[]}
        for lane,extended,learned in LANES:
            lane_start=time.monotonic();proposal=None;preferred=None
            if learned:
                proposal=kernel_search.propose(c,p['target'],policy,43000+i,5)
                preferred=kernel_search.preference(m,length,height,proposal)
            r=lazy_wang.search(m.compiler,m.pattern(length),height,m.accepting_row(len(m.pattern(length))),
                               node_limit=100000,seconds=3,extended=extended,preferred=preferred)
            r['lane']=lane;r['proposal']=proposal;r['preferred_rectangle']=preferred is not None
            if r.get('verified'):
                cert=proof_search.pack(r);rows,_=proof_search.unpack(cert);offset=len(c.formulas)+4
                commands=m.parse(rows[0][offset:offset+length]);proof=c.proof(commands,p['target'])
                r['certificate']=cert;r['commands']=commands;r['kernel_proof']=proof
                r['display_proof']=[{'rule':l['rule'],'formula':latex(l['formula'])} for l in proof]
                for field in ('rows','placements','initial','tile_generations'):r.pop(field,None)
            r['lane_seconds']=time.monotonic()-lane_start
            problem['runs'].append(r)
            print(p['id'],lane,r['status'],r['nodes'],round(r['lane_seconds'],3),'s',flush=True)
        report['problems'].append(problem)
    report['arithmetic_control']=arithmetic_control()
    report['search_training_and_control_seconds']=time.monotonic()-start
    OUTPUT.write_text(json.dumps(report,separators=(',',':'))+'\n')
    report['independent_audit']=audit(OUTPUT)
    report['total_seconds']=time.monotonic()-start
    report['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    OUTPUT.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print('audit',report['independent_audit']['checked_rectangles'],'rectangles',report['independent_audit']['point_placements_checked'],'placements',flush=True)

if __name__=='__main__':main()
