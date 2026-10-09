"""Iteration three: explicitly reused certified markings, fresh growth/learning.

The first two experiments remain cold. This study reads their frozen learned
markings, never their patch witnesses, policy weights or motifs. Historical
learning and certificate costs are accounted for separately. No known human
marking, substitution, or named metatile is imported.
"""
import hashlib,json,resource,time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import Model,Policy,growth_search,cluster_rollout
import boundary_grammar,coverage,diverse_motifs,replay_proofs,spatial
from spatial_context import ContextProposer

HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/"docs/research/gcts-rl-renewal"
OUTPUT=DOCS/"iteration-003.json"

def main():
    start=time.monotonic();prior_path=DOCS/"iteration-002.json";halo_path=DOCS/"halo-probe-002.json"
    prior=json.loads(prior_path.read_text());halo=json.loads(halo_path.read_text())
    assert prior["source_sha256"]["turtle.py"]==hashlib.sha256((HERE/"turtle.py").read_bytes()).hexdigest()
    assert prior["pair_verification"]["verified"] and halo["independent_validation"]
    compact={tuple(p):v for p,v in prior["marking"]["snapshot_for_inspection_only"]}
    exterior={tuple(p):v for p,v in halo["snapshot_for_inspection_only"]}
    cfg={"donors":4,"donor_target":96,"donor_node_limit":10000,"donor_seconds":25,
         "motif_max_size":4,"frequency_library_limit":8,"diversity_per_category":2,
         "training_episodes":24,"training_target":24,"evaluation_target":128,
         "evaluation_starts":3,"node_limit":10000,"seconds":15,
         "macro_validation_limit":64,"core_radii":[0,4,8,12],"core_node_limit":5000,"core_seconds":15}
    report={"iteration":3,"date":datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
            "experiment_kind":"explicitly_reused_certified_markings_with_fresh_donors_and_policy",
            "initial_policy":"all weights zero","known_substitution_imported":False,"known_tiling_imported":False,
            "prior_snapshot_imported":True,"configuration":cfg,
            "source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob("*.py")},
            "reuse":{"iteration_002_sha256":hashlib.sha256(prior_path.read_bytes()).hexdigest(),
                     "halo_sha256":hashlib.sha256(halo_path.read_bytes()).hexdigest(),
                     "compact_learning_seconds":prior["pair_labels"]["seconds"]+prior["pair_verification"]["seconds"],
                     "exterior_additional_probe_seconds":halo["seconds"],
                     "exterior_independent_validation_seconds":halo["independent_validation"]["seconds"],
                     "scope":"frozen learned point-value assignments only; no saved policy, motifs or patch witnesses"},
            "markings":{"compact":[[p,v] for p,v in sorted(compact.items())],
                        "exterior":[[p,v] for p,v in sorted(exterior.items())]}}
    def save():OUTPUT.write_text(json.dumps(report,indent=2)+"\n")
    donors=[]
    for i in range(cfg["donors"]):
        model=Model(exterior);r=growth_search(model,82000+i,cfg["donor_target"],cfg["donor_node_limit"],cfg["donor_seconds"])
        r["metrics"]=dict(model.metrics);donors.append(r)
        print("fresh donor",i,r["status"],r["tiles"],round(r["seconds"],2),flush=True)
    assert sum(r["status"]=="consistent_finite_patch" for r in donors)>=2
    mine_start=time.monotonic();model=Model(exterior)
    frequency,frequency_stats=spatial.mine(model,donors,max_size=4,limit=8)
    diverse,diverse_stats=diverse_motifs.mine(model,donors,max_size=4,per_category=2)
    report["spatial_libraries"]={"donors":donors,"frequency":{"motifs":frequency,"statistics":frequency_stats},
                                "diversity":{"motifs":diverse,"statistics":diverse_stats},
                                "seconds":time.monotonic()-mine_start}
    print("libraries",len(frequency),len(diverse),diverse_stats,flush=True);save()
    hierarchy_start=time.monotonic()
    report["grammar_inspection"]={"frequency":boundary_grammar.infer(model,donors,frequency,4),
                                  "diversity":boundary_grammar.infer(model,donors,diverse,4,diverse_motifs.partition)}
    report["grammar_inspection"]["seconds"]=time.monotonic()-hierarchy_start
    for name in ("frequency","diversity"):
        print("grammar",name,{k:{field:v[field] for field in ("type_count","types_across_three_levels","types_with_growing_instances","parent_types_with_multiple_child_patterns")}
                              for k,v in report["grammar_inspection"][name]["classifiers"].items()},flush=True)
    save();policy=Policy();train_start=time.monotonic();episodes=[]
    proposer=ContextProposer(diverse,cfg["macro_validation_limit"],83000)
    for i in range(cfg["training_episodes"]):
        r=cluster_rollout(Model(exterior),83000+i,diverse,cfg["training_target"],policy,True,proposer)
        episodes.append(r)
        if (i+1)%4==0:print("context RL episode",i+1,r["tiles"],r["sequence_extra_moves"],flush=True)
    report["training"]={"episodes":episodes,"updates":policy.updates,"weights":dict(policy.weights),
                        "seconds":time.monotonic()-train_start,"proposal_provider":"spatial_context.ContextProposer",
                        "scope":"bounded diverse macros with shared-placement context; complete singleton fallback"}
    save();evaluation=[]
    lane_markings={"baseline":None,"compact GCTS":compact,"exterior GCTS":exterior,"RL":None,"exterior GCTS+RL":exterior}
    for lane,marking in lane_markings.items():
        for i in range(cfg["evaluation_starts"]):
            model=Model(marking);uses_rl="RL" in lane
            proposer=ContextProposer(diverse,cfg["macro_validation_limit"],84000+i)
            r=growth_search(model,84000+i,cfg["evaluation_target"],cfg["node_limit"],cfg["seconds"],
                            policy if uses_rl else None,diverse if uses_rl else (),None,proposer if uses_rl else None)
            r.update({"lane":lane,"metrics":dict(model.metrics)});evaluation.append(r)
            print("evaluation",lane,i,r["status"],r["tiles"],round(r["seconds"],2),flush=True)
        report["evaluation"]=evaluation;save()
    core_runs=[]
    for lane in ("baseline","compact GCTS","exterior GCTS","exterior GCTS+RL"):
        for i in range(cfg["evaluation_starts"]):
            model=Model(lane_markings[lane]);uses_rl="RL" in lane
            proposer=ContextProposer(diverse,cfg["macro_validation_limit"],85000+i)
            r=coverage.search(model,tuple(cfg["core_radii"]),85000+i,cfg["core_node_limit"],cfg["core_seconds"],
                              policy if uses_rl else None,diverse if uses_rl else (),proposer if uses_rl else None)
            r.update({"lane":lane,"metrics":dict(model.metrics)});core_runs.append(r)
            print("coverage",lane,i,r["status"],r["tiles"],round(r["seconds"],2),flush=True)
        report["core_coverage"]=core_runs;save()
    report["serialized_certificate_audit"]=replay_proofs.audit(prior)
    report["total_seconds"]=time.monotonic()-start
    report["peak_process_memory_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["substitution_status"]="open: inspected abstract boundary/hull types; no exact stationary recursive map"
    report["plane_proof_status"]="open: finite core coverage retains a viable exposed frontier"
    save();print("finished iteration three",round(report["total_seconds"],2),flush=True)

if __name__=="__main__":main()
