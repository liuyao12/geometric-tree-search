"""External arithmetic statements and finite bounds, with no proof witnesses."""
import copy
import logic as L
from semantic_proof_problems import addition

def problems():
    z=L.F('zero');n,a,b=map(L.V,('n','a','b'))
    s=lambda t:L.F('succ',t);add=lambda p,q:L.F('add',p,q);mul=lambda p,q:L.F('mul',p,q)
    theory=addition();theory['schemas']=['nat-induction']
    multiplication=copy.deepcopy(theory);multiplication['functions']['mul']=2
    x,y=L.V('x'),L.V('y')
    multiplication['axioms'].update(MZ=L.All('x',L.Eq(mul(x,z),z)),MS=L.All('x',L.All('y',L.Eq(mul(x,s(y)),add(mul(x,y),x)))))
    def row(id,label,t,target,length,bound,enabled=True):
        return dict(id=id,label=label,theory=copy.deepcopy(t),target=target,length=length,term_bound=bound,enable_induction=enabled)
    leftzero=L.All('n',L.Eq(add(z,n),n))
    no_schema=copy.deepcopy(theory);no_schema['schemas']=[]
    return [row('ind-add-left-zero','Zero on the left of addition',theory,leftzero,7,4),
            row('ind-add-left-one','One on the left of addition',theory,L.All('n',L.Eq(add(s(z),n),s(n))),7,5),
            row('ind-mul-left-zero','Zero on the left of multiplication',multiplication,L.All('n',L.Eq(mul(z,n),z)),8,5),
            row('ind-add-left-successor','Successor in the first input',theory,L.All('a',L.All('b',L.Eq(add(s(a),b),s(add(a,b))))),11,5),
            row('ind-no-schema','Same statement without induction authorization',no_schema,leftzero,7,4),
            row('ind-too-short','Same statement with one fewer proof cell',theory,leftzero,6,4),
            row('ind-wrong-target','Shifted target control',theory,L.All('n',L.Eq(add(z,n),s(n))),7,4)]
