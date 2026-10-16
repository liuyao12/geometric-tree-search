"""Small certificate kernel for classical first-order logic with equality.

Closed theory axioms, propositional tautologies, universal instantiation and
distribution, equality substitution, modus ponens, and generalization. Terms
and formulas are immutable tagged tuples. Search is deliberately separate:
the current proposer is bounded forward equational rewriting, not a complete
first-order prover. No Python eval or executable proof payloads are accepted.
"""
from collections import deque
from itertools import product

def V(x): return ("var", x)
def F(f, *args): return ("fun", f, tuple(args))
def Eq(a,b): return ("eq",a,b)
def Imp(a,b): return ("imp",a,b)
def Not(a): return ("not",a)
def All(x,a): return ("all",x,a)

def term_free(t):
    return {t[1]} if t[0]=="var" else set().union(*(term_free(a) for a in t[2]))

def free(a):
    k=a[0]
    if k=="eq": return term_free(a[1]) | term_free(a[2])
    if k=="pred": return set().union(*(term_free(t) for t in a[2]))
    if k=="all": return free(a[2])-{a[1]}
    if k=="not": return free(a[1])
    if k=="bot": return set()
    return free(a[1]) | free(a[2])

def names(a):
    """All variable names, including bound ones (for hygienic fresh naming)."""
    if a[0]=="all": return {a[1]} | names(a[2])
    if a[0] in ("not",): return names(a[1])
    if a[0] in ("imp","and","or"): return names(a[1]) | names(a[2])
    return free(a)

def term_sub(t,x,r):
    if t[0]=="var": return r if t[1]==x else t
    return F(t[1],*(term_sub(a,x,r) for a in t[2]))

def substitute(a,x,t):
    k=a[0]
    if k=="eq": return Eq(term_sub(a[1],x,t),term_sub(a[2],x,t))
    if k=="pred": return ("pred",a[1],tuple(term_sub(r,x,t) for r in a[2]))
    if k=="all":
        y,b=a[1:]
        if y==x or x not in free(b): return a
        if y in term_free(t):
            used=names(b) | term_free(t) | {x,y}
            j=0
            while "fresh"+str(j) in used: j+=1
            z="fresh"+str(j)
            b=substitute(b,y,V(z)); y=z
        return All(y,substitute(b,x,t))
    if k=="not": return Not(substitute(a[1],x,t))
    if k=="bot": return a
    return (k,substitute(a[1],x,t),substitute(a[2],x,t))

def tautology(a):
    atoms=set()
    def collect(b):
        if b[0] in ("imp","and","or"): collect(b[1]); collect(b[2])
        elif b[0]=="not": collect(b[1])
        elif b[0]!="bot": atoms.add(b)
    collect(a)
    atoms=sorted(atoms,key=repr)
    def truth(b,env):
        k=b[0]
        if k=="bot": return False
        if k=="not": return not truth(b[1],env)
        if k=="imp": return not truth(b[1],env) or truth(b[2],env)
        if k=="and": return truth(b[1],env) and truth(b[2],env)
        if k=="or": return truth(b[1],env) or truth(b[2],env)
        return env[b]
    return all(truth(a,dict(zip(atoms,values))) for values in product((False,True),repeat=len(atoms)))

class Kernel:
    def __init__(self,functions,predicates,axioms):
        self.functions=dict(functions); self.predicates=dict(predicates)
        self.axioms=dict(axioms)
        for a in self.axioms.values():
            self.formula(a)
            if free(a): raise ValueError("theory axioms must be closed")
    def term(self,t):
        if not isinstance(t,tuple): raise ValueError("term must be an immutable AST")
        if len(t)==2 and t[0]=="var" and isinstance(t[1],str): return
        if len(t)!=3 or t[0]!="fun" or not isinstance(t[2],tuple): raise ValueError("malformed term")
        if self.functions.get(t[1])!=len(t[2]): raise ValueError("unknown function or arity")
        for a in t[2]: self.term(a)
    def formula(self,a):
        if not isinstance(a,tuple) or not a: raise ValueError("malformed formula")
        k=a[0]
        if k=="eq" and len(a)==3: self.term(a[1]); self.term(a[2]); return
        if k=="pred" and len(a)==3 and isinstance(a[2],tuple):
            if self.predicates.get(a[1])!=len(a[2]): raise ValueError("unknown predicate or arity")
            for t in a[2]: self.term(t)
            return
        if k=="all" and len(a)==3 and isinstance(a[1],str): self.formula(a[2]); return
        if k=="not" and len(a)==2: self.formula(a[1]); return
        if k in ("and","or","imp") and len(a)==3: self.formula(a[1]); self.formula(a[2]); return
        if a==("bot",): return
        raise ValueError("malformed formula")
    def check(self,proof,target):
        """Return False on bad data; references must strictly precede their use."""
        try:
            self.formula(target)
            if not proof: return False
            formulas=[]
            for line in proof:
                a=line["formula"]; self.formula(a); r=line["rule"]
                def prior(i):
                    if type(i) is not int or not 0<=i<len(formulas): raise ValueError("bad reference")
                    return formulas[i]
                if r=="axiom": valid=a==self.axioms[line["name"]]
                elif r=="tautology": valid=tautology(a)
                elif r=="refl": valid=a[0]=="eq" and a[1]==a[2]
                elif r=="instantiate":
                    u=line["universal"]; t=line["term"]
                    self.formula(u); self.term(t)
                    valid=u[0]=="all" and a==Imp(u,substitute(u[2],u[1],t))
                elif r=="distribute":
                    x=line["variable"]; p=line["antecedent"]; q=line["consequent"]
                    self.formula(p); self.formula(q)
                    valid=isinstance(x,str) and x not in free(p) and a==Imp(All(x,Imp(p,q)),Imp(p,All(x,q)))
                elif r=="eq_subst":
                    x=line["variable"]; p=line["template"]; s=line["left"]; t=line["right"]
                    self.formula(p); self.term(s); self.term(t)
                    valid=isinstance(x,str) and a==Imp(Eq(s,t),Imp(substitute(p,x,s),substitute(p,x,t)))
                elif r=="mp":
                    p=prior(line["antecedent"]); pq=prior(line["implication"])
                    valid=pq==Imp(p,a)
                elif r=="generalize":
                    p=prior(line["source"]); x=line["variable"]
                    valid=isinstance(x,str) and a==All(x,p)
                else: valid=False
                if not valid: return False
                formulas.append(a)
            return formulas[-1]==target
        except (KeyError,ValueError,TypeError,IndexError,RecursionError): return False

def match(pattern,t,env):
    if pattern[0]=="var":
        if pattern[1] in env: return env[pattern[1]]==t
        env[pattern[1]]=t; return True
    return (t[0]=="fun" and pattern[1]==t[1] and len(pattern[2])==len(t[2])
            and all(match(a,b,env) for a,b in zip(pattern[2],t[2])))

def rewrite_proposals(t,axioms):
    """Forward quantified equations at every subterm; no kernel privileges."""
    for name,a in axioms.items():
        variables=[]
        while a[0]=="all": variables.append(a[1]); a=a[2]
        if a[0]!="eq": continue
        env={}
        if match(a[1],t,env) and all(x in env for x in variables):
            out=a[2]
            for x in variables: out=term_sub(out,x,env[x])
            yield out,name,variables,env,()
    if t[0]=="fun":
        for i,child in enumerate(t[2]):
            for new,name,vs,env,path in rewrite_proposals(child,axioms):
                args=list(t[2]); args[i]=new
                yield F(t[1],*args),name,vs,env,(i,)+path

def replace_at(t,path,new):
    if not path: return new
    args=list(t[2]); args[path[0]]=replace_at(args[path[0]],path[1:],new)
    return F(t[1],*args)

def equational_search(kernel,start,target,max_depth=8):
    """BFS proposer; each discovered answer requires an independent kernel check."""
    kernel.term(start); kernel.term(target)
    if term_free(start) or term_free(target): raise ValueError("ground rewrite pilot only")
    queue=deque([(start,())]); seen={start}; nodes=0; found=None
    while queue:
        t,steps=queue.popleft(); nodes+=1
        if t==target: found=steps; break
        if len(steps)>=max_depth: continue
        for new,name,vs,env,path in rewrite_proposals(t,kernel.axioms):
            if new not in seen:
                seen.add(new); queue.append((new,steps+((t,new,name,vs,env,path),)))
    if found is None: return {"status":"no_proof_within_forward_rewrite_budget","nodes":nodes}
    proof=[]
    def emit(rule,a,**kw): proof.append({"rule":rule,"formula":a,**kw}); return len(proof)-1
    last=emit("refl",Eq(start,start))
    for before,after,name,variables,env,path in found:
        u=kernel.axioms[name]; index=emit("axiom",u,name=name)
        for x in variables:
            instance=substitute(u[2],u[1],env[x])
            i=emit("instantiate",Imp(u,instance),universal=u,term=env[x])
            index=emit("mp",instance,antecedent=index,implication=i); u=instance
        template=Eq(start,replace_at(before,path,V("hole")))
        i=emit("eq_subst",Imp(u,Imp(Eq(start,before),Eq(start,after))),
               variable="hole",template=template,left=u[1],right=u[2])
        j=emit("mp",Imp(Eq(start,before),Eq(start,after)),antecedent=index,implication=i)
        last=emit("mp",Eq(start,after),antecedent=last,implication=j)
    assert kernel.check(proof,Eq(start,target))
    return {"status":"kernel_checked_derivation","nodes":nodes,"rewrite_steps":len(found),
            "proof":proof,"target":Eq(start,target),"verified":True}

def latex_term(t):
    if t[0]=="var": return t[1]
    f,args=t[1:]
    if f=="zero": return "0"
    if f=="succ": return "S("+latex_term(args[0])+")"
    if f=="add": return "("+latex_term(args[0])+"+"+latex_term(args[1])+")"
    return "\\operatorname{"+f+"}("+",".join(map(latex_term,args))+")"

def latex(a):
    if a[0]=="eq": return latex_term(a[1])+"="+latex_term(a[2])
    if a[0]=="all": return "\\forall "+a[1]+"\\;("+latex(a[2])+")"
    if a[0]=="imp": return "("+latex(a[1])+"\\Rightarrow "+latex(a[2])+")"
    if a[0]=="not": return "\\neg("+latex(a[1])+")"
    return repr(a)

def demo():
    z=F("zero"); one=F("succ",z); two=F("succ",one)
    x,y=V("x"),V("y")
    axioms={"add_zero":All("x",Eq(F("add",x,z),x)),
            "add_successor":All("x",All("y",Eq(F("add",x,F("succ",y)),F("succ",F("add",x,y)))))}
    kernel=Kernel({"zero":0,"succ":1,"add":2},{},axioms)
    result=equational_search(kernel,F("add",one,one),two)
    altered=[dict(line) for line in result["proof"]]
    altered[-1]["formula"]=Eq(F("add",one,one),one)
    result.update({"axioms":[latex(a) for a in axioms.values()],"statement":latex(result["target"]),
        "display_proof":[{"rule":l["rule"],"formula":latex(l["formula"])} for l in result["proof"]],
        "tampered_proof_rejected":not kernel.check(altered,altered[-1]["formula"]),
        "scope":"classical first-order certificate kernel; bounded forward equational search pilot; not compiled to Wang tiles"})
    return result
