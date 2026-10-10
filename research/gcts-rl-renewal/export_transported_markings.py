"""Exact compact reader projection, bound to the independent transfer audit."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    raw=json.loads((DOC/'transported-markings-001.json').read_bytes())
    old=json.loads((DOC/'movable-regions-001.json').read_bytes())
    audit=json.loads((DOC/'transported-markings-audit-001.json').read_bytes())
    if audit['input_sha256']!=digest(DOC/'transported-markings-001.json') or raw['donor_sha256']!=digest(DOC/'movable-regions-001.json'):
        raise ValueError('exact audited inputs')
    if audit['source_sha256']!=digest(HERE/'audit_transported_markings.py'):
        raise ValueError('audit source')
    for pins in (raw['sources'],old['sources'],audit['helpers']):
        if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('frozen sources')
    def project(result):
        fields=('status','proof','placements','endpoint','metrics','seconds','binding_seconds','rule_tests','known','fits_region_bound',
                'tiles','tile_generations','point_check','erased_check','positive_assembly_and_check_seconds')
        row={k:result[k] for k in fields if k in result}
        if result.get('proof') is not None and 'compiled' in result:
            row['compiled_request']=result['compiled']['request']
            if 'deduced' in result:row['deduced_request']=result['deduced']['request']
        return row
    donors=[]
    for row in raw['donors']:
        source=next(c for c in old['cases'] if c['spec']['id']==row['id'])
        donors.append(dict(row,spec=source['spec'],catalog=source['catalog'],
                           certified=[dict(pair=c['pair'],check=k) for c,k in zip(source['certified'],row['checks'])],
                           original_grammar_seconds=source['build_seconds']))
    cases=[]
    for c in raw['cases']:
        runs={lane:project(r) for lane,r in c['runs'].items()}
        fields=('spec','donor','catalog','transport','transport_check','grammar_seconds',
                'construction_seconds','verification_seconds','fresh_pairs','fresh_certification_seconds',
                'fresh_encoding_seconds','fresh_training_seconds')
        cases.append(dict({k:c[k] for k in fields},runs=runs))
    control=raw['unsafe_control']
    return dict(version='transported-markings-reader-001',donors=donors,cases=cases,
                audit=dict(input_sha256=audit['input_sha256'],seconds=audit['seconds'],
                           mutations=len(audit['mutations_rejected']),
                           recipient_pair_states=sum(p['nodes'] for c in audit['cases'] for p in c['recipient_pairs'])),
                producer_seconds=raw['seconds'],peak_process_rss_bytes=raw['peak_process_rss_bytes'],
                unsafe_control=dict(source_spec=control['source_spec'],recipient_spec=control['recipient_spec'],
                                    pair=control['pair'],old_status=control['old_result']['status'],
                                    rejection=control['rejected_reason'],new_result=project(control['new_result']),
                                    catalog=control['catalog']))


if __name__=='__main__':
    (DOC/'transported-markings-reader-001.json').write_text(json.dumps(build(),separators=(',',':'))+'\n')
