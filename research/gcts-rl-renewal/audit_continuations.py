"""Independent finite aggregates, partition and core-coverage replay for 003."""
import hashlib,json,time
from pathlib import Path
from turtle import Model,State,VERTICES,exhaustive_domains
from audit_spatial import aggregate,check_interface,check_hierarchy
from audit_geometry import audit as polygon_audit
from coverage import hexagon

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/"docs/research/gcts-rl-renewal/iteration-003.json"

def audit(data):
    start=time.monotonic()
    marks={name:{tuple(p):v for p,v in pairs} for name,pairs in data["markings"].items()}
    exterior=marks["exterior"];interfaces=levels=0
    for name in ("frequency","diversity"):
        for m in data["spatial_libraries"][name]["motifs"]:
            assert check_interface(m["expansion"],exterior,m["interface"]);interfaces+=1
        for h in data["grammar_inspection"][name]["samples"]:
            assert check_hierarchy(exterior,h);levels+=len(h["levels"])
    checks=[]
    for run in data["core_coverage"]:
        marking=exterior if "exterior" in run["lane"] else marks["compact"] if "compact" in run["lane"] else {}
        totals,_=aggregate(run["placements"],marking)
        for a,b in zip(run["checkpoints"],run["checkpoints"][1:]):
            assert b["placements"][:len(a["placements"])]==a["placements"]
        for c in run["checkpoints"]:
            subtotal,_=aggregate(c["placements"],marking)
            core=hexagon(c["radius"])
            assert len(core)==c["required_core_points"] and all(subtotal.get(p,0)==12 for p in core)
            model=Model(marking);state=State()
            for i,key in enumerate(c["placements"]):state.place(model.placement(key),seed=i==0)
            # Independent domain re-enumeration needs the final root set for
            # viability, not the historical generation sequence for ordering.
            state.roots.update({p:0 for p in core})
            assert all(exhaustive_domains(model,state).values())
        if run["status"]=="consistent_finite_patch_with_core_coverage":
            assert len(run["checkpoints"])==len(run["radii"])
            assert all(totals.get(p,0)==12 for p in hexagon(run["radii"][-1]))
        checks.append({"lane":run["lane"],"seed":run["seed"],"checkpoint_count":len(run["checkpoints"]),
                       "required_core_points":run["checkpoints"][-1]["required_core_points"] if run["checkpoints"] else None,
                       "exact_aggregate_checked":True,"successful_checkpoint_frontiers_reenumerated":True})
    point_seconds=time.monotonic()-start
    runs=data["evaluation"]+data["core_coverage"]+[{**r,"lane":"donor"} for r in data["spatial_libraries"]["donors"]]
    geometric=polygon_audit({"point_model":{"vertices":VERTICES},"pair_catalog":{"samples":[]},"evaluation":runs})
    return {"interfaces":interfaces,"hierarchy_levels":levels,"core_runs":checks,"point_seconds":point_seconds,
            "geometry":geometric,"seconds":time.monotonic()-start,
            "audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope":"finite core sums, retained checkpoint prefixes, full exposed-frontier viability, partition aggregates, polygon non-overlap; no plane certificate"}

if __name__=="__main__":
    data=json.loads(OUTPUT.read_text());result=audit(data);data["independent_audit"]=result
    OUTPUT.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("geometry","core_runs")},indent=2))
    print("audited",len(result["core_runs"]),"core runs; geometry non-overlap",result["geometry"]["all_reported_patches_nonoverlapping"])
