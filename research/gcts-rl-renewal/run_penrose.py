"""Cold unmarked rhomb star model and complete-contact learning pilot."""
import hashlib,json,resource,time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import cyclotomic as ring
import learn_sectors,penrose_sectors as p

HERE=Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/"docs/research/gcts-rl-renewal/penrose-001.json"

def main():
    start=time.monotonic()
    report={"date":datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),"initial_marking":None,
            "known_arrows_imported":False,"known_substitution_imported":False,"known_tiling_imported":False,
            "source_sha256":{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob("*.py")},
            "configuration":{"pair_node_limit":1000,"pair_seconds":2,"roots":p.KINDS,
                             "orientations":10,"inventory_aliases":"distinct transformed prototype identities retained"},
            "point_model":{"domain":"Z[zeta_5] x {0,...,9}","capacity":1,
                           "vertices":p.VERTICES,"occupancy":{k:sorted(v) for k,v in p.BASE.items()},
                           "positive_points_per_tile":10,"active_points_per_tile":40,
                           "generation_rule":"every generated vertex-sector obligation explicitly activated as generation-zero root",
                           "target":"complete all sector slots at initial tile/pair vertices; viable whole exposed frontier",
                           "scheduler":"global dead, global forced, earliest generation, initial-core tie preference, degree/key",
                           "arithmetic":"integer rank-four basis; all rotations and scalar marking actions exact",
                           "rollback":"full child snapshots including activation, roots, generations and incidence",
                           "gap":"connected vertex-star complex to plane tiling faithfulness unproved; unrestricted dense module intersections not tested"},
            "dense_support_obstruction":p.dense_support_obstruction()}
    def save():OUTPUT.write_text(json.dumps(report,indent=2)+"\n")
    model=p.Model();samples=[];catalogs={k:p.pair_catalog(model,k) for k in p.KINDS}
    print("cold sector contact catalogs",{k:len(v) for k,v in catalogs.items()},flush=True)
    for kind in p.KINDS:
        for i,key in enumerate(catalogs[kind]):
            samples.append(p.corona(model,kind,key,91000+i,1000,2))
            if (i+1)%40==0:print("star labels",kind,i+1,dict(Counter(s["status"] for s in samples)),flush=True)
    report["pair_labels"]={"catalog_counts":{k:len(v) for k,v in catalogs.items()},
                           "counts":dict(Counter(s["status"] for s in samples)),"samples":samples,
                           "seconds":sum(s["seconds"] for s in samples)}
    save();verify_start=time.monotonic();proof_nodes=positives=0;overlapping_patches=0;geometry_pairs=0
    for i,s in enumerate(samples):
        if s["status"]=="negative":
            ok,n=p.check_failure(model,s["root_kind"],s["second"],s["certificate"]);assert ok;proof_nodes+=n
        elif s["status"]=="positive":
            required={(tuple(v),sector) for v,sector in s["required_points"]}
            assert p.verify_patch(model,s["placements"],required)
            state=p.State()
            for j,key in enumerate(s["placements"]):state.place(model.placement(key),seed=j<2)
            assert all(p.exhaustive_domains(model,state).values());positives+=1
            overlaps=p.geometry_audit(s["placements"]);s["independent_polygon_overlaps"]=overlaps
            overlapping_patches+=bool(overlaps);geometry_pairs+=s["tiles"]*(s["tiles"]-1)//2
        if (i+1)%80==0:print("independent sector check",i+1,flush=True)
    report["independent_audit"]={"positive_witnesses":positives,"negative_tree_nodes":proof_nodes,
                                 "polygon_pairs_checked":geometry_pairs,"patches_with_polygon_overlap":overlapping_patches,
                                 "seconds":time.monotonic()-verify_start}
    marking,summary=learn_sectors.synthesize(samples)
    report["marking"]={**summary,"snapshot_for_inspection_only":{kind:[[q,v] for q,v in sorted(marking[kind].items())] for kind in p.KINDS}}
    if summary["activation_gate_passed"]:
        report["marking"]["transformed_validation"]=learn_sectors.transformed_checks(marking,samples)
    report["root_star_growth"]=[]
    for lane in ("baseline","learned GCTS"):
        if lane=="learned GCTS" and not summary["activation_gate_passed"]:continue
        for i,kind in enumerate(p.KINDS):
            for j in range(3):
                m=p.Model(marking if lane=="learned GCTS" else None)
                r=p.corona(m,kind,seed=92000+10*i+j,node_limit=2000,seconds=5)
                r.update({"lane":lane,"metrics":dict(m.metrics),"independent_polygon_overlaps":p.geometry_audit(r["placements"])})
                report["root_star_growth"].append(r)
    report["total_seconds"]=time.monotonic()-start
    report["peak_process_memory_bytes"]=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["substitution_status"]="open: no learned rhomb hierarchy or inflation rule"
    report["plane_proof_status"]="open: unmarked connected-star problem; no geometric faithfulness theorem or Penrose arrow characterization"
    report["conformance"]={"point_graph_model_explicit":True,"global_scheduler":True,"complete_alignment_inventory":True,
                           "all_generated_zero_slots_activated":True,"base_polygon_predicates":False,
                           "complete_module_coverage_claimed":False,"cold_start":True,
                           "pending":"semantic tests plus complete developed-complex to plane equivalence; Penrose hierarchical subset search"}
    save();print("finished Penrose point pilot",report["pair_labels"]["counts"],summary,"seconds",round(report["total_seconds"],2),flush=True)

if __name__=="__main__":main()
