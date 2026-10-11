"""Complete source/outcome replay and corruption audit for the corrected control."""
import argparse,copy,json,time
import external_left_successor_focus as checker
from external_left_successor_focus_run import OUT,ROOT,bind,unchanged,operation
from external_left_successor_inputs import dump,load
from external_prover_check import native_formula,records
from external_prover_inputs import canonical,sha
import external_left_successor_audit as original

def run():
    began=time.perf_counter();plan=unchanged();bind();original.after()
    result=load(OUT/'audit.json')
    if result['successful_checked_derivations']!=4 or result['unknown_checks']!=0:
        dump(OUT/'complete-audit.json',dict(status='unknown_corrected_certificates',saved_outcomes=result,seconds=time.perf_counter()-began));return
    setup=load(OUT/'setup.json');summary=load(OUT/'summary.json');pre=load(OUT/'pre-run-audit.json')
    replays=[]
    for e in setup['interfaces']:
        r=operation(dict(e['request'],operation='interface-replay',saved=e['measurement']['result']),'post-audit-'+e['id']+'-replay',30)
        if r['status']!='complete':raise ValueError('complete post-run interface replay')
        replays.append(dict(id=e['id'],measurement=r))
    cases=[];counts=dict(lines=0,boundaries=0,focused_trees=0)
    def reject(name,text,mapping,path,saved):
        try:checker.check_output(text,mapping,path,saved=saved)
        except (ValueError,TimeoutError,TypeError,KeyError,IndexError) as error:
            cases.append(dict(name=name,status='rejected',error=repr(error)));return
        raise AssertionError('actual corrupted complete proof accepted '+name)
    for o in summary['observations']:
        stem='left-successor-'+o['kind']+'-r'+str(o['repetition']);path=OUT/('left-successor-'+o['kind']+'.p');mapping=load(path.with_suffix('.mapping.json'));text=(OUT/(stem+'.tstp')).read_text();good=o['proof_check']['result']
        if len(records(text))!=good['steps']:raise ValueError('actual proof line census')
        counts['lines']+=good['steps']
        for i,c in enumerate(good['checks']):
            if c['status']=='checked_conservative_context_extension':
                counts['boundaries']+=1
                for field,value in [('context_after_sha256','0'*64),('registry_before_sha256','0'*64)]:
                    bad=copy.deepcopy(good);bad['checks'][i][field]=value
                    reject(stem+':'+c['name']+':'+field,text,mapping,str(path),bad)
                bad=copy.deepcopy(good);bad['checks'][i]['reconstruction']['witnesses'][0]['symbol']='unbound_witness'
                reject(stem+':'+c['name']+':witness provenance',text,mapping,str(path),bad)
                bad=copy.deepcopy(good);bad['checks'][i]['reconstruction']['witnesses'][0]['dependencies']=[[1]]
                reject(stem+':'+c['name']+':witness scope',text,mapping,str(path),bad)
            proof=c.get('proof')
            if proof and proof['certificate']['method']=='focused_exact_universal_instances':
                counts['focused_trees']+=1
                bad=copy.deepcopy(good);bad['checks'][i]['proof']['certificate']['refutation']['tree']=['euf']
                reject(stem+':'+c['name']+':altered focused tree',text,mapping,str(path),bad)
                source=next((j for j,e in enumerate(proof['certificate']['instances']) if e['substitution']),None)
                if source is not None:
                    bad=copy.deepcopy(good);bad['checks'][i]['proof']['certificate']['instances'][source]['substitution'].clear()
                    reject(stem+':'+c['name']+':missing quantified substitution',text,mapping,str(path),bad)
        changed=text.replace("file('"+str(path)+"'","file('wrong.p'",1)
        reject(stem+':original input path',changed,mapping,str(path),good)
        bad=copy.deepcopy(good);bad['checks'][-1]['parents']=[]
        reject(stem+':empty contradiction parents',text,mapping,str(path),bad)
    # Exact reused prior-zero-left evidence is bound to its authoritative complete
    # admission/search/compaction audits; no native replay is rerun here.
    prior=ROOT/'.gcts-active/external-induction-tstp-20261011'
    prior_plan=load(prior/'plan.json');authority=load(prior/'native-authority.json');prior_audit=load(prior/'audit.json')
    if sha((prior/'native-authority.json').read_bytes())!=prior_plan['native_authority_sha256'] or prior_audit['status']!='passed' or authority['query_count']!=92:raise ValueError('complete authoritative prior92 binding')
    for n,h in load(OUT/'inventory.json')['source_theorem_native_binding']['prior_audits'].items():
        if authority['exact_artifacts'][n]['sha256']!=h or sha((OUT/'snapshot/prior-zero-left'/n).read_bytes())!=h:raise ValueError('same exact transferred theorem audits')
    old=load(OUT/'prior-attempt/summary.json')
    if len(old['observations'])!=4 or any(o['certificate_status']!='unknown' for o in old['observations']):raise ValueError('every original validation unknown retained')
    if sha((OUT/'all-tests.json').read_bytes())=='' or load(OUT/'all-tests.json')['status']!='passed':raise ValueError('pre-run counterexample gates')
    final=dict(status='passed_complete_corrected_control',plan_sha256=sha((OUT/'plan.json').read_bytes()),summary_sha256=sha((OUT/'summary.json').read_bytes()),setup_sha256=sha((OUT/'setup.json').read_bytes()),pre_run_gate_sha256=sha((OUT/'pre-run-audit.json').read_bytes()),four_proof_replays=result,
        complete_interfaces=24,post_run_interface_replays=replays,current_native_computations_bound=36,prior_native_computations_bound=92,
        prior_native_authority_sha256=sha((prior/'native-authority.json').read_bytes()),prior_complete_audit_sha256=sha((prior/'audit.json').read_bytes()),
        preserved_unknown_count=4,preserved_unknown_manifest_sha256=plan['prior_attempt_manifest_sha256'],proof_census=counts,
        corruptions=cases,fixture_census=dict(input_closure=13,focused_relations=12,focused_mutations=13,shared_context=51),
        seconds=time.perf_counter()-began,scope='Exact universal target and complete three-instance union; separate FOL full-step certificates and independent exact-instance/refutation replay, no native Wang acceptance for E. All current native admissions and prior transfer audits bound as reuse; no native rerun or RL effect is inferred.')
    dump(OUT/'complete-audit.json',final);print('COMPLETE CORRECTED CONTROL AUDIT PASSED',counts,len(cases),final['seconds'],flush=True)

if __name__=='__main__':run()
