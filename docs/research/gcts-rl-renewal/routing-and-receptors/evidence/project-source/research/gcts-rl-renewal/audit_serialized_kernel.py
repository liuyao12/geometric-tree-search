"""Separate JSON/schema/interface replay and expansion into frozen logic.Kernel.

Does not import serialized_kernel or its examples. Every checked declaration
is independently expanded, even unused blocks. Local block assumptions are
temporarily universally closed and instantiated in the oracle kernel; an
additional explicit eigenvariable check restricts generalization to variables
absent from the original open premises. Root expansion has no local axioms.
"""
import hashlib
import json
import pathlib
import time
import logic

FIELDS={
    'axiom':('name',), 'tautology':(), 'refl':(), 'instantiate':('universal','term'),
    'distribute':('variable','antecedent','consequent'),
    'eq_subst':('variable','template','left','right'), 'mp':('antecedent','implication'),
    'generalize':('variable','source'), 'induction':('variable','template'),
    'assumption':('index',), 'block':('name','inputs')}

def freeze(x):
    if isinstance(x,list): return tuple(freeze(a) for a in x)
    if isinstance(x,dict): return {k:freeze(v) for k,v in x.items()}
    return x

def fields(x, keys):
    if type(x) is not dict or set(x)!=set(keys): raise ValueError('invalid fields')

def integer(x):
    if type(x) is not int or x<0: raise ValueError('nonnegative integer required')
    return x

def schema(theory,kernel,variable,template):
    if 'nat-induction' not in theory['schemas']: raise ValueError('schema not enabled')
    if kernel.functions.get('zero')!=0 or kernel.functions.get('succ')!=1: raise ValueError('missing arithmetic signature')
    if type(variable) is not str: raise ValueError('variable name required')
    kernel.formula(template)
    zero_case=logic.substitute(template,variable,logic.F('zero'))
    successor_case=logic.substitute(template,variable,logic.F('succ',logic.V(variable)))
    value=logic.Imp(('and',zero_case,logic.All(variable,logic.Imp(template,successor_case))),logic.All(variable,template))
    for other in sorted(logic.free(template)-{variable},reverse=True): value=logic.All(other,value)
    return value

def replay(payload,expected_problem_sha256=None):
    """Return accepted/rejected with independently expanded root evidence."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON field')
            result[key]=value
        return result
    def bad_number(_): raise ValueError('inexact JSON number')
    try:
        raw=json.loads(payload.decode('utf-8'),object_pairs_hook=pairs,parse_float=bad_number,parse_constant=bad_number)
        fields(raw,('protocol','theory','blocks','proof','target'))
        pinned={name:raw[name] for name in ('protocol','theory','target')}
        fingerprint=hashlib.sha256(json.dumps(pinned,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')).hexdigest()
        if expected_problem_sha256 is not None and fingerprint!=expected_problem_sha256: raise ValueError('problem changed')
        if raw['protocol']!='gcts-fol-1': raise ValueError('unknown protocol')
        d=freeze(raw); theory=d['theory']; fields(theory,('functions','predicates','axioms','schemas'))
        for signature in (theory['functions'],theory['predicates']):
            if type(signature) is not dict: raise ValueError('signature object required')
            for name,arity in signature.items():
                if type(name) is not str: raise ValueError('name required')
                integer(arity)
        if type(theory['schemas']) is not tuple or any(x!='nat-induction' for x in theory['schemas']) or len(set(theory['schemas']))!=len(theory['schemas']): raise ValueError('invalid schemas')
        if type(theory['axioms']) is not dict or any(type(k) is not str for k in theory['axioms']): raise ValueError('invalid axiom map')
        base=logic.Kernel(theory['functions'],theory['predicates'],theory['axioms']); base.formula(d['target'])
        blocks={}; block_evidence=[]
        def expand(lines,assumptions,assumption_indices,out,axioms,available):
            if type(lines) is not tuple or not lines: raise ValueError('proof list required')
            mapping=[]; forbidden=set().union(*(logic.free(a) for a in assumptions))
            def prior(i):
                integer(i)
                if i>=len(mapping): raise ValueError('forward reference')
                return mapping[i]
            for item in lines:
                if type(item) is not dict or item.get('rule') not in FIELDS: raise ValueError('rule required')
                rule=item['rule']; fields(item,('rule','formula')+FIELDS[rule]); a=item['formula']; base.formula(a)
                if rule=='assumption':
                    i=integer(item['index'])
                    if i>=len(assumptions) or a!=assumptions[i]: raise ValueError('bad assumption')
                    mapping.append(assumption_indices[i]); continue
                if rule=='block':
                    name=item['name']
                    if type(name) is not str or name not in available: raise ValueError('block order')
                    b=available[name]; inputs=item['inputs']
                    if type(inputs) is not tuple or len(inputs)!=len(b['premises']): raise ValueError('input arity')
                    references=tuple(prior(i) for i in inputs)
                    if tuple(out[i]['formula'] for i in references)!=b['premises'] or a!=b['conclusion']: raise ValueError('interface mismatch')
                    result=expand(b['proof'],b['premises'],references,out,axioms,b['available'])
                    mapping.append(result); continue
                emitted=dict(item)
                if rule=='induction':
                    expected=schema(theory,base,item['variable'],item['template'])
                    if a!=expected: raise ValueError('wrong induction instance')
                    name='@oracle-induction-'+str(len(axioms))
                    while name in axioms: name+='!'
                    axioms[name]=expected; emitted=dict(rule='axiom',formula=a,name=name)
                elif rule=='axiom':
                    if type(item['name']) is not str or item['name'] not in theory['axioms']: raise ValueError('undeclared axiom')
                elif rule=='mp':
                    emitted.update(antecedent=prior(item['antecedent']),implication=prior(item['implication']))
                elif rule=='generalize':
                    if type(item['variable']) is not str or item['variable'] in forbidden: raise ValueError('eigenvariable restriction')
                    emitted['source']=prior(item['source'])
                out.append(emitted); mapping.append(len(out)-1)
            return mapping[-1]
        if type(d['blocks']) is not tuple: raise ValueError('blocks list required')
        for b in d['blocks']:
            fields(b,('name','premises','conclusion','proof')); name=b['name']
            if type(name) is not str or name in blocks or type(b['premises']) is not tuple: raise ValueError('block declaration')
            base.formula(b['conclusion']); out=[]; indices=[]; axioms=dict(theory['axioms'])
            for i,a in enumerate(b['premises']):
                base.formula(a); closed=a; names=sorted(logic.free(a))
                for x in reversed(names): closed=logic.All(x,closed)
                key='@oracle-assumption-'+str(i)
                while key in axioms: key+='!'
                axioms[key]=closed; out.append(dict(rule='axiom',formula=closed,name=key)); source=len(out)-1
                for x in names:
                    instance=logic.substitute(closed[2],closed[1],logic.V(x))
                    out.append(dict(rule='instantiate',formula=logic.Imp(closed,instance),universal=closed,term=logic.V(x)))
                    out.append(dict(rule='mp',formula=instance,antecedent=source,implication=len(out)-1))
                    source=len(out)-1; closed=instance
                indices.append(source)
            final=expand(b['proof'],b['premises'],indices,out,axioms,blocks)
            out=out[:final+1]
            if out[-1]['formula']!=b['conclusion'] or not logic.Kernel(base.functions,base.predicates,axioms).check(out,b['conclusion']): raise ValueError('expanded block rejected')
            block_evidence.append(dict(name=name,expanded_lines=len(out)))
            blocks[name]=dict(b,available=dict(blocks))
        out=[]; axioms=dict(theory['axioms']); final=expand(d['proof'],(),(),out,axioms,blocks)
        out=out[:final+1]
        if not logic.Kernel(base.functions,base.predicates,axioms).check(out,d['target']): raise ValueError('expanded root rejected')
        return dict(status='accepted',expanded_lines=len(out),proof=out,
                    schema_instances=len(axioms)-len(theory['axioms']),axioms=axioms,blocks=block_evidence)
    except (ValueError,TypeError,KeyError,IndexError,RecursionError,UnicodeError) as exc:
        return dict(status='rejected',reason=str(exc))

def audit(path):
    started=time.perf_counter(); path=pathlib.Path(path); data=json.loads(path.read_text()); count=expanded=0
    for reused in data['reuse']:
        payload=(path.parent/reused['file']).read_bytes()
        if hashlib.sha256(payload).hexdigest()!=reused['sha256']: raise AssertionError('reused evidence changed')
        parent=json.loads(payload)
        for item in data['positive_cases']:
            if item.get('reuse',{}).get('parent')!=reused['file']: continue
            source=next(r for r in parent['logical_runs'] if r['target']==item['reuse']['target'] and r['lane']==item['reuse']['lane'])
            request=json.loads(item['certificate'])
            if request['proof']!=source['kernel_proof'] or request['theory']['axioms']!=parent['logical_declaration']['axioms']:
                raise AssertionError('reused assembly changed')
    for group in ('positive_cases','adversarial_cases','propositional_cases','repeated_blocks','budget_controls','problem_binding'):
        for item in data[group]:
            payload=item['certificate'].encode('ascii')
            if hashlib.sha256(payload).hexdigest()!=item['certificate_sha256']: raise AssertionError('certificate hash mismatch')
            result=replay(payload,item.get('expected_problem_sha256')); reported=item['result']['status']
            if reported=='unknown_resource_budget':
                if result['status']!='accepted': raise AssertionError('budget control is not a valid certificate')
            elif result['status']!=reported: raise AssertionError('checker/oracle mismatch: '+item['name'])
            if 'expanded_lines' in item and result.get('expanded_lines')!=item['expanded_lines']: raise AssertionError('expansion changed')
            count+=1; expanded+=result.get('expanded_lines',0)
    evidence=dict(status='passed',certificates=count,expanded_primitive_lines=expanded,
                  seconds=time.perf_counter()-started,audit_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  frozen_kernel_sha256=hashlib.sha256(pathlib.Path(logic.__file__).read_bytes()).hexdigest(),
                  method='independent decoding and schema/interface replay; all blocks expanded; old Kernel checks every expanded primitive proof')
    data['independent_audit']=evidence; path.write_text(json.dumps(data,separators=(',',':'))+'\n'); return evidence

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'docs/research/gcts-rl-renewal/serialized-kernel-001.json'),indent=2))
