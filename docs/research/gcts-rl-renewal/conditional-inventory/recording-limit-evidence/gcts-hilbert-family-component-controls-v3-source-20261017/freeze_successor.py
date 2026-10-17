from pathlib import Path
import ast,json,hashlib,difflib,subprocess
D=Path('/private/tmp/gcts-hilbert-family-component-controls-v3-source-20261017')
P=Path('/private/tmp/gcts-hilbert-family-component-controls-v2-source-20261017')
N=Path('/private/tmp/gcts-hilbert-family-component-controls-peer-20261017')
def ref(p):
 p=Path(p);assert not p.stat().st_flags&0x40000000,str(p)
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 p=D/n
 with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
oldp=P/'hilbert_family_component_controls_cold_v2.py';old=oldp.read_text()
before="""    def call(fn,args=(),kwargs=None):
        return invoke_fn(fn,args,{}if kwargs is None else kwargs,boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
"""
after="""    def call(fn,args=(),kwargs=None):
        actual_kwargs={}if kwargs is None else kwargs
        if type(fn)is types.FunctionType:
            return invoke_fn(fn,args,actual_kwargs,boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        # The original invoke still receives only a Python function. The thunk
        # additionally guards the actual class/method endpoint it delegates to.
        if type(fn)is types.MethodType:
            receiver,actual_function=fn.__self__,fn.__func__
            receiver_type=type(receiver);method_name=actual_function.__name__
            actual_function_state=anchor_fn(actual_function)
            class_snapshot=support.class_state(receiver_type)
            def actual_guard():
                if(type(fn)is not types.MethodType or fn.__self__is not receiver
                    or fn.__func__is not actual_function or type(receiver)is not receiver_type
                    or not same_fn(actual_function,actual_function_state)
                    or support.class_state(receiver_type)!=class_snapshot):
                    raise RuntimeError('actual bound-method code/MRO/receiver changed')
                effective=getattr(receiver,method_name)
                if(type(effective)is not types.MethodType or effective.__self__is not receiver
                    or effective.__func__is not actual_function):
                    raise RuntimeError('actual receiver effective method changed')
        else:
            need(isinstance(fn,type),'only pinned Python function/class/bound-method delegate')
            actual_class,metaclass=fn,type(fn)
            class_snapshot=support.class_state(actual_class)
            metaclass_snapshot=support.class_state(metaclass)
            def actual_guard():
                if(fn is not actual_class or type(fn)is not metaclass
                    or support.class_state(actual_class)!=class_snapshot
                    or support.class_state(metaclass)!=metaclass_snapshot):
                    raise RuntimeError('actual constructor/metaclass/MRO endpoint changed')
        actual_guard_fn=actual_guard;actual_guard_code=actual_guard.__code__
        actual_guard_state=anchor_fn(actual_guard)
        def thunk():
            if(actual_guard is not actual_guard_fn or actual_guard_fn.__code__is not actual_guard_code
                or not same_fn(actual_guard_fn,actual_guard_state)):
                raise RuntimeError('actual delegate validator changed')
            actual_guard_fn()
            try:
                return fn(*args,**actual_kwargs)
            finally:
                if(actual_guard is not actual_guard_fn or actual_guard_fn.__code__is not actual_guard_code
                    or not same_fn(actual_guard_fn,actual_guard_state)):
                    raise RuntimeError('actual delegate validator changed on exceptional return')
                actual_guard_fn()
                if(actual_guard_fn.__code__is not actual_guard_code
                    or not same_fn(actual_guard_fn,actual_guard_state)):
                    raise RuntimeError('actual delegate validator changed after final guard')
        return invoke_fn(thunk,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
"""
# Preserve normal spelling so each executable attribute token is distinct.
for token in ['__self__is','__func__is','__code__is']:
 after=after.replace(token,token[:-2]+' is')
a="""    graph=call(graph_type,kwargs={'header_pin':qualification['catalog']})
    generated.extend((cls,support.class_state(cls))for cls in (graph_type,type(graph.catalog)))
"""
b="""    generated.append((graph_type,support.class_state(graph_type)))
    graph=call(graph_type,kwargs={'header_pin':qualification['catalog']})
    generated.append((type(graph.catalog),support.class_state(type(graph.catalog))))
"""
edits=[("VERSION='ROOT-Hilbert-shared-family-component-controls-cold-v2-child-unknown'","VERSION='ROOT-Hilbert-shared-family-component-controls-cold-v3-callable-boundaries'"),
(before,after),(a,b),("contract['schema']=='ROOT-Hilbert-family-component-controls-Source-contract-v2'","contract['schema']=='ROOT-Hilbert-family-component-controls-Source-contract-v3'")]
s=old
for a,b in edits:assert s.count(a)==1;s=s.replace(a,b)
p=D/'hilbert_family_component_controls_cold_v3.py';p.write_text(s)
ot,nt=ast.parse(old),ast.parse(s);compile(s,str(p),'exec')
inverse=s
for a,b in reversed(edits):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==old and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ot,include_attributes=False)
unchanged=[]
for x in ot.body:
 if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name!='main':
  y=next(y for y in nt.body if isinstance(y,type(x))and y.name==x.name)
  assert ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False)
  assert old.splitlines(keepends=True)[x.lineno-1:x.end_lineno]==s.splitlines(keepends=True)[y.lineno-1:y.end_lineno]
  unchanged.append(x.name)
patches={}
for direction,left,right in [('forward',old,s),('inverse',s,old)]:
 pp=D/('caller-v2-to-v3-'+direction+'.patch');pp.write_text(''.join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile='target.py',tofile='target.py')))
 wd=D/('patch-audit-'+direction);wd.mkdir();(wd/'target.py').write_text(left)
 r=subprocess.run(['patch','--batch','--fuzz=0','-p0','-i',str(pp)],cwd=wd,capture_output=True,text=True)
 assert r.returncode==0 and (wd/'target.py').read_text()==right,(r.stdout,r.stderr)
 patches[direction]=ref(pp)
source=ref(p);parent_contract=json.loads((P/'Source-contract-v2.json').read_text());sources=dict(parent_contract['sources']);sources['intake']=source
functions=[n for n in ast.walk(nt)if isinstance(n,ast.FunctionDef)]
invoke_node=next(n for n in nt.body if isinstance(n,ast.FunctionDef)and n.name=='invoke')
assert ast.dump(invoke_node,include_attributes=False)==ast.dump(next(n for n in ot.body if isinstance(n,ast.FunctionDef)and n.name=='invoke'),include_attributes=False)
# Static API category inventory: no delegate invoked by this audit.
call_sites=[]
main=next(n for n in nt.body if isinstance(n,ast.FunctionDef)and n.name=='main')
for n in ast.walk(main):
 if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='call':call_sites.append({'line':n.lineno,'expression':ast.unparse(n.args[0])})
assert {x['expression']for x in call_sites}>={'context_checker.ClosedInputs','closed.json','graph_type','wire.model_epoch','closed.close'}
dr=put('Source-delta-v3.json',{'schema':'Hilbert-family-component-controls-cold-immediate-delta-v3','source_only':True,'parent_source':ref(oldp),'source':source,'raw_edits':[{'before':a,'after':b}for a,b in edits],'full_raw_AST_inverse':True,'actual_patch_F0_directions':2,'patches':patches,'inherited_top_functions_raw_AST_exact':unchanged,'parent_delta':ref(P/'caller-Source-delta-v2.json'),'frozen_prior_sources_modified':False})
audit=put('static-audit-v3.json',{'schema':'Hilbert-family-component-controls-static-audit-v3','source_only':True,'scientific_calls':0,'module_evaluations':0,'clock_calls':0,'compile_without_evaluation':True,'raw_edits':4,'actual_patch_F0_directions':2,'whole_raw_AST_inverse':True,'top_level_helpers_raw_AST_exact':unchanged,'call_sites':call_sites,'classification':{'functions':'Original invoke(fn,args,kwargs) unchanged.','classes':'Python thunk checks full actual class and metaclass MRO/function/default/closure snapshots pre/post; original invoke anchors thunk and exceptional finally boundary.','bound_methods':'Python thunk checks actual receiver/type, original function strong anchor+MRO snapshot and freshly resolved effective receiver method pre/post, including exceptional return.','other_callables':'Explicitly rejected, no generic callable bypass.'},'generated_guards':'graph_type class added to ordinary guard before construction; immutable catalog class added immediately after successful construction. Constructor thunk guards actual inherited __new__/__init__/metaclass code throughout.','scientific_helper_source_unchanged':True,'same_fixed15_current_sources':True,'same_original_contexts_limits_native_wire':True,'tests_or_functions_executed':0})
api=json.loads((P/'API-wire-v2.json').read_text());api['schema']='Hilbert-family-component-controls-API-v3';api['cold_VERSION']='ROOT-Hilbert-shared-family-component-controls-cold-v3-callable-boundaries';api['correction']='Guarded classes/bound methods now use a Python thunk inside unchanged invoke exceptional/final boundary. Actual class/MRO/metaclass or method/receiver/function/effective lookup snapshots remain exact; plain function path unchanged. No scientific helper/model/caps/wire change.'
ar=put('API-wire-v3.json',api)
c=parent_contract;c.update(schema='ROOT-Hilbert-family-component-controls-Source-contract-v3',source=source,sources=sources,API=ar,delta=dr,static_audit=audit,parent_contract=ref(P/'Source-contract-v2.json'),parent_current_peer=ref(N/'typed-Source-review-v2.json'),correction=api['correction'])
c['Review_ABI']['schema']='ROOT-Hilbert-family-component-controls-cold-typed-Source-review-v3';c['Review_ABI']['source']=source;c['Review_ABI']['sources']=sources
c['prior_attempt_disclosure']='Root reported one V2 native attempt terminal exit2 before any component record due anchor refusing a class. Source author did not inspect actual files or replay it. It conveys no component success/failure or restoration result; V2 bytes and its peer remain preserved. New actual requires separate Root choice/grant.'
cr=put('Source-contract-v3.json',c)
hr=put('handoff-v3.json',{'schema':'Hilbert-family-component-controls-handoff-v3','source_only':True,'scientific_calls':0,'module_evaluations':0,'clock_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'source':source,'sources':sources,'source_contract':cr,'API':ar,'delta':dr,'static_audit':audit,'controls_source':sources['component_controls'],'controls_contract':c['controls_contract'],'parent_current_peer':c['parent_current_peer'],'Review_ABI':c['Review_ABI']})
print(json.dumps({'handoff':hr,'source':source,'contract':cr},indent=2))
