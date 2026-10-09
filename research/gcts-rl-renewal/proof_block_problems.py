"""Theory and statement families only. No proof or block witnesses."""
import random
import logic

def theory():
    x,y=logic.V('x'),logic.V('y');z=logic.F('zero');add=lambda a,b:logic.F('add',a,b)
    return dict(functions=dict(zero=0,succ=1,add=2,wrap=1),predicates={},schemas=['nat-induction'],
        axioms={'addition-zero':logic.All('x',logic.Eq(add(x,z),x)),
                'addition-successor':logic.All('x',logic.All('y',logic.Eq(add(x,logic.F('succ',y)),logic.F('succ',add(x,y)))))})
def numeral(n):
    t=logic.F('zero')
    for _ in range(n):t=logic.F('succ',t)
    return t
def successors(t,n):
    for _ in range(n):t=logic.F('succ',t)
    return t
def close(eq,names):
    for x in reversed(names):eq=logic.All(x,eq)
    return eq
def associate(terms,right):
    if len(terms)==1:return terms[0]
    return logic.F('add',terms[0],associate(terms[1:],right)) if right else logic.F('add',associate(terms[:-1],right),terms[-1])
def discovery():
    x=logic.V('a');add=lambda a,b:logic.F('add',a,b)
    out=[dict(id='unit-'+str(k),target=close(logic.Eq(add(x,numeral(k)),successors(x,k)),('a',))) for k in (1,2,3)]
    out.append(dict(id='left-zero',target=close(logic.Eq(add(numeral(0),x),x),('a',))))
    for n in (3,4):
        names=tuple('a'+str(i) for i in range(n));terms=tuple(map(logic.V,names))
        out.append(dict(id='bracketing-'+str(n),target=close(logic.Eq(associate(terms,False),associate(terms,True)),names)))
    return out

def family(seed,count,held_out=False):
    rng=random.Random(seed);out=[]
    for i in range(count):
        names=tuple(('held' if held_out else 'train')+str(i)+'v'+str(j) for j in range(2+(i%3)))
        terms=list(map(logic.V,names));a,b=terms[:2];n=4+(i%4) if held_out else 1+(i%3)
        kind=i%3
        if kind==0:
            inner=logic.F('add',a,successors(b,i%4));left=logic.F('add',numeral(0),inner);right=inner
        elif kind==1:
            left=logic.F('add',a,numeral(n));right=successors(a,n)
        else:
            length=(5+i%3) if held_out else (3+i%2)
            leaves=[terms[j%len(terms)] for j in range(length)]
            left,right=associate(leaves,False),associate(leaves,True)
        depth=(2+i%3) if held_out else (i%2)
        for j in range(depth):
            if rng.randrange(2):left,right=logic.F('wrap',left),logic.F('wrap',right)
            else:left,right=logic.F('add',b,left),logic.F('add',b,right)
        out.append(dict(id=('evaluation-' if held_out else 'training-')+str(i),target=close(logic.Eq(left,right),names),kind=('zero','unit','bracketing')[kind],context_depth=depth))
    return out
