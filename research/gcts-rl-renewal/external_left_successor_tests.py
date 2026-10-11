"""Unsupported-feature and closure fixtures, never target proof sequences."""
import copy,json,time
from external_left_successor_inputs import OUT,SOURCE,load,dump,validate_theory,target_body,schema,inputs
from external_prover_inputs import Symbols
from external_prover_check import native_formula,free,alpha,substitute
from external_induction_tstp_audit import exact_input

def independent_schema(p,x,m):
    # Separate tuple AST/free-variable/term-substitution implementation.
    f=native_formula(p,m);base=substitute(f,{x:('fun',m['functions']['zero'],())});step=substitute(f,{x:('fun',m['functions']['succ'],(('var',x),))})
    result=('imp',('and',base,('forall',x,('imp',f,step))),('forall',x,f))
    for v in reversed(sorted(free(f)-{x})):result=('forall',v,result)
    return result

def main():
    began=time.perf_counter();spec=load(SOURCE/'plan.json')['case'];sy=Symbols(spec['theory']);m=dict(functions=sy.functions,predicates=sy.predicates);variables,body=target_body(spec['target']);cases=[]
    for x in variables:
        result=schema(body,x)
        if alpha(native_formula(result,m))!=alpha(independent_schema(body,x,m)) or free(native_formula(result,m)):raise ValueError('all remaining parameters are universally closed')
        cases.append(dict(name='complete target predicate with induction variable '+x,status='checked_fixture_only',parameters=[v for v in variables if v!=x]))
    def reject(name,f):
        try:f()
        except (ValueError,KeyError):cases.append(dict(name=name,status='rejected_unsupported_feature'))
        else:raise ValueError('unsupported feature admitted '+name)
    for name,change in [('missing explicit schema',lambda t:t.update(schemas=[])),('unknown schema',lambda t:t.update(schemas=['other'])),('extra hidden axiom field',lambda t:t.update(hidden_axioms={})),('extra theory signature',lambda t:t['functions'].update(extra=0)),('boolean arity',lambda t:t['functions'].update(succ=True)),('unclosed axiom',lambda t:t['axioms'].update(AZ=['eq',['var','x'],['var','x']]))]:
        t=copy.deepcopy(spec['theory']);change(t);reject(name,lambda t=t:validate_theory(t))
    reject('vacuous/missing induction variable',lambda:schema(body,'z'))
    reject('quantified predicate outside declared equation fragment',lambda:schema(['all','x',body],'x'))
    bad=copy.deepcopy(spec['target']);bad[2][1]='x';reject('duplicated target binder',lambda:target_body(bad))
    bad=copy.deepcopy(spec['target']);bad=bad[2];reject('unbound target parameter',lambda:target_body(bad))
    f=schema(body,'y');changed=copy.deepcopy(f);changed=changed[2]
    if not free(native_formula(changed,m)):raise ValueError('fixture must genuinely lose its parameter closure')
    cases.append(dict(name='dropping parameter closure is observably open',status='checked_fixture_only',reason='Independent tuple free-variable analysis detects the missing universal parameter.'))
    result=dict(status='passed',cases=cases,seconds=time.perf_counter()-began,target_prover_runs=0,scope='Input/closure/unsupported-feature fixtures only. No target derivation or winning induction choice is authored.')
    dump(OUT/'tests.json',result);print('UNSUPPORTED/CLOSURE FIXTURES PASSED',len(cases),flush=True)

if __name__=='__main__':main()
