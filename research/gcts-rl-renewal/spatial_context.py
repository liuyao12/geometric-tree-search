"""Context-aware spatial continuations; preserves the original spatial pilot.

Shared base placement identities are context, not new occupancy. A finite
proposal budget can restrict the macro pool only: every legal base move remains
an action, and Graph alone supplies dead/forced/scheduling domains.
"""
import random,time
from collections import Counter,defaultdict
from turtle import Graph,verify_patch,add,sub,SYMMETRIES
from spatial import keys_tuple,moved

class ContextProposer:
    def __init__(self,library,validation_limit=64,seed=0):
        self.limit=validation_limit; self.rng=random.Random(seed)
        self.aligned=defaultdict(dict); self.structural={}
        for motif in library:
            expansion=keys_tuple(motif["expansion"])
            for g in SYMMETRIES:
                seq=moved(expansion,g)
                for o,p in seq:
                    normalized=tuple(sorted((q,sub(tr,p)) for q,tr in seq))
                    self.aligned[o][normalized]=max(self.aligned[o].get(normalized,0),motif.get("count",1))
    def __call__(self,model,state,graph,keys,library,remaining):
        start=time.monotonic(); actions={(k,) for k in keys}; proposals={}
        version=tuple(sorted(model.marking.items()))
        for key in keys:
            for relative,count in self.aligned[key[0]].items():
                expanded=tuple((o,add(p,key[1])) for o,p in relative)
                new=tuple(k for k in expanded if k not in state.selected)
                if len(new)>remaining or len(new)<2: continue
                # Same new identities have identical aggregate interface even
                # when several cluster descriptions include different context.
                if new not in proposals:
                    proposals[new]=(len(expanded)-len(new),count,self.rng.random(),key,relative)
                else:
                    prior=proposals[new]
                    if (len(expanded)-len(new),count)>prior[:2]:
                        proposals[new]=(len(expanded)-len(new),count,prior[2],key,relative)
        ranked=sorted(proposals.items(),key=lambda item:(-item[1][0],-item[1][1],item[1][2]))
        model.metrics["spatial_templates_considered"]+=len(ranked)
        model.metrics["spatial_templates_omitted_by_budget"]+=max(0,len(ranked)-self.limit)
        for expanded,(shared,count,_,key,relative) in ranked[:self.limit]:
            model.metrics["cluster_validation_attempts"]+=1
            ident=(version,relative)
            if ident not in self.structural:
                self.structural[ident]=verify_patch(model,relative)
                model.metrics["spatial_structural_checks"]+=1
            if not self.structural[ident]: continue
            # Aggregate only NEW constituents. No State copy or full-prefix
            # replay is needed for invalid proposals; internal validity above
            # and integer sums/agreement below certify the extension.
            totals=Counter(); marks={}; valid=True
            for k in expanded:
                c=model.placement(k)
                totals.update(dict(c.occupancy))
                for p,v in c.marks:
                    if p in marks and marks[p]!=v: valid=False; break
                    marks[p]=v
                if not valid: break
            if (not valid or any(state.totals.get(p,0)+v>12 for p,v in totals.items())
                or (state.allowed_points is not None and any(p not in state.allowed_points for p in totals))
                or any(p in state.marks and state.marks[p]!=v for p,v in marks.items())): continue
            child=state.copy(); g=graph.copy(); pending=set(expanded); seq=[]
            while pending:
                kind,_,domain=g.decision(child)
                if kind in ("dead","empty"): break
                available=pending.intersection(domain)
                if not available: break
                k=key if not seq else min(available)
                if k not in available: break
                seq.append(k); pending.remove(k); g.update(model,child,child.place(model.placement(k)))
            if len(seq)>1:
                actions.add(tuple(seq)); model.metrics["spatial_shared_context_tiles"]+=shared
                model.metrics["spatial_valid_prefixes"]+=1
        model.metrics["spatial_proposal_microseconds"]+=round((time.monotonic()-start)*1e6)
        return sorted(actions)
