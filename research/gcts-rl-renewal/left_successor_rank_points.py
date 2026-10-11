"""Necessary fixed-point rank bounds projected through the full point universe.

Zero-based proof row j can contain only a formula of minimum derivation rank
at most j. Every strict-prior source s must likewise support its input formula
by rank s. These are necessary conditions, not a target backcone or proof path.
All full placements and excluded-key reasons remain in the projection record.
"""
import collections,hashlib,time
from certificate_boundary_search import canonical
from left_successor_points import Model as Base

class Model(Base):
    def __init__(self,spec,catalog,admission,witness):
        if witness['basis_sha256']!=hashlib.sha256(canonical(catalog['basis'])).hexdigest():raise ValueError('complete rank basis binding')
        super().__init__(spec,catalog,admission);start=time.perf_counter();self.full_record=super().record();self.rank_witness_sha256=catalog['structural_pruning']['witness_sha256'];ranks={canonical(f):r for f,r in zip(catalog['basis'],witness['formula_ranks'])};removed=[];kept=set()
        for key,meta in sorted(self.metadata.items()):
            j=key[0];inference=meta.get('inference');mode=meta.get('mode',0);inference=inference if inference is not None else mode-1 if mode else None;reason=[]
            if inference is not None:
                r=self.rules[inference];out=ranks[canonical(r['conclusion'])];prem=[ranks[canonical(p)] for p in r['premises']]
                if out is None or out>j:reason.append(dict(bound='output-rank-at-most-row',rank=out,row=j))
                for role,q in enumerate(prem):
                    if q is None or q>=j:reason.append(dict(bound='premise-rank-below-row',input=role,rank=q,row=j))
            if meta['kind']=='inference_input':
                p=self.rules[inference]['premises'][meta['input']];rank=ranks[canonical(p)];source=meta['source']
                if rank is None or rank>source:reason.append(dict(bound='input-rank-at-most-source-row',rank=rank,source=source))
            if reason:removed.append(dict(key=key,reasons=reason))
            else:kept.add(key)
        self.rank_removed=removed;self.cache={k:v for k,v in self.cache.items() if k in kept};self.metadata={k:v for k,v in self.metadata.items() if k in kept};self.align_cache={p:tuple(k for k in ks if k in kept) for p,ks in self.align_cache.items()};self.dependencies=collections.defaultdict(set,{p:keys&kept for p,keys in self.dependencies.items()});self.projection_seconds=time.perf_counter()-start;self.compile_seconds+=self.projection_seconds
    def record(self):
        value=super().record();value.update(rank_projection=dict(full_retained_placement_count=len(self.full_record['placements']),eligible_placement_count=len(self.cache),removed=self.rank_removed,witness_sha256=self.rank_witness_sha256,projection_seconds=self.projection_seconds,eligible_command_counts=[len(self.align_cache[4*j,0]) for j in range(self.spec['length'])],scope='Every full placement was classified by necessary minimum-rank bounds. The declared full positional command domains remain for audit; actual complete eligible graph uses the projected placements. Every finite strict-prior proof word is preserved. No target backcone or selected proof path.'));return value
