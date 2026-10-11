"""Independent rank-projected whole point-tree audit adapter.

The unchanged independent tree/whole auditor is reused. Its full-universe
model admission hook independently reconstructs the unprojected universe,
then classifies every original placement by complete fixed-point ranks. No
rank-model producer is imported. Original observations remain separate.
"""
import gzip,hashlib,json
from pathlib import Path
import left_successor_search_audit as audit
from left_successor_rank_audit import classify

PARENT=audit.OUT
literal_model_binding=audit.A.model_binding
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def projected_model_binding(spec,catalog,model):
    candidates=[]
    for lane in ('without-transfer','with-searched-zero-left'):
        witness_path=PARENT/(lane+'-reachability.json.gz')
        if hashlib.sha256(witness_path.read_bytes()).hexdigest()==catalog['structural_pruning']['witness_sha256']:candidates.append(lane)
    audit.need(len(candidates)==1,'one exact complete rank witness')
    lane=candidates[0];w=load(PARENT/(lane+'-reachability.json.gz'));snapshot=load(PARENT/('rank-'+lane+'-model.json.gz'));full=snapshot['full_retained_model']
    audit.need(snapshot['case']['length']==spec['length'] and snapshot['case']['theory']==spec['theory'] and snapshot['case']['target']==spec['target'],'complete positional rank model scope')
    literal_model_binding(spec,catalog,full)
    ranks={audit.A.packed(f):r for f,r in zip(catalog['basis'],w['formula_ranks'])};kept=[];removed=[]
    for tile in full['placements']:
        reasons=classify(tile,catalog['rules'],ranks)
        if reasons:removed.append(dict(key=tile['key'],reasons=reasons))
        else:kept.append(tile)
    audit.need(model['placements']==kept and model['rank_projection']['removed']==removed,'every actual point key exactly equals the complete necessary-rank projection')
    for field in ('catalog','roots','initial_marks','inference_rules','domains','structural_pruning'):audit.need(model[field]==full[field],'identical full inventory/word boundary '+field)
    audit.need(model['rank_projection']['witness_sha256']==catalog['structural_pruning']['witness_sha256'] and model['rank_projection']['full_retained_placement_count']==len(full['placements']) and model['rank_projection']['eligible_placement_count']==len(kept),'full rank evidence/count bindings')
    return dict(full=len(full['placements']),eligible=len(kept),removed=len(removed))
def main():
    audit.need(json.loads((PARENT/'rank-audit.json').read_text())['status']=='passed_complete_rank_projection_and_language_preservation','passed independent full rank eligibility/equal-language audit')
    audit.OUT=PARENT/'rank-search';audit.TMP=Path('/private/tmp/gcts-left-successor-rank-search-audit-20261011');audit.A.model_binding=projected_model_binding;audit.main()
    result=json.loads((audit.OUT/'search-audit.json').read_text());result.update(phase='necessary-positional-rank-projection',projection_scope='Each actual model is independently reconstructed from every unprojected retained placement and the complete full-grammar rank witness; every eligible placement is retained. The unchanged independent point-tree auditor replays every recorded node. All original four unknowns remain separately recorded.')
    (audit.OUT/'search-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
