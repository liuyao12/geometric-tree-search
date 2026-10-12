"""Independent synthetic literal-pattern advice, not a logic kernel or engine.

Only this task's authored corpus/plan is read. No proof checking, arithmetic
normalization, quantifier substitution, graph legality or theorem lookup.
"""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
class Unsupported(Exception):pass
def term_shape(t,slots,pattern):
 if not isinstance(t,list) or not t:raise Unsupported()
 if t[0]=='var' and len(t)==2 and isinstance(t[1],str):
  if pattern and t[1] not in slots:raise Unsupported()
  return
 if t[0]!='fun' or len(t)!=3 or not isinstance(t[1],str) or not isinstance(t[2],list):raise Unsupported()
 for a in t[2]:term_shape(a,slots,pattern)
def formula_shape(f,slots,pattern):
 if not isinstance(f,list) or not f:raise Unsupported()
 if f[0]=='pred' and len(f)==3 and isinstance(f[1],str) and isinstance(f[2],list):
  for t in f[2]:term_shape(t,slots,pattern)
 elif f[0]=='eq' and len(f)==3:
  term_shape(f[1],slots,pattern);term_shape(f[2],slots,pattern)
 elif f[0]=='not' and len(f)==2:formula_shape(f[1],slots,pattern)
 elif f[0] in ('and','imp') and len(f)==3:
  formula_shape(f[1],slots,pattern);formula_shape(f[2],slots,pattern)
 elif f!=['bot']:raise Unsupported()
def term_match(pattern,recipient,slots,bindings):
 if pattern[0]=='var':
  if recipient[0]!='fun' or recipient[2]:raise Unsupported()
  slot=pattern[1]
  if slot in bindings:return bindings[slot]==recipient
  bindings[slot]=recipient;return True
 if recipient[0]!='fun':return False
 return (pattern[1]==recipient[1] and len(pattern[2])==len(recipient[2])
  and all(term_match(a,b,slots,bindings) for a,b in zip(pattern[2],recipient[2])))
def formula_match(pattern,recipient,slots,bindings):
 if pattern[0]!=recipient[0]:return False
 tag=pattern[0]
 if tag=='pred':return pattern[1]==recipient[1] and len(pattern[2])==len(recipient[2]) and all(term_match(a,b,slots,bindings) for a,b in zip(pattern[2],recipient[2]))
 if tag=='eq':return term_match(pattern[1],recipient[1],slots,bindings) and term_match(pattern[2],recipient[2],slots,bindings)
 if tag=='not':return formula_match(pattern[1],recipient[1],slots,bindings)
 if tag in ('and','imp'):return formula_match(pattern[1],recipient[1],slots,bindings) and formula_match(pattern[2],recipient[2],slots,bindings)
 return tag=='bot'
def structural_advice(pattern,prefix_binders,recipient):
 bindings={}
 try:
  if not isinstance(prefix_binders,list) or any(not isinstance(v,str) for v in prefix_binders) or len(prefix_binders)!=len(set(prefix_binders)):raise Unsupported()
  slots=set(prefix_binders);formula_shape(pattern,slots,True);formula_shape(recipient,slots,False)
  matched=formula_match(pattern,recipient,slots,bindings)
  return dict(status='match' if matched else 'miss',bindings=bindings if matched else {})
 except Unsupported:return dict(status='neutral',bindings={})
def arithmetic_known(case):
 # Declarative fixtures only: these agreement flags are NOT computed proof/kernel facts.
 known=set()
 for row in sorted(case['rows'],key=lambda r:r['row']):
  if (set(row['selected_roles'])=={0,1,2,3} and row['command_guard_agree'] and row['source_formulas_agree']
    and all(type(source) is int and 0<=source<row['row'] and source in known for source in row['ordered_sources'])):known.add(row['row'])
 return sorted(known)
def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def main():
 began=time.perf_counter()
 def timeout(*_):raise TimeoutError('synthetic source controls wall cap')
 signal.signal(signal.SIGALRM,timeout);signal.alarm(5)
 plan=json.loads((OUT/'synthetic-plan-v1.json').read_text())
 for entry in plan['sources']+plan['inputs']:
  if pin(ROOT/entry['path'])!=entry:raise ValueError('immutable source/corpus pin changed')
 corpus=json.loads((OUT/'synthetic-corpus-v1.json').read_text());cases=corpus['matcher_cases'];availability=corpus['availability_cases']
 if len(cases)+len(availability)>64:raise ValueError('synthetic count cap')
 ids=[c['id'] for c in cases+availability]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate synthetic identity')
 outcomes=[]
 for case in cases:
  actual=structural_advice(case['pattern'],case['prefix_binders'],case['available'])
  if actual!=case['expected']:raise AssertionError((case['id'],actual,case['expected']))
  outcomes.append(dict(id=case['id'],actual=actual))
 for case in availability:
  if case['kind']=='arithmetic_adapter':
   actual=arithmetic_known(case)
   if actual!=case['expected_known_rows']:raise AssertionError((case['id'],actual))
  else:
   selected=case['state']['selected_outputs'];actual=[v['row'] for v in selected]
   if actual!=case['expected_rows'] or [v['formula'] for v in selected]!=case['expected_available_formulas']:raise AssertionError(case['id'])
   if 'pattern' in case:
    statuses=[structural_advice(case['pattern'],case['prefix_binders'],v['formula'])['status'] for v in selected]
    merged='match' if 'match' in statuses else 'neutral' if 'neutral' in statuses else 'miss'
    if merged!=case['expected_status']:raise AssertionError(case['id'])
  outcomes.append(dict(id=case['id'],actual=actual))
 signal.alarm(0)
 elapsed=time.perf_counter()-began;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 peak_bytes=peak if sys.platform=='darwin' else peak*1024
 result=dict(status='passed_independent_synthetic_reference_expectations' if elapsed<=5 and peak_bytes<=134217728 else 'unknown_synthetic_resource_budget',
  matcher_cases=len(cases),availability_cases=len(availability),outcomes=outcomes,seconds=elapsed,peak_rss_bytes=peak_bytes,
  producer_matcher_imported=False,producer_compatibility_executed=False,science=dict(actual_models=0,actual_results=0,scientific_imports=0,searches=0,training=0,native_queries=0,replays=0),
  scope='Authored gold corpus checked by independent literal structural reference only. No Hilbert producer matcher gate, arithmetic adapter implementation, proof validity or discovery established.')
 with (OUT/'synthetic-reference-receipt-v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='outcomes'}))
if __name__=='__main__':main()
