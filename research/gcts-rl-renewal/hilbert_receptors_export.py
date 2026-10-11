"""Export the audited symbolic incidence pilot as a standalone proof reader."""
import gzip,hashlib,html,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/hilbert-receptors-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def term(t):return r'\mathrm{'+t[1]+r'}' if t[0]=='fun' else t[1]
def formula(f):
    k=f[0]
    if k=='pred':return r'\operatorname{'+f[1]+r'}\!\left('+','.join(term(t) for t in f[2])+r'\right)'
    if k=='eq':return term(f[1])+'='+term(f[2])
    if k=='not':return r'\neg\left('+formula(f[1])+r'\right)'
    if k=='all':return r'\forall '+f[1]+r'\, '+formula(f[2])
    if k=='bot':return r'\bot'
    return r'\left('+formula(f[1])+{'imp':r'\Rightarrow ','and':r'\land ','or':r'\lor '}[k]+formula(f[2])+r'\right)'
def shown(f,hyp):return 'H' if f==hyp else formula(f)
def main():
    audit=json.loads((OUT/'audit.json').read_text());summary=json.loads((OUT/'summary.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    if audit['status']!='passed' or summary['status']!='complete':raise ValueError('unfinished pilot cannot be published as verified')
    native=load(OUT/'native.json.gz');data=dict(version='hilbert-receptors-001',audit=audit,summary=summary,plan=plan,cases=[])
    closure_audit=json.loads((OUT/'closure-audit.json').read_text())
    if closure_audit['status']!='passed':raise ValueError('closure diagnostic replay unfinished')
    data['closure']=dict(plan=json.loads((OUT/'closure-plan.json').read_text()),result=json.loads((OUT/'closure-result.json').read_text()),audit=closure_audit,
                         heap=json.loads((OUT/'closure-heap-diagnosis.json').read_text()),candidate=json.loads((OUT/'closure-input.json').read_text()),native=load(OUT/'closure-native.json.gz'))
    for spec in plan['cases']:
        raw=load(OUT/(spec['id']+'.json.gz'));hyp=spec['theory']['axioms']['common-distinct-points'];item=dict(spec=spec,hypothesis_tex=formula(hyp),target_tex=formula(spec['target']),inventory=raw['inventory'],compiled=raw['compiled'],observations=[])
        for obs in raw['observations']:
            r=obs['search'];selected={tuple(p['key']):p for p in obs['model']['placements']};proof=r['proof'];rows=[]
            if proof:
                for j,c in enumerate(proof):
                    keys=[k for k in r['placements'] if k[0]==j];tiles=[selected[tuple(k)] for k in sorted(keys,key=lambda k:k[1])];ports=[]
                    for p in tiles:
                        words=[]
                        for (x,y),v in p['marks']:
                            if x%4==2 and y in (0,1):
                                kind='formula' if y==0 else 'command';entry=obs['model']['catalog'][kind][v];words.append(dict(point=[x,y],value=v,kind=kind,word=entry['value']))
                        tile=dict(key=p['key'],role=['C','G','I1','I2'][p['key'][1]],marks=p['marks'],occupancy=p['occupancy'],words=words,kind=p['kind'])
                        if 'source' in p:tile['source']=p['source']
                        ports.append(tile)
                    if c['rule']=='axiom':words='Given: '+('the nine conditions abbreviated by H.' if c['name']=='common-distinct-points' else 'C is incident with u.' if c['name']=='extra-incidence' else 'the universally quantified uniqueness axiom.')
                    elif c['rule']=='block':
                        d=next(d for d in raw['inventory']['definitions'] if d['name']==c['name']);words=('Apply the uniqueness axiom to the earlier common-point conditions.' if d['family']=='universal-uniqueness' else 'Use the earlier line equality to replace the line argument of the earlier incidence statement.')
                    else:words={'refl':'Equality is reflexive.','tautology':'This formula is a propositional tautology.','mp':'Apply the earlier implication to its antecedent.','generalize':'Universally quantify the earlier formula.'}.get(c['rule'],c['rule'])
                    rows.append(dict(index=j+1,command=c,tex=shown(c['formula'],hyp),english=words,tiles=ports))
            query=native[obs['native_query']] if obs['native_query'] is not None else None
            item['observations'].append(dict(lane=obs['lane'],repetition=obs['repetition'],status=r['status'],metrics=r['metrics'],seconds=r['seconds'],setup_seconds=obs['setup_seconds'],peak_rss_bytes=obs['peak_rss_bytes'],rows=rows,root_restored=r['root_restored'],native_query=obs['native_query'],cached_native_acceptance=obs['cached_native_acceptance'],native=None if query is None else dict(request=query['request'],request_sha256=query['request_sha256'],result=query['result'],seconds=query['seconds'])))
        data['cases'].append(item)
    names=['plan.json','native.json.gz','summary.json','audit.json']+[s['id']+'.json.gz' for s in plan['cases']]
    names+=['closure-plan.json','closure-result.json','closure-audit.json','closure-heap-diagnosis.json','closure-input.json','closure-native.json.gz','ground-accepted-request.json']
    artifacts=[]
    for name in names:
        dest='hilbert_receptors_'+name.replace('-','_');shutil.copyfile(OUT/name,DOC/dest);p=DOC/dest;artifacts.append(dict(path=dest,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    data['artifacts']=artifacts;(DOC/'hilbert_receptors_reader_001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    counts={s:sum(o['status']==s for c in data['cases'] for o in c['observations']) for s in ['finite_marked_proof_region','unknown_search_budget','exhausted_finite_marked_region']}
    print(json.dumps(dict(reader_bytes=(DOC/'hilbert_receptors_reader_001.json').stat().st_size,counts=counts,artifacts=artifacts),indent=2))
if __name__=='__main__':main()
