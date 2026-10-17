"""Independent raw/AST/compile/patch review only; no reviewed function executes."""
import ast
import json
import hashlib
import subprocess
from pathlib import Path
P=Path('/private/tmp/gcts-first-admission-diagnostic-peer-20261017')
A=Path('/private/tmp/gcts-first-admission-diagnostic-source-20261017')
refs=[];checks=[]
def ref(path):
    path=Path(path);raw=path.read_bytes();r=dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));refs.append(r);return r,raw
def load(path):
    r,b=ref(path);return r,json.loads(b)
def check(name,ok,**details):
    assert ok,name;checks.append(dict(check=name,passed=True,**details))
def save(name,value):
    path=P/name;assert not path.exists();path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');return ref(path)[0]
def regions(raw):
    lines=raw.decode().splitlines(keepends=True);out={}
    def walk(n,prefix=''):
        for child in ast.iter_child_nodes(n):
            if isinstance(child,ast.FunctionDef):
                k=prefix+child.name;out[k]=(''.join(lines[child.lineno-1:child.end_lineno]),ast.dump(child,include_attributes=False));walk(child,k+'.')
            else:walk(child,prefix)
    walk(ast.parse(raw));return out
def literal(n):
    if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Mult)):
        left,right=literal(n.left),literal(n.right)
        return left+right if isinstance(n.op,ast.Add) else left*right
    return ast.literal_eval(n)
hr,h=load(A/'handoff-v1.json');cr,c=load(h['source_contract']['path']);ar,api=load(h['API']['path']);dr,d=load(h['delta']['path'])
check('exact immutable metadata pins',hr['sha256']=='e3d84b8b7cc3ea1cbda520059fd7c3670e97a9d080cda5f2c347b326af7c1c28' and cr==h['source_contract'] and ar==h['API'] and dr==h['delta'])
raws={};retained={}
for role,r in d['roles'].items():
    sr,s=ref(r['source']['path']);pr,p=ref(r['parent']['path']);raws[role]=s
    check(role+' source/parent exact',sr==r['source']==h['sources'][role] and pr==r['parent'])
    before,after=p.decode(),s.decode();forward,inverse=before,after
    check(role+' raw edit count',len(r['edits'])==(2 if role=='writer_replacement' else 20))
    for i,e in enumerate(r['edits']):check(role+' region '+str(i+1),before[e['old_start']:e['old_end']]==e['before'] and after[e['new_start']:e['new_end']]==e['after'])
    for e in reversed(r['edits']):
        forward=forward[:e['old_start']]+e['after']+forward[e['old_end']:]
        inverse=inverse[:e['new_start']]+e['before']+inverse[e['new_end']:]
    check(role+' full raw inverse',forward.encode()==s and inverse.encode()==p)
    check(role+' full AST inverse',ast.dump(ast.parse(forward),include_attributes=False)==ast.dump(ast.parse(s),include_attributes=False) and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(p),include_attributes=False))
    for way,start,expected in [('forward',p,s),('inverse',s,p)]:
        patch,b=ref(r[way+'_patch']['path']);check(role+' '+way+' patch pin',patch==r[way+'_patch'])
        target=P/(role+'-'+way+'-copy.py');target.write_bytes(start)
        done=subprocess.run(['patch','-s','-F0',str(target),patch['path']],capture_output=True)
        check(role+' actual '+way+' patch and cmp',done.returncode==0 and target.read_bytes()==expected)
    oldr,newr=regions(p),regions(s);exact=[k for k in oldr if oldr[k]==newr.get(k)];retained[role]=exact
    check(role+' unchanged regions raw+AST',exact==r['raw_AST_exact_regions'],regions=exact)
    compile(s,sr['path'],'exec');check(role+' compile without evaluation',True)
reader=ast.parse(raws['saved_reader_candidate']);writer=ast.parse(raws['writer_replacement'])
names={'LEGACY_PHASES','CALLBACK_PHASES','SEARCH_PHASES','MILESTONE_PHASES','MILESTONE_STAGES','MILESTONE_FIELDS','MILESTONE_ENGINE_VERSION','MILESTONE_JOURNAL_MAX_BYTES','DIAGNOSTIC_MAX_BYTES','PHASE_LINE_MAX_BYTES','PHASE_TOTAL_MAX_BYTES'}
const={n.targets[0].id:literal(n.value) for n in reader.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names}
labels=sum((tuple(const[k])for k in ('LEGACY_PHASES','CALLBACK_PHASES','SEARCH_PHASES','MILESTONE_PHASES')),())
wire=[('COMPONENT_INVENTORY_PHASE '+s+' '+str(2**63-1)+'\n').encode()for s in labels]
check('exact34 distinct phases75/2160 bytes',len(labels)==len(set(labels))==34 and max(map(len,wire))==const['PHASE_LINE_MAX_BYTES']==75 and sum(map(len,wire))==const['PHASE_TOTAL_MAX_BYTES']==2160)
check('3MiB journal old whole diagnostic and fixed-null21 bytes',const['MILESTONE_JOURNAL_MAX_BYTES']==3145728 and const['DIAGNOSTIC_MAX_BYTES']==4325376 and len(b'[null,null,null,null]')==21)
er,ea=load(c['engine_API']['path']);check('final engine fields/version/stages',tuple(ea['stages'])==const['MILESTONE_STAGES'] and ea['VERSION']==const['MILESTONE_ENGINE_VERSION'] and all(tuple(ea['stage_fields'][stage])==const['MILESTONE_FIELDS'][i]for i,stage in enumerate(ea['stages'])))
capr,cap=ref(c['capture_source']['path']);check('capture fragment exact',capr==c['capture_source'])
epr,ep=load('/private/tmp/gcts-first-admission-journal-engine-peer-20261017/typed-Source-review-v8.json');check('separate distinct engine peer',ep['source_review_passed'] is True and ep['author_identity']=='/root/hilbert_ordering_diagnosis' and ep['reviewer_identity']!='/root/hilbert_ordering_diagnosis')
branch=next(n for n in ast.walk(writer)if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(x,ast.Constant) and x.value=='CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3'for x in ast.walk(n.test)))
newnodes=ast.Module(body=branch.body,type_ignores=[])
handlers=[n for n in ast.walk(newnodes)if isinstance(n,ast.ExceptHandler)]
check('new omission catches only encoder ValueError',len(handlers)==1 and isinstance(handlers[0].type,ast.Name) and handlers[0].type.id=='ValueError')
check('no original20/scientific delegate in late branch',not any(isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id in {'tick','phase','call','invoke','guard','boundary','project_local_float_deadline'})or(isinstance(n.func,ast.Attribute) and n.func.attr in {'private_state','rebuild_tile','check_marking','check_marked_state','consume_preferences','decision','search','state_snapshot'}))for n in ast.walk(newnodes)))
static=save('static-review-v1.json',dict(schema='first-admission-diagnostic-independent-static-v1',source_only=True,scientific_calls=0,scientific_acceptance=False,checks=checks,raw_references=refs,retained_regions=retained,source_evaluated=False))
overlap='Reviewer authored engine8, older engine/census/point/checker ancestry and diagnostic proposals; not author of Controls current writer/readout or Arithmetic helper. Shared API coordination and prior seam review disclosed. Engine mathematics is not independently self-reviewed: separate cd56b601 peer is bound.'
findings=[
    {'id':'RAW-NATIVE','verdict':'PASS','detail':'Whole writer23268/reader42910/API/contract/parents read.2+20 full raw/AST inverses and four real -F0 patches exact; writer5 nested and reader9 regions exact. Captured native55/builtin-only serialization and native/resource error propagation preserved; new omission catches ValueError only. No late original20/project/scientific call.'},
    {'id':'FULL-RECORD-PREFIX','verdict':'PASS','detail':'Fixed4 captured-header prefix checked before serialization.21 initial bytes include brackets/nulls/commas; replace-null adjustment is record bytes minus4; aggregate3MiB includes whole list. Only complete wrappers enter output; first omission stops suffix. Captured/serialized/omitted counts/headers/next ordinal/reason distinguish absent from omitted. Reader reproduces insertion-order ensure_ascii=True/no-space JSON byte count. Old whole4MiB+131072 bound and exact two-file completion hashes persist.'},
    {'id':'34-PHASE-PROTOCOL','verdict':'PASS','detail':'34 unique labels/75-byte line/2160-byte all-site bound recomputed. Canonical signed64/native monotone times, legacy relative order, sequential P/C groups and per-role ordinals preserved. M1-M4 form prefix outside callback group; M4 precedes P2/C2/C3. Own marker may lack capture; later marker requires prior header. Captures join current marker/next marker/search return; partial final line never counts completed.'},
    {'id':'NO-OFFER-TRACE','verdict':'PASS_IN_CURRENT_PINNED_SCOPE','detail':'C1_READY before M1 holds even no offer: engine ctor preferences=None; first root selection unconditionally invokes fresh BATCH _consume_family consumer. UNKNOWN-empty returns UNKNOWN; READY-empty returns NO_MATCH. Helper emits C1_READY before returning either receipt. Failure prevents M1. This derives from Source, not prior READY1 observation; canonical fallback still has no family admission authority.'},
    {'id':'RAW-ONLY-RECONCILIATION','verdict':'PASS','detail':'Positive full4slot joins stage/version/depth/fields/native stamps with existing strict full native20/512/wire/envelope/current/original authority checks. Failure joins exact captured-vs-serialized prefix and native55 context/terminal/source metadata. Full state/plan/event-shaped values remain opaque builtin JSON; no semantic admission, move/current frame/restoration/theorem/runtime gain from journal or marker.'},
    {'id':'ROOT-ASSEMBLY','verdict':'CONDITIONAL','detail':'Candidate retains parent b444 CURRENT_CONTRACT and v4 response version for Root rebind; not final runnable Root authority. Whole current22/input10 versus original17/input2, cf4 writer insertion, helper1685/engine9fd/capture410a, native/CodeSeal/once/guard/writer anchors,34 whitelist and positive full4slot payload require separate Root composition peer. No actual/result/proofword/scientific input or reviewed function/clock read/evaluated.'},
]
fr=save('findings-v1.json',dict(schema='first-admission-diagnostic-independent-findings-v1',source_contract=cr,findings=findings,blockers=[],author_overlap=overlap,static_evidence=static,distinct_engine_peer=epr,source_only=True,scientific_calls=0,scientific_acceptance=False))
review=dict(h['Review_ABI']);review.update(author_identity='/root/hilbert_advice_controls',reviewer_identity='/root/hilbert_ordering_diagnosis',source_contract=cr,source_review_passed=True,Source_pass=True,verdict='CONDITIONAL_SOURCE_PASS',blockers=[],author_overlap=overlap,findings=fr,static_evidence=static,source_only=True,scientific_calls=0,scientific_acceptance=False,actual_execution_authorized=False,runtime_qualified=False)
rr=save('typed-Source-review-v1.json',review)
ho=save('handoff-v1.json',dict(schema='first-admission-diagnostic-independent-review-handoff-v1',review=rr,findings=fr,static_evidence=static,source_only=True,scientific_calls=0,scientific_acceptance=False,actual_execution_authorized=False))
print(json.dumps(dict(review=rr,findings=fr,handoff=ho,static=static,checks=len(checks)),indent=2))
