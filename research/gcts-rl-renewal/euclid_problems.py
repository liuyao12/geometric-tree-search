"""A guarded Euclid-style construction/congruence fragment, not all of Euclid.

Point guards allow points and metric values to inhabit a tagged, one-sorted
FOL domain. Circle intersection and SAS are explicit assumptions, not proofs.
No coordinate values, theorem witnesses or diagram pixels enter the search.
"""
import logic as L

def P(p):return ('pred','Point',(p,))
def T(a,b,c):return ('pred','Triangle',(a,b,c))
def Seg(a,b):return ('pred','Segment',(a,b))
def N(a,b,c):return ('pred','Noncollinear',(a,b,c))
def B(a,d,b):return ('pred','Between',(a,d,b))
def On(p,c):return ('pred','On',(p,c))
def circle(a,b):return L.F('circle',a,b)
def meet(a,b):return L.F('meet',a,b)
def seg(a,b):return L.F('length',a,b)
def angle(a,b,c):return L.F('angle',a,b,c)
def AND(*items):
    out=items[-1]
    for a in reversed(items[:-1]):out=('and',a,out)
    return out
def close(a,names):
    for x in reversed(names):a=L.All(x,a)
    return a
def clause(names,premises,conclusion):
    for p in reversed(premises):conclusion=L.Imp(p,conclusion)
    return close(conclusion,names)
def theory():
    a,b,c,d,e,f,p=map(L.V,('a','b','c','d','e','f','p'));C=meet(a,b)
    distinct=[P(a),P(b),L.Not(L.Eq(a,b))]
    axioms={
        'length-symmetry':clause(('a','b'),[P(a),P(b)],L.Eq(seg(a,b),seg(b,a))),
        'angle-reversal':clause(('a','b','c'),[P(a),P(b),P(c)],L.Eq(angle(a,b,c),angle(c,b,a))),
        'noncollinear-swap':clause(('a','b','c'),[N(a,b,c)],N(a,c,b)),
        'circle-radius':clause(('a','b','p'),[On(p,circle(a,b)),P(a),P(b),P(p)],L.Eq(seg(a,p),seg(a,b))),
        'intersection-point':clause(('a','b'),distinct,P(C)),
        'intersection-first-circle':clause(('a','b'),distinct,On(C,circle(a,b))),
        'intersection-second-circle':clause(('a','b'),distinct,On(C,circle(b,a))),
        'intersection-noncollinear':clause(('a','b'),distinct,N(a,b,C))}
    # Named diagram interfaces are conservative abbreviations for guards.
    # Both directions are declared so their meaning is not left to a picture.
    for i,q in enumerate((P(a),P(b),L.Not(L.Eq(a,b)))):
        axioms['segment-guard-'+str(i)]=clause(('a','b'),[Seg(a,b)],q)
    axioms['segment-introduction']=clause(('a','b'),distinct,Seg(a,b))
    for i,q in enumerate((P(a),P(b),P(c),N(a,b,c))):
        axioms['triangle-guard-'+str(i)]=clause(('a','b','c'),[T(a,b,c)],q)
    axioms['triangle-introduction']=clause(('a','b','c'),[P(a),P(b),P(c),N(a,b,c)],T(a,b,c))
    # Triangle is the defined guard interface above. This is the same guarded
    # SAS condition expressed through two diagram constituents, not eleven
    # repeated primitive premises. It changes the theory's representation.
    sas=[L.Eq(seg(a,b),seg(d,e)),L.Eq(seg(a,c),seg(d,f)),L.Eq(angle(b,a,c),angle(e,d,f)),T(a,b,c),T(d,e,f)]
    axioms['SAS-opposite-side']=clause(('a','b','c','d','e','f'),sas,L.Eq(seg(b,c),seg(e,f)))
    axioms['SAS-first-base-angle']=clause(('a','b','c','d','e','f'),sas,L.Eq(angle(a,b,c),angle(d,e,f)))
    axioms['SAS-second-base-angle']=clause(('a','b','c','d','e','f'),sas,L.Eq(angle(a,c,b),angle(d,f,e)))
    return dict(functions=dict(circle=2,meet=2,length=2,angle=3),predicates=dict(Point=1,Noncollinear=3,Between=3,On=2,Triangle=3,Segment=2),schemas=[],axioms=axioms)
def statements():
    a,b,c,d=map(L.V,('a','b','c','d'));C=meet(a,b)
    equi=AND(T(a,b,C),L.Eq(seg(a,C),seg(a,b)),L.Eq(seg(b,C),seg(a,b)))
    guards=Seg(a,b)
    iso=AND(T(a,b,c),L.Eq(seg(a,b),seg(a,c)))
    base=L.Eq(angle(a,b,c),angle(a,c,b))
    bisector=AND(T(c,a,d),T(c,b,d),B(a,d,b),L.Eq(seg(c,a),seg(c,b)),L.Eq(angle(a,c,d),angle(b,c,d)))
    return [
        dict(id='euclid-I1',title='I.1: construct an equilateral triangle',target=close(L.Imp(guards,equi),('a','b')),scope='Construction witness is meet(a,b); equal-radius circle intersection, including noncollinearity, is explicitly assumed.'),
        dict(id='euclid-I5',title='I.5: equal base angles',target=close(L.Imp(iso,base),('a','b','c')),scope='Main base-angle conclusion only; SAS is an explicit congruence axiom. Exterior-angle clause is not proved.'),
        dict(id='equilateral-base-angles',title='The constructed triangle has equal base angles',target=close(L.Imp(guards,L.Eq(angle(a,b,C),angle(a,C,b))),('a','b')),scope='A fresh proof composes the searched I.1 and I.5 blocks.'),
        dict(id='euclid-I10-verification',title='I.10: verify the midpoint step',target=close(L.Imp(bisector,AND(B(a,d,b),L.Eq(seg(a,d),seg(b,d)))),('a','b','c','d')),scope='Conditional verification with betweenness and an angle bisector supplied. The bisector construction I.9 and existence of d remain open.')]
