"""Freeze a bounded 24-run derived-input receptor transfer experiment."""
import gzip,hashlib,json
from pathlib import Path
from hilbert_boundary_transfer_catalog import recipients,build
from semantic_inventory_guidance import FIXED

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'plan.json').exists():raise ValueError('immutable declaration already exists')
    deps={};prior_exports={}
    for label,private in [('family','.gcts-active/hilbert-promotion-family-20261011/final-integration-v3.json'),('control','.gcts-active/hilbert-expanded-control-20261011/final-integration.json')]:
        raw=(ROOT/private).read_bytes();m=json.loads(raw);needcount=167 if label=='family' else 49
        if m['status']!='immutable_verified_final' or m['file_count']!=needcount:raise ValueError('exact prior completed export')
        dest=OUT/('prior-'+label+'-export.json');dest.write_bytes(raw);prior_exports[label]=dict(path=str(dest.relative_to(ROOT)),sha256=sha(dest),files=needcount)
        deps[str(dest.relative_to(ROOT))]=dict(sha256=sha(dest),bytes=dest.stat().st_size)
        for r in m['files']:
            p=ROOT/r['path']
            if sha(p)!=r['sha256'] or p.stat().st_size!=r['bytes']:raise ValueError('immutable prior file '+r['path'])
            deps[r['path']]={k:r[k] for k in ['sha256','bytes']}
    policy_path=DOC/'first-order-families-reader-001.json';policy=json.loads(policy_path.read_text())
    prior=json.loads((DOC/'hilbert_promotion_family_v3_plan.json').read_text());control=json.loads((DOC/'hilbert_expanded_control_plan.json').read_text())
    oldpolicy=prior['data_dependencies'][str(policy_path.relative_to(ROOT))]
    if sha(policy_path)!=oldpolicy['sha256'] or policy_path.stat().st_size!=oldpolicy['bytes'] or policy['training']['weights']!=prior['weights']:raise ValueError('exact inherited policy provenance')
    for p in [policy_path,DOC/'first-order-families-audit-001.json']:
        deps[str(p.relative_to(ROOT))]=dict(sha256=sha(p),bytes=p.stat().st_size)
    sources=dict(control['sources'])
    for name in ['catalog','declare','run','audit']:
        p=HERE/('hilbert_boundary_transfer_'+name+'.py');sources[str(p.relative_to(ROOT))]=sha(p)
    for path,h in sources.items():
        if sha(ROOT/path)!=h:raise ValueError('frozen source '+path)
    cases=recipients();catalog=build(cases,load(DOC/'hilbert_promotion_family_v3_catalog.json.gz'))
    schedule=[]
    for ci,case in enumerate(cases):
        methods=[(lang,mode) for lang in ['level1','promoted'] for mode in ['base','fixed','learned']]
        methods=methods[ci:]+methods[:ci]
        for lang,mode in methods:schedule.append(dict(tag=case['id']+'-'+lang+'-'+mode+'-expanded',case_id=case['id'],language=lang,mode=mode,feature_semantics='expanded-word'))
    native=load(DOC/'hilbert_promotion_family_v3_native.json.gz');admissions=[q for q in native if q['purpose'] in ['family_theory_admission','family_base_admission','family_promoted_admission']]
    source=load(DOC/'hilbert_promotion_family_v3_source_native.json.gz')[0];sourceaudit=json.loads((DOC/'hilbert_promotion_family_v3_source_audit.json').read_text())
    plan=dict(version='hilbert-boundary-transfer-plan-1',completed_observations_at_declaration=0,cases=cases,schedule=schedule,
        seed=72000,fixed_weights=list(FIXED),weights=prior['weights'],limits=dict(attempts=600,seconds=15,proposal_limit=24,proposal_checks=2048),
        guard_native_steps=20_000_000_000,whole_native_steps=10_000_000_000,native_production_seconds_ceiling=1200,
        budget_scope='All new theory, complete guard and whole queries; cumulative actual native request elapsed time, checked before the next query. Record prior total, current query and any overshoot explicitly. An unresolved/incomplete guard catalog stops before any search. Whole-query ceiling means unknown native certification; retain all remaining bounded point trials and every checkpoint.',
        hypothesis='A searched two-input receptor can transfer to inputs derived by primitive MP; a deeper coupled pattern exercises the reverse line receptor. No pure-renaming difficulty or new mathematical axiom.',
        prior_prefix='docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_',prior_control_prefix='docs/research/gcts-rl-renewal/hilbert_expanded_control_',
        prior_exports=prior_exports,sources=sources,data_dependencies=deps,
        prior_cost_provenance=dict(library_native_queries=len(admissions),library_native_production_seconds=sum(q['seconds'] for q in admissions),library_native_micro_steps=sum(q['result']['micro_steps'] for q in admissions),
            source_promotion_native_seconds=source['seconds'],source_promotion_replay_seconds=sourceaudit['seconds'],
            inherited_policy_discovery_and_matching_seconds=policy['training']['discovery_and_matching_seconds'],inherited_policy_training_seconds=policy['training']['training_seconds'],
            inherited_policy_full_pilot_seconds=policy['pilot_seconds'],inherited_policy_full_audit_seconds=policy['audit']['seconds'],inherited_policy_episodes=len(policy['training']['episodes']),
            scope='Inherited stages are disclosed separately; their aggregate and component clocks overlap and must not be summed as disjoint cold costs. No new donor discovery, receptor admission or policy training is performed.'),
        library_scope='The exact 28/76 definitions and all 48 bindings retain only the identical closed I.2 axiom and unchanged signature. Every prior admission is bound to its actual full native replay. Added recipient hypotheses are closed; definitions contain no generalization over new free axioms. Whole certification freshly checks all used definitions under the actual recipient theory.',
        measurement='All 24 runs, equal-inventory base/fixed/learned controls, every complete graph/proposal/fallback/rollback tree, fresh native outputs and exact audited reuse; model setup, inclusive feature cost, worker memory, serialization, preparation, prior stages, production and independent replay costs. One deterministic seed, no significance or general speed claim.',
        scope='Finite marked high-level proof adaptation in a guarded Hilbert incidence fragment. No primitive-square compiler equivalence, full Euclidean geometry, or quantified closure claim.')
    if len(schedule)!=24 or len(admissions)!=77:raise ValueError('complete matrix and prior interface provenance')
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(OUT/'declared-catalog.json.gz').write_bytes(gzip.compress(json.dumps(catalog,separators=(',',':')).encode(),mtime=0))
    print(json.dumps(dict(plan_sha256=sha(OUT/'plan.json'),runs=24,groups={k:len(v['basis']) for k,v in catalog['groups'].items()},sources=len(sources),dependencies=len(deps))))
if __name__=='__main__':main()
