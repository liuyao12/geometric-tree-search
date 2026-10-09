"""Two binary stacks and finite programs, with a general TM data compiler.

This is the operational reference, not the literal interpreter. Stack top is
the last bit; empty pop selects its first branch without adding a bit. An
out-of-range executed PC rejects; unreachable dangling targets are allowed.
Programs and inputs are data. Explicit finite capacities/steps return unknown.
"""
from dataclasses import dataclass

OPCODES={'pushL0':'a','pushL1':'b','pushR0':'c','pushR1':'d',
         'popL':'e','popR':'f','jump':'g','accept':'H','reject':'R'}
ARITY={name:0 if name in ('accept','reject') else 3 if name in ('popL','popR') else 1 for name in OPCODES}

def validate(program):
    if type(program) is not tuple or not program: raise ValueError('nonempty immutable program required')
    for item in program:
        if type(item) is not tuple or not item or type(item[0]) is not str or item[0] not in ARITY or len(item)!=ARITY[item[0]]+1:
            raise ValueError('malformed instruction')
        if any(type(n) is not int or n<0 for n in item[1:]): raise ValueError('natural-number address required')
    return program

def encode(program):
    validate(program)
    return ''.join(OPCODES[item[0]]+','.join('p'*n for n in item[1:])+';' for item in program)

def decode(code):
    if type(code) is not str or not code: raise ValueError('program bytes required')
    inverse={v:k for k,v in OPCODES.items()}; result=[]
    for record in code.split(';')[:-1]:
        if not record or record[0] not in inverse: raise ValueError('unknown opcode')
        op=inverse[record[0]]; parts=record[1:].split(',') if ARITY[op] else ()
        if (not ARITY[op] and len(record)!=1) or len(parts)!=ARITY[op] or any(set(p)-{'p'} for p in parts):
            raise ValueError('bad operand syntax')
        result.append((op,)+tuple(len(p) for p in parts))
    if not code.endswith(';'): raise ValueError('unterminated instruction')
    return validate(tuple(result))

def bits(word):
    if type(word) is not tuple or any(type(b) is not int or b not in (0,1) for b in word): raise ValueError('binary immutable stack required')
    return word

def run(program,left=(),right=(),capacities=None,limit=10000):
    if type(limit) is not int or limit<0: raise ValueError('natural step limit required')
    validate(program); left=list(bits(left)); right=list(bits(right)); pc=0; trace=[]
    if capacities is not None:
        if type(capacities) is not tuple or len(capacities)!=2 or any(type(n) is not int or n<0 for n in capacities):
            raise ValueError('two natural capacities required')
        if len(left)>capacities[0] or len(right)>capacities[1]: raise ValueError('initial stack exceeds declared capacity')
    for step in range(limit):
        state=dict(pc=pc,left=tuple(left),right=tuple(right)); trace.append(state)
        if not 0<=pc<len(program): return dict(status='reject',reason='executed address outside program',trace=trace,steps=step)
        op,*args=program[pc]
        if op in ('accept','reject'): return dict(status=op,trace=trace,steps=step+1)
        if op=='jump': pc=args[0]; continue
        stack=left if op[4:5]=='L' or op=='popL' else right
        if op.startswith('push'):
            index=0 if op[4]=='L' else 1
            if capacities is not None and len(stack)==capacities[index]:
                return dict(status='unknown_space_bound',trace=trace,steps=step)
            stack.append(int(op[-1])); pc=args[0]
        else: pc=args[0] if not stack else args[1+stack.pop()]
    return dict(status='unknown_step_budget',trace=trace,steps=limit)

class Assembly:
    def __init__(self): self.instructions=[]; self.labels={}
    def mark(self,name):
        if name in self.labels: raise ValueError('duplicate label')
        self.labels[name]=len(self.instructions)
    def emit(self,op,*args): self.instructions.append((op,)+args)
    def finish(self):
        return validate(tuple((op,)+tuple(self.labels[a] if isinstance(a,str) else a for a in args)
                              for op,*args in self.instructions))

def equality_program():
    return (('popL',1,2,3),('popR',4,5,5),('popR',5,0,5),('popR',5,5,0),('accept',),('reject',))

@dataclass
class Translation:
    program:tuple
    width:int
    alphabet:tuple
    entries:dict
    def input(self,row):
        heads=[(i,s) for i,s in enumerate(row) if isinstance(s,tuple)]
        if len(heads)!=1: raise ValueError('single source head required')
        i,(_,q,a)=heads[0]
        if q not in self.entries or any(s not in self.alphabet for s in row if not isinstance(s,tuple)) or a not in self.alphabet:
            raise ValueError('invalid source configuration')
        def pack(symbols):
            return tuple(bit for s in symbols for bit in reversed(tuple(int(c) for c in format(self.alphabet.index(s),'0'+str(self.width)+'b'))))
        # Right stack has current symbol on top; left stack has nearest left
        # symbol on top. Code bits are popped most significant first.
        left=pack(row[:i]); right=pack(tuple(reversed(tuple(row[i+1:])))+(a,))
        # A data jump chooses the requested source state. Its entry address
        # remains a program operand; the interpreter is unchanged.
        if q!=next(iter(self.entries)): raise ValueError('input must start in the compiled start state')
        return left,right

def compile_tm(compiler,start):
    """Finite TM table -> finite two-stack program, all symbol widths.

    Blank is alphabet[0], encoded by all zero bits. An empty whole-block read
    therefore yields blank. At source-state entries both stack lengths are
    multiples of the code width. Intermediate bit prefixes are not source
    configurations. This is a constructive algorithm, not a formal proof.
    """
    alphabet=tuple(compiler.alphabet); states=tuple(compiler.states)
    if not alphabet or len(set(alphabet))!=len(alphabet) or any(type(s) is not str for s in alphabet): raise ValueError('string alphabet required')
    if len(set(states))!=len(states) or any(type(q) is not str for q in states) or start not in states or compiler.halt not in states: raise ValueError('invalid states')
    for (q,a),(out,w,d) in compiler.transitions.items():
        if q not in states or out not in states or a not in alphabet or w not in alphabet or type(d) is not int or d not in (-1,0,1): raise ValueError('invalid transition')
    width=max(1,(len(alphabet)-1).bit_length()); assembly=Assembly(); serial=0
    # Put start first, independently of state declaration order.
    order=(start,)+tuple(q for q in states if q!=start); entries={}
    def fresh():
        nonlocal serial
        serial+=1; return 'internal:'+str(serial)
    def push_word(stack,index,continuation):
        code=format(index,'0'+str(width)+'b'); labels=[fresh() for _ in code]
        for j,bit in enumerate(reversed(code)):
            assembly.mark(labels[j]); assembly.emit('push'+stack+bit,labels[j+1] if j+1<len(labels) else continuation)
        return labels[0]
    def read_word(stack,handlers,prefix=''):
        label=fresh(); assembly.mark(label)
        if len(prefix)==width:
            handlers(int(prefix,2)); return label
        zero=fresh(); one=fresh()
        assembly.emit('pop'+stack,zero,zero,one)
        assembly.mark(zero); zero_entry=read_word(stack,handlers,prefix+'0')
        # The label is at the next read instruction. No host read occurs.
        if assembly.labels[zero]!=assembly.labels[zero_entry]: raise AssertionError('bad read entry')
        assembly.mark(one); one_entry=read_word(stack,handlers,prefix+'1')
        if assembly.labels[one]!=assembly.labels[one_entry]: raise AssertionError('bad read entry')
        return label
    for q in order:
        label='state:'+q; assembly.mark(label); entries[q]=assembly.labels[label]
        if q==compiler.halt: assembly.emit('accept'); continue
        def handle(index,q=q):
            if index>=len(alphabet) or (q,alphabet[index]) not in compiler.transitions:
                assembly.emit('reject'); return
            out,w,d=compiler.transitions[q,alphabet[index]]; destination='state:'+out; wi=alphabet.index(w)
            if d!=-1:
                push_word('L' if d==1 else 'R',wi,destination)
            else:
                # Push written current to the right, read previous left, then
                # push its symbol to the right as the newly scanned symbol.
                read_left=fresh(); push_word('R',wi,read_left); assembly.mark(read_left)
                def left_handler(li):
                    if li>=len(alphabet): assembly.emit('reject'); return
                    push_word('R',li,destination)
                read_word('L',left_handler)
        read_word('R',handle)
    program=assembly.finish()
    return Translation(program,width,alphabet,entries)
