"""Sequential copy-sweep certificate control, without DAG interface reuse."""
import hashlib,json,time


def problem_hash(proof):
    return hashlib.sha256(json.dumps({k:proof[k] for k in ('machine_sha256','initial','steps','limit','final','status')},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def from_dag(proof):
    out={k:proof[k] for k in ('machine_sha256','initial','steps','limit','final','status','problem_sha256')}
    out['tokens']=[proof['nodes'][i] for i in proof['tokens']]
    return out


def verify(d,proof,expected_problem=None,max_tokens=1000000):
    started=time.perf_counter();fingerprint=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if proof['machine_sha256']!=fingerprint or proof['problem_sha256']!=problem_hash(proof) or expected_problem is not None and expected_problem!=proof['problem_sha256']:raise ValueError('external problem binding')
    if any(type(proof[k]) is not int or proof[k]<0 for k in ('steps','limit')) or proof['steps']>proof['limit']:raise ValueError('natural steps/limit')
    if len(proof['tokens'])>max_tokens:return dict(status='unknown_certificate_budget')
    heads=[(i,s) for i,s in enumerate(proof['initial']) if isinstance(s,(tuple,list))]
    if len(heads)!=1:raise ValueError('one head')
    h,head=heads[0]
    if len(head)!=3 or head[0]!='head':raise ValueError('head tag')
    _,q,a=head;tape=list(proof['initial']);tape[h]=a
    alphabet=set(d['alphabet']);transitions=d['transitions'];allowed={}
    if q not in d['states'] or any(s not in alphabet for s in tape) or tape[0]!='B' or tape[-1]!='B' or not 0<h<len(tape)-1:raise ValueError('finite frame')
    table={(q,a):(out,w,v) for q,a,out,w,v in transitions}
    for source,read,out,write,move in transitions:
        if source==out and read==write and move:allowed.setdefault((source,move),set()).add(read)
    steps=0
    for token in proof['tokens']:
        if set(token)=={'transition'}:
            i=token['transition']
            if type(i) is not int or not 0<=i<len(transitions):raise ValueError('transition ID')
            source,read,out,write,move=transitions[i]
            if q!=source or tape[h]!=read or not 0<h+move<len(tape)-1:raise ValueError('primitive input')
            tape[h]=write;h+=move;q=out;steps+=1
        elif set(token)=={'sweep'}:
            if len(token['sweep'])!=3:raise ValueError('sweep arity')
            source,move,n=token['sweep']
            if type(n) is not int or n<1 or type(move) is not int or move not in (-1,1) or q!=source or (q,move) not in allowed or not 0<h+move*n<len(tape)-1:raise ValueError('sweep input/frame')
            values=tape[h:h+n] if move==1 else tape[h-n+1:h+1]
            if not set(values)<=allowed[q,move]:raise ValueError('sweep read constraint')
            h+=move*n;steps+=n
        else:raise ValueError('token syntax')
    final=tape.copy();final[h]=('head',q,tape[h])
    if steps!=proof['steps'] or json.dumps(final)!=json.dumps(proof['final']):raise ValueError('output/length')
    status={'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,'accept' if q==d['halt'] else 'reject' if q=='reject' else 'unknown_step_budget' if steps==proof['limit'] else 'reject' if (q,tape[h]) not in table else 'unknown_frame_bound' if not 0<h+table[q,tape[h]][2]<len(tape)-1 else None)
    if proof['status']!=status:raise ValueError('terminal/prefix status')
    return dict(status='checked_computation_response',result=status,steps=steps,tokens=len(proof['tokens']),seconds=time.perf_counter()-started)
