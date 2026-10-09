"""Independent post-run interface/hierarchy and finite polygon audit.

Reads an inspection artifact. Does not supply learner labels, policy features,
placement legality, or proposal ordering. No Model/State/Graph paths are used
for the exported aggregate point checks.
"""
import hashlib,json,time
from collections import Counter
from pathlib import Path
from turtle import BASE,VERTICES,SYMMETRIES,transform,add
from audit_geometry import audit as polygon_audit

def aggregate(keys,marking):
    seen=set(); totals=Counter(); marks={}
    for o,tr in keys:
        key=(o,tuple(tr))
        if key in seen: raise ValueError("duplicate placement")
        seen.add(key); g=SYMMETRIES[o]
        for p,v in BASE.items(): totals[add(transform(p,g),tr)]+=v
        for p,v in marking.items():
            q=add(transform(p,g),tr)
            if q in marks and marks[q]!=v: raise ValueError("marking disagreement")
            marks[q]=v
    if any(v>12 for v in totals.values()): raise ValueError("excess occupancy")
    return totals,marks

def check_interface(keys,marking,reported):
    try:
        totals,marks=aggregate(keys,marking)
        def pairs(entries): return {tuple(p):v for p,v in entries}
        return (reported["tiles"]==len(keys) and reported["units"]==sum(totals.values())
            and reported["completed_points"]==sum(v==12 for v in totals.values())
            and len(reported["occupancy"])==len(totals) and pairs(reported["occupancy"])==totals
            and len(reported["marking"])==len(marks) and pairs(reported["marking"])==marks
            and reported["frontier"]==[[list(p),v,12-v] for p,v in sorted(totals.items()) if v<12])
    except (KeyError,TypeError,ValueError,IndexError): return False

def check_hierarchy(marking,h):
    try:
        keys=h["placements"]; n=len(keys); full,_=aggregate(keys,marking); previous=None
        for level in h["levels"]:
            covered=[]; summed=Counter()
            for group in level["groups"]:
                ids=group["base_ids"]
                if any(type(i) is not int or not 0<=i<n for i in ids): return False
                if len(ids)!=len(set(ids)): return False
                covered+=ids; selected=[keys[i] for i in ids]
                if not check_interface(selected,marking,group["interface"]): return False
                summed.update(aggregate(selected,marking)[0])
                if previous is not None:
                    children=group["children"]
                    if len(children)!=len(set(children)): return False
                    if any(type(c) is not int or not 0<=c<len(previous) for c in children): return False
                    if sorted(i for c in children for i in previous[c]["base_ids"])!=sorted(ids): return False
            if sorted(covered)!=list(range(n)) or summed!=full: return False
            previous=level["groups"]
        return bool(previous)
    except (KeyError,TypeError,ValueError,IndexError): return False

def audit(data):
    start=time.monotonic()
    marking={tuple(p):v for p,v in data["marking"]["snapshot_for_inspection_only"]}
    motifs=data["spatial_library"]["motifs"]
    assert all(check_interface(m["expansion"],marking,m["interface"]) for m in motifs)
    hs=data["hierarchies"]["samples"]
    assert hs and all(check_hierarchy(marking,h) for h in hs)
    # Change an aggregate value and reuse a child; both must be detected.
    tampered=json.loads(json.dumps(hs[0])); tampered["levels"][0]["groups"][0]["interface"]["occupancy"][0][1]+=1
    assert not check_hierarchy(marking,tampered)
    tampered_child=json.loads(json.dumps(hs[0])); parent=tampered_child["levels"][1]["groups"][0]
    parent["children"].append(parent["children"][0]); assert not check_hierarchy(marking,tampered_child)
    point_seconds=time.monotonic()-start
    geometric=polygon_audit({"point_model":{"vertices":VERTICES},"pair_catalog":{"samples":data["pair_labels"]["samples"]},
                             "evaluation":data["evaluation"]+[{**r,"lane":"donor"} for r in data["spatial_library"]["donors"]]})
    return {"independent_interfaces":len(motifs),"independent_hierarchies":len(hs),
            "checked_group_levels":sum(len(h["levels"]) for h in hs),"point_seconds":point_seconds,
            "tampered_interface_rejected":True,"tampered_child_rejected":True,
            "geometry":geometric,"seconds":time.monotonic()-start,
            "audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope":"finite exact interfaces and disjoint hierarchy partitions; polygon non-overlap only; no recursive coverage proof"}

if __name__=="__main__":
    path=Path(__file__).resolve().parents[2]/"docs/research/gcts-rl-renewal/iteration-002.json"
    data=json.loads(path.read_text()); result=audit(data); data["independent_audit"]=result
    path.write_text(json.dumps(data,indent=2)+"\n")
    print({k:v for k,v in result.items() if k!="geometry"})
    print("finite polygon overlaps",sum(len(r["overlapping_pairs"]) for r in result["geometry"]["evaluation_runs"]))
