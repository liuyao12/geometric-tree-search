"""Replay source failures, transfer premises, recipient trees and all proofs.

No import of the producer's search, point model, formula logic or transporter.
Independent explicit recipient pair exhaustion additionally checks the theorem
on every measured recipient; this cost is reported separately from warm reuse.
"""
import copy
import hashlib
import json
import time
from pathlib import Path

import check_transported_markings as V
import check_movable_regions as A
from audit_movable_regions import binding, source_negatives

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'
need, freeze, packed = A.need, A.freeze, A.A.packed


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def exhaust(rules, spec, pair):
    totals = dict(nodes=0)
    def visit(chosen):
        totals['nodes'] += 1
        need(totals['nodes'] <= 50000, 'independent recipient pair audit budget')
        ds = A.domains(rules, spec, chosen)
        kind, point, keys = A.decide(ds)
        if kind == 'dead':
            return False
        if kind == 'empty':
            return True
        return any(visit(chosen+(k,)) for k in keys)
    outcome = visit(freeze(pair))
    need(not outcome, 'transported pair must have no recipient completion')
    return dict(status='exhausted_independent_recipient', **totals)


def main():
    began = time.perf_counter()
    path = DOC/'transported-markings-001.json'
    data = json.loads(path.read_bytes())
    source_path = DOC/'movable-regions-001.json'
    donors = json.loads(source_path.read_bytes())
    need(data['donor_sha256'] == digest(source_path), 'exact donor bytes')
    for group in (data['sources'], donors['sources']):
        for n, pin in group.items():
            need(digest(HERE/n) == pin, 'frozen measured source '+n)
    source_checks = {}
    for donor in data['donors']:
        source = next(c for c in donors['cases'] if c['spec']['id'] == donor['id'])
        checks = V.certify_donor(source)
        need(freeze(checks) == freeze(donor['checks']), 'freshly replayed donor failures')
        source_checks[donor['id']] = checks
    reports, mutations = [], []
    def rejects(name, kind, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError, IndexError):
            mutations.append(dict(case=name, kind=kind))
        else:
            raise ValueError('mutation accepted '+name+' '+kind)
    for c in data['cases']:
        spec = c['spec']
        source = next(d for d in donors['cases'] if d['spec']['id'] == c['donor'])
        checked = V.verify(source, spec, c['catalog'], c['transport'], source_checks[c['donor']])
        need(freeze(checked) == freeze(c['transport_check']), 'whole transport projection')
        rules, forms = A.A.inventory(spec)
        replayed = [exhaust(rules, spec, pair) for pair in checked['pairs']]
        row = dict(id=spec['id'], transport=checked, recipient_pairs=replayed, lanes={})
        for lane in ('baseline', 'transported', 'fresh_learning'):
            result = c['runs'][lane]
            marking = () if lane == 'baseline' else checked['pairs'] if lane=='transported' else c['fresh_pairs']
            tree = A.tree(rules, spec, result, marking)
            row['lanes'][lane] = dict(tree=tree)
            if result['proof'] is not None:
                need(A.certificate(rules, spec, result, result['tiles'], marking)==result['point_check'], 'actual positive tile certificate')
                erased = [dict(t, marks=[(p,v) for p,v in t['marks'] if p[0] != -2000]) for t in result['tiles']]
                need(A.certificate(rules, spec, result, erased)==result['erased_check'], 'erased learned layer')
                need(binding(spec, result)==result['compile_binding'], 'whole independent command binding')
        negative = source_negatives(c['runs']['baseline']['search_tree'])
        need(freeze(negative)==freeze(c['runs']['baseline']['negatives']), 'actual recipient learning samples')
        pairs = []
        for item in negative:
            need(not A.tree(rules, spec, seeds=item['pair'], node=item['tree'])['outcome'], 'fresh exhausted label')
            if item['pair'] not in pairs:
                pairs.append(item['pair'])
        need(freeze(pairs)==freeze(c['fresh_pairs']), 'all resolved fresh samples')
        saturation = c['runs']['saturation']
        need(A.A.proof(saturation['proof'],spec['target'],spec['hypotheses'],spec['theory'])==saturation['logical_check'], 'saturation proof')
        need(saturation['fits_region_bound'] is True and len(saturation['proof'])<=spec['bound'], 'matched bound control')
        # Perform the capacity-preserving crop on the actual positive witness.
        if c['positive_crop'] is not None:
            cropped = V.crop(source, spec, c['catalog'], c['transport'], c['runs']['baseline'])
            need(cropped==freeze(c['positive_crop']), 'actual positive restriction map')
        for kind in ('source-context', 'target', 'arity', 'hypothesis', 'grammar', 'closing-bound', 'rule-map', 'scope'):
            bad_spec, bad_cat, bad_plan = copy.deepcopy(spec),copy.deepcopy(c['catalog']),copy.deepcopy(c['transport'])
            if kind=='source-context':bad_plan['source_context']='0'*64
            elif kind=='target':bad_spec['target']=['bot']
            elif kind=='arity':
                signature=bad_spec['theory']['predicates'] or bad_spec['theory']['functions']
                key=next(iter(signature));signature[key]+=1
            elif kind=='hypothesis':bad_spec['hypotheses'].append(bad_spec['target'])
            elif kind=='grammar':bad_cat['rules'][0]['output']=['bot']
            elif kind=='closing-bound':bad_plan['certificates'][0]['maximum_endpoint']+=1
            elif kind=='rule-map':bad_plan['rule_map'][0]=bad_plan['rule_map'][1]
            elif kind=='scope':bad_spec['variables']=list(reversed(bad_spec['variables']))
            bad_plan['target_context']=A.context_hash(bad_cat,bad_spec)
            rejects(spec['id'],kind,lambda:V.verify(source,bad_spec,bad_cat,bad_plan,source_checks[c['donor']]))
        for lane in ('baseline','transported','fresh_learning'):
            result=c['runs'][lane]
            bad=copy.deepcopy(result['tiles']);bad[0]['occupancy'][0][1]=11
            marking=() if lane=='baseline' else checked['pairs'] if lane=='transported' else c['fresh_pairs']
            rejects(spec['id'],lane+'-capacity',lambda:A.certificate(rules,spec,result,bad,marking))
            bad_result=copy.deepcopy(result);bad_result['proof'][-1]['formula']=['bot']
            rejects(spec['id'],lane+'-conclusion',lambda:A.certificate(rules,spec,bad_result,result['tiles'],marking))
        reports.append(row)
        print(spec['id'],'audited',sum(x['nodes'] for x in replayed),'recipient pair states',flush=True)
    control=data['unsafe_control']
    need(control['source_spec']['bound']==2 and control['recipient_spec']['bound']==4,
         'unsafe control boundary declarations')
    control_rules,control_forms=A.A.inventory(control['source_spec'])
    need(not A.tree(control_rules,control['source_spec'],control['old_result'])['outcome'],
         'actual too-small failed pair')
    need(control['rejected_reason']=='closing seed bounds every possible proof end', 'guard rejected unsafe transport')
    new_rules,_=A.A.inventory(control['recipient_spec'])
    control_source=dict(spec=control['source_spec'],catalog=control['catalog'],family=None,bindings=[],
                        context_hash=control['plan']['source_context'],
                        certified=[dict(pair=control['pair'],tree=control['old_result']['search_tree'])])
    target_catalog=dict(control['catalog'],rules=new_rules,formulas=A.A.inventory(control['recipient_spec'])[1])
    checks=V.certify_donor(control_source)
    rejects('unsafe-control','actual-no-closing-seed',lambda:V.verify(control_source,
            control['recipient_spec'],target_catalog,control['plan'],checks))
    need(A.tree(new_rules,control['recipient_spec'],control['new_result'])['outcome'], 'actual larger successful pair')
    need(freeze(control['new_result']['seeds'])==freeze(control['pair']), 'same pair survives larger region')
    need(A.certificate(new_rules,control['recipient_spec'],control['new_result'],control['new_result']['tiles'])==control['new_result']['point_check'], 'counterexample exact proof')
    need(binding(control['recipient_spec'],control['new_result'])==control['new_result']['compile_binding'], 'counterexample primitive binding')
    out=dict(version='transported-markings-audit-001', input_sha256=digest(path),
             donor_sha256=digest(source_path),source_sha256=digest(__file__),
             helpers={n:digest(HERE/n) for n in ('check_transported_markings.py','check_movable_regions.py',
                      'check_quantified_receptors.py','audit_movable_regions.py','audit_quantified_receptors.py')},
             cases=reports,mutations_rejected=mutations,seconds=time.perf_counter()-began,
             unsafe_control=dict(status='checked_counterexample',old_bound=2,new_bound=4,
                                 same_pair=True,old_outcome=False,new_outcome=True),
             scope='Fresh donor exhaustion, checked structural solution map, direct independent recipient pair exhaustion, '
                   'complete recipient search trees and every positive primitive proof binding. No universal kernel formalization.')
    (DOC/'transported-markings-audit-001.json').write_bytes(packed(out)+b'\n')
    print('complete',out['seconds'],'mutations',len(mutations),flush=True)


if __name__=='__main__':main()
