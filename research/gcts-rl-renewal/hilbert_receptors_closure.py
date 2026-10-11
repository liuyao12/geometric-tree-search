"""A separately declared whole-native diagnostic for mechanical proof closure.

This consumes the generic transform agent's exact request. It never contributes
a target script, guard, candidate, pruning rule or training reward to the frozen
ground proof-search experiment. Native replay uses a separate interpreter and
independent input encoder, including unknown step/space outcomes.
"""
import gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words
from audit_certificate_boundary import initial_for,sha
from audit_proof_boundary import code_bytes,input_bytes,PINNED_MICRO,PINNED_PROGRAM
from audit_semantic_inventory import need
from micro_cert import run
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/hilbert-receptors-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-hilbert-receptors-closure-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def pins(plan):
    for f,h in plan['sources'].items():need(sha(ROOT/f)==h,'frozen closure producer/native source '+f)
    for f,d in plan['data_dependencies'].items():need(sha(ROOT/f)==d['sha256'] and (ROOT/f).stat().st_size==d['bytes'],'exact closure input '+f)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'closure-plan.json').read_text());pins(plan);TMP.mkdir(parents=True,exist_ok=True)
    candidate=json.loads((OUT/'closure-input.json').read_text());source=json.loads((OUT/'ground-accepted-request.json').read_text())
    need(candidate['source_artifact_sha256']==sha(OUT/'ground-accepted-request.json') and candidate['source_native_query']==56,'mechanical closure source binding')
    request=candidate['request'];need(request['blocks']==[] and len(request['proof'])==41 and list(request['theory']['axioms'])==['I.2-uniqueness'] and request['theory']['axioms']['I.2-uniqueness']==source['request']['theory']['axioms']['I.2-uniqueness'],'primitive closure request under I.2 alone')
    if sys.argv[1]=='produce':
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
        oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')))
        try:
            q=oracle.request(request,plan['native_steps'],'hilbert_mechanical_closure_diagnostic');fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'closure-native.json.gz',q)
            result=dict(status=q['result']['status'],native_seconds=q['seconds'],total_seconds=time.perf_counter()-began,native_limit=plan['native_steps'],micro_steps=q['result']['micro_steps'],source_native_query=56,commands=41,eigen_binding=candidate['eigen_binding'],scope='Mechanical universal closure of an actually discovered ground sequent, not a new target search or an authored theorem proof. Full independent native replay pending.')
            (OUT/'closure-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
        finally:oracle.close()
    elif sys.argv[1]=='audit':
        rec=load(OUT/'closure-native.json.gz');need(rec['id']==0 and rec['request']==request and rec['request_sha256']==digest(request) and rec['query_target']=='fixed_assertion','exact diagnostic native request')
        micro=load(DOC/'proof-boundary-microcode-001.json.gz');boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(digest(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged native palette')
        boot=initial_for(micro,boundary['cases'][0]['initial'],request);need(rec['boundary_words']==dict(fixed=boot['words'][micro['boundary']['problem']][:-1],free=boot['words'][micro['boundary']['certificate']][:-1]),'independent tagged complete input')
        (TMP/'input.bin').write_bytes(input_bytes(boot));need(sha(TMP/'input.bin')==rec['input_sha256'],'all native input bands')
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'audit-native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));q=run(TMP/'audit-native',(TMP/'code.bin',TMP/'input.bin',TMP/'output.bin',plan['native_steps']))
        for k in ('status','micro_steps','physical_steps','micro_fnv64'):need(str(q[k])==str(rec['result'][k]),'independent native '+k)
        need(sha(TMP/'output.bin')==rec['output_sha256'] and rec['result']['start']==88986,'all output bands and actual parser start')
        result=dict(status='passed',native_outcome=q['status'],micro_steps=q['micro_steps'],seconds=time.perf_counter()-began,request_sha256=digest(request),input_sha256=rec['input_sha256'],output_sha256=rec['output_sha256'],source_program_sha256=PINNED_PROGRAM,source_artifact_sha256=sha(OUT/'ground-accepted-request.json'),scope='Independent whole native replay; an unknown outcome remains unknown. The generic transformation itself belongs to the arithmetic agent’s separately tested infrastructure.')
        (OUT/'closure-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    else:raise ValueError('mode must be produce or audit')
if __name__=='__main__':main()
