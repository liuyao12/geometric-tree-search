"""Inspect extended marking contacts omitted by the t-overlap catalog.

Explicit reused-data control: synthesize radius-one values from the second
cold run's resolved labels, then label additional disagreements UNMARKED.
This probe does not activate the hypothesis and does not claim redundancy.
Unknown limits remain unknown. Full independent negative-proof replay is a
separate required step before a new redundancy claim.
"""
import argparse,hashlib,json,time
from collections import Counter
from pathlib import Path
from turtle import *

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--deepen-unresolved",action="store_true"); args=parser.parse_args()
    here=Path(__file__).resolve().parent
    source=here.parents[1]/"docs/research/gcts-rl-renewal/iteration-002.json"
    output=source.with_name("halo-probe-002.json")
    prior=json.loads(source.read_text()); samples=prior["pair_labels"]["samples"]
    for s in samples: s["second"]=(s["second"][0],tuple(s["second"][1]))
    marking,summary=synthesize(samples,1)
    oracle=Model(); marked=Model(marking); root=rooted(oracle); marked_root=rooted(marked)
    all_keys=set()
    for p in marking:
        for o,g in enumerate(SYMMETRIES):
            for q in marking: all_keys.add((o,sub(p,transform(q,g))))
    old={s["second"] for s in samples}
    keys=sorted(k for k in all_keys if k not in old and root.legal(oracle.placement(k))
                and not marked_root.legal(marked.placement(k)))
    report={"source_snapshot":source.name,"source_snapshot_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "probe_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "turtle_source_sha256":hashlib.sha256((here/"turtle.py").read_bytes()).hexdigest(),
            "cold":False,"provenance":"reuses resolved labels; all additional searches are unmarked",
            "marking_summary":summary,"snapshot_for_inspection_only":[[p,v] for p,v in sorted(marking.items())],
            "additional_disagreeing_contacts":len(keys),"samples":[],
            "scope":"classification probe only; negative certificates await independent replay; hypothesis never activated"}
    start=time.monotonic()
    for i,k in enumerate(keys):
        s=one_corona(oracle,k,180,.75)
        if s["status"]=="positive":
            assert verify_patch(oracle,s["witness"],rooted(oracle,k).totals)
            replay=State()
            for c in s["witness"]: replay.place(oracle.placement(c))
            assert all(exhaustive_domains(oracle,replay).values())
            s["independently_verified_positive"]=True
        report["samples"].append(s)
        if (i+1)%100==0:
            print("halo contacts",i+1,dict(Counter(q["status"] for q in report["samples"])),flush=True)
    report["counts"]=dict(Counter(q["status"] for q in report["samples"]))
    if args.deepen_unresolved:
        for i,s in enumerate(report["samples"]):
            if s["status"]=="unresolved":
                r=one_corona(oracle,s["second"],5000,20)
                r["earlier_attempt"]={"nodes":s["nodes"],"seconds":s["seconds"],"status":s["status"]}
                r["deep_budget"]={"nodes":5000,"seconds":20}
                if r["status"]=="positive":
                    assert verify_patch(oracle,r["witness"],rooted(oracle,s["second"]).totals)
                    replay=State()
                    for k in r["witness"]: replay.place(oracle.placement(k))
                    assert all(exhaustive_domains(oracle,replay).values())
                    r["independently_verified_positive"]=True
                report["samples"][i]=r
                print("deeper contact",i,r["status"],r["nodes"],flush=True)
        report["counts"]=dict(Counter(q["status"] for q in report["samples"]))
    report["seconds"]=time.monotonic()-start
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("finished halo probe",report["counts"],round(report["seconds"],2),flush=True)

if __name__=="__main__": main()
