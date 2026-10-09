"""Independently replay every exclusion of the inspected radius-one marking.

Dead leaves need exhaustive enumeration at the stated empty frontier point,
not every other point. Internal nodes still re-enumerate the ENTIRE frontier
to certify global scheduling and complete alternatives. This changes only
certificate validation cost, not the negative search or its inference rules.
"""
import hashlib,json,time
from pathlib import Path
from turtle import *

def point_domain(model,state,p):
    """Fresh exact alignment enumeration, without Graph/candidate indexes."""
    result=set()
    for o,g in enumerate(SYMMETRIES):
        for q in BASE:
            tr=sub(p,transform(q,g)); key=(o,tr)
            if key in state.selected: continue
            if any(state.totals.get(add(transform(r,g),tr),0)+v>12 for r,v in BASE.items()): continue
            if state.allowed_points is not None and any(add(transform(r,g),tr) not in state.allowed_points for r in BASE): continue
            if any((world:=add(transform(r,g),tr)) in state.marks and state.marks[world]!=v for r,v in model.marking.items()): continue
            result.add(key)
    return result

def check_failure(model,second,proof):
    count=0; target=set(rooted(model,second).totals)
    def visit(state,node):
        nonlocal count
        count+=1
        if "dead" in node:
            p=tuple(node["dead"])
            return p in state.frontier() and not point_domain(model,state,p)
        domains=exhaustive_domains(model,state)
        if not domains or any(not cs for cs in domains.values()): return False
        if all(state.totals.get(p,0)==12 for p in target): return False
        forced=sorted(p for p,cs in domains.items() if len(cs)==1)
        p=forced[0] if forced else min(domains,key=lambda p:(state.generations[p],len(domains[p]),p))
        if tuple(node["point"])!=p or node["kind"]!=("forced" if forced else "branch"): return False
        children=node["children"]
        keys=[(c["placement"][0],tuple(c["placement"][1])) for c in children]
        if len(keys)!=len(set(keys)) or set(keys)!=domains[p]: return False
        for c,key in zip(children,keys):
            child=state.copy(); child.place(model.placement(key))
            if not visit(child,c["proof"]): return False
        return True
    try: return visit(rooted(model,second),proof),count
    except (KeyError,TypeError,ValueError,IndexError,RecursionError): return False,count

def main():
    here=Path(__file__).resolve().parent; folder=here.parents[1]/"docs/research/gcts-rl-renewal"
    probe_path=folder/"halo-probe-002.json"; prior_path=folder/"iteration-002.json"
    probe=json.loads(probe_path.read_text()); prior=json.loads(prior_path.read_text())
    assert probe["source_snapshot_sha256"]==hashlib.sha256(prior_path.read_bytes()).hexdigest()
    marking={tuple(p):v for p,v in probe["snapshot_for_inspection_only"]}
    model=Model(); marked=Model(marking); root=rooted(model); mr=rooted(marked)
    candidates=set()
    for p in marking:
        for o,g in enumerate(SYMMETRIES):
            for q in marking: candidates.add((o,sub(p,transform(q,g))))
    rejected={k for k in candidates if root.legal(model.placement(k)) and not mr.legal(marked.placement(k))}
    samples={}
    for s in prior["pair_labels"]["samples"]+probe["samples"]:
        key=(s["second"][0],tuple(s["second"][1])); samples[key]=s
    assert rejected<=samples.keys()
    start=time.monotonic(); nodes=0
    for i,key in enumerate(sorted(rejected)):
        s=samples[key]; assert s["status"]=="negative",(key,s["status"])
        ok,n=check_failure(model,key,s["certificate"]); assert ok,key; nodes+=n
        if (i+1)%100==0: print("independent halo proofs",i+1,"of",len(rejected),flush=True)
    proof_seconds=time.monotonic()-start
    # Explicitly check scalar equivariance. No transformed polygon predicates.
    checks=0
    for g in SYMMETRIES:
        root_marks={transform(p,g):v for p,v in marking.items()}
        root_totals={transform(p,g):v for p,v in BASE.items()}
        for o,tr in rejected:
            h=compose(g,SYMMETRIES[o]); shifted=transform(tr,g)
            assert all(root_totals.get(add(transform(p,h),shifted),0)+v<=12 for p,v in BASE.items())
            assert any((q:=add(transform(p,h),shifted)) in root_marks and root_marks[q]!=v for p,v in marking.items())
            checks+=1
    result={"all_exclusions_independently_verified":True,"canonical_rejected_contacts":len(rejected),
            "mark_only_additional_contacts":probe["additional_disagreeing_contacts"],"negative_proof_nodes":nodes,
            "transformed_exclusion_checks":checks,"proof_seconds":proof_seconds,"seconds":time.monotonic()-start,
            "validation_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope":"redundant for complete unmarked A2 point-model tilings by exhaustive mark-contact exclusion; no existence or plane proof",
            "activation":"not used in iteration-002 search lanes; future marked runs must freshly reproduce or declare reuse"}
    probe["independent_validation"]=result; probe_path.write_text(json.dumps(probe,indent=2)+"\n")
    print("verified extended marking",result,flush=True)

if __name__=="__main__": main()
