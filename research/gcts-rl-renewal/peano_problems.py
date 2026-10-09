"""Explicit first-order Peano axioms and theorem statements, without witnesses."""
import logic

def Z():return logic.F('zero')
def S(a):return logic.F('succ',a)
def A(a,b):return logic.F('add',a,b)
def M(a,b):return logic.F('mul',a,b)
def close(a,names):
    for name in reversed(names):a=logic.All(name,a)
    return a
def theory():
    x,y=logic.V('x'),logic.V('y')
    return dict(functions=dict(zero=0,succ=1,add=2,mul=2),predicates={},schemas=['nat-induction'],axioms={
        'successor-nonzero':close(logic.Not(logic.Eq(S(x),Z())),('x',)),
        'successor-injective':close(logic.Imp(logic.Eq(S(x),S(y)),logic.Eq(x,y)),('x','y')),
        'addition-zero':close(logic.Eq(A(x,Z()),x),('x',)),
        'addition-successor':close(logic.Eq(A(x,S(y)),S(A(x,y))),('x','y')),
        'multiplication-zero':close(logic.Eq(M(x,Z()),Z()),('x',)),
        'multiplication-successor':close(logic.Eq(M(x,S(y)),A(M(x,y),x)),('x','y'))})
def statements():
    a,b,c=map(logic.V,('a','b','c'))
    return [
        dict(id='add-one',title='Adding one is successor',target=close(logic.Eq(A(a,S(Z())),S(a)),('a',))),
        dict(id='add-left-zero',title='Zero on the left',target=close(logic.Eq(A(Z(),a),a),('a',))),
        dict(id='add-left-successor',title='Successor on the left',target=close(logic.Eq(A(S(a),b),S(A(a,b))),('a','b'))),
        dict(id='add-commutative',title='Addition is commutative',target=close(logic.Eq(A(a,b),A(b,a)),('a','b'))),
        dict(id='add-associative',title='Addition is associative',target=close(logic.Eq(A(A(a,b),c),A(a,A(b,c))),('a','b','c'))),
        dict(id='mul-left-zero',title='Zero times a number',target=close(logic.Eq(M(Z(),a),Z()),('a',))),
        dict(id='mul-right-one',title='Multiplying by one on the right',target=close(logic.Eq(M(a,S(Z())),a),('a',))),
        dict(id='mul-left-one',title='Multiplying by one on the left',target=close(logic.Eq(M(S(Z()),a),a),('a',))),
        dict(id='mul-distributes',title='Multiplication distributes over addition',target=close(logic.Eq(M(a,A(b,c)),A(M(a,b),M(a,c))),('a','b','c'))),
        dict(id='mul-left-successor',title='Successor in the first factor',target=close(logic.Eq(M(S(a),b),A(M(a,b),b)),('a','b'))),
        dict(id='mul-commutative',title='Multiplication is commutative',target=close(logic.Eq(M(a,b),M(b,a)),('a','b'))),
        dict(id='mul-associative',title='Multiplication is associative',target=close(logic.Eq(M(M(a,b),c),M(a,M(b,c))),('a','b','c')))]
