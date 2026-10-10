"""Ground completed clusters checked without the family matcher or policy."""
from check_native_rectangle import Primitive,require
def check(raw,spec,result):
    p=Primitive(raw);checks={name:p.check(spec,result,decorated) for name,decorated in (('original',False),('decorated',True))};selected={(t['x'],t['y']):t for t in result['tiles']};completed=[]
    for identity in result['solution_hints']:
        require(type(identity) is int and 0<=identity<len(result['hints']),'completed native family identity');h=result['hints'][identity];seen=set();marks={}
        for pos,key in h['item']['members']:
            x,y=pos;require((x,y) not in seen and (x,y) in selected and selected[x,y]['triple']==key,'expanded completed family');seen.add((x,y));t=selected[x,y];a,b,c=key;n=p.output(key)
            values={(2*x,2*y-1):b,(2*x,2*y+1):n,(2*x-1,2*y):(a,b),(2*x+1,2*y):(b,c)}
            for px,py,v in ((2*x-2,2*y-1,a),(2*x,2*y-1,b),(2*x+2,2*y-1,c),(2*x,2*y+1,n)):values[px,py,1]=v if v<p.A else (v-p.A)%p.A
            for q,v in values.items():require(q not in marks or marks[q]==v,'compatible original family union');marks[q]=v
        expected=[[list(q),list(v) if isinstance(v,tuple) else v] for q,v in sorted(marks.items())];require(expected==h['item']['marks'],'literal aggregate, no hidden markings');completed.append(dict(id=identity,cells=len(seen),level=h['item']['level'],status='accepted_original_native_cluster'))
    require(len(set(result['solution_hints']))==len(result['solution_hints']),'distinct completed hint occurrences');return checks,completed
