"""Native engine fixtures, not supplied mathematical proof certificates."""
import json
from pathlib import Path
from native_wang_search import pool,encoded
from shared_wang_inventory import input_tape

def guarded(width,height,blank=1,top=None):
    boundary=[]
    for y in range(height):boundary.extend([[[-1,2*y],[blank,blank]],[[2*width-1,2*y],[blank,blank]]])
    if top is not None:boundary.extend([[[2*x,2*height-1],v] for x,v in enumerate(top)])
    return boundary

def projection_certificate(spec,inventory):
    A=inventory.A;pattern=[pool(s) for s in spec['pattern']];positions=[];ordinary={}
    for x,s in enumerate(pattern):
        if s is None:raise ValueError('cone certificate requires a fixed one-head input schema')
        has_head=(s.stop>A and len(s)>0) if isinstance(s,range) else any(v>=A for v in s)
        has_ordinary=any(v in s for v in range(A))
        if has_head:
            if has_ordinary:raise ValueError('ambiguous head presence')
            positions.append(x)
        elif len(s)==1:ordinary[x]=s[0]
    if len(positions)!=1:raise ValueError('exactly one possible initial head position')
    h=positions[0];pins=[]
    for row in range(1,spec['height']+1):
        for x,v in ordinary.items():
            if abs(x-h)>=row:pins.append([[2*x,2*row-1,1],v])
    return dict(version='native-underlying-cone-001',head_position=h,pattern=spec['pattern'],height=spec['height'],pins=pins,
        law='A complete guarded single-head row has its successor head at distance at most one. At an ordinary input center, the output is its old symbol or a head carrying that same symbol. Thus cells outside the write cone retain their underlying input values. All pins concern projections of actual original symbol values; no proof path is supplied.')

def registry(inventory,docs):
    i=inventory;cases=[]
    for height,width in ((2,5),(3,7)):
        h=width//2;pattern=[[1] for _ in range(width)];pattern[h]={'range':[2*i.A,i.D]}
        top=[1]*width;top[h]=i.head(i.accept,9)
        cases.append(dict(id='inverse-accept-'+str(height),title='Unknown predecessor · '+str(height)+' native rows',pattern=pattern,height=height,boundary=guarded(width,height,top=top),accepting=True,
            scope='Find a native acceptance fragment with an unknown nonaccepting initial state. The fixed top is accepting; this is not a complete proof-checker run or a newly proved mathematical theorem.'))
    old=json.loads((Path(docs)/'proof-boundary-001.json').read_text());labels=json.loads((Path(docs)/'shared-wang-reader-001.json').read_text())['inventory']['alphabet']
    prefix=input_tape(old['cases'][0]['initial'],labels)[:13];pattern=[[1],[1],*[ [v] for v in prefix ],[1],[1]];pattern[2]=[i.head(i.start,prefix[0])]
    cases.append(dict(id='boot-prefix',title='Actual start-state boot prefix',pattern=pattern,height=4,boundary=guarded(len(pattern),4),accepting=False,
        scope='The first thirteen physical input cells of the fixed bootstrap, with blank guards outside the four-step head cone. No assertion or certificate payload is read; a complete local rectangle is a prefix, not a proof.'))
    top=[s[0] for s in pattern];top[2]=prefix[0];top[3]=i.head(i.accept,9)
    cases.append(dict(id='premature-accept',title='Accepting top too soon',pattern=pattern,height=2,boundary=guarded(len(pattern),2,top=top),accepting=True,
        scope='A specific two-row accepting boundary over the actual boot prefix. Exhaustion is about this finite boundary, not unprovability of an assertion.'))
    pattern=[[1],[1],[i.head(i.reject,1)],[1],[1]]
    cases.append(dict(id='undefined-center',title='Undefined center · global dead-end control',pattern=pattern,height=1,boundary=guarded(5,1),accepting=False,
        scope='The reject state has no center continuation. The global dead end must outrank the other forced cells.'))
    cases.append(dict(cases[0],id='zero-budget',title='Zero placement budget · unknown control',attempts=0))
    return cases
