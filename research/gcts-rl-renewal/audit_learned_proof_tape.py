"""Independent theorem/input bindings, learned-proof constructor and responses."""
import copy,gzip,hashlib,json,resource,struct,subprocess,time
from pathlib import Path
from audit_proof_boundary import PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE,input_bytes,code_bytes,expected_constructor,micro_output,heap_records
from audit_micro_cert import root_boundary
from audit_tape_kernel import check_table
from audit_tree_kernel import packed,sha,need

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-learned-proof-tape-audit')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bindings(data):
    need((data['program_sha256'],data['micro_sha256'],data['literal_binary_sha256'])==(PINNED_PROGRAM,PINNED_MICRO,PINNED_TABLE),'external machine pins')
    for file,pin in data['sources'].items():need(digest(HERE/file)==pin,'source '+file)
    for file,pin in data['reused_artifacts'].items():need(digest(DOCS/file)==pin,'fixed artifact '+file)
    proposals=json.loads((DOCS/'learned-proof-blocks-001.json').read_text())
    if '/' in data['proposal_id']:row=next(r for r in proposals['evaluation']['runs'] if r['problem']+'/'+r['lane']==data['proposal_id'])
    else:row=next(r for r in proposals['discovery'] if r['problem']['id']==data['proposal_id'])
    need(packed(row['result']['request'])==packed(data['request']),'exact actual searched witness')
    need(sha({k:data['request'][k] for k in ('protocol','theory','target')})==data['problem_pin'],'fixed theorem')
    template=next(r for r in json.loads((DOCS/'proof-boundary-001.json').read_text())['cases'] if r['name']=='reflexivity')['initial']
    need(data['initial']['heads']==template['heads'],'bootstrap heads')
    for t in range(len(template['words'])):
        if t in (29,30):need(data['initial']['capacities'][t]==len(data['initial']['words'][t])+2,'wire frame capacity')
        else:
            need(data['initial']['words'][t]==template['words'][t],'fixed bootstrap words')
            expected=len(template['words'][t])+1+131072 if t==26 else template['capacities'][t]
            need(data['initial']['capacities'][t]==expected,'declared fixed capacity')
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOCS/'learned-proof-tape-001.json';data=json.loads(path.read_text());bindings(data)
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()));need(sha(micro)==PINNED_MICRO,'micro contents')
    literal=gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes());need(hashlib.sha256(literal).hexdigest()==PINNED_TABLE,'literal contents');law=check_table(micro,literal);del literal
    before=time.perf_counter()
    for name,source in (('checker','micro_response_check.cpp'),('snapshot','audit_boundary_micro.cpp'),('selected','audit_tape_micro.cpp')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/name)],check=True)
    compile_seconds=time.perf_counter()-before;(TMP/'code.bin').write_bytes(code_bytes(micro));(TMP/'input.bin').write_bytes(input_bytes(data['initial']))
    need(digest(TMP/'input.bin')==data['input_sha256'],'exact native input')
    expected,request_root=expected_constructor(micro,data['initial'],data['request']);before=time.perf_counter()
    snapshot=json.loads(subprocess.check_output([str(TMP/'snapshot'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'snapshot-output.bin'),str(10**12),str(micro['boundary']['old_start'])]));snapshot['wall_seconds']=time.perf_counter()-before
    out=micro_output(TMP/'snapshot-output.bin');need(snapshot['status']=='stopped_state' and out['state']==micro['boundary']['old_start'],'constructor endpoint')
    need(heap_records(out['words'][micro['heap']])==expected,'actual constructed heap')
    need(int(out['words'][micro['allocation'][0]['slots'][0]][::-1],2)==request_root,'actual request root')
    a=data['artifact'];need(digest(DOCS/a['name'])==a['sha256'] and (DOCS/a['name']).stat().st_size==a['bytes'],'artifact binding')
    raw=gzip.decompress((DOCS/a['name']).read_bytes());need(len(raw)==a['uncompressed_bytes'],'artifact expansion');(TMP/'grammar.bin').write_bytes(raw)
    before=time.perf_counter();r=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'derived.bin'),str(10**12),str(2000000000),str(TMP/'root.json')]))
    r['wall_seconds']=time.perf_counter()-before;need(r['status']=='checked_response' and r['result']=='accepted','derived acceptance')
    for k in ('result','nodes','micro_steps','physical_steps','expanded_leaves','derived_intervals','peak_live_intervals','max_depth'):need(r[k]==data['checker'][k],'fresh derived '+k)
    need(digest(TMP/'derived.bin')==data['output_sha256'],'complete output binding');root=json.loads((TMP/'root.json').read_text());need(root==data['root'],'all derived observations')
    end,head=root_boundary(micro,data['initial'],root,r);need(end==micro_output(TMP/'derived.bin'),'independent root application');need(head==struct.unpack_from('<Q',raw,36)[0],'final physical head')
    mutations=[]
    for key in ('program_sha256','micro_sha256','literal_binary_sha256','problem_pin'):
        wrong=copy.deepcopy(data);wrong[key]='0'*64
        try:bindings(wrong)
        except ValueError:mutations.append(key)
        else:raise ValueError('altered binding accepted')
    for name,offset in (('root',8),('start',12),('leaf-state',48)):
        bad=bytearray(raw);struct.pack_into('<I',bad,offset,0xffffffff);(TMP/'bad.bin').write_bytes(bad)
        failed=subprocess.run([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'bad.bin'),str(TMP/'bad-out.bin'),str(10**12),str(2000000000),str(TMP/'bad-root.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        need(failed.returncode!=0,'forged '+name);mutations.append(name)
    before=time.perf_counter();limited=json.loads(subprocess.check_output([str(TMP/'checker'),str(TMP/'code.bin'),str(TMP/'input.bin'),str(TMP/'grammar.bin'),str(TMP/'limited.bin'),str(10**12),'0',str(TMP/'limited-root.json')]))
    limited['wall_seconds']=time.perf_counter()-before;need(limited['status']=='unknown_certificate_budget','interface cutoff stays unknown')
    cutoff_path=DOCS/'learned-proof-tape-cutoff-001.json';cutoff=json.loads(cutoff_path.read_text())
    bound=dict(data,**{k:cutoff[k] for k in ('proposal_id','request','problem_pin','initial')})
    bound['sources']={cutoff['source']:cutoff['source_sha256'],'audit_tape_micro.cpp':cutoff['runner_source_sha256']};bindings(bound)
    expected_constructor(micro,cutoff['initial'],cutoff['request']);(TMP/'cutoff-input.bin').write_bytes(input_bytes(cutoff['initial']))
    need(digest(TMP/'cutoff-input.bin')==cutoff['input_sha256'],'cutoff exact input');before=time.perf_counter()
    replay=json.loads(subprocess.check_output([str(TMP/'selected'),str(TMP/'code.bin'),str(TMP/'cutoff-input.bin'),str(TMP/'cutoff-output.bin'),str(10**12)]));replay['wall_seconds']=time.perf_counter()-before
    for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(replay[k]==cutoff['selected'][k],'cutoff complete selected replay '+k)
    need(digest(TMP/'cutoff-output.bin')==cutoff['selected_output_sha256'],'cutoff whole output')
    need(cutoff['builder']['status']=='unknown_certificate_budget' and cutoff['builder']['nodes']==9000000,'recorded cutoff is unknown')
    cutoff['independent_audit']=dict(selected=replay,source_sha256=digest(__file__),scope='exact source/input/theorem bindings and complete independent selected execution; builder cutoff is recorded resource evidence, without an accepting response or partial-grammar verification')
    cutoff_path.write_text(json.dumps(cutoff,separators=(',',':'))+'\n')
    data['independent_audit']=dict(checker=r,constructor=snapshot,constructed_nodes=len(expected),literal_law=law,mutations_rejected=mutations,resource_control=limited,
        cutoff_replay=replay,compile_seconds=compile_seconds,seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=digest(__file__),
        scope='fresh derivation of all interfaces, independently reconstructed exact input and actual constructor heap, complete root application/output, all finite literal table rows; unchanged Wang expansion law reused; native toolchain and logical/compiler soundness formalization remain trusted/open')
    path.write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(data['independent_audit'],indent=2),flush=True)
if __name__=='__main__':main()
