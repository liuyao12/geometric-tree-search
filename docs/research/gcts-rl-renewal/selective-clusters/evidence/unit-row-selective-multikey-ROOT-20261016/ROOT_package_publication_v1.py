"""Publish saved current C-control evidence only; no scientific replay."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ACT=Path(__file__).resolve().parent;BASE=ACT.parent.parent
HERE=ACT.parent/'unit-row-selective-multikey-publication-ROOT-20261016';HERE.mkdir(exist_ok=True)
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015');REL=Path('docs/research/gcts-rl-renewal/selective-clusters');folder=BASE/REL
def pin(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(PUB),*args])
baseline='2124598c437d763e3856d634c8e0c5cfb532ce0e'
assert not git('status','--porcelain') and git('rev-parse','HEAD').decode().strip()==baseline
root_index=pin(BASE/'docs/research/gcts-rl-renewal/index.html');modes=('original-controls','domain-controls','advice-controls')
partial=ACT/'ROOT-advice-controls-partial-disposition-v1.json'
advice_disposition=partial if partial.exists() else ACT/'ROOT-advice-controls-disposition-v1.json'
ds={m:read(advice_disposition if m=='advice-controls' else ACT/('ROOT-'+m+'-disposition-v1.json')) for m in modes}
ps={m:read(ACT/('ROOT-'+m+'-plan-v1.json')) for m in modes};ref=ps['advice-controls']
for m in modes:
 for k in ('sources','inputs','source_contract','reviews','runtime','limits','resource_rule'):assert ps[m][k]==ref[k]
 n=read(ACT/(m+'-external-v1/native-terminal.json'));assert n['all_reaped'] and n['caller_pid']==n['wait4_pid'] and n['caller_returncode']==0
 assert ds[m]['native_resources_qualified'] and ds[m]['complete_wire_verified']
 if m!='advice-controls':assert ds[m]['controls_accepted'] and ds[m]['passed_cases']==17 and ds[m]['skipped_cases']==0
result=read(ACT/'ROOT-advice-controls-expanded-result-v1.json');c=result['controls'];art=c['artifacts'];cal=art.get('remote_eligibility');fixture=art.get('selective_C_fixture')
assert len(c['cases'])==43 and c['passed']+c['skipped']==43
if partial.exists():assert ds['advice-controls']['actual_closed'] and not ds['advice-controls']['controls_accepted'] and not ds['advice-controls']['target_admission_qualified']
else:assert ds['advice-controls']['controls_accepted'] and c['passed']==43 and c['skipped']==0 and c['additional_coverage_gaps']==[]
targets={}
for arm in ('canonical-search','advised-search'):
 target_plan=read(ACT/('ROOT-'+arm+'-plan-v1.json'));target=read(ACT/('ROOT-'+arm+'-disposition-v1.json'))
 for k in ('sources','inputs','source_contract','reviews','runtime','limits','resource_rule'):assert target_plan[k]==ref[k]
 assert target['status']=='UNKNOWN' and target['actual_closed'] and target['all_reaped'] and target['failure_lifecycle_verified'] and not target['native_resources_qualified'] and not target['logical_proof_accepted']
 targets[arm]=target
evidence=[];by_original={};omitted=[]
def copy(src,dst):
 assert src.is_file() and not src.is_symlink() and src.suffix in ('.py','.json','.jsonl','.txt','.patch','.md') and not dst.exists()
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());r={'public_path':str(dst.relative_to(folder)),'original_path':str(src),**pin(src)};evidence.append(r);by_original[str(src)]=r['public_path']
groups=['unit-row-selective-C-controls-source-20261016','unit-row-selective-C-controls-independent-source-20261016','unit-row-selective-multikey-cold-ROOT-source-20261016','unit-row-selective-multikey-cold-independent-source-20261016','unit-row-selective-multikey-ROOT-20261016']
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
for rel in ('unit-row-paired-fixture-ROOT-20261016/ROOT_close_advice_controls_saved_v14.py','unit-row-remote-eligibility-ROOT-20261016/ROOT_close_advice_controls_partial_saved_v15.py','unit-row-remote-eligibility-controls-source-20261016/compatible_fibres_controls_v9.py','unit-row-remote-eligibility-cold-ROOT-source-20261016/unit_row_remote_eligibility_cold_v15.py','unit-row-remote-eligibility-cold-ROOT-source-20261016/Source-contract-v15.json'):
 src=ACT.parent/rel
 if str(src) not in by_original:copy(src,folder/'evidence/parents'/src.parent.name/src.name)
save(folder/'evidence-manifest.json',{'schema':'selective-cluster-evidence-manifest-v1','files':evidence,'scope':'Exact current Sources/reviews and all three closed endpoints, including every expanded43 outcome. Partial disposition, when present, accepts wire/native/literal joins only.','omitted_public_duplicate_records':omitted,'omission_reason':'Original and retention complete canonical records remain in the published lossless envelopes.'})
conflict=None
if cal:
 before=cal['before_decision']['state'];bad=cal['bad_key'];marks={tuple(p):v for p,v in before['m']};pre=bad['type_preimage']
 for required,offset in zip(pre['ordered_premise_formulas'],pre['ordered_offsets']):
  point=(1,bad['translation'][1]+offset);value=marks.get(point)
  if value and value[0]=='formula' and json.loads(value[1])!=required:
   conflict={'point':list(point),'assigned_formula':json.loads(value[1]),'required_formula':required,'remote_row':cal['remote']['placement_key']['translation'][1],'pending_row':bad['translation'][1],'pending_rule':{'mp':'MP','generalize':'UG','instantiate':'UI'}.get(pre['primitive_witness']['rule'],pre['primitive_witness']['rule']),'decision':{k:v for k,v in cal['actual_global_decision'].items() if k!='candidate'}};break
prefix='evidence/'+ACT.name+'/'
links=[('Exact evidence manifest','evidence-manifest.json'),('Complete current disposition',prefix+advice_disposition.name),('Complete expanded control record',prefix+'ROOT-advice-controls-expanded-result-v1.json'),('Lossless result envelope',prefix+'advice-controls-owned-v1/engine-result.json'),('Transport concordance',prefix+'ROOT-advice-controls-transport-concordance-v1.json'),('Native terminal and reaping',prefix+'advice-controls-external-v1/native-terminal.json'),('Fresh postterminal observation',prefix+'advice-controls-external-v1/observation.json'),('Original controls disposition',prefix+'ROOT-original-controls-disposition-v1.json'),('Retained-state controls disposition',prefix+'ROOT-domain-controls-disposition-v1.json'),('Independent controls review',by_original[grant['dependency_reviews']['advice_controls_peer']['path']]),('Independent caller review',by_original[ref['reviews']['peer']['path']]),('Control contract','evidence/unit-row-selective-C-controls-source-20261016/Source-contract-v11.json'),('Historical prose erratum','evidence/unit-row-selective-C-controls-source-20261016/inherited-paired-prose-erratum-v1.json'),('Preserved pre-activation negative review','evidence/unit-row-selective-C-controls-independent-source-20261016/typed-Source-review-v10.json'),('Previous complete partial result','../remote-eligibility/reader.html#results')]
stages=[{'label':m.replace('-',' '),'outcome':r'\(17\) passed; no skips' if m!='advice-controls' else '\\('+str(c['passed'])+'\\) reported passed; \\('+str(c['skipped'])+'\\) skipped','native_ns':ds[m]['native_launch_to_postprobe_ns'],'peak_bytes':ds[m]['aggregate_B_bytes'],'qualified':True} for m in modes]
summary={k:v for k,v in (cal or {}).items() if k in ('schema','fixture_ref','family_id','eligible_actual_branch','normal_search_started','normalization_complete','eligibility_gap')}
if cal:summary.update(actual_global_decision=conflict['decision'] if conflict else {k:v for k,v in cal['actual_global_decision'].items() if k!='candidate'},forced_normalization_steps=len(cal['normalization']))
data={'schema':'selective-cluster-saved-reader-v1','lead':'Three independently owned boundaries separate first-ranked adoption, successful continuation and selective rejection.','outcome':f"Original and retained-state controls each pass all \\(17\\) tests. The expanded suite reports \\({c['passed']}\\) passed and \\({c['skipped']}\\) skipped cases. Complete control qualification is {'accepted' if ds['advice-controls']['controls_accepted'] else 'not accepted'}. All processes are closed and reaped.",'stages':stages,'calibration':summary,'conflict':conflict,'cases':[{'case':x['case'],'status':x['status'],'observed':{'reason':x['observed'].get('reason','')} if x['status']=='SKIPPED' else {}} for x in c['cases']], 'calibration_text':'The diagram translates the actual saved C boundary. Component legality and actual global scheduling are recorded separately. Every normalization placement follows a real global FORCED decision; an unrelated decision or occupied pending row leaves an essential gap.','survivor_text':'No normalized survivor observation is qualified.' if not cal or not cal.get('normalization_complete') else 'After normalization, an independent component check still accepts the first different pending key at '+r'\(r='+str(cal['survivor_key']['translation'][1])+r'\). It remains an uninstalled option.','case_note':r'All \(43\) returned outcomes are shown. Full observations are in the expanded record. A partial closer, when present, checks complete wire, native resources and literal saved joins without independently accepting reported PASSED semantics.','assessment':'The control separates a cluster’s internal links from its external receptors. Rejecting one member can invalidate a preferred family while leaving another member geometrically legal. This is a search-policy cleanup question; pending members never become facts merely through preference.','next_step':'Any remaining essential gap must be resolved before the paired target searches are admitted. The comparison must then count all proposal, checking and search costs to a complete verified proof.','trace':(ACT/'advice-controls-external-v1/meter-stderr.txt').read_text(),'links':[{'label':a,'href':b} for a,b in links],'proof_accepted':False,'RL_accepted':False,'broad_goal_complete':False}
data['target']=read(Path(ref['inputs']['declaration']['path']))['target']
data['target_text']=r'Both point-search arms reach the original \(20\,\mathrm{s}\) deadline without a proof. The complete failure records are closed and reaped. Their saved producer counts below are unqualified diagnostics, not accepted trajectories or positive resource results.'
data['target_diagnostics']=[]
for arm,target in targets.items():
 counts=target['observations']['counts']
 data['target_diagnostics'].append({'arm':arm,'nodes':counts['nodes'],'branches':counts['branches'],'backtracks':counts['backtracks'],'advice_selected':counts['advice_selected'],'pending_checks':counts['pending_checks']})
 data['stages'].append({'label':arm.replace('-',' '),'outcome':'UNKNOWN; original deadline','native_ns':target['native_launch_to_postprobe_ns'],'peak_bytes':target['aggregate_B_bytes_observed'],'qualified':False})
 data['links'].append({'label':arm+' complete failure disposition','href':prefix+'ROOT-'+arm+'-disposition-v1.json'})
 data['links'].append({'label':arm+' raw saved producer diagnostic','href':prefix+arm+'-owned-v1/unknown-diagnostic.json'})
data['links'].append({'label':'Earlier ordinary proof, line by line','href':'../shared-bounded-proofs/reader.html#reader'})
data['assessment']=r'The control-only C family exercises selective rejection and restoration successfully. The paired target runs still discover no proof. The advised producer reports choosing advice at every observed branch, with no pending-key continuation check before interruption. Fewer observed branches do not establish a benefit when neither arm reaches a checked proof.'
data['next_step']=r'The earlier ordinary producer already found an independently checked proof of this arithmetic statement. Its representation and work caps differ, so its timing is not a matched speed ratio. The next experiment should diagnose the advised choices and compare total verified-proof cost. These unit-row controls do not establish the full reference graph, fractional/shared support, a universal Wang palette, learned failure markings or RL.'
save(folder/'report-data.json',data)
assert not (PUB/REL).exists();shutil.copytree(folder,PUB/REL)
index=PUB/'docs/research/gcts-rl-renewal/index.html';old=index.read_text();anchor='<section class="panel" id="remote-eligibility">'
assert old.count('RESEARCH NOTEBOOK · 180')==1 and old.count(anchor)==1 and 'id="selective-clusters"' not in old
panel='<section class="panel" id="selective-clusters"><p class="eyebrow">PARALLEL DEVELOPMENT AND INDEPENDENT REVIEW</p><h2>Give selective rejection its own boundary.</h2><p>Three agents divide control implementation, independent correctness review and saved-result verification. Independent review caught two bugs before activation. The new control keeps the first-ranked and successful-continuation contexts intact while giving selective rejection a separately owned cluster family.</p><p>The fresh expanded suite reports \\('+str(c['passed'])+'\\) passed and \\('+str(c['skipped'])+'\\) skipped cases. Both paired target searches reach the original deadline without a proof. <a href="selective-clusters/reader.html#calibration">Inspect the actual marking boundary</a>, <a href="selective-clusters/reader.html#cases">all outcomes</a> and <a href="selective-clusters/reader.html#records">exact records</a>. No new theorem or RL advantage is claimed.</p></section>\n\n'
index.write_text(old.replace('RESEARCH NOTEBOOK · 180','RESEARCH NOTEBOOK · 181',1).replace(anchor,panel+anchor,1));assert pin(BASE/'docs/research/gcts-rl-renewal/index.html')==root_index
files=[{'path':str(p.relative_to(PUB)),**pin(p)} for p in sorted((PUB/REL).rglob('*')) if p.is_file()];files.append({'path':str(index.relative_to(PUB)),**pin(index)})
save(HERE/'publication-task-manifest-v1.json',{'schema':'ROOT-selective-cluster-publication-manifest-v1','baseline':baseline,'files':files,'bytes':sum(x['bytes'] for x in files)})
with (HERE/'stage-paths-v1.nul').open('xb') as f:f.write(b'\0'.join(x['path'].encode() for x in files)+b'\0')
save(HERE/'copy-and-index-QA-v1.json',{'task_files':len(files),'raw_evidence_files':len(evidence),'baseline':baseline,'Root_index_preserved':root_index,'scientific_execution':False})
print(json.dumps({'task_files':len(files),'task_bytes':sum(x['bytes'] for x in files),'raw_evidence_files':len(evidence)}))
