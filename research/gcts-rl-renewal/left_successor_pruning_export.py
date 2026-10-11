"""Scoped public evidence for audited finite-grammar pruning, not target success."""
import gzip,hashlib,json,shutil,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    audit=json.loads((OUT/'reachability-audit.json').read_text());grammar=json.loads((OUT/'audit.json').read_text());compact=json.loads((OUT/'compaction-preparation-audit.json').read_text())
    if audit['status']!='passed_finite_grammar_structural_pruning' or grammar['status']!='passed_preparation_audit_only' or compact['status']!='passed_compaction_preparation_audit_only':raise ValueError('complete preparation/pruning gates')
    names=['plan.json','summary.json','audit-plan.json','audit.json','compaction-preparation-plan.json','compaction-preparation.json','compaction-audit-plan.json','compaction-preparation-audit.json','reachability-plan.json','reachability-summary.json','reachability-audit-plan.json','reachability-audit.json','transfer.json']+[lane+'-'+suffix for lane in ('without-transfer','with-searched-zero-left') for suffix in ('core.json.gz','compact-core.json.gz','primitive.jsonl.gz','reachability.json.gz','reachable-core.json.gz')];files=[]
    for name in names:
        target=DOC/('left_successor_'+name.replace('-','_'));shutil.copyfile(OUT/name,target);files.append(target)
    target=DOC/'left_successor_pruning_sources.zip';plan=json.loads((OUT/'reachability-audit-plan.json').read_text())
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for path,h in sorted(plan['source_sha256'].items()):
            if sha(ROOT/path)!=h:raise ValueError('frozen pruning source '+path)
            z.write(ROOT/path,path)
        for name in names:z.write(OUT/name,name)
        for path in sorted((OUT/'compaction-audit-attempt-01').iterdir()):z.write(path,'compaction-audit-attempt-01/'+path.name)
    files.append(target);files += [HERE/f for f in ('left_successor_catalog.py','left_successor_preflight.py','left_successor_audit.py','left_successor_compact.py','left_successor_compact_audit.py','left_successor_reachability.py','left_successor_reachability_audit.py','left_successor_pruning_export.py')];manifest=dict(status='prepared-audited-pruning-evidence-for-parent',published=False,target_theorem_status='not claimed by this scoped export; arithmetic point search is a separately gated experiment',scope='Complete five-node original grammar, all primitive diagnostic instances, compact interfaces, every full hyperedge/rank/layer, exact retained projection and independent preparation/pruning reconstruction. All unknowns retained; native authority/search success/RL/competitive speed are not inferred.',files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in files]);(OUT/'pruning-public-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(files=len(files),target_success_claim=False,published=False)))
if __name__=='__main__':main()
