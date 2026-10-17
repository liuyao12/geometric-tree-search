"""Compile/AST/raw inverse audit only, without scientific module evaluation."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

S=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
P=Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-source-20261017')


def ref(p):
    b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))


def named(raw):
    t=ast.parse(raw);lines=raw.splitlines(keepends=True);out={}
    def visit(nodes,prefix=''):
        for n in nodes:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                key=prefix+n.name
                out[key]=(b''.join(lines[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False))
                visit(n.body,key+'.')
    visit(t.body)
    return out


checks=[]
for child,parent in (('receiver_inference_cold_v1.py','native_productive_inventory_cold_v2.py'),
                     ('ROOT_read_receiver_inference_saved_v1.py','ROOT_read_native_productive_inventory_saved_v2.py')):
    a=(P/parent).read_bytes();b=(S/child).read_bytes();al=a.splitlines(keepends=True);bl=b.splitlines(keepends=True)
    edits=[]
    for op,i,j,k,l in difflib.SequenceMatcher(a=al,b=bl,autojunk=False).get_opcodes():
        if op!='equal':edits.append({'old_start':i,'old_end':j,'new_start':k,'new_end':l,
                                    'old':b''.join(al[i:j]).decode(),'new':b''.join(bl[k:l]).decode()})
    replay=al[:]
    for e in reversed(edits):replay[e['old_start']:e['old_end']]=e['new'].encode().splitlines(keepends=True)
    assert b''.join(replay)==b
    inverse=bl[:]
    for e in reversed(edits):inverse[e['new_start']:e['new_end']]=e['old'].encode().splitlines(keepends=True)
    assert b''.join(inverse)==a
    assert ast.dump(ast.parse(b''.join(replay)),include_attributes=False)==ast.dump(ast.parse(b),include_attributes=False)
    assert ast.dump(ast.parse(b''.join(inverse)),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
    na,nb=named(a),named(b)
    same=[k for k in na if k in nb and na[k]==nb[k]]
    changed=[k for k in na if k in nb and na[k]!=nb[k]]
    for direction,initial,expected,patch in (('forward',a,b,S/(child+'.forward.patch')),
                                              ('inverse',b,a,S/(child+'.inverse.patch'))):
        dest=S/'raw-patch-audit'/child/direction
        assert not dest.exists();dest.mkdir(parents=True)
        (dest/'source.py').write_bytes(initial)
        r=subprocess.run(['/usr/bin/patch','-F0','-p1','-i',str(patch)],cwd=dest,
                         stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        assert (dest/'source.py').read_bytes()==expected
    compile(b,child,'exec',dont_inherit=True)
    checks.append({'source':ref(S/child),'parent':ref(P/parent),'edits':edits,
        'raw_regions':len(edits),'whole_forward_inverse_AST':True,
        'both_actual_patch_directions_byte_exact':True,'compile_without_evaluation':True,
        'named_regions_raw_AST_unchanged':same,'changed_named_regions':changed,
        'added_named_regions':sorted(set(nb)-set(na)),'removed_named_regions':sorted(set(na)-set(nb))})
helper=S/'receiver_inference_cases_v1.py'
compile(helper.read_bytes(),str(helper),'exec',dont_inherit=True)
out={'schema':'ROOT-receiver-inference-raw-Source-audit-v1','checks':checks,
    'new_case_source':ref(helper),'case_compiles_without_evaluation':True,
    'case_scope':'New generic real receiver probe; no supplied intermediate or proof route. Full native model and fallback retained.',
    'scientific_calls':0,'project_module_evaluated':False}
p=S/'ROOT-raw-Source-audit-v1.json';assert not p.exists();p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'audit':ref(p),'regions':[x['raw_regions'] for x in checks],
                 'unchanged_named_counts':[len(x['named_regions_raw_AST_unchanged']) for x in checks],
                 'changed_named':[x['changed_named_regions'] for x in checks],'scientific_calls':0}))
