"""Separately declared native resource study with external blank-band growth.

The existing RequestOracle and unchanged persistent microtable interpreter run
the exact frozen requests. Only their already audited initial heap capacity
changes. No search, proof transformation, parser/checker or palette change.
"""
import gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from semantic_inventory_oracle import RequestOracle
from audit_proof_boundary import code_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_certificate_boundary import pin

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal';PARENT=ROOT/'.gcts-active/left-successor-20261011';PRE=PARENT/'workspace-study/attempt-02';OUT=PARENT/'workspace-native';TMP=Path('/private/tmp/gcts-left-successor-workspace-native-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());need(json.loads((PRE/'audit.json').read_text())['status']=='passed_workspace_only_capacity_and_encoding_preflight','complete independent physical-boundary gate')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen native resource source '+p)
    for p,h in plan['input_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen exact resource input '+p)
    micro=load(DOC/'proof-boundary-microcode-001.json.gz');need(pin(micro)==PINNED_MICRO,'same universal palette');preflight=load(PRE/'preflight.json.gz');TMP.mkdir(parents=True,exist_ok=True);start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));oracle=RequestOracle(micro,preflight[0]['enlarged_initial'],TMP/'oracle',TMP/'code.bin',TMP);summary=dict(status='running',observations=[],native_queries=0,compile_and_oracle_setup_seconds=time.perf_counter()-start)
    try:
        for obs in preflight:
            need(time.perf_counter()-began<=plan['ceilings']['between_query_seconds'] and len(oracle.records)<plan['ceilings']['native_queries'],'declared native resource ceiling');q=oracle.request(obs['request'],plan['ceilings']['per_query_micro_steps'],'external_heap_band_growth_same_frozen_candidate');need(q['input_sha256']==obs['enlarged_input_sha256'] and q['request_sha256']==obs['request_sha256'],'actual native input exactly equals independently audited encoding');q.update(limit=plan['ceilings']['per_query_micro_steps'],geometry=dict(heap_band=micro['heap'],original_capacity=obs['original_heap_capacity'],capacity=obs['enlarged_initial']['capacities'][micro['heap']],estimated_required_capacity=obs['required_heap_capacity']),original_heap_unknown_query=obs['query']);save(OUT/'native.json.gz',oracle.records)
            for name in ('input.bin','output.bin'):(OUT/('query-%03d-'%q['id']+name+'.gz')).write_bytes(gzip.compress((TMP/name).read_bytes(),mtime=0))
            metric=dict(query=q['id'],request_sha256=q['request_sha256'],proof_commands=len(q['request']['proof']),native_status=q['result']['status'],native_seconds=q['seconds'],micro_steps=q['result']['micro_steps'],physical_steps=q['result']['physical_steps'],geometry=q['geometry']);summary['observations'].append(metric);summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('WORKSPACE NATIVE CHECKPOINT',json.dumps(metric),flush=True)
        summary.update(status='complete_resource_native_outcomes_pending_independent_replay',scope='Separate enlarged physical workspace, same frozen11/67command requests, unchanged parser/checker/microtable/palette and same20B per-query microstep limit. Neither a new proof search nor a GCTS discovery. All earlier heap/search unknowns remain preserved.')
    finally:
        summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');save(OUT/'native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
