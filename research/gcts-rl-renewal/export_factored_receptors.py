"""Small reader projection bound to the search and operational audits."""
import gzip,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build():
    data=json.loads((DOC/'factored-receptors-001.json').read_text());audit=json.loads((DOC/'factored-receptors-audit-001.json').read_text())
    if audit['producer_sha256']!=digest(DOC/'factored-receptors-001.json') or audit['source_sha256']!=digest(HERE/'audit_factored_receptors.py'):raise ValueError('search audit binding')
    native=json.loads(gzip.decompress((DOC/'factored-wang-001.json.gz').read_bytes()));na=json.loads(gzip.decompress((DOC/'factored-wang-audit-001.json.gz').read_bytes()))
    if na['input_sha256']!=digest(DOC/'factored-wang-001.json.gz') or na['source_sha256']!=digest(HERE/'audit_factored_wang.py'):raise ValueError('operational audit binding')
    cases=[]
    for c in data['cases']:
        out={k:c[k] for k in ('id','title','mode','target','length','hypotheses','family','pool','rules','candidate_universe','universe_build_seconds')}
        out['runs']={lane:{k:v for k,v in r.items() if k in ('status','seconds','build_seconds','metrics','graph_metrics','primitive_lines','proof','point_tiles','placements','independent','fits_slot_bound','candidate_cap')} for lane,r in c['runs'].items()}
        out['frames']=[dict(f,domains=[dict(point=d['point'],count=d['count'],factor_records=len(d['blocks']),sample_blocks=d['blocks'][:6]) for d in f['domains']]) for f in c.get('frames',[])]
        cases.append(out)
    row=native['cases'][0]
    return dict(version='factored-receptors-reader-001',cases=cases,audit=dict(seconds=audit['seconds'],mutations=len(audit['mutations_rejected']),policy_proposal_steps=audit['policy_proposal_steps'],sha256=digest(DOC/'factored-receptors-audit-001.json')),
        seconds=data['seconds'],peak_process_rss_bytes=data['peak_process_rss_bytes'],reused_policy_training_seconds=data['reused_policy_training_seconds'],ground_candidate_cap=data['ground_candidate_cap'],
        native=dict(result='accepted',inventory_fingerprint=native['inventory_fingerprint'],builder=row['builder'],checker=row['checker'],literal=row['literal'],seconds=native['seconds'],audit_seconds=na['seconds'],
            lines=[dict(label=l['label'],input=l['input_context'],output=l['output_context'],outcome=l['outcome'],physical_height=l['fragment']['physical_height']) for l in na['cases'][0]['lines']],
            grammar=row['grammar'],events=row['events'],responses=row['responses']))
if __name__=='__main__':
    view=build();p=DOC/'factored-receptors-reader-001.json';p.write_text(json.dumps(view,separators=(',',':'))+'\n');print(p.name,p.stat().st_size)
