"""Separate authored policy-training and evaluation statements, no proof paths."""
import logic as L
from proof_cluster_problems import numeral as N,plus as A,succ as S,problem,donors,evaluation
from semantic_proof_problems import addition

def multiplication():
    theory=addition();theory['functions']['mul']=2;x,y=L.V('x'),L.V('y');m=lambda a,b:L.F('mul',a,b);z=N(0)
    theory['axioms'].update(MZ=L.All('x',L.Eq(m(x,z),z)),MS=L.All('x',L.All('y',L.Eq(m(x,S(y)),A(m(x,y),x)))));return theory

def training():
    out=[]
    for a,b in ((0,1),(2,1),(1,2)):
        out.append(problem(f'train-add-{a}-{b}',f'Training addition {a} and {b}',L.Eq(A(N(a),N(b)),N(a+b)),b+2,a+b+3))
    out += [problem('train-successor','Training addition in a successor',L.Eq(S(A(N(0),N(1))),N(2)),3,5),
        problem('train-inner-right','Training nested second input',L.Eq(A(N(0),A(N(0),N(1))),N(1)),5,6),
        problem('train-inner-left','Training nested first input',L.Eq(A(A(N(0),N(1)),N(0)),N(1)),4,6),
        problem('train-mul-successor','Training multiplication in a successor',L.Eq(S(L.F('mul',N(1),N(1))),N(2)),5,8,multiplication()),
        problem('train-mul-zero','Training multiplication by zero',L.Eq(L.F('mul',N(2),N(0)),N(0)),3,6,multiplication())]
    return out
