"""Reject known-dead cluster endpoints, retaining every singleton action.

This is an analytic proposal filter using the complete point graph, not GCTS
marking learning. Fixed-boundary dead-prefix certificates are context scoped.
"""
import time
from collections import OrderedDict
from region_tiles import packed_state

class ViableProposer:
    def __init__(self,compiled,cache_size=128,sample_limit=16):
        self.compiled=compiled;self.cache_size=cache_size;self.cache=OrderedDict()
        self.samples=[];self.sample_limit=sample_limit
    def actions(self,model,state,graph,keys,check=lambda:None):
        actions=self.compiled.actions(model,state,graph,keys,check)
        start=time.monotonic();signature=self.compiled.fingerprint(state,keys);check()
        if signature in self.cache:
            result,rejected=self.cache.pop(signature);self.cache[signature]=(result,rejected)
            model.metrics['viability_cache_hits']+=1;model.metrics['dead_macro_endpoints_rejected']+=rejected
            model.metrics['proposal_seconds']+=time.monotonic()-start
            return list(result)
        result=[];rejected=0;prefixes={(): (state,graph)}
        for action in actions:
            if len(action)==1:result.append(action);continue
            child,cg=state,graph;prefix=()
            for k in action:
                check();prefix=prefix+(k,)
                if prefix not in prefixes:
                    child=child.copy();cg=cg.copy()
                    kind,p,domain=cg.decision(child)
                    if k not in domain:raise AssertionError('unscheduled viability replay')
                    cg.update(model,child,child.place(model.placement(k)));prefixes[prefix]=(child,cg)
                    model.metrics['viability_graph_updates']+=1
                else:child,cg=prefixes[prefix]
            kind,p,domain=cg.decision(child);model.metrics['viability_endpoints_checked']+=1
            if kind=='dead':
                rejected+=1
                if len(self.samples)<self.sample_limit:
                    self.samples.append({'boundary':model.boundary.packed(),'context':packed_state(state),'action':action,
                                         'endpoint':packed_state(child),'certificate':{'dead':p},
                                         'scope':'fixed prefix, fixed required set and support envelope; no claim about this shape in another context'})
            else:result.append(action)
        result=tuple(result)
        if self.cache_size:
            self.cache[signature]=(result,rejected)
            while len(self.cache)>self.cache_size:self.cache.popitem(last=False)
        model.metrics['dead_macro_endpoints_rejected']+=rejected
        model.metrics['viability_seconds']+=time.monotonic()-start
        model.metrics['proposal_seconds']+=time.monotonic()-start
        return list(result)
