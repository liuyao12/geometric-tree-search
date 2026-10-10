"""Fresh recipient searches using checked closing-prefix failure transport."""
import hashlib
import json
import resource
import time
from pathlib import Path

import transported_markings as T
import check_transported_markings as V
import movable_proof_regions as M
import check_movable_regions as A
import quantified_receptors as Q
from audit_movable_regions import binding
from serialized_kernel import canonical
from audit_serialized_kernel import replay

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'
DONORS = ('universal-mp', 'ambient-y', 'arithmetic', 'hilbert-typing', 'geometry-family')


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decorate(model, spec, result):
    if result['proof'] is None:
        return
    began = time.perf_counter()
    result['tiles'] = [dict(key=k, occupancy=model.placement(k).occupancy, marks=model.placement(k).marks)
                       for k in result['placements']]
    result['point_check'] = A.certificate(model.catalog['rules'], spec, result, result['tiles'], model.marking)
    erased = [dict(t, marks=tuple((p, v) for p, v in t['marks'] if p[0] != -2000)) for t in result['tiles']]
    result['erased_check'] = A.certificate(model.catalog['rules'], spec, result, erased)
    result['compiled'] = M.compile_region(result['proof'], spec['target'], spec['hypotheses'], spec['theory'])
    if replay(canonical(result['compiled']['request']))['status'] != 'accepted':
        raise ValueError('independent host checker')
    if spec['hypotheses']:
        result['deduced'] = M.compile_region(result['proof'], spec['target'], spec['hypotheses'], spec['theory'], True)
    result['compile_binding'] = binding(spec, result)
    result['positive_assembly_and_check_seconds'] = time.perf_counter()-began


def unsafe_control(donor):
    source = M.freeze(donor)
    source['spec']['bound'] = 2
    catalog = T.inventory(source['spec'])
    h = source['spec']['hypotheses']
    def instance(which):
        return next(i for i,r in enumerate(catalog['rules']) if r['kind']=='forall-elim'
                    and r['inputs'][0]==h[which] and r['parameters']['term']==('var','x'))
    pair = ((0,instance(0),(-2,)),(1,instance(1),(-1,)))
    old = M.Model(catalog,source['spec']['target'],2,h)
    failed = M.search(old,seeds=pair)
    source['catalog'] = catalog
    source['context_hash'] = old.context_hash()
    source['certified'] = [dict(pair=pair,tree=failed['search_tree'])]
    checks = V.certify_donor(source)
    spec,mapping = T.recipient(source,False,2)
    new_catalog = T.inventory(spec)
    plan = T.propose(source,spec,new_catalog,mapping)
    try:
        V.verify(source,spec,new_catalog,plan,checks)
    except ValueError as error:
        reason = str(error)
    else:
        raise ValueError('unsafe no-closing-seed transport accepted')
    model = M.Model(new_catalog,spec['target'],4,spec['hypotheses'])
    succeeded = M.search(model,seeds=pair)
    decorate(model,spec,succeeded)
    return dict(source_spec=source['spec'],catalog=catalog,pair=pair,
                old_result=failed,checks=checks,recipient_spec=spec,
                plan=plan,rejected_reason=reason,new_result=succeeded)


def main():
    began = time.perf_counter()
    source_path = DOC/'movable-regions-001.json'
    data = json.loads(source_path.read_bytes())
    for n, pin in data['sources'].items():
        if digest(HERE/n) != pin:
            raise ValueError('frozen donor source '+n)
    names = ('transported_markings.py', 'check_transported_markings.py', 'run_transported_markings.py',
             'movable_proof_regions.py', 'check_movable_regions.py', 'quantified_receptors.py',
             'check_quantified_receptors.py', 'audit_movable_regions.py', 'serialized_kernel.py',
             'audit_serialized_kernel.py', 'logic.py', 'turtle.py')
    pins = {n: digest(HERE/n) for n in names}
    donors, cases = [], []
    for name in DONORS:
        donor = next(c for c in data['cases'] if c['spec']['id'] == name)
        start = time.perf_counter()
        checks = V.certify_donor(donor)
        certification = time.perf_counter()-start
        donors.append(dict(id=name, context=donor['context_hash'], checks=checks,
                           cache_build_seconds=certification,
                           original_learning_seconds=donor['training_seconds'],
                           source_bound=donor['spec']['bound']))
        for changed, extra in ((False, 1), (True, 4)):
            spec, mapping = T.recipient(donor, changed, extra)
            start = time.perf_counter()
            catalog = T.inventory(spec)
            grammar_seconds = time.perf_counter()-start
            start = time.perf_counter()
            proposal = T.propose(donor, spec, catalog, mapping)
            construction = time.perf_counter()-start
            start = time.perf_counter()
            accepted = V.verify(donor, spec, catalog, proposal, checks)
            verification = time.perf_counter()-start
            runs = {}
            for lane, pairs in (('baseline', ()), ('transported', accepted['pairs'])):
                start = time.perf_counter()
                model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'], pairs)
                binding_seconds = time.perf_counter()-start
                result = M.search(model, node_limit=40000, seconds=15, collect_pairs=lane=='baseline')
                result['binding_seconds'] = binding_seconds
                decorate(model, spec, result)
                runs[lane] = result
            model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'])
            saturation = Q.saturation(model)
            if saturation['proof'] is not None:
                saturation['logical_check'] = A.A.proof(saturation['proof'], spec['target'], spec['hypotheses'], spec['theory'])
                saturation['fits_region_bound'] = len(saturation['proof']) <= spec['bound']
            start = time.perf_counter()
            fresh = []
            for item in runs['baseline']['negatives']:
                checked = A.tree(catalog['rules'], spec, seeds=item['pair'], node=item['tree'])
                if checked['outcome']:
                    raise ValueError('negative training label')
                if item['pair'] not in fresh:
                    fresh.append(item['pair'])
            fresh_certification = time.perf_counter()-start
            start = time.perf_counter()
            fresh_model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'], fresh)
            fresh_encoding = time.perf_counter()-start
            fresh_run = M.search(fresh_model, node_limit=40000, seconds=15)
            decorate(fresh_model, spec, fresh_run)
            runs['fresh_learning'] = fresh_run
            runs['saturation'] = saturation
            positive_map = None
            if runs['baseline']['proof'] is not None and runs['baseline']['endpoint'] <= donor['spec']['bound']:
                positive_map = T.M.freeze(V.crop(donor, spec, catalog, proposal, runs['baseline']))
            row = dict(spec=spec, donor=name, catalog=catalog, transport=proposal,
                       transport_check=accepted, grammar_seconds=grammar_seconds,
                       construction_seconds=construction, verification_seconds=verification,
                       fresh_pairs=fresh, fresh_certification_seconds=fresh_certification,
                       fresh_encoding_seconds=fresh_encoding,
                       fresh_training_seconds=runs['baseline']['binding_seconds']+runs['baseline']['seconds']+fresh_certification+fresh_encoding,
                       positive_crop=positive_map, runs=runs)
            cases.append(row)
            print(spec['id'], {k:(r['status'],r.get('endpoint'),r.get('metrics',{}).get('nodes')) for k,r in runs.items()},
                  'transported',len(accepted['pairs']),'fresh',len(fresh),flush=True)
    control = unsafe_control(data['cases'][0])
    out = dict(version='transported-markings-001', donor_sha256=digest(source_path), sources=pins,
               donors=donors, cases=cases, seconds=time.perf_counter()-began,
               unsafe_control=control,
               peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               scope='Checked failure transport through a closing prefix, enlarged bounds and signature bijections. '
                     'Actual sparse values feed the unchanged full point graph. No RL or new native Wang execution.')
    if any(digest(HERE/n) != pin for n, pin in pins.items()):
        raise ValueError('measured source changed')
    (DOC/'transported-markings-001.json').write_bytes(canonical(out)+b'\n')
    print('complete',out['seconds'],flush=True)


if __name__ == '__main__':
    main()
