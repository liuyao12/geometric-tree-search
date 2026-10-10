"""Independent native family abstraction, matching and policy arithmetic.

No producer family, graph, matcher or policy implementation is imported.
Original membership and receptor legality use the auditor's literal table.
"""
import hashlib,math,random
from collections import Counter
from check_native_wang import normalize,need
from serialized_kernel import canonical
SHAPES=((2,1),(1,2),(3,1),(1,3),(2,2),(3,2),(2,3));FEATURES=('family','cells','level','known_receptors','head_fraction','accept_fraction','progress','defer');FIXED=(1.,2.,.5,1.,.5,1.,0.,-2.)
def schema(tiles,A):
    symbols={};states={};default={}
    def expression(v):
        if v<A:
            if v not in symbols:symbols[v]='s'+str(len(symbols));default[symbols[v]]=v
            return ['s',symbols[v]]
        q,s=divmod(v-A,A)
        if q not in states:states[q]='q'+str(len(states));default[states[q]]=q
        symbol=expression(s)[1];return ['h',states[q],symbol]
    x0=min(t['x'] for t in tiles);y0=min(t['y'] for t in tiles);pattern=[]
    for t in sorted(tiles,key=lambda t:(t['y'],t['x'])):pattern.append(dict(x=t['x']-x0,y=t['y']-y0,triple=[expression(v) for v in t['triple']],north=expression(t['N'])))
    return pattern,default
def mine(rows):
    templates={};frequencies=Counter();sources={};A=60
    for index,row in enumerate(rows):
        r=row['result']
        if r['status']!='finite_exact_native_rectangle':continue
        cells={(t['x'],t['y']):t for t in r['tiles']}
        for w,h in SHAPES:
            for y in range(r['height']-h+1):
                for x in range(r['width']-w+1):
                    leaves=[cells[x+dx,y+dy] for dy in range(h) for dx in range(w)];pattern,default=schema(leaves,A);name='native-family-'+hashlib.sha256(canonical(pattern)).hexdigest()[:24]
                    templates.setdefault(name,dict(name=name,width=w,height=h,pattern=pattern,defaults=default,source=dict(donor=index,origin=[x,y],tiles=leaves)));frequencies[name]+=1;sources.setdefault(name,set()).add(index)
    selected=[]
    for w,h in SHAPES:
        pool=[n for n,t in templates.items() if (t['width'],t['height'])==(w,h)];pool.sort(key=lambda n:(-len(sources[n]),-frequencies[n],n));selected+=pool[:3]
    def tree(indices):
        if len(indices)==1:return dict(leaf=indices[0],level=0)
        n=len(indices)//2;children=[tree(indices[:n]),tree(indices[n:])];return dict(children=children,level=1+max(c['level'] for c in children))
    result=[]
    for name in selected:
        t=templates[name];h=tree(list(range(len(t['pattern']))));result.append(dict(t,occurrences=frequencies[name],donors=sorted(sources[name]),hierarchy=h,level=h['level']))
    return result,dict(distinct=len(templates),windows=sum(frequencies.values()),offered=len(result),per_shape=3,shapes=SHAPES)
def ports(row,origin):
    x,y=2*(row['x']+origin[0]),2*(row['y']+origin[1]);a,b,c=row['triple'];n=row['north']
    result=[((x,y-1),b),((x,y+1),n),((x-1,y),[a,b]),((x+1,y),[b,c])]
    for px,py,e in ((x-2,y-1,a),(x,y-1,b),(x+2,y-1,c),(x,y+1,n)):result.append(((px,py,1),['s',e[-1]]))
    return result
def unify(e,v,binding,ref):
    if type(v) is not int or not 0<=v<ref.D:return False
    if e[0]=='s':values={e[1]:v} if v<ref.A else None
    elif v>=ref.A:q,s=divmod(v-ref.A,ref.A);values={e[1]:q,e[2]:s}
    else:values=None
    if values is None or any(k in binding and binding[k]!=a for k,a in values.items()):return False
    binding.update(values);return True
def evaluate(e,b,ref):return b[e[1]] if e[0]=='s' else ref.A+ref.A*b[e[1]]+b[e[2]]
def assignments(pos,key,n,ref):
    x,y=2*pos[0],2*pos[1];a,b,c=key;result={(x,y-1):b,(x,y+1):n,(x-1,y):(a,b),(x+1,y):(b,c)}
    for px,py,v in ((x-2,y-1,a),(x,y-1,b),(x+2,y-1,c),(x,y+1,n)):result[px,py,1]=v if v<ref.A else (v-ref.A)%ref.A
    return result
def legal(replay,pos,key,marks):
    try:n=replay.ref.successor(key)
    except ValueError:return False
    x,y=pos
    if y==0:
        for p,v in zip((x-1,x,x+1),key):
            if 0<=p<replay.width:
                s=normalize(replay.spec['pattern'][p])
                if s is not None and v not in s:return False
    return all(p not in marks or marks[p]==v for p,v in assignments(pos,key,n,replay.ref).items())
def instantiate(replay,t,origin,marks):
    binding={};known=total=0;ref=replay.ref
    for row in t['pattern']:
        x,y=row['x']+origin[0],row['y']+origin[1]
        if not 0<=x<replay.width or not 0<=y<replay.height:return None
        if (x,y) in replay.values and not all(unify(e,v,binding,ref) for e,v in zip(row['triple'],replay.values[x,y])):return None
        for p,e in ports(row,origin):
            total+=1
            if p not in marks:continue
            known+=1;v=marks[p]
            if len(p)==2 and p[0]%2:
                if not isinstance(v,tuple) or len(v)!=2 or not all(unify(a,b,binding,ref) for a,b in zip(e,v)):return None
            elif not unify(e,v,binding,ref):return None
        if y==0:
            for p,e in zip((x-1,x,x+1),row['triple']):
                if 0<=p<replay.width:
                    value=normalize(replay.spec['pattern'][p])
                    if value is not None and len(value)==1 and not unify(e,value[0],binding,ref):return None
    resolved=dict(t['defaults'],**binding);members=[];pending=[];aggregate={}
    for row in t['pattern']:
        p=row['x']+origin[0],row['y']+origin[1];key=tuple(evaluate(e,resolved,ref) for e in row['triple'])
        try:n=ref.successor(key)
        except ValueError:return None
        if n!=evaluate(row['north'],resolved,ref):return None
        if p in replay.values:
            if replay.values[p]!=key:return None
        elif not legal(replay,p,key,marks):return None
        else:pending.append([list(p),list(key)])
        members.append([list(p),list(key)])
        for q,v in assignments(p,key,n,ref).items():
            if (q in aggregate and aggregate[q]!=v) or (q in marks and marks[q]!=v):return None
            aggregate[q]=v
    if len(pending)<2:return None
    return dict(template=t['name'],level=t['level'],origin=list(origin),binding=resolved,bound_receptors=binding,members=members,pending=pending,marks=[[list(q),list(v) if isinstance(v,tuple) else v] for q,v in sorted(aggregate.items())],known_fraction=known/max(1,total))
def proposals(replay,library,point,limit):
    marks=replay.markings();found={};scanned=0
    for t in library:
        for a in t['pattern']:
            scanned+=1;r=instantiate(replay,t,(point[0]-a['x'],point[1]-a['y']),marks)
            if r is not None:found.setdefault(tuple((tuple(p),tuple(v)) for p,v in r['members']),r)
    pool=sorted(found.values(),key=lambda r:(-len(r['pending']),-r['known_fraction'],-r['level'],r['template'],r['origin']))[:limit];return pool,dict(scanned=scanned,matched=len(found),offered=len(pool))
def review(replay,hint,kind,point):
    pending=[];marks=replay.markings()
    for p,key in hint['item']['members']:
        p,key=tuple(p),tuple(key)
        if p in replay.values:
            if replay.values[p]!=key:return None,dict(phase='dropped',reason='occupied_differently',pending=[],eligible=[])
        elif not legal(replay,p,key,marks):return None,dict(phase='dropped',reason='member_no_longer_legal',pending=[],eligible=[])
        else:pending.append([list(p),list(key)])
    for p,v in hint['item']['marks']:
        p=tuple(p);v=tuple(v) if isinstance(v,list) else v
        if p in marks and marks[p]!=v:return None,dict(phase='dropped',reason='interface_disagreement',pending=pending,eligible=[])
    if not pending:return None,dict(phase='completed',pending=[],eligible=[])
    eligible=[v for p,v in pending if tuple(p)==point] if kind in ('branch','forced') else []
    return dict(hint,waiting=not bool(eligible)),dict(phase=('resumed' if hint['waiting'] else 'continuing') if eligible else 'suspended',pending=pending,eligible=eligible)
def policy(replay,pool,weights,stochastic,rng):
    vectors=[(0.,)*7+(1.,)]
    for item in pool:
        n=len(item['pending']);heads=sum(v[1]>=replay.ref.A for _,v in item['pending']);accepts=sum(v[1]>=replay.ref.A and (v[1]-replay.ref.A)//replay.ref.A==replay.ref.accept for _,v in item['pending']);vectors.append((1.,n/8,item['level']/4,item['known_fraction'],heads/n,accepts/n,len(replay.order)/len(replay.required),0.))
    scores=[sum(a*b for a,b in zip(v,weights)) for v in vectors];peak=max(scores);m=[math.exp(s-peak) for s in scores];total=sum(m);probabilities=[v/total for v in m];draw=rng.random() if stochastic else None;selected=max(range(len(scores)),key=lambda j:(scores[j],-j))
    if stochastic:
        cumulative=0.;selected=len(scores)-1
        for j,p in enumerate(probabilities):
            cumulative+=p
            if draw<cumulative:selected=j;break
    gradient=[vectors[selected][j]-sum(p*v[j] for p,v in zip(probabilities,vectors)) for j in range(8)]
    return None if selected==0 else pool[selected-1],dict(features=vectors,scores=scores,probabilities=probabilities,draw=draw,selected=selected,gradient=gradient)
