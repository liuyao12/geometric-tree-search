"""Compose reviewed instrumentation Sources; never evaluate project modules."""
import ast,difflib,hashlib,json,subprocess
from pathlib import Path
S=Path('/private/tmp/gcts-first-admission-ROOT-source-20261017')
P=Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
D=Path('/private/tmp/gcts-first-admission-diagnostic-source-20261017')
H=Path('/private/tmp/gcts-engine-milestone-helper-source-20261017')
E=Path('/private/tmp/gcts-first-admission-journal-engine-source-20261017')
def ref(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(p.read_bytes())
def save(n,v):
    p=S/n;assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');return ref(p)
def replacement(raw,node,value):
    lines=raw.splitlines(keepends=True);return ''.join(lines[:node.lineno-1])+value+''.join(lines[node.end_lineno:])
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
    a=parent.read_bytes();b=p.read_bytes();al=a.splitlines(keepends=True);bl=b.splitlines(keepends=True);edits=[]
    for op,i,j,k,l in difflib.SequenceMatcher(a=al,b=bl,autojunk=False).get_opcodes():
        if op!='equal':edits.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,old=b''.join(al[i:j]).decode(),new=b''.join(bl[k:l]).decode()))
    forward=al[:];inverse=bl[:]
    for e in reversed(edits):
        forward[e['old_start']:e['old_end']]=e['new'].encode().splitlines(keepends=True)
        inverse[e['new_start']:e['new_end']]=e['old'].encode().splitlines(keepends=True)
    assert b''.join(forward)==b and b''.join(inverse)==a
    for direction,initial,expected in [('forward',a,b),('inverse',b,a)]:
        patch=S/(name+'.'+direction+'.patch');patch.write_text(''.join(difflib.unified_diff(initial.decode().splitlines(keepends=True),expected.decode().splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py')))
        q=S/'raw-patch-audit-v1'/name/direction;q.mkdir(parents=True);(q/'source.py').write_bytes(initial)
        subprocess.run(['/usr/bin/patch','-F0','-p1','-i',str(patch)],cwd=q,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);assert(q/'source.py').read_bytes()==expected
    na,nb=named(a),named(b)
    audits.append(dict(source=ref(p),parent=ref(parent),edits=edits,raw_regions=len(edits),whole_forward_inverse_AST=True,both_actual_patch_directions_byte_exact=True,compile_without_evaluation=True,named_regions_raw_AST_unchanged=[k for k in na if k in nb and na[k]==nb[k]],changed_named_regions=[k for k in na if k in nb and na[k]!=nb[k]],added_named_regions=sorted(set(nb)-set(na)),removed_named_regions=sorted(set(na)-set(nb))))
    return ref(p)
h=load(P/'handoff-v1.json');c=load(P/'Source-contract-v1.json');fixed={k:v for k,v in c['sources'].items()if k!='intake'}
fixed['receiver_cases']=load(H/'handoff-v1.json')['source'];fixed['family_engine']=load(E/'handoff-v8.json')['source']
raw=(P/'callback_stage_receiver_cold_v1.py').read_text();raw=literal(raw,'VERSION','ROOT-receiver-inference-probe-cold-v5-first-admission-journal');raw=literal(raw,'FIXED',fixed)
writer=(D/'save_failure_diagnostic_v3.fragment.py').read_text();wn=ast.parse(writer).body;assert len(wn)==1 and isinstance(wn[0],ast.FunctionDef) and wn[0].name=='save_failure_diagnostic'
raw=replacement(raw,next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)and n.name=='save_failure_diagnostic'),writer.rstrip()+'\n')
phase_node=next(n for n in ast.walk(ast.parse(raw))if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='phase_labels'for t in n.targets));old_phases=ast.literal_eval(phase_node.value)
new_phases=('M1_PLAN_READY','M2_EVENT_READY','M3_PLACE_RETURN','M4_CHILD_DECISION');assert len(old_phases)==30
raw=replacement(raw,phase_node,'    phase_labels='+repr(old_phases+new_phases)+'\n')
needle="    phase('BEFORE_POOL_READ')";assert raw.count(needle)==1
raw=raw.replace(needle,(S/'capture_engine_milestone.fragment.py').read_text()+"    diagnostic_capture['engine_milestones']=engine_milestone_records\n"+needle)
needle='            tick=tick,phase=phase,capture_provider_summary=capture_provider_summary)';assert raw.count(needle)==1
raw=raw.replace(needle,'            tick=tick,phase=phase,capture_provider_summary=capture_provider_summary,\n            engine_milestone_observer=capture_engine_milestone)')
needle="'CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2',EARLY_G)";assert raw.count(needle)==1;raw=raw.replace(needle,"'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3',EARLY_G)")
needle="payload={'schema':'ROOT-receptor-inference-probe-payload-v1','receiver':receiver,";assert raw.count(needle)==1
raw=raw.replace(needle,needle+"\n        'engine_milestones':engine_milestone_records,")
intake=source('first_admission_receiver_cold_v1.py',P/'callback_stage_receiver_cold_v1.py',raw)
c.update(sources={'intake':intake,**fixed},parent_source=ref(P/'callback_stage_receiver_cold_v1.py'),successor_scope='Four bounded first root-family lifecycle diagnostic sites, immutable owned data retention, explicit bounded failure-prefix writer and saved readout. Original mathematical model, all native/checking/scheduler/fallback/rollback and all search/time/work limits unchanged. Raw milestones never qualify a transfer, primitive, trajectory or proof.')
c['phase_sites']=list(old_phases+new_phases)
c['first_admission_diagnostics']={'engine_handoff':ref(E/'handoff-v8.json'),'helper_handoff':ref(H/'handoff-v1.json'),'writer_reader_handoff':ref(D/'handoff-v1.json'),'capture_fragment':ref(S/'capture_engine_milestone.fragment.py'),'maximum_sites':4,'phase_labels':list(new_phases),'maximum_phase_lines':34,'failure_journal_bytes':3145728,'whole_failure_diagnostic_bytes':4325376,'capture':'Read-only engine-owned COW references; no new model/snapshot/check/hash/copy call. Full raw4slots in positive payload, explicit complete-record prefix and captured headers in bounded failure wire. Original native20 capture and failure55 builtin writing remain separate; no raw evidence admission.'}
cref=save('Source-contract-v1.json',c)
reader=(D/'first_admission_saved_reader_v3.py').read_text();reader=literal(reader,'CURRENT_CONTRACT',cref);reader=reader.replace('ROOT-receiver-inference-probe-cold-v4-callback-stages','ROOT-receiver-inference-probe-cold-v5-first-admission-journal')
rref=source('ROOT_read_first_admission_receiver_saved_v1.py',P/'ROOT_read_callback_stage_receiver_saved_v1.py',reader)
rc=load(P/'reader-Source-contract-v1.json');rc.update(source=rref,current_operative_contract=cref,parent_source=ref(P/'ROOT_read_callback_stage_receiver_saved_v1.py'));rcref=save('reader-Source-contract-v1.json',rc)
h.update(source=intake,sources=c['sources'],source_contract=cref,reader=rref,reader_source_contract=rcref,parent_handoff=ref(P/'handoff-v1.json'));h['Review_ABI'].update(source=intake,sources=c['sources'],source_contract=cref)
save('handoff-v1.json',h);save('ROOT-raw-Source-audit-v1.json',{'schema':'ROOT-first-admission-source-audit-v1','checks':audits,'scientific_calls':0,'project_module_evaluated':False})
(S/'ROOT_external_once_v1.py').write_bytes((P/'ROOT_external_once_v1.py').read_bytes())
print(json.dumps({'handoff':ref(S/'handoff-v1.json'),'regions':[x['raw_regions']for x in audits],'scientific_calls':0}))
