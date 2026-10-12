"""Synthetic AST corpus authoring only; no engine/kernel/model/result imports."""
import json
from pathlib import Path
OUT=Path('.gcts-active/receptor-matching-cross-domain-source-20261011')
def V(n):return ['var',n]
def F(n,*xs):return ['fun',n,list(xs)]
def P(n,*xs):return ['pred',n,list(xs)]
def E(a,b):return ['eq',a,b]
def N(a):return ['not',a]
def A(a,b):return ['and',a,b]
def Q(x,a):return ['all',x,a]
def I(a,b):return ['imp',a,b]
x,y,z=map(V,['x','y','z']);a,b,c=map(F,['a','b','c']);zero=F('zero')
cases=[]
def add(name,pattern,binders,available,status,bindings=None,note=None):
 cases.append(dict(id=name,kind='literal_receptor',pattern=pattern,prefix_binders=binders,available=available,
  expected=dict(status=status,bindings=bindings or {}),scope_note=note or 'Literal structural advice only; no logical consequence asserted.'))
add('distinct-slots',P('Rel',x,y),['x','y'],P('Rel',a,b),'match',{'x':a,'y':b})
add('distinct-slots-same-constant-permitted',P('Rel',x,y),['x','y'],P('Rel',a,a),'match',{'x':a,'y':a},'Distinct bound variables do not require distinct images.')
add('prefix-renamed-slots',P('Rel',V('u'),V('v')),['u','v'],P('Rel',a,b),'match',{'u':a,'v':b},'Only prefix-slot renaming, not general alpha-equivalence rewriting.')
add('repeated-slot-agrees',P('Rel',x,x),['x'],P('Rel',a,a),'match',{'x':a})
add('repeated-slot-disagrees',P('Rel',x,x),['x'],P('Rel',a,b),'miss')
add('literal-rigid-completed-constant',P('Rel',c,y),['y'],P('Rel',c,a),'match',{'y':a})
add('completed-constant-cannot-rebind',P('Rel',c,y),['y'],P('Rel',b,a),'miss')
add('zero-arity-arithmetic-image',E(F('add',x,zero),x),['x'],E(F('add',a,zero),a),'match',{'x':a})
add('arithmetic-compound-constructor-literal',E(F('succ',F('add',x,zero)),F('succ',x)),['x'],E(F('succ',F('add',a,zero)),F('succ',a)),'match',{'x':a})
add('compound-slot-image-neutral',P('Rel',x),['x'],P('Rel',F('succ',zero)),'neutral',note='Compound substitution image outside the first bounded matcher, not a logical failure.')
add('free-recipient-slot-image-neutral',P('Rel',x),['x'],P('Rel',V('freeRecipient')),'neutral')
add('free-pattern-variable-not-prefix-neutral',P('Rel',z),['x'],P('Rel',a),'neutral')
add('rigid-zero-arity-exact',E(zero,zero),[],E(zero,zero),'match')
add('rigid-zero-arity-name-miss',E(zero,zero),[],E(a,a),'miss')
add('predicate-name-literal',P('P',x),['x'],P('Q',a),'miss')
add('predicate-arity-literal',P('P',x,y),['x','y'],P('P',a),'miss')
add('term-constructor-name-literal',E(F('succ',x),a),['x'],E(F('other',b),a),'miss')
add('term-constructor-arity-literal',E(F('pair',x,a),b),['x'],E(F('pair',c),b),'miss')
add('ordered-fixed-argument-miss',P('Rel',x,c),['x'],P('Rel',c,a),'miss')
add('ordered-variable-bindings-retained',P('Rel',x,y),['x','y'],P('Rel',b,a),'match',{'x':b,'y':a})
add('polarity-negative-match',N(P('P',x)),['x'],N(P('P',a)),'match',{'x':a})
add('polarity-negative-vs-positive',N(P('P',x)),['x'],P('P',a),'miss')
add('double-negation-not-normalized',P('P',x),['x'],N(N(P('P',a))),'miss')
add('ordered-conjunction-match',A(P('P',x),P('Q',x)),['x'],A(P('P',a),P('Q',a)),'match',{'x':a})
add('ordered-conjunction-miss',A(P('P',x),P('Q',x)),['x'],A(P('Q',a),P('P',a)),'miss')
add('ordered-equality-not-symmetry',E(a,b),[],E(b,a),'miss')
add('nested-pattern-quantification-neutral',A(P('P',x),Q('y',P('Q',y))),['x'],A(P('P',a),Q('y',P('Q',y))),'neutral')
add('quantified-recipient-neutral',P('P',x),['x'],Q('y',P('P',y)),'neutral')
add('shadowed-leading-prefix-neutral',P('P',x),['x','x'],P('P',a),'neutral')
add('unsupported-exists-neutral',['exists','x',P('P',x)],[],P('P',a),'neutral')
add('unsupported-or-neutral',['or',P('P',x),P('Q',x)],['x'],['or',P('P',a),P('Q',a)],'neutral')
add('bot-literal-match',['bot'],[],['bot'],'match')
add('implication-order-literal',I(P('P',x),P('Q',x)),['x'],I(P('Q',a),P('P',a)),'miss')
availability=[
 dict(id='mark-only-not-available',kind='availability',state=dict(selected_outputs=[],assigned_formula_marks=[dict(row=3,formula=P('P',a),occupied=False)]),expected_rows=[],expected_available_formulas=[],scope_note='An assigned marking constrains future output; it supplies no currently available hypothesis.'),
 dict(id='duplicate-formulas-distinct-rows',kind='availability',state=dict(selected_outputs=[dict(row=0,formula=P('P',a)),dict(row=1,formula=P('P',a))],assigned_formula_marks=[]),expected_rows=[0,1],expected_available_formulas=[P('P',a),P('P',a)],scope_note='Advice may be Boolean but primitive/reference identities must not be merged.'),
 dict(id='separate-facts-not-conjoined',kind='availability',state=dict(selected_outputs=[dict(row=0,formula=P('P',a)),dict(row=1,formula=P('Q',a))],assigned_formula_marks=[]),pattern=A(P('P',x),P('Q',x)),prefix_binders=['x'],expected_status='miss',expected_rows=[0,1],expected_available_formulas=[P('P',a),P('Q',a)],scope_note='No conjunction construction or logical inference is permitted by receptor ranking.'),
 dict(id='arithmetic-command-role-only-incomplete',kind='arithmetic_adapter',rows=[dict(row=0,selected_roles=[0],command_guard_agree=True,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[dict(row=0,formula=E(zero,zero))],expected_known_rows=[],scope_note='Command placement alone is not a complete C/G/I1/I2 row.'),
 dict(id='arithmetic-three-roles-incomplete',kind='arithmetic_adapter',rows=[dict(row=0,selected_roles=[0,1,2],command_guard_agree=True,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[],expected_known_rows=[]),
 dict(id='arithmetic-four-roles-zero-input-complete',kind='arithmetic_adapter',rows=[dict(row=0,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[],expected_known_rows=[0]),
 dict(id='arithmetic-complete-output-with-unavailable-source',kind='arithmetic_adapter',rows=[dict(row=2,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[1],source_formulas_agree=True,formula=E(a,a))],assigned_formula_marks=[dict(row=1,formula=E(a,a))],expected_known_rows=[],scope_note='Complete later row with an assigned but unproved earlier-source formula is not a known output.'),
 dict(id='arithmetic-complete-known-dependency',kind='arithmetic_adapter',rows=[dict(row=1,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[0],source_formulas_agree=True,formula=E(a,a)),dict(row=0,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[],expected_known_rows=[0,1]),
 dict(id='arithmetic-guard-command-mismatch',kind='arithmetic_adapter',rows=[dict(row=0,selected_roles=[0,1,2,3],command_guard_agree=False,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[],expected_known_rows=[]),
 dict(id='arithmetic-source-formula-mismatch',kind='arithmetic_adapter',rows=[dict(row=1,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[0],source_formulas_agree=False,formula=E(a,a)),dict(row=0,selected_roles=[0,1,2,3],command_guard_agree=True,ordered_sources=[],source_formulas_agree=True,formula=E(zero,zero))],assigned_formula_marks=[],expected_known_rows=[0])
]
corpus=dict(schema='independent-synthetic-receptor-cross-domain-corpus-v1',scope='Synthetic structural ranking advice, not mathematical inference/proof search. No actual model/result/target word.',api_pending=True,matcher_cases=cases,availability_cases=availability,
 expectation_scope='Gold expectations follow the prospective prefix-only literal matcher; producer API integration and independent fixture execution remain separately gated. Arithmetic adapter cases are declarative completion requirements, not an engine implementation.')
with (OUT/'synthetic-corpus-v1.json').open('x') as f:json.dump(corpus,f,indent=2);f.write('\n')
print(json.dumps({'status':'synthetic_corpus_authored','matcher_cases':len(cases),'availability_cases':len(availability)}))
