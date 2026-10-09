"""Second cold iteration: spatial proposals, hierarchy inspection, proof kernels.

No saved marking, policy, witness, motif, or substitution is read. Results from
iteration one remain a separate historical comparison with different targets.
"""
import hashlib,json,resource,time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import *
import logic,spatial,wang

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parent.parent/"docs/research/gcts-rl-renewal/iteration-002.json"

def main():
    start=time.monotonic()
    report={"iteration":2,"date":datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
            "initial_marking":None,"initial_policy":"all weights zero","known_substitution_imported":False,
            "known_tiling_imported":False,"prior_snapshot_imported":False,
            "source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob("*.py")},
            "configuration":{"donors":6,"donor_target":64,"motif_max_size":4,"library_limit":8,
                "training_episodes":24,"training_target":24,"evaluation_target":64,"evaluation_starts":3,
                "node_limit":2000,"seconds":12,"proposal_provider":"spatial.Proposer"}}
    def save(): OUTPUT.write_text(json.dumps(report,indent=2)+"\n")
    oracle=Model(); catalog=pair_catalog(oracle)
    samples=[one_corona(oracle,key,180,1.5) for key in catalog]
    report["pair_labels"]={"count":len(samples),"counts":dict(Counter(s["status"] for s in samples)),
                           "seconds":sum(s["seconds"] for s in samples),"samples":samples}
    print("cold labels",report["pair_labels"]["counts"],flush=True); save()
    check_start=time.monotonic(); checked=0
    for i,s in enumerate(samples):
        if s["status"]=="negative":
            ok,n=check_failure_certificate(oracle,s["second"],s["certificate"]); assert ok; checked+=n
        elif s["status"]=="positive":
            assert verify_patch(oracle,s["witness"],rooted(oracle,s["second"]).totals)
            replay=State()
            for key in s["witness"]: replay.place(oracle.placement(key))
            assert all(exhaustive_domains(oracle,replay).values())
        else: raise AssertionError("unresolved cold labels; marking activation postponed")
        if (i+1)%50==0: print("checked contact",i+1,flush=True)
    marking,summary=synthesize(samples,0)
    assert summary["positive_accepted"]==summary["positives"] and summary["negative_rejected"]>summary["negatives"]/2
    report["marking"]={**summary,"snapshot_for_inspection_only":[[p,v] for p,v in sorted(marking.items())],
                       "redundancy_checks":verify_redundancy_scope(marking,samples)}
    report["pair_verification"]={"verified":True,"negative_nodes":checked,"seconds":time.monotonic()-check_start}
    save()
    donors=[]
    for i in range(6):
        r=growth_search(Model(marking),50000+i,64,6000,30); donors.append(r)
        print("spatial donor",i,r["tiles"],r["status"],flush=True)
    mine_start=time.monotonic()
    library,stats=spatial.mine(Model(marking),donors,max_size=4,limit=8)
    report["spatial_library"]={"motifs":library,"statistics":stats,"donors":donors,
        "seconds":time.monotonic()-mine_start,"scope":"spatial point-connected motifs; not substitution rules"}
    print("spatial library",stats,flush=True); save()
    proposer=spatial.Proposer(library); policy=Policy(); episodes=[]; train_start=time.monotonic()
    for i in range(24):
        r=cluster_rollout(Model(marking),60000+i,library,24,policy,True,proposer); episodes.append(r)
        if (i+1)%4==0: print("spatial RL episode",i+1,r["tiles"],flush=True)
    report["training"]={"episodes":episodes,"updates":policy.updates,"seconds":time.monotonic()-train_start,
                        "weights":dict(policy.weights),"scope":"REINFORCE over spatial schedulable prefixes with complete base fallback"}
    positives=[s for s in samples if s["status"]=="positive"]
    evaluation=[]
    for lane in ("baseline","GCTS","RL","GCTS+RL"):
        for i in range(3):
            second=positives[i*len(positives)//3]["second"]
            model=Model(marking if "GCTS" in lane else None)
            r=growth_search(model,70000+i,64,2000,12,policy if "RL" in lane else None,
                            library if "RL" in lane else (),second,proposer if "RL" in lane else None)
            r.update({"lane":lane,"initial_pair":second,"metrics":dict(model.metrics)})
            evaluation.append(r); print("spatial evaluation",lane,i,r["tiles"],r["status"],round(r["seconds"],2),flush=True)
    report["evaluation"]=evaluation; save()
    hierarchy_start=time.monotonic(); hierarchies=[]
    # Evaluation prefixes were never inputs to motif extraction or policy updates.
    # Finite shape overlap with donors is possible, and is explicitly reported.
    for r in evaluation:
        if r["lane"]=="GCTS" and r["status"]=="consistent_finite_patch":
            h=spatial.partition(Model(marking),r["placements"],library,3)
            h.update({"seed":r["seed"],"placements":r["placements"]}); hierarchies.append(h)
    report["hierarchies"]={"samples":hierarchies,"seconds":time.monotonic()-hierarchy_start,
        "scope":"three exact finite partition levels; no inflation map or recursive coverage invariant inferred"}
    report["logic"]=logic.demo(); report["wang_certificate_search"]=wang.certificate_demo()
    report["total_seconds"]=time.monotonic()-start
    report["peak_process_memory_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["substitution_status"]="open: exact spatial interfaces and finite hierarchy partitions, no stationary recursive rule"
    report["plane_proof_status"]="open"
    report["proof_system_status"]="first-order certificate kernel + separate Wang arithmetic certificate search; compiler linking them remains open"
    save(); print("finished",round(report["total_seconds"],2),"seconds",flush=True)

if __name__=="__main__": main()
