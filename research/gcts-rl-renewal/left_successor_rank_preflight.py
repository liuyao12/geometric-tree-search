"""Frozen full-universe positional-rank projection preparation, no search."""
import copy,gzip,hashlib,json,resource,time
from pathlib import Path
from left_successor_rank_points import Model

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    began=time.perf_counter();plan=json.loads((OUT/'rank-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('frozen rank preparation source '+p)
    summary=dict(status='preparing',native_queries=0,target_searches=0,variants=[])
    for lane in base['variants']:
        c=load(OUT/(lane+'-reachable-core.json.gz'));admission=json.loads((OUT/(lane+'-admission.json')).read_text());w=load(OUT/(lane+'-reachability.json.gz'));spec=copy.deepcopy(base['case']);spec.update(id='rank-preparation-'+lane,length=plan['length']);m=Model(spec,c,admission,w);record=dict(case=spec,lane=lane,full_retained_model=m.full_record,rank_projected_model=m.record());(OUT/('rank-'+lane+'-model.json.gz')).write_bytes(gzip.compress(json.dumps(record,separators=(',',':')).encode(),mtime=0));row=dict(lane=lane,full_retained_placements=len(m.full_record['placements']),eligible_placements=len(m.cache),removed_placements=len(m.rank_removed),eligible_command_counts=m.record()['rank_projection']['eligible_command_counts'],model_setup_seconds=m.compile_seconds,projection_seconds=m.projection_seconds);summary['variants'].append(row);print(row,flush=True);del m,record,c,w,admission
    summary.update(status='prepared_rank_projection_pending_independent_audit',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scope='Complete positional candidate universe projected by necessary rank conditions, with full original and projected records. No target search, native call or proof path.');(OUT/'rank-preparation.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
