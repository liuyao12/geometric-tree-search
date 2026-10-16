"""Source-only raw/AST joins after Root's manual whole-delta review."""
import ast, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def check(r):
 p=Path(r['path']);assert pin(p)==r;return p
def save(n,x):
 p=HERE/n
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
hpath=BASE/'unit-row-paired-fixture-controls-source-20261016/handoff-v8.json'
assert pin(hpath)['sha256']=='2c6bf9733f327a5963fce8e2cfdb0b14e36fd8ff366629765c9461b911471c74'
h=read(hpath);c=read(check(h['source_contract']));d=read(check(h['source_delta']))
for r in [h['source'],h['source_contract'],h['parent_source'],h['parent_contract'],h['base_source'],h['base_contract'],*h['sources'].values(),*d['patches'].values()]:check(r)
for dd,key in [(d,'parent'),(d['base_forward_and_inverse'],'base')]:
 raw=check(dd[key]).read_text();current=check(dd['current']).read_text();out=raw
 for e in dd['edits']:
  i=e['forward_offset_at_this_step'];a=e['before_utf8'];b=e['after_utf8'];assert out[i:i+len(a)]==a;out=out[:i]+b+out[i+len(a):]
 assert out==current
 for e in reversed(dd['edits']):
  i=e['forward_offset_at_this_step'];a=e['before_utf8'];b=e['after_utf8'];assert out[i:i+len(b)]==b;out=out[:i]+a+out[i+len(b):]
 assert out==raw
compile(ast.parse(check(h['source']).read_bytes()),h['source']['path'],'exec')
assert len(h['all_case_names'])==len(set(h['all_case_names']))==43
r=dict(c['Review_ABI'],schema='ROOT-paired-fixture-controls-Source-review-v1',source_contract=h['source_contract'],sources=h['sources'],reviewer_identity='/root',source_review_passed=True,source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],authorship_disclosure='Controls authored by the controls agent. Root owns caller, measurement and saved disposition; this is a distinct whole-delta review, not an independent reimplementation.',checks=[
 'Read complete combined delta6-to8 and repair7-to8; independently recovered both parents by exact raw inverse and AST/compile only.',
 'Original A adoption/owned inner/remote rejection/forced retirement remain separate; sibling B uses same original universal AX at rows1,2 and same futureUG9, original target/grammar and real global decision.',
 'B uses full actual adviser batch, fresh independent receipt, first actual selection, anchor-only real search and owned inner token. No desired family filter, future preinstallation, degree shortcut or eligibility inference.',
 'Separate callback holders, one shared total24 observation cap. Actual PENDING callback request/state/decision/receipt retained; all existing direct native checks charged.',
 'Immutable7 negative gap preserved;8 positive aliases exist only after actual selected pending. Unsuccessful continuation retained under its own artifact, adoption eligibility distinguished from observed pending selection.',
 'All43 case meanings and eight-keyword API retained; occupied component must join actual accepted B callback and same engine family/seed/outer restoration. Original remote and forced tests stay A.',
 'No runtime/fit/proof/RL/full graph conformance claim; fresh17/17/43 and full native/wire gates still required before targets.'
 ])
print(json.dumps({'controls_review':save('ROOT-controls-Source-review-v1.json',r)}))
hp=HERE/'ROOT-close-advice-controls-handoff-v14.json';hh=read(hp)
assert pin(hp)['sha256']=='3a6986d449278690c041fc6a1cf5df5609f88b6396a030f4662e6adfe6518fbf'
dd=read(check(hh['delta']));a=check(dd['parent']).read_text();b=check(dd['source']).read_text();out=[];pos=0
for e in dd['edits']:
 assert a[e['old_start']:e['old_end']]==e['old'];out.extend([a[pos:e['old_start']],e['new']]);pos=e['old_end']
out.append(a[pos:]);assert ''.join(out)==b
out=[];pos=0
for e in dd['edits']:
 assert b[e['new_start']:e['new_end']]==e['new'];out.extend([b[pos:e['new_start']],e['old']]);pos=e['new_end']
out.append(b[pos:]);assert ''.join(out)==a
ta,tb=ast.parse(a),ast.parse(b);compile(tb,hh['source']['path'],'exec')
for n in ta.body:
 if isinstance(n,ast.FunctionDef):
  m=next(v for v in tb.body if isinstance(v,ast.FunctionDef) and v.name==n.name)
  assert ast.dump(n,include_attributes=False)==ast.dump(m,include_attributes=False) and ast.get_source_segment(a,n)==ast.get_source_segment(b,m)
save('ROOT-saved-closer-Source-review-v1.json',{'schema':'ROOT-saved-closer-distinct-review-v1','source':hh['source'],'source_contract':hh['source_contract'],'author_identity':hh['author_identity'],'reviewer_identity':'/root','source_review_passed':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'checks':['Complete delta and whole closer read; full forward/inverse independently recovered; all5 helper raw/AST bodies unchanged.','Old native/wire/first30 and original A remote/forced assertions retained. B source batch/receipt/seed/adoption/family/real PENDING callback/event/placement/inner+outer restoration explicitly joined.','Current controls8 positive flag and whole continuation alias equality required. Saved-data concordance only, no project import or mathematical replay. Strict positive closer may reject partial results; never licenses missing cases.']})
p=HERE/'ROOT_prepare_v14.py';s=p.read_text();s=s.replace('controls7','controls8');p.write_text(s);compile(ast.parse(s),str(p),'exec')
