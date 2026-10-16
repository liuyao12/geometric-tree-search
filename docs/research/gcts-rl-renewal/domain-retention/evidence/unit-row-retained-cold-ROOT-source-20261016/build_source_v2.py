"""Source-only lossless evidence-transport repair; no scientific execution."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,x):
    p=HERE/name
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
    return pin(p)
old=HERE/'unit_row_retained_domain_cold_v1.py';raw=old.read_bytes()
assert pin(old)['sha256']=='264211f1415b5908f765a14630722e5456cf520327d73ebf5b7f1323df47c352'
text=raw.decode()
def replace(a,b):
    global text
    assert text.count(a)==1,a[:100];text=text.replace(a,b,1)
replace("VERSION='unit-row-retained-domain-cold-v1'","VERSION='unit-row-retained-domain-cold-v2-lossless-wire'")
replace('import copy\n','import base64\nimport binascii\nimport zlib\nimport copy\n')
replace("contract['schema'] == 'unit-row-retained-domain-cold-Source-contract-v1'","contract['schema'] == 'unit-row-retained-domain-cold-Source-contract-v2'")
replace('copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types)','copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types,base64,binascii,zlib)')
encoder='''def encode_result_transport(expanded_raw):
    """Lossless transport only; caller invoke charges original20 pre/post gates."""
    need(type(expanded_raw) is bytes and len(expanded_raw) <= 16*1048576,
         'whole expanded lossless result output cap')
    compressed = zlib.compress(expanded_raw, 6)
    envelope = {'schema':'ROOT-unit-row-lossless-result-envelope-v1',
        'encoding':'zlib+base64', 'expanded_bytes':len(expanded_raw),
        'expanded_sha256':hashlib.sha256(expanded_raw).hexdigest(),
        'compressed_bytes':len(compressed),
        'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
        'payload_base64':base64.b64encode(compressed).decode('ascii')}
    encoded = canonical(envelope) + b'\\n'
    need(len(encoded) <= 4*1048576, 'whole encoded lossless result output cap')
    return encoded

'''
replace('def main(argv):\n',encoder+'def main(argv):\n')
insertion='''    result_raw = invoke_fn(encode_result_transport,(result_raw,),{},
        boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
'''
replace("    need(len(result_raw) <= 4*1048576, 'whole bounded global engine output')",insertion+"    need(len(result_raw) <= 4*1048576, 'whole bounded global engine output')")
selected=HERE/'unit_row_retained_domain_cold_v2.py'
with selected.open('xb') as f:f.write(text.encode())
t=ast.parse(text);compile(t,str(selected),'exec')
c=read(HERE/'Source-contract-v1.json');source=pin(selected);sources=dict(c['sources'],intake=source)
olddefs={n.name:n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)}
newdefs={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
for name in [*c['unchanged15_helpers'],'save_failure_diagnostic']:
    assert ast.get_source_segment(raw.decode(),olddefs[name])==ast.get_source_segment(text,newdefs[name])
    assert ast.dump(olddefs[name],include_attributes=False)==ast.dump(newdefs[name],include_attributes=False)
tail=b"    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1',"
assert text.encode()[text.encode().index(tail):].replace(insertion.encode(),b'',1)==raw[raw.index(tail):]
c.update(schema='unit-row-retained-domain-cold-Source-contract-v2',sources=sources,parent_source=pin(old),parent_contract=pin(HERE/'Source-contract-v1.json'),
 unchanged_positive_output_exit_tail=False,
 positive_tail_delta='Only one guarded encode_result_transport call inserted before existing4MiB output check. Removing that call recovers the entire old canonical result/output/response/stdout/native exit tail byte-for-byte.',
 transport={'schema':'ROOT-unit-row-lossless-result-envelope-v1','encoding':'zlib+base64','fields':['schema','encoding','expanded_bytes','expanded_sha256','compressed_bytes','compressed_sha256','payload_base64'],
  'encoded_file_cap_bytes':4194304,'expanded_full_canonical_JSON_LF_cap_bytes':16777216,'zlib_level':6,
  'scope':'Lossless transport of the ENTIRE canonical result+LF. No snapshot/control/receipt/candidate/trace trimming, sampling or omission. This changes output representation, not mathematical/search semantics.',
  'guard':'Native20 before and after encoding via original invoke. base64,binascii,zlib imported before seal and included in existing full module/function guard. Original failure-only writer unchanged; no new custody framework.',
  'decoder':'Root saved-only strict outer JSON/LF and base64 canonical re-encoding, both compressed and expanded hashes/bytes; bounded single zlib stream with eof and no trailing/unconsumed data; full canonical expanded JSON+LF. No scientific replay in metadata reconciliation.',
  'prior_failure':'Original264211 domain-controls raw4MiB-cap failure remains UNKNOWN/unqualified with no counters. Current Source binding needs fresh control actuals; do not inherit old original17 runtime qualification.',
  'limits':'Original20/512MiB/failure55/owned60/caller90+1 and encoded4MiB file cap retained. Expanded16MiB is a new bounded representation parameter, not the old raw4MiB bound. No output or resource fit prediction.'})
c['Review_ABI']=dict(c['Review_ABI'],source=source,sources=sources)
cr=save('Source-contract-v2.json',c)
save('static-evidence-v2.json',{'schema':'ROOT-retained-lossless-caller-static-v2','source':source,'source_contract':cr,
 'all15_helpers_and_failure_writer_raw_AST_exact':True,'positive_tail_exact_after_removing_only_encoder_call':True,
 'new_function':'encode_result_transport','Source11':True,'input2_and_six_limits_unchanged':True,'compile_only':True,'scientific_execution':False})
handoff=save('handoff-v2.json',{'schema':'ROOT-retained-lossless-cold-Source-handoff-v2','source':source,'source_contract':cr,
 'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_only':True,'scientific_calls':0,'scientific_acceptance':False,
 'actual_execution_authorized':False,'independent_review_pending':True,'parent_handoff':pin(HERE/'handoff-v1.json')})
print(json.dumps({'source':source,'source_contract':cr,'handoff':handoff}))
