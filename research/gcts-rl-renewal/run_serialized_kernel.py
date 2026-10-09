"""Sequential checker controls. Authored certificates; no GCTS/RL search claim."""
import hashlib
import copy
import json
import pathlib
import resource
import statistics
import time
from datetime import datetime,timezone
import logic
from serialized_kernel import check,canonical,problem_hash
from serialized_examples import addition_induction,flatten_blocks,primitive_cases,adversarial_cases,propositional_cases,request

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/research/gcts-rl-renewal/serialized-kernel-001.json'

def record(name,payload,expected,**kwargs):
    result=check(payload,**kwargs)
    if result['status']!=expected: raise AssertionError((name,result))
    return dict(name=name,certificate=payload.decode('ascii'),certificate_sha256=hashlib.sha256(payload).hexdigest(),result=result)

def main():
    started=time.perf_counter(); here=pathlib.Path(__file__).parent
    names=['serialized_kernel.py','serialized_examples.py','run_serialized_kernel.py','logic.py']
    data=dict(date=datetime.now(timezone.utc).isoformat(),protocol='gcts-fol-1',
              scope='fixed serialized first-order host checker, registered induction and exact nonrecursive proof blocks; authored certificates, not a TM/Wang compiler or learned proof search',
              source_sha256={n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in names},
              checker_limits=dict(work=2000000,bytes=10000000),positive_cases=[],adversarial_cases=[],propositional_cases=[],repeated_blocks=[],budget_controls=[],problem_binding=[],reuse=[])
    for name,d in [('addition-induction-hierarchy',addition_induction())]+primitive_cases():
        data['positive_cases'].append(record(name,canonical(d),'accepted'))
    parent_path=OUTPUT.parent/'hierarchy-bridge-001.json'; parent_bytes=parent_path.read_bytes(); parent=json.loads(parent_bytes)
    data['reuse'].append(dict(file=parent_path.name,sha256=hashlib.sha256(parent_bytes).hexdigest(),
                             scope='two previously searched logical assemblies; geometric lemmas remain external declared axioms, not re-proved by the serialized checker'))
    declaration=parent['logical_declaration']
    for target in ('five','ten'):
        prior=next(r for r in parent['logical_runs'] if r['target']==target and 'kernel_proof' in r)
        d=request(declaration['functions'],declaration['predicates'],declaration['axioms'],
                  proof=prior['kernel_proof'],target=prior['kernel_proof'][-1]['formula'])
        item=record('reused-coarse-obstruction-'+target,canonical(d),'accepted')
        item['reuse']=dict(parent=parent_path.name,lane=prior['lane'],target=target)
        data['positive_cases'].append(item)
    for name,d in adversarial_cases(): data['adversarial_cases'].append(record(name,canonical(d),'rejected'))
    p=canonical(addition_induction())
    for name,payload in [('duplicate-json-field',p.replace(b'"protocol":',b'"protocol":"gcts-fol-1","protocol":',1)),
                         ('floating-point-arity',p.replace(b'"zero":0',b'"zero":0.0',1)),
                         ('nonfinite-json-number',p.replace(b'"zero":0',b'"zero":NaN',1))]:
        data['adversarial_cases'].append(record(name,payload,'rejected'))
    for i,d in enumerate(propositional_cases()):
        expected='accepted' if logic.tautology(d['target']) else 'rejected'
        data['propositional_cases'].append(record('propositional-'+str(i+1),canonical(d),expected))
    for repeats in (1,8,32,128):
        d=addition_induction(repeats); flat=flatten_blocks(d)
        controls=[('blocks',canonical(d)),('flat',canonical(flat))]; times={name:[] for name,_ in controls}
        for replica in range(5):
            for name,payload in (controls if replica%2==0 else list(reversed(controls))):
                r=check(payload)
                if r['status']!='accepted': raise AssertionError(r)
                times[name].append(r['seconds'])
        for name,payload in controls:
            item=record(name+'-'+str(repeats),payload,'accepted')
            item.update(repeats=repeats,lane=name,seconds=times[name],median_seconds=statistics.median(times[name]),
                        expanded_lines=len(flat['proof']),root_lines=len(d['proof'] if name=='blocks' else flat['proof']))
            data['repeated_blocks'].append(item)
    for name,parameters in [('work-limit',dict(max_work=1)),('byte-limit',dict(max_bytes=1))]:
        item=record(name,p,'unknown_resource_budget',**parameters); item['limits']=parameters; data['budget_controls'].append(item)
    agreed=addition_induction(); pin=problem_hash(agreed)
    proposals=[('same-problem-hierarchy',agreed,'accepted'),('same-problem-flat',flatten_blocks(agreed),'accepted')]
    forged=copy.deepcopy(agreed); forged['theory']['axioms']['invented']=agreed['target']; forged.update(blocks=[],proof=[dict(rule='axiom',formula=agreed['target'],name='invented')])
    proposals.append(('proof-proposer-invented-axiom',forged,'rejected'))
    target=copy.deepcopy(agreed); target.update(blocks=[],proof=target['proof'][:1],target=target['proof'][0]['formula'])
    proposals.append(('proof-proposer-changed-target',target,'rejected'))
    signature=copy.deepcopy(agreed); signature['theory']['functions']['unused-function']=0
    proposals.append(('proof-proposer-changed-signature',signature,'rejected'))
    for name,d,expected in proposals:
        item=record(name,canonical(d),expected,expected_problem_sha256=pin)
        item['expected_problem_sha256']=pin; item['unpinned_status']=check(canonical(d))['status']
        data['problem_binding'].append(item)
    data.update(total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                benchmark='five rotated-order sequential cold checks per certificate; parsing, theory and block validation included; no timing claim for search or independent expansion',
                conformance='no tiling engine modified; proof blocks are syntactic proof proposals with checked formula interfaces, not point tiles or learned GCTS markings; existing Wang scheduler unchanged')
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({k:data[k] for k in ('date','total_seconds','peak_process_memory_bytes')},indent=2))
    for item in data['repeated_blocks']:
        print(item['name'],item['result']['certificate_bytes'],item['result']['rule_checks'],item['median_seconds'])

if __name__=='__main__': main()
