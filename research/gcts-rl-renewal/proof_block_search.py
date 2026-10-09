"""Searched, universally closed equational blocks and cold RL proposals.

This is a semantic proposal adaptation, not a replacement Wang/GCTS graph.
Both axiom directions and every term position remain available in the finite
term envelope; learner order never supplies logical impossibility labels.
The induction tactic is explicitly authored. Proofs and block contents are
searched; neither an authored proof nor a substitution/lemma library is input.
"""
import collections,copy,hashlib,itertools,json,random,time
import logic
from serialized_kernel import canonical,check,problem_hash,PROTOCOL
from turtle import Policy

def freeze(x):return tuple(freeze(y) for y in x) if isinstance(x,list) else x
def size(t):return 1 if t[0]=='var' else 1+sum(map(size,t[2]))
def parts(t):
    yield t
    if t[0]=='fun':
        for a in t[2]:yield from parts(a)
def locations(t,path=()):
    yield path,t
    if t[0]=='fun':
        for i,a in enumerate(t[2]):yield from locations(a,path+(i,))
def bind(pattern,t,variables,env):
    if pattern[0]=='var':
        if pattern[1] not in variables:return pattern==t
        old=env.get(pattern[1]);env[pattern[1]]=t;return old is None or old==t
    return t[0]=='fun' and pattern[1]==t[1] and len(pattern[2])==len(t[2]) and all(bind(p,a,variables,env) for p,a in zip(pattern[2],t[2]))
def replace_variables(t,env):
    if t[0]=='var':return env.get(t[1],t)
    return logic.F(t[1],*(replace_variables(a,env) for a in t[2]))
def equation(name,formula,origin,proof_cost=1,index=None):
    variables=[];body=freeze(formula)
    while body[0]=='all':variables.append(body[1]);body=body[2]
    if body[0]!='eq':return None
    return dict(name=name,formula=freeze(formula),variables=tuple(variables),body=body,origin=origin,proof_cost=proof_cost,index=index)
def equations(theory,library=(),assumptions=()):
    out=[equation(n,a,'axiom') for n,a in theory['axioms'].items()]
    out += [equation(b['name'],b['conclusion'],'block',b['expanded_rules']) for b in library]
    out += [equation('premise-'+str(i),a,'assumption',index=i) for i,a in enumerate(assumptions)]
    return tuple(r for r in out if r is not None)
def actions(t,rules,limit):
    """Complete matching directions/locations for this declared rule fragment.

    Quantified variables must occur on both sides. Rules needing unconstrained
    substitutions are outside this proposer, not outside the fixed checker.
    Actions are not deduplicated by endpoint: different proof blocks remain
    distinct policy choices. A visited endpoint is only a search-cycle control.
    """
    out=[]
    for path,sub in locations(t):
        for r in rules:
            for direction in (1,-1):
                left,right=r['body'][1:] if direction==1 else r['body'][1:][::-1]
                env={}
                if bind(left,sub,set(r['variables']),env) and set(r['variables'])<=env.keys():
                    after=logic.replace_at(t,path,replace_variables(right,env))
                    if after!=t and size(after)<=limit:
                        out.append(dict(before=t,after=after,rule=r,bindings=env,path=path,direction=direction))
    return out

def distance(a,b):
    if a==b:return 0
    if a[0]=='var' or b[0]=='var' or a[1]!=b[1] or len(a[2])!=len(b[2]):return max(size(a),size(b))
    return sum(distance(x,y) for x,y in zip(a[2],b[2]))
def features(action,target):
    a,b=action['before'],action['after'];target_parts=set(parts(target))
    return dict(bias=1,finishes=int(b==target),distance_gain=(distance(a,target)-distance(b,target))/8,
        size_gain=(size(a)-size(b))/8,target_overlap=(len(set(parts(b))&target_parts)-len(set(parts(a))&target_parts))/8,
        learned_block=int(action['rule']['origin']=='block'),expansion_cost=min(1000,action['rule']['proof_cost'])/100,
        context_depth=len(action['path'])/8)
def invert(a):return dict(a,before=a['after'],after=a['before'],direction=-a['direction'])
def unfold(parents,t):
    path=[]
    while parents[t] is not None:
        before,action=parents[t];path.append(action);t=before
    return path[::-1]
def rewrite_search(start,target,rules,term_limit,node_limit,policy=None,seed=0,rollouts=0,horizon=10,learn=False):
    began=time.perf_counter();stats=dict(expanded=0,enumerated=0,rollout_moves=0,rollout_attempts=0,rollout_success=0)
    traces=[];rng=random.Random(seed);solution=None
    for attempt in range(rollouts):
        t=start;path=[];seen={t};gradients=[];stats['rollout_attempts']+=1
        for _ in range(horizon):
            if t==target:break
            offered=actions(t,rules,term_limit);stats['enumerated']+=len(offered)
            offered=[a for a in offered if a['after'] not in seen]
            if not offered:break
            fs=[features(a,target) for a in offered]
            if learn:i,g=policy.select(rng,fs);gradients.append(g)
            else:
                scores=[sum(policy.weights[k]*v for k,v in f.items()) for f in fs] if policy else [0]*len(fs)
                top=max(scores);i=rng.choice([i for i,s in enumerate(scores) if s==top])
            action=offered[i];path.append(action);t=action['after'];seen.add(t);stats['rollout_moves']+=1
        success=t==target;work=stats['enumerated']+sum(a['rule']['proof_cost'] for a in path)
        reward=(1.0 if success else -.5)-min(.5,work/10000)
        if learn:policy.update(gradients,reward)
        traces.append(dict(attempt=attempt,success=success,reward=reward,moves=len(path),gradients=gradients,
            actions=[dict(rule=a['rule']['name'],origin=a['rule']['origin'],path=a['path'],direction=a['direction'],before=a['before'],after=a['after']) for a in path]))
        if success:solution=path;stats['rollout_success']+=1;break
    if solution is None:
        queues=[collections.deque([start]),collections.deque([target])];parents=[{start:None},{target:None}]
        if start==target:solution=[]
        while solution is None and (queues[0] or queues[1]) and stats['expanded']<node_limit:
            side=0 if queues[0] and (not queues[1] or len(queues[0])<=len(queues[1])) else 1
            t=queues[side].popleft();stats['expanded']+=1
            offered=actions(t,rules,term_limit);stats['enumerated']+=len(offered)
            for action in offered:
                after=action['after']
                if after not in parents[side]:parents[side][after]=(t,action);queues[side].append(after)
                if after in parents[1-side]:
                    left=unfold(parents[0],after);right=unfold(parents[1],after)
                    solution=left+[invert(a) for a in reversed(right)];break
    return dict(status='found' if solution is not None else 'unknown_fragment_or_node_budget',path=solution,stats=stats,
        rollouts=traces,seconds=time.perf_counter()-began,term_limit=term_limit,node_limit=node_limit)

class Proof:
    def __init__(self):self.lines=[]
    def emit(self,rule,formula,**kw):self.lines.append(dict(rule=rule,formula=formula,**kw));return len(self.lines)-1
    def mp(self,antecedent,implication):
        p=self.lines[antecedent]['formula'];q=self.lines[implication]['formula']
        if q[0]!='imp' or q[1]!=p:raise ValueError('bad builder MP')
        return self.emit('mp',q[2],antecedent=antecedent,implication=implication)
    def append(self,lines):
        offset=len(self.lines)
        for line in lines:
            item=dict(line)
            if item['rule']=='mp':item['antecedent']+=offset;item['implication']+=offset
            if item['rule']=='generalize':item['source']+=offset
            if item['rule']=='block':item['inputs']=[i+offset for i in item['inputs']]
            self.lines.append(item)
        return len(self.lines)-1

def fresh(*terms):
    used=set().union(*(logic.term_free(t) for t in terms));n=0
    while 'gctsHole'+str(n) in used:n+=1
    return 'gctsHole'+str(n)
def proof_for_path(start,path):
    out=Proof();last=out.emit('refl',logic.Eq(start,start));current=start
    for action in path:
        if action['before']!=current:raise ValueError('noncontiguous rewrite certificate')
        r=action['rule'];u=r['formula']
        if r['origin']=='axiom':index=out.emit('axiom',u,name=r['name'])
        elif r['origin']=='block':index=out.emit('block',u,name=r['name'],inputs=[])
        else:index=out.emit('assumption',u,index=r['index'])
        for x in r['variables']:
            term=action['bindings'][x];instance=logic.substitute(u[2],u[1],term)
            ax=out.emit('instantiate',logic.Imp(u,instance),universal=u,term=term);index=out.mp(index,ax);u=instance
        left,right=u[1:]
        if action['direction']==-1:
            name=fresh(left,right);template=logic.Eq(logic.V(name),left)
            refl=out.emit('refl',logic.Eq(left,left))
            schema=out.emit('eq_subst',logic.Imp(u,logic.Imp(logic.Eq(left,left),logic.Eq(right,left))),variable=name,template=template,left=left,right=right)
            index=out.mp(refl,out.mp(index,schema));left,right=right,left;u=logic.Eq(left,right)
        name=fresh(start,current,action['after'],left,right)
        template=logic.Eq(start,logic.replace_at(current,action['path'],logic.V(name)))
        after=action['after'];schema=out.emit('eq_subst',logic.Imp(u,logic.Imp(logic.Eq(start,current),logic.Eq(start,after))),
            variable=name,template=template,left=left,right=right)
        last=out.mp(last,out.mp(index,schema));current=after
    return out.lines

def deduce(lines,premise):
    """Hilbert deduction for the searched equational fragment (no generalize)."""
    out=Proof();lift=[]
    for line in lines:
        a=line['formula'];lifted=logic.Imp(premise,a)
        if line['rule']=='assumption':
            if line['index']!=0 or a!=premise:raise ValueError('deduction assumption')
            index=out.emit('tautology',lifted)
        elif line['rule']=='mp':
            b=lines[line['antecedent']]['formula'];ba=logic.Imp(b,a)
            schema=logic.Imp(logic.Imp(premise,ba),logic.Imp(logic.Imp(premise,b),lifted))
            ax=out.emit('tautology',schema);index=out.mp(lift[line['antecedent']],out.mp(lift[line['implication']],ax))
        else:
            if line['rule'] in ('generalize','block') and (line['rule']=='generalize' or line['inputs']):raise ValueError('unsupported deduction reference')
            i=out.emit(line['rule'],a,**{k:v for k,v in line.items() if k not in ('rule','formula')})
            ax=out.emit('tautology',logic.Imp(a,lifted));index=out.mp(i,ax)
        lift.append(index)
    return out.lines

def induction_schema(x,p):
    body=logic.Imp(('and',logic.substitute(p,x,logic.F('zero')),logic.All(x,logic.Imp(p,logic.substitute(p,x,logic.F('succ',logic.V(x)))))),logic.All(x,p))
    for y in reversed(sorted(logic.free(p)-{x})):body=logic.All(y,body)
    return body

def required_blocks(lines,library):
    by_name={b['name']:b for b in library};needed=set()
    def visit(proof):
        for line in proof:
            if line['rule']=='block' and line['name'] not in needed:
                name=line['name']
                if name not in by_name:raise ValueError('unknown learned block')
                needed.add(name);visit(by_name[name]['proof'])
    visit(lines)
    return [{k:b[k] for k in ('name','premises','conclusion','proof')} for b in library if b['name'] in needed]
def request(theory,target,proof,library=()):return dict(protocol=PROTOCOL,theory=theory,target=target,blocks=required_blocks(proof,library),proof=proof)

def prove(theory,target,library=(),policy=None,seed=0,node_limit=1000,slack=3,rollouts=0,learn=False,max_inductions=3):
    began=time.perf_counter();target=freeze(target);variables=[];body=target
    while body[0]=='all':variables.append(body[1]);body=body[2]
    if body[0]!='eq':return dict(status='unknown_proposer_fragment',seconds=time.perf_counter()-began)
    records=[]
    def attempt(eq,assumptions=(),offset=0):
        rs=equations(theory,library,assumptions);limit=max(size(eq[1]),size(eq[2]))+slack
        result=rewrite_search(eq[1],eq[2],rs,limit,node_limit,policy,seed+offset,rollouts,learn=learn)
        path=result.pop('path');record=dict(result,goal=eq,assumptions=assumptions)
        records.append(record)
        if path is None:return None
        record['path']=[dict(a,rule={k:v for k,v in a['rule'].items() if k!='proof_cost'}) for a in path]
        return proof_for_path(eq[1],path)
    lines=attempt(body)
    method='equational-rewrite'
    if lines is None and variables and max_inductions>0 and 'nat-induction' in theory['schemas']:
        # Explicit strategy: induction on the innermost quantified variable.
        x=variables[-1];base=logic.substitute(body,x,logic.F('zero'));step=logic.substitute(body,x,logic.F('succ',logic.V(x)))
        base_lines=attempt(base,offset=101)
        if base_lines is None and len(variables)>1:
            closed=base
            for y in reversed(variables[:-1]):closed=logic.All(y,closed)
            child=prove(theory,closed,library,policy,seed+303,node_limit,slack,rollouts,learn,max_inductions-1)
            records.extend(dict(r,recursive_base=True) for r in child.get('records',[]))
            if child['status']=='accepted_proposal':
                partial=Proof();index=partial.append(freeze_lines(child['request']['proof']));u=closed
                for y in variables[:-1]:
                    instance=logic.substitute(u[2],u[1],logic.V(y));ax=partial.emit('instantiate',logic.Imp(u,instance),universal=u,term=logic.V(y));index=partial.mp(index,ax);u=instance
                base_lines=partial.lines
        step_lines=attempt(step,(body,),offset=202)
        if base_lines is not None and step_lines is not None:
            out=Proof();base_i=out.append(base_lines);deduced=deduce(step_lines,body);step_i=out.append(deduced)
            universal=logic.All(x,logic.Imp(body,step));step_i=out.emit('generalize',universal,variable=x,source=step_i)
            both=('and',base,universal);taut=out.emit('tautology',logic.Imp(base,logic.Imp(universal,both)))
            both_i=out.mp(step_i,out.mp(base_i,taut));schema=induction_schema(x,body)
            schema_i=out.emit('induction',schema,variable=x,template=body)
            for y in sorted(logic.free(body)-{x}):
                inst=logic.substitute(schema[2],schema[1],logic.V(y));ax=out.emit('instantiate',logic.Imp(schema,inst),universal=schema,term=logic.V(y));schema_i=out.mp(schema_i,ax);schema=inst
            result_i=out.mp(both_i,schema_i)
            for y in reversed(variables[:-1]):result_i=out.emit('generalize',logic.All(y,out.lines[result_i]['formula']),variable=y,source=result_i)
            lines=out.lines;method='searched-base-and-step-with-authored-induction-tactic'
    elif lines is not None:
        out=Proof();index=out.append(lines)
        for x in reversed(variables):index=out.emit('generalize',logic.All(x,out.lines[index]['formula']),variable=x,source=index)
        lines=out.lines
    if lines is None:return dict(status='unknown_search_budget_or_fragment',records=records,seconds=time.perf_counter()-began)
    d=request(theory,target,lines,library);payload=canonical(d);checked=check(payload,expected_problem_sha256=problem_hash(d))
    if checked['status']!='accepted':raise ValueError(('searched proof failed fixed checker',checked,method))
    return dict(status='accepted_proposal',method=method,request=json.loads(payload),check=checked,records=records,
        seconds=time.perf_counter()-began,root_lines=len(lines),blocks=len(d['blocks']))

def promote(result,library):
    if result['status']!='accepted_proposal':return None
    d=result['request'];conclusion=freeze(d['target']);r=equation('candidate',conclusion,'block')
    if r is None or logic.free(conclusion) or r['body'][1]==r['body'][2]:return None
    if any(freeze(b['conclusion'])==conclusion for b in library):return None
    name='learned-'+hashlib.sha256(canonical(conclusion)).hexdigest()[:12]
    proof=freeze_lines(d['proof']);cost=expanded_rules(proof,library)
    block=dict(name=name,premises=[],conclusion=conclusion,proof=proof,expanded_rules=cost,
        provenance=dict(method=result['method'],problem_sha256=problem_hash(d),certificate_sha256=result['check']['certificate_sha256'],root_lines=len(proof),dependencies=[b['name'] for b in d['blocks']]))
    # Validate the new definition, not merely the source theorem proof.
    probe=dict(protocol=PROTOCOL,theory=d['theory'],target=conclusion,blocks=d['blocks']+[{k:block[k] for k in ('name','premises','conclusion','proof')}],proof=[dict(rule='block',formula=conclusion,name=name,inputs=[])])
    verified=check(canonical(probe),expected_problem_sha256=problem_hash(probe))
    if verified['status']!='accepted':raise ValueError('new block definition rejected')
    block['definition_check']=verified;library.append(block);return block

def freeze_lines(lines):
    formula_fields={'formula','universal','term','template','left','right','antecedent','consequent'}
    return [{k:freeze(v) if k in formula_fields and isinstance(v,list) else v for k,v in line.items()} for line in lines]
def expanded_rules(lines,library):
    costs={b['name']:b['expanded_rules'] for b in library}
    return sum(costs[line['name']] if line['rule']=='block' else 1 for line in lines)
