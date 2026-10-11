"""Independent expansion, compaction and whole native input/output replay.

Does not import the block expansion or compaction producer. The two native
variants must be reconstructed from the originally searched whole certificate.
Host logical replay is reported separately from native acceptance/unknown.
"""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from audit_certificate_boundary import initial_for,pin,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_proofs import whole_replay
from micro_cert import run

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/induction-receptors-20261011';TMP=Path('/private/tmp/gcts-induction-compaction-independent-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def need(t,m):
    if not t:raise ValueError(m)
def refs(row):
    r=row['rule'];need(r not in ('assumption','block'),'primitive closed root required')
    return ['antecedent','implication'] if r=='mp' else ['source'] if r=='generalize' else []
def expanded(request):
    definitions={d['name']:d for d in request['blocks']};commands=[];active=[]
    def emit(lines,premises):
        images=[]
        for j,source in enumerate(lines):
            row=copy.deepcopy(source);r=row['rule']
            if r=='assumption':
                k=row['index'];need(type(k) is int and 0<=k<len(premises),'local assumption');i=premises[k];need(commands[i]['formula']==row['formula'],'premise identity')
            elif r=='block':
                name=row['name'];need(name not in active and name in definitions,'nonrecursive known block');d=definitions[name];inputs=row['inputs'];need(all(type(k) is int and 0<=k<j for k in inputs),'strict earlier block input');args=[images[k] for k in inputs]
                need([commands[k]['formula'] for k in args]==d['premises'] and row['formula']==d['conclusion'],'block interface');active.append(name);i=emit(d['proof'],args);active.pop()
            else:
                for field in refs(row):
                    need(type(row[field]) is int and 0<=row[field]<j,'strict earlier primitive input');row[field]=images[row[field]]
                i=len(commands);commands.append(row)
            images.append(i)
        need(bool(images),'nonempty block');return images[-1]
    last=emit(request['proof'],[]);need(last==len(commands)-1 and commands[last]['formula']==request['target'],'expanded final target');return commands
def sliced(proof):
    required={len(proof)-1}
    for j in range(len(proof)-1,-1,-1):
        for field in refs(proof[j]):need(type(proof[j][field]) is int and 0<=proof[j][field]<j,'strict earlier DAG reference')
        if j in required:required.update(proof[j][field] for field in refs(proof[j]))
    positions=sorted(required);images={j:i for i,j in enumerate(positions)};result=[]
    for j in positions:
        row=copy.deepcopy(proof[j])
        for field in refs(row):row[field]=images[row[field]]
        result.append(row)
    return result
def shared(proof):
    result=[];images=[];formulas=[]
    for j,command in enumerate(proof):
        row=copy.deepcopy(command)
        for field in refs(row):need(type(row[field]) is int and 0<=row[field]<j,'strict earlier formula share');row[field]=images[row[field]]
        if row['formula'] in formulas:i=formulas.index(row['formula'])
        else:i=len(result);result.append(row);formulas.append(row['formula'])
        images.append(i)
    return sliced(result[:images[-1]+1])
def main():
    began=time.perf_counter();plan=json.loads((OUT/'compaction-plan.json').read_text());summary=json.loads((OUT/'compaction-summary.json').read_text());records=load(OUT/'compaction-native.json.gz');original=load(OUT/'attempt-02/native-records.json.gz')[74]
    for path,h in plan['source_sha256'].items():need(sha(ROOT/path)==h,'frozen compaction source '+path)
    need(summary['status']=='complete' and len(records)==len(plan['variants']) and original['request_sha256']==plan['original_request_sha256'],'complete predeclared variants and original request')
    full=expanded(original['request']);result=dict(status='checking',expanded_commands=len(full),variants=[])
    DOC=ROOT/'docs/research/gcts-rl-renewal';micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native checker')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));steps=0
    for mode,rec in zip(plan['variants'],records):
        proof=sliced(full) if mode=='backward-slice' else shared(full);expected=copy.deepcopy(original['request']);expected.update(blocks=[],proof=proof)
        need(rec['request']==expected and rec['request_sha256']==pin(expected),'complete independent transformed request equality');need(whole_replay(expected)['status']=='accepted','separate whole logical audit')
        initial=initial_for(micro,boundary['cases'][0]['initial'],expected);(TMP/'input.bin').write_bytes(input_bytes(initial));need(sha(TMP/'input.bin')==rec['input_sha256'],'full parser input');response=run(TMP/'native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',rec['limit']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(response[k])==str(rec['result'][k]),'native whole replay '+k)
        need(rec['result']['start']==88986 and sha(TMP/'output.bin')==rec['output_sha256'],'full output and true parser start');steps+=response['micro_steps']
        result['variants'].append(dict(mode=mode,commands=len(proof),native_status=response['status'],native_micro_steps=response['micro_steps'],native_replay_seconds=response['seconds'],logical_audit_only='accepted',whole_input_output_sha256_matched=True));result.update(native_micro_steps=steps,seconds=time.perf_counter()-began)
        (OUT/'compaction-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('compaction replay',mode,response['status'],flush=True)
    result.update(status='passed',scope='Original searched proof mechanically expanded, both generic transformations independently reconstructed, exact unchanged theory/target, strict prior dependencies, and both whole native computations independently replayed from true parser state88986 with full input/output hashes and execution fingerprint. No new proof search or native heap increase.')
    (OUT/'compaction-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPACTION AUDIT PASSED',result['seconds'],flush=True)
if __name__=='__main__':main()
