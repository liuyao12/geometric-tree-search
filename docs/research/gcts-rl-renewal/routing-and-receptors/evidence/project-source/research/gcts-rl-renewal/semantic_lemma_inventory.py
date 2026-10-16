"""Parameterize discovered proofs and specialize a checked lemma dependency DAG.

Parameters stand for formulas, using uniform replacement of nullary predicates.
These templates are proposals: the unchanged native checker checks each ground
definition before its interface may be used by the point compiler.
"""
import copy,itertools
from certificate_boundary_search import canonical,digest

def transform(value,atoms):
    if isinstance(value,list):
        if len(value)==3 and value[0]=='pred' and value[2]==[]:
            name=value[1]
            if name not in atoms:atoms[name]=len(atoms)
            return ['meta',atoms[name]]
        return [transform(x,atoms) for x in value]
    if isinstance(value,dict):return {k:transform(v,atoms) for k,v in value.items()}
    return value

def mine(request,ground_inventory,provenance):
    """Use a searched command sequence, with no invented derivation steps."""
    proof=request['proof'];premises=[];indices={};converted=[];dependencies=set()
    ground={r['name']:r for r in ground_inventory}
    for command in proof:
        c=copy.deepcopy(command)
        if c['rule']=='axiom':
            f=request['theory']['axioms'][c['name']]
            if f!=c['formula']:raise ValueError('donor axiom does not match')
            key=canonical(f)
            if key not in indices:indices[key]=len(premises);premises.append(f)
            c=dict(rule='assumption',formula=f,index=indices[key])
        elif c['rule']=='block':
            item=ground[c.pop('name')];dependencies.add(item['family'])
            c['call']=dict(family=item['family'],arguments=item['arguments'])
        converted.append(c)
    atoms={};template=transform(dict(premises=premises,conclusion=request['target'],proof=converted),atoms)
    params=len(atoms)
    identity=digest(dict(parameters=params,template=template))
    return dict(id=identity,parameters=params,template=template,dependencies=sorted(dependencies),
                provenance=provenance,donor_atoms=list(atoms),
                scope='Uniform formula substitution template extracted from an actual searched proof. Ground native checking remains mandatory.')

def replace(value,arguments):
    if isinstance(value,list):
        if len(value)==2 and value[0]=='meta':
            if not isinstance(value[1],int) or not 0<=value[1]<len(arguments):raise ValueError('parameter outside binding')
            return copy.deepcopy(arguments[value[1]])
        return [replace(v,arguments) for v in value]
    if isinstance(value,dict):return {k:replace(v,arguments) for k,v in value.items()}
    return value

def unify(pattern,formula,binding):
    if isinstance(pattern,list) and len(pattern)==2 and pattern[0]=='meta':
        k=pattern[1]
        if k in binding:return binding if binding[k]==formula else None
        out=binding.copy();out[k]=formula;return out
    if isinstance(pattern,list):
        if not isinstance(formula,list) or len(pattern)!=len(formula):return None
        for p,f in zip(pattern,formula):
            binding=unify(p,f,binding)
            if binding is None:return None
        return binding
    return binding if pattern==formula else None

def bindings(family,basis):
    """Complete finite interface join; no known proof path supplies a binding."""
    interface=family['template']['premises']+[family['template']['conclusion']]
    found={}
    def visit(index,binding):
        if index==len(interface):
            free=[j for j in range(family['parameters']) if j not in binding]
            for choices in itertools.product(basis,repeat=len(free)):
                b={**binding,**dict(zip(free,choices))}
                args=[b[j] for j in range(family['parameters'])]
                found[canonical(args)]=args
            return
        for formula in basis:
            b=unify(interface[index],formula,binding)
            if b is not None:visit(index+1,b)
    visit(0,{})
    return [found[k] for k in sorted(found)]

def specialize(library,basis):
    """Return complete matched interfaces and their dependency-first definitions."""
    by_id={f['id']:f for f in library}
    if len(by_id)!=len(library):raise ValueError('duplicate family identity')
    definitions={};order=[];active=set()
    def build(fid,args):
        f=by_id[fid]
        if len(args)!=f['parameters']:raise ValueError('binding arity')
        name='lemma'+digest(dict(family=fid,arguments=args))
        if name in definitions:
            old=definitions[name]
            if old['family']!=fid or old['arguments']!=args:raise ValueError('identifier collision')
            return name
        if name in active:raise ValueError('cyclic lemma dependency')
        active.add(name);ground=replace(f['template'],args);proof=[]
        level=1
        for c in ground['proof']:
            c=copy.deepcopy(c)
            if c['rule']=='block':
                call=c.pop('call');dep=build(call['family'],call['arguments'])
                c['name']=dep;level=max(level,definitions[dep]['level']+1)
            proof.append(c)
        native=dict(name=name,premises=ground['premises'],conclusion=ground['conclusion'],proof=proof)
        definitions[name]=dict(name=name,family=fid,arguments=copy.deepcopy(args),level=level,definition=native)
        active.remove(name);order.append(name);return name
    interfaces=[]
    for family in library:
        for args in bindings(family,basis):interfaces.append(build(family['id'],args))
    return dict(definitions=[definitions[n] for n in order],interfaces=list(dict.fromkeys(interfaces)),
                native_blocks=[definitions[n]['definition'] for n in order],
                scope='All interface matches to the declared syntactic basis; dependency definitions registered before use. This generated inventory is not yet authority without native acceptance.')

def used_definitions(inventory,proof):
    """Keep the dependency closure of actual calls, in original registry order.

    This removes unused definitions from a certificate, not candidate interfaces
    from search. The final whole native checker checks this smaller certificate.
    No imported or already-trusted theorem is introduced by the operation.
    """
    definitions={d['name']:d['definition'] for d in inventory['definitions']}
    needed=set();active=set()
    def visit(name):
        if name in needed:return
        if name in active:raise ValueError('cyclic used lemma')
        if name not in definitions:raise ValueError('unregistered lemma call')
        active.add(name)
        for command in definitions[name]['proof']:
            if command['rule']=='block':visit(command['name'])
        active.remove(name);needed.add(name)
    for command in proof:
        if command['rule']=='block':visit(command['name'])
    output=[copy.deepcopy(d) for d in inventory['native_blocks'] if d['name'] in needed]
    if len(output)!=len(needed):raise ValueError('inconsistent native registry')
    seen=set()
    for definition in output:
        if any(c['name'] not in seen for c in definition['proof'] if c['rule']=='block'):
            raise ValueError('dependency must precede its call')
        seen.add(definition['name'])
    return output
