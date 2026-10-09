"""Small-step tree bytecode with finite byte atoms and immutable cons cells.

No primitive knows terms, formulas, proof rules, signatures or induction.
The compiler accepts a deliberately small Python-shaped static source language;
request data is never compiled or executed. A heap DAG shares equal cons cells.
This is an operational tree machine, not yet a literal tape/Wang interpreter.
"""
import ast,hashlib,json,time
from collections import Counter
NIL=256
PRIMITIVES={'cons':('cons',2),'head':('head',1),'tail':('tail',1),
            'is_pair':('pair',1),'atom_eq':('atom',2),'byte_succ':('succ',1)}

class Resource(Exception):pass

class Heap:
    def __init__(self,nodes=(),limit=None):
        self.nodes=[];self.index={};self.limit=limit
        for a,b in nodes:
            if (a,b) in self.index:raise ValueError('duplicate initial heap node')
            self.cons(a,b)
    def cons(self,a,b):
        if any(type(v) is not int or not 0<=v<257+len(self.nodes) for v in (a,b)):
            raise ValueError('cons children must be existing nodes or atoms')
        k=(a,b)
        if k not in self.index:
            if self.limit is not None and len(self.nodes)>=self.limit:raise Resource('tree heap bound')
            self.index[k]=257+len(self.nodes);self.nodes.append(k)
        return self.index[k]
    def head(self,x):
        if type(x) is not int or not 257<=x<257+len(self.nodes):raise ValueError('head requires a cons node')
        return self.nodes[x-257][0]
    def tail(self,x):
        if type(x) is not int or not 257<=x<257+len(self.nodes):raise ValueError('tail requires a cons node')
        return self.nodes[x-257][1]
    def word(self,values):
        out=NIL
        for x in reversed(values):out=self.cons(x,out)
        return out
    def text(self,value):return self.word(value.encode('utf-8','surrogatepass'))
    def natural(self,n):
        out=NIL
        for _ in range(n):out=self.cons(1,out)
        return out

def encode_json(heap,value):
    """Syntax-only adapter; tags distinguish booleans and exact naturals.

    0 object, 1 array, 2 string, 3 natural, 4 negative, 5 bool, 6 null.
    The iterative walk avoids a second native recursion bound. Object order is
    retained, not used to classify a theory or certificate.
    """
    todo=[('visit',value)];values=[]
    while todo:
        op,x=todo.pop()
        if op=='visit':
            if type(x) is dict:
                items=list(x.items());todo.append(('object',[k for k,v in items]));todo.extend(('visit',v) for k,v in reversed(items))
            elif type(x) is list:todo.append(('array',len(x)));todo.extend(('visit',v) for v in reversed(x))
            elif type(x) is str:values.append(heap.cons(2,heap.text(x)))
            elif type(x) is bool:values.append(heap.cons(5,int(x)))
            elif type(x) is int:values.append(heap.cons(3 if x>=0 else 4,heap.natural(abs(x))))
            elif x is None:values.append(heap.cons(6,NIL))
            else:raise ValueError('JSON adapter accepts only exact integer data')
        else:
            n=x if op=='array' else len(x);children=values[-n:] if n else []
            if n:del values[-n:]
            body=heap.word(children) if op=='array' else heap.word([heap.cons(heap.text(k),v) for k,v in zip(x,children)])
            values.append(heap.cons(1 if op=='array' else 0,body))
    if len(values)!=1:raise ValueError('adapter stack')
    return values[0]

class Compiler:
    def __init__(self,source):
        self.heap=Heap();self.constants=[];self.functions=[];tree=ast.parse(source)
        if any(not isinstance(n,ast.FunctionDef) for n in tree.body):raise ValueError('only static function definitions allowed')
        self.names={n.name:i for i,n in enumerate(tree.body)}
        if len(self.names)!=len(tree.body) or set(self.names)&set(PRIMITIVES):raise ValueError('duplicate/reserved function')
        for fn in tree.body:self.function(fn)
    def function(self,fn):
        if fn.decorator_list or fn.args.defaults or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg or fn.args.posonlyargs:
            raise ValueError('ordinary positional functions required')
        self.locals={a.arg:i for i,a in enumerate(fn.args.args)};self.registers=len(self.locals);self.code=[];self.loops=[]
        for s in fn.body:self.statement(s)
        self.emit('const',self.fresh(),self.constant(False));self.emit('return',self.registers-1)
        self.functions.append({'name':fn.name,'arity':len(fn.args.args),'registers':self.registers,'code':self.code})
    def fresh(self):r=self.registers;self.registers+=1;return r
    def emit(self,*op):self.code.append(list(op));return len(self.code)-1
    def constant(self,v):
        if v is None:x=NIL
        elif type(v) is bool:x=int(v)
        elif type(v) is int and 0<=v<=255:x=v
        elif type(v) is str:x=self.heap.text(v)
        else:raise ValueError('only byte atoms, strings, booleans and nil literals')
        if x not in self.constants:self.constants.append(x)
        return self.constants.index(x)
    def expression(self,e):
        if isinstance(e,ast.Name):return self.locals[e.id]
        r=self.fresh()
        if isinstance(e,ast.Constant):self.emit('const',r,self.constant(e.value))
        elif isinstance(e,ast.Call) and isinstance(e.func,ast.Name) and not e.keywords:
            args=[self.expression(a) for a in e.args];name=e.func.id
            if name in PRIMITIVES:
                op,n=PRIMITIVES[name]
                if len(args)!=n:raise ValueError('primitive arity')
                self.emit(op,r,*args)
            elif name in self.names:self.emit('call',r,self.names[name],args)
            else:raise ValueError('unknown static function')
        elif isinstance(e,ast.UnaryOp) and isinstance(e.op,ast.Not):self.emit('not',r,self.expression(e.operand))
        elif isinstance(e,ast.BoolOp):
            end=[]
            for i,v in enumerate(e.values):
                q=self.expression(v);self.emit('move',r,q)
                if i+1<len(e.values):
                    at=self.emit('branch',r,-1,-1);self.code[at][2 if isinstance(e.op,ast.Or) else 3]=len(self.code);end.append((at,3 if isinstance(e.op,ast.Or) else 2))
            for at,slot in end:self.code[at][slot]=len(self.code)
        else:raise ValueError('unsupported static expression '+type(e).__name__)
        return r
    def statement(self,s):
        if isinstance(s,ast.Assign) and len(s.targets)==1 and isinstance(s.targets[0],ast.Name):
            q=self.expression(s.value);name=s.targets[0].id
            if name not in self.locals:self.locals[name]=self.fresh()
            self.emit('move',self.locals[name],q)
        elif isinstance(s,ast.Return):self.emit('return',self.expression(s.value))
        elif isinstance(s,ast.If):
            at=self.emit('branch',self.expression(s.test),-1,-1);self.code[at][3]=len(self.code)
            for t in s.body:self.statement(t)
            jump=self.emit('jump',-1);self.code[at][2]=len(self.code)
            for t in s.orelse:self.statement(t)
            self.code[jump][1]=len(self.code)
        elif isinstance(s,ast.While) and not s.orelse:
            begin=len(self.code);at=self.emit('branch',self.expression(s.test),-1,-1);self.code[at][3]=len(self.code);self.loops.append([])
            for t in s.body:self.statement(t)
            self.emit('jump',begin);end=len(self.code);self.code[at][2]=end
            for j in self.loops.pop():self.code[j][1]=end
        elif isinstance(s,ast.Break) and self.loops:self.loops[-1].append(self.emit('jump',-1))
        else:raise ValueError('unsupported static statement '+type(s).__name__)
    def declaration(self):return {'atom_max':256,'nil':NIL,'nodes':self.heap.nodes,'constants':self.constants,'functions':self.functions}

def fingerprint(declaration):return hashlib.sha256(json.dumps(declaration,separators=(',',':'),sort_keys=True).encode()).hexdigest()

def validate(program):
    """Validate the static instruction grammar, never any proof semantics."""
    def integer(v,lo,hi):return type(v) is int and lo<=v<hi
    if set(program)!={'atom_max','nil','nodes','constants','functions'} or type(program['atom_max']) is not int or program['atom_max']!=256 or type(program['nil']) is not int or program['nil']!=256:
        raise ValueError('tree declaration header')
    heap=Heap(program['nodes']);bound=257+len(heap.nodes)
    if not isinstance(program['constants'],list) or any(not integer(x,0,bound) for x in program['constants']):raise ValueError('constant node')
    fs=program['functions']
    if not isinstance(fs,list) or not fs or fs[0]['name']!='main' or fs[0]['arity']!=1:raise ValueError('one-input main required')
    if len({f['name'] for f in fs})!=len(fs):raise ValueError('duplicate function')
    widths={'const':3,'move':3,'cons':4,'head':3,'tail':3,'pair':3,'atom':4,'succ':3,'not':3,'branch':4,'jump':2,'call':4,'return':2}
    for f in fs:
        if set(f)!={'name','arity','registers','code'} or type(f['name']) is not str or not integer(f['arity'],0,f['registers']+1) or not integer(f['registers'],1,10000000) or not f['code']:
            raise ValueError('function declaration')
        n=f['registers'];code=f['code']
        for ins in code:
            if type(ins) is not list or not ins or ins[0] not in widths or len(ins)!=widths[ins[0]]:raise ValueError('opcode grammar')
            op=ins[0];a=ins[1:]
            reg=lambda x:integer(x,0,n)
            if op=='const':ok=reg(a[0]) and integer(a[1],0,len(program['constants']))
            elif op=='jump':ok=integer(a[0],0,len(code))
            elif op=='branch':ok=reg(a[0]) and all(integer(x,0,len(code)) for x in a[1:])
            elif op=='call':ok=reg(a[0]) and integer(a[1],0,len(fs)) and type(a[2]) is list and len(a[2])==fs[a[1]]['arity'] and all(reg(x) for x in a[2])
            else:ok=all(reg(x) for x in a)
            if not ok:raise ValueError('instruction operand')
    return True

def run(program,heap,input_node,limit=20000000,keep=60):
    start=time.perf_counter();functions=program['functions'];fn=0;pc=0;registers=[NIL]*functions[0]['registers'];registers[0]=input_node
    frames=[];profile=Counter();trace=[];digest=hashlib.sha256();peak=0
    def finish(status,steps,**kw):
        return dict(status=status,steps=steps,event_sha256=digest.hexdigest(),profile=dict(profile),peak_frames=peak,
                    heap_nodes=len(heap.nodes),trace=trace,seconds=time.perf_counter()-start,**kw)
    for step in range(limit):
        instruction=functions[fn]['code'][pc];op,*a=instruction;event=[fn,pc,op];pc+=1
        try:
            if op=='const':registers[a[0]]=program['constants'][a[1]];event.append(registers[a[0]])
            elif op=='move':registers[a[0]]=registers[a[1]];event.append(registers[a[0]])
            elif op=='cons':registers[a[0]]=heap.cons(registers[a[1]],registers[a[2]]);event.append(registers[a[0]])
            elif op in ('head','tail'):registers[a[0]]=getattr(heap,op)(registers[a[1]]);event.append(registers[a[0]])
            elif op=='pair':registers[a[0]]=int(registers[a[1]]>NIL);event.append(registers[a[0]])
            elif op=='atom':registers[a[0]]=int(registers[a[1]]<=NIL and registers[a[2]]<=NIL and registers[a[1]]==registers[a[2]]);event.append(registers[a[0]])
            elif op=='succ':
                v=registers[a[1]]
                if not 0<=v<255:raise ValueError('byte successor requires a byte below 255')
                registers[a[0]]=v+1;event.append(registers[a[0]])
            elif op=='not':
                v=registers[a[1]]
                if v not in (0,1):raise ValueError('Boolean branch value required')
                registers[a[0]]=1-v;event.append(registers[a[0]])
            elif op=='branch':
                v=registers[a[0]]
                if v not in (0,1):raise ValueError('Boolean branch value required')
                pc=a[1+v];event.append(v)
            elif op=='jump':pc=a[0]
            elif op=='call':
                values=[registers[i] for i in a[2]];target=functions[a[1]]
                if len(values)!=target['arity']:raise ValueError('static call arity')
                frames.append((fn,pc,registers,a[0]));fn=a[1];pc=0;registers=values+[NIL]*(target['registers']-len(values));profile[target['name']]+=1;event.append(values)
            elif op=='return':
                value=registers[a[0]];event.append(value)
                if not frames:
                    if len(trace)<keep:trace.append(event)
                    digest.update(json.dumps(event,separators=(',',':')).encode()+b'\n')
                    return finish('accepted' if value==1 else 'rejected',step+1,value=value)
                fn,pc,registers,destination=frames.pop();registers[destination]=value
            else:raise ValueError('unknown tree opcode')
        except Resource as exc:
            return finish('unknown_heap_budget',step,reason=str(exc))
        except (ValueError,IndexError,KeyError) as exc:
            return finish('rejected',step+1,reason='invalid data operation: '+str(exc),function=functions[fn]['name'],pc=pc-1)
        if len(trace)<keep:trace.append(event)
        digest.update(json.dumps(event,separators=(',',':')).encode()+b'\n');peak=max(peak,len(frames))
    return finish('unknown_step_budget',limit)
