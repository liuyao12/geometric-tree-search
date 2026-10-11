"""Separate frozen rank phase using the unchanged checkpointed runner.

Only the input point-model factory and private output directory are adapted.
The complete scheduler, decoding, native checker and generic whole compilation
are unchanged. The original four unknown search observations are not replaced.
"""
import gzip,json
from pathlib import Path
import left_successor_search as runner
from left_successor_rank_points import Model

PARENT=runner.OUT
def ranked(spec,catalog,admission):
    for lane in ('without-transfer','with-searched-zero-left'):
        p=PARENT/(lane+'-reachability.json.gz');w=json.loads(gzip.decompress(p.read_bytes()))
        if catalog['structural_pruning']['witness_sha256']==admission['pruning_witness_sha256'] and w['basis_sha256']==catalog_basis(catalog):return Model(spec,catalog,admission,w)
    raise ValueError('no exact rank witness')
def catalog_basis(c):
    import hashlib
    from certificate_boundary_search import canonical
    return hashlib.sha256(canonical(c['basis'])).hexdigest()
def main():
    if json.loads((PARENT/'rank-audit.json').read_text())['status']!='passed_complete_rank_projection_and_language_preservation':raise ValueError('complete independent rank projection gate')
    runner.OUT=PARENT/'rank-search';runner.TMP=Path('/private/tmp/gcts-left-successor-rank-search-20261011');runner.Model=ranked;runner.main()
if __name__=='__main__':main()
