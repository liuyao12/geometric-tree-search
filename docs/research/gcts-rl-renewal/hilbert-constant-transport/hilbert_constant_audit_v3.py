"""Independent tuple-AST finite transport audit. No producer/checker imports.

Reconstruct the whole domain/DAG from the exact prior native request, perform
separate six-rule derivation checks and independently regenerate corruptions.
Native computations and the general correspondence theorem are not checked.
"""
import copy,gzip,hashlib,itertools,json,resource,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
class Bad(ValueError):pass
class ResourceUnknown(Exception):pass
def require(p,s):
    if not p:raise Bad(s)
def encoding(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode()
def fingerprint(x):return hashlib.sha256(encoding(x)).hexdigest()
def immutable(x):
    if type(x) is list:return tuple(immutable(y) for y in x)
    if type(x) is dict:return {k:immutable(y) for k,y in x.items()}
    return x
def memory():return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def checkpoint():
    if memory()>512*1024*1024:raise ResourceUnknown('512 MiB peak RSS ceiling')
def file_hash(p):checkpoint();b=p.read_bytes();checkpoint();return hashlib.sha256(b).hexdigest()
def read(p,strict=False):
    b=p.read_bytes();checkpoint();b=gzip.decompress(b) if p.suffix=='.gz' else b
    if strict:
        def names(xs):
            out={}
            for k,v in xs:
                require(k not in out,'duplicate raw key');out[k]=v
            return out
        def exact(_):raise Bad('inexact number')
        return json.loads(b,object_pairs_hook=names,parse_float=exact,parse_constant=exact)
    return json.loads(b)
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n');checkpoint()
def shape(x,ks):require(type(x) is dict and set(x)==set(ks),'exact record fields')
def integer(n):require(type(n) is int and n>=0,'nonnegative integer');return n

def wf_term(t,signature):
    require(type(t) is tuple and bool(t),'tuple term')
    if t[0]=='var':require(len(t)==2 and type(t[1]) is str,'var shape')
    else:require(t[0]=='fun' and len(t)==3 and type(t[1]) is str and t[2]==() and signature['functions'].get(t[1])==0,'declared nullary symbol')
def wf_formula(f,signature):
    require(type(f) is tuple and bool(f),'tuple formula');tag=f[0]
    if tag=='all':require(len(f)==3 and type(f[1]) is str,'quantifier');wf_formula(f[2],signature)
    elif tag in ['and','or','imp']:
        require(len(f)==3,'connective');wf_formula(f[1],signature);wf_formula(f[2],signature)
    elif tag=='not':require(len(f)==2,'not shape');wf_formula(f[1],signature)
    elif tag=='eq':require(len(f)==3,'eq shape');wf_term(f[1],signature);wf_term(f[2],signature)
    elif tag=='pred':
        require(len(f)==3 and type(f[1]) is str and type(f[2]) is tuple and signature['predicates'].get(f[1])==len(f[2]),'predicate signature')
        for t in f[2]:wf_term(t,signature)
    else:require(f==('bot',),'bottom')
def fv(f):
    tag=f[0]
    if tag=='all':return fv(f[2])-{f[1]}
    if tag in ['pred','eq']:
        terms=f[2] if tag=='pred' else f[1:];return {t[1] for t in terms if t[0]=='var'}
    if tag=='bot':return set()
    result=set()
    for part in f[1:]:result.update(fv(part))
    return result
def plug(f,v,t):
    require(type(t) is tuple and len(t)==3 and t[0]=='fun' and t[2]==(),'closed plug operand')
    def replace(a):return t if a==('var',v) else a
    k=f[0]
    if k=='pred':return (k,f[1],tuple(replace(a) for a in f[2]))
    if k=='eq':return (k,replace(f[1]),replace(f[2]))
    if k=='all':return f if f[1]==v else (k,f[1],plug(f[2],v,t))
    if k=='bot':return f
    return (k,*(plug(a,v,t) for a in f[1:]))
def validate_derivation(definition,signature,theorems,registry):
    d=immutable(definition);shape(d,['name','premises','conclusion','proof']);require(type(d['name']) is str,'declared name')
    require(type(d['premises']) is tuple and type(d['proof']) is tuple and d['proof'],'local proof list')
    for f in (*d['premises'],d['conclusion']):wf_formula(f,signature);require(not fv(f),'closed port')
    history=[];edges=[]
    def ref(n):integer(n);require(n<len(history),'earlier numeric reference');return history[n]
    for step in d['proof']:
        require(type(step) is dict,'step object');rule=step.get('rule');a=step.get('formula');wf_formula(a,signature)
        if rule=='mp':
            shape(step,['rule','formula','antecedent','implication']);require(ref(step['implication'])==('imp',ref(step['antecedent']),a),'MP match')
        elif rule=='assumption':
            shape(step,['rule','formula','index']);n=integer(step['index']);require(n<len(d['premises']) and a==d['premises'][n],'assumption port')
        elif rule=='axiom':
            shape(step,['rule','formula','name']);require(type(step['name']) is str and immutable(theorems.get(step['name']))==a,'theory name/image')
        elif rule=='block':
            shape(step,['rule','formula','name','inputs']);require(type(step['name']) is str and step['name'] in registry,'dependency availability')
            child=immutable(registry[step['name']]);require(type(step['inputs']) is tuple and tuple(ref(i) for i in step['inputs'])==child['premises'] and a==child['conclusion'],'ordered child ports');edges.append(step['name'])
        elif rule=='eq_subst':
            shape(step,['rule','formula','variable','template','left','right']);v=step['variable'];p=step['template'];s=step['left'];t=step['right'];wf_formula(p,signature);wf_term(s,signature);wf_term(t,signature)
            require(v=='incidenceHole' and p[0:2]==('pred','Incident') and p[2][1]==('var',v) and p[2][0][0]=='fun','restricted atomic template')
            require(a==('imp',('eq',s,t),('imp',plug(p,v,s),plug(p,v,t))),'eq schema')
        elif rule=='instantiate':
            shape(step,['rule','formula','universal','term']);u=step['universal'];t=step['term'];wf_formula(u,signature);wf_term(t,signature)
            require(u[0]=='all' and a==('imp',u,plug(u[2],u[1],t)),'closed instance')
        else:raise Bad('rule outside the six forms')
        history.append(a)
    require(history[-1]==d['conclusion'],'declared end');return edges

def translation(value,images):
    """Independent tuple walk; symbols are never replaced inside strings."""
    value=immutable(value)
    if type(value) is tuple:
        if len(value)==3 and value[0]=='fun' and value[2]==():
            require(value[1] in images,'unmapped constant');return immutable(images[value[1]])
        return tuple(translation(x,images) for x in value)
    if type(value) is dict:return {k:translation(x,images) for k,x in value.items()}
    return value
def reconstruct(request):
    bases=request['blocks'][:2];composite=request['blocks'][2];require(len(request['blocks'])==3,'three source programs')
    theory={'functions':dict.fromkeys(['P','Q','R','l','m','n'],0),'predicates':{'Point':1,'Line':1,'Incident':2},'schemas':[], 'axioms':request['theory']['axioms']}
    records=[];aliases=[];registry={};roles={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m','n'],'v':['l','m','n']}
    for index,order in [(0,['A','B','u','v']),(1,['C','u','v']),(2,['A','B','C','u','v'])]:
        original=request['blocks'][index];family=['universal-uniqueness','incidence-equality-transport','searched-incidence-transport'][index]
        sourcebody={k:v for k,v in original.items() if k!='name'}
        for choices in itertools.product(*(roles[k] for k in order)):
            names={'A':'P','B':'Q','C':'R','u':'l','v':'m'}
            for key,val in zip(order,choices):names[key]=val
            images={k:['fun',n,[]] for k,n in names.items()};body=translation(sourcebody,images);depends=[];mapnames={}
            if index==2:
                for child in bases:
                    transformed=translation({k:v for k,v in child.items() if k!='name'},images)
                    new='hilbert-'+fingerprint(transformed);require(new in registry and encoding(registry[new])==encoding(dict(name=new,**transformed)),'entire alias body matches earlier child')
                    depends.append(new);mapnames[child['name']]=new
                body=copy.deepcopy(body)
                for step in body['proof']:
                    if step['rule']=='block':step['name']=mapnames[step['name']]
            name=('hilbert-' if index<2 else 'hilbert-promoted-')+fingerprint(body);require(name not in registry,'no undeclared duplicate identity')
            definition=dict(name=name,**body);registry[name]=definition
            records.append(dict(family=family,source_block=original['name'],constant_map=images,axiom_name_map={'I.2-uniqueness':'I.2-uniqueness'},dependency_name_map=mapnames,dependencies=depends,definition=definition,body_sha256=fingerprint(body),source_body_sha256=fingerprint(sourcebody)))
            for old,new in mapnames.items():aliases.append(dict(owner=name,source_dependency=old,target_dependency=new,target_body_sha256=fingerprint({k:v for k,v in registry[new].items() if k!='name'})))
    return theory,records,aliases
def verify(cert,request,binding):
    shape(cert,['version','authority','source_native_binding','recipient_theory','records','dependency_aliases']);require(cert['version']=='hilbert-closed-constant-certificate-1' and cert['authority']=='finite_structural_preservation_only','authority label');require(cert['source_native_binding']==binding,'exact original native binding')
    theory,expected,aliases=reconstruct(request)
    require(encoding(cert['recipient_theory'])==encoding(theory) and encoding(cert['records'])==encoding(expected) and encoding(cert['dependency_aliases'])==encoding(aliases),'full independent domain/DAG reconstruction')
    source_registry={}
    for d in request['blocks']:validate_derivation(d,request['theory'],request['theory']['axioms'],source_registry);source_registry[d['name']]=d
    registry={};command_total=edge_total=commutations=0
    sources={d['name']:d for d in request['blocks']}
    for r in cert['records']:
        checkpoint();d=r['definition'];images=r['constant_map'];require(set(images)=={'A','B','C','u','v'},'total image map')
        for key,t in images.items():
            require(type(t) is list and len(t)==3 and t[0]=='fun' and t[2]==[] and t[1] in theory['functions'],'closed declared image')
        for a in request['theory']['axioms'].values():require(encoding(translation(a,images))==encoding(theory['axioms']['I.2-uniqueness']),'retained source axiom image')
        for step in sources[r['source_block']]['proof']:
            if step['rule']=='instantiate':
                u=immutable(step['universal']);t=immutable(step['term']);left=translation(plug(u[2],u[1],t),images);right=plug(translation(u[2],images),u[1],translation(t,images));require(left==right,'instance commuting square');commutations+=1
            if step['rule']=='eq_subst':
                for operand in [step['left'],step['right']]:
                    f=immutable(step['template']);v=step['variable'];t=immutable(operand);require(translation(plug(f,v,t),images)==plug(translation(f,images),v,translation(t,images)),'eq commuting square');commutations+=1
        actual=validate_derivation(d,theory,theory['axioms'],registry);require(actual==r['dependencies'],'exact dependency list');registry[d['name']]=d;command_total+=len(d['proof']);edge_total+=len(actual)
    require(len(registry)==171 and command_total==963 and edge_total==216 and commutations==198,'whole finite expected work')
    return dict(definitions=171,mapped_commands=command_total,dependency_edges=edge_total,aliases=len(aliases),substitution_commutations=commutations)
def mutate(original,case):
    v=copy.deepcopy(original);container=v
    for field in case['path'][:-1]:container=container[field]
    field=case['path'][-1]
    if case['operation']=='delete':container.pop(field) if type(container) is dict else container.pop(field)
    elif case['operation']=='set':container[field]=copy.deepcopy(case['value'])
    elif case['operation']=='append':container[field]=container[field]+[copy.deepcopy(container[field][case['copy_index']])]
    elif case['operation']=='swap':
        arr=container[field];i,j=case['left'],case['right'];arr[i],arr[j]=arr[j],arr[i]
    else:raise Bad('undeclared mutation')
    return v
def main():
    os_limits=[]
    for kind,label in [(resource.RLIMIT_DATA,'RLIMIT_DATA'),(resource.RLIMIT_AS,'RLIMIT_AS/RSS')]:
        prior=resource.getrlimit(kind)
        try:
            finite=[512*1024*1024]+[x for x in prior if x!=resource.RLIM_INFINITY];target=min(finite)
            resource.setrlimit(kind,(target,prior[1]));os_limits.append(dict(name=label,status='set_soft',prior=list(prior),requested_soft=target,actual=list(resource.getrlimit(kind))))
        except (ValueError,OSError) as e:os_limits.append(dict(name=label,status='unsupported',reason=str(e),prior=list(prior)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(ResourceUnknown('180s audit wall ceiling')));signal.alarm(180);began=time.perf_counter();phase='pins'
    try:
        plan=read(HERE/'plan-v3.json');require(plan['budgets']==dict(production_wall_seconds=180,audit_wall_seconds=180,host_ceiling_bytes=512*1024*1024),'frozen limits');entries=0
        for rel,p in {**plan['source_pins'],**plan['inputs']}.items():require(file_hash(ROOT/rel)==p['sha256'] and (ROOT/rel).stat().st_size==p['bytes'],'frozen file '+rel)
        for rel,p in plan['preserved_manifests'].items():
            require(file_hash(ROOT/rel)==p['sha256'],'preserved manifest')
            for r in read(ROOT/rel)['files']:require(file_hash(ROOT/r['path'])==r['sha256'] and (ROOT/r['path']).stat().st_size==r['bytes'],'prior evidence unchanged');entries+=1
        record=read(ROOT/plan['source_record'])[0];receipt=read(ROOT/plan['source_receipt']);snapshot=read(ROOT/plan['source_snapshot']);request=record['request']
        require(record['result']['status']==receipt['native_outcome']=='accepted' and receipt['status']=='passed' and receipt['native_micro_steps']==record['result']['micro_steps'],'exact native/replay receipts')
        require(fingerprint(request)==record['request_sha256']==receipt['request_sha256']==snapshot['source_request_sha256'],'request identity')
        require(snapshot['blocks']==request['blocks'] and snapshot['source_theory']==request['theory'],'prior schema extraction exact')
        binding=dict(request_sha256=record['request_sha256'],input_sha256=record['input_sha256'],output_sha256=record['output_sha256'],native_record_file_sha256=plan['inputs'][plan['source_record']]['sha256'],native_receipt_file_sha256=plan['inputs'][plan['source_receipt']]['sha256'],native_micro_steps=record['result']['micro_steps'])
        phase='finite replay';cert=read(HERE/'certificate-v3.json.gz',strict=True);stage=time.perf_counter();finite=verify(cert,request,binding);finite_seconds=time.perf_counter()-stage
        preview=read(ROOT/plan['preview'])['primary'];require(encoding([r['definition'] for r in cert['records']])==encoding([r['definition'] for r in preview['base_definitions']+preview['promoted_definitions']]),'exact frozen planning grammar correspondence')
        phase='corruptions';reports=read(HERE/'corruptions-v3.json');expected=[];stage=time.perf_counter()
        for case in plan['certificate_corruptions']:
            v=mutate(cert,case)
            try:verify(v,request,binding)
            except (Bad,KeyError,IndexError,TypeError):expected.append(dict(name=case['name'],mutant_sha256=fingerprint(v),status='rejected'))
            else:raise Bad('certificate corruption accepted '+case['name'])
        for case in plan['primitive_corruptions']:
            i=case['record_index'];d=mutate(cert['records'][i]['definition'],case);available={r['definition']['name']:r['definition'] for r in cert['records'][:i]}
            try:validate_derivation(d,cert['recipient_theory'],cert['recipient_theory']['axioms'],available)
            except (Bad,KeyError,IndexError,TypeError):expected.append(dict(name=case['name'],mutant_sha256=fingerprint(d),status='rejected'))
            else:raise Bad('primitive corruption accepted '+case['name'])
        duplicate=b'{"version":"first","version":"second"}'
        def unique(items):
            result={}
            for k,v in items:require(k not in result,'duplicate raw field');result[k]=v
            return result
        try:json.loads(duplicate,object_pairs_hook=unique)
        except Bad:expected.append(dict(name='raw-duplicate-json-field',mutant_sha256=hashlib.sha256(duplicate).hexdigest(),status='rejected'))
        else:raise Bad('raw duplicate accepted')
        require(len(reports)==len(expected) and all(all(r[k]==v for k,v in e.items()) for r,e in zip(reports,expected)),'all actual corruption results independently reproduced')
        corruption_seconds=time.perf_counter()-stage;production=read(HERE/'production-v3.json')
        require(production['status']=='checked_finite_structural_preservation' and production['certificate_sha256']==file_hash(HERE/'certificate-v3.json.gz') and all(production[k]==v for k,v in finite.items()),'authoritative production report bound to independent evidence')
        require(production['peak_rss_bytes']<=512*1024*1024 and production['production_seconds_before_final_result_write']<=180,'production resource limits')
        promoted=cert['records'][63:];coincident={'coincident_common_points':sum(r['constant_map']['A']==r['constant_map']['B'] for r in promoted),'coincident_lines':sum(r['constant_map']['u']==r['constant_map']['v'] for r in promoted),'transport_equals_A':sum(r['constant_map']['C']==r['constant_map']['A'] for r in promoted),'transport_equals_B':sum(r['constant_map']['C']==r['constant_map']['B'] for r in promoted)}
        require(coincident==production['positive_noninjective_counts'] and coincident==dict(coincident_common_points=54,coincident_lines=36,transport_equals_A=36,transport_equals_B=36),'complete noninjective coverage')
        checkpoint();result=dict(status='passed_finite_structural_audit',**finite,certificate_sha256=file_hash(HERE/'certificate-v3.json.gz'),plan_sha256=file_hash(HERE/'plan-v3.json'),production_sha256=file_hash(HERE/'production-v3.json'),rejected_corruptions=len(expected),positive_noninjective_counts=coincident,preserved_file_entries=entries,finite_replay_seconds=finite_seconds,corruption_replay_seconds=corruption_seconds,audit_seconds_before_final_result_write=time.perf_counter()-began,peak_rss_bytes=memory(),native_queries=0,point_models=0,target_searches=0,authority_adapter_activated=False,native_program_correspondence='open',scope='Independent tuple syntax/domain/DAG reconstruction, exact source receipt bindings and finite local-rule checks; not new native execution, formal native-program correspondence or activated inventory. Harness elapsed includes the final audit-file write.')
        result['os_limits']=os_limits
        save(HERE/'audit-v3.json',result);print(json.dumps(result),flush=True)
    except (ResourceUnknown,MemoryError) as e:
        save(HERE/'audit-v3.json',dict(status='unknown_audit_resource',phase=phase,reason=str(e),seconds=time.perf_counter()-began,peak_rss_bytes=memory()));raise
    finally:signal.alarm(0)
if __name__=='__main__':main()
