"""Independent entire point-universe rank-eligibility projection audit.

No rank-model producer import. The original universe is reconstructed by the
literal point auditor, then every placement is classified from explicit full
grammar ranks. A small exhaustive strict-prior-word fixture checks the generic
language-preservation implication, including all source choices and cycles.
"""
import gzip,hashlib,itertools,json,time
from pathlib import Path
import induction_receptors_audit as A

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def fixture():
    rules=[([],0),([0],1),([1],2),([2],0),([3],3),([0,1],2)];ranks=[0,1,2,None];count=0
    def words(outputs):
        nonlocal count
        if len(outputs)==4:return
        j=len(outputs)
        for premises,out in rules:
            choices=[[s for s,q in enumerate(outputs) if q==p] for p in premises]
            for sources in itertools.product(*choices):
                need(ranks[out] is not None and ranks[out]<=j and all(ranks[p]<=s<j for p,s in zip(premises,sources)),'every arbitrary valid strict-prior fixture word satisfies positional rank conditions');count+=1;words(outputs+[out])
    words([]);return count
def classify(tile,rules,ranks):
    j=tile['slot'];kind=tile['kind'];rule_id=tile['inference'] if kind in ('command','guard') else tile['mode']-1 if tile['mode'] else None;reasons=[]
    if rule_id is not None:
        r=rules[rule_id];rank=ranks[A.packed(r['conclusion'])]
        if rank is None or rank>j:reasons.append(dict(bound='output-rank-at-most-row',rank=rank,row=j))
        for role,p in enumerate(r['premises']):
            rank=ranks[A.packed(p)]
            if rank is None or rank>=j:reasons.append(dict(bound='premise-rank-below-row',input=role,rank=rank,row=j))
    if kind=='inference_input':
        rank=ranks[A.packed(rules[rule_id]['premises'][tile['input']])]
        if rank is None or rank>tile['source']:reasons.append(dict(bound='input-rank-at-most-source-row',rank=rank,source=tile['source']))
    return reasons
def main():
    began=time.perf_counter();plan=json.loads((OUT/'rank-audit-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'reachability-audit.json').read_text())['status']=='passed_finite_grammar_structural_pruning','independent full grammar ranks');need(json.loads((OUT/'admission-audit.json').read_text())['status']=='passed_complete_reachable_native_admission','whole actual retained admission')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen rank auditor '+p)
    result=dict(status='checking',variants=[],native_queries=0,target_searches=0,exhaustive_fixture_valid_words=fixture())
    for lane in base['variants']:
        raw=load(OUT/('rank-'+lane+'-model.json.gz'));c=load(OUT/(lane+'-reachable-core.json.gz'));w=load(OUT/(lane+'-reachability.json.gz'));full=raw['full_retained_model'];projected=raw['rank_projected_model'];A.model_binding(raw['case'],c,full);ranks={A.packed(f):rank for f,rank in zip(c['basis'],w['formula_ranks'])};kept=[];removed=[]
        for tile in full['placements']:
            reasons=classify(tile,c['rules'],ranks)
            if reasons:removed.append(dict(key=tile['key'],reasons=reasons))
            else:kept.append(tile)
        need(projected['placements']==kept and projected['rank_projection']['removed']==removed,'every full candidate classified exactly once; no extra restriction');need(projected['rank_projection']['witness_sha256']==c['structural_pruning']['witness_sha256'] and full['catalog']==projected['catalog'] and full['roots']==projected['roots'] and full['initial_marks']==projected['initial_marks'] and full['inference_rules']==projected['inference_rules'] and full['domains']==projected['domains'],'same exact words, complete root boundary, full rules and positional grammar');need(len(kept)==projected['rank_projection']['eligible_placement_count'] and len(full['placements'])==projected['rank_projection']['full_retained_placement_count'],'full universe/projection counts')
        result['variants'].append(dict(lane=lane,complete_full_retained_universe=len(full['placements']),exact_rank_eligible_universe=len(kept),excluded=len(removed),all_excluded_keys_have_a_necessary_rank_obstruction=True,all_eligible_keys_and_exact_marks_retained=True,equal_successful_finite_strict_prior_word_language=True));print('rank full-universe projection audit',lane,len(full['placements']),len(kept),flush=True)
    result.update(status='passed_complete_rank_projection_and_language_preservation',seconds=time.perf_counter()-began,safety='Induct over zero-based proof rows. Every zero-input output has rank0. Every later inference has strict-prior source rows, whose formulas have rank at most their rows; the full fixed point gives its output rank at most one plus the maximum premise rank, hence at most the current row. Each selected source receptor has rank at most its source row. Thus every original valid proof word retains all C/G/I1/I2 placements. Conversely projected placements are unchanged original placements, so no new word is introduced. No target backcone, target path, native authority change or full-FOL claim.')
    (OUT/'rank-audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
