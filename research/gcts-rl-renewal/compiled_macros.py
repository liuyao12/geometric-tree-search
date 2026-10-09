"""Exact reusable representation of the existing boundary proposal relation.

Envelope compilation and trace memoization change neither the proposal pool
nor the singleton graph. This is an optimization, not learned GCTS pruning.
"""
import hashlib,json,time
from collections import defaultdict,OrderedDict
from turtle import SYMMETRIES,add,sub
from spatial import moved,keys_tuple
from boundary_macros import Proposer

def digest(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()

class CompiledProposer:
    def __init__(self,library,universe,limit=8,cache_size=128,shared_prefixes=True):
        start=time.monotonic();self.library=library;self.limit=limit;self.universe=universe
        self.cache_size=cache_size;self.shared_prefixes=shared_prefixes;self.cache=OrderedDict();self.gains={};self.fallback=Proposer(library,limit)
        self.types=universe.types;self.allowed=universe.allowed;self.index=defaultdict(list)
        if len(self.types)!=1 or self.types[0].identity!='base' or self.types[0].marks or self.types[0].expansion!=((0,(0,0,0)),):
            raise ValueError('compiler requires the declared unmarked identity singleton')
        inventory=set(universe.keys);self.inventory=frozenset(inventory);by_orientation=defaultdict(list)
        for key in universe.keys:
            if universe.model.placement(key).expansion!=((key[1],key[2]),):raise ValueError('nonidentity wrapper')
            by_orientation[key[1]].append(key)
        templates={tuple(sorted(moved(keys_tuple(m['expansion']),g))) for m in library for g in SYMMETRIES}
        patches=set()
        for template in sorted(templates):
            o,anchor=template[0]
            for name,orientation,tr in by_orientation[o]:
                offset=sub(tr,anchor);patch=tuple(sorted(('base',q,add(p,offset)) for q,p in template))
                if all(k in inventory for k in patch):patches.add(patch)
        self.patches=tuple(sorted(patches))
        for i,patch in enumerate(self.patches):
            for k in patch:self.index[k].append(i)
        self.index={k:tuple(ids) for k,ids in self.index.items()};self.seconds=time.monotonic()-start
        self.manifest={'patches':len(self.patches),'incidences':sum(map(len,self.index.values())),
                       'indexed_base_poses':len(self.index),'templates':len(templates),
                       'patch_sha256':digest(self.patches),'incidence_sha256':digest(sorted(self.index.items())),
                       'cache_size':cache_size,'shared_prefixes':shared_prefixes,'seconds':self.seconds}

    def fork(self,cache_size,shared_prefixes=True):
        """Share immutable compilation; isolate each lane's request/cache data."""
        out=object.__new__(type(self));out.__dict__=self.__dict__.copy()
        out.cache_size=cache_size;out.shared_prefixes=shared_prefixes;out.cache=OrderedDict();out.gains={}
        out.manifest=self.manifest|{'cache_size':cache_size,'shared_prefixes':shared_prefixes,'seconds':0.}
        return out

    def fingerprint(self,state,keys):
        return (state.required,tuple(sorted(state.totals.items())),tuple(sorted(state.marks.items())),
                tuple(sorted(state.owned_base)),tuple(sorted(state.generations.items())),
                tuple(sorted(state.roots.items())),tuple(sorted(state.selected)),tuple(keys))

    def actions(self,model,state,graph,keys,check=lambda:None):
        start=time.monotonic()
        if tuple(model.types.values())!=self.types or state.allowed_points!=self.allowed:
            raise ValueError('compiled envelope or tile/marking version mismatch')
        # Context wholly outside P can be owned exterior data. The original
        # relation permits it; use that relation rather than omit such patches.
        if any(('base',o,tr) not in self.inventory for o,tr in state.owned_base):
            model.metrics['compiled_exterior_fallbacks']+=1
            return self.fallback.actions(model,state,graph,keys,check)
        signature=self.fingerprint(state,keys);check()
        model.metrics['compiled_trace_seconds']+=time.monotonic()-start
        if signature in self.cache:
            actions,raw_count=self.cache.pop(signature);self.cache[signature]=(actions,raw_count)
            model.metrics['trace_cache_hits']+=1;model.metrics['macro_raw_proposals']+=raw_count
            model.metrics['macro_offered']+=sum(len(a)>1 for a in actions)
            model.metrics['proposal_seconds']+=time.monotonic()-start
            return list(actions)
        model.metrics['trace_cache_misses']+=1;filter_start=time.monotonic()
        if state.required not in self.gains:
            self.gains[state.required]={k:sum(v for p,v in model.placement(k).occupancy if p in state.required) for k in self.universe.keys}
        gains=self.gains[state.required];owned={('base',o,tr) for o,tr in state.owned_base};legal={};raw={}
        for first in keys:
            for i in self.index.get(first,()):
                check();pending=tuple(k for k in self.patches[i] if k not in owned)
                if len(pending)<2:continue
                valid=True
                for k in pending:
                    if k not in legal:
                        legal[k]=state.legal(model.placement(k));model.metrics['compiled_local_legality_tests']+=1
                    if not legal[k]:valid=False;break
                if valid:raw[first,pending]=(sum(gains[k] for k in pending),len(pending))
        model.metrics['compiled_filter_seconds']+=time.monotonic()-filter_start
        rank_start=time.monotonic();chosen=sorted(raw,key=lambda x:(-raw[x][0]/len(x[1]),-raw[x][1],x))[:self.limit]
        model.metrics['compiled_rank_seconds']+=time.monotonic()-rank_start
        validate_start=time.monotonic();actions={(k,) for k in keys};model.metrics['macro_raw_proposals']+=len(raw)
        # Snapshots stored here are immutable during planning. A new prefix
        # gets fresh copies; identical prefixes reuse the exact same graph.
        prefixes={(): (state,graph)}
        for first,pending in chosen:
            check();model.metrics['macro_validations']+=1;trial=state.copy()
            try:
                for key in pending:trial.place(model.placement(key))
            except ValueError:continue
            child,cg=prefixes[()];remaining=set(pending);seq=[]
            while remaining:
                check();kind,_,domain=cg.decision(child)
                if kind in ('dead','empty'):break
                available=remaining.intersection(domain);key=first if not seq else min(available) if available else None
                if key not in available:break
                prefix=tuple(seq)+(key,)
                if self.shared_prefixes and prefix in prefixes:
                    child,cg=prefixes[prefix];model.metrics['shared_prefix_hits']+=1
                else:
                    child=child.copy();cg=cg.copy();cg.update(model,child,child.place(model.placement(key)))
                    if self.shared_prefixes:prefixes[prefix]=(child,cg)
                    model.metrics['macro_validation_moves']+=1
                remaining.remove(key);seq.append(key);model.metrics['macro_validation_steps']+=1
            if len(seq)>1:actions.add(tuple(seq))
        actions=tuple(sorted(actions))
        model.metrics['compiled_validation_seconds']+=time.monotonic()-validate_start
        if self.cache_size:
            self.cache[signature]=(actions,len(raw))
            while len(self.cache)>self.cache_size:self.cache.popitem(last=False)
        model.metrics['macro_offered']+=sum(len(a)>1 for a in actions)
        model.metrics['proposal_seconds']+=time.monotonic()-start
        return list(actions)
