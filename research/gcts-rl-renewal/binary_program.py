"""Signed relative binary operands and optional next links for two-stack programs.

The original instruction tuples use absolute natural targets. The encoded
record's operand is relative to its own instruction index. An executed target
outside the program rejects; unused signed targets remain legal data.
"""
from stack_program import OPCODES,ARITY,validate

def encode(program,next_links=True):
    validate(program)
    if type(next_links) is not bool: raise ValueError('boolean next-link option required')
    def address(index,n):
        if next_links and n==index+1: return 'n'
        return ('>' if n>=index else '<')+format(abs(n-index),'b')
    return ''.join(OPCODES[item[0]]+','.join(address(i,n) for n in item[1:])+';' for i,item in enumerate(program))

def decode(code):
    if type(code) is not str or not code or not code.endswith(';'): raise ValueError('terminated program required')
    inverse={v:k for k,v in OPCODES.items()}; result=[]
    for index,record in enumerate(code.split(';')[:-1]):
        if not record or record[0] not in inverse: raise ValueError('unknown opcode')
        op=inverse[record[0]]; parts=record[1:].split(',') if ARITY[op] else ()
        if (not ARITY[op] and len(record)!=1) or len(parts)!=ARITY[op]: raise ValueError('bad instruction arity')
        values=[]
        for p in parts:
            if p=='n': values.append(index+1); continue
            if len(p)<2 or p[0] not in '<>' or set(p[1:])-{'0','1'} or (len(p)>2 and p[1]=='0') or p=='<0':
                raise ValueError('canonical signed binary operand required')
            values.append(index+(1 if p[0]=='>' else -1)*int(p[1:],2))
        result.append((op,)+tuple(values))
    return tuple(result)

def workspace(program,next_links=True):
    validate(program)
    if type(next_links) is not bool: raise ValueError('boolean next-link option required')
    return max((max(1,abs(n-i).bit_length()) for i,item in enumerate(program) for n in item[1:] if not next_links or n!=i+1),default=0)
