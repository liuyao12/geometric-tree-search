"""Freeze terminal-failure preservation and canonical wire adversarial repair."""
import ast,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def pin(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def rel(p):return str(p.relative_to(ROOT))
def main():
    began=time.perf_counter();dest=HERE/'plan-v2.json'
    if dest.exists():raise ValueError('repair already frozen')
    old=json.loads((HERE/'plan-v1.json').read_text());cost=json.loads((HERE/'stage-costs-v1.json').read_text())
    if cost['status']!='unknown_or_failed' or cost['stages'][0]['exit_code']!=0 or cost['stages'][1]['exit_code']!=1 or not all(s['child_wait_reaped'] for s in cost['stages']):raise ValueError('authoritative failure and terminal evidence')
    sources=sorted(HERE.glob('hilbert_transport_*_v2.py'))
    if len(sources)!=5:raise ValueError('all five repair sources before freeze')
    for p in sources:ast.parse(p.read_text())
    inputs={rel(p):pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p not in sources}
    plan=dict(version='hilbert-transport-catalog-plan-2-wire-normalization-repair',status='frozen_before_repair',source_pins={rel(p):pin(p) for p in sources},inputs=inputs,
        original_plan_sha256=pin(HERE/'plan-v1.json')['sha256'],original_catalog_sha256=pin(HERE/'catalog-v1.json.gz')['sha256'],
        original_catalog_production_seconds=cost['stages'][0]['process_wall_seconds'],failed_audit_process_seconds=cost['stages'][1]['process_wall_seconds'],
        failed_audit_external_max_sampled_rss_bytes=max(s['rss_bytes'] for s in cost['stages'][1]['rss_samples']),failed_audit_kernel_peak='unavailable',
        cause='In-memory shared-container alias action changed several model fields in some v1 mutants; independent JSON decoding removed alias identity. Catalog/domain checks completed before actual mutant SHA reconciliation failed.',
        repair='Only regenerated19corruption inputs use canonical JSON round-trip before field mutation; each exact payload saved and independently reconstructed/byte-content checked. Full independent catalog/model/graph/tiny replay still required. Original catalog and all completed producer observations stay unchanged.',
        budgets=dict(production_total_wall_seconds=180,audit_total_wall_seconds=180,repair_production_seconds=180-cost['stages'][0]['process_wall_seconds'],repair_audit_seconds=180-cost['stages'][1]['process_wall_seconds'],host_ceiling_bytes=512*1024*1024),
        resource_scope='Original failed audit final kernel peak unavailable and memory gate unestablished; all actual time costs retained. New repair/replay enforce strict512MiB with same fail-closed owned-child RSS/time monitoring, childSIGALRM and final kernel peak. No unobserved prior memory peak invented.',
        unchanged='All171definitions/216aliases/1768prototypes/8840rawalignments/4430orderedbindings/1492initialdomains, point compiler, authority epoch, scheduler metadata and complete fallback are frozen; no theorem path/search/native admission or existing-engine activation.',
        source_plan_inputs=old['inputs'],native_queries=0,target_searches=0,existing_engine_activation=False,declaration_seconds_before_plan_write=time.perf_counter()-began)
    dest.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan_sha256=pin(dest)['sha256'],sources=len(sources),inputs=len(inputs),budgets=plan['budgets'])))
if __name__=='__main__':main()
