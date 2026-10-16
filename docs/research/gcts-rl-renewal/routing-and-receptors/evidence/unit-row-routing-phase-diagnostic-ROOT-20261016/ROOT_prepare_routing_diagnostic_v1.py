"""Root metadata/AST-only review and one prospective diagnostic grant."""
import ast,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(r):
    p=Path(r['path']);assert p.is_absolute()and p==p.resolve()and pin(p)==r;return p
def save(name,v):
    p=HERE/name
    with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
    return pin(p)
def literal(t,name):
    n=next(n for n in t.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets));return ast.literal_eval(n.value)
def segment(b,n):return b''.join(b.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True);hunks=patch.splitlines(keepends=True);out=[];pos=0;ix=2
    assert hunks[0].startswith(b'--- ')and hunks[1].startswith(b'+++ ')
    while ix<len(hunks):
        m=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',hunks[ix]);assert m
        start=int(m[1]);count=int(m[2]or b'1');newcount=int(m[4]or b'1');ix+=1
        begin=start-1 if count else start;assert begin>=pos;out.extend(lines[pos:begin]);pos=begin;used=made=0
        while ix<len(hunks)and not hunks[ix].startswith(b'@@ '):
            line=hunks[ix];ix+=1;assert line[:1]in(b' ',b'-',b'+')
            if line[:1]in(b' ',b'-'):assert lines[pos]==line[1:];pos+=1;used+=1
            if line[:1]in(b' ',b'+'):out.append(line[1:]);made+=1
        assert used==count and made==newcount
    out.extend(lines[pos:]);return b''.join(out)
def inverse(d,current):
    old=checked(d['parent']).read_bytes();assert pin(Path(d['source']['path']))==d['source']
    forward,back=old,current
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode();assert old[e['old_start']:e['old_end']]==a and current[e['new_start']:e['new_end']]==b
        forward=forward[:e['old_start']]+b+forward[e['old_end']:];back=back[:e['new_start']]+a+back[e['new_end']:]
    assert forward==current and back==old
    assert patch_bytes(old,checked(d['patches'][0]).read_bytes())==current and patch_bytes(current,checked(d['patches'][1]).read_bytes())==old
    return old
def main():
    folder=BASE/'unit-row-routing-phase-diagnostic-cold-source-20261016'
    cr=pin(folder/'Source-contract-v1.json');assert cr['sha256']=='b75016984df98895c6429491d9bb1cc3039be2042b3816d72c5f749d3473fc06'
    c=read(checked(cr));s,i=c['sources'],c['inputs'];assert len(s)==14 and len(i)==8
    for refs in(s,i,c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():checked(ref)
    raw=checked(c['source']).read_bytes();assert c['source']==s['intake'];t=ast.parse(raw)
    for ref in s.values():compile(ast.parse(checked(ref).read_bytes()),ref['path'],'exec')
    for name,want in [('FIXED',{k:v for k,v in s.items()if k!='intake'}),('FIXED_INPUTS',i),('ORIGINAL_SOURCES',c['original_model_sources']),('ORIGINAL_INPUTS',c['original_model_inputs']),('ORIGINAL_BINDING',c['original_model_binding']),('LIMITS',c['limits']),('QUALIFICATION_CASES_BY_PURPOSE',c['API']['purpose_modes_and_ordered_cases']),('VERSION',c['version']),('SCOPE',c['scope'])]:assert literal(t,name)==want
    d=read(checked(c['source_delta']));assert d['edit_count']==len(d['edits'])==17
    old=inverse(d,raw);ot=ast.parse(old)
    of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
    assert len(of)==18 and set(of)==set(nf)
    for name in set(of)-{'main'}:assert segment(old,of[name])==segment(raw,nf[name])and ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    on={n.name:n for n in of['main'].body if isinstance(n,ast.FunctionDef)};nn={n.name:n for n in nf['main'].body if isinstance(n,ast.FunctionDef)}
    assert len(on)==34 and set(nn)==set(on)|{'routing_phase'}
    for name in set(on)-{'protocol_family'}:assert segment(old,on[name])==segment(raw,nn[name])and ast.dump(on[name],include_attributes=False)==ast.dump(nn[name],include_attributes=False)
    protocol=nn['protocol_family']
    prior_calls=[n for n in protocol.body if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='routing_phase')]
    assert len(protocol.body)-len(prior_calls)==8
    protocol.body=prior_calls;assert ast.dump(protocol,include_attributes=False)==ast.dump(on['protocol_family'],include_attributes=False)
    oc={n.name:n for n in ot.body if isinstance(n,ast.ClassDef)};nc={n.name:n for n in t.body if isinstance(n,ast.ClassDef)};assert len(oc)==2 and set(oc)==set(nc)
    for name in oc:assert segment(old,oc[name])==segment(raw,nc[name])and ast.dump(oc[name],include_attributes=False)==ast.dump(nc[name],include_attributes=False)
    suffix=b'    boundary();offset=0\n';assert old[old.index(suffix):]==raw[raw.index(suffix):]
    parent=read(checked(c['parent_source_contract']))
    for k in('inputs','original_model_sources','original_model_inputs','original_model_binding','limits'):assert c[k]==parent[k]
    assert all(s[k]==v for k,v in parent['sources'].items()if k!='intake')
    assert c['API']['purpose_modes_and_ordered_cases']==parent['API']['purpose_modes_and_ordered_cases']and c['essential_case_count']==12 and c['endpoint_count']==6
    labels=c['diagnostic']['ordered_labels'];assert len(labels)==len(set(labels))==16
    calls=[n for n in ast.walk(ast.parse(raw))if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='routing_phase']
    calls.sort(key=lambda n:n.lineno);assert [ast.literal_eval(n.args[0])for n in calls]==labels
    assert [n.lineno for n in calls]==[p['source_line']for p in c['diagnostic']['positions']]
    line_sizes=[len(('UNQUALIFIED_ROUTING_PHASE_OBSERVATION '+label+' '+str(2**63-1)+'\n').encode())for label in labels]
    assert max(line_sizes)==93 and sum(line_sizes)==1321
    choice=pin(HERE/'ROOT-diagnostic-choice-v1.json');assert c['implementation_choice']==choice
    comp=read(checked(c['component_source_contract']))
    assert all(s[k]==v for k,v in comp['sources'].items())
    for role,ref in c['component_reviews'].items():
        r=read(checked(ref));assert r['sources']==comp['sources']and r['source_contract']==c['component_source_contract']and r['source_review_passed']is r['source_only']is True and r['scientific_calls']==0 and r['scientific_acceptance']is False
    peerpath=BASE/'unit-row-routing-phase-diagnostic-cold-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['source']==s['intake']and peer['sources']==s and peer['source_contract']==cr and peer['scope']==c['scope']and peer['reviewer_identity']=='/root/hilbert_ordering_diagnosis'and peer['source_review_passed']is peer['source_only']is True and peer['scientific_calls']==0 and peer['scientific_acceptance']is False
    checks=save('ROOT-caller-raw-inverse-review-v1.json',dict(schema='ROOT-routing-phase-raw-inverse-review-v1',source=s['intake'],source_contract=cr,parent=d['parent'],exact17region_actualpatch_inverse=True,top_helpers17_nested33_classes2_raw_AST_exact=True,protocol_eight_marker_erasure_AST_exact=True,native_final_and_failure_suffix_exact=True,current14_input8_original17_input2_verified=True,marker_lines16_max93_total1321=True,AST_compile_without_eval_only=True,scientific_calls=0))
    rr=dict(c['Review_ABI']);rr.update(source_contract=cr,reviewer_identity='/root',source_review_passed=True,concrete_blockers=[],raw_inverse_review=checks,whole_operative_Source_and_contract_review=True,authorship_disclosure='Root reviewed complete changed writer, all16 sites and their enclosing groups, operative contract, and all17 exact edit inverses. Unchanged scientific bodies/helpers/classes/native tail join prior whole-reviewed007b by raw/AST/actual patch equality. Controls is caller author; distinct diagnosis peer plus Root review bind this current Source. Root owns metadata/grant/actuals.',checks=['Original scientific compounds, original/current model distinction, all12 essentials and6 native limits preserved.','Writer uses captured native tick/builtin write, fixed ASCII whitelist and bounded positive partialwrites; no model call/cache/history/reset added.','All16 marker sites are fixed; intervals inclusive only. Missing writes do not establish cause or completion.','Only one routing diagnostic granted; case countnull/qualified0 and all scientific/engine/native-positive/RL/advantage acceptancefalse evenexit0.'])
    rootreview=save('ROOT-caller-Source-review-v1.json',rr)
    runtime=pin('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9');assert runtime['sha256']=='bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'
    owned=HERE/'RP-owned-v1';external=HERE/'RP-external-v1';assert not owned.exists()and not external.exists()
    common=dict(invocation_id='routing-phase-diagnostic-20261016-v1',purpose='unit-row-marked-aware-router-protocol-controls',output_directory=str(owned),sources=s,inputs=i,source_contract=cr,reviews=dict(ROOT=rootreview,peer=pin(peerpath)),runtime=runtime,limits=c['limits'],resource_rule='single-owned-process-native-terminal-v1')
    grant=save('ROOT-RP-authorization-v1.json',dict(common,schema='ROOT-routed-engine-qualification-authorization-v1',author_identity='/root',actual_execution_authorized=True,maximum_actual_invocations=1,protocol_choice=choice,diagnostic_only=True,reported_case_count=None,qualified_case_count=0,qualification_accepted=False,engine_promoted=False,scientific_acceptance=False,target_budget_changed=False))
    plan=save('ROOT-RP-plan-v1.json',dict(common,schema='ROOT-routed-engine-qualification-plan-v1',ROOT_authorization=grant))
    print(json.dumps(dict(plan=plan,external_directory=str(external),scientific_calls=0)))
if __name__=='__main__':main()
