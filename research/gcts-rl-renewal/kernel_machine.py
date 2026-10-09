"""Finite first-order kernel envelopes -> literal TM -> point Wang proofs.

The external catalog bounds *syntax*, not proof length. All supported kernel
instances inside it are compiled, without reading a proof. A Boolean fact tape
remembers which formulas have been proved; certificate symbols select sound
Horn inferences. No host callback runs during a machine transition. Increasing
finite syntax catalogs and certificate/run bounds covers every finite proof
accepted by logic.Kernel. This is relative to that kernel, not a formalized
semantic soundness/completeness theorem or an infinite theory schema checker.
"""
from dataclasses import dataclass
from itertools import product
import logic, wang
from rewrite_machine import Builder

def immutable(value):
    if isinstance(value, list): return tuple(immutable(v) for v in value)
    if isinstance(value, dict): return {k: immutable(v) for k,v in value.items()}
    return value

def size(a):
    if a[0] in ('var','bot'): return 1
    if a[0] in ('fun','pred'): return 1+sum(size(t) for t in a[2])
    if a[0]=='all': return 1+size(a[2])
    return 1+sum(size(t) for t in a[1:])

def latex(a):
    if a[0]=='pred':
        symbol=''.join({'_':r'\_','{':r'\{','}':r'\}','\\':r'\backslash '}.get(c,c) for c in a[1])
        return r'\operatorname{'+symbol+'}'+('('+','.join(logic.latex_term(t) for t in a[2])+')' if a[2] else '')
    if a[0]=='bot':return r'\bot'
    if a[0]=='all':return r'\forall '+a[1]+r'\;('+latex(a[2])+')'
    if a[0]=='not':return r'\neg('+latex(a[1])+')'
    if a[0] in ('imp','and','or'):
        return '('+latex(a[1])+{'imp':r'\Rightarrow ','and':r'\land ','or':r'\lor '}[a[0]]+latex(a[2])+')'
    return logic.latex(a)

@dataclass(frozen=True)
class Inference:
    premises: tuple
    conclusion: int
    witness: dict

class Catalog:
    def __init__(self,kernel,formulas,terms=(),variables=(),templates=()):
        self.kernel=kernel
        self.formulas=tuple(dict.fromkeys(formulas)); self.index={a:i for i,a in enumerate(self.formulas)}
        self.terms=tuple(dict.fromkeys(terms)); self.variables=tuple(dict.fromkeys(variables))
        self.templates=tuple(dict.fromkeys(templates))
        if not self.formulas or any(not isinstance(x,str) for x in self.variables): raise ValueError('invalid syntax catalog')
        for a in self.formulas+self.templates: kernel.formula(a)
        for t in self.terms: kernel.term(t)
        rules=[]
        def add(premises,a,rule,**parameters):
            rules.append(Inference(tuple(self.index[p] for p in premises),self.index[a],
                                   {'formula':a,'rule':rule,**parameters}))
        for a in self.formulas:
            for name,b in kernel.axioms.items():
                if a==b: add((),a,'axiom',name=name)
            if logic.tautology(a): add((),a,'tautology')
            if a[0]=='eq' and a[1]==a[2]: add((),a,'refl')
            if a[0]=='all' and a[1] in self.variables and a[2] in self.index:
                add((a[2],),a,'generalize',variable=a[1])
            if a[0]!='imp': continue
            p,q=a[1:]
            if p in self.index and q in self.index: add((p,a),q,'mp')
            if p[0]=='all':
                for t in self.terms:
                    if q==logic.substitute(p[2],p[1],t):
                        add((),a,'instantiate',universal=p,term=t); break
                x,b=p[1:]
                if b[0]=='imp' and x not in logic.free(b[1]) and q==logic.Imp(b[1],logic.All(x,b[2])):
                    add((),a,'distribute',variable=x,antecedent=b[1],consequent=b[2])
            if p[0]=='eq' and q[0]=='imp':
                found=False
                for x in self.variables:
                    for template in self.templates:
                        if q==logic.Imp(logic.substitute(template,x,p[1]),logic.substitute(template,x,p[2])):
                            add((),a,'eq_subst',variable=x,template=template,left=p[1],right=p[2]); found=True; break
                    if found: break
        self.inferences=tuple(rules)

    def declaration(self):
        return {'functions':self.kernel.functions,'predicates':self.kernel.predicates,'axioms':self.kernel.axioms,
                'formulas':self.formulas,'terms':self.terms,'variables':self.variables,'templates':self.templates}

    @classmethod
    def from_declaration(cls,d):
        d=immutable(d)
        return cls(logic.Kernel(d['functions'],d['predicates'],d['axioms']),d['formulas'],
                   d['terms'],d['variables'],d['templates'])

    def proof(self,commands,target):
        """Independent logical reconstruction; it does not simulate the TM."""
        if target not in self.index: raise ValueError('target outside declared language')
        proved={}; lines=[]
        for r in commands:
            if type(r) is not int or not 0<=r<len(self.inferences): raise ValueError('bad inference id')
            item=self.inferences[r]
            if any(p not in proved for p in item.premises): raise ValueError('premise not yet proved')
            line=dict(item.witness)
            if line['rule']=='mp': line.update(antecedent=proved[item.premises[0]],implication=proved[item.premises[1]])
            if line['rule']=='generalize': line['source']=proved[item.premises[0]]
            lines.append(line); proved[item.conclusion]=len(lines)-1
        if self.index[target] not in proved: raise ValueError('target not proved')
        if not lines or lines[-1]['formula']!=target:
            lines=lines[:proved[self.index[target]]+1]
        if not self.kernel.check(lines,target): raise ValueError('independent kernel rejected the decoded proof')
        return lines

    def commands_for_proof(self,proof,target):
        """Completeness witness for any input proof whose instances are present."""
        if not self.kernel.check(proof,target): raise ValueError('invalid kernel proof')
        commands=[]; proved=set()
        for line in proof:
            a=line['formula']
            if a not in self.index: raise ValueError('proof formula outside language')
            choices=[i for i,r in enumerate(self.inferences) if r.conclusion==self.index[a]
                     and r.witness['rule']==line['rule'] and all(p in proved for p in r.premises)]
            if not choices: raise ValueError('proof instance outside catalog')
            commands.append(choices[0]); proved.add(self.index[a])
        self.proof(commands,target); return tuple(commands)

class KernelMachine:
    def __init__(self,catalog,target):
        if target not in catalog.index: raise ValueError('target outside language')
        self.catalog=catalog; self.target=target
        self.rules=tuple(f'r:{i}' for i in range(len(catalog.inferences)))
        alphabet=('B','L','0','1','#','X','$','_')+self.rules
        b=Builder(alphabet); self.builder=b
        read=b.state('read-inference')
        b.put(read,'X',read,'X',1); b.put(read,'_',read,'X',1)
        def seek_left(cont):
            q=b.state('seek-L')
            for s in alphabet:
                if s!='L': b.put(q,s,q,s,-1)
            b.put(q,'L',cont,'L',1); return q
        def slot(index,cont,write=False):
            q=b.state('fact-slot')
            if write:
                for s in ('0','1'): b.put(q,s,cont,'1',1)
            else: b.put(q,'1',cont,'1',1)
            for _ in range(index):
                previous=b.state('scan-facts')
                for s in ('0','1'): b.put(previous,s,q,s,1)
                q=previous
            return seek_left(q)
        back=b.state('return-to-certificate')
        for s in ('0','1'): b.put(back,s,back,s,1)
        b.put(back,'#',read,'#',1)
        for token,item in zip(self.rules,catalog.inferences):
            entry=slot(item.conclusion,back,write=True)
            for premise in reversed(item.premises): entry=slot(premise,entry)
            b.put(read,token,entry,'X',-1)
        clean=b.state('erase-accepted-workspace'); left=b.state('return-accepting-L')
        for s in alphabet:
            if s!='$': b.put(clean,s,clean,'B',1)
        b.put(clean,'$',left,'B',-1)
        b.put(left,'B',left,'B',-1); b.put(left,'L','accept','L',0)
        b.put(read,'$',slot(catalog.index[target],seek_left(clean)),'$',-1)
        self.start=b.state('start'); b.put(self.start,'#',read,'#',1)
        self.compiler=wang.Compiler(alphabet,tuple(b.states),b.transitions,'accept')

    def tokens(self,commands):
        if any(type(r) is not int or not 0<=r<len(self.rules) for r in commands): raise ValueError('bad command')
        return tuple(self.rules[r] for r in commands)
    def parse(self,tokens):
        out=[]
        for token in tokens:
            if token=='_': continue
            if token not in self.rules: raise ValueError('bad certificate symbol')
            out.append(self.rules.index(token))
        return tuple(out)
    def initial(self,tokens):
        if any(t not in self.rules+('_',) for t in tokens): raise ValueError('bad certificate alphabet')
        return ('B','B','L')+('0',)*len(self.catalog.formulas)+(wang.head(self.start,'#'),)+tuple(tokens)+('$','B','B')
    def pattern(self,length):
        if type(length) is not int or length<0: raise ValueError('invalid certificate length')
        row=self.initial(('_',)*length); start=len(self.catalog.formulas)+4
        return tuple(self.rules+('_',) if start<=i<start+length else (s,) for i,s in enumerate(row))
    def accepting_row(self,width): return ('B','B',wang.head('accept','L'))+('B',)*(width-3)
    def run(self,tokens,limit=100000):
        row=self.initial(tokens); rows=[row]
        for _ in range(limit):
            if any(isinstance(s,tuple) and s[1]=='accept' for s in row):
                if row!=self.accepting_row(len(row)): raise AssertionError('bad accepting normal form')
                return {'status':'accept','steps':len(rows)-1,'rows':rows}
            try: row=wang.direct_step(self.compiler,row)
            except (ValueError,KeyError): return {'status':'reject','steps':len(rows)-1,'rows':rows}
            rows.append(row)
        return {'status':'unknown_step_budget','steps':len(rows)-1,'rows':rows}

def variable_name(rank):
    """Shortlex enumeration of all Python strings, including Unicode names."""
    base=0x110000
    if rank==0: return ''
    rank-=1; length=1; count=base
    while rank>=count: rank-=count; length+=1; count*=base
    chars=[]
    for _ in range(length): chars.append(chr(rank%base)); rank//=base
    return ''.join(reversed(chars))

def compositions(total,n):
    if n==0:
        if total==0: yield ()
        return
    for first in range(1,total-n+2):
        for rest in compositions(total-first,n-1): yield (first,)+rest

def language_stage(kernel,target,bound):
    """Finite, exhaustive syntax envelope. Expensive, but genuinely fair.

    Stage k includes every term/formula with <=k AST nodes and the first k
    variable names, plus names appearing in the externally fixed problem.
    Every finite literal Kernel proof is eventually contained (including its
    substitution templates and terms). This is not an efficient implementation
    of semantic first-order completeness or an axiom-schema enumerator.
    """
    if type(bound) is not int or bound<1: raise ValueError('positive syntax bound required')
    kernel.formula(target)
    variables=tuple(sorted(set().union(logic.names(target),*(logic.names(a) for a in kernel.axioms.values()),
                                      (variable_name(i) for i in range(bound)))))
    terms={n:[] for n in range(1,bound+1)}; formulas={n:[] for n in range(1,bound+1)}
    terms[1].extend(logic.V(x) for x in variables)
    for n in range(1,bound+1):
        for f,arity in kernel.functions.items():
            for sizes in compositions(n-1,arity):
                terms[n].extend(logic.F(f,*args) for args in product(*(terms[s] for s in sizes)))
        formulas[n].extend(('pred',p,args) for p,arity in kernel.predicates.items()
                           for sizes in compositions(n-1,arity) for args in product(*(terms[s] for s in sizes)))
        if n==1: formulas[n].append(('bot',))
        for sizes in compositions(n-1,2):
            formulas[n].extend(logic.Eq(*args) for args in product(*(terms[s] for s in sizes)))
            formulas[n].extend((op,*args) for op in ('imp','and','or') for args in product(*(formulas[s] for s in sizes)))
        if n>1:
            formulas[n].extend(logic.Not(a) for a in formulas[n-1])
            formulas[n].extend(logic.All(x,a) for x in variables for a in formulas[n-1])
    ts=tuple(t for n in terms for t in terms[n]); fs=tuple(a for n in formulas for a in formulas[n])
    # Target need not appear before its size bound; callers skip such stages.
    return Catalog(kernel,fs,ts,variables,fs)
