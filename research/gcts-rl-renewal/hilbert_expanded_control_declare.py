"""Freeze the missing fixed, word-expanded ordering control before any run."""
import hashlib,json
from pathlib import Path
from semantic_inventory_guidance import FIXED

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-expanded-control-20261011'
OLD=ROOT/'.gcts-active/hilbert-promotion-family-20261011'
DOC=ROOT/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'plan.json').exists():raise ValueError('immutable declaration already exists')
    raw=(OLD/'final-integration-v3.json').read_bytes();manifest=json.loads(raw)
    if manifest['status']!='immutable_verified_final' or manifest['file_count']!=167:raise ValueError('exact complete prior export')
    deps={}
    for r in manifest['files']:
        p=ROOT/r['path']
        if sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:raise ValueError('prior export changed '+r['path'])
        deps[r['path']]={k:r[k] for k in ['sha256','bytes']}
    (OUT/'prior-export.json').write_bytes(raw)
    deps[str((OUT/'prior-export.json').relative_to(ROOT))]=dict(sha256=sha(OUT/'prior-export.json'),bytes=len(raw))
    prior=json.loads((DOC/'hilbert_promotion_family_v3_plan.json').read_text())
    api=json.loads((DOC/'hilbert_promotion_family_v3_api_token_amendment.json').read_text())
    resource=json.loads((DOC/'hilbert_promotion_family_v3_guard_resource_plan.json').read_text())
    sources=dict(prior['sources'],**api['versioned_sources'],**resource['versioned_sources'])
    for name in ['declare','run','audit']:
        path=HERE/('hilbert_expanded_control_'+name+'.py');sources[str(path.relative_to(ROOT))]=sha(path)
    for path,h in sources.items():
        if sha(ROOT/path)!=h:raise ValueError('prior frozen source changed '+path)
    pairs=[]
    for case in prior['cases']:
        for rep in prior['repetitions']:
            for language in (['level1','promoted'] if rep==1 else ['promoted','level1']):
                tag=case['id']+'-'+language+'-fixed-expanded-r'+str(rep)
                oldtag=case['id']+'-'+language+'-learned-expanded-r'+str(rep)
                pairs.append(dict(tag=tag,case_id=case['id'],language=language,repetition=rep,
                    paired_tag=oldtag,paired_checkpoint='docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_'+oldtag.replace('-','_')+'.json.gz',
                    paired_final='docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_'+oldtag.replace('-','_')+'_final.json.gz'))
    plan=dict(version='hilbert-expanded-control-plan-1',completed_observations_at_declaration=0,
        original_export_sha256=sha(OUT/'prior-export.json'),original_export_files=167,
        prior_prefix='docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_',cases=prior['cases'],
        schedule=pairs,seed=prior['seed'],limits=prior['limits'],whole_native_steps=prior['whole_native_steps'],
        mode='fixed',feature_semantics='expanded-word',fixed_weights=list(FIXED),paired_weights=prior['weights'],
        sources=sources,data_dependencies=deps,
        treatment='Only the ordering weights change against each frozen learned-expanded pair; same complete inventory, model, feature units, seed, budgets, proposal generation and complete fallback.',
        reuse='Only byte-identical whole requests from the fully independently replayed prior native ledger or an earlier independently audited new acceptance may be reused. Prior preparation and replay costs remain disclosed as historical shared dependencies; incremental setup, hash checking, model construction, search, serialization, lookup and fresh computation/replay are separately charged.',
        measurement='All 16 added trials, paired attempt and graph/proposal counters, status and whole native outcome; preparation/search/native/audit costs and process peak RSS. Two repetitions use the same deterministic seed, not independent statistical samples. No new RL training or significance claim.',
        scope='Guarded symbolic Hilbert incidence fragment, unchanged 28 or 76 high-level point interfaces; no literal primitive-square equivalence, full Euclidean geometry, or quantified closure claim.')
    if len(pairs)!=16:raise ValueError('complete 4 x 2 x 2 schedule')
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),schedule=16,sources=len(sources),dependencies=len(deps))))
if __name__=='__main__':main()
