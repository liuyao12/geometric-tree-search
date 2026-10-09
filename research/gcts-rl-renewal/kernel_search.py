"""Certificate proposals and complete Wang search for first-order envelopes."""
import itertools, random, time
from turtle import Policy
import logic, lazy_wang, proof_search
from kernel_machine import Catalog,KernelMachine,language_stage,size

def bounds(stage):
    for syntax in range(1,stage+1):
        for certificate in range(stage-syntax+1):
            for height in range(stage-syntax-certificate+1):
                yield syntax,2**certificate,2**height,2**stage

def fair_search(kernel,target,max_stage=None,extended=True):
    """Unbounded dovetail over syntax, certificate length, height and nodes.

    Every fixed finite envelope/rectangle is retried with unbounded node
    budget. All transitions, symbolic domains and alternatives remain finite.
    No time cut-off in the theoretical dovetail; bounded calls mean unknown.
    Full syntax enumeration has extreme cost and is not a practical prover.
    """
    catalogs={}; machines={}; history=[]; attempts=0
    for stage in itertools.count(1):
        if max_stage is not None and stage>max_stage:
            return {'status':'unknown_outer_stage_budget','attempts':attempts,'recent_attempts':history[-16:]}
        for syntax,length,height,nodes in bounds(stage):
            if syntax not in catalogs: catalogs[syntax]=language_stage(kernel,target,syntax)
            c=catalogs[syntax]
            if target not in c.index: continue
            if syntax not in machines: machines[syntax]=KernelMachine(c,target)
            m=machines[syntax]
            result=lazy_wang.search(m.compiler,m.pattern(length),height,m.accepting_row(len(m.pattern(length))),
                                   node_limit=nodes,seconds=float('inf'),extended=extended)
            attempts+=1; history.append({'syntax_bound':syntax,'length':length,'height':height,'nodes':nodes,'status':result['status']})
            if result.get('verified'):
                cert=proof_search.pack(result)
                if not replay(c,target,length,height,cert): raise AssertionError('kernel/Wang replay failed')
                return {'status':'kernel_proof_found_by_fair_bounds','attempts':attempts,'syntax_bound':syntax,
                        'declaration':c.declaration(),'target':target,'certificate_length':length,'height':height,'certificate':cert}

def replay(catalog,target,length,height,certificate):
    """Externally fixed theory/language/target; no certificate-selected axioms."""
    try:
        m=KernelMachine(catalog,target); rows,placements=proof_search.unpack(certificate)
        pattern=m.pattern(length)
        if certificate['height']!=height or certificate['width']!=len(pattern): return False
        if not lazy_wang.independent_check(m.compiler,pattern,m.accepting_row(len(pattern)),rows,placements,
                                           extended=certificate['marking']=='redundant-neighbor-values'): return False
        start=len(catalog.formulas)+4
        commands=m.parse(rows[0][start:start+length]); catalog.proof(commands,target)
        return True
    except (ValueError,KeyError,TypeError,IndexError,RecursionError): return False

def features(catalog,target,facts,rule):
    item=catalog.inferences[rule]; a=catalog.formulas[item.conclusion]
    target_parts=set()
    def parts(b):
        target_parts.add(b)
        if b[0]=='all': parts(b[2])
        elif b[0] in ('imp','and','or'): parts(b[1]); parts(b[2])
        elif b[0]=='not': parts(b[1])
    parts(target)
    return {'target_conclusion':int(a==target),'target_subformula':int(a in target_parts),
            'premise_count':len(item.premises),'conclusion_size':size(a),'bias':1,
            'rule:'+item.witness['rule']:1}

def propose(catalog,target,policy,seed,horizon,learn=False):
    """Cold inference-sequence policy; finite kernel facts are its environment.

    This is an auxiliary proposal process. Its legal-action list never replaces
    Wang graph degrees. A successful sequence becomes a scheduler-validated
    rectangle preference and every base Wang alternative is retained.
    """
    rng=random.Random(seed); facts=set(); commands=[]; traces=[]; start=time.monotonic()
    for _ in range(horizon):
        if catalog.index[target] in facts: break
        actions=[i for i,r in enumerate(catalog.inferences) if r.conclusion not in facts and all(p in facts for p in r.premises)]
        if not actions: break
        fs=[features(catalog,target,facts,i) for i in actions]
        if learn:
            chosen,gradient=policy.select(rng,fs); traces.append(gradient)
        else:
            rng.shuffle(actions); fs=[features(catalog,target,facts,i) for i in actions]
            chosen=max(range(len(actions)),key=lambda j:sum(policy.weights[k]*v for k,v in fs[j].items()))
        r=actions[chosen]; commands.append(r); facts.add(catalog.inferences[r].conclusion)
    success=catalog.index[target] in facts
    if success: catalog.proof(commands,target)
    reward=(1-len(commands)/(2*max(1,horizon))) if success else -.5
    if learn: policy.update(traces,reward)
    return {'commands':tuple(commands),'verified':success,'reward':reward,'seconds':time.monotonic()-start,
            'scope':'kernel inference proposal only; all Wang alternatives retained'}

def preference(machine,length,height,proposal):
    if not proposal['verified'] or len(proposal['commands'])>length: return None
    tokens=machine.tokens(proposal['commands'])+('_',)*(length-len(proposal['commands']))
    result=machine.run(tokens,limit=height)
    if result['status']!='accept': return None
    rows=result['rows']+[result['rows'][-1]]*(height+1-len(result['rows']))
    return lazy_wang.preferred_from_rows(machine.compiler,rows)

def problems(distractors=0):
    """Declared small languages are built from problems, never proof witnesses."""
    def pred(s): return ('pred',s,())
    P,Q,R=map(pred,('P','Q','R'))
    ax={'given_P':P,'P_Q':logic.Imp(P,Q),'Q_R':logic.Imp(Q,R)}
    fs=(P,Q,R,logic.Imp(P,Q),logic.Imp(Q,R))
    c=logic.F('c'); d=logic.F('d'); x=logic.V('x'); hole=logic.V('hole')
    f=lambda t:logic.F('f',t)
    u=logic.All('x',logic.Eq(f(x),x)); instance=logic.Eq(f(c),c)
    eq=logic.Eq(c,d); refl=logic.Eq(f(c),f(c)); goal=logic.Eq(f(c),f(d))
    inner=logic.Imp(refl,goal); outer=logic.Imp(eq,inner)
    items=[('syllogism',{}, {'P':0,'Q':0,'R':0},ax,fs,R,(),(),()),
           ('instantiation',{'c':0,'f':1},{},{'given_universal':u},(u,logic.Imp(u,instance),instance),instance,(c,),('x',),()),
           ('equality_congruence',{'c':0,'d':0,'f':1},{},{'given_equality':eq},(eq,refl,outer,inner,goal),goal,
            (c,d,f(c),f(d)),('hole',),(logic.Eq(f(c),f(hole)),)),
           ('generalization',{}, {},{},(logic.Eq(x,x),logic.All('x',logic.Eq(x,x))),logic.All('x',logic.Eq(x,x)),(x,),('x',),()),
           ('tautology',{}, {'P':0},{},(logic.Imp(P,P),),logic.Imp(P,P),(),(),()),
           ('distribution',{}, {'P':0,'Q':0}, {'given_universal':logic.All('x',logic.Imp(P,Q)),'given_P':P},
            (logic.All('x',logic.Imp(P,Q)),P,logic.Imp(logic.All('x',logic.Imp(P,Q)),logic.Imp(P,logic.All('x',Q))),
             logic.Imp(P,logic.All('x',Q)),logic.All('x',Q)),logic.All('x',Q),(),('x',),())]
    result=[]
    for name,functions,predicates,axioms,formulas,target,terms,variables,templates in items:
        predicates=dict(predicates); axioms=dict(axioms); formulas=list(formulas)
        for j in range(distractors):
            symbol=f'D{j}'; predicates[symbol]=0; a=pred(symbol); axioms[f'distractor_{j}']=a; formulas.append(a)
        k=logic.Kernel(functions,predicates,axioms)
        result.append({'id':name,'catalog':Catalog(k,formulas,terms,variables,templates),'target':target})
    return result
