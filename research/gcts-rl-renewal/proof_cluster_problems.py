"""Authored donor nominations and held-out arithmetic/context statements.

No proof sequence or cluster is supplied. All donor mining happens before
evaluation. Exact finite base grammar/cell bounds agree across the three lanes.
"""
import logic as L
from semantic_proof_problems import addition

def numeral(n):return L.F('zero') if n==0 else L.F('succ',numeral(n-1))
def plus(a,b):return L.F('add',a,b)
def succ(a):return L.F('succ',a)
def problem(id,label,target,length,bound,theory=None):return dict(id=id,label=label,theory=theory or addition(),target=target,length=length,term_bound=bound)
def donors():
    a=L.V('a');out=[]
    for n in (1,2):
        right=a
        for _ in range(n):right=succ(right)
        out.append(problem(f'donor-{n}',f'Parameterized addition by {n}',L.All('a',L.Eq(plus(a,numeral(n)),right)),n+2,n+4))
    return out
def evaluation():
    z,one,two,three=numeral(0),numeral(1),numeral(2),numeral(3);out=[]
    for a,b in ((1,1),(2,2),(0,3),(2,3)):
        out.append(problem(f'add-{a}-{b}',f'Numeral addition {a} and {b}',L.Eq(plus(numeral(a),numeral(b)),numeral(a+b)),b+2,a+b+3))
    out.extend([problem('successor-context','Addition inside a successor',L.Eq(succ(plus(one,two)),numeral(4)),4,7),
                problem('nested-left','Nested addition in the first input',L.Eq(plus(plus(one,one),one),three),5,8),
                problem('nested-right','Nested addition in the second input',L.Eq(plus(one,plus(one,one)),three),6,8),
                problem('short-envelope','Too few cells for the expanded proof',L.Eq(plus(z,two),two),3,5),
                problem('different-target','Different target control',L.Eq(plus(z,one),two),3,4)])
    theory=addition();theory['functions']['mul']=2;x,y=L.V('x'),L.V('y');m=lambda a,b:L.F('mul',a,b)
    theory['axioms'].update(MZ=L.All('x',L.Eq(m(x,z),z)),MS=L.All('x',L.All('y',L.Eq(m(x,succ(y)),plus(m(x,y),x)))))
    out.append(problem('mul-one','Multiplication of one by one',L.Eq(m(one,one),one),5,7,theory));return out
