"""Root Source-only reader review and byte-exact copy; no reader execution."""
import ast
import json
from pathlib import Path
from ROOT_review_raw_caller_v1 import checked, pin, patch_bytes

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
FOLDER=BASE/'unit-row-global-forced-diagnostic-saved-source-20261016'


def read(p):return json.loads(Path(p).read_bytes())
def literal(tree,name):
    return ast.literal_eval(next(n for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)).value)
def segment(raw,node):return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def main():
    cp=pin(FOLDER/'Source-contract-v2.json')
    assert cp['sha256']=='2e83abd182cc48f1fe837d98c6002d7d357dc77d1496a078203e31340fca9430'
    c=read(checked(cp));parent=read(checked(c['parent_source_contract']))
    for k in('caller_source_contract','caller_source','current_sources','inputs',
             'original_model_sources','original_model_inputs','original_model_binding','limits','scope','flags'):
        assert c[k]==parent[k],k
    assert c['caller_source_contract']['sha256']=='06e873d471df980c4c0f5591679090cf254cf94be02e992477a28c07f0652595'
    caller=read(checked(c['caller_source_contract']))
    assert c['current_sources']==caller['sources']and c['inputs']==caller['inputs']
    assert c['original_model_sources']==caller['original_model_sources']and c['original_model_inputs']==caller['original_model_inputs']
    assert c['original_model_binding']==caller['original_model_binding']and c['limits']==caller['limits']
    d=read(checked(c['source_delta']));raw=checked(c['source']).read_bytes();old=checked(d['parent']).read_bytes()
    assert c['source']==d['source']and c['source']['sha256']=='7f77ab7b2ac03ea3053d256f1a89773c70c314ae0402d28e288700a57155f1d6'
    forward,inverse=old,raw
    assert len(d['edits'])==4
    for e in reversed(d['edits']):
        a,b=e['old'].encode(),e['new'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        forward=forward[:e['old_start']]+b+forward[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert forward==raw and inverse==old
    assert patch_bytes(old,checked(d['actual_unified_patches']['forward']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['actual_unified_patches']['full_inverse']).read_bytes())==old
    ot,nt=ast.parse(old),ast.parse(raw)
    assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ot,include_attributes=False)
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)}
    nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
    assert len(of)==13 and set(of)==set(nf)
    for name in set(of)-{'main'}:
        assert segment(old,of[name])==segment(raw,nf[name])
        assert ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    assert literal(nt,'EXPECTED_CONTRACT')==c['caller_source_contract']
    assert literal(nt,'VERSION')=='unit-row-global-forced-saved-diagnostic-reader-v2'
    assert literal(nt,'LIMITS')==c['limits']
    assert b'native_deadline_confirmed'not in raw and b"'failure_cause_established':False"in raw
    allowed={'hashlib','json','math','os','stat','sys','re','pathlib'}
    assert all(all(a.name.split('.')[0]in allowed for a in n.names)if isinstance(n,ast.Import)
               else n.module in allowed for n in nt.body if isinstance(n,(ast.Import,ast.ImportFrom)))
    compile(nt,c['source']['path'],'exec')
    peer_path=BASE/'unit-row-global-forced-diagnostic-saved-independent-source-20261016/typed-Source-review-v2.json'
    peer=read(peer_path)
    assert peer['source']==c['source']and peer['source_contract']==cp and peer['sources']==c['sources']and peer['scope']==c['scope']
    assert peer['reviewer_identity']=='/root/hilbert_ordering_diagnosis'and peer['author_identity']=='/root/arithmetic_induction'
    assert peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    review=dict(c['Review_ABI']);review.update(source_contract=cp,reviewer_identity='/root',source_review_passed=True,
        source_only=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],
        whole_current_Source_and_contract_read=True,peer_review=pin(peer_path),
        full_raw_AST_and_actual_patch_inverse_verified=True,top12_helpers_raw_AST_exact=True,
        authorship_disclosure='Root read whole reader V1, all V2 changed regions and both complete contracts through literal map concordance, independently verified four-region and actual patch inverses, and reviewed every native/source/once/session/failure/wire/flag join. Root authored only metadata audits, grants and actuals. Arithmetic authored reader; diagnosis is distinct reviewer.',
        checks=[
            'Standalone stdlib raw JSON/ASCII metadata only; no model or proof/search/checker import/evaluation, no lossless scientific payload decoding or replay.',
            'Same full plan/grant/current14/input8/original17/input2/binding, consumed once, terminal same session, native2/wait4/pid/status/probe, Date/failure55/memory512 joins remain strict.',
            'Whole two-file diagnostic requires full LF/hash/bytes/context/clock/four scalar slots. Absent/one-file writer stays unavailable; malformed complete-named pair fails closed.',
            'Strict complete marker grammar/order/uint/native clock preserved. Optional final bounded raw ASCII fragment is uninterpreted, with no reconstructed sample/error/phase fact.',
            'Literal shared tick line and inclusive caller lifetime are separate observations; no cause or throw-time assertion. Latest entry is never an active failure frame or returned move.',
            'All case counts unavailable except zero newly qualified; proof/trajectory/restoration/exhaustion/resource-success/GCTS/RL flags remain false. Successful raw result requires separate complete reconciliation.',
            'Author repeated metadata profile read was interrupted; no claim of fresh repetition from that stage. This review preserves inherited raw capsules and literal maps. Actual cold caller already performed its own fresh pinned input checks; reader runtime retains every fresh raw check.'
        ])
    with(HERE/'ROOT-saved-reader-Source-review-v2.json').open('x')as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
    target=HERE/Path(c['source']['path']).name
    with target.open('xb')as f:f.write(raw)
    assert target.read_bytes()==raw
    print(json.dumps(dict(review=pin(HERE/'ROOT-saved-reader-Source-review-v2.json'),copied_reader=pin(target))))


if __name__=='__main__':main()
