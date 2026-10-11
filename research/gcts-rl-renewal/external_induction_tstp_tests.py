"""Full-adapter soundness fixtures; authored fixture proofs are NOT target runs."""
import copy,json,pathlib,time
from external_prover_inputs import sha
from external_prover_check import formula_text
from external_induction_tstp_check import check_output,consequence,replay_consequence,reconstruct_witnesses,compact_extension
from external_prover_check import records

ROOT=pathlib.Path(__file__).resolve().parents[2];PRIVATE=ROOT/'.gcts-active/external-induction-tstp-20261011'

def sample():
    mapping=dict(functions={},predicates={},function_arities={},predicate_arities={},entries=[dict(name='goal',role='conjecture',original_name='Fixture reflexivity, not arithmetic target',formula=['all','n',['eq',['var','n'],['var','n']]])])
    output="""% SZS output start CNFRefutation
fof(g,conjecture,![X]:(X=X),file('fixture.p',goal)).
fof(n,negated_conjecture,~(![X]:(X=X)),inference(assume_negation,[status(cth)],[g])).
fof(k,plain,(esk0!=esk0),inference(fof_skolemize,[status(esa)],[n])).
cnf(f,plain,$false,inference(cn,[status(thm)],[k])).
% SZS output end CNFRefutation
"""
    return mapping,output

def main():
    began=time.perf_counter();PRIVATE.mkdir(parents=True,exist_ok=True);cases=[]
    def reject(name,fn,reason):
        try:fn()
        except (ValueError,KeyError) as e:cases.append(dict(name=name,status='rejected expected corruption',reason=reason,error=str(e)))
        else:raise AssertionError('bad fixture accepted '+name)
    mapping,output=sample();check=check_output(output,mapping,'fixture.p');saved=json.loads(json.dumps(check));replay=check_output(output,mapping,'fixture.p',saved=saved)
    cases.append(dict(name='whole fixture and serialized full replay',status='accepted fixture only',reason='Inputs, target negation, fresh witness extension, every consequence and contradiction are fully reconstructed.',steps=check['steps']))
    mutations=[('wrong target input',output.replace('![X]:(X=X)','![X]:(X!=X)',1),'Original AST/role binding is checked directly.'),
               ('wrong input path',output.replace("file('fixture.p'","file('elsewhere.p'"),'File identity is exact.'),
               ('forward proof parent',output.replace('[n])).','[future])).'),'Strict previous-node DAG provenance is required.'),
               ('positive conjecture as premise',output.replace('[k])).','[g])).'),'The desired theorem is never an assumed proof fact.'),
               ('incorrect negation',output.replace('~(![X]:(X=X))','![X]:(X=X)'),'Polarity-correct target negation is mandatory.'),
               ('missing negation',output.replace('assume_negation','fof_nnf'),'No unregistered negated-target assumption is allowed.'),
               ('unknown introduction rule',output.replace('fof_skolemize','magic'),'A fresh symbol name never suffices for admission.'),
               ('Skolem wrong status',output.replace('status(esa)','status(thm)'),'Exact isolated conservative transformation requires the expected relation annotation.'),
               ('Skolem literal reversed',output.replace('(esk0!=esk0)','(esk0=esk0)'),'Witness reconstruction retains every literal polarity.'),
               ('extra unintroduced predicate',output.replace('$false','p(esk0)'),'Fresh predicates/definitions remain unsupported.'),
               ('Skolem arity changed later',output.replace('cnf(f,plain,$false','cnf(f,plain,(esk0(esk0)!=esk0)'),'Later uses retain the declared witness arity.'),
               ('final contradiction removed',output.replace('cnf(f,plain,$false','cnf(f,plain,(esk0!=esk0)'),'The last formula must be a checked contradiction.'),
               ('opaque introduced source',output.replace('inference(fof_skolemize,[status(esa)],[n])','introduced(definition,[new_symbols(skolem,[esk0])],[n])'),'Opaque symbol introductions cannot establish validity.'),
               ('repeated node identity',output.replace('cnf(f,','cnf(k,'),'Node identities are unique.')]
    for name,changed,reason in mutations:reject(name,lambda changed=changed:check_output(changed,mapping,'fixture.p'),reason)
    for name,field in [('context digest corrupt','context_after_sha256'),('registry digest corrupt','registry_before_sha256')]:
        bad=copy.deepcopy(saved);bad['checks'][2][field]='0'*64;reject(name,lambda bad=bad:check_output(output,mapping,'fixture.p',saved=bad),'Serialized certificates bind the entire shared context and fresh-symbol registry.')
    bad=copy.deepcopy(saved);bad['checks'][3]['proof']['certificate']['check']['refutation']['tree']=['clause',999]
    reject('ordinary refutation tree corrupt',lambda:check_output(output,mapping,'fixture.p',saved=bad),'Actual contradiction trees are replayed, not accepted by status string.')

    # A satisfiable theory with an old named point cannot justify choosing it
    # as the counterexample to a universal target. This would prove a false
    # theorem if original symbols were not reserved before reading the trace.
    m=dict(functions={'named':'esk0'},predicates={'P':'p'},function_arities={'esk0':0},predicate_arities={'p':1},entries=[dict(name='a',role='axiom',original_name='named fact',formula=['pred','P',[['fun','named',[]]]]),dict(name='goal',role='conjecture',original_name='invalid universal',formula=['all','x',['pred','P',[['var','x']]]])])
    bad="""% SZS output start CNFRefutation
fof(a,axiom,p(esk0),file('fixture.p',a)).
fof(g,conjecture,![X]:p(X),file('fixture.p',goal)).
fof(n,negated_conjecture,?[X]:~p(X),inference(assume_negation,[status(cth)],[g])).
fof(k,plain,~p(esk0),inference(fof_skolemize,[status(esa)],[n])).
cnf(f,plain,$false,inference(cn,[status(thm)],[a,k])).
% SZS output end CNFRefutation
"""
    reject('old input constant causes false theorem',lambda:check_output(bad,m,'fixture.p'),'The original input reserves a named object even before witness processing; existential counterexamples cannot be chosen arbitrarily.')
    m=dict(functions={},predicates={'P':'p'},function_arities={},predicate_arities={'p':1},entries=[dict(name='a',role='axiom',original_name='has P',formula=['exists','x',['pred','P',[['var','x']]]]),dict(name='b',role='axiom',original_name='has non-P',formula=['exists','y',['not',['pred','P',[['var','y']]]]]),dict(name='goal',role='conjecture',original_name='false fixture',formula=['bot'])])
    bad="""% SZS output start CNFRefutation
fof(a,axiom,?[X]:p(X),file('fixture.p',a)).
fof(b,axiom,?[Y]:~p(Y),file('fixture.p',b)).
fof(g,conjecture,$false,file('fixture.p',goal)).
fof(n,negated_conjecture,$true,inference(assume_negation,[status(cth)],[g])).
fof(k0,plain,p(esk0),inference(fof_skolemize,[status(esa)],[a])).
fof(k1,plain,~p(esk0),inference(fof_skolemize,[status(esa)],[b])).
cnf(f,plain,$false,inference(cn,[status(thm)],[k0,k1])).
% SZS output end CNFRefutation
"""
    reject('cross-node reused witness causes false theorem',lambda:check_output(bad,m,'fixture.p'),'One global context/registry rejects reusing a witness from another satisfiable existential premise.')
    for name,p,c in [('lost universal dependency','![X]:?[Y]:(X!=Y)','![X]:(X!=esk0)'),('later universal captured','?[X]:![Y]:r(X,Y)','![Y]:r(esk0(Y),Y)'),('universal quantifier dropped','![X]:?[Y]:r(X,Y)','r(a,esk0(a))')]:
        reject(name,lambda p=p,c=c:reconstruct_witnesses(formula_text(p),formula_text(c)),'The independently recovered witness proposal cannot change dependencies, capture later variables or narrow a universal scope.')
    for name,p,c in [('quantifier order changed','![X]:?[Y]:r(X,Y)','?[Y]:![X]:r(X,Y)'),('existence becomes named instance','?[X]:p(X)','p(a)'),('ground becomes universal','p(a)','![X]:p(X)')]:
        reject(name,lambda p=p,c=c:consequence([formula_text(p)],formula_text(c)),'Neither propositional abstraction nor finite Herbrand/EUF can establish this invalid unrestricted entailment.')
    p=formula_text('(a=a) & (![X]:p(X))');c=formula_text('![Y]:p(Y)');proof=consequence([p],c);replay_consequence([p],c,json.loads(json.dumps(proof)))
    cases.append(dict(name='quantified atom propositional projection',status='accepted fixture only',reason='Uniform abstraction admits a propositional consequence while preserving the full quantified formula as an atom.'))
    bad=copy.deepcopy(proof);bad['certificate']['atoms']={'fake':'abstract0'}
    reject('proposition atom identity corrupt',lambda:replay_consequence([p],c,bad),'Quantified formula identities are independently rebound during certificate replay.')
    mapping,output=sample()
    compact=output.replace('inference(fof_skolemize,[status(esa)],[n])','inference(distribute,[status(thm)],[inference(fof_nnf,[status(thm)],[inference(skolemize,[status(esa)],[inference(variable_rename,[status(thm)],[inference(fof_nnf,[status(thm)],[n])])])])])')
    checked=check_output(compact,mapping,'fixture.p');serialized=json.loads(json.dumps(checked));check_output(compact,mapping,'fixture.p',saved=serialized)
    cases.append(dict(name='compact Skolem fixture with explicit replacement and complete serialized replay',status='accepted fixture only',reason='Exact parent NNF, scope-preserving fresh witness formula and displayed-child consequence are independently certified.'))
    for name,changed in [
        ('compact two Skolem annotations',compact.replace('inference(variable_rename,[status(thm)]','inference(skolemize,[status(esa)]')),
        ('compact hidden second parent',compact.replace('[n])])])','[n,g])])])')),
        ('compact forbidden wrapper',compact.replace('inference(distribute','inference(magic')),
        ('compact wrong wrapper relation',compact.replace('distribute,[status(thm)]','distribute,[status(esa)]')),
        ('compact wrong literal',compact.replace('(esk0!=esk0)','(esk0=esk0)')),
        ('compact fresh predicate',compact.replace('(esk0!=esk0)','q(esk0)')),
        ('compact disappeared witness',compact.replace('(esk0!=esk0)','$true'))]:
        reject(name,lambda changed=changed:check_output(changed,mapping,'fixture.p'),'Compact labels do not bypass exact parent provenance, witness scope/freshness or a full displayed-child consequence certificate.')
    for name,change in [
        ('compact witness path corrupt',lambda b:b['checks'][2]['reconstruction']['witnesses'][0].update(path=[2])),
        ('compact witness name corrupt',lambda b:b['checks'][2]['reconstruction']['witnesses'][0].update(symbol='elsewhere')),
        ('compact normalized AST corrupt',lambda b:b['checks'][2]['reconstruction'].update(normalized_parent=['top'])),
        ('compact intermediate AST corrupt',lambda b:b['checks'][2]['reconstruction'].update(witness_formula=['top'])),
        ('compact postprocessing tree corrupt',lambda b:b['checks'][2]['reconstruction']['postprocessing']['certificate']['check']['refutation'].update(tree=['clause',999]))]:
        b=copy.deepcopy(serialized);change(b);reject(name,lambda b=b:check_output(compact,mapping,'fixture.p',saved=b),'Replay binds and reconstructs every synthetic intermediate, lexical witness proposal and semantic consequence tree.')
    source=records(compact)[2]['source'];sig=dict(function_arities={},predicate_arities={'r':2})
    for name,p,c in [('compact omitted dependency','![X]:?[Y]:r(X,Y)','![X]:r(X,esk0)'),('compact captured later universal','?[X]:![Y]:r(X,Y)','![Y]:r(esk0(Y),Y)'),('compact narrowed universal scope','![X]:?[Y]:r(X,Y)','r(esk0,esk1)'),('compact false quantifier reorder','?[X]:![Y]:r(X,Y)','![Y]:r(esk0(Y),Y)')]:
        reject(name,lambda p=p,c=c:compact_extension(formula_text(p),formula_text(c),source,'n',sig,set(sig['predicate_arities'])),'The reconstructed original lexical dependencies must match every new function arity; unrelated subsequent normalization cannot waive that requirement.')
    for name,sig,reserved,p,c in [
        ('compact original constant is not fresh',dict(function_arities={'esk0':0},predicate_arities={'p':1}),{'p','esk0'},'?[X]:p(X)','p(esk0)'),
        ('compact earlier introduced witness is not fresh',dict(function_arities={},predicate_arities={'p':1}),{'p','esk0'},'?[X]:p(X)','p(esk0)'),
        ('compact inconsistent witness arity',dict(function_arities={},predicate_arities={'r':2}),{'r'},'?[X]:r(X,X)','r(esk0,esk0(esk0))'),
        ('compact sibling existentials merged',dict(function_arities={},predicate_arities={'p':1}),{'p'},'(?[X]:p(X)) & (?[Y]:~p(Y))','p(esk0) & ~p(esk0)'),
        ('compact later scope changes witness argument',dict(function_arities={},predicate_arities={'r':2}),{'r'},'![X]:?[Y]:r(X,Y)','![X]:r(X,esk0(a))')]:
        reject(name,lambda sig=sig,reserved=reserved,p=p,c=c:compact_extension(formula_text(p),formula_text(c),source,'n',sig,reserved),'Existing names, merged existential occurrences and altered arities/dependencies never establish conservative witness extension.')
    m=copy.deepcopy(mapping);m['function_arities']['__checker_s1']=0
    reject('original symbol enters checker Skolem namespace',lambda:check_output(compact,m,'fixture.p'),'Independent grounding has a private symbol namespace; exact input export uses disjoint f/p names and collisions fail closed.')
    checker=pathlib.Path(__file__).with_name('external_prover_check.py')
    if sha(checker.read_bytes())!='76c95c28d9cddbb5d18b4ce32ab7f2d23cd964e6420250d73efa97baa210835a':raise AssertionError('published checker changed')
    result=dict(status='passed',cases=cases,seconds=time.perf_counter()-began,target_prover_runs=0,scope='Authored development fixture proofs and counterexamples only; none counts as automatic arithmetic target discovery.')
    (PRIVATE/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status='passed',cases=len(cases),seconds=result['seconds']),indent=2))

if __name__=='__main__':main()
