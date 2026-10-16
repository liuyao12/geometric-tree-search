"""Root raw inverse and whole-read attestation for saved-only helpers; no science."""
import ast
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
FOLDER=HERE.parent/'unit-row-channel4-stageC-saved-source-20261016'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(r):
    p=Path(r['path']);assert p==p.resolve() and pin(p)==r;return p
def segment(raw,n):return b''.join(raw.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def patch_bytes(old,patch):
    lines=old.splitlines(keepends=True);hunks=patch.splitlines(keepends=True)
    assert hunks[0].startswith(b'--- ') and hunks[1].startswith(b'+++ ')
    output=[];pos=0;index=2
    while index<len(hunks):
        m=re.fullmatch(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n',hunks[index]);assert m
        start=int(m[1]);count=int(m[2]or b'1');newcount=int(m[4]or b'1');index+=1
        begin=start-1 if count else start
        assert begin>=pos;output.extend(lines[pos:begin]);pos=begin;consumed=produced=0
        while index<len(hunks) and not hunks[index].startswith(b'@@ '):
            line=hunks[index];index+=1;assert line[:1]in(b' ',b'-',b'+')
            if line[:1]in(b' ',b'-'):assert lines[pos]==line[1:];pos+=1;consumed+=1
            if line[:1]in(b' ',b'+'):output.append(line[1:]);produced+=1
        assert consumed==count and produced==newcount
    output.extend(lines[pos:]);return b''.join(output)

contract_ref=pin(FOLDER/'Source-contract-v1.json')
assert contract_ref['sha256']=='70e82eb5cebe8438e7fe12759afaf339ba2ad9e8dc8cf664da53b6b9d093d304'
contract=read(checked(contract_ref));delta=read(checked(contract['source_delta']))
findings={}
for role,wanted_count in(('decoder',3),('closer',24)):
    d=delta['components'][role];raw=checked(d['source']).read_bytes();old=checked(d['parent']).read_bytes()
    assert d['source']==contract['sources'][role] and d['edit_count']==len(d['edits'])==wanted_count
    assert d['parent']==contract['parent_helpers'][role]
    rebuilt=old;inverse=raw
    for e in reversed(d['edits']):
        a,b=e['old_utf8'].encode(),e['new_utf8'].encode()
        assert old[e['old_start']:e['old_end']]==a and raw[e['new_start']:e['new_end']]==b
        rebuilt=rebuilt[:e['old_start']]+b+rebuilt[e['old_end']:]
        inverse=inverse[:e['new_start']]+a+inverse[e['new_end']:]
    assert rebuilt==raw and inverse==old
    assert patch_bytes(old,checked(d['forward_patch']).read_bytes())==raw
    assert patch_bytes(raw,checked(d['inverse_patch']).read_bytes())==old
    tree=ast.parse(raw);parent=ast.parse(old);compile(tree,d['source']['path'],'exec')
    of={n.name:n for n in parent.body if isinstance(n,ast.FunctionDef)}
    nf={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    for name in d['whole_raw_AST_preserved_functions']:
        assert segment(old,of[name])==segment(raw,nf[name])
        assert ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)
    if role=='closer':
        start=b"bracket=read(HERE/('ROOT-";end=b'transport=read('
        before=old[old.index(b"bracket=read(HERE/'ROOT-stageB-tool-bracket-v1.json')"):old.index(end)]
        begin=raw.index(start);after=raw[begin:raw.index(end,begin)]
        transformed=before.replace(b"HERE/'ROOT-stageB-tool-bracket-v1.json'",b"HERE/('ROOT-'+mode+'-tool-bracket-v1.json')")
        assert transformed==after
    findings[role]=dict(source=d['source'],parent=d['parent'],whole_Source_read=True,full_raw_forward_inverse=True,
        actual_unified_forward_inverse=True,edit_count=wanted_count,unchanged_functions=d['whole_raw_AST_preserved_functions'],AST_compile_only=True)
review=dict(contract['Review_ABI']);review.update(source_contract=contract_ref,reviewer_identity='/root',source_only=True,
    source_review_passed=True,scientific_calls=0,scientific_acceptance=False,concrete_blockers=[],helpers_executed=False,
    whole_two_helpers_and_contract_read=True,raw_inverse_findings=findings,
    authorship_disclosure='Root authored prior saved framework and reviewed entire current decoder/closer. Current adaptations authored by arithmetic. This is conditional saved-only Source review; independent peer review is also required before Root use.',
    checks=[
      'Strict decoder retains canonical duplicate/nonfinite-safe bounded JSON, base64 re-encoding, one full zlib stream/no tails, compressed/expanded hashes and full records; same4MiB/16MiB caps.',
      'Success path preserves complete original native/wait4/Date/probe gates, whole output2/response2LF/current11/input8 and original17 binding. New literal checks join real current origin receipts, ZERO transfer wrapper/chain, full states and exact rollback.',
      'Natural UNKNOWN path retains real ordered original2/marked1 streams/EOF, normal fresh certifier None and unchanged actual unresolved frontier; no raw EOF completion authority or candidate/proof-rule replay.',
      'Scheduler data remains NONLOGICAL and exact all9 statuses accounted. Failure main explicitly takes separate administrative closure, exact nativeTimeout/exit2/reaped/noowned; all C5-C7 countsNone and zero qualified, no inferred partial progress or positive resource/trajectory.',
      'Aggregate requires four unique closed plans/invocations/output dirs and shared current Sources/marking/originalepoch; reports six qualified only if three positive closures pass and leaves all9/StageC false. No combined20 claim, replay, new clock/process or scientific acceptance.'
    ])
p=HERE/'ROOT-stageC-saved-helper-Source-review-v1.json'
with p.open('x')as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(pin(p)))
