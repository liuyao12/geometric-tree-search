"""Cold RL proposals and complete symbolic Wang search for word proofs.

All benchmark theories and statements are declared here, outside certificates.
The alphabet/rules define the formal problem; no proof commands seed the policy.
Tiny held-out statements test this implementation, not general proof difficulty.
"""
import hashlib,json,random,resource,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import Policy
from rewrite_machine import Theory,ProofMachine,check_derivation,tm_theory
import lazy_wang,proof_search,wang

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/"docs/research/gcts-rl-renewal/proof-search-001.json"
THEORY=Theory(('a','b'),((('a',),('b',)),(('b',),('a',)),(('a','a'),('a',)),(('b',),('b','b'))))
CASES=((('a',),('b',),3,3,128),
       (('a','a'),('b','b'),4,6,256),
       (('a','b','a'),('b','b','b'),5,7,384))
LANES=(("standard Wang",False,False),("analytic GCTS",True,False),
       ("RL + standard Wang",False,True),("analytic GCTS + RL",True,True))

def machine_digest(machine):
    c=machine.compiler
    raw={"alphabet":c.alphabet,"states":c.states,"halt":c.halt,
         "transitions":sorted(c.transitions.items(),key=repr)}
    return hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def reduction_example():
    """Operational witness for the general transition-shape construction."""
    compiler=wang.Compiler(('B','1'),('start','next','halt'),
                           {('start','B'):('next','1',1),('next','B'):('halt','1',0)},'halt')
    theory,encode=tm_theory(compiler);row=('B',wang.head('start','B'),'B','B')
    word=source=encode(row);commands=[];trace=[word];rows=[row]
    for _ in range(2):
        row=wang.direct_step(compiler,row);desired=encode(row);rows.append(row)
        choices=[(command,new) for command,new in proof_search.singles(theory,word,100) if new==desired]
        assert len(choices)==1
        command,word=choices[0];commands.append(command);trace.append(word)
    while word!=('ACCEPT',):
        command,word=next(proof_search.singles(theory,word,100));commands.append(command);trace.append(word)
    assert check_derivation(theory,source,('ACCEPT',),commands)[0]
    machine=ProofMachine(theory,('ACCEPT',));tokens=machine.certificate_tokens(commands)
    result=machine.run(source,16,tokens,10000);assert result['status']=='accept'
    return {"scope":"finite example checks the arbitrary-TM reduction; universality follows from the general transition forms and configuration invariant",
            "theory":{"alphabet":theory.alphabet,"rules":theory.rules},"source":source,"target":('ACCEPT',),
            "commands":commands,"derivation":trace,"tm_rows":rows,"checker_machine_steps":result['steps'],
            "checked":True,"transition_shapes":"stay, left/right interior moves, left/right blank border extension, halt-only erasure",
            "invariant":"one state marker and preserved L/R delimiters before halt; only halt marker enables ACCEPT cleanup"}

def main():
    start=time.monotonic()
    report={"date":datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
            "source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob('*.py')},
            "proof_relation":"finite directed word reachability over arbitrary finite alphabets and rules",
            "theory":{"alphabet":THEORY.alphabet,"rules":THEORY.rules},
            "configuration":{"training_seed":22000,"training_episodes":64,"training_source_lengths":[4,5,6],
                             "training_capacity":8,"training_actions":8,"evaluation_seeds":[24000,24001,24002],
                             "nodes_per_rectangle":100000,"seconds_per_rectangle":5,
                             "lanes":[name for name,_,_ in LANES]},
            "conformance":{"domain":"doubled integer grid centers with fixed finite rectangle roots",
                           "required_generation":0,"placed_generation":1,"occupancy":"one at each center; four edge midpoint values",
                           "inventory":"four disjoint Cartesian blocks exhaust zero/one-head triples; no materialized million-type list",
                           "incidence":"complete symbolic center domains; (center,triple) reverse incidence is its unique center",
                           "scheduler":"global dead, global forced, earliest generation; root ties by row then column",
                           "rollback":"trail restores selected cells, all marks including new distant dependencies, domains, order and generations",
                           "proposal":"learned word-rule singleton/two-move sequences; independently validated proof compiles to tile preferences",
                           "execution":"every preferred tile still uses the global graph scheduler; all base alternatives retained",
                           "marking_control":"analytic redundant neighbor-value assignment, not a learned failure marking",
                           "unknown":"every node/time/stage-limited non-success is unknown; no unprovability inference"},
            "marking_lemma":{"hypothesis":"complete standard Wang rectangle; blank side pairs",
                             "assignment":"tile (a,b,c) also assigns a,c at the bottom-value points of its left/right neighbors",
                             "reason":"horizontal W=(a,b), E=(b,c) equalities already imply a=S_left and c=S_right; exterior side values are blank",
                             "conclusion":"the extended marking preserves every complete solution; finite prefixes can be pruned sooner",
                             "learned":False},
            "limitations":["first-order Hilbert kernel to this executable checker remains open",
                           "finite compiler tests and independent semantic certificates are not a formally verified compiler",
                           "tiny held-out rewrite problems do not establish performance on general mathematical proofs",
                           "turtle substitution and Penrose hierarchical subsystem remain open"]}
    rng=random.Random(22000);policy=Policy();episodes=[];training_start=time.monotonic()
    for i in range(64):
        n=rng.randrange(4,7);source=tuple(rng.choice(('a','a','b')) for _ in range(n));target=('b',)*n
        machine=ProofMachine(THEORY,target)
        result=proof_search.propose(machine,source,8,23000+i,policy,max_actions=8,learn=True)
        result.update({"source":source,"target":target});episodes.append(result)
    report['training']={"cold_start":"zero weights; no certificate, saved policy, proof witness or proof-specific move sequence imported",
                        "episodes":episodes,"weights":dict(policy.weights),"seconds":time.monotonic()-training_start,
                        "success":sum(e['status']=='checked_rewrite_proposal' for e in episodes),
                        "reward":"checked goal + edit-distance improvement, costs for actual word moves and compiled TM steps; no macro-count reward"}
    print('cold proof policy',report['training']['success'],'/',len(episodes),'seconds',round(report['training']['seconds'],3),flush=True)
    report['evaluation']=[];report['problems']=[]
    def save():OUTPUT.write_text(json.dumps(report,separators=(',',':'))+'\n')
    for i,(source,target,capacity,certificate_length,height) in enumerate(CASES):
        compile_start=time.monotonic();machine=ProofMachine(THEORY,target);compile_seconds=time.monotonic()-compile_start
        pattern=machine.pattern(source,capacity,certificate_length);u=lazy_wang.Universe(machine.compiler)
        report['problems'].append({"id":i,"source":source,"target":target,"capacity":capacity,
                                   "certificate_length":certificate_length,"height":height,"width":len(pattern),
                                   "states":len(machine.compiler.states),"tape_alphabet":len(machine.compiler.alphabet),
                                   "transitions":len(machine.compiler.transitions),"tile_types":u.inventory_count,
                                   "compile_seconds":compile_seconds,"machine_sha256":machine_digest(machine)})
        for lane,extended,use_rl in LANES:
            lane_start=time.monotonic();proposal=None;preferred=None;preference_seconds=0
            if use_rl:
                proposal=proof_search.propose(machine,source,capacity,24000+i,policy,max_actions=8)
                preference_start=time.monotonic()
                preferred=proof_search.rectangle_preference(machine,source,capacity,certificate_length,height,proposal)
                preference_seconds=time.monotonic()-preference_start
            result=lazy_wang.search(machine.compiler,pattern,height,machine.accepting_row(len(pattern)),
                                    node_limit=100000,seconds=5,preferred=preferred,extended=extended)
            result=proof_search.pack(result);result=json.loads(json.dumps(result))
            result.update({"problem_id":i,"lane":lane,"proposal":proposal,"preference_seconds":preference_seconds,
                           "preferred_tiles":len(preferred or {}),"lane_seconds":time.monotonic()-lane_start,
                           "seed":24000+i if use_rl else None})
            if result.get('verified'):
                replay_start=time.monotonic()
                assert proof_search.replay(machine,source,capacity,certificate_length,height,result)
                rows,_=proof_search.unpack(result);tokens=rows[0][capacity+4:capacity+4+certificate_length]
                commands=machine.parse_certificate(tokens);ok,trace=check_derivation(THEORY,source,target,commands,capacity);assert ok
                result.update({"found_tokens":tokens,"found_commands":commands,"word_derivation":trace,
                               "serialized_replay_seconds":time.monotonic()-replay_start})
            report['evaluation'].append(result);save()
            print('problem',i,lane,result['status'],'nodes',result['nodes'],'seconds',round(result['lane_seconds'],3),flush=True)
    report['universality_reduction']=reduction_example()
    machine=ProofMachine(THEORY,('b',))
    report['fair_bound_control']=proof_search.fair_search(machine,('a',),max_stage=2)
    report['fairness']={"schedule":"at stage s, all powers-of-two bounds with exponent sum at most s and node budget 2**s",
                        "proof":"any finite derivation fits some capacity and padded certificate; its accepting computation fits a larger power-of-two height. This fixed triple recurs at every later stage with unbounded node budget; finite complete DFS eventually covers its proof",
                        "implementation":"fair_search; unlimited execution has no wall-clock cutoff; bounded example is unknown",
                        "truth_scope":"semidecides derivability in the declared word theory; does not decide arbitrary truth or terminate on every negative"}
    report['total_seconds']=time.monotonic()-start
    report['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save();print('finished generic proof pilot',round(report['total_seconds'],3),'seconds',flush=True)

if __name__=='__main__':main()
