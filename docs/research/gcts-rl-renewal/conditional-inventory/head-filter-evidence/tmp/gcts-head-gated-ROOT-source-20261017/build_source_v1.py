"""Current Source/contract/patch metadata only; no scientific module evaluation."""
import ast,difflib,hashlib,json,subprocess
from pathlib import Path
S=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017')
P=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(p.read_bytes())
def save(n,v):
 p=S/n;assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');return ref(p)
def literal(raw,name,value):
 n=next(n for n in ast.parse(raw).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets));a=raw.splitlines(keepends=True)
 return ''.join(a[:n.lineno-1])+name+'='+repr(value)+'\n'+''.join(a[n.end_lineno:])
def source(n,parent,raw):
 p=S/n;assert not p.exists();compile(raw,str(p),'exec',dont_inherit=True);p.write_text(raw);a=parent.read_text()
 for direction,x,y in [('forward',a,raw),('inverse',raw,a)]:
  (S/(n+'.'+direction+'.patch')).write_text(''.join(difflib.unified_diff(x.splitlines(keepends=True),y.splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py')))
 return ref(p)
# Ready only after distinct implementation packet freezes.
ph=load(Path('/private/tmp/gcts-head-gated-provider-source-20261017/handoff-v8-2.json'))
eh=load(Path('/private/tmp/gcts-head-gated-family-engine-source-20261017/handoff-v7.json'))
c=load(P/'Source-contract-v2.json');h=load(P/'handoff-v2.json')
fixed={k:v for k,v in c['sources'].items()if k!='intake'}
fixed['receiver_provider']=ph['source'];fixed['family_engine']=eh['source']
fixed['head_gate']=ref(Path('/private/tmp/gcts-coarse-head-plan-marks-source-20261017/coarse_formula_head_plan_marks_v1.py'))
helper=(P/'receiver_inference_cases_v1.py').read_text();helper=literal(helper,'VERSION','ROOT-receiver-inference-cases-v2-head-gated')
needle="            residual_policy=modules['residual_policy'], mined=copy(mined),";assert helper.count(needle)==1
helper=helper.replace(needle,"            residual_policy=modules['residual_policy'], head_gate_module=modules['head_gate'],\n            mined=copy(mined),")
fixed['receiver_cases']=source('head_gated_receiver_cases_v1.py',P/'receiver_inference_cases_v1.py',helper)
raw=(P/'receiver_inference_cold_v2.py').read_text();raw=literal(raw,'VERSION','ROOT-receiver-inference-probe-cold-v3-head-gated');raw=literal(raw,'FIXED',fixed)
intake=source('head_gated_receiver_cold_v1.py',P/'receiver_inference_cold_v2.py',raw)
c['sources']={'intake':intake,**fixed};assert len(c['sources'])==22 and len(c['inputs'])==10
c['parent_source']=ref(P/'receiver_inference_cold_v2.py')
c['successor_scope']='Current provider8/head-gate module and engine7 metadata pins; helper ownVERSION plus explicit head_gate_module injection; caller ownVERSION/FIXED only; saved-reader only current contract/responseVERSION. Original17/input2/24rows/B12N44, complete fallback/scheduler, frozen inventory, matching modes/allocations/caps and all native/guard/closure machinery unchanged. New planning gate cost stays inside same provider1m/native20s. No theorem or speed claim.'
c['head_gate_integration']={'source':fixed['head_gate'],'source_peer':ref(Path('/private/tmp/gcts-coarse-head-plan-marks-peer-20261017/typed-Source-review-v1.json')),'call_site':'Provider after common whole physical-plan construction and attempted assignment increment, before matching/binding, both modes.','authority':'Completed known head conflict skips only this advisory plan. Unknown/absent passes; full native fallback and fresh admission unchanged. No native m5 activation or learned marking.','provider_handoff':ref(Path(ph['source']['path']).parent/'handoff-v8-2.json'),'engine_handoff':ref(Path(eh['source']['path']).parent/'handoff-v7.json')}
cref=save('Source-contract-v1.json',c)
reader=(P/'ROOT_read_receiver_inference_saved_v2.py').read_text();reader=literal(reader,'CURRENT_CONTRACT',cref);reader=reader.replace('ROOT-receiver-inference-probe-cold-v2','ROOT-receiver-inference-probe-cold-v3-head-gated')
rref=source('ROOT_read_head_gated_receiver_saved_v1.py',P/'ROOT_read_receiver_inference_saved_v2.py',reader)
rc=load(P/'reader-Source-contract-v2.json');rc.update(source=rref,current_operative_contract=cref,parent_source=ref(P/'ROOT_read_receiver_inference_saved_v2.py'));rcref=save('reader-Source-contract-v1.json',rc)
h.update(source=intake,sources=c['sources'],source_contract=cref,reader=rref,reader_source_contract=rcref,parent_handoff=ref(P/'handoff-v2.json'))
h['Review_ABI'].update(source=intake,sources=c['sources'],source_contract=cref)
save('handoff-v1.json',h)
for n in ('ROOT_external_once_v1.py',):
 raw=(P/n).read_bytes();(S/n).write_bytes(raw);assert ref(S/n)['sha256']==ref(P/n)['sha256']
def named(raw):
 lines=raw.splitlines(keepends=True);out={}
 def visit(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    key=prefix+n.name;out[key]=(b''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False));visit(n.body,key+'.')
 visit(ast.parse(raw).body);return out
checks=[]
for child,parent in [('head_gated_receiver_cold_v1.py',P/'receiver_inference_cold_v2.py'),('head_gated_receiver_cases_v1.py',P/'receiver_inference_cases_v1.py'),('ROOT_read_head_gated_receiver_saved_v1.py',P/'ROOT_read_receiver_inference_saved_v2.py')]:
 a=parent.read_bytes();b=(S/child).read_bytes();al=a.splitlines(keepends=True);bl=b.splitlines(keepends=True);edits=[]
 for op,i,j,k,l in difflib.SequenceMatcher(a=al,b=bl,autojunk=False).get_opcodes():
  if op!='equal':edits.append({'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':b''.join(al[i:j]).decode(),'new':b''.join(bl[k:l]).decode()})
 forward=al[:];inverse=bl[:]
 for e in reversed(edits):forward[e['old_start']:e['old_end']]=e['new'].encode().splitlines(keepends=True);inverse[e['new_start']:e['new_end']]=e['old'].encode().splitlines(keepends=True)
 assert b''.join(forward)==b and b''.join(inverse)==a
 for direction,initial,expected in [('forward',a,b),('inverse',b,a)]:
  d=S/'raw-patch-audit-v1'/child/direction;d.mkdir(parents=True);(d/'source.py').write_bytes(initial)
  subprocess.run(['/usr/bin/patch','-F0','-p1','-i',str(S/(child+'.'+direction+'.patch'))],cwd=d,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);assert(d/'source.py').read_bytes()==expected
 na,nb=named(a),named(b);assert set(na)==set(nb)
 checks.append({'source':ref(S/child),'parent':ref(parent),'edits':edits,'raw_regions':len(edits),'whole_forward_inverse_AST':ast.dump(ast.parse(b''.join(forward)),include_attributes=False)==ast.dump(ast.parse(b),include_attributes=False)and ast.dump(ast.parse(b''.join(inverse)),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False),'both_actual_patch_directions_byte_exact':True,'compile_without_evaluation':True,'named_regions_raw_AST_unchanged':[k for k in na if na[k]==nb[k]],'changed_named_regions':[k for k in na if na[k]!=nb[k]]})
save('ROOT-raw-Source-audit-v1.json',{'schema':'ROOT-head-gated-receiver-source-audit-v1','checks':checks,'scientific_calls':0,'project_module_evaluated':False})
print(json.dumps({'handoff':ref(S/'handoff-v1.json'),'regions':[x['raw_regions']for x in checks],'changed_named':[x['changed_named_regions']for x in checks],'scientific_calls':0}))
