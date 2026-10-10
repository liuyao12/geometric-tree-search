"""Direct raw-table transitions and point certificates, no domain code."""
import array,hashlib,struct
PIN='fd1621b29a7d497859c850a116b295956db99b3d7c4c076e3b78bed680d682dd'
def require(t,s):
    if not t:raise ValueError(s)
class Primitive:
    def __init__(self,raw):
        require(hashlib.sha256(raw).hexdigest()==PIN,'fixed literal table');self.raw=raw
        magic,self.A,self.Q,self.start,self.accept,self.reject,self.space=struct.unpack_from('<7I',raw);require(magic==0x47544d31,'magic');self.D=self.A*(self.Q+1)
        self.offsets=array.array('I');p=28
        for _ in range(self.Q):self.offsets.append(p);p+=20+20*struct.unpack_from('<I',raw,p+16)[0]
        require(p==len(raw),'whole literal table')
    def action(self,q,s):
        p=self.offsets[q];fallback,move,_,_,n=struct.unpack_from('<5I',self.raw,p)
        for j in range(n):
            read,out,w,d,_=struct.unpack_from('<5I',self.raw,p+20+20*j)
            if read==s:return out,w,d-1
        return None if not fallback else (fallback-1,s,move-1)
    def output(self,triple):
        require(len(triple)==3 and all(type(v) is int and 0<=v<self.D for v in triple),'three configuration symbols');A=self.A;a,b,c=triple
        require(sum(v>=A for v in triple)<=1,'local head count')
        if b>=A:
            q,s=divmod(b-A,A)
            if q==self.accept:return b
            step=self.action(q,s);require(step is not None,'defined center action');out,w,d=step;return A+A*out+w if d==0 else w
        for v,d in ((a,1),(c,-1)):
            if v>=A:
                q,s=divmod(v-A,A);step=None if q==self.accept else self.action(q,s)
                if step is not None and step[2]==d:return A+A*step[0]+b
        return b
    def check(self,spec,result,decorated=True):
        width=len(spec['pattern']);height=spec['height'];seen=set();marks={}
        def put(p,v):
            p=tuple(p);v=tuple(v) if isinstance(v,list) else v
            require(p not in marks or marks[p]==v,'literal global agreement');marks[p]=v
        for p,v in result['boundary']:
            if decorated or len(p)==2:put(p,v)
        def allowed(s,v):return s is None or v in (range(*s['range']) if isinstance(s,dict) else s)
        for t in result['tiles']:
            x,y=t['x'],t['y'];require(0<=x<width and 0<=y<height and (x,y) not in seen,'unit center capacity');seen.add((x,y));a,b,c=t['triple'];n=self.output(t['triple'])
            require(t['identity']==':'.join(map(str,(a,b,c))) and (t['S'],t['N'],t['W'],t['E'])==(b,n,[a,b],[b,c]),'original Wang tile')
            if y==0:
                for j,v in ((x-1,a),(x,b),(x+1,c)):
                    if 0<=j<width:require(allowed(spec['pattern'][j],v),'fixed/free input boundary')
            values={(2*x,2*y-1):b,(2*x,2*y+1):n,(2*x-1,2*y):(a,b),(2*x+1,2*y):(b,c)}
            if decorated and result['extended']:values.update({(2*x-2,2*y-1):a,(2*x+2,2*y-1):c})
            if decorated and result['projected']:
                for px,py,v in ((2*x-2,2*y-1,a),(2*x,2*y-1,b),(2*x+2,2*y-1,c),(2*x,2*y+1,n)):values[px,py,1]=v if v<self.A else (v-self.A)%self.A
            for p,v in values.items():put(p,v)
        require(len(result['tile_generations'])==len(seen) and all(g==1 for g in result['tile_generations']),'root/placement generation')
        complete=result['status']=='finite_exact_native_rectangle'
        if complete:require(len(seen)==width*height,'all required centers filled')
        return dict(status='accepted_original_rectangle' if complete else 'accepted_partial_state',cells=len(seen),mark_points=len(marks),decorated=decorated)
