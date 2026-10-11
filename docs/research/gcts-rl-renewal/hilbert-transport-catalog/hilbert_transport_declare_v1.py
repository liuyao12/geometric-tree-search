"""Freeze the exact complete point compiler phase before construction or audit."""
import ast,gzip,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'.gcts-active/hilbert-constant-certificates-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal';PLANNING=ROOT/'.gcts-active/hilbert-chain-composition-plan-20261011'
def pin(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def rel(p):return str(p.relative_to(ROOT))
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    began=time.perf_counter();dest=HERE/'plan-v1.json'
    if dest.exists():raise ValueError('immutable frozen plan exists')
    py=sorted(HERE.glob('hilbert_transport_*_v1.py'));sources=py+[HERE/'hilbert_transport_reader_v1.js']
    if len(py)!=6:raise ValueError('all sixPython sources must precede freeze')
    for p in py:ast.parse(p.read_text())
    preserved_paths=[PLANNING/'manifest-v1.json',ROOT/'.gcts-active/hilbert-promotion-family-20261011/final-integration-v3.json',ROOT/'.gcts-active/hilbert-expanded-control-20261011/final-integration.json',ROOT/'.gcts-active/hilbert-boundary-transfer-20261011/final-integration.json',OLD/'export-v3.json'];preserved={rel(p):pin(p) for p in preserved_paths};entries=0
    for p in preserved_paths:
        for r in json.loads(p.read_text())['files']:
            if pin(ROOT/r['path'])!={k:r[k] for k in ['sha256','bytes']}:raise ValueError('old raw evidence changed')
            entries+=1
    links=dict(certificate=rel(OLD/'certificate-v3.json.gz'),structural_audit=rel(OLD/'audit-v3.json'),source_snapshot=rel(PLANNING/'source-schemas-v1.json'),source_record=rel(DOC/'hilbert_promotion_family_v3_source_native.json.gz'),source_receipt=rel(DOC/'hilbert_promotion_family_v3_source_audit.json'),argument=rel(DOC/'constant-transport-argument.html'),ledger=rel(DOC/'constant-transport-ledger.json'),argument_review=rel(DOC/'constant-transport-review.json'))
    ledger=json.loads((ROOT/links['ledger']).read_text());extra=[OLD/'hilbert_constant_checker_v3.py',OLD/'hilbert_constant_audit_v3.py',OLD/'plan-v3.json',OLD/'stage-costs-v3.json',OLD/'supervisor-failure-v2.json',ROOT/'docs/basic-tiling-algorithm.md']+[ROOT/p for p in ledger['sources']]
    inputs={rel(p):pin(p) for p in [*[ROOT/p for p in links.values()],*extra]}
    certificate=json.loads(gzip.decompress((ROOT/links['certificate']).read_bytes()))
    corruptions=[]
    def c(name,target,path,value=None,operation='set',**kw):corruptions.append(dict(name=name,target=target,path=path,operation=operation,**({'value':value} if operation=='set' else {}),**kw))
    c('native-authority-label','model',['authority','kind'],'native_accepted');c('stale-authority-epoch','model',['authority','epoch'],'stale');c('forged-certificate-binding','model',['authority','certificate_sha256'],'0'*64);c('stale-argument-binding','model',['authority','argument_sha256'],'0'*64)
    c('missing-full-dependency','model',['interfaces',63,'dependencies',0],operation='delete');c('ordered-premise-swapped','model',['interfaces',36,'premises'],list(reversed(certificate['records'][36]['definition']['premises'])));c('premise-multiplicity-erased','model',['interfaces',63,'premises',1],operation='delete')
    c('formula-code-collision','model',['formula_codes',1],certificate['recipient_theory']['axioms']['I.2-uniqueness']);c('assigned-zero-erased','model',['prototypes',3,'m',0],operation='delete');c('rotation-added','model',['orientations'],['identity','rotate90']);c('root-generation-wrong','model',['root_generations',0,2],1)
    c('missing-raw-alignment','model',['placements',0],operation='delete');c('fractional-t-replaced','model',['prototypes',0,'t',0,2],0);c('spurious-seed-reference-port','model',['ordered_bindings',4,'inputs'],[])
    c('duplicate-placement-identity','model',['placements'],operation='append',copy_index=0);c('exterior-sentinel-erased','model',['fixed_m',0],operation='delete');c('noninjective-map-changed-without-proof','certificate',['records',63,'constant_map','B'],['fun','Q',[]]);c('equality-template-hole-corrupted','certificate',['records',36,'definition','proof',2,'variable'],'otherHole');c('alias-missing','certificate',['dependency_aliases',0],operation='delete')
    # Ordered binding4 is row1's first seed, so use its shape to detect a
    # spurious premise reference rather than accidentally repeat [] unchanged.
    corruptions[13]['value']=[0]
    plan=dict(version='hilbert-transport-point-catalog-plan-1',status='frozen_before_production',rows=5,budgets=dict(production_wall_seconds=180,audit_wall_seconds=180,host_ceiling_bytes=512*1024*1024),source_pins={rel(p):pin(p) for p in sources},inputs=inputs,preserved_manifests=preserved,**links,
        source_request_sha256='82f39e52121200450c03f1e6e1a2a86a65b0bd7d1b96a7f27b4643fc8ac85ef7',
        recipient='Only guarded I.2 theory; ordered local inputs H(P,Q,l,m),H(P,Q,m,n),Incident(R,l); final-row formula Incident(R,n). Full4input/axiom +171block row grammar, not unrestricted FOL.',
        predicted_counts=dict(definitions=171,formula_codes=55,prototypes=1768,rejected_prototypes=540,raw_alignments=8840,strict_prior_bindings=4430,inconsistent_strict_prior=1350,consistent_strict_prior=3080,initial_point_candidates=1492),
        probe_scope='Every initial legal candidate1492 gets one placement/complete graph-domain/rollback probe; no theorem path searched. Artificial two-formula3-row grammar exhausts315 capacity-legal row choices, all valid placement permutations, and all same-row overlap pairs.',
        point_contract='t unit at(0,row); formula m at(1,row) and earlier reference points; port offsets at(2+k,row). Values exact integers, injective canonical formula codes starting0; missing is absent. Relative negative row offsets remain unchanged under vertical translation. Exterior formula sentinels-1 reject negative references through marking disagreement. Identity orientation only. All required rows are active roots generation0.',
        fallback='All63lower transported interfaces and4seed/axiom declarations remain in the complete inventory. Added108searched interfaces are separately labeled symbolic row rules, not scheduler-bypassing macros or aggregate t expansions.',
        authority_scope='certified_transport only for the exact finite six-rule source relation and its row compiler. No native_accepted relabel, no existing-native-engine activation; formal serializer/native/compiler and aggregate expansion correspondences open.',
        resource_enforcement='Task-owned escalated fail-closed external RSS/time watchdog, child SIGALRM, supported OS-limit probes, final kernel-peak validation; unsupported probes are reported, not credited. Fresh180s production+180s audit/512MiB.',
        dependency_costs=dict(prior_structural_production_seconds=7.3899025,prior_structural_audit_seconds=10.903200416,prior_v1_failure_seconds=.027183875,prior_v2_child_work_seconds='unknown',original_cumulative_structural_gate='not_established',donor_native_acceptance_seconds=31.310553125,donor_full_native_replay_seconds=33.958145583),
        corruptions=corruptions,preserved_file_entries=entries,native_queries=0,target_searches=0,existing_engine_activation=False,authority_adapter_native_accepted=False,declaration_seconds_before_plan_write=time.perf_counter()-began)
    plan['authority_epoch']=sha(dict(sources=plan['source_pins'],inputs=inputs,counts=plan['predicted_counts'],rows=5))
    dest.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan_sha256=pin(dest)['sha256'],sources=len(sources),corruptions=len(corruptions),prior_entries=entries,predicted_counts=plan['predicted_counts'])))
if __name__=='__main__':main()
