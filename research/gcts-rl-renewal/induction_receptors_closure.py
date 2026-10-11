"""Generic checked-proof expansion, hypothesis discharge and eigen closure.

These transformations consume a found ground certificate; they do not choose
a target proof path. The resulting request still needs whole native acceptance.
No block or hypothesis is silently promoted to a global axiom.
"""
import copy
import logic as L
from induction_receptors_catalog import Proof,freeze,thaw,deduce,occupied,close

def expand(request):
    definitions={d['name']:d for d in request['blocks']};out=Proof();active=set()
    def sequence(lines,assumptions=()):
        mapped=[]
        for row in lines:
            r=row['rule'];c=copy.deepcopy(row)
            if r=='assumption':
                index=c['index']
                if not 0<=index<len(assumptions):raise ValueError('local assumption index')
                i=assumptions[index]
                if out.lines[i]['formula']!=c['formula']:raise ValueError('local premise formula mismatch')
            elif r=='block':
                name=c['name']
                if name in active or name not in definitions:raise ValueError('unknown or recursive lemma')
                d=definitions[name]
                if any(type(j) is not int or not 0<=j<len(mapped) for j in c['inputs']):raise ValueError('strict earlier lemma input required')
                refs=[mapped[j] for j in c['inputs']]
                if [out.lines[j]['formula'] for j in refs]!=d['premises'] or c['formula']!=d['conclusion']:raise ValueError('lemma interface mismatch')
                active.add(name);i=sequence(d['proof'],refs);active.remove(name)
            else:
                for k in ('antecedent','implication') if r=='mp' else ('source',) if r=='generalize' else ():
                    if not 0<=c[k]<len(mapped):raise ValueError('strict earlier reference required')
                    c[k]=mapped[c[k]]
                out.lines.append(c);i=len(out.lines)-1
            mapped.append(i)
        if not mapped:raise ValueError('empty proof expansion')
        return mapped[-1]
    last=sequence(request['proof'])
    if out.lines[last]['formula']!=request['target']:raise ValueError('expanded target differs')
    if last!=len(out.lines)-1:
        f=freeze(request['target']);a=out.emit('tautology',L.Imp(f,f));out.mp(last,a)
    return out.lines

def discharge(request,hypothesis_axioms):
    """Replace ground named hypotheses by one explicit conjunction assumption.

    The conjunction is mechanically built in declared input order. Its members
    follow by tautological projections; only then is the single assumption
    discharged by the generic Hilbert transform.
    """
    names=list(hypothesis_axioms)
    if not names or len(names)!=len(set(names)):raise ValueError('distinct named hypotheses required')
    theory=copy.deepcopy(request['theory']);hypotheses=[freeze(theory['axioms'][n]) for n in names]
    H=hypotheses[-1]
    for f in reversed(hypotheses[:-1]):H=('and',f,H)
    for n in names:del theory['axioms'][n]
    source=expand(request);out=Proof();assumption=out.emit('assumption',H,index=0);mapped=[]
    for row in source:
        c=copy.deepcopy(row);r=c['rule']
        if r=='axiom' and c['name'] in names:
            f=freeze(c['formula']);a=out.emit('tautology',L.Imp(H,f));i=out.mp(assumption,a)
        else:
            for k in ('antecedent','implication') if r=='mp' else ('source',) if r=='generalize' else ():c[k]=mapped[c[k]]
            out.lines.append(c);i=len(out.lines)-1
        mapped.append(i)
    if i!=len(out.lines)-1:raise ValueError('discharge suffix mismatch')
    lines=deduce(out.lines,H);target=lines[-1]['formula']
    return dict(protocol=request['protocol'],theory=theory,blocks=[],proof=lines,target=target)

def eigen_close(request,constants):
    """Replace fresh nullary constants by fresh variables, then quantify.

    Constants must be absent from every retained axiom and have arity zero.
    Fresh names avoid *all* bound/free names and command variable fields in the
    source proof, so even eq_subst/instantiate templates stay capture-free.
    """
    constants=list(constants)
    if len(constants)!=len(set(constants)):raise ValueError('duplicate eigen constant')
    if request['blocks']:raise ValueError('expand local definitions before eigen closure')
    theory=copy.deepcopy(request['theory']);used=set()
    def scan(v):
        if isinstance(v,dict):
            if isinstance(v.get('variable'),str):used.add(v['variable'])
            for a in v.values():scan(a)
        elif isinstance(v,list):
            if v and v[0]=='var':used.add(v[1])
            if v and v[0]=='all':used.add(v[1])
            for a in v:scan(a)
    scan(request)
    def occurs(v,name):
        return isinstance(v,list) and (v==['fun',name,[]] or any(occurs(x,name) for x in v)) or isinstance(v,dict) and any(occurs(x,name) for x in v.values())
    binding={}
    for constant in constants:
        if theory['functions'].get(constant)!=0:raise ValueError('eigen symbol must be a declared nullary function')
        if any(occurs(f,constant) for f in theory['axioms'].values()):raise ValueError('eigen constant occurs in a retained axiom')
        i=0
        while 'eigen'+str(i) in used:i+=1
        name='eigen'+str(i);used.add(name);binding[constant]=name;del theory['functions'][constant]
    def replace(v):
        if isinstance(v,dict):return {k:replace(a) for k,a in v.items()}
        if isinstance(v,list):
            if len(v)==3 and v[0]=='fun' and not v[2] and v[1] in binding:return ['var',binding[v[1]]]
            return [replace(a) for a in v]
        return v
    lines=replace(request['proof']);target=replace(request['target']);out=Proof();out.lines=lines
    for name in reversed(list(binding.values())):
        i=len(out.lines)-1;target=['all',name,target];out.emit('generalize',freeze(target),variable=name,source=i)
    return dict(protocol=request['protocol'],theory=theory,blocks=[],proof=out.lines,target=target),binding

def close_ground(request,hypothesis_axioms,eigen_constants):
    result=discharge(request,hypothesis_axioms);result,binding=eigen_close(result,eigen_constants)
    return dict(request=result,eigen_binding=binding,authored_infrastructure='Generic block expansion, conjunction projection, dependency-aware deduction and fresh-eigenconstant closure; no new target search or authored theorem proof.',status='requires_whole_native_check')
