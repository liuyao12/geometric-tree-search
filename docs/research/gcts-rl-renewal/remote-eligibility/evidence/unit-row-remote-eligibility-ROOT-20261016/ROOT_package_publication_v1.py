"""Package complete partial-control saved records; no scientific replay."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ACT=Path(__file__).resolve().parent;BASE=ACT.parent.parent
HERE=ACT.parent/'unit-row-remote-eligibility-publication-ROOT-20261016';HERE.mkdir(exist_ok=True)
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015');REL=Path('docs/research/gcts-rl-renewal/remote-eligibility');folder=BASE/REL
def pin(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(PUB),*args])
baseline='0dcb2b8003e69e727ea6e53aa0606e11b301d7b2'
assert not git('status','--porcelain') and git('rev-parse','HEAD').decode().strip()==baseline
root_index=pin(BASE/'docs/research/gcts-rl-renewal/index.html');modes=('original-controls','domain-controls','advice-controls')
ds={m:read(ACT/('ROOT-'+m+('-partial-disposition-v1.json' if m=='advice-controls' else '-disposition-v1.json'))) for m in modes}
ps={m:read(ACT/('ROOT-'+m+'-plan-v1.json')) for m in modes};ref=ps['advice-controls']
for m in modes:
 for k in ('sources','inputs','source_contract','reviews','runtime','limits','resource_rule'):assert ps[m][k]==ref[k]
 n=read(ACT/(m+'-external-v1/native-terminal.json'));assert n['all_reaped'] and n['caller_pid']==n['wait4_pid'] and n['caller_returncode']==0
 d=ds[m];assert d['native_resources_qualified'] and d['complete_wire_verified']
 if m=='advice-controls':assert d['actual_closed'] and not d['controls_accepted'] and not d['target_admission_qualified'] and d['reported_passed_cases']==28 and d['reported_skipped_cases']==15
 else:assert d['controls_accepted'] and d['passed_cases']==17 and d['skipped_cases']==0
for arm in ('canonical-search','advised-search'):assert not (ACT/('ROOT-'+arm+'-plan-v1.json')).exists()
old=read(ACT.parent/'unit-row-paired-fixture-ROOT-20261016/ROOT-advice-controls-plan-v1.json')
for k in ('inputs','runtime','limits','resource_rule'):assert old[k]==ref[k]
assert {k for k in ref['sources'] if old['sources'][k]!=ref['sources'][k]}=={'advice_controls','intake'}
result=read(ACT/'ROOT-advice-controls-expanded-result-v1.json');c=result['controls'];art=c['artifacts'];cal=art['remote_eligibility'];decision=cal['actual_global_decision'];bad=cal['bad_key'];before=cal['before_decision']['state']
assert decision['kind']=='FORCED' and decision['row']==1 and bad['translation']==[0,8] and not cal['eligible_actual_branch'] and not cal['normal_search_started']
assert art['pending_success_fixture']['pending_selection_observed'] is True
assert c['passed']==28 and c['skipped']==15 and len(c['cases'])==43
comparison={'schema':'ROOT-remote-eligibility-comparison-v1','previous_goal_turn':'progress','current_goal_turn':'progress','broad_goal_complete':False,'scientific_replay':False,'actuals':3,'all_closed_and_reaped':True,'same_Source17_input2_reviews_runtime_limits_within_version':True,'changed_sources':['advice_controls','intake'],'same_mathematical_input_runtime_limits':True,'target_actuals_launched':0,'proof_accepted':False,'GCTS_advantage_accepted':False,'RL_accepted':False,'current_full_record_returned':True,'reported_passed':28,'reported_skipped':15,'reported_PASSED_semantics_independently_accepted_here':False}
save(HERE/'ROOT-same-Source-comparison-v1.json',comparison)
evidence=[];by_original={};omitted=[]
def copy(src,dst):
 assert src.is_file() and not src.is_symlink() and src.suffix in ('.py','.json','.jsonl','.txt','.patch','.md') and not dst.exists()
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());r={'public_path':str(dst.relative_to(folder)),'original_path':str(src),**pin(src)};evidence.append(r);by_original[str(src)]=r['public_path']
groups=['unit-row-remote-eligibility-controls-source-20261016','unit-row-remote-eligibility-controls-independent-source-20261016','unit-row-remote-eligibility-cold-ROOT-source-20261016','unit-row-remote-eligibility-cold-independent-source-20261016','unit-row-remote-eligibility-ROOT-20261016']
for name in groups:
 p=ACT.parent/name
 for src in sorted(p.rglob('*')):
  if not src.is_file() or '__pycache__' in src.parts:continue
  rel=src.relative_to(p)
  if p==ACT and str(rel) in ('ROOT-original-controls-expanded-result-v1.json','ROOT-domain-controls-expanded-result-v1.json'):
   omitted.append({'original_path':str(src),**pin(src)});continue
  copy(src,folder/'evidence'/p.name/rel)
for role,r in {**ref['sources'],**ref['inputs']}.items():
 src=Path(r['path']);assert pin(src)=={k:r[k] for k in ('sha256','bytes')}
 if str(src) not in by_original:copy(src,folder/'evidence/original-authority'/role/src.name)
grant=read(Path(ref['ROOT_authorization']['path']))
for role,r in grant['dependency_reviews'].items():
 src=Path(r['path']);assert pin(src)=={k:r[k] for k in ('sha256','bytes')}
 if str(src) not in by_original:copy(src,folder/'evidence/dependency-reviews'/role/src.name)
for rel in ('.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py','.gcts-active/arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py','docs/basic-tiling-algorithm.md'):
 src=BASE/rel;copy(src,folder/'evidence/measurement'/src.name)
for rel in ('unit-row-paired-fixture-cold-ROOT-source-20261016/unit_row_paired_fixture_cold_v14.py','unit-row-paired-fixture-cold-ROOT-source-20261016/Source-contract-v14.json','unit-row-paired-fixture-controls-source-20261016/compatible_fibres_controls_v8.py','unit-row-paired-fixture-controls-source-20261016/Source-contract-v8.json','unit-row-paired-fixture-ROOT-20261016/ROOT_close_advice_controls_saved_v14.py'):
 src=ACT.parent/rel
 if str(src) not in by_original:copy(src,folder/'evidence/parents'/src.parent.name/src.name)
copy(HERE/'ROOT-same-Source-comparison-v1.json',folder/'evidence/ROOT-same-Source-comparison-v1.json')
save(folder/'evidence-manifest.json',{'schema':'remote-eligibility-evidence-manifest-v1','files':evidence,'scope':'Exact current Sources/reviews and all three closed current endpoints, including complete expanded43 with every SKIP. Partial closure verifies wire/resource/literal concordance, not independent semantics of reported PASS labels.','omitted_public_duplicate_records':omitted,'omission_reason':'Original and retention complete canonical expanded records remain in their published lossless envelopes.'})
marks={tuple(p):v for p,v in before['m']};pre=bad['type_preimage'];conflicts=[]
for required,offset in zip(pre['ordered_premise_formulas'],pre['ordered_offsets']):
 point=(1,bad['translation'][1]+offset);value=marks.get(point)
 if value and value[0]=='formula' and json.loads(value[1])!=required:
  conflicts.append({'point':list(point),'assigned_formula':json.loads(value[1]),'required_formula':required})
assert conflicts
# Coordinate/formula translation for display only, never a new legality check.
conflict=dict(conflicts[0],remote_row=cal['remote']['placement_key']['translation'][1],pending_row=bad['translation'][1],pending_rule={'mp':'MP','generalize':'UG','instantiate':'UI'}.get(pre['primitive_witness']['rule'],pre['primitive_witness']['rule']),decision={k:v for k,v in decision.items() if k!='candidate'})
prefix='evidence/unit-row-remote-eligibility-ROOT-20261016/'
links=[('Exact evidence manifest','evidence-manifest.json'),('Complete partial disposition',prefix+'ROOT-advice-controls-partial-disposition-v1.json'),('Complete current expanded control record',prefix+'ROOT-advice-controls-expanded-result-v1.json'),('Current lossless result envelope',prefix+'advice-controls-owned-v1/engine-result.json'),('Full transport concordance',prefix+'ROOT-advice-controls-transport-concordance-v1.json'),('Native terminal and reaping',prefix+'advice-controls-external-v1/native-terminal.json'),('Fresh postterminal observation',prefix+'advice-controls-external-v1/observation.json'),('Once invocation',prefix+'advice-controls-external-v1/ONCE.json'),('Complete tool time bracket',prefix+'ROOT-advice-controls-tool-bracket-v1.json'),('Original controls disposition',prefix+'ROOT-original-controls-disposition-v1.json'),('Retained-state controls disposition',prefix+'ROOT-domain-controls-disposition-v1.json'),('Independent controls9 review',by_original[grant['dependency_reviews']['advice_controls_peer']['path']]),('Independent caller15 review',by_original[ref['reviews']['peer']['path']]),('Partial saved closer Root review',prefix+'ROOT-partial-closer-Source-review-v1.json'),('Current control contract','evidence/unit-row-remote-eligibility-controls-source-20261016/Source-contract-v9.json'),('Current caller contract','evidence/unit-row-remote-eligibility-cold-ROOT-source-20261016/Source-contract-v15.json'),('Earlier immutable timeout','../paired-fixture/reader.html#results')]
stages=[{'label':m.replace('-',' '),'outcome':r'\(28\) reported passed; \(15\) skipped' if m=='advice-controls' else r'\(17\) passed; no skips','native_ns':ds[m]['native_launch_to_postprobe_ns'],'peak_bytes':ds[m]['aggregate_B_bytes'],'qualified':True} for m in modes]
data={'schema':'remote-eligibility-saved-reader-v1','lead':'The expanded suite returns a complete record. It exposes a concrete boundary mismatch and preserves every essential gap.','outcome':r'Original and retained-state controls each pass all \(17\) tests without skips. The expanded suite reports \(28\) passed and \(15\) skipped cases within \(10.642492\,\mathrm{s}\). Complete control qualification and target admission remain false. All processes are closed and reaped.','stages':stages,'calibration':cal,'conflict':conflict,'cases':c['cases'],'calibration_text':r'The independent consumer rejects the saved pending MP key at row \(8\) for a conflicting remote formula mark. The real global decision is FORCED at row \(1\), so this boundary does not qualify the immediate pending-rejection search. The control records that gap and starts no unrelated search.','case_note':r'All \(43\) returned outcomes are shown. These are the suite’s reported outcomes; the separate partial closer verifies complete wire, native resources and saved joins, and does not independently re-prove the reported PASSED semantics.','assessment':r'This changes the next action. The actual first-ranked original family has one future member, at row \(8\). It cannot exercise a test that requires another legal future member to remain after rejection, or the existing two-member forced-retirement test. The separate sibling records a real pending selection, but its linked inputs also do not establish selective rejection. Cluster interface shape must be part of control eligibility.','next_step':'Next, declare a separately owned generic multi-member control fixture with an unoccupied external read whose conflict leaves a different legal future member. Use actual whole batches and independent validation. Follow only genuinely forced moves before checking branch eligibility. Preserve current first-ranked-family evidence and keep any control-only family selection separate from the target policy.','trace':(ACT/'advice-controls-external-v1/meter-stderr.txt').read_text(),'links':[{'label':a,'href':b} for a,b in links],'proof_accepted':False,'RL_accepted':False,'broad_goal_complete':False}
save(folder/'report-data.json',data)
assert not (PUB/REL).exists();shutil.copytree(folder,PUB/REL)
index=PUB/'docs/research/gcts-rl-renewal/index.html';before_index=index.read_text();anchor='<section class="panel" id="paired-fixture">'
assert before_index.count('RESEARCH NOTEBOOK · 179')==1 and before_index.count(anchor)==1 and 'id="remote-eligibility"' not in before_index
panel='<section class="panel" id="remote-eligibility"><p class="eyebrow">COMPLETE PARTIAL CONTROL RECORD</p><h2>Check the branch before testing rejection.</h2><p>The expanded suite now returns a complete record: \\(28\\) reported passed and \\(15\\) skipped cases, within \\(10.642492\\,\\mathrm{s}\\). A remote marking rejects a pending key at row \\(8\\), while the actual global decision is FORCED at row \\(1\\). The boundary is ineligible for the immediate rejection test. All gaps remain explicit; no target proof search is admitted.</p><p>The actual first-ranked family has only one future member. A separate generic multi-member fixture is needed for selective rejection and remaining-family tests. The reader displays the saved remote tile, conflicting formulas and every returned case.</p><p><a href="remote-eligibility/reader.html#calibration">Actual marking conflict</a> · <a href="remote-eligibility/reader.html#cases">All control outcomes</a> · <a href="remote-eligibility/reader.html#records">Exact evidence</a>.</p></section>\n\n'
index.write_text(before_index.replace('RESEARCH NOTEBOOK · 179','RESEARCH NOTEBOOK · 180',1).replace(anchor,panel+anchor,1));assert pin(BASE/'docs/research/gcts-rl-renewal/index.html')==root_index
files=[{'path':str(p.relative_to(PUB)),**pin(p)} for p in sorted((PUB/REL).rglob('*')) if p.is_file()];files.append({'path':str(index.relative_to(PUB)),**pin(index)})
save(HERE/'publication-task-manifest-v1.json',{'schema':'ROOT-remote-eligibility-publication-manifest-v1','baseline':baseline,'files':files,'bytes':sum(x['bytes'] for x in files)})
with (HERE/'stage-paths-v1.nul').open('xb') as f:f.write(b'\0'.join(x['path'].encode() for x in files)+b'\0')
save(HERE/'copy-and-index-QA-v1.json',{'task_files':len(files),'raw_evidence_files':len(evidence),'baseline':baseline,'Root_index_preserved':root_index,'scientific_execution':False})
print(json.dumps({'task_files':len(files),'task_bytes':sum(x['bytes'] for x in files),'raw_evidence_files':len(evidence),'target_actuals_launched':False}))
