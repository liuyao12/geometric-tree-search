"""Target-independent DAG compaction of an already searched certificate.

Expansion never invents a logical inference. Backward slicing removes only
commands not used by the last line. Formula sharing reuses an earlier exact
formula in the same closed ambient theory, remaps strict-prior references and
then slices again. It rejects remaining local assumptions and block commands.
Whole native certification is still required after either transformation.
"""
import copy,gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
from induction_receptors_closure import expand
from audit_semantic_proofs import whole_replay
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/induction-receptors-20261011';TMP=Path('/private/tmp/gcts-induction-compaction-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def keys(row):
    if row['rule'] in ('block','assumption'):raise ValueError('only expanded closed ambient proofs may be compacted')
    return ('antecedent','implication') if row['rule']=='mp' else ('source',) if row['rule']=='generalize' else ()
def slice_proof(proof):
    if not proof:raise ValueError('empty proof')
    keep=set();todo=[len(proof)-1]
    for j,row in enumerate(proof):
        for k in keys(row):
            if type(row[k]) is not int or not 0<=row[k]<j:raise ValueError('strict-prior proof dependency required')
    while todo:
        j=todo.pop()
        if j in keep:continue
        keep.add(j);todo.extend(proof[j][k] for k in keys(proof[j]))
    remap={j:i for i,j in enumerate(sorted(keep))};out=[]
    for j in sorted(keep):
        row=copy.deepcopy(proof[j])
        for k in keys(row):row[k]=remap[row[k]]
        out.append(row)
    return out
def formula_dag(proof):
    out=[];mapped=[];seen={}
    for j,original in enumerate(proof):
        row=copy.deepcopy(original)
        for k in keys(row):
            if type(row[k]) is not int or not 0<=row[k]<j:raise ValueError('strict-prior proof dependency required')
            row[k]=mapped[row[k]]
        word=json.dumps(row['formula'],sort_keys=True,separators=(',',':'))
        if word in seen:i=seen[word]
        else:i=len(out);out.append(row);seen[word]=i
        mapped.append(i)
    # If the terminal formula was already present, that earlier derivation is
    # the terminal one. Discard the later unrelated suffix before slicing.
    return slice_proof(out[:mapped[-1]+1])
def fixture():
    f=['eq',['fun','zero',[]],['fun','zero',[]]]
    p=[dict(rule='refl',formula=f),dict(rule='refl',formula=f),dict(rule='tautology',formula=['imp',f,f]),dict(rule='mp',formula=f,antecedent=1,implication=2)]
    assert len(slice_proof(p))==3 and formula_dag(p)==[p[0]]
    try:formula_dag([dict(rule='assumption',formula=f,index=0)])
    except ValueError:pass
    else:raise ValueError('open assumptions were compacted')
    try:slice_proof([dict(rule='generalize',formula=['all','n',f],variable='n',source=-1)])
    except ValueError:pass
    else:raise ValueError('negative dependency accepted')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'compaction-plan.json').read_text())
    for path,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:raise ValueError('compaction frozen source '+path)
    fixture();records=load(OUT/'attempt-02/native-records.json.gz');original=records[74]['request']
    if records[74]['request_sha256']!=plan['original_request_sha256']:raise ValueError('original searched proof binding')
    prep=time.perf_counter();expanded=expand(original);expanded_request=copy.deepcopy(original);expanded_request.update(blocks=[],proof=expanded)
    if whole_replay(expanded_request)['status']!='accepted':raise ValueError('expanded proof host audit')
    variants=[]
    for mode in plan['variants']:
        proof=slice_proof(expanded) if mode=='backward-slice' else formula_dag(expanded)
        request=copy.deepcopy(original);request.update(blocks=[],proof=proof)
        if request['target']!=original['target'] or request['theory']!=original['theory'] or whole_replay(request)['status']!='accepted':raise ValueError('compact whole proof host audit')
        variants.append(dict(mode=mode,request=request,commands=len(proof)))
    preparation_seconds=time.perf_counter()-prep
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));summary=dict(status='running',original_query=74,expanded_commands=len(expanded),preparation_seconds=preparation_seconds,variants=[])
    try:
        for item in variants:
            q=oracle.request(item['request'],plan['native_steps'],'induction_receptor_compaction_'+item['mode']);fixed,free=boundary_words(q['request']);q.update(boundary_words=dict(fixed=fixed,free=free),limit=plan['native_steps'])
            save(OUT/'compaction-native.json.gz',oracle.records)
            for name in ('input.bin','output.bin'):(OUT/(item['mode']+'-'+name+'.gz')).write_bytes(gzip.compress((TMP/'native'/name).read_bytes(),mtime=0))
            summary['variants'].append(dict(mode=item['mode'],commands=item['commands'],native_query=q['id'],native_status=q['result']['status'],native_seconds=q['seconds'],native_micro_steps=q['result']['micro_steps'],request_sha256=q['request_sha256']))
            (OUT/'compaction-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['variants'][-1]),flush=True)
        summary.update(status='complete',total_seconds=time.perf_counter()-began)
    finally:
        (OUT/'compaction-summary.json').write_text(json.dumps(summary,indent=2)+'\n');oracle.close()
if __name__=='__main__':main()
