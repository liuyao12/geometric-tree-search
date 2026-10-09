"""Port controls. These author inputs, and are never called by the tree VM."""
import copy
import logic
from serialized_examples import request,line,block,induction_formula,addition_induction,flatten_blocks

def extra_cases():
    rows=[]
    def add(name,proof,**kw):rows.append((name,request(proof=proof,target=proof[-1]['formula'],**kw)))
    # Force decimal freshness across 9 -> 10, with occupied bound and free names.
    body=logic.Eq(logic.V('x'),logic.V('y'))
    for i in range(12):body=('and',body,logic.Eq(logic.V('fresh'+str(i)),logic.V('fresh'+str(i))))
    u=logic.All('x',logic.All('y',body));t=logic.V('y')
    wanted=logic.Imp(u,logic.substitute(u[2],'x',t))
    add('capture-fresh12',[line('instantiate',wanted,universal=u,term=t)])
    shadow=logic.All('x',logic.All('x',logic.Eq(logic.V('x'),logic.V('x'))))
    add('shadowed-binder',[line('instantiate',logic.Imp(shadow,shadow[2]),universal=shadow,term=logic.V('y'))])
    names=('', 'a', '\u0000', '\u03b1', '\U0001f9a2', '\ud800', 'fresh0')
    template=logic.Eq(logic.V('x'),logic.V('x'))
    for n in names:template=('and',template,logic.Eq(logic.V(n),logic.V(n)))
    add('unicode-induction-order',[line('induction',induction_formula('x',template),variable='x',template=template)],
        functions={'zero':0,'succ':1},schemas=['nat-induction'])
    # A free antecedent prevents distribution even though the shape looks right.
    p=logic.Eq(logic.V('x'),logic.V('x'));q=('bot',)
    f=logic.Imp(logic.All('x',logic.Imp(p,q)),logic.Imp(p,logic.All('x',q)))
    add('free-distribution-antecedent',[line('distribute',f,variable='x',antecedent=p,consequent=q)])
    a=logic.Eq(logic.V('x'),logic.V('x'))
    add('unused-invalid-block',[line('refl',a)],blocks=[block('unused',[],a,[line('assumption',a,index=0)])])
    for count in (1,4,16):
        d=addition_induction(count);rows.append(('modular-induction-'+str(count),d));rows.append(('flat-induction-'+str(count),flatten_blocks(d)))
    base=request(proof=[line('refl',a)],target=a)
    edits=[('negative-signature',lambda d:d['theory']['functions'].update(f=-1)),
           ('boolean-term-name',lambda d:d['proof'][0].update(formula=['eq',['var',True],['var',True]])),
           ('unknown-term-tag',lambda d:d['proof'][0].update(formula=['eq',['mystery','x'],['mystery','x']])),
           ('nonarray-proof',lambda d:d.update(proof={})),
           ('empty-proof',lambda d:d.update(proof=[])),
           ('nonarray-blocks',lambda d:d.update(blocks={})),
           ('missing-rule-parameter',lambda d:d['proof'][0].update(rule='instantiate'))]
    for name,edit in edits:
        d=copy.deepcopy(base);edit(d);rows.append((name,d))
    return rows
