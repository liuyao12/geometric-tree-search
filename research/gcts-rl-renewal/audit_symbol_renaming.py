"""Independent symbol-bijection, primitive/native input and point-graph audit."""
import copy,hashlib,json,time
from pathlib import Path
from audit_serialized_kernel import freeze,replay
from audit_proof_compaction import native_binding
import audit_induction_proofs as I
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def pack(a):return json.dumps(a,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def need(a,s):
    if not a:raise ValueError(s)
def renamed(value,names,axioms):
    if isinstance(value,list):
        if value and value[0]=='pred':return ['pred',names[value[1]],[renamed(x,names,axioms) for x in value[2]]]
        return [renamed(x,names,axioms) for x in value]
    if not isinstance(value,dict):return value
    result={}
    for key,item in value.items():
        if key=='predicates':result[key]={names[k]:v for k,v in item.items()}
        elif key=='axioms':result[key]={axioms[k]:renamed(v,names,axioms) for k,v in item.items()}
        elif key=='name' and value.get('rule')=='axiom':result[key]=axioms[item]
        elif key=='axiom':result[key]=axioms[item]
        else:result[key]=renamed(item,names,axioms)
    return result
def main():
    started=time.perf_counter();path=DOCS/'symbol-renaming-001.json';d=json.loads(path.read_text());source=(DOCS/d['source']['file']).read_bytes();old=json.loads(source)
    need(hashlib.sha256(source).hexdigest()==d['source']['sha256'],'audited source binding')
    for n,pin in d['sources'].items():need(hashlib.sha256((HERE/n).read_bytes()).hexdigest()==pin,'source pin '+n)
    need([r['id'] for r in d['cases']]==['I.5','I.6','triangle-order'],'all displayed proofs covered')
    need(set(d['names'])==set(d['names'].keys()) and len(set(d['names'].values()))==len(d['names']),'bijective symbol map')
    code=json.loads((DOCS/'tree-kernel-001.json').read_text())['program'];rows=[];negative=0
    for r in d['cases']:
        original=next(x for x in old['runs'] if x['id']==r['id'] and 'decoded' in x['result']);req=original['result']['decoded']['request']
        need(r['source_request_sha256']==hashlib.sha256(pack(req)).hexdigest(),'original request pin')
        expect=renamed(req,d['names'],r['axiom_names']);need(expect==r['request'],'exact syntax renaming, every interface')
        p=replay(pack(r['request']));need(p['status']=='accepted' and p['expanded_lines']==r['primitive_lines']==original['primitive_lines'],'whole primitive proof')
        native_binding(code,r['request'],r['native']);need(r['native']['status']=='accepted','native result')
        c=original['catalog'];rc=renamed(c,d['names'],r['axiom_names']);a=I.Points(freeze(c),original['length'],'support');b=I.Points(freeze(rc),original['length'],'support')
        need(a.tiles==b.tiles and a.initial_marks==b.initial_marks and len(a.tiles)==r['identical_point_candidates'],'every exact candidate and boundary marking identical')
        wrong=copy.deepcopy(r['request']);wrong['theory']['predicates'][d['names']['SegEq']]=3
        need(replay(pack(wrong))['status']=='rejected','changed signature rejected');negative+=1
        wrong=copy.deepcopy(r['request']);used=next(l['name'] for block in wrong['blocks'] for l in block['proof'] if l['rule']=='axiom');wrong['theory']['axioms'].pop(used)
        need(replay(pack(wrong))['status']=='rejected','undeclared axiom rejected');negative+=1
        graph=None
        if 'fresh_gcts_control' in r:
            control=r['fresh_gcts_control'];graph=[I.point_run(freeze(c),3,freeze(control['original'])),I.point_run(freeze(rc),3,freeze(control['renamed']))]
            need(control['original']['search_tree']==control['renamed']['search_tree'] and control['renamed']['decoded']['request']==r['request'],'identical full graph trajectory and exact proof')
        rows.append(dict(id=r['id'],primitive_lines=p['expanded_lines'],point_candidates=len(a.tiles),fresh_graph_audits=graph))
    d['independent_audit']=dict(status='passed',seconds=time.perf_counter()-started,cases=rows,mutation_rejections=negative,method='independent exact AST/name bijection; primitive replay; native code/input binding; independently enumerated point inventories; both full elementary GCTS graph/rollback traces')
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print('passed',len(rows),'renamings,',negative,'negative controls')
if __name__=='__main__':main()
