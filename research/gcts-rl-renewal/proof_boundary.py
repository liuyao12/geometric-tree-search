"""A free proof boundary assembled by finite symbol operations.

The fixed band contains three tagged trees (protocol, theory, target). The
free band contains two trees (blocks, proof). Postfix atoms have nine bits;
cons has one bit. Neither band supplies node IDs, heap records or code.
Every constructor goes through the existing literal canonical-cons routine.
"""
from tree_machine import Heap,encode_json
from tape_tree_machine import Lowering,RAW,bits
from pathlib import Path
from tree_machine import Compiler

KEYS=('protocol','theory','target','blocks','proof')

def boundary_program():
    here=Path(__file__).resolve().parent
    source=(here/'boundary_syntax.tree').read_text()+(here/'fol_checker.tree').read_text().replace('def main(request):','def semantic_main(request):',1)
    return Compiler(source).declaration()

def decoded_heap(word):
    nodes=[]
    for i,record in enumerate(word.split(';')[:-1]):
        label,children=record.split(':');a,c=children.split(',')
        if int(label[::-1],2)!=257+i:raise ValueError('heap label')
        nodes.append([int(a[::-1],2),int(c[::-1],2)])
    return nodes

def tree_word(nodes,root):
    todo=[root];out=[]
    while todo:
        x=todo.pop()
        if x==-1:out.append('1');continue
        if x<=256:out.append('0'+bits(x).ljust(9,'0'))
        else:
            a,c=nodes[x-257];todo.extend((-1,c,a))
    return ''.join(out)

def value_word(value):
    h=Heap();root=encode_json(h,value);return tree_word(h.nodes,root)

def boundary_words(request):
    return (''.join(value_word(request[k]) for k in KEYS[:3])+';',
            ''.join(value_word(request[k]) for k in KEYS[3:])+';')

class BoundaryLowering(Lowering):
    def __init__(self,program):
        super().__init__(program);b=self.b;old_start=self.start
        self.problem=self.tapes;self.certificate=self.tapes+1;self.values=self.tapes+2
        self.value=self.tapes+3;self.left=self.tapes+4;self.right=self.tapes+5
        self.fields=list(range(self.tapes+6,self.tapes+11))
        self.key=self.tapes+11;self.row=self.tapes+12;self.body=self.tapes+13
        self.tapes+=14
        h=Heap(program['nodes']);self.key_nodes=[h.text(k) for k in KEYS];self.boot_nodes=list(h.nodes)
        self.old_start=old_start

        # Build a tagged object from five exactly popped values. The keys are
        # fixed machine constants, not supplied by the certificate boundary.
        root_slot=self.alloc[0]['slots'][0]
        q=self.cons(root_slot,self.key,self.body,old_start)
        q=b.constant(self.key,0,q)
        for key,field in zip(self.key_nodes,self.fields):
            q=self.cons(self.body,self.row,self.body,q)
            q=self.cons(self.row,self.key,field,q)
            q=b.constant(self.key,key,q)
        q=b.constant(self.body,256,q)
        empty=b.row(self.values,{'^':[q,'^',1]},'boundary-empty-stack')
        q=b.advance(self.values,empty,-1)
        for field in self.fields[3:]:q=self.pop(field,q)
        self.finish=q
        self.certificate_start=self.parse_band(self.certificate,self.finish)
        # Freeze the three assertion values in separate bands and reset the
        # value stack before any free command can run. A cons command on an
        # empty free stack now rejects even if later commands add five trees.
        empty=b.row(self.values,{'^':[self.certificate_start,'^',1]},'boundary-fixed-stack-empty')
        fixed=b.advance(self.values,empty,-1)
        for field in self.fields[:3]:fixed=self.pop(field,fixed)
        self.start=self.parse_band(self.problem,fixed)

    def push(self,done):
        b=self.b;loop=b.state('boundary-push')
        end=b.symbol(self.values,';',done)
        choices={'^':[end,'^',0]}
        for bit in ('0','1'):
            back=b.advance(self.value,loop,-1)
            put=b.row(self.values,{'B':[back,bit,1]},'boundary-push-bit')
            choices[bit]=[put,bit,0]
        b.put(loop,self.value,choices)
        return b.rewind(self.value,b.end(self.value,b.advance(self.value,loop,-1)))

    def pop(self,destination,done):
        b=self.b;loop=b.state('boundary-pop')
        end=b.advance(self.values,b.rewind(destination,done),1)
        choices={s:[end,s,0] for s in ('^',';')}
        for bit in ('0','1'):
            back=b.advance(self.values,loop,-1)
            put=b.row(destination,{'B':[back,bit,1]},'boundary-pop-bit')
            choices[bit]=[put,'B',0]
        b.put(loop,self.values,choices)
        delimiter=b.row(self.values,{';':[loop,'B',-1]},'boundary-pop-delimiter')
        return b.clear(destination,b.advance(self.values,delimiter,-1))

    def parse_band(self,tape,done):
        b=self.b;loop=b.state('boundary-token')
        pushed=self.push(loop)
        constructed=self.cons(self.value,self.left,self.right,pushed)
        cons=self.pop(self.right,self.pop(self.left,constructed))
        # A finite nine-bit decision tree rejects atom values above nil.
        def atom(prefix):
            if len(prefix)==9:
                n=int(prefix[::-1],2)
                return b.constant(self.value,n,pushed) if n<=256 else self.reject
            q=b.state('boundary-atom-bit')
            b.put(q,tape,{s:[atom(prefix+s),s,1] for s in ('0','1')});return q
        parsed=atom('')
        # After the delimiter, only padding is allowed. This rejects an early
        # terminator followed by data, without trusting a host length parser.
        tail=b.state('boundary-padding')
        at_end=b.row(tape,{'^':[done,'^',1]},'boundary-rewind-end')
        rewind=b.state('boundary-rewind')
        b.put(rewind,tape,{s:[at_end if s=='^' else rewind,s,0 if s=='^' else -1] for s in RAW})
        # The physical lowering reports unknown if padding reaches #. Avoid
        # walking to that bound by placing a second, fixed end delimiter.
        b.put(tail,tape,{'B':[tail,'B',1],':':[rewind,':',-1]})
        b.put(loop,tape,{'0':[parsed,'0',1],'1':[cons,'1',1],';':[tail,';',1]})
        return loop

    def initial_boundary(self,problem,certificate,heap_padding=65536,stack_capacity=32768,word_capacity=64):
        initial=super().initial({'node':256,'nodes':self.boot_nodes},word_capacity,heap_padding,stack_capacity)
        # Each finite band ends with ':' after the chosen payload/padding.
        for t,w in ((self.problem,problem),(self.certificate,certificate)):
            initial['words'][t]=w+':';initial['capacities'][t]=len(w)+3
        initial['capacities'][self.values]=stack_capacity
        return initial

    def declaration(self):
        d=super().declaration();d['boundary']=dict(problem=self.problem,certificate=self.certificate,values=self.values,
            value=self.value,left=self.left,right=self.right,fields=self.fields,key=self.key,row=self.row,body=self.body,
            old_start=self.old_start,key_nodes=self.key_nodes,boot_nodes=self.boot_nodes,
            wire='0 followed by nine little-endian bits for an atom 0..256; 1 for cons; ; terminates; : is fixed frame end')
        return d
