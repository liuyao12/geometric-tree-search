"""Independent mechanical-source binding and complete native admission replay."""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from audit_semantic_inventory import need,pin,code_bytes,PINNED_MICRO,PINNED_PROGRAM
import audit_semantic_inventory as N

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-receptors-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
TMP=Path('/private/tmp/gcts-hilbert-receptors-promotion-audit-20261011')

def main():
    began=time.perf_counter();plan=json.loads((OUT/'promotion-admission-plan.json').read_text())
    for path,sha in plan['sources'].items():need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,'exact predeclared source '+path)
    for path,d in plan['data_dependencies'].items():need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==d['sha256'] and (ROOT/path).stat().st_size==d['bytes'],'exact predeclared input '+path)
    source=json.loads((OUT/'ground-accepted-request.json').read_text());old=source['request'];result=json.loads((OUT/'promotion-admission-result.json').read_text());records=json.loads(gzip.decompress((OUT/'promotion-admission-native.json.gz').read_bytes()))
    need(len(records)==1 and source['native_query']==56 and source['result']['status']=='accepted' and json.loads((OUT/'audit.json').read_text())['status']=='passed','actually searched audited source')
    hypotheses=source['hypothesis_axioms'];retained=source['retained_axioms'];need(retained==['I.2-uniqueness'] and hypotheses==['common-distinct-points','extra-incidence'],'exact discharge/retain partition')
    premises=[old['theory']['axioms'][n] for n in hypotheses];proof=[]
    for step in old['proof']:
        if step['rule']=='axiom' and step['name'] in hypotheses:
            i=hypotheses.index(step['name']);need(step['formula']==premises[i],'same local input formula')
            proof.append({'rule':'assumption','index':i,'formula':copy.deepcopy(step['formula'])})
        else:proof.append(copy.deepcopy(step))
    body={'premises':premises,'conclusion':old['target'],'proof':proof};definition={'name':'hilbert-promoted-'+pin(body),**body}
    need(result['interface']['definition']==definition and result['interface']['dependencies']==[d['name'] for d in old['blocks']] and result['interface']['level']==2,'entire searched composite, with all actual dependencies')
    theory=copy.deepcopy(old['theory']);theory['axioms']={'I.2-uniqueness':old['theory']['axioms']['I.2-uniqueness']};taut=['imp',['bot'],['bot']]
    request={'protocol':old['protocol'],'theory':theory,'blocks':old['blocks']+[definition],'proof':[{'rule':'tautology','formula':taut}],'target':taut}
    need(records[0]['request']==request and records[0]['purpose']=='hilbert_searched_level_two_admission' and result['status']==records[0]['result']['status'],'exact new-theory whole admission')
    micro=json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()));boundary=json.loads((DOC/'proof-boundary-001.json').read_text());need(pin(micro)==PINNED_MICRO and boundary['program_sha256']==PINNED_PROGRAM,'unchanged computational palette')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'audit_tape_micro.cpp'),'-o',str(TMP/'native')],check=True);(TMP/'code.bin').write_bytes(code_bytes(micro));N.TMP=TMP
    steps,accepted=N.replay_native(records,{0:request},micro,boundary['cases'][0]['initial'],plan['native_steps'])
    audit={'status':'passed','native_outcome':records[0]['result']['status'],'native_queries':1,'native_micro_steps':steps,'distinct_acceptances':len(accepted),'request_sha256':pin(request),'seconds':time.perf_counter()-began,'source_native_query':56,'source_request_sha256':source['request_sha256'],'scope':'All native bands replayed; identity binding only. Higher interface is the actually searched four-row proof under two local inputs, with the complete prior dependency declarations and I.2 alone.'}
    (OUT/'promotion-admission-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit),flush=True)

if __name__=='__main__':main()
