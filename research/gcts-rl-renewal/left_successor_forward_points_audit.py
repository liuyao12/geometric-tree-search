"""Independent complete-universe and exact point-tiling audit of control words."""
import gzip,hashlib,json,time
from pathlib import Path
import induction_receptors_audit as A
from audit_semantic_inventory import LiteralDomains,legal,advance
from audit_semantic_proofs import whole_replay

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'forward-control'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    began=time.perf_counter();plan=json.loads((OUT/'point-audit-plan.json').read_text());result=dict(status='checking',variants=[])
    for p,h in plan['source_sha256'].items():A.need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact point audit sources '+p)
    for entry in load(OUT/'point-encoding.json.gz'):
        c=load(PARENT/(entry['lane']+'-reachable-core.json.gz'));raw=load(OUT/(entry['lane']+'.json.gz'));A.need(entry['actual_word']['search']['proof']==raw['proof'],'exact separately reconstructed forward word')
        for mode in ('actual_word','same_boundary_embedding'):
            if mode not in entry:continue
            image=entry[mode];spec=image['case'];model=image['model'];proof=image['search']['proof'];A.model_binding(spec,c,model);inventory={tuple(t['key']):t for t in model['placements']};keys=list(map(tuple,image['search']['placements']));A.need(len(set(keys))==4*len(proof) and len(keys)==4*len(proof),'one tile per exact row/role');roots={tuple(p):0 for p in model['roots']};state=dict(totals={},marks={tuple(p):v for p,v in model['initial_marks']},generations=roots.copy(),roots=roots,selected=set(),order=[],tile_generations=[])
            for key in keys:A.need(key in inventory and legal(inventory[key],state),'exact occupancy/extended scalar agreement');state=advance(inventory[key],state)
            A.need(not LiteralDomains(inventory)(state) and all(state['totals'].get(p,0)==12 for p in roots),'complete exact point tiling of fixed boundary');names={r['name'] for r in proof if r['rule']=='block'};request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=proof,target=spec['target']);A.need(whole_replay(request)['status']=='accepted','separate host logical check of source-explicit control word');A.need(spec['theory']==raw['theory'] and spec['target']==raw['target'],'unchanged theory and target');result['variants'].append(dict(lane=entry['lane'],mode=mode,rows=len(proof),full_placements=len(inventory),selected_tiles=len(keys),all_root_occupancies_and_extended_scalar_markings_agree=True,host_logical_status='accepted',native_whole_status='unknown_space_budget for unpadded word; padded variant not submitted',GCTS_search=False))
    result.update(status='passed_exact_control_word_point_encoding',seconds=time.perf_counter()-began,scope='Every full model independently reconstructed, all direct-encoding placements checked for exact occupancy/mark equality and strict-prior logical sources. Both 11-row candidates embed in the identical 12-row target boundary by one irrelevant zero-input filler. This is an encoded forward control, not a GCTS discovery; native whole unknowns are unchanged.')
    (OUT/'point-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
