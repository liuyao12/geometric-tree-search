"""Complete fresh sorted domain for the actually discovered incidence receptor.

Only the recorded searched definition is specialized. Exact canonical decorated
definitions, rather than logical equivalence or a sampled pool, justify dedup.
The primitive-interface baseline is the same 28 authored level-one rules.
"""
import copy,itertools
from certificate_boundary_search import canonical,digest
from hilbert_receptors_catalog import axiom,condition,F,P,I,syntax_and_definitions

PARAMETERS=['A','B','C','u','v']
DOMAINS={'A':['P','Q'],'B':['P','Q'],'C':['P','Q','R'],'u':['l','m'],'v':['l','m']}

def rename(value,binding):
    if isinstance(value,list):
        if len(value)==3 and value[0]=='fun' and value[2]==[] and value[1] in binding:
            return ['fun',binding[value[1]],[]]
        return [rename(x,binding) for x in value]
    if isinstance(value,dict):return {k:rename(v,binding) for k,v in value.items()}
    return value

def recipients():
    p,q,r,l,m=map(F,['P','Q','R','l','m']);h=condition(p,q,l,m);inc=P('Incident',r,l)
    signature=dict(functions={x:0 for x in ['P','Q','R','l','m']},predicates=dict(Point=1,Line=1,Incident=2),schemas=[])
    base=dict(sorts={'point':['P','Q','R'],'line':['l','m']},uniqueness_points=['P','Q'],target=P('Incident',r,m),
              scope='Fresh uninterpreted constants in the guarded incidence fragment; no coordinates. No proof sequence supplied.')
    direct=dict(**signature,axioms={'I.2-uniqueness':axiom(),'common-distinct-points':h,'extra-incidence':inc})
    composed=dict(**signature,axioms={'I.2-uniqueness':axiom(),'common-distinct-points':h,'extra-incidence-trigger':I(h,inc)})
    output=[]
    for group,theory,short,enough in [('direct',direct,3,4),('composed',composed,4,5)]:
        for boundary,length in [('short',short),('sufficient',enough)]:
            output.append(dict(id='fresh-'+group+'-'+boundary,group=group,boundary=boundary,length=length,
                               title='Fresh '+group+' incidence: '+str(length)+' rows',theory=copy.deepcopy(theory),**copy.deepcopy(base)))
    return output

def build(source_request):
    specs=recipients();built=syntax_and_definitions(specs[0]);base=built['definitions'];byname={d['name']:d for d in base}
    if len(base)!=28:raise ValueError('complete primitive-interface baseline')
    template=source_request['blocks'][-1];dependencies=source_request['blocks'][:-1]
    if len(dependencies)!=2 or len(template['premises'])!=2 or len(template['proof'])!=4:raise ValueError('actual admitted source receptor shape')
    records=[];unique={};names={}
    for values in itertools.product(*(DOMAINS[p] for p in PARAMETERS)):
        binding=dict(zip(PARAMETERS,values));mapped={};deps=[]
        for original in dependencies:
            d=rename({k:v for k,v in original.items() if k!='name'},binding)
            name='hilbert-'+digest(d);actual=dict(name=name,**d)
            if name not in byname or byname[name]['definition']!=actual:raise ValueError('complete matching dependency absent')
            mapped[original['name']]=name;deps.append(name)
        body=rename({k:v for k,v in template.items() if k!='name'},binding)
        for step in body['proof']:
            if step['rule']=='block':step['name']=mapped[step['name']]
        word=canonical(body);name='hilbert-promoted-'+digest(body)
        if name in names and names[name]!=word:raise ValueError('identifier collision is not exact identity')
        names[name]=word
        if word not in unique:
            unique[word]=dict(name=name,level=2,family='searched-incidence-transport',arguments=values,
                              dependencies=deps,definition=dict(name=name,**body))
        records.append(dict(binding=binding,name=unique[word]['name'],decorated_word_hex=word.hex(),dependencies=deps))
    if len(records)!=48:raise ValueError('full sorted binding domain')
    promoted=list(unique.values());definitions=base+promoted
    theory=copy.deepcopy(specs[0]['theory']);theory['axioms']={'I.2-uniqueness':axiom()}
    groups={}
    for spec in specs:
        if spec['group'] in groups:continue
        b=syntax_and_definitions(spec)
        if b['definitions']!=base:raise ValueError('recipient-independent complete base interfaces')
        groups[spec['group']]=dict(catalog=b['catalog'],basis=b['catalog']['basis'],representative=spec)
    return dict(theory=theory,cases=specs,groups=groups,base_definitions=base,promoted_definitions=promoted,
                definitions=definitions,binding_records=records,parameter_order=PARAMETERS,parameter_domains=DOMAINS,
                bindings_before_dedup=len(records),distinct_decorated_interfaces=len(promoted),
                deduplication='Exact equality of the complete canonical premises/conclusion/proof, including bound dependency names; no logical-equivalence pruning.',
                source_request_sha256=digest(source_request),source_definition_name=template['name'])
