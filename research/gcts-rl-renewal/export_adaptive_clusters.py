"""Lossless reader projection; full executed experiments stay in the raw file."""
import hashlib
import json
from pathlib import Path
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def project(data,audit):
    names=('status','placements','tile_generations','proof','endpoint','metrics','seconds',
           'grammar_seconds','positive_check_seconds','tiles','point_check','solution_transactions',
           'candidate_universe','mode','weights','deduction_scope')
    def run(r):
        out={n:r[n] for n in names if n in r}
        if 'compiled' in r:out['compiled_request']=r['compiled']['request']
        return out
    return dict(version='adaptive-clusters-reader-001',audit=audit,
                donors=[dict(spec=d['spec'],catalog=d['catalog'],result=run(d['result'])) for d in data['donors']],
                library=[dict(name=t['name'],pattern=t['pattern'],level=t['level'],children=t['children'],
                              source_id=t['source']['spec']['id'],source_members=t['source']['members']) for t in data['library']],
                cases=[dict(spec=c['spec'],catalog=c['catalog'],runs={k:run(r) for k,r in c['runs'].items()},
                            saturation={k:v for k,v in c['saturation'].items() if k!='region_certificate'}) for c in data['cases']],
                training=dict(seconds=data['training']['seconds'],episodes=len(data['training']['episodes']),
                              weights=data['training']['weights'],features=data['training']['features']),
                donor_seconds=data['donor_seconds'],seconds=data['seconds'],peak_process_rss_bytes=data['peak_process_rss_bytes'])


def main():
    raw=DOC/'adaptive-clusters-001.json';audit=json.loads((DOC/'adaptive-clusters-audit-001.json').read_bytes())
    if audit['input_sha256']!=hashlib.sha256(raw.read_bytes()).hexdigest():raise ValueError('current audit required')
    value=project(json.loads(raw.read_bytes()),audit)
    (DOC/'adaptive-clusters-reader-001.json').write_bytes(canonical(value)+b'\n')


if __name__=='__main__':main()
