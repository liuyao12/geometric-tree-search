"""Source metadata composition only; no project module evaluation or execution."""
import ast,difflib,hashlib,json,subprocess
from pathlib import Path
S=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
P=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017')
D=Path('/private/tmp/gcts-callback-stage-diagnostic-source-20261017')
H=Path('/private/tmp/gcts-callback-stage-helper-source-20261017')
def ref(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(p.read_bytes())
def save(n,v):
    p=S/n;assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');return ref(p)
def replacement(raw,node,value):
    lines=raw.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+value+''.join(lines[node.end_lineno:])
def literal(raw,name,value):
    n=next(n for n in ast.parse(raw).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return replacement(raw,n,name+'='+repr(value)+'\n')
def named(raw):
    lines=raw.splitlines(keepends=True);out={}
    def visit(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                key=prefix+n.name;out[key]=(b''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False));visit(n.body,key+'.')
    visit(ast.parse(raw).body);return out
audits=[]
def source(name,parent,raw):
    p=S/name;assert not p.exists();compile(raw,str(p),'exec',dont_inherit=True);p.write_text(raw)
    a=parent.read_bytes();b=p.read_bytes();al=a.splitlines(keepends=True);bl=b.splitlines(keepends=True)
    edits=[]
    for op,i,j,k,l in difflib.SequenceMatcher(a=al,b=bl,autojunk=False).get_opcodes():
        if op!='equal':edits.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,old=b''.join(al[i:j]).decode(),new=b''.join(bl[k:l]).decode()))
    forward=al[:];inverse=bl[:]
    for e in reversed(edits):
        forward[e['old_start']:e['old_end']]=e['new'].encode().splitlines(keepends=True)
        inverse[e['new_start']:e['new_end']]=e['old'].encode().splitlines(keepends=True)
    assert b''.join(forward)==b and b''.join(inverse)==a
    for direction,initial,expected in [('forward',a,b),('inverse',b,a)]:
        patch=S/(name+'.'+direction+'.patch')
        patch.write_text(''.join(difflib.unified_diff(initial.decode().splitlines(keepends=True),expected.decode().splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py')))
        q=S/'raw-patch-audit-v1'/name/direction;q.mkdir(parents=True);(q/'source.py').write_bytes(initial)
        subprocess.run(['/usr/bin/patch','-F0','-p1','-i',str(patch)],cwd=q,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        assert(q/'source.py').read_bytes()==expected
    na,nb=named(a),named(b)
    audits.append(dict(source=ref(p),parent=ref(parent),edits=edits,raw_regions=len(edits),whole_forward_inverse_AST=True,both_actual_patch_directions_byte_exact=True,compile_without_evaluation=True,named_regions_raw_AST_unchanged=[k for k in na if k in nb and na[k]==nb[k]],changed_named_regions=[k for k in na if k in nb and na[k]!=nb[k]],added_named_regions=sorted(set(nb)-set(na)),removed_named_regions=sorted(set(na)-set(nb))))
    return ref(p)
h=load(P/'handoff-v1.json');c=load(P/'Source-contract-v1.json')
fixed={k:v for k,v in c['sources'].items() if k!='intake'}
fixed['receiver_cases']=load(H/'handoff-v1.json')['source']
raw=(P/'head_gated_receiver_cold_v1.py').read_text()
raw=literal(raw,'VERSION','ROOT-receiver-inference-probe-cold-v4-callback-stages')
raw=literal(raw,'FIXED',fixed)
writer=(D/'save_failure_diagnostic_v2.fragment.py').read_text()
wn=ast.parse(writer).body;assert len(wn)==1 and isinstance(wn[0],ast.FunctionDef) and wn[0].name=='save_failure_diagnostic'
raw=replacement(raw,next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='save_failure_diagnostic'),writer.rstrip()+'\n')
phase_node=next(n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='phase_labels' for t in n.targets))
old_phases=ast.literal_eval(phase_node.value)
new_phases=tuple('P'+str(j)+'_'+s for j in (1,2) for s in ('ENTER','DELEGATE_RETURN','CALLBACK_READY'))+tuple('C'+str(j)+'_'+s for j in (1,2,3) for s in ('ENTER','DELEGATE_RETURN','CALLBACK_READY'))+('SEARCH_RETURN_OBSERVED','POSTSEARCH_SNAPSHOT_READY')
assert len(old_phases)==13 and len(new_phases)==17
raw=replacement(raw,phase_node,'    phase_labels='+repr(old_phases+new_phases)+'\n')
needle="    latest_observations={'proposer':None,'fallback':None,'completion':None,'validator':None}\n"
assert raw.count(needle)==1;raw=raw.replace(needle,needle+(S/'capture_provider_summary.fragment.py').read_text())
needle='            tick=tick,phase=phase)';assert raw.count(needle)==1
raw=raw.replace(needle,'            tick=tick,phase=phase,capture_provider_summary=capture_provider_summary)')
needle="                    f(diagnostic_output_path,diagnostic_context_raw,latest_observations,\n                      'CONTROLS_TIMEOUT_LAST_SCALARS',EARLY_G)";assert raw.count(needle)==1
raw=raw.replace(needle,"                    f(diagnostic_output_path,diagnostic_context_raw,diagnostic_capture,\n                      'CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2',EARLY_G)")
intake=source('callback_stage_receiver_cold_v1.py',P/'head_gated_receiver_cold_v1.py',raw)
c.update(sources={'intake':intake,**fixed},parent_source=ref(P/'head_gated_receiver_cold_v1.py'),successor_scope='Instrumentation-only receiver helper and Root bounded raw provider-return journal under unchanged scientific/native model. Complete new callback phase grammar; no widened work, node, time, memory, result, proof or pruning authority.')
c['phase_sites']=list(old_phases+new_phases)
c['callback_diagnostics']={'helper_handoff':ref(H/'handoff-v1.json'),'diagnostic_handoff':ref(D/'handoff-v3.json'),'erratum':ref(Path('/private/tmp/gcts-head-gated-performance-source-20261017/diagnostic-bound-erratum-v2.json')),'maximum_provider_callbacks_recorded':2,'maximum_consumer_callbacks_recorded':3,'new_stage_sites':list(new_phases),'maximum_phase_lines':30,'provider_summary':'Two nullable fixed-scalar return observations; no valid-offer, current-state, callback-return or proof admission. Original20 ticks only; late writer pure captured builtins/failure55.'}
cref=save('Source-contract-v1.json',c)
reader=(D/'callback_stage_saved_reader_v3.py').read_text()
reader=literal(reader,'CURRENT_CONTRACT',cref)
reader=reader.replace('ROOT-receiver-inference-probe-cold-v3-head-gated','ROOT-receiver-inference-probe-cold-v4-callback-stages')
rref=source('ROOT_read_callback_stage_receiver_saved_v1.py',P/'ROOT_read_head_gated_receiver_saved_v1.py',reader)
rc=load(P/'reader-Source-contract-v1.json');rc.update(source=rref,current_operative_contract=cref,parent_source=ref(P/'ROOT_read_head_gated_receiver_saved_v1.py'))
rcref=save('reader-Source-contract-v1.json',rc)
h.update(source=intake,sources=c['sources'],source_contract=cref,reader=rref,reader_source_contract=rcref,parent_handoff=ref(P/'handoff-v1.json'))
h['Review_ABI'].update(source=intake,sources=c['sources'],source_contract=cref)
save('handoff-v1.json',h)
save('ROOT-raw-Source-audit-v1.json',{'schema':'ROOT-callback-stage-source-audit-v1','checks':audits,'scientific_calls':0,'project_module_evaluated':False})
(S/'ROOT_external_once_v1.py').write_bytes((P/'ROOT_external_once_v1.py').read_bytes())
print(json.dumps({'handoff':ref(S/'handoff-v1.json'),'regions':[x['raw_regions']for x in audits],'scientific_calls':0}))
