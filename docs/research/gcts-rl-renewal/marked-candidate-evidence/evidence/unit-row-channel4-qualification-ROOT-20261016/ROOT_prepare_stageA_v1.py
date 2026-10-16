"""Raw/AST-only once-plan preparation. No project imports or scientific calls."""
import ast,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(ref):
 p=Path(ref['path']);assert p.is_absolute()and p==p.resolve()and pin(p)==ref;return p
def save(name,value):
 p=HERE/name
 with p.open('x')as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
def main(argv):
 assert len(argv)==4
 hp,hs,pp,ps=argv;hp=Path(hp);pp=Path(pp)
 assert pin(hp)['sha256']==hs and pin(pp)['sha256']==ps
 h=read(hp);cr=h['source_contract'];c=read(checked(cr));s=c['sources'];i=c['inputs']
 assert len(s)==11 and len(i)==8
 for ref in [*s.values(),*i.values(),*c['original_model_sources'].values()]:checked(ref)
 for ref in s.values():compile(ast.parse(Path(ref['path']).read_bytes()),ref['path'],'exec')
 peer=read(pp);assert peer['source']==s['intake']and peer['sources']==s and peer['source_contract']==cr
 assert peer['scope']==c['scope']and peer['author_identity']=='/root/arithmetic_induction'
 assert peer['reviewer_identity']not in ('/root','/root/arithmetic_induction')
 assert peer['source_only']is True and peer['source_review_passed']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
 root=dict(c['Review_ABI']);root.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,
  source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],
  authorship_disclosure='Root whole-reviewed new stageA caller and engine11/adapter. Arithmetic authored caller/engine/c354; distinct controls peer authored some dependencies and reviewed whole current caller. Root owns plan and actual only; no project functions executed during review.',
  checks=[
   'Current cold Source11/input8 separately authenticated from unchanged original semantic Source17/input2. Prior Root marking acceptance and complete saved data joins fixed; fresh independent marking rederivation occurs. No old intake/engine/control actual rerun or receipt rebasing.',
   'Whole current caller and contract read; inherited17 helpers and transport/nativeexit/failure55 tail raw/AST inverse checked. Same original native20/500MiB reserve,512MiB aggregate,owned60/caller90+1/once/meter2/CodeSeal/strong anchors/immediate guards/whole two-file lossless wire. All cold costs charged.',
   'StageA only: fresh complete finite UG ZERO/SINGLETON/MANY and genuine complete1-to-marked0 through E0 conflict; valid partial deep42 samples losing one or both witnesses remain UNKNOWN. Full proposals/checks/base and marked states/rejections retained. Exclusions are labeled conditional control inputs, never learned pruning.',
   'Real original69 and filtered cursors preserve surviving full packet order/ordinals/context/completion and explicit absence. Fresh c960/c354 complete cover needed for short EOF classification. Direct certifier set-equality and context fields tested only at owned API seams; actual sequence retained separately.',
   'Every declared case must complete with exact expected builtin error for negatives; real native/resource/authority faults propagate, not pass. Abort/interruption poisons cursor. No target proofword/donor/route/search, graph/transition/rollback qualification, RL or benefit claim.',
   'Engine11 plus marked adapter have separate Root+peer conditional Source passes. Runtime success here qualifies only named local degree/cursor controls. Later possible-support/refcount/archive/global-engine controls and matched target comparisons remain mandatory.'
  ])
 rr=save('ROOT-stageA-caller-Source-review-v1.json',root)
 engine_root=pin(HERE/'ROOT-engine-Source-review-v2.json')
 engine_peer=pin(BASE/'unit-row-channel4-engine-independent-source-20261016/typed-Source-review-v2.json')
 for ref in (engine_root,engine_peer):
  r=read(checked(ref));assert r['source']==s['engine']and r['adapter_source']==s['marked_adapter']and r['source_review_passed']is True
  assert r['scientific_calls']==0 and r['scientific_acceptance']is False
 limits=dict(aggregate_owned_bytes=536870912,caller_finish_reserve_seconds=1,caller_seconds=90,failure_only_seconds=55,joint_seconds=20,owned_seconds=60)
 assert c['limits']==limits
 runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
 assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
 owned=HERE/'stageA-owned-v1';external=HERE/'stageA-external-v1';assert not owned.exists()and not external.exists()
 common=dict(invocation_id='channel4-degree-cursor-qualification-20261016-v1',purpose='unit-row-channel4-degree-cursor-controls',
  output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rr,peer=pin(pp)),runtime=runtime,limits=limits,resource_rule='single-owned-process-native-terminal-v1')
 grant=save('ROOT-stageA-authorization-v1.json',dict(common,schema='ROOT-channel4-stageA-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,
  protocol_choice=pin(HERE/'ROOT-stageA-choice-v1.json'),dependency_reviews=dict(engine_ROOT=engine_root,engine_peer=engine_peer)))
 plan=save('ROOT-stageA-plan-v1.json',dict(common,schema='ROOT-channel4-stageA-plan-v1',ROOT_authorization=grant))
 save('ROOT-stageA-preflight-v1.json',dict(schema='ROOT-channel4-stageA-preflight-v1',handoff=pin(hp),plan=plan,scientific_calls=0,
  current_Source11_input8_original_Source17_verified=True,fresh_owned_and_external_outputs=True))
 print(json.dumps(dict(plan=plan,external_directory=str(external))))
if __name__=='__main__':main(sys.argv[1:])
