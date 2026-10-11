"""Explicit pending/complete HTML reader export; measured sources are untouched."""
import gzip,hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-promotion-family-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def main():
    # Each public artifact uses precisely the bytes parsed into this snapshot.
    # The producer replaces files atomically; mutable checkpoints are bracketed.
    while True:
        before=(OUT/'progress.json').read_bytes();cache={}
        def snap(path):
            if path not in cache:cache[path]=path.read_bytes()
            return cache[path]
        progress=json.loads(before);cache[OUT/'progress.json']=before
        native=json.loads(gzip.decompress(snap(OUT/'native.json.gz'))) if (OUT/'native.json.gz').exists() else []
        native_audit=json.loads(snap(OUT/'native-audit-progress.json')) if (OUT/'native-audit-progress.json').exists() else None
        if before==(OUT/'progress.json').read_bytes() and len(native)>=progress['native_queries'] and (native_audit is None or native_audit['native_queries']<=len(native)):break
        time.sleep(.05)
    def packed(path):return json.loads(gzip.decompress(snap(path)))
    def plain(path):return json.loads(snap(path))
    plan=plain(OUT/'plan.json');catalog=packed(OUT/'catalog.json.gz')
    audit=plain(OUT/'audit.json') if (OUT/'audit.json').exists() else None
    data=dict(version='hilbert-promotion-family-001',plan=plan,progress=progress,catalog=catalog,audit=audit,native_audit=native_audit,cases=[],
              native=[{k:v for k,v in r.items() if k not in ['request','boundary_words']} for r in native])
    ground=ROOT/'.gcts-active/hilbert-receptors-20261011/ground-accepted-request.json'
    data['source']=dict(native=packed(ROOT/plan['source_native_record'])[0],audit=plain(ROOT/plan['source_native_audit']),ground=plain(ground))
    inventory=packed(OUT/'inventories.json.gz') if (OUT/'inventories.json.gz').exists() else None
    data['inventories']=inventory
    data['compiled']=packed(OUT/'compiled.json.gz') if (OUT/'compiled.json.gz').exists() else None
    for spec in plan['cases']:
        item=dict(spec=spec,observations=[])
        for summary in [o for o in progress['observations'] if o['case_id']==spec['id']]:
            obs=packed(OUT/(summary['tag']+'-final.json.gz'));r=obs['search'];model=obs['model'];placed={tuple(p['key']):p for p in model['placements']};rows=[]
            if r['proof'] is not None:
                for j,c in enumerate(r['proof']):
                    tiles=[]
                    for key in sorted([k for k in r['placements'] if k[0]==j],key=lambda k:k[1]):
                        p=placed[tuple(key)];words=[]
                        for point,value in p['marks']:
                            if point[0]%4==2 and point[1] in [0,1]:
                                kind='formula' if point[1]==0 else 'command';words.append(dict(point=point,value=value,kind=kind,word=model['catalog'][kind][value]['value']))
                        tile=dict(key=p['key'],role=['C','G','I1','I2'][key[1]],occupancy=p['occupancy'],marks=p['marks'],kind=p['kind'],words=words)
                        if 'source' in p:tile['source']=p['source']
                        tiles.append(tile)
                    rows.append(dict(index=j+1,command=c,tiles=tiles))
            q=obs['native_query'];item['observations'].append(dict(summary=summary,rows=rows,metrics=r['metrics'],root_restored=r['root_restored'],pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'],
                native=None if q is None else dict(request=native[q]['request'],request_sha256=native[q]['request_sha256'],result=native[q]['result'],seconds=native[q]['seconds'])))
        data['cases'].append(item)
    names=['plan.json','progress.json','catalog.json.gz','native.json.gz','native-audit-progress.json','audit.json','inventories.json.gz','compiled.json.gz']
    names += [o['tag']+suffix for o in progress['observations'] for suffix in ['.json.gz','-final.json.gz']]
    artifacts=[]
    for name in names:
        src=OUT/name
        if not src.exists():continue
        dest='hilbert_promotion_family_'+name.replace('-','_');p=DOC/dest;p.write_bytes(snap(src))
        artifacts.append(dict(path=dest,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    for label,src in [('source_native.json.gz',ROOT/plan['source_native_record']),('source_audit.json',ROOT/plan['source_native_audit']),('source_ground.json',ground)]:
        dest='hilbert_promotion_family_'+label;p=DOC/dest;p.write_bytes(snap(src))
        artifacts.append(dict(path=dest,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    data['artifacts']=artifacts;path=DOC/'hilbert_promotion_family_reader_001.json';path.write_text(json.dumps(data,separators=(',',':'))+'\n')
    result=dict(status=progress['status'],verified=audit is not None and audit['status']=='passed' and progress['status']=='complete',reader_bytes=path.stat().st_size,artifacts=artifacts)
    (OUT/'export.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='artifacts'}))
if __name__=='__main__':main()
