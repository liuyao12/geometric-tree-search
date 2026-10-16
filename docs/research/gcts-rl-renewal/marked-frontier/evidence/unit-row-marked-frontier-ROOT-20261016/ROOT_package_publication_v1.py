"""Publish saved current C-control evidence only; no scientific replay."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ACT=Path(__file__).resolve().parent;BASE=ACT.parent.parent
HERE=ACT.parent/'unit-row-marked-frontier-publication-ROOT-20261016';HERE.mkdir(exist_ok=True)
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015');REL=Path('docs/research/gcts-rl-renewal/marked-frontier');folder=BASE/REL
def pin(p):
 b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(PUB),*args])
baseline='83bd1caa9c6a437bd5b723ceb3457ed1175dc4e0'
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
 if m!='advice-controls':assert ds[m]['controls_accepted'] and ds[m]['passed_cases']==(23 if m=='original-controls' else 17) and ds[m]['skipped_cases']==0
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
groups=['unit-row-marking-aware-engine-source-20261016','unit-row-marking-aware-engine-independent-source-20261016','unit-row-marking-aware-controls-source-20261016','unit-row-marking-aware-controls-independent-source-20261016','unit-row-marked-frontier-cold-ROOT-source-20261016','unit-row-marked-frontier-cold-independent-source-20261016','unit-row-marked-frontier-ROOT-20261016']
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

original=read(ACT/'ROOT-original-controls-expanded-result-v1.json')['controls'];extra=original['cases'][17:]
assert len(original['cases'])==23 and len(extra)==6 and all(x['status']=='PASSED' for x in original['cases'])
comp=extra[2]['observed'];fill=extra[4]['observed'];initial=comp['initial_state'];assert comp['ROW_decision']=={'kind':'BRANCH','row':0} and comp['MARK_decision']=={'kind':'BRANCH','row':3}
assert fill['next_decision']=={'kind':'BRANCH','row':6} and fill['restored_decision']=={'kind':'BRANCH','row':3}
for rel in ('unit-row-selective-C-controls-source-20261016/Source-contract-v11.json','unit-row-selective-C-controls-source-20261016/handoff-v11.json','unit-row-selective-multikey-cold-ROOT-source-20261016/unit_row_selective_multikey_cold_v16.py','unit-row-selective-multikey-cold-ROOT-source-20261016/Source-contract-v16.json','unit-row-lazy-engine-controls-source-20261015/lazy_engine_adversarial_controls_v1.py','unit-row-lazy-engine-controls-source-20261015/Source-contract-v1.json','unit-row-compatible-fibres-engine-source-20261016/lazy_unit_row_global_engine_v8.py'):
 src=ACT.parent/rel
 if str(src) not in by_original:copy(src,folder/'evidence/parents'/src.parent.name/src.name)
# Include the current original full record for direct boundary inspection.
src=ACT/'ROOT-original-controls-expanded-result-v1.json';copy(src,folder/'evidence'/ACT.name/src.name);omitted=[r for r in omitted if r['original_path']!=str(src)]
# The earlier manifest is written after all current raw copies below.
prefix='evidence/'+ACT.name+'/'
links=[('Exact evidence manifest','evidence-manifest.json'),('Original23 complete disposition',prefix+'ROOT-original-controls-disposition-v1.json'),('Full original23 boundary record',prefix+'ROOT-original-controls-expanded-result-v1.json'),('Retention17 disposition',prefix+'ROOT-domain-controls-disposition-v1.json'),('Cluster43 disposition',prefix+'ROOT-advice-controls-disposition-v1.json'),('Complete current cluster record',prefix+'ROOT-advice-controls-expanded-result-v1.json'),('Current target policy concordance',prefix+'ROOT-target-policy-saved-join-v1.json'),('Engine9 independent review','evidence/unit-row-marking-aware-engine-independent-source-20261016/typed-Source-review-v1.json'),('Original23 independent review','evidence/unit-row-marking-aware-controls-independent-source-20261016/typed-Source-review-v2.json'),('Caller17 independent review','evidence/unit-row-marked-frontier-cold-independent-source-20261016/typed-Source-review-v17.json'),('Original23 saved closer Root review',prefix+'ROOT-original23-closer-Source-review-v1.json'),('Earlier ordinary proof, line by line','../shared-bounded-proofs/reader.html#reader'),('Previous ROW target experiment','../selective-clusters/reader.html#targets')]
stages=[]
for mode,n in (('original-controls',23),('domain-controls',17),('advice-controls',43)):
 d=ds[mode];stages.append({'label':mode.replace('-',' '),'outcome':r'\('+str(n)+r'\) passed; no skips','native_ns':d['native_launch_to_postprobe_ns'],'peak_bytes':d['aggregate_B_bytes'],'qualified':True})
target_diagnostics=[]
for arm,d in targets.items():
 counts=d['observations']['counts'];target_diagnostics.append(dict(arm=arm,**{k:counts[k] for k in ('nodes','branches','backtracks','advice_selected','forced')}))
 stages.append({'label':arm.replace('-',' '),'outcome':'UNKNOWN; original deadline','native_ns':d['native_launch_to_postprobe_ns'],'peak_bytes':d['aggregate_B_bytes_observed'],'qualified':False})
 links.extend([{'label':arm+' complete failure disposition','href':prefix+'ROOT-'+arm+'-disposition-v1.json'},{'label':arm+' raw saved diagnostic','href':prefix+arm+'-owned-v1/unknown-diagnostic.json'}])
phases={'initial':{'state':initial,'mark_row':3,'explanation':r'The same original point state gives ROW branch \(r=0\), MARK branch \(r=3\). Assigned output formulas remain unproved obligations.'},'filled':{'state':fill['classified']['state'],'mark_row':6,'explanation':r'After a legal public UG fill at \(r=3\), the actual MARK decision selects \(r=6\). The test does not rerun ROW on this state.'},'restored':{'state':fill['restored']['state'],'mark_row':3,'explanation':r'Owned rollback restores the entire warm snapshot. The actual MARK decision again selects \(r=3\).'}}
mark_value=next(value for point,value in initial['m'] if point==[1,3]);assert mark_value[0]=='formula'
data={'schema':'marked-frontier-saved-reader-v1','lead':'The new rule follows an assigned output constraint within the earliest generation. Its mechanism checks pass; both target searches still return UNKNOWN.','outcome':r'All \(23\) policy/original controls, \(17\) retention controls and \(43\) cluster controls pass without skips. Both MARK target arms reach the original \(20\,\mathrm{s}\) deadline without a proof. All five actuals are closed and reaped.','stages':stages,'phases':phases,'pending_formula':json.loads(mark_value[1]),'target':read(Path(ref['inputs']['declaration']['path']))['target'],'cases':[{'case':x['case'],'status':x['status'],'scope':x['scope'],'observed':{'reason':x['observed'].get('reason','')}} for x in extra],'target_diagnostics':target_diagnostics,'target_text':r'Both current runs start with the constrained target at row \(23\). Saved producer prefixes then report dead early-premise contexts. Each records \(17\) branch placements and \(16\) backtracks before interruption. These are unqualified producer observations; they do not establish accepted trajectories or positive resource results.','assessment':'The frontier policy does change the observed search direction. It does not establish a proof-search benefit in this experiment. Independent review and current controls qualify the implementation mechanism in its stated unit-row scope, while the target results remain UNKNOWN. The earlier ordinary search already found a checked proof of this statement.','next_step':'Next, freshly certify concrete local dead-end contexts before treating them as failure-learning labels. Any synthesized extra marking needs an explicit point domain, proof scope, positive replay and actual graph-pruning measurement. Saved interrupted traces alone cannot justify generalized exclusions or learned-mark activation.','links':[{'label':x[0],'href':x[1]} if type(x) is tuple else x for x in links],'proof_accepted':False,'RL_accepted':False,'broad_goal_complete':False}
save(folder/'report-data.json',data)
save(folder/'evidence-manifest.json',{'schema':'marked-frontier-evidence-manifest-v1','files':evidence,'scope':'Current Source17/input2, genuine23/17/43 controls and both closed UNKNOWN target endpoints. Saved reader performs no scientific replay.','omitted_public_duplicate_records':omitted,'omission_reason':'Retention expanded record remains whole in the published lossless envelope.'})
assert not (PUB/REL).exists();shutil.copytree(folder,PUB/REL)
index=PUB/'docs/research/gcts-rl-renewal/index.html';old=index.read_text();anchor='<section class="panel" id="selective-clusters">'
assert old.count('RESEARCH NOTEBOOK · 181')==1 and old.count(anchor)==1 and 'id="marked-frontier"' not in old
panel='<section class="panel" id="marked-frontier"><p class="eyebrow">MARKING-AWARE FRONTIER · FIVE CLOSED ACTUALS</p><h2>Follow the constrained output; both targets remain unknown.</h2><p>All \\(23\\) policy/original, \\(17\\) retention and \\(43\\) cluster controls pass without skips. In a real original-language fixture, ROW chooses row \\(0\\), MARK row \\(3\\); after a legal fill MARK chooses row \\(6\\), and owned rollback restores row \\(3\\). Both target arms use the new generation tie and reach the original deadline without a proof. No acceleration or RL benefit is claimed.</p><p><a href="marked-frontier/reader.html#boundary">Interact with the actual saved boundary</a> · <a href="marked-frontier/reader.html#targets">Inspect both target outcomes</a> · <a href="marked-frontier/reader.html#records">Read exact evidence</a>.</p></section>\n\n'
index.write_text(old.replace('RESEARCH NOTEBOOK · 181','RESEARCH NOTEBOOK · 182',1).replace(anchor,panel+anchor,1));assert pin(BASE/'docs/research/gcts-rl-renewal/index.html')==root_index
files=[{'path':str(p.relative_to(PUB)),**pin(p)} for p in sorted((PUB/REL).rglob('*')) if p.is_file()];files.append({'path':str(index.relative_to(PUB)),**pin(index)})
save(HERE/'publication-task-manifest-v1.json',{'schema':'ROOT-selective-cluster-publication-manifest-v1','baseline':baseline,'files':files,'bytes':sum(x['bytes'] for x in files)})
with (HERE/'stage-paths-v1.nul').open('xb') as f:f.write(b'\0'.join(x['path'].encode() for x in files)+b'\0')
save(HERE/'copy-and-index-QA-v1.json',{'task_files':len(files),'raw_evidence_files':len(evidence),'baseline':baseline,'Root_index_preserved':root_index,'scientific_execution':False})
print(json.dumps({'task_files':len(files),'task_bytes':sum(x['bytes'] for x in files),'raw_evidence_files':len(evidence)}))
