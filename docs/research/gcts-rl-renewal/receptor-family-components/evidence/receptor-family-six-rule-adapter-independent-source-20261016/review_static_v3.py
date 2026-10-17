"""Independent static metadata only: no Source import or helper execution."""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path.cwd();A=ROOT/'.gcts-active/receptor-family-six-rule-adapter-source-20261016';D=ROOT/'.gcts-active/receptor-family-six-rule-adapter-independent-source-20261016'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def apply_edits(a,b,d):
 parts=[];pos=0
 for e in d['edits']:
  x,y=e['old_start'],e['old_end'];assert x>=pos and a[x:y]==e['old_utf8'].encode();parts.extend((a[pos:x],e['new_utf8'].encode()));pos=y
 parts.append(a[pos:]);assert b''.join(parts)==b
 parts=[];pos=0
 for e in d['edits']:
  x,y=e['new_start'],e['new_end'];assert x>=pos and b[x:y]==e['new_utf8'].encode();parts.extend((b[pos:x],e['old_utf8'].encode()));pos=y
 parts.append(b[pos:]);assert b''.join(parts)==a
 assert ast.dump(ast.parse(b''.join(parts)),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
def patch(a,p):
 lines=a.decode().splitlines(True);diff=p.read_text().splitlines(True);assert diff[0].startswith('--- ') and diff[1].startswith('+++ ')
 out=[];cursor=0;i=2
 while i<len(diff):
  m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',diff[i]);assert m
  oldstart=int(m[1])-1;oldcount=int(m[2] or '1');newcount=int(m[4] or '1')
  if oldcount==0:oldstart+=1
  assert oldstart>=cursor;out.extend(lines[cursor:oldstart]);cursor=oldstart;i+=1;used=made=0
  while i<len(diff) and not diff[i].startswith('@@'):
   line=diff[i];assert line[:1] in (' ','+','-')
   if line[:1] in (' ','-'):assert cursor<len(lines) and lines[cursor]==line[1:];cursor+=1;used+=1
   if line[:1] in (' ','+'):out.append(line[1:]);made+=1
   i+=1
  assert used==oldcount and made==newcount
 out.extend(lines[cursor:]);return ''.join(out).encode()
files=[A/f'receptor_family_six_rule_adapter_v{i}.py' for i in (1,2,3)]
raws=[p.read_bytes() for p in files];trees=[ast.parse(b) for b in raws]
assert pin(files[2])['sha256']=='4bd6c6fe723b17da0afec54fb0409f33dcb01e699e774f673e8de12c33efeba9'
compile(raws[2],str(files[2]),'exec')
refs=[pin(p) for p in files]
for i in (2,3):
 d=json.loads((A/f'Source-delta-v{i}.json').read_bytes());apply_edits(raws[i-2],raws[i-1],d)
 assert d['source']==pin(files[i-1]) and d['parent']==pin(files[i-2])
 for p in d['patches']:
  pp=Path(p['path']);assert pin(pp)==p
 assert patch(raws[i-2],Path(d['patches'][0]['path']))==raws[i-1]
 assert patch(raws[i-1],Path(d['patches'][1]['path']))==raws[i-2]
 refs.extend([pin(A/f'Source-delta-v{i}.json')]+d['patches'])
functions=[]
for tr,raw in zip(trees,raws):
 lines=raw.decode().splitlines(True)
 functions.append({n.name:{'raw':''.join(lines[n.lineno-1:n.end_lineno]),'ast':ast.dump(n,include_attributes=False),'line':n.lineno,'end_line':n.end_lineno} for n in tr.body if isinstance(n,ast.FunctionDef)})
unchanged=[]
for k,v in functions[0].items():
 if k!='adapt_expansion':
  assert all(f[k]['raw']==v['raw'] and f[k]['ast']==v['ast'] for f in functions[1:]);unchanged.append(k)
assert len(unchanged)==7
assert [n.names[0].name for n in trees[2].body if isinstance(n,ast.Import)]==['hashlib','json']
assert not any(isinstance(n,ast.ImportFrom) for n in ast.walk(trees[2]))
assert not any(isinstance(n,ast.ExceptHandler) for n in ast.walk(trees[2]))
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('exec','eval','__import__','open') for n in ast.walk(trees[2]))
result={'schema':'receptor-family-six-rule-adapter-independent-static-v3','source':pin(files[2]),'raw_refs':refs,'raw_both_delta_inverses':True,'actual_all_four_patch_directions_exact':True,'whole_AST_both_inverses':True,'seven_helpers_raw_AST_exact':unchanged,'changed_function':{'name':'adapt_expansion','line':functions[2]['adapt_expansion']['line'],'end_line':functions[2]['adapt_expansion']['end_line']},'imports':['hashlib','json'],'no_exception_handlers':True,'AST_parse_compile_without_evaluation':True,'module_or_helper_execution':False,'scientific_calls':0,'runtime_qualified':False}
p=D/'independent-static-v3.json';p.open('xb').write((json.dumps(result,indent=2,sort_keys=True)+'\n').encode());print(json.dumps(pin(p)))
