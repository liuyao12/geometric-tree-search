"""Freeze sources, exact inputs, finite domain, corruptions and budgets first."""
import ast,gzip,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=ROOT/'.gcts-active/hilbert-chain-composition-plan-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def pin(p):return dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def rel(p):return str(p.relative_to(ROOT))
def main():
    began=time.perf_counter();dest=HERE/'plan-v2.json'
    if dest.exists():raise ValueError('already frozen')
    preserved={}
    for p in [OLD/'manifest-v1.json',ROOT/'.gcts-active/hilbert-promotion-family-20261011/final-integration-v3.json',ROOT/'.gcts-active/hilbert-expanded-control-20261011/final-integration.json',ROOT/'.gcts-active/hilbert-boundary-transfer-20261011/final-integration.json']:
        preserved[rel(p)]=pin(p)
        for r in json.loads(p.read_text())['files']:
            q=ROOT/r['path']
            if pin(q)!=dict(sha256=r['sha256'],bytes=r['bytes']):raise ValueError('prior evidence changed')
    source_paths=sorted(HERE.glob('hilbert_constant_*_v2.py'))
    if len(source_paths)!=6:raise ValueError('all six sources before execution')
    for p in source_paths:ast.parse(p.read_text())
    snapshot=OLD/'source-schemas-v1.json';record=DOC/'hilbert_promotion_family_v3_source_native.json.gz';receipt=DOC/'hilbert_promotion_family_v3_source_audit.json';preview=OLD/'inventory-preview-v1.json.gz'
    original=json.loads(gzip.decompress(preview.read_bytes()))['primary'];first=original['base_definitions'][0]['name'];transport=original['base_definitions'][36]['name'];promoted=original['promoted_definitions'][0]['name']
    cert=[];primitive=[]
    def c(name,path,value=None,operation='set',**kw):cert.append(dict(name=name,path=path,operation=operation,**({} if operation!='set' else {'value':value}),**kw))
    def d(name,index,path,value):primitive.append(dict(name=name,record_index=index,path=path,operation='set',value=value))
    c('map-open-variable',['records',63,'constant_map','A'],['var','P'])
    c('map-non-nullary-term',['records',63,'constant_map','C'],['fun','f',[['fun','P',[]]]])
    c('map-undeclared-constant',['records',63,'constant_map','u'],['fun','missing',[]])
    c('map-wrong-role',['records',63,'constant_map','A'],['fun','l',[]])
    c('map-missing-source-key',['records',63,'constant_map','B'],operation='delete')
    c('map-extra-source-key',['records',63,'constant_map','foreign'],['fun','P',[]])
    c('axiom-missing-I2',['recipient_theory','axioms','I.2-uniqueness'],operation='delete')
    c('axiom-wrong-image',['recipient_theory','axioms','I.2-uniqueness'],['bot'])
    c('axiom-name-map-forged',['records',63,'axiom_name_map','I.2-uniqueness'],'missing')
    c('signature-arity-changed',['recipient_theory','predicates','Incident'],1)
    c('signature-fresh-symbol-removed',['recipient_theory','functions','n'],operation='delete')
    c('source-request-binding-forged',['source_native_binding','request_sha256'],'0'*64)
    c('source-output-binding-forged',['source_native_binding','output_sha256'],'0'*64)
    c('authority-native-label',['authority'],'native_accepted')
    c('reference-forward',['records',63,'definition','proof',3,'inputs'],[3,2])
    c('reference-reordered',['records',63,'definition','proof',3,'inputs'],[2,1])
    c('local-premise-erased',['records',63,'definition','premises',0],['bot'])
    c('template-hole-forged',['records',36,'definition','proof',2,'template'],['pred','Incident',[['fun','P',[]],['var','otherHole']]])
    c('body-hash-forged',['records',63,'body_sha256'],'0'*64)
    c('dependency-name-stale',['records',63,'definition','proof',1,'name'],'missing')
    c('dependency-forward',['records',63,'definition','proof',1,'name'],promoted)
    c('alias-target-forged',['dependency_aliases',0,'target_dependency'],transport)
    c('alias-body-forged',['dependency_aliases',0,'target_body_sha256'],'0'*64)
    c('missing-dependency-entry',['records',0],operation='delete')
    c('duplicate-complete-entry',['records'],operation='append',copy_index=0)
    c('duplicate-alias-entry',['dependency_aliases'],operation='append',copy_index=0)
    c('missing-alias-entry',['dependency_aliases',0],operation='delete')
    c('declaration-order-changed',['records'],operation='swap',left=0,right=63)
    d('rule-assumption-negative',0,['proof',0,'index'],-1)
    d('rule-assumption-boolean',0,['proof',0,'index'],True)
    d('rule-axiom-missing-name',0,['proof',1,'name'],'missing')
    d('rule-instance-open-term',0,['proof',2,'term'],['var','open'])
    d('rule-instance-wrong-formula',0,['proof',2,'formula'],['bot'])
    d('rule-instance-not-universal',0,['proof',2,'universal'],['bot'])
    d('rule-mp-forward',0,['proof',10,'antecedent'],10)
    d('rule-mp-wrong-implication',0,['proof',10,'implication'],1)
    d('rule-equality-hole-variable',36,['proof',2,'variable'],'otherHole')
    d('rule-equality-template',36,['proof',2,'template'],['pred','Incident',[['fun','P',[]],['var','otherHole']]])
    d('rule-equality-open-left',36,['proof',2,'left'],['var','open'])
    d('rule-equality-unknown-right',36,['proof',2,'right'],['fun','missing',[]])
    d('rule-child-missing',63,['proof',1,'name'],'missing')
    d('rule-child-forward',63,['proof',3,'inputs'],[3,2])
    d('rule-child-reordered',63,['proof',3,'inputs'],[2,1])
    d('rule-child-duplicated-input',63,['proof',3,'inputs'],[1,1])
    d('rule-new-generalize',63,['proof',0,'rule'],'generalize')
    d('rule-conclusion-mismatch',63,['conclusion'],['bot'])
    failed=json.loads((HERE/'stage-costs-v1.json').read_text())
    if failed['stages']!=[dict(stage='produce',process_wall_seconds=failed['stages'][0]['process_wall_seconds'],exit_code=1,timeout=False)]:raise ValueError('exact failed prelogical v1 stage')
    frozen_v1=[*sorted(HERE.glob('hilbert_constant_*_v1.py')),HERE/'plan-v1.json',HERE/'stage-costs-v1.json',HERE/'produce-stdout-v1.txt',HERE/'produce-stderr-v1.txt']
    inputs=[snapshot,record,receipt,preview,OLD/'proposal-v1.json',ROOT/'docs/basic-tiling-algorithm.md',DOC/'proof-boundary-001.json',DOC/'proof-boundary-microcode-001.json.gz',*frozen_v1]
    plan=dict(version='hilbert-constant-structural-phase-plan-1',status='frozen_before_execution',completed_productions=0,completed_audits=0,native_queries=0,point_models=0,target_searches=0,authority_adapter_activation_authorized=False,
        budgets=dict(production_wall_seconds=180,audit_wall_seconds=180,host_ceiling_bytes=512*1024*1024),
        resource_enforcement='External50ms RSS/time watchdog and child SIGALRM; supported soft RLIMIT_DATA/AS/RSS probes recorded rather than silently presumed; final kernel peak RSS above512MiB rejects as unknown. Failed v1 time is deducted from the aggregate180s production gate. Host native requests/model/search activation prohibited.',
        source_pins={rel(p):pin(p) for p in source_paths},inputs={rel(p):pin(p) for p in inputs},preserved_manifests=preserved,
        source_snapshot=rel(snapshot),source_record=rel(record),source_receipt=rel(receipt),preview=rel(preview),
        constant_domains={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m','n'],'v':['l','m','n']},
        counts=dict(uniqueness=36,equality_transport=27,promoted=108,total=171,dependency_edges=216),
        certificate_corruptions=cert,primitive_corruptions=primitive,raw_duplicate_corruption=True,
        corruption_scope='Both changed structural certificates and direct local six-rule cases. Some edits are valid in a broader logic but outside this declared constant-only transport protocol; rejection does not claim mathematical invalidity.',
        source_schema_scope='Exact prior accepted/replayed three-block request under I.2 alone. Assumptions, references and commands preserved, including contradictory/noninjective premises. No generality beyond these finite mapped instances is proved.',
        outcome_scope='Finite checked structural preservation only. Formal pinned-native semantic correspondence and any certified_transport authority adapter remain open. No57/228native batch, graph or target proof is authorized.',
        declaration_seconds_before_plan_write=time.perf_counter()-began,
        resource_only_v2_amendment=dict(original_plan_sha256=pin(HERE/'plan-v1.json')['sha256'],failed_stage=failed['stages'][0],
            original_failure='macOS hard RLIMIT_DATA setup raised current limit exceeds maximum limit before source/certificate work',
            changed='Supported soft-limit probes, external watchdog, final kernel peak gate; no logical checker/171-domain/216-DAG/47-corruption changes.',
            failed_v1_pins={rel(p):pin(p) for p in frozen_v1},logical_work_before_repair=0))
    plan['version']='hilbert-constant-structural-phase-plan-2-resource-only'
    dest.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan_sha256=pin(dest)['sha256'],sources=len(source_paths),certificate_corruptions=len(cert),primitive_corruptions=len(primitive),all_corruptions=len(cert)+len(primitive)+1)))
if __name__=='__main__':main()
