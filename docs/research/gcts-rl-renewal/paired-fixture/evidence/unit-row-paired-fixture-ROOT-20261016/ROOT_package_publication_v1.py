"""Package closed saved evidence and the authored reader; no scientific replay."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ACT=Path(__file__).resolve().parent;BASE=ACT.parent.parent
HERE=ACT.parent/'unit-row-paired-fixture-publication-ROOT-20261016';HERE.mkdir(exist_ok=True)
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015');REL=Path('docs/research/gcts-rl-renewal/paired-fixture');folder=BASE/REL
def pin(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(PUB),*args])
baseline='fe46dc68c5125d8f1b0cb0838d18b475109f8955'
assert not git('status','--porcelain') and git('rev-parse','HEAD').decode().strip()==baseline
root_index=pin(BASE/'docs/research/gcts-rl-renewal/index.html')
modes=('original-controls','domain-controls','advice-controls')
ds={m:read(ACT/('ROOT-'+m+'-disposition-v1.json')) for m in modes};ps={m:read(ACT/('ROOT-'+m+'-plan-v1.json')) for m in modes};ref=ps['advice-controls']
for m in modes:
 for k in ('sources','inputs','source_contract','reviews','runtime','limits','resource_rule'):assert ps[m][k]==ref[k]
 n=read(ACT/(m+'-external-v1/native-terminal.json'));assert n['all_reaped'] and n['caller_pid']==n['wait4_pid'] and n['caller_returncode']==(2 if m=='advice-controls' else 0)
 d=ds[m]
 if m=='advice-controls':assert d['actual_closed'] and d['failure_lifecycle_verified'] and not d['native_resources_qualified'] and not d['returned_control_record'] and d['passed_cases'] is None and d['skipped_cases'] is None
 else:assert d['complete_wire_verified'] and d['native_resources_qualified'] and d['controls_accepted'] and d['passed_cases']==17 and d['skipped_cases']==0
for arm in ('canonical-search','advised-search'):assert not (ACT/('ROOT-'+arm+'-plan-v1.json')).exists()
old=read(ACT.parent/'unit-row-latest-context-ROOT-20261016/ROOT-advice-controls-plan-v1.json')
for k in ('inputs','runtime','limits','resource_rule'):assert old[k]==ref[k]
assert {k for k in ref['sources'] if old['sources'][k]!=ref['sources'][k]}=={'advice_controls','intake'}
comparison={'schema':'ROOT-paired-fixture-comparison-v1','previous_goal_turn':'progress','current_goal_turn':'progress','broad_goal_complete':False,'scientific_replay':False,'actuals':3,'all_closed_and_reaped':True,'same_Source17_input2_reviews_runtime_limits_within_version':True,'across_versions_changed_sources':['advice_controls','intake'],'across_versions_same_mathematical_input_runtime_limits':True,'target_actuals_launched':0,'proof_accepted':False,'GCTS_advantage_accepted':False,'RL_accepted':False,'unqualified_marker_observations_only':True}
save(HERE/'ROOT-same-Source-comparison-v1.json',comparison)
evidence=[];by_original={};omitted=[]
def copy(src,dst):
 assert src.is_file() and not src.is_symlink() and src.suffix in ('.py','.json','.jsonl','.txt','.patch','.md') and not dst.exists()
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());r={'public_path':str(dst.relative_to(folder)),'original_path':str(src),**pin(src)};evidence.append(r);by_original[str(src)]=r['public_path']
groups=['unit-row-paired-fixture-controls-source-20261016','unit-row-paired-fixture-controls-independent-source-20261016','unit-row-paired-fixture-cold-ROOT-source-20261016','unit-row-paired-fixture-cold-independent-source-20261016','unit-row-paired-fixture-dependency-audit-source-20261016','unit-row-paired-fixture-ROOT-20261016']
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
for rel in ('unit-row-latest-context-typed-keys-cold-ROOT-source-20261016/unit_row_latest_context_cold_v13.py','unit-row-latest-context-typed-keys-cold-ROOT-source-20261016/Source-contract-v13.json','unit-row-continuation-progress-controls-source-20261016/compatible_fibres_controls_v6.py','unit-row-continuation-progress-controls-source-20261016/Source-contract-v6.json','unit-row-latest-context-ROOT-20261016/ROOT_close_advice_controls_saved_v11.py'):
 src=ACT.parent/rel
 if str(src) not in by_original:copy(src,folder/'evidence/parents'/src.parent.name/src.name)
copy(HERE/'ROOT-same-Source-comparison-v1.json',folder/'evidence/ROOT-same-Source-comparison-v1.json')
save(folder/'evidence-manifest.json',{'schema':'paired-fixture-evidence-manifest-v1','files':evidence,'scope':'Exact sources, independent negative7/corrected8 and caller14 reviews, all three closed current actuals. Diagnostics never substitute for case records.','omitted_public_duplicate_records':omitted,'omission_reason':'The complete canonical expanded records remain in their published lossless envelopes; no fields or cases removed.'})
d=ds['advice-controls'];roles={x['role']:x for x in d['retained_latest_context']['last_observations']}
stages=[{'label':m.replace('-',' '),'outcome':r'\(17\) passed; no skips' if m!='advice-controls' else 'UNKNOWN; no case record','native_ns':ds[m]['native_launch_to_postprobe_ns'],'peak_bytes':ds[m].get('aggregate_B_bytes',ds[m].get('aggregate_B_bytes_observed')),'qualified':ds[m]['native_resources_qualified']} for m in modes]
role_rows=[]
for role in ('proposer','fallback','completion','validator'):
 x=roles.get(role);role_rows.append({'role':role,'row':x['row'] if x else None,'selected_count':x['selected_count'] if x else None,'elapsed_ns':x['elapsed_from_launch_ns'] if x else None})
prefix='evidence/unit-row-paired-fixture-ROOT-20261016/'
links=[('Exact evidence manifest','evidence-manifest.json'),('Current unknown disposition',prefix+'ROOT-advice-controls-disposition-v1.json'),('Complete timeout scalar record',prefix+'advice-controls-owned-v1/unknown-diagnostic.json'),('Raw completion marker',prefix+'advice-controls-owned-v1/diagnostic-completion.json'),('Native trace and error',prefix+'advice-controls-external-v1/meter-stderr.txt'),('Native terminal and reaping',prefix+'advice-controls-external-v1/native-terminal.json'),('Once invocation',prefix+'advice-controls-external-v1/ONCE.json'),('Fresh postterminal observation',prefix+'advice-controls-external-v1/observation.json'),('Complete tool time bracket',prefix+'ROOT-advice-controls-tool-bracket-v1.json'),('Original controls disposition',prefix+'ROOT-original-controls-disposition-v1.json'),('Retained-state disposition',prefix+'ROOT-domain-controls-disposition-v1.json'),('Original controls lossless result',prefix+'original-controls-owned-v1/engine-result.json'),('Retained-state lossless result',prefix+'domain-controls-owned-v1/engine-result.json'),('Unexecuted version7 negative review','evidence/unit-row-paired-fixture-controls-independent-source-20261016/typed-Source-review-v7.json'),('Corrected version8 independent review',by_original[grant['dependency_reviews']['advice_controls_peer']['path']]),('Caller14 independent review',by_original[ref['reviews']['peer']['path']]),('Paired artifact and control contract','evidence/unit-row-paired-fixture-controls-source-20261016/Source-contract-v8.json'),('Current caller contract','evidence/unit-row-paired-fixture-cold-ROOT-source-20261016/Source-contract-v14.json'),('Saved-result checker review',prefix+'ROOT-saved-closer-Source-review-v1.json'),('Earlier complete observations','../latest-context/reader.html#results')]
data={'schema':'paired-fixture-saved-reader-v1','lead':'Independent review caught a real control defect. The revised paired boundary reaches a later diagnostic position, but the complete cluster suite still times out.','outcome':'Original search and retained-state controls each pass every test without skips. The expanded cluster suite is UNKNOWN: no guarded case record was returned. All three processes are closed and reaped. No target proof search was admitted.','stages':stages,'roles':role_rows,'observation_text':r'The trace includes the position after the paired continuation block and the start of the original remote-conflict lifecycle, at \(7.281975\,\mathrm{s}\) from launch. This is a reached-write observation, not an accepted case outcome. The last validator slot is row \(3\), entry count \(4\); later fallback and proposer slots have entry counts \(9\) and \(10\). These fields do not establish a successful PENDING receipt.','assessment':'The paired design has removed a static ambiguity: successful continuation and remote rejection now have distinct control boundaries and explicit evidence links. The current actual does not return the records needed to qualify either test. Its later marker position narrows investigation toward the original remote lifecycle, while leaving the intervening costs and execution path unqualified.','next_step':'Next, inspect whether the original remote-conflict boundary can reach its intended pending-member rejection branch under the real scheduler. Preserve all existing case meanings and complete fallback. Another unchanged rerun, extra logging or a larger limit would not resolve that semantic question.','trace':(ACT/'advice-controls-external-v1/meter-stderr.txt').read_text(),'links':[{'label':a,'href':b} for a,b in links],'proof_accepted':False,'RL_accepted':False,'broad_goal_complete':False}
save(folder/'report-data.json',data)
assert not (PUB/REL).exists();shutil.copytree(folder,PUB/REL)
index=PUB/'docs/research/gcts-rl-renewal/index.html';before=index.read_text();anchor='<section class="panel" id="latest-context">'
assert before.count('RESEARCH NOTEBOOK · 178')==1 and before.count(anchor)==1 and 'id="paired-fixture"' not in before
panel='<section class="panel" id="paired-fixture"><p class="eyebrow">PARALLEL REVIEW AND PAIRED CONTROLS</p><h2>Two boundaries for two cluster tests.</h2><p>Independent review caught a control reporting defect before execution. The corrected version keeps successful continuation separate from remote rejection and forced retirement. Fresh original and retained-state suites each pass all \\(17\\) tests without skips; the expanded cluster suite still returns UNKNOWN at the unchanged limit, with no case record.</p><p>The raw trace now includes the position after the paired continuation block and the start of the remote-conflict block. This does not certify a passed test or a discovered theorem. The next investigation is whether the original remote boundary reaches its intended rejection branch.</p><p><a href="paired-fixture/reader.html#results">Measured results and timing visual</a> · <a href="paired-fixture/reader.html#design">Paired control design</a> · <a href="paired-fixture/reader.html#parallel">What parallel review contributed</a> · <a href="paired-fixture/reader.html#records">Exact records</a>.</p></section>\n\n'
index.write_text(before.replace('RESEARCH NOTEBOOK · 178','RESEARCH NOTEBOOK · 179',1).replace(anchor,panel+anchor,1))
assert pin(BASE/'docs/research/gcts-rl-renewal/index.html')==root_index
files=[{'path':str(p.relative_to(PUB)),**pin(p)} for p in sorted((PUB/REL).rglob('*')) if p.is_file()];files.append({'path':str(index.relative_to(PUB)),**pin(index)})
save(HERE/'publication-task-manifest-v1.json',{'schema':'ROOT-paired-fixture-publication-manifest-v1','baseline':baseline,'files':files,'bytes':sum(x['bytes'] for x in files)})
with (HERE/'stage-paths-v1.nul').open('xb') as f:f.write(b'\0'.join(x['path'].encode() for x in files)+b'\0')
save(HERE/'copy-and-index-QA-v1.json',{'task_files':len(files),'raw_evidence_files':len(evidence),'baseline':baseline,'Root_index_preserved':root_index,'scientific_execution':False})
print(json.dumps({'task_files':len(files),'task_bytes':sum(x['bytes'] for x in files),'raw_evidence_files':len(evidence),'target_actuals_launched':False}))
