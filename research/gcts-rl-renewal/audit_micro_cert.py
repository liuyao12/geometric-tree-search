"""Producer-independent bindings, literal lowering and response verification."""
import gzip,hashlib,json,resource,struct,subprocess,time
from pathlib import Path
from audit_proof_boundary import PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,input_bytes,code_bytes,expected_constructor,micro_output
from audit_tape_kernel import check_table
from audit_tree_kernel import packed,need

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-micro-response-audit')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha(x):return hashlib.sha256(packed(x)).hexdigest()

def check_bindings(data):
    need(data['program_sha256']==PINNED_PROGRAM and data['micro_sha256']==PINNED_MICRO and data['literal_binary_sha256']==PINNED_TABLE,'external machine pins')
    for file,pin in data['sources'].items():need(digest(HERE/file)==pin,'source '+file)
    for file,pin in data['reused_artifacts'].items():need(digest(DOCS/file)==pin,'fixed artifact '+file)

def root_boundary(micro,initial,root,result):
    """Independently apply the derived interface and its physical affine law."""
    need(root['q']==micro['start'] and root['out'] in (micro['accept'],micro['reject']),'root endpoint')
    tapes=[list('^'+w+'B'*(n-len(w)-1)) for w,n in zip(initial['words'],initial['capacities'])];heads=list(initial['heads']);base=[];offset=1
    for n in initial['capacities']:base.append(offset+1);offset+=n+2
    physical=int(root['physical_constant']);seen=set()
    for b in root['bands']:
        t=b['tape'];need(t not in seen and 0<=t<len(tapes),'one response per band');seen.add(t);h=heads[t]
        need(0<=h+b['extent'][0]<=h+b['extent'][1]<len(tapes[t]),'derived frame')
        physical+=b['physical_coefficient']*(base[t]+h)
        for lo,hi,mask in b['pre']:
            need(lo<hi and mask>0 and mask<128,'symbol-mask interval')
            for p in range(lo,hi):need(mask&(1<<'B^01:,;'.index(tapes[t][h+p])),'root precondition')
    for b in root['bands']:
        t=b['tape'];h=heads[t]
        for lo,hi,s in b['writes']:
            need(lo<hi and 0<=s<7,'write interval')
            for p in range(lo,hi):tapes[t][h+p]='B^01:,;'[s]
        heads[t]+=b['shift']
    need(physical==result['physical_steps'] and root['steps']==result['micro_steps'],'affine/step count')
    return dict(state=root['out'],heads=heads,words=[''.join(t[1:]).rstrip('B') for t in tapes]),base[root['last']]+heads[root['last']]

def main():
    start=time.perf_counter();TMP.mkdir(exist_ok=True);data=json.loads((DOCS/'micro-responses-001.json').read_text());check_bindings(data)
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()));need(sha(micro)==PINNED_MICRO,'microcode contents')
    literal=gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes());need(hashlib.sha256(literal).hexdigest()==PINNED_TABLE,'literal table contents');law=check_table(micro,literal);del literal
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'micro_response_check.cpp'),'-o',str(TMP/'checker')],check=True)
    (TMP/'code.bin').write_bytes(code_bytes(micro));prior=json.loads((DOCS/'proof-boundary-001.json').read_text());summaries=[];mutations=[]
    for row in data['cases']:
        old=next(r for r in prior['cases'] if r['name']==row['name']);need(packed(row['initial'])==packed(old['initial']) and packed(row['request'])==packed(old['request']),'exact saved input provenance')
        need(sha({k:row['request'][k] for k in ('protocol','theory','target')})==row['problem_pin'],'fixed theorem binding')
        expected_constructor(micro,row['initial'],row['request'])
        a=row['artifact'];need(digest(DOCS/a['name'])==a['sha256'] and (DOCS/a['name']).stat().st_size==a['bytes'],'grammar artifact')
        raw=gzip.decompress((DOCS/a['name']).read_bytes());need(len(raw)==a['uncompressed_bytes'],'grammar length');(TMP/'grammar.bin').write_bytes(raw)
        (TMP/'input.bin').write_bytes(input_bytes(row['initial']));need(digest(TMP/'input.bin')==row['input_sha256'],'native input binding')
        before=time.perf_counter();r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'output.bin'),str(10**12),str(1500000000),str(TMP/'root.json')]))
        need(r['status']=='checked_response','complete response');r['wall_seconds']=time.perf_counter()-before
        for k in ('result','nodes','micro_steps','physical_steps','expanded_leaves','derived_intervals','peak_live_intervals','max_depth'):need(r[k]==row['checker'][k],'fresh derived '+k)
        need(digest(TMP/'output.bin')==row['output_sha256']==old['output_sha256'],'whole derived output')
        root=json.loads((TMP/'root.json').read_text());need(root==row['root'],'all exported derived observations')
        end,head=root_boundary(micro,row['initial'],root,r);need(end==micro_output(TMP/'output.bin'),'independent root application')
        claimedhead=struct.unpack_from('<Q',raw,36)[0];need(head==claimedhead,'physical final head')
        # Header mutations reject before any full derivation is required.
        if row['name']=='reflexivity':
            for field,offset,value in (('root',8,0xffffffff),('start',12,0),('first-leaf-state',48,0xffffffff)):
                bad=bytearray(raw);struct.pack_into('<I',bad,offset,value);(TMP/'bad.bin').write_bytes(bad)
                failed=subprocess.run([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'bad.bin'),str(TMP/'bad-output.bin'),str(10**12),str(1500000000),str(TMP/'bad-root.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                need(failed.returncode!=0,'forged '+field+' accepted');mutations.append(field)
        summaries.append(dict(name=row['name'],checker=r,whole_output_sha256=digest(TMP/'output.bin'),root_bands=len(root['bands'])));print(row['name'],'all interfaces independently derived',flush=True)
    # A proof cannot make its own altered program/theorem pins authoritative.
    import copy
    for key in ('program_sha256','micro_sha256','literal_binary_sha256'):
        changed=copy.deepcopy(data);changed[key]='0'*64
        try:check_bindings(changed)
        except ValueError:mutations.append(key)
        else:raise ValueError('changed external pin accepted')
    data['independent_audit']=dict(cases=summaries,literal_law=law,mutations_rejected=mutations,
        source_sha256=digest(__file__),checker_source_sha256=digest(HERE/'micro_response_check.cpp'),
        seconds=time.perf_counter()-start,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='every grammar interface derived afresh without replaying its expanded computation; independent root application and full literal row law; native toolchain and algorithms remain trusted')
    (DOCS/'micro-responses-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(data['independent_audit'],indent=2),flush=True)
if __name__=='__main__':main()
