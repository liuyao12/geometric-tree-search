"""One fresh process per observed representation/ordering lane.

Receives admitted syntax/lemma context and a compact negative constraint packet,
never a target proof, a searched path, or a teacher witness. Peak RSS is the
whole process through the search, not an isolated engine allocation estimate.
"""
import gzip,json,resource,sys,time
from pathlib import Path
from semantic_receptor_points import Model
from semantic_inventory_search import search
from boundary_reuse_constraints import PointModel,DirectModel,original_record


def main():
    began=time.perf_counter();job=json.loads(Path(sys.argv[1]).read_text())
    base=Model(job['case'],job['compiled'],job['inventory']);stage=time.perf_counter()
    layer=job['layer']
    if layer=='point':model=PointModel(base,job['constraints'],job['transfer_certificate'])
    elif layer=='direct':model=DirectModel(base,job['constraints'],job['transfer_certificate'])
    elif layer=='original':model=base
    else:raise ValueError('unknown representation')
    representation_seconds=time.perf_counter()-stage;setup_seconds=time.perf_counter()-began
    if layer=='direct' and job['mode']!='base':raise ValueError('direct comparison deliberately uses base ordering')
    out=search(model,job['mode'],weights=job['weights'] if job['mode']=='learned' else None,
        stochastic=False,seed=66000,**job['limits'])
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform!='darwin':rss*=1024
    if layer=='direct':
        # In this finite unit-occupancy universe, the Graph fallback reason
        # occurs exactly when a still-required original candidate is rejected
        # by the explicit direct conjunction predicate. Ordinary t/m rejection
        # already has separate capacity/marking/selected reasons.
        out['graph_metrics']['removed_incidences:direct_conjunction']=out['graph_metrics'].pop('removed_incidences:completed_frontier',0)
    result=dict(layer=layer,mode=job['mode'],repetition=job['repetition'],search=out,
        model=original_record(model),setup_seconds=setup_seconds,
        representation_seconds=representation_seconds,peak_rss_bytes=int(rss),
        scope='Fresh process; admitted context and failure packet explicitly reused. Search clock includes graph construction and complete trace collection. Setup excludes the later native check; peak RSS covers loading, model construction and search, not just plugin memory.')
    Path(sys.argv[2]).write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0))
    print(layer,job['mode'],out['status'],out['metrics'].get('attempts',0),flush=True)


if __name__=='__main__':main()
