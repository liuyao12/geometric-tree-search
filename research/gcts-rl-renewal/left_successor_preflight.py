"""Bounded complete-catalog growth measurements before native admission."""
import collections,gzip,hashlib,json,resource,time
from pathlib import Path
from left_successor_catalog import core,primitive_stream,prospective_points
from certificate_boundary_search import canonical
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';OLD=ROOT/'.gcts-active/induction-receptors-20261011'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def check(plan,began,bytes_count=0):
    if time.perf_counter()-began>plan['ceilings']['preflight_seconds']:raise TimeoutError('unknown_preparation_time_budget')
    if bytes_count>plan['ceilings']['primitive_uncompressed_bytes']:raise MemoryError('unknown_preparation_output_budget')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>plan['ceilings']['rss_bytes']:raise MemoryError('unknown_preparation_memory_budget')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    for path,h in plan['source_sha256'].items():
        if sha(ROOT/path)!=h:raise ValueError('frozen preflight source '+path)
    q=load(OLD/'compaction-native.json.gz')[1];audit=json.loads((OLD/'compaction-audit.json').read_text());recovery=json.loads((OLD/'recovery-audit.json').read_text());prior=json.loads((OLD/'attempt-01/audit.json').read_text())
    if q['result']['status']!='accepted' or any(a['status']!='passed' for a in (audit,recovery,prior)) or q['request_sha256']!=plan['transferred_request_sha256']:raise ValueError('transfer requires actually searched whole-native theorem and complete independent audits')
    if q['request']['theory']!=plan['case']['theory']:raise ValueError('transfer theory changed')
    name='searchedZeroLeft'+q['request_sha256'];entry=dict(name=name,conclusion=q['request']['target'],proof=q['request']['proof'],theory=q['request']['theory'],request_sha256=q['request_sha256'],origin='actually-searched-and-native-checked-zero-left-theorem',authored_interfaces_are_not_learned=True)
    result=dict(status='running',native_queries=0,variants=[],transfer=dict(request_sha256=q['request_sha256'],proof_commands=len(entry['proof']),theory_unchanged=True,all_original_audits='passed',historical_full_cost_ledger='.gcts-active/induction-receptors-20261011/integration.json'))
    (OUT/'transfer.json').write_text(json.dumps(entry,indent=2)+'\n')
    try:
        for lane in plan['variants']:
            stage=time.perf_counter();c=core(plan['case'],[entry] if lane=='with-searched-zero-left' else []);save(OUT/(lane+'-core.json.gz'),c);check(plan,began)
            counts=collections.Counter();byte_count=0;digest=hashlib.sha256();stream_stage=time.perf_counter()
            with gzip.GzipFile(filename=str(OUT/(lane+'-primitive.jsonl.gz')),mode='wb',mtime=0) as f:
                for j,p in enumerate(primitive_stream(c)):
                    word=canonical(p)+b'\n';f.write(word);digest.update(word);counts[p['rule']]+=1;byte_count+=len(word)
                    if j%1024==0:check(plan,began,byte_count)
            check(plan,began,byte_count)
            definitions=c['definitions'];sizes=[len(canonical(d)) for d in definitions];commands=[len(d['proof']) for d in definitions]
            # Independent logical replay is a preparation audit only. There is
            # no forged native-admission token and no target search yet.
            host_stage=time.perf_counter()
            for j,d in enumerate(definitions):
                taut=['imp',['bot'],['bot']];request=dict(protocol='gcts-fol-1',theory=plan['case']['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
                if whole_replay(request)['status']!='accepted':raise ValueError('local definition host audit')
                if j%32==0:check(plan,began,byte_count)
            stats=dict(lane=lane,terms=len(c['terms']),basis_formulas=len(c['basis']),interfaces=len(c['rules']),local_definitions=len(definitions),local_commands=sum(commands),max_local_commands=max(commands),local_definition_json_bytes=sum(sizes),max_local_definition_json_bytes=max(sizes),core_gzip_bytes=(OUT/(lane+'-core.json.gz')).stat().st_size,primitive_counts=dict(counts),primitive_uncompressed_bytes=byte_count,primitive_gzip_bytes=(OUT/(lane+'-primitive.jsonl.gz')).stat().st_size,primitive_stream_sha256=digest.hexdigest(),core_seconds=c['build_seconds'],primitive_stream_seconds=host_stage-stream_stage,host_definition_audit_seconds=time.perf_counter()-host_stage,whole_preflight_seconds=time.perf_counter()-stage,prospective_point_counts=[prospective_points(c,n) for n in plan['prospective_lengths']],peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,authority='host-audit-only; native admission not performed')
            result['variants'].append(stats);(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(stats),flush=True)
        result.update(status='complete_preflight_not_native_admitted',seconds=time.perf_counter()-began,scope='Complete declared five-node contextual grammar and every exposed primitive instance were generated, no top-k or sampled catalog. No native model or target search is authorized until complete local admission. Two semantic inventories are explicit; they are not an equal-inventory speed comparison. Future cached-vs-fresh admission controls must use the same transferred inventory.')
    except (TimeoutError,MemoryError) as e:
        result.update(status=str(e),seconds=time.perf_counter()-began);raise
    finally:(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
