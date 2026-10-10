"""Small read-only projection: actual core squares and discovered proof rows."""
import gzip,hashlib,json
from pathlib import Path
from audit_serialized_kernel import replay
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    file=DOCS/'shared-wang-001.json.gz';d=json.loads(gzip.decompress(file.read_bytes()))
    audit=json.loads((DOCS/'shared-wang-audit-001.json').read_text())
    if audit['status']!='passed' or sha(file.read_bytes())!=audit['source_artifact']['sha256']:raise ValueError('audit binding')
    i=Inventory(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes()))
    cases=[];states=set()
    for row in d['cases']:
        c=row['catalog'];r=row['result'];request=row['request'];primitive=replay(json.dumps(request,separators=(',',':')).encode('ascii'))
        if primitive['status']!='accepted':raise ValueError('displayed primitive proof')
        tiles=[]
        for slot,rid,refs in sorted(r['placements']):
            rule=c['rules'][rid]
            tiles.append(dict(slot=slot,refs=refs,formula=c['formulas'][rule['output']],recipe=rule['recipe'],
                              root_line=r['decoded']['commands'][slot]['final_line']))
        for tile in row['patch']['tiles']:
            for symbol in tile['triple']:
                decoded=i.decode(symbol)
                if decoded is not None:states.add(decoded[0])
        cases.append(dict(kind=row['kind'],target=request['target'],theory=request['theory'],request=request,
            tiles=tiles,primitive=primitive['proof'],search=dict(nodes=r['nodes'],attempts=r['attempts'],seconds=row['search_cold_seconds']),
            selected=row['selected'],literal=row['literal'],patch=row['patch'],fixed_bytes=len(row['fixed_word']),
            free_bytes=len(row['free_word']),problem_pin=row['problem_pin'],inventory_fingerprint=row['inventory_fingerprint']))
    transitions={str(q):{str(s):list(a) for s in range(i.A) if (a:=i.transition(q,s)) is not None} for q in sorted(states)}
    view=dict(version=d['version'],source=audit['source_artifact'],audit=audit,inventory=d['inventory'],
        transition_rows=transitions,cases=cases,controls=[dict(name=r['name'],status=r['result']['status']) for r in d['controls']],
        total_seconds=d['total_seconds'],compile_seconds=d['compile_seconds'],sources=d['sources'])
    (DOCS/'shared-wang-reader-001.json').write_text(json.dumps(view,separators=(',',':'))+'\n')
    print('exported',len(cases),'queries',sum(len(r['patch']['tiles']) for r in cases),'literal squares',sum(len(r['primitive']) for r in cases),'primitive lines')
if __name__=='__main__':main()
