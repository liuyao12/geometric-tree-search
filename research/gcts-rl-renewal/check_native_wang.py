"""Independent raw-table aggregates, literal rules and complete domain counts.

No producer, native process or shared Inventory class is imported. The index
counts compressed default rows and then adjusts every explicit override.
Query-specific inverse lists are used only after the entire table is scanned.
"""
import array,struct

def need(t,s):
    if not t:raise ValueError(s)
def normalize(s):
    if s is None:return None
    if isinstance(s,dict):return range(*s['range'])
    if isinstance(s,range):return s
    return tuple(sorted(set(s)))

class Reference:
    def __init__(self,raw,queries):
        magic,self.A,self.Q,self.start,self.accept,self.reject,self.space=struct.unpack_from('<7I',raw)
        need(magic==0x47544d31 and self.accept==0,'fixed native header');A=self.A;self.D=A*(self.Q+1)
        wanted={v['north'] for v in queries if v['north'] is not None and v['north']>=A};qs={(n-A)//A for n in wanted}
        self.rows=[];p=28;defaults=[0,0,0];defined=0
        incoming={r:{q:[0]*A for q in qs} for r in (1,2)};self.sources={(0,n):[] for n in wanted}
        self.sources.update({(r,q):[] for r in (1,2) for q in qs})
        adjustments=[]
        for q in range(self.Q):
            default,direction,_,_,n=struct.unpack_from('<5I',raw,p);p+=20;choices={}
            for _ in range(n):
                s,out,w,m,_=struct.unpack_from('<5I',raw,p);p+=20;need(s not in choices and s<A and out<self.Q and w<A and m<3,'all literal actions');choices[s]=(out,w,m-1)
            self.rows.append((default-1 if default else None,direction-1,choices));defined+=A if default else n
            if default:
                need(direction!=1,'this pinned table has moving defaults');defaults[direction]+=1
                role=1 if direction==2 else 2
                if default-1 in qs:
                    incoming[role][default-1]=[v+1 for v in incoming[role][default-1]]
                    self.sources[role,default-1].extend(A+A*q+s for s in range(A))
            adjustments.append((q,default-1 if default else None,direction-1,choices))
        need(p==len(raw) and self.rows[0]==(None,0,{}),'whole table and absorbing adapter')
        self.defined=defined;self.plain=[[0]*A for _ in range(A)];self.under=[[0]*A for _ in range(A)];self.valid=[sum(defaults)]*A
        entered={1:[defaults[2]]*A,2:[defaults[0]]*A};self.stay={n:[0]*A for n in wanted}
        for s in range(A):self.plain[s][s]=self.under[s][s]=sum(defaults)
        for q,default,direction,choices in adjustments:
            for s,(out,w,d) in choices.items():
                if default is not None:
                    self.plain[s][s]-=1;self.under[s][s]-=1;role=1 if direction==1 else 2;entered[role][s]-=1
                    if default in qs:incoming[role][default][s]-=1
                else:self.valid[s]+=1
                self.under[s][w]+=1
                if d:
                    self.plain[s][w]+=1;role=1 if d==1 else 2;entered[role][s]+=1
                    if out in qs:incoming[role][out][s]+=1;self.sources[role,out].append(A+A*q+s)
                else:
                    n=A+A*out+w
                    if n in wanted:self.stay[n][s]+=1;self.sources[0,n].append(A+A*q+s)
        for s in range(A):
            self.valid[s]+=1;self.under[s][s]+=1;n=A+s
            if n in wanted:self.stay[n][s]+=1;self.sources[0,n].append(n)
        self.incoming=incoming;self.entered=entered
        for (role,n),values in self.sources.items():
            north=n if role==0 else A+A*n
            self.sources[role,n]=tuple(h for h in sorted(set(values)) if self.member(h,role,north))
        self.cache={}
    def delta(self,q,s):
        default,direction,choices=self.rows[q];return choices.get(s,None if default is None else (default,s,direction))
    def member(self,h,role,north):
        A=self.A;q,s=divmod(h-A,A)
        if q==self.accept:
            if role:return north is None or north<A
            output=h
        else:
            action=self.delta(q,s)
            if role:
                if north is None or north< -1:return True
                entering=action is not None and action[2]==(1 if role==1 else -1)
                return not entering if north<A else entering and action[0]==(north-A)//A
            if action is None:return False
            out,w,d=action;output=A+A*out+w if d==0 else w
        return north is None or (output if north>=0 else (output-A)%A if output>=A else output)==(north if north>=0 else -2-north)
    def count(self,role,north,allowed):
        s=normalize(allowed);key=role,north,s
        if key in self.cache:return self.cache[key]
        if s is not None and not isinstance(s,range):result=sum(self.member(h,role,north) for h in s)
        elif isinstance(s,range) and not len(s):result=0
        else:
            body=None;excluded=False
            if s is not None:
                need(s.stop==self.D and s.step in (1,self.A),'whole or fiber selector');body=(s.start-self.A)%self.A if s.step==self.A else None
                excluded=s.start>=2*self.A;need(s.start in (self.A+(body or 0),2*self.A+(body or 0)),'full/nonaccepting selector')
            cols=range(self.A) if body is None else (body,);size=(self.Q-int(excluded))*len(cols)
            if role:
                if north is None or north< -1:result=size
                elif north<self.A:result=size-sum(self.entered[role][j] for j in cols)
                else:result=sum(self.incoming[role][(north-self.A)//self.A][j] for j in cols)
            elif north is None:result=sum(self.valid[j] for j in cols)-int(excluded)*len(cols)
            elif north< -1:
                w=-2-north;result=sum(self.under[j][w] for j in cols)-int(excluded and (body is None or body==w))
            elif north<self.A:result=sum(self.plain[j][north] for j in cols)
            else:
                result=sum(self.stay[north][j] for j in cols)
                if excluded and (north-self.A)//self.A==0 and (body is None or body==(north-self.A)%self.A):result-=1
        self.cache[key]=result;return result
    def heads(self,role,north,allowed):
        s=normalize(allowed)
        if north is not None and north>=self.A:
            values=self.sources[role,north if role==0 else (north-self.A)//self.A]
        else:values=range(self.A,self.D) if s is None else s
        return (h for h in values if (s is None or h in s) and self.member(h,role,north))
    def successor(self,triple):
        A=self.A;a,b,c=triple;heads=[v for v in triple if v>=A];need(len(heads)<=1,'at most one input head')
        if b>=A:
            q,s=divmod(b-A,A)
            if q==self.accept:return b
            tr=self.delta(q,s);need(tr is not None,'defined center transition');out,w,d=tr;return A+A*out+w if d==0 else w
        for v,d in ((a,1),(c,-1)):
            if v>=A:
                q,s=divmod(v-A,A);tr=None if q==self.accept else self.delta(q,s)
                if tr is not None and tr[2]==d:return A+A*tr[0]+b
        return b
    def domain(self,allowed,north,projections=(None,)*4):
        A=self.A;slots=[normalize(s) for s in allowed];plain=[];heads=[]
        for s,tau in zip(slots,projections[:3]):
            plain.append(tuple(v for v in range(A) if (s is None or v in s) and (tau is None or v==tau)))
            if s is None:h=None if tau is None else range(A+tau,self.D,A)
            elif isinstance(s,range):
                first=s.start+max(0,(A-s.start+s.step-1)//s.step)*s.step
                if tau is not None:first+=(tau-(first-A)%A)%A
                h=range(first,s.stop,A if tau is not None else s.step) if first<s.stop and (s.step==1 or tau is None or (first-s.start)%s.step==0) else ()
            else:h=tuple(v for v in s if v>=A and (tau is None or (v-A)%A==tau))
            heads.append(h)
        tn=projections[3]
        if tn is not None and north is not None and (north if north<A else (north-A)%A)!=tn:return [],0
        selector=north if north is not None or tn is None else -2-tn
        normal=tuple(v for v in plain[1] if (north is None or v==north) and (tn is None or v==tn))
        side=tuple(v for v in plain[1] if (north is None or (v==north if north<A else v==(north-A)%A)) and (tn is None or v==tn))
        ab,bb,cb=plain
        # Explicit wrappers prevent a three-symbol ordinary tuple from being
        # confused with a head selector.
        blocks=[(ab,normal,cb),(ab,{'selector':(0,selector,heads[1])},cb),({'selector':(1,selector,heads[0])},side,cb),(ab,side,{'selector':(2,selector,heads[2])})]
        count=sum(__import__('functools').reduce(lambda a,v:a*(self.count(*v['selector']) if isinstance(v,dict) else len(v)),block,1) for block in blocks)
        return blocks,count
    def options(self,blocks):
        def values(v):return self.heads(*v['selector']) if isinstance(v,dict) else iter(v)
        for aa,bb,cc in blocks:
            if any((self.count(*v['selector']) if isinstance(v,dict) else len(v))==0 for v in (aa,bb,cc)):continue
            for a in values(aa):
                for b in values(bb):
                    for c in values(cc):yield a,b,c
