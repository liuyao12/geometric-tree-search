"""Generic translation of the separately extracted word into point tiles.

This does not search or steer GCTS. It selects the exact scalar tiles encoding
each independently extracted command/source. A 12-row version inserts the
first zero-input grammar command just before the final conclusion if needed.
"""
import copy,gzip,hashlib,json,time
from pathlib import Path
from left_successor_points import Model
from certificate_boundary_search import canonical

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'forward-control'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def encode(catalog,admission,theory,target,proof,identity):
    spec=copy.deepcopy(json.loads((PARENT/'plan.json').read_text())['case']);spec.update(id=identity,length=len(proof));model=Model(spec,catalog,admission);record=model.record();placements=[]
    for j,row in enumerate(proof):
        command={k:v for k,v in row.items() if k not in ('source','inputs')};matches=[(k,d['rule']) for k,d in enumerate(record['domains'][j]) if d['command']==command]
        if len(matches)!=1:raise ValueError('one exact interface per command')
        k,i=matches[0];r=catalog['rules'][i];sources=row.get('inputs',[row['source']] if row['rule']=='generalize' else []);mode=i+1 if r['premises'] else 0;placements.extend([(j,0,k,0),(j,1,k,0)])
        for role in range(2):placements.append((j,2+role,mode,sources[role]+1 if role<len(r['premises']) else 0))
    return dict(case=spec,model=record,search=dict(proof=proof,placements=placements),scope='Direct generic encoding of the ordinary forward-control word, not a GCTS search trace.')
def main():
    began=time.perf_counter();plan=json.loads((OUT/'point-plan.json').read_text())
    for p,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('frozen point translator '+p)
    if json.loads((OUT/'audit.json').read_text())['status']!='passed_complete_forward_control_and_native_replay':raise ValueError('independent forward gate')
    evidence=[]
    for lane in plan['lanes']:
        raw=load(OUT/(lane+'.json.gz'));c=load(PARENT/(lane+'-reachable-core.json.gz'));a=json.loads((PARENT/(lane+'-admission.json')).read_text());proof=raw['proof'];entry=dict(lane=lane,actual_word=encode(c,a,raw['theory'],raw['target'],proof,'forward-control-'+lane+'-word'))
        padded=copy.deepcopy(proof)
        if len(padded)<=plan['comparison_rows']:
            seed=copy.deepcopy(next(r['command'] for r in c['rules'] if not r['premises']))
            if seed['rule']=='block':seed['inputs']=[]
            while len(padded)<plan['comparison_rows']:padded.insert(len(padded)-1,copy.deepcopy(seed))
            entry['same_boundary_embedding']=encode(c,a,raw['theory'],raw['target'],padded,'forward-control-'+lane+'-12-row-embedding')
        evidence.append(entry)
    (OUT/'point-encoding.json.gz').write_bytes(gzip.compress(json.dumps(evidence,separators=(',',':')).encode(),mtime=0));(OUT/'point-summary.json').write_text(json.dumps(dict(status='encoded_not_yet_independently_audited',seconds=time.perf_counter()-began,native_queries=0,GCTS_searches=0,scope='Generic word-to-tiles translation and deterministic zero-input padding only, not search or native whole acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
