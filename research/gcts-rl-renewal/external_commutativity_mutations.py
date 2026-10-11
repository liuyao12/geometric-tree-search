"""Post-result adversarial replay of every actually used certificate method."""
import copy,json,time
from pathlib import Path
from external_commutativity_audit import OUT,load,dump,sha,need
from external_left_successor_focus import check_output
from external_prover_check import records

def run():
    began=time.perf_counter();summary=load(OUT/'summary.json');audit=load(OUT/'audit.json')
    need(audit['status']=='passed_complete_result_source_input_replay_audit','full result replay gate')
    source=Path(__file__);dump(OUT/'mutation-plan.json',dict(source_sha256=sha(source.read_bytes()),summary_sha256=sha((OUT/'summary.json').read_bytes()),audit_sha256=sha((OUT/'audit.json').read_bytes()),scope='Post-result mutations of all actual setup and target witness boundaries and focused refutations; no new proof search or soundness relaxation.'))
    cases=[];census=dict(lines=0,boundaries=0,focused_trees=0)
    def reject(name,text,mapping,path,bad):
        try:check_output(text,mapping,path,saved=bad)
        except (ValueError,TimeoutError,TypeError,KeyError,IndexError) as error:cases.append(dict(name=name,status='rejected',error=repr(error)));return
        raise AssertionError('corrupt actual certificate accepted '+name)
    for o in summary['setup']+summary['observations']:
        if o['certificate_status']!='checked_complete_derivation':continue
        stem=o['stem'];path=OUT/('commutativity-'+o['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(stem+'.tstp')).read_text();good=o['proof_check']['result']
        need(len(records(text))==good['steps'],'actual proof census');census['lines']+=good['steps']
        for i,c in enumerate(good['checks']):
            if c['status']=='checked_conservative_context_extension':
                census['boundaries']+=1
                for field in ('context_after_sha256','registry_before_sha256'):
                    bad=copy.deepcopy(good);bad['checks'][i][field]='0'*64;reject(stem+':'+c['name']+':'+field,text,mapping,str(path),bad)
                for field,value in [('symbol','unbound_witness'),('dependencies',[[1]])]:
                    bad=copy.deepcopy(good);bad['checks'][i]['reconstruction']['witnesses'][0][field]=value;reject(stem+':'+c['name']+':'+field,text,mapping,str(path),bad)
            proof=c.get('proof')
            if proof and proof['certificate']['method']=='focused_exact_universal_instances':
                census['focused_trees']+=1;bad=copy.deepcopy(good);bad['checks'][i]['proof']['certificate']['refutation']['tree']=['euf'];reject(stem+':'+c['name']+':altered refutation',text,mapping,str(path),bad)
                j=next((j for j,e in enumerate(proof['certificate']['instances']) if e['substitution']),None)
                if j is not None:
                    bad=copy.deepcopy(good);bad['checks'][i]['proof']['certificate']['instances'][j]['substitution'].clear();reject(stem+':'+c['name']+':missing universal substitution',text,mapping,str(path),bad)
        bad=copy.deepcopy(good);bad['checks'][-1]['parents']=[];reject(stem+':missing final parents',text,mapping,str(path),bad)
        altered=text.replace("file('"+str(path)+"'","file('wrong.p'",1);reject(stem+':wrong input file',altered,mapping,str(path),good)
    result=dict(status='passed_actual_certificate_corruption_audit',proof_census=census,corruptions=cases,seconds=time.perf_counter()-began,summary_sha256=sha((OUT/'summary.json').read_bytes()),complete_audit_sha256=sha((OUT/'audit.json').read_bytes()),mutation_plan_sha256=sha((OUT/'mutation-plan.json').read_bytes()))
    dump(OUT/'mutation-audit.json',result);print(json.dumps(dict(status=result['status'],proof_census=census,corruptions=len(cases),seconds=result['seconds'])),flush=True)
if __name__=='__main__':run()
