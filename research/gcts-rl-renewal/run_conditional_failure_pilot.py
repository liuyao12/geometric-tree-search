"""Matched original/unary/pair/combined study, plus a fresh fork-and-join target."""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from certificate_boundary_cases import theory
from certificate_boundary_search import digest
from native_receptor_points import compile_guards
from semantic_receptor_points import Model
from semantic_inventory_search import search
from semantic_inventory_worker import oracle_for,verify,register
from semantic_point_smt import solve
from prefix_failure_markings import learn as learn_unary,MarkedModel as Unary
from audit_prefix_failure_markings import teacher as unary_teacher,check_learning as check_unary,check_overlay as audit_unary,extended_tree
from conditional_failure_markings import learn,MarkedModel,CombinedModel
from audit_conditional_failure_markings import teacher,check_learning,check_overlay,check_combined
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/conditional-attachments-20261011';TMP=Path('/private/tmp/gcts-conditional-attachments-20261011')


def joint_statement():
    p,q,r,s=[['pred',name,[]] for name in ('P','Q','R','S')]
    return dict(id='shared-premise-join',title='Shared premise, two branches, one conclusion',
        theory=theory(predicates=dict(P=0,Q=0,R=0,S=0),
            axioms=dict(seed=p,left=['imp',p,q],right=['imp',p,r],join=['imp',q,['imp',r,s]])),
        target=s,length=8,
        scope='New branching assertion and finite envelope. No proof commands, ordering, reference path or intermediate facts are supplied. Notebook 63 semantic families and policy are explicitly reused; fresh native guard compilation and registry admission.')


def main():
    began=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
    policy=json.loads((DOC/'semantic-inventory-policy-001.json').read_text())
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP),executable=str(TMP/'oracle')))
    summaries=[]
    try:
        for name in ('forked-semantic','shared-premise-join','renamed-five'):
            qstart=len(oracle.records);source=None
            if name=='shared-premise-join':
                spec=joint_statement();compiled=compile_guards(spec,oracle)
                if compiled['status']!='complete':raise ValueError('fresh joint guard compilation unfinished')
                inventory=register(spec,policy['library'],compiled,oracle)
                if inventory['status']!='native_accepted':raise ValueError('fresh joint inventory not admitted')
            else:
                path=DOC/('semantic-inventory-001-'+name+'-base-r1.json.gz')
                raw=path.read_bytes();old=json.loads(gzip.decompress(raw))
                spec,compiled,inventory=old['case'],old['compiled'],old['inventory']
                source=dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),
                    scope='Reused native-admitted catalog/registry only. Earlier search results and failure labels are not reused.')
            parent=Model(spec,compiled,inventory)
            unary=learn_unary(parent,400,.25,check=unary_teacher);uc=check_unary(parent,unary)
            def checking(base,probe):
                result=teacher(base,probe)
                if (probe['id']+1)%16==0:
                    print(name,'pair teachers',probe['id']+1,flush=True)
                return result
            learning=learn(parent,[(1,2),(2,3)],400,.25,check=checking);certificate=check_learning(parent,learning)
            singles={(p['slot'],digest(p['formula'])):p['label'] for p in unary['probes']}
            genuine=[p['id'] for p in learning['probes'] if p['label']=='negative'
                     and all(singles[j,digest(f)]=='positive' for j,f in zip(p['slots'],p['formulas']))]
            results=[];records={};checks={}
            for layer in ('original','unary','conditional','combined'):
                base=Model(spec,compiled,inventory)
                um=Unary(base,unary,uc);pm=MarkedModel(base,learning,certificate)
                if layer=='original':model=base;check=dict(status='original')
                elif layer=='unary':model=um;check=audit_unary(base,unary,uc,um.record())
                elif layer=='conditional':model=pm;check=check_overlay(base,learning,certificate,pm.record())
                else:
                    audit_unary(base,unary,uc,um.record());check_overlay(base,learning,certificate,pm.record())
                    model=CombinedModel(base,um,pm);check=check_combined(base,um.record(),pm.record(),model.record())
                record=model.record()
                if layer=='original':record['initial_marks']=sorted(model.initial().marks.items())
                records[layer]=record;checks[layer]=check
                for mode in ('base','fixed','learned'):
                    weights=policy['weights'] if mode=='learned' else None
                    # Fresh state, graph and metrics for every observed lane.
                    model.metrics.clear()
                    out=search(model,mode,weights=weights,attempts=5000,seconds=30,seed=66000)
                    checked=extended_tree(spec,record,out,inventory,weights,record['initial_marks'])
                    native=None
                    if out['proof'] is not None:
                        q=verify(oracle,spec,out['proof'],inventory,'conditional_pilot_final_'+layer+'_'+mode)
                        if q['result']['status']!='accepted':raise ValueError('fresh final native computation unfinished')
                        native=q['id'];fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                    results.append(dict(layer=layer,mode=mode,search=out,tree_check=checked,native_query=native))
                    print(name,layer,mode,out['status'],out['metrics'].get('attempts',0),'native',native,flush=True)
            smt=None
            if name=='shared-premise-join':
                smt=solve(Model(spec,compiled,inventory),seconds=30)
                if smt['proof']:
                    q=verify(oracle,spec,smt['proof'],inventory,'fresh_joint_z3_control')
                    if q['result']['status']!='accepted':raise ValueError('SMT joint native check unfinished')
                    fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                    smt['native_query']=q['id']
                print(name,'z3',smt['status'],flush=True)
            data=dict(version='conditional-failure-pilot-001',case=spec,compiled=compiled,inventory=inventory,
                reused_context=source,frozen_policy_sha256=hashlib.sha256((DOC/'semantic-inventory-policy-001.json').read_bytes()).hexdigest(),
                unary_learning=unary,unary_certificate=uc,learning=learning,certificate=certificate,
                genuine_conditional_negatives=genuine,models=records,overlay_checks=checks,results=results,
                smt_control=smt,records=oracle.records[qstart:],
                scope='One fresh paired observation per layer and ordering. Learning starts without imported failure assignments. Reuses disclosed Notebook 63 families/policy; original fork and chain admissions reused, new joint target freshly admitted. All teachers and final selected roots independently checked. Not cold timing or new RL training.')
            for q in data['records']:
                fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
            target=OUT/(name+'-pilot.json.gz');target.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))
            summary=dict(case=name,unary_counts=unary['counts'],pair_counts=learning['counts'],
                genuine_conditional_negatives=len(genuine),unary_learning_seconds=unary['seconds'],pair_learning_seconds=learning['seconds'],
                results=[dict(layer=r['layer'],mode=r['mode'],status=r['search']['status'],attempts=r['search']['metrics'].get('attempts',0),
                              seconds=r['search']['seconds'],native_query=r['native_query']) for r in results],
                artifact=target.name,bytes=target.stat().st_size,smt_status=smt['status'] if smt else None)
            summaries.append(summary)
            (OUT/'summary.json').write_text(json.dumps(dict(status='in_progress',cases=summaries),indent=2)+'\n')
        (OUT/'summary.json').write_text(json.dumps(dict(status='paired_pilot_complete',cases=summaries,
            native_queries=len(oracle.records),seconds=time.perf_counter()-began),indent=2)+'\n')
        print('conditional pilot complete',round(time.perf_counter()-began,3),flush=True)
    finally:oracle.close()


if __name__=='__main__':main()
