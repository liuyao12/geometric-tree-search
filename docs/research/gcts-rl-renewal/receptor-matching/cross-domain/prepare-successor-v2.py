"""Refined source/synthetic corpus only. Preserve every v1 byte."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
c=json.loads((OUT/'synthetic-corpus-v1.json').read_text());c['schema']='independent-synthetic-receptor-cross-domain-corpus-v2'
def V(x):return ['var',x]
def F(x,*args):return ['fun',x,list(args)]
def P(x,*args):return ['pred',x,list(args)]
def A(p,q):return ['and',p,q]
x=V('x');a=F('a');b=F('b');z=F('zero');compound=F('succ',z)
def add(name,pattern,binders,available,status,bindings=None,note=None):
 c['matcher_cases'].append(dict(id=name,kind='literal_receptor',pattern=pattern,prefix_binders=binders,available=available,expected=dict(status=status,bindings=bindings or {}),scope_note=note or 'Synthetic advice only; not an inference or rejection.'))
add('definite-mismatch-after-compound-slot',P('Rel',x,a),['x'],P('Rel',compound,b),'miss',note='Literal rigid mismatch wins over a neutral unsupported slot image elsewhere.')
add('definite-mismatch-before-compound-slot',P('Rel',a,x),['x'],P('Rel',b,compound),'miss')
add('conjunction-mismatch-after-compound-slot',A(P('P',x),P('Q',a)),['x'],A(P('P',compound),P('Q',b)),'miss')
add('compound-slot-with-no-definite-mismatch',A(P('P',x),P('Q',a)),['x'],A(P('P',compound),P('Q',a)),'neutral')
add('global-quantification-still-neutral-despite-mismatch',A(P('P',a),['all','y',P('Q',V('y'))]),[],A(P('P',b),['all','y',P('Q',V('y'))]),'neutral')
add('empty-prefix-name-neutral',P('P',V('')),[''],P('P',a),'neutral')
add('empty-predicate-name-neutral',P('',x),['x'],P('',a),'neutral')
add('empty-function-name-neutral',P('P',x),['x'],P('P',F('')),'neutral')
c['expectation_scope']='Gold match/miss/neutral statuses and successful bindings follow the finalized narrow literal API. Nonmatch/neutral export no bindings. Definite literal mismatch outranks unsupported compound slot image within a supported formula; globally unsupported quantification/free recipient/empty symbol is neutral. Producer compatibility remains separately gated.'
with (OUT/'synthetic-corpus-v2.json').open('x') as f:json.dump(c,f,indent=2);f.write('\n')
s=(OUT/'synthetic_reference_controls_v1.py').read_text()
s=s.replace("isinstance(t[1],str):", "isinstance(t[1],str) and t[1]:")
s=s.replace("  if pattern and t[1] not in slots:raise Unsupported()", "  if not pattern or t[1] not in slots:raise Unsupported()")
s=s.replace("not isinstance(t[1],str) or not isinstance(t[2],list)", "not isinstance(t[1],str) or not t[1] or not isinstance(t[2],list)")
s=s.replace("isinstance(f[1],str) and isinstance(f[2],list)", "isinstance(f[1],str) and bool(f[1]) and isinstance(f[2],list)")
start=s.index('def term_match(');end=s.index('def structural_advice(',start)
s=s[:start]+'''def merge_status(values):
 # Eagerly examine all supported siblings; definite mismatch outranks neutral image.
 return 'miss' if 'miss' in values else 'neutral' if 'neutral' in values else 'match'
def term_match(pattern,recipient,slots,bindings):
 if pattern[0]=='var':
  if recipient[0]!='fun' or recipient[2]:return 'neutral'
  slot=pattern[1]
  if slot in bindings:return 'match' if bindings[slot]==recipient else 'miss'
  bindings[slot]=recipient;return 'match'
 if recipient[0]!='fun' or pattern[1]!=recipient[1] or len(pattern[2])!=len(recipient[2]):return 'miss'
 return merge_status([term_match(a,b,slots,bindings) for a,b in zip(pattern[2],recipient[2])])
def formula_match(pattern,recipient,slots,bindings):
 if pattern[0]!=recipient[0]:return 'miss'
 tag=pattern[0]
 if tag=='pred':
  if pattern[1]!=recipient[1] or len(pattern[2])!=len(recipient[2]):return 'miss'
  return merge_status([term_match(a,b,slots,bindings) for a,b in zip(pattern[2],recipient[2])])
 if tag=='eq':return merge_status([term_match(pattern[1],recipient[1],slots,bindings),term_match(pattern[2],recipient[2],slots,bindings)])
 if tag=='not':return formula_match(pattern[1],recipient[1],slots,bindings)
 if tag in ('and','imp'):return merge_status([formula_match(pattern[1],recipient[1],slots,bindings),formula_match(pattern[2],recipient[2],slots,bindings)])
 return 'match' if tag=='bot' else 'neutral'
''' + s[end:]
s=s.replace("any(not isinstance(v,str) for v in prefix_binders)", "any(not isinstance(v,str) or not v for v in prefix_binders)")
s=s.replace("  matched=formula_match(pattern,recipient,slots,bindings)\n  return dict(status='match' if matched else 'miss',bindings=bindings if matched else {})", "  status=formula_match(pattern,recipient,slots,bindings)\n  return dict(status=status,bindings=bindings if status=='match' else {})")
s=s.replace("synthetic-plan-v1.json", "synthetic-plan-v2.json").replace('synthetic-corpus-v1.json','synthetic-corpus-v2.json').replace('synthetic-reference-receipt-v1.json','synthetic-reference-receipt-v2.json')
s=s.replace('passed_independent_synthetic_reference_expectations','passed_independent_synthetic_reference_v2_expectations')
with (OUT/'synthetic_reference_controls_v2.py').open('x') as f:f.write(s)
print(json.dumps({'status':'refined_synthetic_successor_authored','matcher_cases':len(c['matcher_cases']),'availability_cases':len(c['availability_cases'])}))
