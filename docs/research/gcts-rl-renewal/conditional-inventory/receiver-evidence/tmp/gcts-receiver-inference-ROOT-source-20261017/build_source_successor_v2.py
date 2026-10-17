"""Source metadata only: thin current-pin repair successor; no module evaluation."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

S=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
def ref(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(name):return json.loads((S/name).read_bytes())
def save(name,value):
    p=S/name;assert not p.exists();p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');return ref(p)
def literal(raw,name,value):
    n=next(n for n in ast.parse(raw).body if isinstance(n,ast.Assign)
           and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
    a=raw.splitlines(keepends=True)
    return ''.join(a[:n.lineno-1])+name+'='+repr(value)+'\n'+''.join(a[n.end_lineno:])
def source(child,parent,raw):
    p=S/child;assert not p.exists();compile(raw,str(p),'exec',dont_inherit=True);p.write_text(raw)
    a=(S/parent).read_text()
    for suffix,x,y in [('forward',a,raw),('inverse',raw,a)]:
        (S/(child+'.'+suffix+'.patch')).write_text(''.join(difflib.unified_diff(x.splitlines(keepends=True),y.splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py')))
    return ref(p)
c=load('Source-contract-v1.json');h=load('handoff-v1.json')
fixed={k:v for k,v in c['sources'].items() if k!='intake'}
fixed['receiver_provider']=ref(Path('/private/tmp/gcts-observed-receptor-provider-source-20261017/receptor_transfer_physical_provider_v7.py'))
fixed['family_engine']=ref(Path('/private/tmp/gcts-family-census-engine-source-20261017/receptor_family_search_engine_v6.py'))
raw=(S/'receiver_inference_cold_v1.py').read_text()
raw=literal(raw,'VERSION','ROOT-receiver-inference-probe-cold-v2')
raw=literal(raw,'FIXED',fixed)
raw=raw.replace('One separately granted native conditional component/inventory experiment.\nFull original model; automatic native prefixes; no engine, branch or proof route.',
                'One separately granted real receiver-search probe with a reused inventory.\nFull original model; actual global decisions; no supplied proof or receiver route.')
raw=raw.replace('exact current executable Source17 and saved input8','exact current executable Sources and saved inputs')
intake=source('receiver_inference_cold_v2.py','receiver_inference_cold_v1.py',raw)
c['sources']={'intake':intake,**fixed}
c['parent_source']=ref(S/'receiver_inference_cold_v1.py')
c['successor_scope']='Only current provider7 and engine6 pins/own response VERSION; inherited purpose/limits/native machinery/helper remain. Header and one diagnostic wording corrected to describe actual engine use/current data maps. No scientific actual used predecessor.'
cref=save('Source-contract-v2.json',c)
reader=(S/'ROOT_read_receiver_inference_saved_v1.py').read_text()
reader=literal(reader,'CURRENT_CONTRACT',cref)
reader=reader.replace('ROOT-receiver-inference-probe-cold-v1','ROOT-receiver-inference-probe-cold-v2')
rref=source('ROOT_read_receiver_inference_saved_v2.py','ROOT_read_receiver_inference_saved_v1.py',reader)
rc=load('reader-Source-contract-v1.json');rc['source']=rref;rc['current_operative_contract']=cref
rc['parent_source']=ref(S/'ROOT_read_receiver_inference_saved_v1.py')
rcref=save('reader-Source-contract-v2.json',rc)
h.update(source=intake,sources=c['sources'],source_contract=cref,reader=rref,reader_source_contract=rcref)
h['Review_ABI'].update(source=intake,sources=c['sources'],source_contract=cref)
h['parent_handoff']=ref(S/'handoff-v1.json')
save('handoff-v2.json',h)
print(json.dumps({'source':intake,'contract':cref,'reader':rref,'scientific_calls':0}))
