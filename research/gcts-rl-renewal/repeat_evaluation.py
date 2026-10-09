"""Replace a wall-time pilot affected by simultaneous research jobs.

The artifact keeps the first measurements and accounts for both passes. This
pass reuses exactly the same trained weights and library, resets all search
models/caches/proposers, and runs the matched tile-count lanes sequentially.
No donor or training rerun is needed to address the timing confound.
"""
import hashlib,json,resource,time
from pathlib import Path
from turtle import Model,Policy,growth_search
from spatial_context import ContextProposer

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/"docs/research/gcts-rl-renewal/iteration-003.json"

def main():
    report=json.loads(OUTPUT.read_text());assert report["total_seconds"]
    assert "evaluation_repeat" not in report
    cfg=report["configuration"];policy=Policy();policy.weights.update(report["training"]["weights"])
    library=report["spatial_libraries"]["diversity"]["motifs"]
    marks={name:{tuple(p):v for p,v in pairs} for name,pairs in report["markings"].items()}
    lane_marks={"baseline":None,"compact GCTS":marks["compact"],"exterior GCTS":marks["exterior"],
                "RL":None,"exterior GCTS+RL":marks["exterior"]}
    original_sha=hashlib.sha256(OUTPUT.read_bytes()).hexdigest();original=report["evaluation"]
    start=time.monotonic();runs=[]
    for lane,marking in lane_marks.items():
        for i in range(cfg["evaluation_starts"]):
            model=Model(marking);uses_rl="RL" in lane
            proposer=ContextProposer(library,cfg["macro_validation_limit"],84000+i)
            r=growth_search(model,84000+i,cfg["evaluation_target"],cfg["node_limit"],cfg["seconds"],
                            policy if uses_rl else None,library if uses_rl else (),None,proposer if uses_rl else None)
            r.update({"lane":lane,"metrics":dict(model.metrics)});runs.append(r)
            print("sequential repeat",lane,i,r["status"],r["tiles"],round(r["seconds"],2),flush=True)
    report["evaluation"]=runs
    report["evaluation_repeat"]={"prior_artifact_sha256":original_sha,"prior_runs":original,
                                 "reason":"initial tile-count pass overlapped the Penrose pilot and semantic tests; replaced to remove known CPU contention",
                                 "seconds":time.monotonic()-start,"searches_sequential":True,
                                 "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                 "scope":"same frozen weights, library, configurations and seeds; fresh search caches"}
    report["total_seconds"]+=report["evaluation_repeat"]["seconds"]
    report["peak_process_memory_bytes"]=max(report["peak_process_memory_bytes"],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    OUTPUT.write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":main()
