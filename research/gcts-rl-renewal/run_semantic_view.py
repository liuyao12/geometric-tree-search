"""Small browser projection of the immutable full experiment; no new search."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    source=DOCS/'semantic-proofs-001.json';d=json.loads(source.read_text());out={k:d[k] for k in ('configuration','scope','control','compile_seconds','total_seconds','peak_driver_memory_bytes','program_sha256')}
    out.update(parent=dict(file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest()),exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),independent_audit={k:v for k,v in d['independent_audit'].items() if k!='cases'},cases=[])
    for c in d['cases']:
        row=dict(problem=c['problem'],catalog_sha256=c['catalog_sha256'],catalog={k:c['catalog'][k] for k in ('theory','target','target_id','formulas','close_variables','configuration')},rules=[],runs=[])
        for rule in c['catalog']['rules']:
            recipe=rule['recipe'];label=recipe['witness']['rule'] if recipe['kind']=='primitive' else recipe.get('axiom',recipe['kind'])
            row['rules'].append(dict(inputs=rule['inputs'],output=rule['output'],kind=recipe['kind'],label=label,move=recipe.get('move')))
        for run in c['runs']:
            r=run['result'];v={k:r[k] for k in ('status','nodes','branches','attempts','backtracks','seconds','placements','limits','scope')}
            for k in ('forced','build_seconds','graph_seconds','candidate_universe','peak_candidate_nodes','peak_incidences','decode_seconds','samples','metrics'):
                if k in r:v[k]=r[k]
            if 'decoded' in r:v['proof']=r['decoded']['request']['proof'];v['block_count']=len(r['decoded']['request']['blocks'])
            row['runs'].append(dict(lane=run['lane'],result=v,native=run.get('native'),cold_seconds=run['cold_seconds'],catalog_build_seconds=run['catalog_build_seconds'],catalog_validation_seconds=run['catalog_validation_seconds']))
        row['audit']=next(a for a in d['independent_audit']['cases'] if a['id']==c['problem']['id']);out['cases'].append(row)
    target=DOCS/'semantic-proof-view-001.json';target.write_text(json.dumps(out,separators=(',',':'))+'\n');print(target.name,target.stat().st_size)
if __name__=='__main__':main()
