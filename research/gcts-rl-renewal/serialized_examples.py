"""Authored certificates and adversarial cases; not a discovery/search lane."""
import copy
import logic
from serialized_kernel import PROTOCOL, canonical

def request(functions=None, predicates=None, axioms=None, schemas=(), blocks=(), proof=(), target=None):
    return dict(protocol=PROTOCOL, theory=dict(functions=functions or {}, predicates=predicates or {},
                axioms=axioms or {}, schemas=list(schemas)), blocks=list(blocks),
                proof=list(proof), target=target)

def line(rule, formula, **parameters): return dict(rule=rule, formula=formula, **parameters)
def block(name, premises, conclusion, proof):
    return dict(name=name, premises=premises, conclusion=conclusion, proof=proof)

def induction_formula(variable, template):
    """Generator uses the frozen old kernel's substitution, not the new checker."""
    zero = logic.F('zero'); successor = logic.F('succ', logic.V(variable))
    formula = logic.Imp(('and', logic.substitute(template, variable, zero),
                         logic.All(variable, logic.Imp(template, logic.substitute(template, variable, successor)))),
                        logic.All(variable, template))
    for y in reversed(sorted(logic.free(template)-{variable})): formula=logic.All(y, formula)
    return formula

def addition_induction(repeats=1):
    """Prove left zero for addition; arithmetic axioms define recursion on right."""
    x, y = logic.V('x'), logic.V('y'); z = logic.F('zero'); sx = logic.F('succ', x)
    add = lambda a,b: logic.F('add', a,b)
    p = logic.Eq(add(z,x), x); p0 = logic.substitute(p,'x',z); ps = logic.substitute(p,'x',sx)
    e = logic.Eq(add(z,sx),logic.F('succ',add(z,x)))
    step = logic.Imp(p,ps); universal = logic.All('x',step); target = logic.All('x',p)
    template = logic.Eq(add(z,sx),logic.F('succ',logic.V('hole')))
    equality_schema = logic.Imp(p,logic.Imp(e,ps))
    exchange = logic.Imp(equality_schema,logic.Imp(e,step))
    congruence = block('congruence-step',[e],step,[
        line('assumption',e,index=0),
        line('eq_subst',equality_schema,variable='hole',template=template,left=add(z,x),right=x),
        line('tautology',exchange),
        line('mp',logic.Imp(e,step),antecedent=1,implication=2),
        line('mp',step,antecedent=0,implication=3)])
    both = ('and',p0,universal); combine = logic.Imp(p0,logic.Imp(universal,both))
    induction = block('induction-step',[p0,universal],target,[
        line('assumption',p0,index=0),line('assumption',universal,index=1),
        line('tautology',combine),line('mp',logic.Imp(universal,both),antecedent=0,implication=2),
        line('mp',both,antecedent=1,implication=3),
        line('induction',induction_formula('x',p),variable='x',template=p),
        line('mp',target,antecedent=4,implication=5)])
    # A closed recursion axiom is an input: an open e premise would forbid
    # generalization over x. This interface preserves the eigenvariable rule.
    az = logic.All('x',logic.Eq(add(x,z),x))
    ar = logic.All('x',logic.All('y',logic.Eq(add(x,logic.F('succ',y)),logic.F('succ',add(x,y)))))
    ar_z = logic.substitute(ar[2],ar[1],z)
    response = block('left-zero-response',[p0,ar],target,[
        line('assumption',p0,index=0),line('assumption',ar,index=1),
        line('instantiate',logic.Imp(ar,ar_z),universal=ar,term=z),
        line('mp',ar_z,antecedent=1,implication=2),
        line('instantiate',logic.Imp(ar_z,e),universal=ar_z,term=x),
        line('mp',e,antecedent=3,implication=4),
        line('block',step,name='congruence-step',inputs=[5]),
        line('generalize',universal,variable='x',source=6),
        line('block',target,name='induction-step',inputs=[0,7])])
    proof = [line('axiom',az,name='add-zero'),line('instantiate',logic.Imp(az,p0),universal=az,term=z),
             line('mp',p0,antecedent=0,implication=1),line('axiom',ar,name='add-successor')]
    proof += [line('block',target,name='left-zero-response',inputs=[2,3]) for _ in range(repeats)]
    return request(dict(zero=0,succ=1,add=2),axioms={'add-zero':az,'add-successor':ar},
                   schemas=['nat-induction'],blocks=[congruence,induction,response],proof=proof,target=target)

def flatten_blocks(d):
    """Authored full-expansion control, preserving the same induction rule."""
    result=copy.deepcopy(d); registry={b['name']:b for b in d['blocks']}; out=[]
    def expand(lines,inputs):
        indices=[]
        for source in lines:
            item=dict(source); rule=item['rule']
            if rule=='assumption': indices.append(inputs[item['index']]); continue
            if rule=='block':
                called=registry[item['name']]
                indices.append(expand(called['proof'],tuple(indices[i] for i in item['inputs']))); continue
            if rule=='mp': item.update(antecedent=indices[item['antecedent']],implication=indices[item['implication']])
            if rule=='generalize': item['source']=indices[item['source']]
            out.append(item); indices.append(len(out)-1)
        return indices[-1]
    expand(d['proof'],()); result.update(blocks=[],proof=out); return result

def primitive_cases():
    a = ('pred','P',()); b = ('pred','Q',()); x=logic.V('x'); y=logic.V('y')
    cases=[]
    def add(name,proof,**kw): cases.append((name,request(proof=proof,target=proof[-1]['formula'],**kw)))
    add('closed-axiom',[line('axiom',a,name='p')],predicates={'P':0},axioms={'p':a})
    add('propositional-tautology',[line('tautology',logic.Imp(a,a))],predicates={'P':0})
    add('reflexivity',[line('refl',logic.Eq(x,x))])
    u=logic.All('x',logic.All('y',logic.Eq(x,y)))
    add('capture-avoiding-instantiation',[line('instantiate',logic.Imp(u,logic.substitute(u[2],'x',y)),universal=u,term=y)])
    d=logic.Imp(logic.All('x',logic.Imp(a,b)),logic.Imp(a,logic.All('x',b)))
    add('universal-distribution',[line('distribute',d,variable='x',antecedent=a,consequent=b)],predicates={'P':0,'Q':0})
    template=logic.All('y',logic.Eq(x,y)); s=logic.V('z'); t=y
    formula=logic.Imp(logic.Eq(s,t),logic.Imp(logic.substitute(template,'x',s),logic.substitute(template,'x',t)))
    add('equality-with-bound-variable',[line('eq_subst',formula,variable='x',template=template,left=s,right=t)])
    add('modus-ponens',[line('axiom',a,name='p'),line('tautology',logic.Imp(a,a)),line('mp',a,antecedent=0,implication=1)],predicates={'P':0},axioms={'p':a})
    add('generalization',[line('refl',logic.Eq(x,x)),line('generalize',logic.All('x',logic.Eq(x,x)),variable='x',source=0)])
    for depth in (1,4,16,64,96):
        term=logic.V('a name with spaces / \u03b1')
        for _ in range(depth): term=logic.F('f',term)
        add('term-depth-'+str(depth),[line('refl',logic.Eq(term,term))],functions={'f':1})
    for arity in (0,1,16,128):
        term=logic.F('wide',*(logic.V(str(i)) for i in range(arity)))
        add('input-arity-'+str(arity),[line('refl',logic.Eq(term,term))],functions={'wide':arity})
    for variable in ('','x','fresh0','\u03b1'):
        template=logic.All('fresh0',logic.Eq(logic.V(variable),logic.V('parameter')))
        formula=induction_formula(variable,template)
        add('induction-name-'+repr(variable),[line('induction',formula,variable=variable,template=template)],
            functions={'zero':0,'succ':1},schemas=['nat-induction'])
    old=logic.demo()
    add('old-ground-addition-certificate',old['proof'],functions={'zero':0,'succ':1,'add':2},
        axioms=logic.Kernel({'zero':0,'succ':1,'add':2},{},{'z':logic.All('x',logic.Eq(logic.F('add',x,logic.F('zero')),x)),
            's':logic.All('x',logic.All('y',logic.Eq(logic.F('add',x,logic.F('succ',y)),logic.F('succ',logic.F('add',x,y)))))}).axioms)
    # Keep exactly the old certificate's names; the formulas above are identical.
    cases[-1][1]['theory']['axioms']={'add_zero':cases[-1][1]['theory']['axioms']['z'],
                                    'add_successor':cases[-1][1]['theory']['axioms']['s']}
    return cases

def propositional_cases():
    terms={1:[('pred','P',()),('pred','Q',()),('bot',)]}
    for n in range(2,6):
        terms[n]=[logic.Not(a) for a in terms[n-1]]
        for left in range(1,n-1):
            terms[n].extend((op,a,b) for op in ('imp','and','or')
                           for a in terms[left] for b in terms[n-1-left])
    return [request(predicates={'P':0,'Q':0},proof=[line('tautology',a)],target=a)
            for n in terms for a in terms[n]]

def adversarial_cases():
    base=addition_induction(); cases=[]
    def add(name,mutate):
        d=copy.deepcopy(base); mutate(d); cases.append((name,d))
    add('missing-induction-authorization',lambda d:d['theory'].update(schemas=[]))
    add('unknown-schema',lambda d:d['theory'].update(schemas=['trust-me']))
    add('duplicate-schema',lambda d:d['theory'].update(schemas=['nat-induction']*2))
    add('schema-without-successor',lambda d:d['theory']['functions'].pop('succ'))
    add('boolean-arity',lambda d:d['theory']['functions'].update(zero=False))
    add('open-theory-axiom',lambda d:d['theory']['axioms'].update(untrusted=logic.Eq(logic.V('x'),logic.V('y'))))
    add('wrong-final-target',lambda d:d.update(target=('bot',)))
    add('root-assumption',lambda d:d['proof'].append(line('assumption',d['target'],index=0)))
    add('forward-proof-reference',lambda d:d['proof'][2].update(antecedent=2))
    add('boolean-proof-reference',lambda d:d['proof'][2].update(antecedent=False))
    add('negative-proof-reference',lambda d:d['proof'][2].update(antecedent=-1))
    add('wrong-block-input',lambda d:d['proof'][4].update(inputs=[3,2]))
    add('missing-block-input',lambda d:d['proof'][4].update(inputs=[2]))
    add('forward-block-reference',lambda d:d['blocks'].reverse())
    add('recursive-block-reference',lambda d:d['blocks'][0]['proof'].append(line('block',d['blocks'][0]['conclusion'],name='congruence-step',inputs=[0])))
    add('duplicate-block-name',lambda d:d['blocks'][1].update(name='congruence-step'))
    add('extra-payload-field',lambda d:d['proof'][0].update(executable='arbitrary code'))
    add('unrecognized-rule',lambda d:d['proof'][0].update(rule='oracle'))
    add('damaged-induction-formula',lambda d:d['blocks'][1]['proof'][5].update(formula=('bot',)))
    a=('pred','P',(logic.V('x'),)); univ=logic.All('x',a)
    illegal=block('bad',[a],univ,[line('assumption',a,index=0),line('generalize',univ,variable='x',source=0)])
    cases.append(('generalization-of-open-premise',request(predicates={'P':1},blocks=[illegal],proof=[line('tautology',logic.Imp(a,a))],target=logic.Imp(a,a))))
    u=logic.All('x',logic.All('y',logic.Eq(logic.V('x'),logic.V('y'))))
    captured=logic.Imp(u,logic.All('y',logic.Eq(logic.V('y'),logic.V('y'))))
    cases.append(('captured-instantiation',request(proof=[line('instantiate',captured,universal=u,term=logic.V('y'))],target=captured)))
    return cases
