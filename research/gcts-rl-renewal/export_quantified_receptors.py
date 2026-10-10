"""Reader projection bound to complete search and operational audits."""
import gzip,hashlib,json
from pathlib import Path
import quantified_receptors as Q
from check_quantified_receptors import freeze
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build():
    data=json.loads((DOC/'quantified-receptors-001.json').read_bytes());audit=json.loads((DOC/'quantified-receptors-audit-001.json').read_bytes());native=json.loads(gzip.decompress((DOC/'quantified-wang-001.json.gz').read_bytes()));na=json.loads(gzip.decompress((DOC/'quantified-wang-audit-001.json.gz').read_bytes()))
    if audit['input_sha256']!=digest(DOC/'quantified-receptors-001.json') or audit['source_sha256']!=digest(HERE/'audit_quantified_receptors.py'):raise ValueError('search audit binding')
    if na['input_sha256']!=digest(DOC/'quantified-wang-001.json.gz') or na['source_sha256']!=digest(HERE/'audit_quantified_wang.py'):raise ValueError('operational audit binding')
    cases=[]
    for c in data['cases']:
        row=dict(spec=c['spec'],build_seconds=c['build_seconds'],rules=len(c['catalog']['rules']),formulas=len(c['catalog']['formulas']),runs={})
        for lane,r in c['runs'].items():row['runs'][lane]={k:r[k] for k in ('status','seconds','metrics','logical','proof','tiles','placements','point_certificate','fits_slot_bound') if k in r}
        r=c['runs']['gcts'];row['used_rules']={str(k[1]):c['catalog']['rules'][k[1]] for k in r['placements']}
        forbidden=set().union(*(Q.L.free(a) for a in c['spec']['hypotheses']));row['scope']={x:int(x in forbidden) for x in c['spec']['variables']}
        row['deduced_request']=r.get('deduced',{}).get('request');row['compiled_request']=r.get('compiled',{}).get('request')
        row['frames']=[dict(kind=f['kind'],point=f['point'],key=f['key'],domains=[dict(point=d['point'],count=d['count'],factor_records=len(d['blocks'])) for d in f['domains']]) for f in r.get('frames',[])]
        if c['spec']['id']=='scope-reject':
            m=Q.Model(freeze(c['catalog']),freeze(c['spec']['target']),c['spec']['length'],freeze(c['spec']['hypotheses']));rid=next(i for i,r in enumerate(m.catalog['rules']) if r['kind']=='generalize' and r['output']==m.target);tile=m.placement((0,rid,(-1,)));row['blocked_tile']=dict(key=tile.key,occupancy=tile.occupancy,marks=tile.marks)
        cases.append(row)
    natives=[]
    for r,a in zip(native['cases'],na['cases']):
        if r['name']!=a['name']:raise ValueError('native ordering')
        natives.append(dict(name=r['name'],request=r['request'],builder=r['builder'],checker=r['checker'],literal=r['literal'],seconds=r['seconds'],lines=[dict(label=l['label'],input=l['input_context'],output=l['output_context'],physical_height=l['fragment']['physical_height'],outcome=l['outcome']) for l in a['lines']],grammar=r['grammar'],events=r['events'],responses=r['responses']))
    return dict(version='quantified-receptors-reader-001',family=data['family'],cases=cases,seconds=data['seconds'],peak_process_rss_bytes=data['peak_process_rss_bytes'],audit=dict(seconds=audit['seconds'],mutations=len(audit['mutations_rejected']),countermodel=audit['capture_countermodel']),native=dict(inventory_fingerprint=native['inventory_fingerprint'],seconds=native['seconds'],compile_seconds=native['compile_seconds'],audit_seconds=na['seconds'],mutations=len(na['mutations_rejected']),cases=natives))
if __name__=='__main__':
    p=DOC/'quantified-receptors-reader-001.json';p.write_text(json.dumps(build(),separators=(',',':'))+'\n');print(p.name,p.stat().st_size)
