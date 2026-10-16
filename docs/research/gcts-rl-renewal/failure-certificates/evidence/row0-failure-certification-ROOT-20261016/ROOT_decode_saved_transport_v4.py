"""Bounded saved JSON/zlib/base64 concordance only; no project/scientific imports."""
import base64,hashlib,json,math,os,stat,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
ENCODED_CAP=4194304
EXPANDED_CAP=16777216
def need(v,message):
    if not v:raise ValueError(message)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def pairs(items):
    x={}
    for k,v in items:need(k not in x,'duplicate JSON key');x[k]=v
    return x
def constant(x):raise ValueError('nonfinite JSON token')
def finite(x):
    y=float(x);need(math.isfinite(y),'finite JSON float');return y
def decode(b):return json.loads(b,object_pairs_hook=pairs,parse_float=finite,parse_constant=constant)
def buffer_pin(p,b):
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read_bounded(p,cap):
    need(p.is_absolute() and p==p.resolve(),'canonical saved metadata path')
    fd=os.open(str(p),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        need(stat.S_ISREG(info.st_mode) and 0<=info.st_size<=cap,'bounded regular saved file')
        chunks=[];total=0
        while True:
            block=os.read(fd,min(65536,cap+1-total))
            if not block:break
            chunks.append(block);total+=len(block)
            need(total<=cap,'whole saved file cap/EOF')
        return b''.join(chunks)
    finally:os.close(fd)
def checked_raw(r):
    p=Path(r['path']);raw=read_bounded(p,1048576)
    need(buffer_pin(p,raw)==r,'same authenticated saved metadata buffer')
    return raw
need(len(sys.argv)==2 and sys.argv[1] == 'certification','one saved endpoint mode')
mode=sys.argv[1];plan_path=HERE/('ROOT-'+mode+'-plan-v1.json');plan_raw=read_bounded(plan_path,1048576);plan=decode(plan_raw)
contract=decode(checked_raw(plan['source_contract']))
need(contract['API']['transport']=='Unchanged16MiB expanded/4MiB compressed zlib+base64 fullhash envelope. Filename engine-result.json is inherited transport only; no engine/search invoked.','frozen inherited transport bounds')
p=HERE/(mode+'-owned-v1')/'engine-result.json';raw=read_bounded(p,ENCODED_CAP)
need(0<len(raw)<=ENCODED_CAP and raw.endswith(b'\n'),'whole bounded encoded file/LF')
env=decode(raw)
need(type(env) is dict and set(env)=={'schema','encoding','expanded_bytes','expanded_sha256','compressed_bytes','compressed_sha256','payload_base64'},'exact envelope7')
need(env['schema']=='ROOT-unit-row-lossless-result-envelope-v1' and env['encoding']=='zlib+base64','current envelope schema/encoding')
need(canonical(env)+b'\n'==raw,'entire canonical outer JSON plus LF')
for k,cap in (('expanded_bytes',EXPANDED_CAP),('compressed_bytes',ENCODED_CAP)):
    need(type(env[k]) is int and 0<env[k]<=cap,'literal bounded byte length')
for k in ('expanded_sha256','compressed_sha256'):
    need(type(env[k]) is str and len(env[k])==64 and all(c in '0123456789abcdef' for c in env[k]),'literal SHA256')
need(type(env['payload_base64']) is str and env['payload_base64'].isascii(),'literal ASCII base64')
compressed=base64.b64decode(env['payload_base64'],validate=True)
need(base64.b64encode(compressed).decode('ascii')==env['payload_base64'],'canonical base64 re-encoding')
need(len(compressed)==env['compressed_bytes'] and hashlib.sha256(compressed).hexdigest()==env['compressed_sha256'],'entire compressed bytes/hash')
stream=zlib.decompressobj(wbits=zlib.MAX_WBITS)
expanded=stream.decompress(compressed,EXPANDED_CAP+1)
need(len(expanded)<=EXPANDED_CAP and stream.eof is True and not stream.unused_data and not stream.unconsumed_tail,'one complete bounded zlib stream; no tails/concatenation')
need(len(expanded)==env['expanded_bytes'] and hashlib.sha256(expanded).hexdigest()==env['expanded_sha256'],'entire expanded bytes/hash including LF')
need(expanded.endswith(b'\n') and expanded.count(b'\n')==1,'one complete canonical expanded JSON/LF')
result=decode(expanded)
need(canonical(result)+b'\n'==expanded and result['schema']=='ROOT-unit-row-global-engine-result-v1','whole original expanded result JSON')
need(result['sources']==plan['sources'] and result['inputs']==plan['inputs'] and result['purpose']==plan['purpose'],'same current executable Source7/input8/purpose')
out=HERE/('ROOT-'+mode+'-expanded-result-v1.json')
with out.open('xb') as f:f.write(expanded)
meta={'schema':'ROOT-lossless-saved-transport-concordance-v1','plan':buffer_pin(plan_path,plan_raw),'encoded_file':buffer_pin(p,raw),'expanded_file':buffer_pin(out,expanded),
 'compressed_bytes':len(compressed),'compressed_sha256':env['compressed_sha256'],'encoding':'zlib+base64',
 'encoded_cap_bytes':ENCODED_CAP,'expanded_cap_bytes':EXPANDED_CAP,'strict_canonical_JSON_LF':True,
 'strict_base64_reencoded':True,'single_complete_zlib_stream':True,'trailing_or_unconsumed_bytes':False,
 'all_full_record_bytes_retained':True,'scientific_replay':False,'logical_proof_accepted':False,'trajectory_accepted':False,'resource_success_accepted':False}
q=HERE/('ROOT-'+mode+'-transport-concordance-v1.json')
meta_raw=(json.dumps(meta,indent=2,sort_keys=True)+'\n').encode()
with q.open('xb') as f:f.write(meta_raw)
print(json.dumps({'concordance':buffer_pin(q,meta_raw),'encoded_bytes':len(raw),'expanded_bytes':len(expanded),'scientific_replay':False}))
