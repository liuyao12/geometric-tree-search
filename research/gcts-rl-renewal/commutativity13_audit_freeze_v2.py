"""Freeze lifetime-only audit repair; preserve failed v1 and original ceilings."""
import datetime
import hashlib
import json
import zipfile
from pathlib import Path
from commutativity13_phase_freeze import closure
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.gcts-active/commutativity13-20261011'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=json.loads((OUT/'preflight-audit-plan.json').read_text());failed=json.loads((OUT/'preflight-audit.json').read_text())
    if failed['status']!='unknown_complete_preflight_audit_resource_budget':raise ValueError('exact historical gate')
    for p,v in {**old['source_sha256'],**old['input_sha256']}.items():
        if h(ROOT/p)!=v:raise ValueError('v1 exact freeze '+p)
    path=OUT/'preflight-audit-plan-v2.json'
    if path.exists():raise ValueError('immutable v2 freeze already exists')
    inputs=dict(old['input_sha256'])
    for n in ['preflight-audit-plan.json','preflight-audit.json','fixed-r1-projection-audit.json','fixed-r2-projection-audit.json','preflight-audit.log']:
        inputs[str((OUT/n).relative_to(ROOT))]=h(OUT/n)
    source={**old['source_sha256'],**closure(['commutativity13_audit_v2','commutativity13_audit_freeze_v2'])}
    zpath=OUT/'preflight-audit-sources-v2.zip'
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in source:
            if p.endswith('.py'):z.write(ROOT/p,p)
    source[str(zpath.relative_to(ROOT))]=h(zpath)
    plan=dict(status='frozen_lifetime_only_complete_audit_repair',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,input_sha256=inputs,
              prior_audit_seconds=failed['seconds'],prior_peak_rss_bytes=failed['peak_rss_bytes'],cumulative_audit_seconds=300,rss_bytes=536870912,
              amendment='Release complete static/value witnesses before fixture replay. Repeat all589oldactualevent checks, all19848placements/18480family bindings, exact canonical model and all four complete fixture trees. Failedv1 preserved; no producer restart/trace rewrite/targetsearch/nativequery/resourcewidening.',
              authorization='Parent authorized lifetime-only repair and cumulative original300s audit gate after v1memoryunknown.')
    path.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan_sha256=h(path),sources=len(source),inputs=len(inputs),remaining_audit_seconds=300-failed['seconds'])))
if __name__=='__main__':main()
