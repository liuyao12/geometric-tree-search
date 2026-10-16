"""Typed templates mined from actual proofs; ground native admission is mandatory.

Constants become closed-term parameters and predicate names become parameters
of fixed arity. Function heads of positive arity and variable/binder names stay
literal. A template is a proposal, not an independently trusted theorem.
"""
import copy,itertools,time
from certificate_boundary_search import canonical,digest
from semantic_lemma_inventory import used_definitions

def mine(request,inventory,provenance):
    definitions={d['name']:d for d in inventory['definitions']} if inventory else {}
    premises=[];rows=[];dependencies=set()
    for row in request['proof']:
        c=copy.deepcopy(row)
        if c['rule']=='axiom':
            f=request['theory']['axioms'][c['name']]
            if f!=c['formula']:raise ValueError('donor axiom identity')
            if f not in premises:premises.append(f)
            c=dict(rule='assumption',formula=f,index=premises.index(f))
        elif c['rule']=='block':
            d=definitions[c.pop('name')];dependencies.add(d['family'])
            c['call']=dict(family=d['family'],arguments=copy.deepcopy(d['arguments']))
        rows.append(c)
    parameters=[];origins=[];identities={}
    def parameter(kind,value,arity=None):
        identity=(kind,canonical(value),arity)
        if identity not in identities:
            identities[identity]=len(parameters)
            parameters.append(dict(kind=kind,**({'arity':arity} if kind=='predicate' else {})))
            origins.append(copy.deepcopy(value))
        n=identities[identity]
        return ['term_meta',n] if kind=='term' else ['predicate_meta',n,arity]
    def abstract(v):
        if isinstance(v,list):
            if len(v)==3 and v[0]=='fun' and v[2]==[]:return parameter('term',v)
            if len(v)==3 and v[0]=='pred':return ['pred',parameter('predicate',v[1],len(v[2])),[abstract(t) for t in v[2]]]
            if len(v)==3 and v[0]=='predicate_argument':return [v[0],parameter('predicate',v[1],v[2]),v[2]]
            return [abstract(x) for x in v]
        if isinstance(v,dict):return {k:abstract(x) for k,x in v.items()}
        return v
    template=abstract(dict(premises=premises,conclusion=request['target'],proof=rows))
    body=dict(parameters=parameters,template=template,dependencies=sorted(dependencies))
    return dict(id=digest(body),**body,donor_values=origins,provenance=provenance,
                scope='Closed-term and fixed-arity predicate-name template from searched commands. Binder names are literal. Every matched ground definition requires native admission.')

def argument(kind,value,arity=None):
    return ['term_argument',copy.deepcopy(value)] if kind=='term' else ['predicate_argument',value,arity]

def valid_argument(parameter,arg,spec,catalog):
    if parameter['kind']=='term':
        return isinstance(arg,list) and len(arg)==2 and arg[0]=='term_argument' and arg[1] in catalog['equality_terms']
    return (isinstance(arg,list) and len(arg)==3 and arg[0]=='predicate_argument' and
            arg[2]==parameter['arity'] and spec['theory']['predicates'].get(arg[1])==arg[2])

def replace(value,args):
    if isinstance(value,list):
        if value and value[0] in ('term_meta','predicate_meta'):
            if type(value[1]) is not int or not 0<=value[1]<len(args):raise ValueError('parameter outside binding')
            arg=args[value[1]]
            if value[0]=='term_meta':
                if arg[0]!='term_argument':raise ValueError('term parameter kind')
                return copy.deepcopy(arg[1])
            if arg[0]!='predicate_argument' or arg[2]!=value[2]:raise ValueError('predicate parameter arity')
            return arg[1]
        return [replace(v,args) for v in value]
    if isinstance(value,dict):return {k:replace(v,args) for k,v in value.items()}
    return value

def match(pattern,value,binding,family,spec,catalog):
    if isinstance(pattern,list) and pattern and pattern[0] in ('term_meta','predicate_meta'):
        index=pattern[1]
        arg=argument('term',value) if pattern[0]=='term_meta' else argument('predicate',value,pattern[2])
        if not valid_argument(family['parameters'][index],arg,spec,catalog):return None
        if index in binding:return binding if binding[index]==arg else None
        return {**binding,index:arg}
    if isinstance(pattern,list):
        if not isinstance(value,list) or len(pattern)!=len(value):return None
        for p,v in zip(pattern,value):
            binding=match(p,v,binding,family,spec,catalog)
            if binding is None:return None
        return binding
    return binding if pattern==value else None

def bindings(family,spec,catalog):
    """Complete interface join in the declared finite typed parameter universe."""
    pool=[]
    for p in family['parameters']:
        pool.append([argument('term',t) for t in catalog['equality_terms']] if p['kind']=='term' else
                    [argument('predicate',n,a) for n,a in sorted(spec['theory']['predicates'].items()) if a==p['arity']])
    interface=family['template']['premises']+[family['template']['conclusion']];found={}
    def visit(i,b):
        if i==len(interface):
            missing=[k for k in range(len(pool)) if k not in b]
            for values in itertools.product(*(pool[k] for k in missing)):
                complete={**b,**dict(zip(missing,values))};args=[complete[k] for k in range(len(pool))]
                found[canonical(args)]=args
            return
        for formula in catalog['basis']:
            bound=match(interface[i],formula,b,family,spec,catalog)
            if bound is not None:visit(i+1,bound)
    visit(0,{})
    return [found[k] for k in sorted(found)]

def specialize(library,spec,catalog):
    families={f['id']:f for f in library}
    if len(families)!=len(library):raise ValueError('duplicate family identity')
    definitions={};order=[];active=set();interfaces=[];began=time.perf_counter()
    def build(fid,args):
        f=families[fid]
        if len(args)!=len(f['parameters']) or not all(valid_argument(p,a,spec,catalog) for p,a in zip(f['parameters'],args)):raise ValueError('typed family binding')
        name='lemma'+digest(dict(family=fid,arguments=args))
        if name in definitions:
            if definitions[name]['arguments']!=args or definitions[name]['family']!=fid:raise ValueError('ground identity collision')
            return name
        if name in active:raise ValueError('cyclic family definition')
        active.add(name);ground=replace(f['template'],args);proof=[];level=1
        for row in ground['proof']:
            c=copy.deepcopy(row)
            if c['rule']=='block':
                call=c.pop('call');dep=build(call['family'],call['arguments']);c['name']=dep
                level=max(level,definitions[dep]['level']+1)
            proof.append(c)
        native=dict(name=name,premises=ground['premises'],conclusion=ground['conclusion'],proof=proof)
        definitions[name]=dict(name=name,family=fid,arguments=copy.deepcopy(args),level=level,definition=native)
        active.remove(name);order.append(name);return name
    for f in library:
        for args in bindings(f,spec,catalog):interfaces.append(build(f['id'],args))
    return dict(definitions=[definitions[n] for n in order],interfaces=list(dict.fromkeys(interfaces)),
                native_blocks=[definitions[n]['definition'] for n in order],matching_seconds=time.perf_counter()-began)

def admit(spec,inventory,oracle,limit=5*10**9):
    """Check every ground definition with its exact dependency closure.

    Splitting admission keeps unused definitions out of bounded native memory.
    Final certificates still submit all definitions actually called together.
    Unknown or rejected admission never authorizes an omitted candidate.
    """
    began=time.perf_counter();queries=[];taut=['imp',['bot'],['bot']]
    for d in inventory['definitions']:
        call=dict(rule='block',formula=d['definition']['conclusion'],name=d['name'])
        blocks=used_definitions(inventory,[call])
        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=blocks,
                     proof=[dict(rule='tautology',formula=taut)],target=taut)
        q=oracle.request(request,limit,'first_order_family_definition');queries.append(dict(name=d['name'],query=q['id']))
        if q['result']['status']!='accepted':return dict(**inventory,status='unknown_or_rejected_native_inventory',admissions=queries,admission_seconds=time.perf_counter()-began)
    return dict(**inventory,status='native_accepted',admissions=queries,admission_seconds=time.perf_counter()-began,
                scope='All finite matched interfaces have ground-native-checked definitions and dependency closures. No universal family soundness theorem is claimed.')
