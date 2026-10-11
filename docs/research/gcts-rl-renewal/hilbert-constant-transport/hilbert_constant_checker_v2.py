"""Finite structural certificate checker; no native or point authority.

Six actual rule forms and closed zero-arity constant images only. This checks
explicit source/mapped syntax and local derivations, not native correspondence.
"""
import copy, hashlib, itertools, json

class Invalid(ValueError):pass
def need(p,s):
    if not p:raise Invalid(s)
def word(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(x):return hashlib.sha256(word(x)).hexdigest()
def strict_json(raw):
    def pairs(xs):
        d={}
        for k,v in xs:
            need(k not in d,'duplicate JSON field');d[k]=v
        return d
    def bad(_):raise Invalid('inexact JSON number')
    return json.loads(raw,object_pairs_hook=pairs,parse_float=bad,parse_constant=bad)
def fields(d,ks):need(type(d) is dict and set(d)==set(ks),'exact fields')
def natural(v):need(type(v) is int and v>=0,'natural index');return v
def constant(n):return ['fun',n,[]]
def mapped(x,m):
    if isinstance(x,list):
        if len(x)==3 and x[0]=='fun' and x[2]==[]:
            need(x[1] in m,'undeclared source constant');return copy.deepcopy(m[x[1]])
        return [mapped(a,m) for a in x]
    if isinstance(x,dict):return {k:mapped(a,m) for k,a in x.items()}
    return x
def term(t,s):
    need(type(t) is list and bool(t),'term AST')
    if len(t)==2 and t[0]=='var':need(type(t[1]) is str,'variable name');return
    need(len(t)==3 and t[0]=='fun' and type(t[1]) is str and t[2]==[] and s['functions'].get(t[1])==0,'zero-arity declared constant')
def formula(f,s):
    need(type(f) is list and bool(f),'formula AST');k=f[0]
    if k=='pred':
        need(len(f)==3 and type(f[1]) is str and type(f[2]) is list and s['predicates'].get(f[1])==len(f[2]),'predicate arity')
        for t in f[2]:term(t,s)
    elif k=='eq':
        need(len(f)==3,'equality shape');term(f[1],s);term(f[2],s)
    elif k=='all':
        need(len(f)==3 and type(f[1]) is str,'binder shape');formula(f[2],s)
    elif k=='not':need(len(f)==2,'negation shape');formula(f[1],s)
    elif k in ['and','or','imp']:
        need(len(f)==3,'binary connective shape');formula(f[1],s);formula(f[2],s)
    else:need(f==['bot'],'bottom shape')
def free(f):
    if f[0]=='all':return free(f[2])-{f[1]}
    if f[0]=='pred':return {t[1] for t in f[2] if t[0]=='var'}
    if f[0]=='eq':return {t[1] for t in f[1:] if t[0]=='var'}
    if f[0]=='bot':return set()
    return set().union(*(free(g) for g in f[1:]))
def subst(f,x,t):
    need(t[0]=='fun' and t[2]==[],'substitution restricted to a closed constant')
    def tr(u):return copy.deepcopy(t) if u==['var',x] else copy.deepcopy(u)
    k=f[0]
    if k=='pred':return [k,f[1],[tr(u) for u in f[2]]]
    if k=='eq':return [k,tr(f[1]),tr(f[2])]
    if k=='all':return copy.deepcopy(f) if f[1]==x else [k,f[1],subst(f[2],x,t)]
    if k=='bot':return ['bot']
    return [k,*[subst(g,x,t) for g in f[1:]]]
RULE_FIELDS={'assumption':['index'],'axiom':['name'],'instantiate':['universal','term'],
             'eq_subst':['variable','template','left','right'],'mp':['antecedent','implication'],'block':['name','inputs']}
def check_block(d,s,axioms,available):
    fields(d,['name','premises','conclusion','proof']);need(type(d['name']) is str,'block name')
    need(type(d['premises']) is list and type(d['proof']) is list and bool(d['proof']),'nonempty block proof')
    for f in d['premises']+[d['conclusion']]:formula(f,s);need(not free(f),'closed interface')
    prior=[];dependencies=[]
    for c in d['proof']:
        need(type(c) is dict and c.get('rule') in RULE_FIELDS,'only six actual rules');r=c['rule'];fields(c,['rule','formula']+RULE_FIELDS[r]);f=c['formula'];formula(f,s)
        def earlier(i):
            natural(i);need(i<len(prior),'strict-earlier reference');return prior[i]
        if r=='assumption':
            i=natural(c['index']);need(i<len(d['premises']) and f==d['premises'][i],'ordered local premise')
        elif r=='axiom':need(type(c['name']) is str and axioms.get(c['name'])==f,'exact named theorem axiom')
        elif r=='instantiate':
            u=c['universal'];formula(u,s);term(c['term'],s);need(c['term'][0]=='fun','closed instantiation term')
            need(u[0]=='all' and f==['imp',u,subst(u[2],u[1],c['term'])],'universal instance')
        elif r=='eq_subst':
            x=c['variable'];p=c['template'];formula(p,s);term(c['left'],s);term(c['right'],s)
            need(x=='incidenceHole' and p[0]=='pred' and p[1]=='Incident' and p[2][1]==['var',x] and p[2][0][0]=='fun','actual atomic incidence template')
            need(c['left'][0]==c['right'][0]=='fun','closed equality operands')
            need(f==['imp',['eq',c['left'],c['right']],['imp',subst(p,x,c['left']),subst(p,x,c['right'])]],'equality substitution')
        elif r=='mp':need(earlier(c['implication'])==['imp',earlier(c['antecedent']),f],'literal MP match')
        else:
            need(type(c['name']) is str and c['name'] in available,'earlier dependency declaration')
            b=available[c['name']];need(type(c['inputs']) is list,'input list')
            need([earlier(i) for i in c['inputs']]==b['premises'] and f==b['conclusion'],'exact ordered block interface')
            dependencies.append(c['name'])
        prior.append(f)
    need(prior[-1]==d['conclusion'],'last conclusion');return dependencies
def binding_check(m,signature):
    fields(m,['A','B','C','u','v'])
    roles={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m','n'],'v':['l','m','n']}
    for k,t in m.items():
        term(t,signature);need(t[0]=='fun' and t[1] in roles[k],'closed role-preserving image')

def reconstruct(source):
    source_blocks=source['blocks'];need(len(source_blocks)==3,'exact three schemas')
    u,e,r=source_blocks;output=[];aliases=[];registered={}
    theory={'functions':{x:0 for x in ['P','Q','R','l','m','n']},'predicates':{'Point':1,'Line':1,'Incident':2},'schemas':[],
            'axioms':copy.deepcopy(source['source_theory']['axioms'])}
    recipes=[('universal-uniqueness',u,['A','B','u','v'],[['P','Q'],['P','Q'],['l','m','n'],['l','m','n']]),
             ('incidence-equality-transport',e,['C','u','v'],[['P','Q','R'],['l','m','n'],['l','m','n']]),
             ('searched-incidence-transport',r,['A','B','C','u','v'],[['P','Q'],['P','Q'],['P','Q','R'],['l','m','n'],['l','m','n']])]
    for family,original,keys,pools in recipes:
        for values in itertools.product(*pools):
            names={'A':'P','B':'Q','C':'R','u':'l','v':'m'};names.update(dict(zip(keys,values)));m={k:constant(v) for k,v in names.items()}
            binding_check(m,theory);body=mapped({k:v for k,v in original.items() if k!='name'},m);dep_names={};deps=[]
            if original==r:
                for dependency in [u,e]:
                    db=mapped({k:v for k,v in dependency.items() if k!='name'},m);dn='hilbert-'+sha(db)
                    need(dn in registered and registered[dn]==dict(name=dn,**db),'exact mapped dependency identity')
                    dep_names[dependency['name']]=dn;deps.append(dn)
                for c in body['proof']:
                    if c['rule']=='block':c['name']=dep_names[c['name']]
            name=('hilbert-promoted-' if original==r else 'hilbert-')+sha(body)
            need(name not in registered,'unexpected identical decorated duplicate')
            definition=dict(name=name,**body);registered[name]=definition
            record=dict(family=family,source_block=original['name'],constant_map=m,axiom_name_map={'I.2-uniqueness':'I.2-uniqueness'},
                dependency_name_map=dep_names,dependencies=deps,definition=definition,body_sha256=sha(body),source_body_sha256=sha({k:v for k,v in original.items() if k!='name'}))
            output.append(record)
            for old,new in dep_names.items():aliases.append(dict(owner=name,source_dependency=old,target_dependency=new,target_body_sha256=sha({k:v for k,v in registered[new].items() if k!='name'})))
    return theory,output,aliases

def check(certificate,source,expected_binding):
    fields(certificate,['version','authority','source_native_binding','recipient_theory','records','dependency_aliases'])
    need(certificate['version']=='hilbert-closed-constant-certificate-1' and certificate['authority']=='finite_structural_preservation_only','separate structural authority')
    need(certificate['source_native_binding']==expected_binding,'exact source native/replay binding')
    source_available={};source_commands=0
    for d in source['blocks']:
        check_block(d,source['source_theory'],source['source_theory']['axioms'],source_available);source_available[d['name']]=d;source_commands+=len(d['proof'])
    theory,expected,aliases=reconstruct(source)
    need(certificate['recipient_theory']==theory,'exact six-constant recipient theory')
    need(certificate['records']==expected,'complete ordered finite certificate reconstruction')
    need(certificate['dependency_aliases']==aliases,'complete dependency alias DAG')
    available={};commands=0;dependencies=0;commutations=0
    for record in certificate['records']:
        binding_check(record['constant_map'],theory)
        original=source_available[record['source_block']];m=record['constant_map']
        need(record['axiom_name_map']=={'I.2-uniqueness':'I.2-uniqueness'} and mapped(source['source_theory']['axioms']['I.2-uniqueness'],m)==theory['axioms']['I.2-uniqueness'],'theorem-axiom mapping')
        for c in original['proof']:
            if c['rule']=='instantiate':
                u=c['universal'];t=c['term'];need(mapped(subst(u[2],u[1],t),m)==subst(mapped(u[2],m),u[1],mapped(t,m)),'actual closed instantiation commutation');commutations+=1
            if c['rule']=='eq_subst':
                for t in [c['left'],c['right']]:
                    need(mapped(subst(c['template'],c['variable'],t),m)==subst(mapped(c['template'],m),c['variable'],mapped(t,m)),'actual equality commutation');commutations+=1
        d=record['definition'];deps=check_block(d,theory,theory['axioms'],available)
        need(deps==record['dependencies'],'all dependencies exact and ordered');available[d['name']]=d;commands+=len(d['proof']);dependencies+=len(deps)
    need(len(available)==171 and dependencies==216,'complete finite inventory/DAG')
    return dict(status='checked_finite_structural_preservation',definitions=len(available),source_commands=source_commands,
        mapped_commands=commands,dependency_edges=dependencies,aliases=len(aliases),substitution_commutations=commutations,
        native_program_correspondence='open',native_queries=0,point_models=0,target_searches=0,authority_adapter_activated=False)
