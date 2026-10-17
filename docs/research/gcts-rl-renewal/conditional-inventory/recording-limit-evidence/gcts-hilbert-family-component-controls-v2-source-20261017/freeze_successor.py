from pathlib import Path
import ast,json,hashlib,difflib,subprocess
D=Path('/private/tmp/gcts-hilbert-family-component-controls-v2-source-20261017')
P=Path('/private/tmp/gcts-hilbert-family-component-controls-source-20261017')
N=Path('/private/tmp/gcts-hilbert-family-component-controls-peer-20261017')
def ref(p):
 p=Path(p);assert not p.stat().st_flags&0x40000000,str(p)
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 p=D/n
 with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
def const(s,n):return next(ast.literal_eval(x.value)for x in ast.parse(s).body if isinstance(x,ast.Assign)and isinstance(x.targets[0],ast.Name)and x.targets[0].id==n)
def line(s,n):
 x=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign)and isinstance(x.targets[0],ast.Name)and x.targets[0].id==n)
 return ''.join(s.splitlines(keepends=True)[x.lineno-1:x.end_lineno])
oldh=(P/'hilbert_family_component_controls_v1.py').read_text()
hedits=[("VERSION = 'hilbert-shared-family-native-component-controls-v1'","VERSION = 'hilbert-shared-family-native-component-controls-v2-child-unknown'"),
("        continued=consume([],hint_checkpoint,child);evidence['child_continuation']=continued\n",
 "        continued=consume([],hint_checkpoint,child);evidence['child_continuation']=continued\n        if continued['status']=='UNKNOWN':\n            graph.rollback(root_checkpoint)\n            return finish('UNKNOWN','ACTUAL_CHILD_CONTINUATION_CHECK_UNFINISHED')\n")]
h=oldh
for a,b in hedits:assert h.count(a)==1;h=h.replace(a,b)
hp=D/'hilbert_family_component_controls_v2.py';hp.write_text(h)
olds=(P/'hilbert_family_component_controls_cold_v1.py').read_text();fixed=const(olds,'FIXED');fixed['component_controls']=ref(hp)
cedits=[(line(olds,'VERSION'),"VERSION='ROOT-Hilbert-shared-family-component-controls-cold-v2-child-unknown'\n"),
(line(olds,'FIXED'),'FIXED='+repr(fixed)+'\n'),
("contract['schema']=='ROOT-Hilbert-family-component-controls-Source-contract-v1'","contract['schema']=='ROOT-Hilbert-family-component-controls-Source-contract-v2'")]
s=olds
for a,b in cedits:assert s.count(a)==1;s=s.replace(a,b)
sp=D/'hilbert_family_component_controls_cold_v2.py';sp.write_text(s)
for body,p in [(h,hp),(s,sp)]:ast.parse(body);compile(body,str(p),'exec')
all_deltas={};audit_regions={};patches={}
for role,old,new,edits,op,np in [('controls',oldh,h,hedits,P/'hilbert_family_component_controls_v1.py',hp),('caller',olds,s,cedits,P/'hilbert_family_component_controls_cold_v1.py',sp)]:
 inverse=new
 for a,b in reversed(edits):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
 assert inverse==old and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
 unchanged=[];changed=[]
 ot,nt=ast.parse(old),ast.parse(new)
 for x in ot.body:
  if not isinstance(x,(ast.FunctionDef,ast.ClassDef)):continue
  y=next(z for z in nt.body if isinstance(z,type(x))and z.name==x.name)
  if ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False):
   assert old.splitlines(keepends=True)[x.lineno-1:x.end_lineno]==new.splitlines(keepends=True)[y.lineno-1:y.end_lineno]
   unchanged.append(x.name)
  else:changed.append(x.name)
 assert changed==(['run_component_controls']if role=='controls'else ['main'])
 audit_regions[role]={'raw_AST_exact':unchanged,'changed':changed}
 pp={}
 for direction,left,right in [('forward',old,new),('inverse',new,old)]:
  p=D/(role+'-v1-to-v2-'+direction+'.patch');p.write_text(''.join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile='target.py',tofile='target.py')))
  wd=D/('patch-audit-'+role+'-'+direction);wd.mkdir();(wd/'target.py').write_text(left)
  r=subprocess.run(['patch','--batch','--fuzz=0','-p0','-i',str(p)],cwd=wd,capture_output=True,text=True)
  assert r.returncode==0 and (wd/'target.py').read_text()==right,(r.stdout,r.stderr)
  pp[direction]=ref(p)
 patches[role]=pp
 all_deltas[role]=put(role+'-Source-delta-v2.json',{'schema':'Hilbert-component-controls-'+role+'-immediate-delta-v2','source_only':True,'parent_source':ref(op),'source':ref(np),'raw_edits':[{'before':a,'after':b}for a,b in edits],'full_raw_AST_inverse':True,'actual_patch_F0_directions':2,'patches':pp,'inherited_regions':audit_regions[role],'parent_addition_delta':ref(P/(role+'-Source-delta-v1.json')),'prior_frozen_Source_modified':False})
source=ref(sp);helper=ref(hp);sources={'intake':source,**fixed}
negative=ref(N/'typed-Source-review-v1.json');nv=json.loads(Path(negative['path']).read_text());assert nv['source_review_passed']is False
collector_peer=ref(N/'collector-typed-Source-review-v2.json');cv=json.loads(Path(collector_peer['path']).read_text());assert cv['source_review_passed']is True and cv['source']==fixed['collector']
api=json.loads((P/'API-wire-v1.json').read_text());api['schema']='Hilbert-family-component-controls-API-v2';api['cold_VERSION']=const(s,'VERSION');api['controls_VERSION']=const(h,'VERSION');api['correction']='ACTUAL child continuation UNKNOWN is checked before BRANCH/nonbranch dispatch, rolls back to owned root and returns whole component UNKNOWN. It can neither set a completed child recheck nor become a negative ValueError. All other behavior/wires/caps/model remain unchanged.';api['source_versioning']='Current cold compiles actual separately named V2 helper source and requires its current source hash. Collector V2 consumes actual adapter V3; no façade/version alias.'
ar=put('API-wire-v2.json',api)
audit=put('static-audit-v2.json',{'schema':'Hilbert-family-component-controls-static-audit-v2','source_only':True,'scientific_calls':0,'module_evaluations':0,'clock_calls':0,'compile_without_evaluation':True,'actual_patch_F0_directions':4,'whole_raw_AST_inverse':True,'raw_edit_counts':{'controls':2,'caller':3},'regions':audit_regions,'correction_static_order':'Native child decision -> consume -> evidence retains returned packet -> explicit UNKNOWN rollback/finish -> actual child kind dispatch. No catch or changed native callback error taxonomy.','all_other_limits_models_and_wire_fields_raw_exact':True,'preserved_negative':negative})
hc=json.loads((P/'controls-Source-contract-v1.json').read_text());hc.update(schema='Hilbert-family-component-controls-helper-Source-contract-v2',source=helper,sources={'component_controls':helper},API=ar,delta=all_deltas['controls'],static_audit=audit,dependencies=fixed,parent_contract=ref(P/'controls-Source-contract-v1.json'),preserved_negative=negative,correction=api['correction']);hc['Review_ABI']['source']=helper;hc['Review_ABI']['sources']=hc['sources'];hc['Review_ABI']['schema']='Hilbert-family-component-controls-helper-typed-Source-review-v2'
hcr=put('controls-Source-contract-v2.json',hc)
c=json.loads((P/'Source-contract-v1.json').read_text());c.update(schema='ROOT-Hilbert-family-component-controls-Source-contract-v2',source=source,sources=sources,API=ar,delta=all_deltas['caller'],controls_contract=hcr,controls_delta=all_deltas['controls'],static_audit=audit,parent_contract=ref(P/'Source-contract-v1.json'),preserved_negative=negative,correction=api['correction'])
c['component_peers']['collector_v2']=collector_peer;c['collector_current_peer']='Exact current collectorV2 peer is bound above; no runtime qualification. Current caller/helper distinct review still required before actual.';c['Review_ABI']['source']=source;c['Review_ABI']['sources']=sources;c['Review_ABI']['schema']='ROOT-Hilbert-family-component-controls-cold-typed-Source-review-v2'
cr=put('Source-contract-v2.json',c)
hr=put('handoff-v2.json',{'schema':'Hilbert-family-component-controls-handoff-v2','source_only':True,'scientific_calls':0,'module_evaluations':0,'clock_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':source,'sources':sources,'source_contract':cr,'controls_source':helper,'controls_contract':hcr,'API':ar,'deltas':all_deltas,'static_audit':audit,'preserved_negative':negative,'collector_current_peer':collector_peer,'Review_ABI':c['Review_ABI']})
print(json.dumps({'handoff':hr,'source':source,'controls':helper,'contract':cr},indent=2))
