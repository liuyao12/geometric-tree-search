"""Compile arbitrary finite string-rewriting proof checks to a finite TM.

Theory: directed finite word rules. Assertion: source =>* target. Certificate:
rule-index, unary position, semicolon, repeated. Theory and target are external
to the certificate. The machine supports arbitrary rule lengths (including
empty words) and a padded word buffer whose capacity is a declared input bound.
Increasing capacity and certificate length is necessary for complete search.
No host-language operation occurs during a compiled transition.
"""
from dataclasses import dataclass
from itertools import product
import wang

@dataclass(frozen=True)
class Theory:
    alphabet:tuple
    rules:tuple
    def __post_init__(self):
        if not isinstance(self.alphabet,tuple) or not isinstance(self.rules,tuple):raise ValueError("immutable theory required")
        if len(set(self.alphabet))!=len(self.alphabet) or any(not isinstance(s,str) for s in self.alphabet):
            raise ValueError("distinct string alphabet symbols required")
        for left,right in self.rules:
            if not isinstance(left,tuple) or not isinstance(right,tuple):raise ValueError("immutable rule words required")
            if any(s not in self.alphabet for s in left+right):raise ValueError("rule uses undeclared symbol")

def check_derivation(theory,source,target,commands,capacity=None):
    """Independent mathematical rewrite semantics, no compiled-machine paths."""
    word=tuple(source);trace=[word]
    if any(s not in theory.alphabet for s in word+tuple(target)):return False,trace
    for rule,position in commands:
        if type(rule) is not int or not 0<=rule<len(theory.rules) or type(position) is not int or position<0:
            return False,trace
        left,right=theory.rules[rule]
        if position>len(word) or word[position:position+len(left)]!=left:return False,trace
        word=word[:position]+right+word[position+len(left):]
        if capacity is not None and len(word)>capacity:return False,trace
        trace.append(word)
    return word==tuple(target),trace

class Builder:
    def __init__(self,alphabet):self.alphabet=tuple(alphabet);self.states=["accept"];self.transitions={};self.serial=0
    def state(self,label):
        self.serial+=1;q=f"q{self.serial}:{label}";self.states.append(q);return q
    def put(self,q,s,out,w,d):
        if (q,s) in self.transitions and self.transitions[q,s]!=(out,w,d):raise ValueError("transition collision")
        self.transitions[q,s]=out,w,d

class ProofMachine:
    def __init__(self,theory,target):
        self.theory=theory;self.target=tuple(target)
        if any(s not in theory.alphabet for s in self.target):raise ValueError("unknown target symbol")
        self.W={s:f"w:{i}" for i,s in enumerate(theory.alphabet)}
        self.C={s:f"c:{i}" for i,s in enumerate(theory.alphabet)}
        self.rules=tuple(f"r:{i}" for i in range(len(theory.rules)))
        alphabet=("B","L","#","$","P","H","X","p",";","_","cP","c#","cH")+tuple(self.W.values())+tuple(self.C.values())+self.rules
        b=Builder(alphabet);self.builder=b
        native=tuple(self.W.values())+("P","#")
        cursor=tuple(self.C.values())+("cP","c#")
        cursor_to_native={**{self.C[s]:self.W[s] for s in theory.alphabet},"cP":"P","c#":"#"}
        def seek_left_L(cont):
            q=b.state("seek-L")
            for s in alphabet:
                if s!="L":b.put(q,s,q,s,-1)
            b.put(q,"L",cont,"L",1);return q
        def seek_cursor(cont):
            q=b.state("seek-cursor")
            for s in alphabet:
                if s in cursor:b.put(q,s,cont,s,0)
                elif s!="L":b.put(q,s,q,s,-1)
            return q
        def seek_separator(cont):
            q=b.state("seek-separator")
            for s in tuple(self.W.values())+tuple(self.C.values())+("P","cP"):
                b.put(q,s,q,s,1)
            for s in ("#","c#"):b.put(q,s,cont,s,1)
            return q
        def mark_cursor(cont):
            q=b.state("mark-cursor")
            for s in theory.alphabet:b.put(q,self.W[s],cont,self.C[s],0)
            b.put(q,"P",cont,"cP",0);b.put(q,"#",cont,"c#",0);return q
        def delete_one(cont):
            q=b.state("delete-at-cursor");first=b.state("delete-first-read");regular=b.state("delete-read")
            advance=b.state("delete-advance");first_end=b.state("delete-first-end");end=b.state("delete-end")
            back=seek_cursor(cont)
            for s in theory.alphabet:
                b.put(q,self.C[s],first,"cH",1)
                wf=b.state("delete-first-write");wr=b.state("delete-write")
                b.put(first,self.W[s],wf,"H",-1);b.put(wf,"cH",advance,self.C[s],1)
                b.put(regular,self.W[s],wr,"H",-1);b.put(wr,"H",advance,self.W[s],1)
            b.put(advance,"H",regular,"H",1)
            for s in ("P","#"):
                b.put(first,s,first_end,s,-1);b.put(regular,s,end,s,-1)
            b.put(first_end,"cH",back,"cP",0);b.put(end,"H",back,"P",-1)
            return q
        def insert_one(symbol,cont):
            q=b.state("insert-at-cursor");after=b.state("advance-insert-cursor")
            mark=mark_cursor(cont);back=seek_cursor(after)
            carry={s:b.state("carry-word") for s in theory.alphabet}
            for s in theory.alphabet:
                b.put(q,self.C[s],carry[s],self.C[symbol],1)
                for t in theory.alphabet:b.put(carry[s],self.W[t],carry[t],self.W[s],1)
                b.put(carry[s],"P",back,self.W[s],-1)
            b.put(q,"cP",back,self.C[symbol],1)
            b.put(after,self.C[symbol],mark,self.W[symbol],1)
            return q
        # Accept only after every certificate byte has been consumed and the
        # rewritten word equals the externally supplied target exactly.
        clean_right=b.state("clean-right");return_L=b.state("return-L")
        for s in alphabet:
            if s!="$":b.put(clean_right,s,clean_right,"B",1)
        b.put(clean_right,"$",return_L,"B",-1)
        b.put(return_L,"B",return_L,"B",-1);b.put(return_L,"L","accept","L",0)
        clean=seek_left_L(clean_right);target_end=b.state("target-end")
        for s in ("P","#"):b.put(target_end,s,clean,s,-1)
        next_target=target_end
        for s in reversed(self.target):
            q=b.state("target-symbol");b.put(q,self.W[s],next_target,self.W[s],1);next_target=q
        target_entry=seek_left_L(next_target)
        read_rule=b.state("read-rule");b.put(read_rule,"X",read_rule,"X",1)
        b.put(read_rule,"_",read_rule,"X",1)  # Explicit unused certificate padding.
        b.put(read_rule,"$",target_entry,"$",-1)
        for i,(left,right) in enumerate(theory.rules):
            scan_position=b.state("read-position")
            finish=b.state("unmark-cursor");to_read=seek_separator(read_rule)
            for s in cursor:b.put(finish,s,to_read,cursor_to_native[s],0)
            rewrite=finish
            for s in reversed(right):rewrite=insert_one(s,rewrite)
            for _ in left:rewrite=delete_one(rewrite)
            if left:
                to_rewrite=seek_cursor(rewrite);matching=to_rewrite
                for j in range(len(left)-1,-1,-1):
                    q=b.state("match-left");s=left[j]
                    token=self.C[s] if j==0 else self.W[s]
                    b.put(q,token,matching,token,-1 if j==len(left)-1 and j else (0 if len(left)==1 else 1))
                    matching=q
                entry_match=matching
            else:entry_match=rewrite
            advance=b.state("advance-position-cursor");to_scan=seek_separator(scan_position)
            mark_next=mark_cursor(to_scan)
            for s in theory.alphabet:b.put(advance,self.C[s],mark_next,self.W[s],1)
            b.put(scan_position,"X",scan_position,"X",1)
            b.put(scan_position,"p",seek_cursor(advance),"X",-1)
            b.put(scan_position,";",seek_cursor(entry_match),"X",-1)
            setup=mark_cursor(to_scan);b.put(read_rule,self.rules[i],seek_left_L(setup),"X",-1)
        self.start=b.state("start");b.put(self.start,"#",read_rule,"#",1)
        self.compiler=wang.Compiler(alphabet,tuple(b.states),b.transitions,"accept")
    def certificate_tokens(self,commands):
        if any(type(r) is not int or not 0<=r<len(self.rules) or type(pos) is not int or pos<0 for r,pos in commands):
            raise ValueError("invalid command")
        return tuple(token for r,pos in commands for token in (self.rules[r],)+("p",)*pos+(";",))
    def parse_certificate(self,tokens):
        commands=[];i=0
        while i<len(tokens):
            if tokens[i]=="_":i+=1;continue
            if tokens[i] not in self.rules:raise ValueError("rule token expected")
            r=self.rules.index(tokens[i]);i+=1;position=0
            while i<len(tokens) and tokens[i]=="p":position+=1;i+=1
            if i==len(tokens) or tokens[i]!=";":raise ValueError("command terminator expected")
            i+=1;commands.append((r,position))
        return commands
    def initial(self,source,capacity,tokens):
        source=tuple(source)
        if type(capacity) is not int or capacity<max(len(source),len(self.target)):
            raise ValueError("word buffer too small for statement")
        if any(s not in self.theory.alphabet for s in source):raise ValueError("unknown source symbol")
        if any(t not in self.rules+("p",";","_") for t in tokens):raise ValueError("invalid certificate alphabet")
        return ("B","B","L")+tuple(self.W[s] for s in source)+("P",)*(capacity-len(source))+(wang.head(self.start,"#"),)+tuple(tokens)+("$","B","B")
    def pattern(self,source,capacity,certificate_length):
        example=self.initial(source,capacity,(";",)*certificate_length)
        first=4+capacity;last=first+certificate_length
        return tuple(self.rules+("p",";","_") if first<=i<last else (s,) for i,s in enumerate(example))
    def accepting_row(self,width):return ("B","B",wang.head("accept","L"))+("B",)*(width-3)
    def run(self,source,capacity,tokens,step_limit=100000):
        row=self.initial(source,capacity,tokens);rows=[row]
        for _ in range(step_limit):
            if any(isinstance(s,tuple) and s[1]=="accept" for s in row):
                assert row==self.accepting_row(len(row));return {"status":"accept","rows":rows,"steps":len(rows)-1}
            try:row=wang.direct_step(self.compiler,row)
            except (ValueError,KeyError):return {"status":"reject","rows":rows,"steps":len(rows)-1}
            rows.append(row)
        return {"status":"unknown_step_budget","rows":rows,"steps":len(rows)-1}

def tm_theory(compiler):
    """General TM acceptance -> finite directed word-reachability reduction.

    Configuration: L, left tape, q-state, scanned symbol, right tape, R.
    Exactly one state marker is preserved until accepting cleanup. Rules for
    border moves extend blank tape. Cleanup is enabled only at the halt state.
    """
    if not compiler.alphabet or len(set(compiler.alphabet))!=len(compiler.alphabet) or any(isinstance(s,tuple) for s in compiler.alphabet):
        raise ValueError("distinct non-head tape symbols required")
    if len(set(compiler.states))!=len(compiler.states) or compiler.halt not in compiler.states:raise ValueError("invalid states")
    for (q,a),(next_q,write,direction) in compiler.transitions.items():
        if q not in compiler.states or a not in compiler.alphabet or next_q not in compiler.states or write not in compiler.alphabet or direction not in (-1,0,1):
            raise ValueError("invalid transition")
    tape={s:f"a:{i}" for i,s in enumerate(compiler.alphabet)}
    states={q:f"s:{i}" for i,q in enumerate(compiler.states)}
    blank=compiler.alphabet[0];rules=[]
    for (q,a),(next_q,write,direction) in compiler.transitions.items():
        if q==compiler.halt:continue
        if direction==0:rules.append(((states[q],tape[a]),(states[next_q],tape[write])))
        elif direction==1:
            for c in compiler.alphabet:rules.append(((states[q],tape[a],tape[c]),(tape[write],states[next_q],tape[c])))
            rules.append(((states[q],tape[a],"R"),(tape[write],states[next_q],tape[blank],"R")))
        elif direction==-1:
            for c in compiler.alphabet:rules.append(((tape[c],states[q],tape[a]),(states[next_q],tape[c],tape[write])))
            rules.append((("L",states[q],tape[a]),("L",states[next_q],tape[blank],tape[write])))
        else:raise ValueError("invalid head move")
    for s in compiler.alphabet:
        rules.append(((states[compiler.halt],tape[s]),(states[compiler.halt],)))
        rules.append(((tape[s],states[compiler.halt]),(states[compiler.halt],)))
    rules.append((("L",states[compiler.halt],"R"),("ACCEPT",)))
    theory=Theory(("L","R","ACCEPT")+tuple(tape.values())+tuple(states.values()),tuple(rules))
    def encode(row):
        if sum(isinstance(s,tuple) for s in row)!=1 or any(s not in compiler.symbols for s in row):raise ValueError("one valid configuration head required")
        word=["L"]
        for s in row:
            if isinstance(s,tuple):word.extend((states[s[1]],tape[s[2]]))
            else:word.append(tape[s])
        return tuple(word+["R"])
    return theory,encode
