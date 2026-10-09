"""One literal one-tape interpreter for every two-binary-stack program.

No program/input enters construction of the alphabet, states or transitions.
Unary jump operands are interpreted on tape; temporary marks are restored at
each fetch. Fixed padded stack regions make space a declared experiment bound.
The runner performs only literal read/write/head transitions. Decoding fetch
checkpoints is observation and never decides a transition.
"""
import hashlib
import json
import time
import wang
from rewrite_machine import Builder
from stack_program import encode,bits,OPCODES

class UniformMachine:
    def __init__(self):
        ops=tuple(OPCODES.values()); active={s:'@'+s for s in ops if s not in ('H','R')}
        target={s:'t'+s for s in ops}; cursor={'p':'cp',',':'c,',';':'c;'}
        alphabet=('B','L','#','|','$','P','0','1','p',',',';','x')+ops+tuple(active.values())+tuple(target.values())+tuple(cursor.values())
        b=Builder(alphabet); self.builder=b; self.active=active; self.target=target; self.cursor=cursor
        reject='reject'; space='space-bound'; b.states.extend((reject,space))
        fetch=b.state('fetch-opcode'); self.fetch=fetch
        def seek_L(cont):
            q=b.state('seek-L')
            for s in alphabet:
                if s!='L': b.put(q,s,q,s,-1)
            b.put(q,'L',cont,'L',1); return q
        def find(symbols,cont,direction=1):
            q=b.state('find-marker')
            for s in alphabet:
                if s in symbols: b.put(q,s,cont,s,0)
                elif s not in ('B','$'): b.put(q,s,q,s,direction)
            return q
        # Resolve an operand using a moving target-opcode mark. Read/consume
        # one unary p, advance one instruction, then restore the operand.
        read_cursor=b.state('read-address-cursor'); restore=b.state('restore-address')
        finish_target=b.state('restore-target-opcode')
        for s,t in target.items(): b.put(finish_target,t,fetch,s,0)
        find_target=seek_L(find(tuple(target.values()),finish_target))
        b.put(restore,'x',restore,'p',-1)
        for s in alphabet:
            if s!='x': b.put(restore,s,find_target,s,0)
        for s in (',',';'): b.put(read_cursor,cursor[s],restore,s,-1)
        mark_next_cursor=b.state('advance-address-cursor')
        advance_target=b.state('advance-target'); scan_record=b.state('skip-target-record'); next_opcode=b.state('mark-next-target')
        for s,t in target.items(): b.put(advance_target,t,scan_record,s,1)
        for s in alphabet:
            if s in (';','c;'): b.put(scan_record,s,next_opcode,s,1)
            elif s!='#': b.put(scan_record,s,scan_record,s,1)
        seek_cursor=seek_L(find(tuple(cursor.values()),read_cursor))
        for s,t in target.items(): b.put(next_opcode,s,seek_cursor,t,0)
        b.put(next_opcode,'#',reject,'#',0)
        cursor_advance=seek_L(find(tuple(target.values()),advance_target))
        for s,cs in cursor.items(): b.put(mark_next_cursor,s,cursor_advance,cs,0)
        b.put(read_cursor,'cp',mark_next_cursor,'x',1)
        first_target=b.state('mark-first-target')
        for s,t in target.items(): b.put(first_target,s,seek_cursor,t,0)
        first_jump=seek_L(first_target)
        remove_active=b.state('restore-active-opcode')
        for s,asymbol in active.items(): b.put(remove_active,asymbol,first_jump,s,0)
        return_active=seek_L(find(tuple(active.values()),remove_active))
        choose_operand=b.state('mark-selected-operand')
        for s,cs in cursor.items(): b.put(choose_operand,s,return_active,cs,0)
        # Return from a stack operation to the active instruction, then select
        # its empty / zero / one operand. The operand's cursor survives jumps
        # both to the left and to the right of its original instruction.
        selection={}
        for branch in range(3):
            continuation=choose_operand
            for _ in range(branch):
                skip=b.state('skip-address')
                for s in ('p',): b.put(skip,s,skip,s,1)
                b.put(skip,',',continuation,',',1); continuation=skip
            at_anchor=b.state('select-branch-address')
            for asymbol in active.values(): b.put(at_anchor,asymbol,continuation,asymbol,1)
            selection[branch]=seek_L(find(tuple(active.values()),at_anchor))
        # Push and pop are literal scans of the designated padded region.
        # Separate stack-entry scans per action avoid conflicting exits.
        def stack_scan(index,cont):
            seek=b.state('seek-stack')
            for s in alphabet:
                if s!='#': b.put(seek,s,seek,s,1)
            if index:
                skip=b.state('skip-left-stack')
                for s in ('0','1','P'): b.put(skip,s,skip,s,1)
                b.put(skip,'|',cont,'|',1); b.put(seek,'#',skip,'#',1)
            else: b.put(seek,'#',cont,'#',1)
            return seek
        for opcode,index,bit in (('a',0,'0'),('b',0,'1'),('c',1,'0'),('d',1,'1')):
            scan=b.state('push-bit')
            for s in ('0','1'): b.put(scan,s,scan,s,1)
            b.put(scan,'P',selection[0],bit,0)
            b.put(scan,'|' if index==0 else '$',space,'|' if index==0 else '$',0)
            b.put(fetch,opcode,stack_scan(index,scan),active[opcode],1)
        for opcode,index in (('e',0),('f',1)):
            scan=b.state('pop-scan'); top=b.state('pop-top')
            for s in ('0','1'): b.put(scan,s,scan,s,1)
            for s in ('P','|' if index==0 else '$'): b.put(scan,s,top,s,-1)
            for bit in (0,1): b.put(top,str(bit),selection[1+bit],'P',0)
            delimiter='#' if index==0 else '|'; b.put(top,delimiter,selection[0],delimiter,0)
            b.put(fetch,opcode,stack_scan(index,scan),active[opcode],1)
        b.put(fetch,'g',choose_operand,active['g'],1); b.put(fetch,'R',reject,'R',0)
        # The accepting top is independent of program and input. Record the
        # final stacks at the H fetch before cleanup, then erase the workspace.
        clean=b.state('erase-accepting-workspace'); back=b.state('return-accepting-L')
        for s in alphabet:
            if s!='$': b.put(clean,s,clean,'B',1)
        b.put(clean,'$',back,'B',-1); b.put(back,'B',back,'B',-1); b.put(back,'L','accept','L',0)
        b.put(fetch,'H',seek_L(clean),'H',0)
        # Validate every encoded record and the bit-prefix/padding suffix of
        # both stacks before entering the first program instruction.
        first=b.state('first-program-opcode'); subsequent=b.state('next-program-opcode')
        unary_end=b.state('one-address'); pop_first=b.state('pop-first-address')
        pop_second=b.state('pop-second-address'); pop_third=b.state('pop-third-address'); noargs=b.state('no-operand')
        b.put(unary_end,'p',unary_end,'p',1); b.put(unary_end,';',subsequent,';',1)
        for current,nextq in ((pop_first,pop_second),(pop_second,pop_third)):
            b.put(current,'p',current,'p',1); b.put(current,',',nextq,',',1)
        b.put(pop_third,'p',pop_third,'p',1); b.put(pop_third,';',subsequent,';',1)
        b.put(noargs,';',subsequent,';',1)
        for q in (first,subsequent):
            for opcode in ops:
                cont=noargs if opcode in ('H','R') else pop_first if opcode in ('e','f') else unary_end
                b.put(q,opcode,cont,opcode,1)
        native_fetch=b.state('begin-first-instruction')
        for opcode in ops: b.put(native_fetch,opcode,fetch,opcode,0)
        left_bits=b.state('validate-left-bits'); left_pad=b.state('validate-left-padding')
        right_bits=b.state('validate-right-bits'); right_pad=b.state('validate-right-padding')
        b.put(subsequent,'#',left_bits,'#',1)
        for q,pad,delimiter,cont in ((left_bits,left_pad,'|',right_bits),(right_bits,right_pad,'$',seek_L(native_fetch))):
            for bit in ('0','1'): b.put(q,bit,q,bit,1)
            b.put(q,'P',pad,'P',1); b.put(q,delimiter,cont,delimiter,1 if delimiter=='|' else -1)
            b.put(pad,'P',pad,'P',1); b.put(pad,delimiter,cont,delimiter,1 if delimiter=='|' else -1)
        start=b.state('start'); b.put(start,'L',first,'L',1); self.start=start
        self.compiler=wang.Compiler(alphabet,tuple(b.states),b.transitions,'accept')

    def declaration(self):
        c=self.compiler
        return dict(alphabet=c.alphabet,states=c.states,halt=c.halt,start=self.start,fetch=self.fetch,
                    transitions=[(q,s,out,w,d) for (q,s),(out,w,d) in sorted(c.transitions.items())])

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.declaration(),sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def initial(self,program,left=(),right=(),capacities=(8,8)):
        code=encode(program); bits(left); bits(right)
        if type(capacities) is not tuple or len(capacities)!=2 or any(type(n) is not int or n<0 for n in capacities): raise ValueError('invalid capacities')
        if len(left)>capacities[0] or len(right)>capacities[1]: raise ValueError('initial stack exceeds capacity')
        return ('B','B',wang.head(self.start,'L'))+tuple(code)+('#',)+tuple(map(str,left))+('P',)*(capacities[0]-len(left))+('|',)+tuple(map(str,right))+('P',)*(capacities[1]-len(right))+('$','B','B')

    def accepting_row(self,width): return ('B','B',wang.head('accept','L'))+('B',)*(width-3)

    def run(self,program,left=(),right=(),capacities=(8,8),limit=2000000,keep_rows=False):
        if type(limit) is not int or limit<0: raise ValueError('natural step limit required')
        started=time.perf_counter(); initial=self.initial(program,left,right,capacities)
        tape=list(initial); position,q,symbol=next((i,s[1],s[2]) for i,s in enumerate(tape) if isinstance(s,tuple)); tape[position]=symbol
        code=encode(program); left_start=4+len(code); right_start=left_start+capacities[0]+1
        offsets={}; offset=3
        for i,record in enumerate(code.split(';')[:-1]): offsets[offset]=i; offset+=len(record)+1
        rows=[initial] if keep_rows else None; boundaries=[]
        def row():
            result=tape.copy(); result[position]=wang.head(q,result[position]); return tuple(result)
        for step in range(limit+1):
            if q==self.fetch:
                if tuple(tape[3:3+len(code)])!=tuple(code): raise AssertionError('program not restored at fetch')
                if position not in offsets: raise AssertionError('fetch is not at an opcode')
                def read(start,size):
                    values=tape[start:start+size]; n=next((i for i,v in enumerate(values) if v=='P'),len(values))
                    if any(v not in ('0','1') for v in values[:n]) or any(v!='P' for v in values[n:]): raise AssertionError('bad stack checkpoint')
                    return tuple(map(int,values[:n]))
                boundaries.append(dict(pc=offsets[position],left=read(left_start,capacities[0]),right=read(right_start,capacities[1]),tm_step=step))
            if q in ('accept','reject','space-bound'):
                status='unknown_space_bound' if q=='space-bound' else q; break
            if step==limit: status='unknown_step_budget'; break
            transition=self.compiler.transitions.get((q,tape[position]))
            if transition is None: status='reject'; break
            q,write,direction=transition; tape[position]=write; position+=direction
            if not 0<=position<len(tape): status='unknown_tape_bound'; break
            if keep_rows: rows.append(row())
        result=dict(status=status,steps=step,boundaries=boundaries,seconds=time.perf_counter()-started,
                    width=len(initial),initial=initial,final=row() if 0<=position<len(tape) else None,capacities=capacities,machine_sha256=self.fingerprint())
        if rows is not None: result['rows']=rows
        if status=='accept' and result['final']!=self.accepting_row(len(initial)): raise AssertionError('accepting cleanup failed')
        return result
