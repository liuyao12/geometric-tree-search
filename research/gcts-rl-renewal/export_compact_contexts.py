"""Audited projection of searched rows, discharged commands and native spans."""
import gzip,hashlib,json
from pathlib import Path
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def project(data,audit,native,native_audit):
    cases=[]
    for c in data['cases']:
        r=c['result'];fields=('status','placements','tile_generations','proof','endpoint','metrics','seconds','tiles','point_check')
        row={k:r[k] for k in fields if k in r}
        if 'compact' in r:
            row['compact']={k:v for k,v in r['compact'].items() if k not in ('host','independent','source_check')}
        cases.append(dict(spec=c['spec'],catalog=c['catalog'],result=row,grammar_seconds=c['grammar_seconds'],
            total_seconds=c['total_seconds'],expanded_comparison=c['expanded_comparison']))
    ns=[]
    for c,a in zip(native['cases'],native_audit['cases']):
        ns.append(dict(name=c['name'],expected=c['expected'],header=c['header'],builder=c['builder'],checker=c['checker'],literal=c['literal'],
            lines=[dict(label=l['label'],outcome=l['outcome'],physical_height=l['fragment']['physical_height'],
                literal_width=l['fragment']['literal_width'],from_event=l['fragment']['from_event'],to_event=l['fragment']['to_event'],
                incoming=dict(assumptions=l['input_context']['assumptions'],forbidden=l['input_context']['forbidden'],
                    registry=l['input_context']['registry'],proved_count=len(l['input_context']['proved']))) for l in a['lines']],
            contexts=a['contexts'],fragments=a['fragments']))
    return dict(version='compact-contexts-reader-001',cases=cases,audit=audit,
        library=[{k:v for k,v in t.items() if k!='source'} for t in data['library']],
        transfer={k:v for k,v in data['transfer'].items() if k!='catalog'},
        seconds=data['seconds'],peak_process_rss_bytes=data['peak_process_rss_bytes'],
        native=dict(inventory_fingerprint=native['inventory_fingerprint'],inventory=native['inventory'],cases=ns,
            seconds=native['seconds'],compile_seconds=native['compile_seconds'],audit_seconds=native_audit['seconds'],
            audit_mutations=len(native_audit['mutations_rejected'])))
def main():
    data=json.loads((DOC/'compact-contexts-001.json').read_bytes());audit=json.loads((DOC/'compact-contexts-audit-001.json').read_bytes())
    native=json.loads(gzip.decompress((DOC/'context-wang-001.json.gz').read_bytes()));other=json.loads(gzip.decompress((DOC/'context-wang-audit-001.json.gz').read_bytes()))
    if audit['input_sha256']!=digest(DOC/'compact-contexts-001.json') or other['input_sha256']!=digest(DOC/'context-wang-001.json.gz'):raise ValueError('exact audit input required')
    (DOC/'compact-contexts-reader-001.json').write_bytes(canonical(project(data,audit,native,other))+b'\n')
if __name__=='__main__':main()
