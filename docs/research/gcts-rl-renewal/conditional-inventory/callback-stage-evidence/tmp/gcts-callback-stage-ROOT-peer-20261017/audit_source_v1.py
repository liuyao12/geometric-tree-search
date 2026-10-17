"""Reviewer raw/AST/patch audit only. Never loads or calls reviewed modules."""
import ast
import hashlib
import json
import pathlib
import subprocess

HERE = pathlib.Path('/private/tmp/gcts-callback-stage-ROOT-peer-20261017')
AUTHOR = pathlib.Path('/private/tmp/gcts-callback-stage-ROOT-source-20261017')
checks = []
refs = []

def check(name, value, **details):
    if not value:
        raise AssertionError(name)
    checks.append(dict(check=name, passed=True, **details))

def ref(path):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    value = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    refs.append(value)
    return value, raw

def load(path):
    value, raw = ref(path)
    return value, json.loads(raw)

def ast_text(raw):
    return ast.dump(ast.parse(raw), include_attributes=False)

def regions(raw):
    lines = raw.decode().splitlines(keepends=True)
    result = {}
    def walk(node, prefix=''):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                result[name] = (''.join(lines[child.lineno-1:child.end_lineno]), ast.dump(child, include_attributes=False))
                walk(child, name+'.')
            else:
                walk(child, prefix)
    walk(ast.parse(raw))
    return result

def literal_assignments(raw):
    return {n.targets[0].id: ast.literal_eval(n.value)
            for n in ast.parse(raw).body if isinstance(n, ast.Assign)
            and len(n.targets)==1 and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in {'FIXED','FIXED_INPUTS','LIMITS','ORIGINAL_SOURCES','ORIGINAL_INPUTS','ORIGINAL_BINDING','VERSION','SCOPE'}}

h_ref, h = load(AUTHOR/'handoff-v1.json')
check('current handoff exact requested pin', h_ref['sha256']=='a0f81b29c2963b7ed75a6f19be4ffe4468973c984ba3d12d41e793909d4abcc5' and h_ref['bytes']==14681)
source_ref, raw = ref(h['source']['path'])
contract_ref, contract = load(h['source_contract']['path'])
check('current source and contract full bytes', source_ref==h['source'] and contract_ref==h['source_contract'])
check('current exact review ABI', h['Review_ABI']['source']==source_ref and h['Review_ABI']['source_contract']==contract_ref and h['Review_ABI']['sources']==h['sources'])
parent_ref, parent = ref(contract['parent_source']['path'])
check('parent exact source pin', parent_ref==contract['parent_source'])
audit_ref, author_audit = load(AUTHOR/'ROOT-raw-Source-audit-v1.json')
item = author_audit['checks'][0]
check('caller audit identity and eight complete raw regions', item['source']==source_ref and item['parent']==parent_ref and len(item['edits'])==8)
old_lines = parent.decode().splitlines(keepends=True)
new_lines = raw.decode().splitlines(keepends=True)
for i,e in enumerate(item['edits']):
    check('raw old/new region '+str(i+1), ''.join(old_lines[e['old_start']:e['old_end']])==e['old'] and ''.join(new_lines[e['new_start']:e['new_end']])==e['new'])
forward=old_lines[:]
for e in reversed(item['edits']):
    forward[e['old_start']:e['old_end']]=e['new'].splitlines(keepends=True)
inverse=new_lines[:]
for e in reversed(item['edits']):
    inverse[e['new_start']:e['new_end']]=e['old'].splitlines(keepends=True)
check('independent whole raw forward and inverse', ''.join(forward).encode()==raw and ''.join(inverse).encode()==parent)
check('independent whole AST forward and inverse', ast_text(''.join(forward))==ast_text(raw) and ast_text(''.join(inverse))==ast_text(parent))
patches=[]
for direction,initial,expected in [('forward',parent,raw),('inverse',raw,parent)]:
    patch_ref,patchraw=ref(AUTHOR/('callback_stage_receiver_cold_v1.py.'+direction+'.patch'))
    copy_path=HERE/('caller-'+direction+'-patch-copy.py')
    copy_path.write_bytes(initial)
    result=subprocess.run(['patch','-s','-F0',str(copy_path),patch_ref['path']],capture_output=True)
    check('actual '+direction+' patch application and exact cmp',result.returncode==0 and copy_path.read_bytes()==expected,
          returncode=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode())
    patches.append(patch_ref)
check('current caller compiles without evaluation', isinstance(compile(raw,source_ref['path'],'exec'),type(compile('','<empty>','exec'))))
old_regions,new_regions=regions(parent),regions(raw)
unchanged=[k for k in old_regions if k in new_regions and old_regions[k]==new_regions[k]]
changed=[k for k in old_regions if k in new_regions and old_regions[k]!=new_regions[k]]
added=sorted(set(new_regions)-set(old_regions))
check('all unchanged named regions independently exact',len(unchanged)==34 and changed==['save_failure_diagnostic','main','main.run_receiver'] and added==['main.capture_provider_summary'],unchanged=unchanged,changed=changed,added=added)
writer_ref, writer = ref('/private/tmp/gcts-callback-stage-diagnostic-source-20261017/save_failure_diagnostic_v2.fragment.py')
check('reviewed writer embedded raw exact',writer in raw and new_regions['save_failure_diagnostic'][0].rstrip('\n') == writer.decode().rstrip('\n'))
capture_ref,capture = ref(AUTHOR/'capture_provider_summary.fragment.py')
check('reviewed capture fragment inserted raw exact',capture.decode() in raw.decode() and capture_ref['bytes']==2841)
oldlit,newlit=literal_assignments(parent),literal_assignments(raw)
for name in ('FIXED_INPUTS','LIMITS','ORIGINAL_SOURCES','ORIGINAL_INPUTS','ORIGINAL_BINDING','SCOPE'):
    check('unchanged literal '+name,oldlit[name]==newlit[name])
check('only current helper changes in executable dependency map',set(newlit['FIXED'])==set(oldlit['FIXED']) and [k for k in oldlit['FIXED'] if oldlit['FIXED'][k]!=newlit['FIXED'][k]]==['receiver_cases'])
check('source22 versus original17 and input10/input2 contract joins',len(h['sources'])==22 and len(contract['original_model_sources'])==17 and len(contract['inputs'])==10 and len(contract['original_model_inputs'])==2 and contract['sources']==h['sources'] and newlit['FIXED']=={k:v for k,v in h['sources'].items() if k!='intake'} and contract['inputs']==newlit['FIXED_INPUTS'] and contract['limits']==newlit['LIMITS'] and contract['original_model_sources']==newlit['ORIGINAL_SOURCES'] and contract['original_model_inputs']==newlit['ORIGINAL_INPUTS'] and contract['original_model_binding']==newlit['ORIGINAL_BINDING'])
helper_ref,helper=ref(h['sources']['receiver_cases']['path'])
check('exact current reviewed helper pin',helper_ref==h['sources']['receiver_cases'] and helper_ref['sha256']=='150e5eb32dd4bbfbb44e19554072d2fdc0412f9f1faba228bac8e414a868b094')
helper_peer_ref,helper_peer=load('/private/tmp/gcts-callback-stage-helper-peer-20261017/typed-Source-review-v1.json')
seam_peer_ref,seam_peer=load('/private/tmp/gcts-callback-stage-diagnostic-peer-20261017/typed-Source-review-v3.json')
negative_ref,negative=load('/private/tmp/gcts-callback-stage-diagnostic-peer-20261017/typed-Source-review-v2.json')
check('prior independent helper/seam reviews and preserved negative',helper_peer['scientific_calls']==0 and seam_peer['scientific_calls']==0 and negative['scientific_calls']==0)
main_node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='main')
labels=next(ast.literal_eval(n.value) for n in main_node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='phase_labels' for t in n.targets))
check('integrated exact phase whitelist and finite wire bound',list(labels)==contract['phase_sites'] and len(set(labels))==30 and max(len(('COMPONENT_INVENTORY_PHASE '+s+' '+str(2**63-1)+'\n').encode()) for s in labels)==75 and sum(len(('COMPONENT_INVENTORY_PHASE '+s+' '+str(2**63-1)+'\n').encode()) for s in labels)==1913)
check('unchanged final transport/native error tail raw',raw[raw.index(b"    need(receiver['schema']"):].replace(b"'version':VERSION",b"'version':VERSION")==parent[parent.index(b"    need(receiver['schema']"):])
evidence=dict(schema='callback-stage-integrated-caller-independent-source-audit-v1',source_only=True,scientific_calls=0,scientific_acceptance=False,checks=checks,raw_references=refs,notes=['No author builder, model, checker, helper or reviewed module imported or evaluated.','No actual/result/plan/grant contents or scientific inputs read. All work limited to listed Sources/contracts/prior Source reviews and real patch applications on reviewer-owned Source copies.'])
(HERE/'static-review-v1.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(checks=len(checks),unchanged=len(unchanged),source=source_ref,contract=contract_ref,helper_peer=helper_peer_ref,seam_peer=seam_peer_ref,negative=negative_ref,patches=patches)))
