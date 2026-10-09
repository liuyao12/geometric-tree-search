"""Fixed literal interpreter with signed binary displacements and bounded scratch.

Program, input and capacities are data; none enters table construction. The
binary scratch counter is erased and all program marks restored at each fetch.
Direct marker seeks also differ from the historical unary machine, so timing
comparisons concern these two complete representations, not addressing alone.
"""
import hashlib
import json
import time
import wang
from rewrite_machine import Builder
from stack_program import bits,OPCODES
from binary_program import encode,workspace

class BinaryMachine:
    def __init__(self):
        ops=tuple(OPCODES.values()); active={s:'@'+s for s in ops if s not in ('H','R')}
        target={s:'t'+s for s in ops}; cursor={'0':'c0','1':'c1',',':'c,',';':'c;'}
        alphabet=('B','L','A','Ar','Al','#','|','$','P','0','1',',',';','<','>','n','d<','d>')+ops+tuple(active.values())+tuple(target.values())+tuple(cursor.values())
        b=Builder(alphabet); self.builder=b; self.active=active; self.target=target; self.cursor=cursor
        reject='reject'; space='space-bound'; work_bound='workspace-bound'; b.states.extend((reject,space,work_bound))
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
        # Copy the selected operand into a bit-prefix scratch counter.
        # Program bits retain their value; a single cursor locates the next bit.
        copy_bit=b.state('copy-address-bit'); next_cursor=b.state('next-address-bit')
        restore_cursor=b.state('restore-copy-cursor')
        for bit in ('0','1'): b.put(restore_cursor,cursor[bit],next_cursor,bit,1)
        return_cursor=find((cursor['0'],cursor['1']),restore_cursor,-1)
        def forward_work(cont):
            q=b.state('seek-work')
            for s in alphabet:
                if s in ('A','Ar','Al'): b.put(q,s,cont,s,1)
                elif s not in ('B','$'): b.put(q,s,q,s,1)
            return q
        for bit in ('0','1'):
            append=b.state('append-counter-bit')
            for s in ('0','1'): b.put(append,s,append,s,1)
            b.put(append,'P',return_cursor,bit,0)
            b.put(append,'#',work_bound,'#',0)
            b.put(copy_bit,cursor[bit],forward_work(append),cursor[bit],0)
            b.put(next_cursor,bit,copy_bit,cursor[bit],0)
        # Signed displacement starts at the active instruction, not record zero.
        finish_target=b.state('restore-target-opcode')
        for symbol,t in target.items(): b.put(finish_target,t,fetch,symbol,0)
        find_target=seek_L(find(tuple(target.values()),finish_target))
        restore_end=b.state('restore-address-end')
        for symbol in (',',';'): b.put(restore_end,cursor[symbol],find_target,symbol,0)
        return_end=find((cursor[','],cursor[';']),restore_end,-1)
        restore_work=b.state('restore-work-delimiter')
        for symbol in alphabet:
            if symbol in ('Ar','Al'): b.put(restore_work,symbol,return_end,'A',-1)
            elif symbol not in ('B','L'): b.put(restore_work,symbol,restore_work,symbol,-1)
        clear=b.state('erase-counter')
        for symbol in ('0','1'): b.put(clear,symbol,clear,'P',1)
        for symbol in ('P','#'): b.put(clear,symbol,restore_work,symbol,-1)
        clear_start=seek_L(forward_work(clear))
        test_work=b.state('seek-counter-mode')
        for symbol in alphabet:
            if symbol not in ('A','Ar','Al','B','$'): b.put(test_work,symbol,test_work,symbol,1)
        advance_right=b.state('advance-right-target'); scan_record=b.state('skip-right-record'); next_opcode=b.state('mark-right-target')
        for symbol,t in target.items(): b.put(advance_right,t,scan_record,symbol,1)
        for symbol in alphabet:
            if symbol in (';','c;'): b.put(scan_record,symbol,next_opcode,symbol,1)
            elif symbol not in ('A','Ar','Al','B','$'): b.put(scan_record,symbol,scan_record,symbol,1)
        for symbol,t in target.items(): b.put(next_opcode,symbol,test_work,t,0)
        b.put(next_opcode,'A',reject,'A',0)
        advance_left=b.state('advance-left-target'); prior_end=b.state('prior-record-end'); prior_body=b.state('prior-record-body'); prior_opcode=b.state('mark-left-target')
        for symbol,t in target.items(): b.put(advance_left,t,prior_end,symbol,-1)
        for symbol in (';','c;'): b.put(prior_end,symbol,prior_body,symbol,-1)
        b.put(prior_end,'L',reject,'L',0)
        for symbol in alphabet:
            if symbol in (';','c;','L'): b.put(prior_body,symbol,prior_opcode,symbol,1)
            elif symbol not in ('A','Ar','Al','B','$'): b.put(prior_body,symbol,prior_body,symbol,-1)
        for symbol,t in target.items(): b.put(prior_opcode,symbol,test_work,t,0)
        for direction,mode,advance in (('right','Ar',advance_right),('left','Al',advance_left)):
            counter=b.state('counter-zero-'+direction); tail=b.state('counter-tail-'+direction); borrow=b.state('counter-borrow-'+direction)
            b.put(test_work,mode,counter,mode,1)
            for symbol in ('P','#'): b.put(counter,symbol,clear_start,symbol,0)
            b.put(counter,'0',counter,'0',1); b.put(counter,'1',tail,'1',0)
            for symbol in ('0','1'): b.put(tail,symbol,tail,symbol,1)
            for symbol in ('P','#'): b.put(tail,symbol,borrow,symbol,-1)
            b.put(borrow,'0',borrow,'1',-1); b.put(borrow,'1',find(tuple(target.values()),advance,-1),'0',0)
        remove_active=b.state('mark-current-target')
        for symbol,asymbol in active.items(): b.put(remove_active,asymbol,test_work,target[symbol],0)
        return_active=find(tuple(active.values()),remove_active,-1)
        for symbol in (',',';'): b.put(next_cursor,symbol,return_active,cursor[symbol],0)
        first_bit=b.state('mark-first-address-bit')
        for bit in ('0','1'): b.put(first_bit,bit,copy_bit,cursor[bit],0)
        restore_direction=b.state('restore-direction-cursor')
        for symbol in ('<','>'): b.put(restore_direction,'d'+symbol,first_bit,symbol,1)
        return_direction=find(('d<','d>'),restore_direction,-1)
        choose_operand=b.state('choose-signed-operand')
        for symbol,mode in (('<','Al'),('>','Ar')):
            mark_mode=b.state('mark-address-direction')
            b.put(mark_mode,'A',return_direction,mode,0)
            b.put(choose_operand,symbol,find(('A',),mark_mode,1),'d'+symbol,0)
        # Explicit next links skip the address counter and preserve program data.
        next_body=b.state('skip-next-link-record'); next_fetch=b.state('fetch-next-link')
        for symbol in alphabet:
            if symbol==';': b.put(next_body,symbol,next_fetch,symbol,1)
            elif symbol not in ('A','B','$'): b.put(next_body,symbol,next_body,symbol,1)
        for symbol in ops: b.put(next_fetch,symbol,fetch,symbol,0)
        b.put(next_fetch,'A',reject,'A',0)
        next_active=b.state('restore-next-link-opcode')
        for symbol,asymbol in active.items(): b.put(next_active,asymbol,next_body,symbol,1)
        b.put(choose_operand,'n',find(tuple(active.values()),next_active,-1),'n',0)
        # Return from a stack operation to the active instruction, then select
        # its empty / zero / one operand. The operand's cursor survives jumps
        # both to the left and to the right of its original instruction.
        selection={}
        for branch in range(3):
            continuation=choose_operand
            for _ in range(branch):
                skip=b.state('skip-address')
                for s in ('0','1','<','>','n'): b.put(skip,s,skip,s,1)
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
        noargs=b.state('no-operand'); b.put(noargs,';',subsequent,';',1)
        def operand(delimiter,cont):
            begin=b.state('begin-signed-address'); positive=b.state('positive-binary-start'); negative=b.state('negative-binary-start'); zero=b.state('zero-address'); rest=b.state('binary-address-tail'); short=b.state('next-link-end')
            b.put(begin,'>',positive,'>',1); b.put(begin,'<',negative,'<',1); b.put(begin,'n',short,'n',1)
            b.put(positive,'0',zero,'0',1); b.put(positive,'1',rest,'1',1); b.put(negative,'1',rest,'1',1)
            b.put(zero,delimiter,cont,delimiter,1); b.put(short,delimiter,cont,delimiter,1)
            for bit in ('0','1'): b.put(rest,bit,rest,bit,1)
            b.put(rest,delimiter,cont,delimiter,1)
            return begin
        one_address=operand(';',subsequent)
        pop_third=operand(';',subsequent); pop_second=operand(',',pop_third); pop_first=operand(',',pop_second)
        for q in (first,subsequent):
            for opcode in ops:
                cont=noargs if opcode in ('H','R') else pop_first if opcode in ('e','f') else one_address
                b.put(q,opcode,cont,opcode,1)
        native_fetch=b.state('begin-first-instruction')
        for opcode in ops: b.put(native_fetch,opcode,fetch,opcode,0)
        left_bits=b.state('validate-left-bits'); left_pad=b.state('validate-left-padding')
        right_bits=b.state('validate-right-bits'); right_pad=b.state('validate-right-padding')
        work_pad=b.state('validate-empty-workspace')
        b.put(subsequent,'A',work_pad,'A',1); b.put(work_pad,'P',work_pad,'P',1); b.put(work_pad,'#',left_bits,'#',1)
        for q,pad,delimiter,cont in ((left_bits,left_pad,'|',right_bits),(right_bits,right_pad,'$',seek_L(native_fetch))):
            for bit in ('0','1'): b.put(q,bit,q,bit,1)
            b.put(q,'P',pad,'P',1); b.put(q,delimiter,cont,delimiter,1 if delimiter=='|' else -1)
            b.put(pad,'P',pad,'P',1); b.put(pad,delimiter,cont,delimiter,1 if delimiter=='|' else -1)
        start=b.state('start'); b.put(start,'L',first,'L',1); self.start=start
        self.compiler=wang.Compiler(alphabet,tuple(b.states),b.transitions,'accept')

    def declaration(self):
        c=self.compiler
        return dict(alphabet=c.alphabet,states=c.states,halt=c.halt,start=self.start,fetch=self.fetch,
                    transitions=[(q,s,out,w,d) for (q,s),(out,w,d) in sorted(c.transitions.items())],address_format='signed-relative-binary-or-next')

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.declaration(),sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def initial(self,program,left=(),right=(),capacities=(8,8),workspace_capacity=None,next_links=True):
        code=encode(program,next_links); bits(left); bits(right)
        if workspace_capacity is None: workspace_capacity=workspace(program,next_links)
        if type(workspace_capacity) is not int or workspace_capacity<0: raise ValueError('natural workspace capacity required')
        if type(capacities) is not tuple or len(capacities)!=2 or any(type(n) is not int or n<0 for n in capacities): raise ValueError('invalid capacities')
        if len(left)>capacities[0] or len(right)>capacities[1]: raise ValueError('initial stack exceeds capacity')
        return ('B','B',wang.head(self.start,'L'))+tuple(code)+('A',)+('P',)*workspace_capacity+('#',)+tuple(map(str,left))+('P',)*(capacities[0]-len(left))+('|',)+tuple(map(str,right))+('P',)*(capacities[1]-len(right))+('$','B','B')

    def accepting_row(self,width): return ('B','B',wang.head('accept','L'))+('B',)*(width-3)

    def run(self,program,left=(),right=(),capacities=(8,8),limit=2000000,keep_rows=False,workspace_capacity=None,next_links=True):
        if type(limit) is not int or limit<0: raise ValueError('natural step limit required')
        started=time.perf_counter(); workspace_capacity=workspace(program,next_links) if workspace_capacity is None else workspace_capacity; initial=self.initial(program,left,right,capacities,workspace_capacity,next_links)
        tape=list(initial); position,q,symbol=next((i,s[1],s[2]) for i,s in enumerate(tape) if isinstance(s,tuple)); tape[position]=symbol
        code=encode(program,next_links); work_start=4+len(code); left_start=work_start+workspace_capacity+1; right_start=left_start+capacities[0]+1
        offsets={}; offset=3
        for i,record in enumerate(code.split(';')[:-1]): offsets[offset]=i; offset+=len(record)+1
        rows=[initial] if keep_rows else None; boundaries=[]
        def row():
            result=tape.copy(); result[position]=wang.head(q,result[position]); return tuple(result)
        for step in range(limit+1):
            if q==self.fetch:
                if tuple(tape[3:3+len(code)])!=tuple(code): raise AssertionError('program not restored at fetch')
                if tape[3+len(code)]!='A': raise AssertionError('workspace delimiter not restored at fetch')
                if position not in offsets: raise AssertionError('fetch is not at an opcode')
                if any(s!='P' for s in tape[work_start:work_start+workspace_capacity]): raise AssertionError('workspace not erased at fetch')
                def read(start,size):
                    values=tape[start:start+size]; n=next((i for i,v in enumerate(values) if v=='P'),len(values))
                    if any(v not in ('0','1') for v in values[:n]) or any(v!='P' for v in values[n:]): raise AssertionError('bad stack checkpoint')
                    return tuple(map(int,values[:n]))
                boundaries.append(dict(pc=offsets[position],left=read(left_start,capacities[0]),right=read(right_start,capacities[1]),tm_step=step))
            if q in ('accept','reject','space-bound','workspace-bound'):
                status={'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,q); break
            if step==limit: status='unknown_step_budget'; break
            transition=self.compiler.transitions.get((q,tape[position]))
            if transition is None: status='reject'; break
            q,write,direction=transition; tape[position]=write; position+=direction
            if not 0<=position<len(tape): status='unknown_tape_bound'; break
            if keep_rows: rows.append(row())
        result=dict(status=status,steps=step,boundaries=boundaries,seconds=time.perf_counter()-started,
                    width=len(initial),initial=initial,final=row() if 0<=position<len(tape) else None,capacities=capacities,machine_sha256=self.fingerprint(),workspace_capacity=workspace_capacity,next_links=next_links)
        if rows is not None: result['rows']=rows
        if status=='accept' and result['final']!=self.accepting_row(len(initial)): raise AssertionError('accepting cleanup failed')
        return result
