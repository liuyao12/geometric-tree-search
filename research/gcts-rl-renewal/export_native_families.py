"""Exact native leaves, variable interfaces and actual policy receptor states."""
import gzip,hashlib,json,struct
from pathlib import Path
from check_native_rectangle import Primitive
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(ref):
    p=DOC/ref['file']
    if sha(p)!=ref['sha256']:raise ValueError('whole raw native family digest')
    return json.loads(gzip.decompress(p.read_bytes()))
def project(data,audit):
    raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());p=Primitive(raw);states=set()
    def ground(pos,key):
        a,b,c=key;n=p.output(key);states.update((v-p.A)//p.A for v in list(key)+[n] if v>=p.A);return dict(x=pos[0],y=pos[1],identity=':'.join(map(str,key)),triple=key,S=b,N=n,W=[a,b],E=[b,c])
    def run(row,ref):
        r=row['result'];fields=('status','attempts','forced','branches','backtracks','width','height','extended','projected','boundary','tiles','tile_generations','initial_census','initial_candidate_nodes','point_checks','cluster_checks','root_rollback_verified','limits','seconds','total_seconds','preparation_seconds','verification_seconds','peak_process_rss_bytes','metrics','mode','weights','stochastic','seed','hints','solution_hints');result={k:r[k] for k in fields};result.update(certificate=row['certificate'],raw=ref,policy_events=[])
        current=[];snapshots={}
        for event in r['events']:
            if event['kind']=='alternative':current=current[:event['depth']]
            if 'policy_event' in event:snapshots[event['policy_event']]=[ground(pos,key) for pos,key in current]
            if 'key' in event:current.append((event['point'],event['key']))
        for event in r['policy_events']:result['policy_events'].append(dict(event,tiles=snapshots[event['id']]))
        for t in r['tiles']:ground([t['x'],t['y']],t['triple'])
        for hint in r['hints']:
            for pos,key in hint['item']['members']:ground(pos,key)
        for event in r['policy_events']:
            for item in event['items']:
                for pos,key in item['members']:ground(pos,key)
        return result
    cases=[]
    for c in data['cases']:
        runs={}
        for lane in data['lanes']:
            ref=next(v for v in c['runs'] if v['lane']==lane and v['repetition']==0);runs[lane]=run(read(ref),ref)
        cases.append(dict(spec=c['spec'],runs=runs,timings=c['timings']))
    donors=[dict(spec=d['spec'],input_library=d['input_library'],result=run(read(d['raw']),d['raw'])) for d in data['donors']];episodes=[]
    for e in data['training']['episodes']:
        row=read(e['raw']);r=row['result'];episodes.append(dict(e,status=r['status'],attempts=r['attempts'],total_seconds=r['total_seconds'],limits=r['limits'],events=[{k:v for k,v in a.items() if k!='items'} for a in r['policy_events']],family_choices=sum(a['selected']>0 for a in r['policy_events'])))
    for family in data['library']:
        for t in family['source']['tiles']:ground([t['x'],t['y']],t['triple'])
    table_rows=[]
    for q in sorted(states):
        offset=p.offsets[q];fallback,direction,_,_,n=struct.unpack_from('<5I',raw,offset);table_rows.append(dict(q=q,fallback=fallback,direction=direction,actions=[list(struct.unpack_from('<5I',raw,offset+20+20*j)[:4]) for j in range(n)]))
    labels=json.loads((DOC/'shared-wang-reader-001.json').read_text())['inventory']['alphabet'];training={k:v for k,v in data['training'].items() if k!='episodes'};training['episodes']=episodes
    return dict(version='native-families-reader-001',input_sha256=sha(DOC/'native-families-001.json'),audit=audit,lanes=data['lanes'],repetitions=data['repetitions'],cases=cases,donors=donors,library=data['library'],mining=data['mining'],training=training,donor_seconds=data['donor_seconds'],compile_seconds=data['compile_seconds'],seconds=data['seconds'],inventory=dict(A=p.A,Q=p.Q,D=p.D,start=p.start,accept=p.accept,reject=p.reject,space=p.space,defined=17899987,tile_types=data['tile_types'],fingerprint=data['inventory_fingerprint'],literal_table_sha256=data['literal_table_sha256'],alphabet=labels,rows=table_rows),scope=data['scope'],timing_scope=data['timing_scope'],projection_scope='Every primary native partial/positive leaf and actual policy receptor state; all hint declarations and completed expansions; all evaluation observations and training score/update summaries. Browser checks exact original/decorated points, family membership/guards, each displayed policy pool and arithmetic summaries. Full counted domains, all repeated trees, sampled RNG and every failed-branch learning event are replayed by the independent backend audit.')
def main():
    path=DOC/'native-families-001.json';data=json.loads(path.read_text());audit=json.loads((DOC/'native-families-audit-001.json').read_text())
    if audit['status']!='passed' or audit['input_sha256']!=sha(path):raise ValueError('passed whole native family audit binding')
    (DOC/'native-families-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
