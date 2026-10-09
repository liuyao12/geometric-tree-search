"""Equality synthesis from ALL resolved two-rhomb star completion tests.

All forty vertex-sector slots per prototype are eligible, including t=0.
Unknown labels impose no constraint. Complete-sample learning and independent
proof replay gate activation; scores may fail, in which case nothing is used.
"""
from collections import Counter
import cyclotomic as ring
import penrose_sectors as p

class Equality:
    def __init__(self,points):self.parent={q:q for q in points}
    def find(self,q):
        while self.parent[q]!=q:
            self.parent[q]=self.parent[self.parent[q]];q=self.parent[q]
        return q
    def union(self,a,b):
        a,b=self.find(a),self.find(b);self.parent[max(a,b)]=min(a,b)

def overlaps(sample):
    kind=sample["root_kind"];other,r,tr=sample["second"]
    first={(v,s) for v in p.VERTICES[kind] for s in range(10)}
    return [((kind,world[0],world[1]),(other,v,s))
            for v in p.VERTICES[other] for s in range(10)
            if (world:=p.point_action((v,s),r,tuple(tr))) in first]

def synthesize(samples):
    eq=Equality((kind,v,s) for kind in p.KINDS for v in p.VERTICES[kind] for s in range(10))
    history=[];resolved=[]
    for sample in samples:
        if sample["status"]=="unresolved":continue
        if sample["status"]=="positive":
            for a,b in overlaps(sample):eq.union(a,b)
        resolved.append(sample)
        negatives=[s for s in resolved if s["status"]=="negative"]
        history.append({"resolved":len(resolved),"components":len({eq.find(q) for q in eq.parent}),
                        "negatives":len(negatives),
                        "rejected":sum(any(eq.find(a)!=eq.find(b) for a,b in overlaps(s)) for s in negatives)})
    assigned=set()
    for sample in samples:
        if sample["status"]=="negative":
            for a,b in overlaps(sample):
                if eq.find(a)!=eq.find(b):assigned.update((a,b));break
    colors={q:i for i,q in enumerate(sorted({eq.find(q) for q in assigned}))}
    marking={kind:{} for kind in p.KINDS}
    for kind,v,s in assigned:marking[kind][v,s]=colors[eq.find((kind,v,s))]
    def accepted(sample):
        return all((a[1],a[2]) not in marking[a[0]] or (b[1],b[2]) not in marking[b[0]]
                   or marking[a[0]][a[1],a[2]]==marking[b[0]][b[1],b[2]] for a,b in overlaps(sample))
    counts=Counter(s["status"] for s in samples)
    positives=sum(s["status"]=="positive" and accepted(s) for s in samples)
    negatives=sum(s["status"]=="negative" and not accepted(s) for s in samples)
    gate=not counts["unresolved"] and positives==counts["positive"] and (not counts["negative"] or negatives>counts["negative"]/2)
    return marking,{"history":history,"support_slots":80,"assigned":len(assigned),"free":80-len(assigned),
                    "colors":len(colors),"positives":counts["positive"],"positive_accepted":positives,
                    "negatives":counts["negative"],"negative_rejected":negatives,"unresolved":counts["unresolved"],
                    "activation_gate_passed":gate,"scope":"two-prototype scalar equality hypothesis on all vertex-sector slots"}

def transformed_checks(marking,samples):
    model=p.Model(marking);checks=0;rejected=0
    for sample in samples:
        root=p.rooted(model,sample["root_kind"])
        key=sample["second"];key=key[0],key[1],tuple(key[2]);illegal=not root.legal(model.placement(key))
        if illegal:
            assert sample["status"]=="negative";rejected+=1
        for r in range(10):
            state=p.State();state.place(model.placement((sample["root_kind"],r,ring.ZERO)),seed=True)
            transformed=key[0],(key[1]+r)%10,p.rotate(key[2],r)
            assert (not state.legal(model.placement(transformed)))==illegal;checks+=1
    return {"transformed_checks":checks,"canonical_rejected":rejected,
            "complete_mark_overlap_catalog":True,
            "conditional_scope":"with replayed negative trees, redundant for complete connected vertex-star point tilings; geometric faithfulness open"}
