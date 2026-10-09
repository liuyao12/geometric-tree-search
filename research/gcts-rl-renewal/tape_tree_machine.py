"""Complete tree-bytecode lowering to finite selected-tape microcode.

All runtime operations are symbol read/write/head moves. There are no runtime
heap, register, formula or inference callbacks. Binary words encode node IDs;
one sequential tape holds the canonical cons table and one holds live frames.
The following single-tape lowering makes selection itself literal scans.
"""
import hashlib,json,time
from itertools import combinations
from tree_machine import validate

RAW=('B','^','0','1',':',',',';')
def bits(n):return format(n,'b')[::-1]
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def allocation(p):
    """Exact CFG liveness; clique interference, then deterministic coloring."""
    out=[]
    for f in p['functions']:
        code=f['code'];n=len(code);reads=[];defs=[];edges=[]
        for pc,ins in enumerate(code):
            op,*a=ins
            read=({a[0]} if op in ('branch','return') else set(a[2]) if op=='call' else
                  set() if op in ('jump','const') else set(a[1:]))
            defined=set() if op in ('jump','branch','return') else {a[0]}
            after=[] if op=='return' else [a[0]] if op=='jump' else a[1:] if op=='branch' else [pc+1] if pc+1<n else []
            reads.append(read);defs.append(defined);edges.append(after)
        before=[set() for _ in code];after=[set() for _ in code]
        changed=True
        while changed:
            changed=False
            for i in reversed(range(n)):
                a=set().union(*(before[j] for j in edges[i])) if edges[i] else set()
                b=reads[i]|(a-defs[i])
                if a!=after[i] or b!=before[i]:after[i]=a;before[i]=b;changed=True
        graph=[set() for _ in range(f['registers'])]
        for i in range(n):
            for a,b in combinations(before[i]|defs[i]|after[i],2):
                graph[a].add(b);graph[b].add(a)
        colors={}
        for r in sorted(range(f['registers']),key=lambda r:(-len(graph[r]),r)):
            occupied={colors[t] for t in graph[r] if t in colors};c=0
            while c in occupied:c+=1
            colors[r]=c
        out.append(dict(slots=[colors[i] for i in range(f['registers'])],live_in=[sorted(s) for s in before],live_out=[sorted(s) for s in after]))
    return out

class Builder:
    def __init__(self):self.rows=[];self.names=[]
    def state(self,name):
        q=len(self.rows);self.rows.append(None);self.names.append(name);return q
    def put(self,q,tape,choices):
        if self.rows[q] is not None:raise ValueError('duplicate microstate')
        self.rows[q]=[tape,choices]
    def row(self,tape,choices,name='micro'):
        q=self.state(name);self.put(q,tape,choices);return q
    def jump(self,tape,out):
        return self.row(tape,{s:[out,s,0] for s in RAW},'jump')
    def rewind(self,t,out):
        q=self.state('rewind');self.put(q,t,{s:[out,s,1] if s=='^' else [q,s,-1] for s in RAW});return q
    def clear(self,t,out):
        q=self.state('clear-word');done=self.rewind(t,out)
        self.put(q,t,{'0':[q,'B',1],'1':[q,'B',1],'B':[done,'B',0]});return self.rewind(t,q)
    def constant(self,t,n,out):
        return self.clear(t,self.write_const(t,bits(n),out))
    def write_const(self,t,word,out):
        q=self.rewind(t,out)
        for s in reversed(word):q=self.row(t,{'B':[q,s,1]},'literal-bit')
        return q
    def symbol(self,t,s,out,move=1):return self.row(t,{x:[out,s,move] for x in RAW if x!='^'},'write-symbol')
    def advance(self,t,out,move=1):return self.row(t,{s:[out,s,move] for s in RAW},'advance')
    def skip(self,t,delimiter,out):
        q=self.state('skip-record')
        self.put(q,t,{s:[out,s,1] if s==delimiter else [q,s,1] for s in RAW if s not in ('B','^')})
        return q
    def end(self,t,out):
        q=self.state('word-end');self.put(q,t,{'0':[q,'0',1],'1':[q,'1',1],'B':[out,'B',0]});return q
    def append(self,src,dst,out,delimiter='B',source_start=True):
        loop=self.state('copy-word');choices={delimiter:[out,delimiter,0]}
        for bit in ('0','1'):
            step=self.advance(src,loop)
            write=self.row(dst,{'B':[step,bit,1]},'copy-bit')
            choices[bit]=[write,bit,0]
        self.put(loop,src,choices);return self.rewind(src,loop) if source_start else loop
    def copy(self,src,dst,out,delimiter='B',source_start=True):
        if src==dst and delimiter=='B':return self.rewind(src,out)
        return self.clear(dst,self.append(src,dst,self.rewind(dst,out),delimiter,source_start))
    def equal(self,x,y,endx,endy,yes,no):
        if x==y and endx==endy:return self.jump(x,yes)
        loop=self.state('compare-word');choices={}
        check_end=self.row(y,{s:[yes if s==endy else no,s,0] for s in RAW},'compare-end')
        choices[endx]=[check_end,endx,0]
        for bit in ('0','1'):
            advance_y=self.advance(y,loop)
            compare=self.row(y,{s:[advance_y if s==bit else no,s,0] for s in RAW},'compare-bit')
            choices[bit]=[compare,bit,1]
        self.put(loop,x,choices);return loop
    def is_pair(self,t,yes,no):
        # Node IDs are canonical binary naturals; nine bits distinguish 256.
        end_states={}
        for seen in (False,True):
            end_states[seen]=self.row(t,{'B':[yes if seen else no,'B',0],'0':[yes,'0',0],'1':[yes,'1',0]},'node-range')
        layer={(seen):self.row(t,{'B':[no,'B',0],'0':[end_states[False],'0',1],'1':[end_states[seen],'1',1]},'ninth-bit') for seen in (False,True)}
        for _ in range(8):
            layer={seen:self.row(t,{'B':[no,'B',0],'0':[layer[seen],'0',1],'1':[layer[True],'1',1]},'node-range-bit') for seen in (False,True)}
        return self.rewind(t,layer[False])
    def boolean(self,t,zero,one,bad):
        choice={}
        for bit,out in (('0',zero),('1',one)):
            tail=self.row(t,{s:[out if s=='B' else bad,s,0] for s in RAW},'boolean-end')
            choice[bit]=[tail,bit,1]
        return self.rewind(t,self.row(t,choice,'boolean'))
    def increment(self,t,out):
        done=self.rewind(t,out);q=self.state('increment')
        self.put(q,t,{'0':[done,'1',0],'1':[q,'0',1],'B':[done,'1',1]});return self.rewind(t,q)

class Lowering:
    def __init__(self,p):
        validate(p);self.program=p;self.alloc=allocation(p);b=Builder();self.b=b
        self.registers=max(max(a['slots'])+1 for a in self.alloc)
        self.arity=max(f['arity'] for f in p['functions'])
        self.arg=self.registers
        self.work=self.arg+self.arity
        self.heap=self.work+4;self.next=self.heap+1;self.stack=self.next+1;self.tapes=self.stack+1
        self.accept=b.state('accept');self.reject=b.state('reject');self.space=b.state('space-bound')
        self.entries=[[b.state('instruction/'+str(f)+'/'+str(pc)) for pc in range(len(fn['code']))] for f,fn in enumerate(p['functions'])]
        sites=[(f,i) for f,fn in enumerate(p['functions']) for i,ins in enumerate(fn['code']) if ins[0]=='call']
        self.call_ids={site:i+1 for i,site in enumerate(sites)};self.address_width=max(1,len(sites).bit_length())
        self.restore={}
        returned=self.work
        root_done=b.boolean(returned,self.reject,self.accept,self.reject)
        self.restore[0]=b.row(self.stack,{':':[root_done,'B',0]},'root-frame')
        for f,pc in sites:
            ins=p['functions'][f]['code'][pc];_,dst,target,args=ins
            slots=self.alloc[f]['slots'];saved=sorted(set(slots[r] for r in self.alloc[f]['live_out'][pc] if r!=dst))
            continuation=b.copy(returned,slots[dst],self.entries[f][pc+1])
            continuation=b.row(self.stack,{':':[continuation,'B',0]},'remove-frame')
            for r in saved:
                loop=b.state('pop-value')
                stop={s:[continuation,s,0] for s in (',',':')}
                for bit in ('0','1'):
                    again=b.advance(self.stack,loop,-1)
                    put=b.row(r,{'B':[again,bit,1]},'restore-register')
                    stop[bit]=[put,'B',0]
                b.put(loop,self.stack,stop)
                begin=b.row(self.stack,{',':[loop,'B',-1]},'pop-separator')
                continuation=b.clear(r,begin)
            self.restore[self.call_ids[f,pc]]=continuation
        def dispatch(prefix):
            if len(prefix)==self.address_width:return self.restore.get(int(prefix,2),self.reject)
            q=b.state('return-address');choices={}
            for bit in ('0','1'):choices[bit]=[dispatch(prefix+bit),'B',-1]
            b.put(q,self.stack,choices);return q
        decode=dispatch('')
        top=b.row(self.stack,{';':[decode,'B',-1]},'return-frame')
        self.return_entry=b.row(self.stack,{'B':[top,'B',-1]},'return-stack')
        for f,fn in enumerate(p['functions']):
            for pc,ins in enumerate(fn['code']):
                entry=self.compile_instruction(f,pc,ins)
                # A state alias is an ordinary same-symbol transition.
                b.put(self.entries[f][pc],0,{s:[entry,s,0] for s in RAW})
        entry=self.entries[0][0];a=self.alloc[0]
        for r in a['live_in'][0]:
            if r!=0:entry=b.constant(a['slots'][r],256,entry)
        self.start=entry
    def compile_instruction(self,f,pc,ins):
        b=self.b;p=self.program;op,*a=ins;slots=self.alloc[f]['slots']
        done=self.entries[f][pc+1] if pc+1<len(self.entries[f]) else self.reject
        r=lambda k:slots[k]
        bool_value=lambda dst,out: b.constant(dst,int(out),done)
        if op=='jump':return self.entries[f][a[0]]
        if op=='const':return b.constant(r(a[0]),p['constants'][a[1]],done)
        if op=='move':return b.copy(r(a[1]),r(a[0]),done)
        if op=='branch':return b.boolean(r(a[0]),self.entries[f][a[1]],self.entries[f][a[2]],self.reject)
        if op=='not':return b.boolean(r(a[1]),bool_value(r(a[0]),True),bool_value(r(a[0]),False),self.reject)
        if op=='pair':return b.is_pair(r(a[1]),bool_value(r(a[0]),True),bool_value(r(a[0]),False))
        if op=='atom':
            yes=bool_value(r(a[0]),True);no=bool_value(r(a[0]),False)
            compare=b.equal(r(a[1]),r(a[2]),'B','B',yes,no)
            compare=b.rewind(r(a[1]),b.rewind(r(a[2]),compare))
            test=b.is_pair(r(a[2]),no,compare)
            return b.is_pair(r(a[1]),no,test)
        if op=='succ':
            out=b.increment(self.work+1,b.copy(self.work+1,r(a[0]),done))
            # Reject 255 and nil; all other non-pair IDs are byte inputs.
            check256=self.compare_constant(self.work+1,256,self.reject,out)
            check255=self.compare_constant(self.work+1,255,self.reject,check256)
            check=b.is_pair(self.work+1,self.reject,check255)
            return b.copy(r(a[1]),self.work+1,check)
        if op in ('head','tail'):
            dest=r(a[0]);find=b.state('lookup-record')
            copied=b.copy(self.heap,dest,done,',' if op=='head' else ';',False)
            # On match heap cursor is on the colon. Tail first skips a.
            at_child=b.advance(self.heap,copied if op=='head' else b.skip(self.heap,',',copied))
            next_record=b.skip(self.heap,';',find)
            compare=b.equal(self.heap,self.work+1,':','B',at_child,next_record)
            begin=b.rewind(self.work+1,compare)
            b.put(find,self.heap,{'0':[begin,'0',0],'1':[begin,'1',0],'B':[self.reject,'B',0]})
            search=b.is_pair(self.work+1,b.rewind(self.heap,find),self.reject)
            return b.copy(r(a[1]),self.work+1,search)
        if op=='cons':return self.cons(r(a[0]),r(a[1]),r(a[2]),done)
        if op=='call':
            dst,target,args=a;target_slots=self.alloc[target]['slots'];live=self.alloc[target]['live_in'][0]
            q=self.entries[target][0]
            for logical in live:
                q=b.copy(self.arg+logical,target_slots[logical],q) if logical<p['functions'][target]['arity'] else b.constant(target_slots[logical],256,q)
            # Append address and delimiter at stack's persistent end cursor.
            address=bits(self.call_ids[f,pc]).ljust(self.address_width,'0')
            q=b.symbol(self.stack,';',q)
            for bit in reversed(address):q=b.symbol(self.stack,bit,q)
            saved=sorted(set(slots[t] for t in self.alloc[f]['live_out'][pc] if t!=dst))
            for tape in reversed(saved):
                end=b.symbol(self.stack,',',q);loop=b.state('save-live-register')
                choices={'^':[end,'^',0]}
                for bit in ('0','1'):
                    step=b.advance(tape,loop,-1)
                    put=b.row(self.stack,{'B':[step,bit,1]},'save-register-bit');choices[bit]=[put,bit,0]
                b.put(loop,tape,choices)
                q=b.rewind(tape,b.end(tape,b.advance(tape,loop,-1)))
            q=b.symbol(self.stack,':',q)
            for i in reversed(range(len(args))):q=b.copy(r(args[i]),self.arg+i,q)
            return q
        if op=='return':return b.copy(r(a[0]),self.work,self.return_entry)
        raise ValueError('unlowered opcode '+op)
    def compare_constant(self,t,n,yes,no):
        b=self.b;q=b.equal(t,self.work+3,'B','B',yes,no)
        return b.constant(self.work+3,n,b.rewind(t,b.rewind(self.work+3,q)))
    def cons(self,dst,a,c,done):
        b=self.b;h=self.heap;first=self.work+1;second=self.work+2;record=self.work+3
        loop=b.state('cons-record')
        # At the end append the canonical new record and advance the ID.
        complete=b.increment(self.next,done)
        complete=b.symbol(h,';',complete)
        complete=b.append(second,h,complete)
        complete=b.symbol(h,',',complete)
        complete=b.append(first,h,complete)
        complete=b.symbol(h,':',complete)
        complete=b.append(self.next,h,complete)
        allocate=b.copy(self.next,dst,complete)
        skip=b.skip(h,';',loop)
        found=b.copy(record,dst,done)
        cmp_b=b.equal(h,second,';','B',found,skip)
        cmp_b=b.rewind(second,cmp_b)
        cmp_a=b.equal(h,first,',','B',b.advance(h,cmp_b),skip)
        cmp_a=b.rewind(first,cmp_a)
        start=b.copy(h,record,b.advance(h,cmp_a),':',False)
        b.put(loop,h,{'B':[allocate,'B',0],'0':[start,'0',0],'1':[start,'1',0]})
        return b.copy(a,first,b.copy(c,second,b.rewind(h,loop)))
    def declaration(self):
        return dict(raw=list(RAW),rows=self.b.rows,names=self.b.names,start=self.start,accept=self.accept,reject=self.reject,space=self.space,
            tapes=self.tapes,registers=self.registers,arg=self.arg,work=self.work,heap=self.heap,next=self.next,stack=self.stack,
            address_width=self.address_width,allocation=self.alloc,entries=self.entries,program_sha256=sha(self.program))
    def initial(self,initial,word_capacity=64,heap_padding=4096,stack_capacity=32768):
        values=['']*self.tapes;heads=[1]*self.tapes
        slot=self.alloc[0]['slots'][0];values[slot]=bits(initial['node'])
        for i in range(self.registers):
            if i!=slot:values[i]=bits(256)
        values[self.heap]=''.join(bits(257+i)+':'+bits(a)+','+bits(c)+';' for i,(a,c) in enumerate(initial['nodes']))
        values[self.next]=bits(257+len(initial['nodes']))
        values[self.stack]=':'+('0'*self.address_width)+';';heads[self.stack]=len(values[self.stack])+1
        capacities=[word_capacity]*self.tapes;capacities[self.heap]=len(values[self.heap])+heap_padding;capacities[self.stack]=stack_capacity
        if any(len(v)+1>=n for v,n in zip(values,capacities)):raise ValueError('initial tape capacity')
        return dict(words=values,heads=heads,capacities=capacities)

def virtual_run(d,initial,limit=10000000,keep=20):
    tapes=[['^']+list(w)+['B']*(n-len(w)-1) for w,n in zip(initial['words'],initial['capacities'])]
    heads=list(initial['heads']);q=d['start'];physical=0;trace=[];start=time.perf_counter()
    # Literal physical layout: L, then one header and padded band per tape.
    headers=[];offset=1
    for n in initial['capacities']:headers.append(offset);offset+=n+2
    last=0;digest=14695981039346656037;mask=(1<<64)-1
    def hash_values(values):
        nonlocal digest
        for v in values:digest=((digest^v)*1099511628211)&mask
    for step in range(limit):
        if q in (d['accept'],d['reject'],d['space']):break
        t,choices=d['rows'][q];pos=heads[t];s=tapes[t][pos];action=choices.get(s)
        if action is None:q=d['reject'];break
        out,w,move=action;marker=headers[t]+1+pos
        physical+=last+marker+2+int(move!=0)
        hash_values((q,t,pos,RAW.index(s),out,RAW.index(w),move+1))
        if len(trace)<keep:trace.append([q,t,pos,s,out,w,move,physical])
        tapes[t][pos]=w;heads[t]+=move;last=marker+move;q=out
        if not 0<=heads[t]<len(tapes[t]):q=d['space'];step+=1;break
    else:step=limit
    terminal='accepted' if q==d['accept'] else 'rejected' if q==d['reject'] else 'unknown_space_budget' if q==d['space'] else 'unknown_step_budget'
    return dict(status=terminal,micro_steps=step,physical_steps=physical,micro_fnv64=str(digest),state=q,heads=heads,
                words=[''.join(t[1:]).rstrip('B') for t in tapes],trace=trace,seconds=time.perf_counter()-start)

def physical_declaration(d):
    """Finite table, compressed solely by same-symbol self-loop rows.

    Enumerating the finite alphabet expands every default to ordinary TM
    transitions. There are no predicates, arithmetic or data-dependent hooks.
    """
    raw=list(RAW)+['#'];marked=['@'+s for s in raw];headers=['S'+str(i) for i in range(d['tapes'])]
    alphabet=['L']+raw+marked+headers;rows=[];names=[];entry={}
    def state(name):q=len(rows);rows.append(None);names.append(name);return q
    halt={name:state(name) for name in ('accept','reject','space')}
    for q,row in enumerate(d['rows']):
        if row is not None:entry[q]=[state('select/'+str(q)),state('header/'+str(q)),state('head/'+str(q)),state('read/'+str(q))]
    def start(q):
        return halt['accept'] if q==d['accept'] else halt['reject'] if q==d['reject'] else halt['space'] if q==d['space'] else entry[q][0]
    marker_states={}
    for q in range(len(d['rows'])):marker_states[q]=state('mark/'+str(q))
    for q,row in enumerate(d['rows']):
        if row is None:continue
        t,choices=row;s,h,find,read=entry[q]
        rows[s]=[[s,-1],{'L':[h,'L',1]}]
        rows[h]=[[h,1],{headers[t]:[find,headers[t],1]}]
        rows[find]=[[find,1],{m:[read,m,0] for m in marked}]
        overrides={}
        for a,(out,w,move) in choices.items():
            overrides['@'+a]=[start(out) if not move else marker_states[out],'@'+w if not move else w,move]
        overrides['@#']=[halt['space'],'@#',0]
        rows[read]=[None,overrides]
    for q,m in marker_states.items():
        rows[m]=[None,{s:[start(q),'@'+s,0] for s in raw if s!='#'}|{'#':[halt['space'],'#',0]}]
    return dict(alphabet=alphabet,rows=rows,names=names,start=start(d['start']),accept=halt['accept'],reject=halt['reject'],space=halt['space'],entries=entry,micro_sha256=sha(d))

def physical_input(initial):
    tape=['L']
    for i,(word,head,n) in enumerate(zip(initial['words'],initial['heads'],initial['capacities'])):
        body=['^']+list(word)+['B']*(n-len(word)-1);body[head]='@'+body[head]
        tape+=['S'+str(i)]+body+['#']
    return tape
