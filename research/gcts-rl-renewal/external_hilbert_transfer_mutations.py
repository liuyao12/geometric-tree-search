"""Actual certificate corruptions; independent unchanged replay functions."""
import copy,time,re
from pathlib import Path
from external_hilbert_transfer_audit import OUT,load,dump,need,sha
from external_left_successor_focus import check_output,replay_consequence
from external_prover_check import records,closed
from external_hilbert_run import validate_theory

def run():
    began=time.perf_counter();summary=load(OUT/'summary.json');audit=load(OUT/'audit.json')
    need(audit['status']=='passed_complete_result_source_input_replay_audit','complete audit first')
    dump(OUT/'mutation-plan.json',dict(source_sha256=sha(Path(__file__).read_bytes()),summary_sha256=sha((OUT/'summary.json').read_bytes()),audit_sha256=sha((OUT/'audit.json').read_bytes()),scope='Post-result altered trees and universal-instance bindings from every actual local certificate, plus exact-input/parent trace corruptions. No E run, changed checker, proof search or soundness relaxation.'))
    cases=[];census=dict(lines=0,boundaries=0,focused_trees=0,propositional_trees=0)
    def reject(name,fn):
        try:fn()
        except (ValueError,TimeoutError,TypeError,KeyError,IndexError) as e:cases.append(dict(name=name,status='rejected',reason=repr(e)));return
        raise ValueError('corrupt certificate accepted '+name)
    for o in summary['observations']:
        if o['certificate_status']!='checked_complete_derivation':continue
        path=OUT/('hilbert-'+o['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(o['stem']+'.tstp')).read_text();good=o['proof_check']['result'];rs=records(text);known={r['name']:r for r in rs};census['lines']+=len(rs)
        for c in good['checks']:
            if c['status']=='checked_conservative_context_extension':census['boundaries']+=1
            if not c.get('proof'):continue
            parents=[closed(known[n]['formula']) for n in c['parents']];child=closed(known[c['name']]['formula']);proof=c['proof'];method=proof['certificate']['method'];prefix=o['stem']+':'+c['name']
            if method=='focused_exact_universal_instances':
                census['focused_trees']+=1;bad=copy.deepcopy(proof);bad['certificate']['refutation']['tree']=['euf'];reject(prefix+':false EUF conflict',lambda:replay_consequence(parents,child,bad))
                j=next((j for j,e in enumerate(proof['certificate']['instances']) if e['substitution']),None)
                if j is not None:
                    bad=copy.deepcopy(proof);bad['certificate']['instances'][j]['substitution'].clear();reject(prefix+':missing universal substitution',lambda:replay_consequence(parents,child,bad))
                bad=copy.deepcopy(proof);bad['certificate']['input_sha256']='0'*64;reject(prefix+':changed relation digest',lambda:replay_consequence(parents,child,bad))
            elif method=='uniform_propositional_abstraction':
                census['propositional_trees']+=1;bad=copy.deepcopy(proof);bad['certificate']['check']['refutation']['tree']=['euf'];reject(prefix+':false propositional conflict',lambda:replay_consequence(parents,child,bad))
            else:raise ValueError('post-result mutation coverage missing for method '+method)
        bad=copy.deepcopy(good);bad['checks'][-1]['parents']=[];reject(o['stem']+':missing final parent bindings',lambda:check_output(text,mapping,str(path),saved=bad))
        changed=text.replace("file('"+str(path)+"'","file('wrong.p'",1);need(changed!=text,'real file corruption');reject(o['stem']+':wrong original input path',lambda:check_output(changed,mapping,str(path),saved=good))
        first=next(r for r in rs if r['source'].get('head')=='file' and r['role']!='conjecture');pattern=r'((?:fof|cnf)\('+re.escape(first['name'])+r',\s*'+re.escape(first['role'])+r',).*?(,\s*file\()'
        changed,count=re.subn(pattern,r'\g<1> $false\g<2>',text,count=1);need(count==1,'real supplied axiom corruption');reject(o['stem']+':altered supplied axiom',lambda:check_output(changed,mapping,str(path),saved=good))
    spec=load(OUT/'inventory.json')['cases'][0]['spec']
    bad=copy.deepcopy(spec);bad['theory']['schemas']=['unexported'];reject('unexported theory schema',lambda:validate_theory(bad))
    bad=copy.deepcopy(spec);bad['theory']['hidden_axioms']={};reject('hidden theory feature',lambda:validate_theory(bad))
    result=dict(status='passed_actual_certificate_corruption_audit',proof_census=census,corruptions=cases,seconds=time.perf_counter()-began,summary_sha256=sha((OUT/'summary.json').read_bytes()),complete_audit_sha256=sha((OUT/'audit.json').read_bytes()),mutation_plan_sha256=sha((OUT/'mutation-plan.json').read_bytes()),scope='Every actually used logical tree has an altered-conflict test, every focused relation has exact source binding tested, and every proof has trace/input/parent corruptions. This audit reuses unchanged replay code; it does not claim formal kernel verification.')
    dump(OUT/'mutation-audit.json',result);print(dict(status=result['status'],census=census,corruptions=len(cases),seconds=result['seconds']),flush=True)
if __name__=='__main__':run()
