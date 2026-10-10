"""Independent syntax, inference, expansion, and point-certificate checker.

Does not import the producer, point graph, or learned policy. Concrete rule
expansions are checked, including unused lines. Hashes never establish equality.
"""
import collections, itertools, time

def frozen(a):
    if isinstance(a,dict):return {k:frozen(v) for k,v in a.items()}
    return tuple(frozen(x) for x in a) if isinstance(a,(list,tuple)) else a
def need(ok,message):
    if not ok:raise ValueError(message)
def formula(a):
    need(isinstance(a,tuple),'immutable formula required')
    if a in (('P',),('Q',)):return
    need(len(a) in (2,3),'formula arity')
    if a[0]=='not' and len(a)==2:formula(a[1]);return
    if a[0]=='imp' and len(a)==3:formula(a[1]);formula(a[2]);return
    raise ValueError('unknown formula constructor')
def word(a):
    formula(a)
    if len(a)==1:return a[0]
    return ('n'+word(a[1])) if len(a)==2 else ('i'+word(a[1])+word(a[2]))
def decode_word(s):
    def read(j):
        need(j<len(s),'truncated formula')
        if s[j] in 'PQ':return (s[j],),j+1
        if s[j]=='n':a,k=read(j+1);return ('not',a),k
        need(s[j]=='i','unknown prefix token');a,k=read(j+1);b,k=read(k);return ('imp',a,b),k
    a,j=read(0);need(s[j:]=='e','complete unique terminator');return a
def is_schema(kind,a):
    try:
        if kind=='H1':return a[0]=='imp' and a[2][0]=='imp' and a[1]==a[2][2]
        if kind=='H2':
            x,y=a[1],a[2];aa,bb,cc=x[1],x[2][1],x[2][2]
            return a==('imp',('imp',aa,('imp',bb,cc)),('imp',('imp',aa,bb),('imp',aa,cc)))
        if kind=='H3':
            aa,bb=a[2][1:]
            return a==('imp',('imp',('not',bb),('not',aa)),('imp',aa,bb))
    except (ValueError,TypeError,IndexError):return False
    return False

def logical(proof,target,hypotheses=(),allow_lemmas=True):
    proof=frozen(proof);target=frozen(target);hypotheses=frozen(hypotheses)
    formula(target)
    for a in hypotheses:formula(a)
    values={j:a for j,a in enumerate(hypotheses,-len(hypotheses))};expanded=[];outer_to_inner={j:j for j in values}
    for j,line in enumerate(proof):
        a=line['formula'];formula(a);refs=line['refs'];kind=line['kind']
        need(all(type(i) is int and i in values and i<j for i in refs),'references must be earlier and in this scope')
        if kind in ('H1','H2','H3'):
            need(not refs and is_schema(kind,a),'invalid axiom schema');expanded.append(dict(kind=kind,formula=a,refs=()))
        elif kind=='mp':
            need(len(refs)==2 and values[refs[1]]==('imp',values[refs[0]],a),'invalid modus ponens')
            expanded.append(dict(kind=kind,formula=a,refs=tuple(outer_to_inner[i] for i in refs)))
        elif kind=='lemma':
            need(allow_lemmas and not refs and line['name']=='identity','unavailable lemma family')
            parameter=line['parameter'];formula(parameter)
            need(a==('imp',parameter,parameter),'family parameter/output binding')
            inner=logical(line['expansion'],a,(),False)['expanded'];offset=len(expanded)
            for r in inner:expanded.append(dict(r,refs=tuple(i+offset for i in r['refs'])))
        else:raise ValueError('unknown inference')
        outer_to_inner[j]=len(expanded)-1;values[j]=a
    need(proof and proof[-1]['formula']==target,'final conclusion')
    # Recheck the flattened proof to prevent expansion-index and scope leakage.
    if allow_lemmas:logical(expanded,target,hypotheses,False)
    return dict(status='accepted',commands=len(proof),primitive_lines=len(expanded),expanded=expanded)

def independent_basis():
    p,q=('P',),('Q',);pool=[p,q,('imp',p,p),('imp',p,q),('imp',q,p),('imp',q,q)];axioms=[]
    for a,b in itertools.product(pool,repeat=2):axioms.append(('H1',('imp',a,('imp',b,a))))
    for a,b,c in itertools.product(pool,repeat=3):
        axioms.append(('H2',('imp',('imp',a,('imp',b,c)),('imp',('imp',a,b),('imp',a,c)))))
    for a,b in itertools.product(pool,repeat=2):axioms.append(('H3',('imp',('imp',('not',b),('not',a)),('imp',a,b))))
    universe=set()
    def sub(a):
        universe.add(a)
        for v in a[1:]:sub(v)
    for _,a in axioms:sub(a)
    rules=[dict(kind=k,inputs=(),output=a) for k,a in axioms]
    for a in sorted(universe,key=word):
        if a[0]=='imp':rules.append(dict(kind='mp',inputs=(a[1],a),output=a[2]))
    return pool,rules

def inventory(catalog,library):
    pool,expected=independent_basis()
    for f in library:
        need(f['parameter']==('P',) and f['conclusion']==('imp',('P',),('P',)),'registered family interface')
        logical(f['proof'],f['conclusion'],(),False)
        def subst(a,v):
            if a==('P',):return v
            return (a[0],)+tuple(subst(x,v) for x in a[1:])
        for a in pool:
            expansion=[dict(r,formula=subst(r['formula'],a)) for r in f['proof']]
            expected.append(dict(kind='lemma',name=f['name'],parameter=a,inputs=(),
                output=subst(f['conclusion'],a),expansion=expansion))
    need(frozen(catalog['rules'])==frozen(expected),'complete fixed schema/rule inventory')
    return expected

def points(proof,target,hypotheses=()):
    proof=frozen(proof);hypotheses=frozen(hypotheses);target=frozen(target)
    marks={};totals={};assignments=0
    def put(p,v):
        nonlocal assignments
        assignments+=1;need(p not in marks or marks[p]==v,'conflicting marking');marks[p]=v
    def port(j,a):
        for k,v in enumerate(word(a)+'e'):put((2*j,2+k),v)
        put((2*j,1),0)
    port(len(proof)-1,target)
    for j,a in enumerate(hypotheses,-len(hypotheses)):port(j,a)
    for j,r in enumerate(proof):
        totals[(2*j,0)]=12;port(j,r['formula'])
        for ref in r['refs']:port(ref,(hypotheses[ref+len(hypotheses)] if ref<0 else proof[ref]['formula']))
    return dict(marks=marks,totals=totals,assignments=assignments)

def sparse(initial_marks,tiles,length):
    """Agreement/coverage only; inventory binding is checked separately."""
    marks={};totals=collections.Counter();assignments=0
    for entries in [initial_marks]+[t['marks'] for t in tiles]:
        for p,v in entries:
            assignments+=1;need(p not in marks or marks[p]==v,'mark disagreement');marks[p]=v
    for t in tiles:
        for p,v in t['occupancy']:totals[p]+=v;need(totals[p]<=12,'overfilled point')
    need(set(totals)=={(2*j,0) for j in range(length)} and all(v==12 for v in totals.values()),'whole exact target')
    return dict(assignments=assignments,distinct_mark_points=len(marks))

def certificate(catalog,target,length,hypotheses,placements,point_tiles,library=()):
    catalog=frozen(catalog);target=frozen(target);hypotheses=frozen(hypotheses);placements=frozen(placements);point_tiles=frozen(point_tiles);library=frozen(library)
    rules=inventory(catalog,library);need(len(placements)==length==len(point_tiles),'whole target coverage')
    need(len(set(placements))==length,'unique placements');need({k[0] for k in placements}==set(range(length)),'every proof slot')
    by_slot={};marks={};totals=collections.Counter();assignments=0
    def add(entries):
        nonlocal assignments
        local={}
        for p,v in entries:
            need(type(v) is int and v==0 or type(v) is str and v in ('P','Q','i','n','e'),'finite palette')
            need(p not in local or local[p]==v,'mark is single valued');local[p]=v
            need(p not in marks or marks[p]==v,'global point agreement');marks[p]=v;assignments+=1
    def port(j,a):return [((2*j,2+k),v) for k,v in enumerate(word(a)+'e')]+[((2*j,1),0)]
    add(port(length-1,target))
    for j,a in enumerate(hypotheses,-len(hypotheses)):add(port(j,a))
    for key,tile in zip(placements,point_tiles):
        slot,rid,refs=key;need(type(slot) is int and type(rid) is int and 0<=rid<len(rules),'inventory identity')
        r=rules[rid];need(len(refs)==len(r['inputs']) and all(type(j) is int and -len(hypotheses)<=j<slot for j in refs),'allowed backward references')
        need(tile['key']==key and tile['occupancy']==(((2*slot,0),12),),'occupancy/type binding')
        expected=dict(port(slot,r['output']))
        for j,a in zip(refs,r['inputs']):
            for p,v in port(j,a):need(p not in expected or expected[p]==v,'single-valued inference marks');expected[p]=v
        need(tile['marks']==tuple(sorted(expected.items())),'all remote marking assignments bound')
        add(tile['marks']);totals[(2*slot,0)]+=12
        row=dict(kind=r['kind'],formula=r['output'],refs=refs)
        if r['kind']=='lemma':row.update(name=r['name'],parameter=r['parameter'],expansion=r['expansion'])
        by_slot[slot]=row
    need(all(totals[(2*j,0)]==12 for j in range(length)),'exact point capacities')
    proof=[by_slot[j] for j in range(length)];checked=logical(proof,target,hypotheses)
    for j in range(-len(hypotheses),length):
        letters='';k=0
        while (2*j,2+k) in marks:
            letters+=marks[(2*j,2+k)];k+=1
            if letters[-1]=='e':break
        a=decode_word(letters);need(a==(hypotheses[j+len(hypotheses)] if j<0 else proof[j]['formula']),'actual marking string decodes to displayed formula')
    return dict(status='accepted',commands=length,primitive_lines=checked['primitive_lines'],assignments=assignments,
                distinct_mark_points=len(marks),scope='independent full point-data and primitive logical expansion replay')
