"""One finite, request-independent Wang palette from the pinned FOL machine.

The palette is represented by four finite Cartesian families, not by a list
of hundreds of billions of squares. A tile identity is its three input
symbols. No formulas, theory names, proof paths or callbacks enter this class.
This is an inventory/verification adapter, not a GCTS search implementation.
"""
import array, hashlib, struct

TABLE_PIN='fd1621b29a7d497859c850a116b295956db99b3d7c4c076e3b78bed680d682dd'
SPEC='gcts-shared-wang-1:at-most-one-head;accept-absorbing;radius-one;translation-only;doubled-grid'

class Inventory:
    def __init__(self, raw):
        if hashlib.sha256(raw).hexdigest()!=TABLE_PIN:
            raise ValueError('external literal-table pin')
        self.raw=raw
        magic,self.A,self.Q,self.start,self.accept,self.reject,self.space=struct.unpack_from('<7I',raw)
        if magic!=0x47544d31:raise ValueError('table magic')
        self.offsets=array.array('I');p=28;defined=0
        for q in range(self.Q):
            self.offsets.append(p)
            default,direction,micro,tape,n=struct.unpack_from('<5I',raw,p)
            defined+=self.A if default else n
            p+=20+20*n
        if p!=len(raw):raise ValueError('table length')
        self.D=self.A*(self.Q+1)
        self.defined=defined
        # The published accepting row has no actions. Acceptance padding is
        # the explicit radius-one reduction convention, not a machine action.
        if self.row(self.accept)[0] or self.row(self.accept)[4]:raise ValueError('accept row')
        self.counts=dict(copy=self.A**3,center=(defined+self.A)*self.A**2,
                         left=self.Q*self.A**3,right=self.Q*self.A**3)
        self.fingerprint=hashlib.sha256((SPEC+'\n'+TABLE_PIN).encode('ascii')).hexdigest()

    def row(self,q):
        if type(q) is not int or not 0<=q<self.Q:raise ValueError('state')
        return struct.unpack_from('<5I',self.raw,self.offsets[q])

    def transition(self,q,s):
        if type(s) is not int or not 0<=s<self.A:raise ValueError('ordinary symbol')
        default,direction,_,_,n=self.row(q);p=self.offsets[q]+20
        for j in range(n):
            a,out,w,move,_=struct.unpack_from('<5I',self.raw,p+20*j)
            if a==s:return out,w,move-1
        return (default-1,s,direction-1) if default else None

    def head(self,q,s):
        if type(q) is not int or type(s) is not int or not 0<=q<self.Q or not 0<=s<self.A:
            raise ValueError('head symbol')
        return self.A+self.A*q+s

    def decode(self,v):
        if type(v) is not int or not 0<=v<self.D:raise ValueError('configuration symbol')
        return None if v<self.A else divmod(v-self.A,self.A)

    def successor(self,a,b,c):
        hs=[self.decode(v) for v in (a,b,c)]
        if sum(h is not None for h in hs)>1:return None
        if hs[1] is not None:
            q,s=hs[1]
            if q==self.accept:return b
            action=self.transition(q,s)
            if action is None:return None
            out,w,d=action
            return self.head(out,w) if d==0 else w
        for h,direction in ((hs[0],1),(hs[2],-1)):
            if h is None or h[0]==self.accept:continue
            action=self.transition(*h)
            if action is not None and action[2]==direction:return self.head(action[0],b)
        return b

    def tile(self,a,b,c):
        n=self.successor(a,b,c)
        if n is None:raise ValueError('triple outside palette')
        return dict(identity=':'.join(map(str,(a,b,c))),triple=[a,b,c],S=b,N=n,W=[a,b],E=[b,c])

    def contains(self,tile):
        try:return self.tile(*tile['triple'])==tile
        except (ValueError,TypeError,KeyError):return False

    def step(self,tape,q,head):
        action=self.transition(q,tape[head])
        if action is None:raise ValueError('undefined transition')
        out,w,d=action;tape[head]=w
        return out,head+d

def points(tile,x=0,y=0):
    return dict(t=[[[2*x,2*y],1]],m=[[[2*x,2*y-1],tile['S']],
        [[2*x,2*y+1],tile['N']],[[2*x-1,2*y],tile['W']],[[2*x+1,2*y],tile['E']]])

def input_tape(initial,labels):
    result=['L']
    for i,(word,h,n) in enumerate(zip(initial['words'],initial['heads'],initial['capacities'])):
        body=['^']+list(word)+['B']*(n-len(word)-1);body[h]='@'+body[h]
        result.extend(['S'+str(i),*body,'#'])
    index={s:i for i,s in enumerate(labels)}
    return [index[s] for s in result]

def patch(inventory,initial,labels,problem_band,height=5,width=13,limit=2000000):
    """An actual local window, sampled at the first fixed-input symbol read.

    Every exported tile belongs to the same palette. The omitted exterior
    is supplied by the recorded full-machine trajectory, not claimed tiled
    by this cropped picture. A literal prefix is replayed without sweeps.
    """
    tape=input_tape(initial,labels);q=inventory.start;h=0;step=0
    payload=2+sum(n+2 for n in initial['capacities'][:problem_band])+1
    while step<limit:
        row=inventory.row(q)
        if h==payload and row[2]:break
        q,h=inventory.step(tape,q,h);step+=1
    else:raise ValueError('prefix patch step budget')
    left=h-width//2;rows=[];trajectory=[]
    for y in range(height+1):
        # Include the two context symbols, hence an exact boundary for each
        # cropped row of triples. Read/write head may leave the window later.
        row=[inventory.head(q,tape[x]) if x==h else tape[x] for x in range(left-1,left+width+1)]
        rows.append(row);trajectory.append([step,q,h])
        if y<height:q,h=inventory.step(tape,q,h);step+=1
    tiles=[dict(x=x,y=y,**inventory.tile(*rows[y][x:x+3]))
           for y in range(height) for x in range(width)]
    if any(t['N']!=rows[t['y']+1][t['x']+1] for t in tiles):raise ValueError('local successor mismatch')
    return dict(width=width,height=height,left=left,rows=rows,trajectory=trajectory,tiles=tiles,
                prefix_steps=trajectory[0][0],payload_cell=payload,
                scope='cropped exact literal trajectory; supplied lateral boundary; not an accepting proof rectangle')
