"""Reproducible cold research iteration. Never reads a saved model or tiling."""
import argparse
import hashlib
import json
import resource
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import *
import cyclotomic
import wang
from inflation import probe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"docs/research/gcts-rl-renewal/iteration-001.json")
    parser.add_argument("--episodes",type=int,default=120)
    parser.add_argument("--cluster-episodes",type=int,default=60)
    parser.add_argument("--evaluation-seeds",type=int,default=5)
    parser.add_argument("--target",type=int,default=32)
    parser.add_argument("--node-limit",type=int,default=1600)
    parser.add_argument("--seconds",type=float,default=15)
    args = parser.parse_args()
    start = time.monotonic()
    config = {k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()}
    report = {"iteration":1,"date":datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
              "config":config,"initial_marking":None,"initial_policy":"all weights zero",
              "known_substitution_imported":False,"known_tiling_imported":False,
              "geometry_source":"GCTS-I.html turtle vertices and angle units only",
              "source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob("*.py")},
              "point_model":{"capacity":12,"support_points":len(BASE),"orientations":12,"vertices":VERTICES,
                             "occupancy":[[p,v] for p,v in BASE.items()],"sum_units":sum(BASE.values())}}
    def checkpoint():
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+"\n")
    oracle = Model()
    catalog = pair_catalog(oracle)
    samples = []
    for i,key in enumerate(catalog):
        samples.append(one_corona(oracle,key,node_limit=180,seconds=1.5))
        if (i+1)%50==0: print("pair labels",i+1,dict(Counter(s["status"] for s in samples)),flush=True)
    report["pair_catalog"] = {"count":len(catalog),"counts":dict(Counter(s["status"] for s in samples)),
                              "seconds":sum(s["seconds"] for s in samples),"samples":samples}
    checkpoint()
    verification_start = time.monotonic()
    proof_nodes = 0
    for i,s in enumerate(samples):
        if s["status"]=="negative":
            valid,n = check_failure_certificate(oracle,s["second"],s["certificate"])
            assert valid,(i,s["second"])
            proof_nodes += n
        elif s["status"]=="positive":
            initial = rooted(oracle,s["second"])
            assert verify_patch(oracle,s["witness"],initial.totals)
            state = State()
            for key in s["witness"]: state.place(oracle.placement(key))
            assert all(exhaustive_domains(oracle,state).values())
        if (i+1)%50==0: print("independent pair verification",i+1,flush=True)
    report["pair_verification"] = {"verified":True,"negative_proof_nodes":proof_nodes,
                                    "seconds":time.monotonic()-verification_start}
    synthesis_start = time.monotonic()
    marking,summary = synthesize(samples,0)
    gate = (len(samples)==len(catalog) and not any(s["status"]=="unresolved" for s in samples)
            and summary["positive_accepted"]==summary["positives"]
            and summary["negative_rejected"]>summary["negatives"]/2)
    assert gate
    # Exact soundness gate: scalar pullback, support inside positive t-support,
    # complete relative pair catalog, every rejected contact proved negative.
    assert set(marking)<=set(BASE)
    marked = Model(marking)
    seed = rooted(marked)
    rejected = {key for key in catalog if not seed.legal(marked.placement(key))}
    negative = {s["second"] for s in samples if s["status"]=="negative"}
    assert rejected<=negative and len(rejected)==summary["negative_rejected"]
    report["marking"] = {**summary,"gate_passed":gate,"seconds":time.monotonic()-synthesis_start,
                         "snapshot_for_inspection_only":[[p,v] for p,v in sorted(marking.items())],
                         "provenance":"synthesized in this cold run; never loaded by runner",
                         "scope":"redundant for complete A2 point-model tilings by certified pair exclusion; finite prefixes may change"}
    report["marking"]["redundancy_checks"] = verify_redundancy_scope(marking,samples)
    report["extended_support_controls"] = []
    for radius in (1,2):
        _,control = synthesize(samples,radius)
        report["extended_support_controls"].append({**control,"radius":radius,
            "scope":"learned restriction only; mark-only contacts outside pair catalog are not certified"})
    checkpoint()
    print("marking",summary["assigned"],"values; rejected",len(rejected),flush=True)
    policy = Policy()
    train_start = time.monotonic()
    episodes = []
    for i in range(args.episodes):
        episodes.append(rollout(Model(),10000+i,args.target,policy,learn=True))
    report["single_training"] = {"episodes":episodes,"seconds":time.monotonic()-train_start,
                                 "updates":policy.updates,"scope":"unmarked candidate policy; bootstrap only"}
    # The donor patches are searched from this run's own geometry and labels.
    # They never come from a known substitution or a bundled tiling catalog.
    donors = []
    for i in range(8):
        donors.append(growth_search(Model(marking),20000+i,args.target,args.node_limit,args.seconds))
        print("cluster donor",i,donors[-1]["tiles"],donors[-1]["status"],flush=True)
    library = mine_clusters(marked,donors)
    report["cluster_library"] = {"motifs":library,"donors":donors,
        "scope":"irregular sequences, lengths two through five; not substitution rules"}
    sequence_policy = Policy()
    cluster_start = time.monotonic()
    cluster_episodes = []
    for i in range(args.cluster_episodes):
        cluster_episodes.append(cluster_rollout(Model(marking),30000+i,library,args.target,sequence_policy,learn=True))
        if (i+1)%20==0: print("sequence RL training",i+1,flush=True)
    report["cluster_training"] = {"episodes":cluster_episodes,"seconds":time.monotonic()-cluster_start,
        "updates":sequence_policy.updates,"scope":"REINFORCE selects validated sequences with base fallback"}
    evaluation = []
    positives = [s for s in samples if s["status"]=="positive"]
    # Evaluation starts from several fixed pairs; donors/train rollouts start
    # from a single tile. All pair labels still participate in GCTS synthesis.
    # These starts need not be absent as subpatches of training trajectories.
    for lane in ("baseline","GCTS","RL","GCTS+RL"):
        for i in range(args.evaluation_seeds):
            second = positives[(i*len(positives)//args.evaluation_seeds)%len(positives)]["second"]
            model = Model(marking if lane in ("GCTS","GCTS+RL") else None)
            run = growth_search(model,40000+i,args.target,args.node_limit,args.seconds,
                                sequence_policy if "RL" in lane else None,library if "RL" in lane else (),second)
            run["lane"] = lane
            run["initial_pair"] = second
            run["metrics"] = dict(model.metrics)
            evaluation.append(run)
            print("evaluation",lane,i,run["tiles"],run["nodes"],run["status"],flush=True)
    report["evaluation"] = evaluation
    report["inflation_controls"] = [probe(s) for s in (2,3)]
    report["penrose"] = cyclotomic.audit()
    report["wang"] = wang.demo()
    report["total_seconds"] = time.monotonic()-start
    report["peak_process_memory_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["substitution_status"] = "not discovered; no inflation or metatile rule supplied"
    report["plane_tiling_proof_status"] = "not established by this experiment"
    report["theorem_prover_status"] = "not implemented; Wang encoding and finite accepting computation verified"
    checkpoint()
    print("finished",round(report["total_seconds"],1),"seconds",str(args.output),flush=True)

if __name__=="__main__": main()
