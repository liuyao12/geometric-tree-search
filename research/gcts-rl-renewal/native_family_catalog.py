"""Cold native patches become guarded families over symbol/state receptors.

Templates never license a tile: each ground expansion is checked against the
unchanged literal inventory and current point graph. Defaults come solely
from fresh donor rectangles. No family contributes to candidate counts.
"""
import hashlib,time
from collections import Counter
from serialized_kernel import canonical
from native_wang_search import assignments

SHAPES=((2,1),(1,2),(3,1),(1,3),(2,2),(3,2),(2,3))
def fingerprint(value):return hashlib.sha256(canonical(value)).hexdigest()
def schema(tiles,A):
    ss={};qs={};defaults={}
    def var(kind,value):
        d=ss if kind=='s' else qs
        if value not in d:d[value]=kind+str(len(d));defaults[d[value]]=value
        return d[value]
    def expr(v):
        if v<A:return ['s',var('s',v)]
        q,s=divmod(v-A,A);return ['h',var('q',q),var('s',s)]
    left=min(t['x'] for t in tiles);bottom=min(t['y'] for t in tiles)
    pattern=[dict(x=t['x']-left,y=t['y']-bottom,triple=[expr(v) for v in t['triple']],north=expr(t['N'])) for t in sorted(tiles,key=lambda t:(t['y'],t['x']))]
    return pattern,defaults
def mine(donors,inventory,per_shape=3):
    began=time.perf_counter();templates={};occurrences=Counter();sources={}
    for donor_index,row in enumerate(donors):
        r=row['result']
        if r['status']!='finite_exact_native_rectangle':continue
        cells={(t['x'],t['y']):t for t in r['tiles']}
        for w,h in SHAPES:
            for y in range(r['height']-h+1):
                for x in range(r['width']-w+1):
                    tiles=[cells[x+dx,y+dy] for dy in range(h) for dx in range(w)]
                    pattern,defaults=schema(tiles,inventory.A);name='native-family-'+fingerprint(pattern)[:24]
                    templates.setdefault(name,dict(name=name,width=w,height=h,pattern=pattern,defaults=defaults,source=dict(donor=donor_index,origin=[x,y],tiles=tiles)))
                    occurrences[name]+=1;sources.setdefault(name,set()).add(donor_index)
    offered=[]
    for w,h in SHAPES:
        names=[n for n,t in templates.items() if (t['width'],t['height'])==(w,h)]
        names.sort(key=lambda n:(-len(sources[n]),-occurrences[n],n));offered+=names[:per_shape]
    library=[]
    # Every larger family has an explicit binary ownership tree. Leaves are
    # original tile positions; no new inference rule is promoted.
    def hierarchy(indices):
        if len(indices)==1:return dict(leaf=indices[0],level=0)
        cut=len(indices)//2;a=hierarchy(indices[:cut]);b=hierarchy(indices[cut:]);return dict(children=[a,b],level=1+max(a['level'],b['level']))
    for name in offered:
        t=templates[name];t.update(occurrences=occurrences[name],donors=sorted(sources[name]),hierarchy=hierarchy(list(range(len(t['pattern'])))));t['level']=t['hierarchy']['level'];library.append(t)
    return library,dict(seconds=time.perf_counter()-began,distinct=len(templates),windows=sum(occurrences.values()),offered=len(library),per_shape=per_shape,shapes=SHAPES)
def expression(e,binding,A):return binding[e[1]] if e[0]=='s' else A+A*binding[e[1]]+binding[e[2]]
def bind(e,value,binding,i):
    if type(value) is not int or not 0<=value<i.D:return False
    if e[0]=='s':pairs=((e[1],value),) if value<i.A else ()
    elif value>=i.A:q,s=divmod(value-i.A,i.A);pairs=((e[1],q),(e[2],s))
    else:pairs=()
    if not pairs:return False
    for name,v in pairs:
        if name in binding and binding[name]!=v:return False
        binding[name]=v
    return True
def ports(t,origin,extended=False,projected=False):
    x,y=2*(t['x']+origin[0]),2*(t['y']+origin[1]);a,b,c=t['triple'];n=t['north']
    values=[((x,y-1),b),((x,y+1),n),((x-1,y),(a,b)),((x+1,y),(b,c))]
    if extended:values+= [((x-2,y-1),a),((x+2,y-1),c)]
    if projected:
        def underlying(e):return ['s',e[-1]]
        values+=[((px,py,1),underlying(e)) for px,py,e in ((x-2,y-1,a),(x,y-1,b),(x+2,y-1,c),(x,y+1,n))]
    return values
def validate(library,inventory):
    seen=set()
    for t in library:
        if t['name'] in seen or t['name']!='native-family-'+fingerprint(t['pattern'])[:24]:raise ValueError('distinct native schema identity')
        seen.add(t['name']);source=t['source']['tiles'];pattern,defaults=schema(source,inventory.A)
        if (pattern,defaults)!=(t['pattern'],t['defaults']):raise ValueError('actual donor abstraction')
        occupied=set();marks={}
        for row in t['pattern']:
            p=row['x'],row['y'];key=tuple(expression(e,defaults,inventory.A) for e in row['triple']);tile=inventory.tile(*key)
            if p in occupied or tile['N']!=expression(row['north'],defaults,inventory.A):raise ValueError('original native family guard')
            occupied.add(p)
            for q,v in assignments(tile,*p)[1].items():
                if q in marks and marks[q]!=v:raise ValueError('internal native agreement')
                marks[q]=v
        if occupied!={(x,y) for y in range(t['height']) for x in range(t['width'])}:raise ValueError('exact donor patch shape')
        def leaves(node):
            if 'leaf' in node:
                if node!=dict(leaf=node['leaf'],level=0):raise ValueError('primitive hierarchy leaf')
                return [node['leaf']]
            children=node['children']
            if len(children)!=2 or node['level']!=1+max(c['level'] for c in children):raise ValueError('descending native composition')
            return leaves(children[0])+leaves(children[1])
        if leaves(t['hierarchy'])!=list(range(len(t['pattern']))) or t['level']!=t['hierarchy']['level']:raise ValueError('exact distinct hierarchy ownership')
    return True
class Matcher:
    def __init__(self,library,graph):
        self.library=library;self.g=graph;validate(library,graph.universe.inventory)
    def instantiate(self,t,origin):
        g=self.g;i=g.universe.inventory;binding={};known=total=0
        for row in t['pattern']:
            x,y=row['x']+origin[0],row['y']+origin[1]
            if not 0<=x<g.width or not 0<=y<g.height:return None
            if (x,y) in g.selected:
                for e,v in zip(row['triple'],g.selected[x,y]):
                    if not bind(e,v,binding,i):return None
            for p,e in ports(row,origin,g.extended,g.projected):
                total+=1
                if p not in g.marks:continue
                known+=1;v=g.marks[p]
                if p[0]%2 and len(p)==2:
                    if not isinstance(v,tuple) or len(v)!=2 or not all(bind(a,b,binding,i) for a,b in zip(e,v)):return None
                elif not bind(e,v,binding,i):return None
            if y==0:
                for x0,e in zip((x-1,x,x+1),row['triple']):
                    if 0<=x0<g.width and g.pattern[x0] is not None and len(g.pattern[x0])==1:
                        if not bind(e,g.pattern[x0][0],binding,i):return None
        resolved={**t['defaults'],**binding};members=[];marks={};pending=[]
        for row in t['pattern']:
            p=row['x']+origin[0],row['y']+origin[1];key=tuple(expression(e,resolved,i.A) for e in row['triple'])
            try:tile=i.tile(*key)
            except ValueError:return None
            if tile['N']!=expression(row['north'],resolved,i.A):return None
            if p in g.selected:
                if g.selected[p]!=key:return None
            elif not g.domains[p].contains(key):return None
            else:pending.append([list(p),list(key)])
            members.append([list(p),list(key)])
            for q,v in assignments(tile,*p,g.extended,g.projected,i.A)[1].items():
                if (q in marks and marks[q]!=v) or (q in g.marks and g.marks[q]!=v):return None
                marks[q]=v
        if len(pending)<2:return None
        return dict(template=t['name'],level=t['level'],origin=list(origin),binding=resolved,bound_receptors=binding,members=members,pending=pending,marks=[[list(p),list(v) if isinstance(v,tuple) else v] for p,v in sorted(marks.items())],known_fraction=known/max(1,total))
    def proposals(self,point,limit=8):
        unique={};scanned=0
        for t in self.library:
            for anchor in t['pattern']:
                scanned+=1;origin=point[0]-anchor['x'],point[1]-anchor['y'];item=self.instantiate(t,origin)
                if item is None:continue
                key=tuple((tuple(p),tuple(k)) for p,k in item['members'])
                unique.setdefault(key,item)
        pool=sorted(unique.values(),key=lambda r:(-len(r['pending']),-r['known_fraction'],-r['level'],r['template'],r['origin']))[:limit]
        return pool,dict(scanned=scanned,matched=len(unique),offered=len(pool))
