"""Adversarial unrestricted-FOL, exact-instance and altered-refutation gates."""
import copy,json,pathlib,time
import external_left_successor_focus as f
from external_prover_check import formula_text
from external_left_successor_inputs import dump

def run(path):
    began=time.perf_counter();events=[];certificates={}
    def relation(name,ps,target,accepted):
        parents=[formula_text(s) if isinstance(s,str) else s for s in ps];child=formula_text(target) if isinstance(target,str) else target
        try:
            result=f.consequence(parents,child);f.replay_consequence(parents,child,result);status='checked'
            if not accepted:raise AssertionError('unsound acceptance '+name)
            certificates[name]=(parents,child,result)
        except (ValueError,TimeoutError) as error:
            status='unknown'
            if accepted:raise
        events.append(dict(name=name,expected='checked' if accepted else 'unknown',observed=status))
    relation('universal_function_instance',['![X]:f(X)=X'],'f(a)=a',True)
    relation('successor_context_congruence',['![X]:f(X)=X'],'g(f(a))=g(a)',True)
    relation('universal_parameter_dependence',['![X]:f(X,X)=X'],'f(a,a)=a',True)
    relation('distinct_arguments_are_not_diagonal',['![X]:f(X,X)=X'],'f(a,b)=a',False)
    relation('finite_domain_sample_is_not_universal',['p(a)'],'![X]:p(X)',False)
    relation('finite_two_names_do_not_exhaust_domain',['p(a)','p(b)'],'![X]:p(X)',False)
    relation('idempotent_function_is_not_identity',['![X]:f(f(X))=f(X)'],'![X]:f(X)=X',False)
    relation('existential_witness_cannot_be_uniform',['![X]:?[Y]:p(X,Y)'],'?[Y]:![X]:p(X,Y)',False)
    relation('existential_witness_cannot_be_captured',['![X]:?[Y]:p(X,Y)'],'![X]:p(X,X)',False)
    relation('reverse_quantifier_order_not_implied',['![X]:?[Y]:f(X,Y)=X'],'?[Y]:![X]:f(X,Y)=X',False)
    relation('empty_premises_do_not_imply_equality',[],'a=b',False)
    reserved=('fun','__checker_s1',())
    relation('reserved_internal_symbol_rejected',['![X]:f(X)=X'],('eq',('fun','f',(reserved,)),reserved),False)
    parents,child,good=certificates['universal_function_instance']
    source=next(i for i,e in enumerate(good['certificate']['instances']) if e['substitution'])
    mutations=[]
    def reject(name,change):
        bad=copy.deepcopy(good);change(bad)
        try:f.replay_consequence(parents,child,bad)
        except (ValueError,TypeError,IndexError,KeyError) as error:
            mutations.append(dict(name=name,status='rejected',error=repr(error)));return
        raise AssertionError('corrupt exact-instance certificate accepted '+name)
    reject('missing_universal_substitution',lambda r:r['certificate']['instances'][source]['substitution'].clear())
    reject('extra_universal_substitution',lambda r:r['certificate']['instances'][source]['substitution'].update(unbound=('fun','a',())))
    reject('unbound_substitution_variable',lambda r:r['certificate']['instances'][source]['substitution'].update({next(iter(r['certificate']['instances'][source]['substitution'])):('var','X')}))
    reject('introduced_function_has_no_provenance',lambda r:r['certificate']['instances'][source]['substitution'].update({next(iter(r['certificate']['instances'][source]['substitution'])):('fun','undeclared',())}))
    reject('wrong_function_arity',lambda r:r['certificate']['instances'][source]['substitution'].update({next(iter(r['certificate']['instances'][source]['substitution'])):('fun','f',())}))
    reject('wrong_source_clause',lambda r:r['certificate']['instances'][0].update(clause=999999))
    reject('changed_ground_clause',lambda r:r['certificate']['instances'][0].update(ground_clause=[]))
    reject('changed_clausal_preprocessing',lambda r:r['certificate']['universal_clauses'].clear())
    reject('changed_internal_witness_provenance',lambda r:r['certificate']['internal_witnesses'].append(('fake',0)))
    reject('finite_satisfiability_is_not_a_certificate',lambda r:r['certificate']['refutation'].update(status='unknown_ground_satisfiable'))
    reject('empty_equality_conflict',lambda r:r['certificate']['refutation'].update(tree=['euf']))
    reject('one_branch_missing',lambda r:r['certificate']['refutation'].update(tree=['split',0,['euf']]))
    # A genuine ground-refutation tree cannot be recycled for another relation.
    try:f.replay_consequence([],formula_text('a=b'),good)
    except ValueError as error:mutations.append(dict(name='different_logical_relation',status='rejected',error=repr(error)))
    else:raise AssertionError('unbound relation accepted')
    output=dict(status='passed',relations=events,mutations=mutations,seconds=time.perf_counter()-began,scope='Finite samples never justify universal entailment; lexical witnesses, exact ground substitutions and both refutation branches remain mandatory. No target proof is supplied.')
    dump(path,output);return output

if __name__=='__main__':
    import sys
    r=run(pathlib.Path(sys.argv[1]));print('FOCUS COUNTEREXAMPLES/MUTATIONS PASSED',len(r['relations']),len(r['mutations']),flush=True)
