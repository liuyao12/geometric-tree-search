"""Independent whole-region audit, redundant exclusions and exact-input reuse."""
import copy
import gzip
import hashlib
import json
import time
from pathlib import Path

import check_movable_regions as A
from quantified_receptor_cases import registry
from audit_quantified_receptors import bind_compiled, expected_commands
from audit_serialized_kernel import replay
from audit_proof_boundary import expected_constructor, input_bytes, PINNED_PROGRAM, PINNED_MICRO, PINNED_TABLE
from proof_boundary import boundary_words

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'
need, freeze, packed = A.need, A.freeze, A.A.packed


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def source_negatives(tree, chosen=()):
    out = []
    def visit(t, keys):
        if t['kind'] in ('dead', 'empty'):
            return t['kind'] == 'empty'
        success = False
        for child in t['children']:
            k = keys+(freeze(child['key']),)
            ok = visit(child['tree'], k)
            if not ok and len(k) == 2:
                out.append(dict(pair=k, tree=child['tree']))
            success |= ok
        return success
    visit(tree, chosen)
    return out


def binding(spec, result):
    if result['proof']:
        return bind_compiled(spec, result)
    d = freeze(spec)
    need(d['hypotheses'] and d['hypotheses'][-1] == d['target'], 'zero-line input')
    lines, _ = expected_commands([], d['hypotheses'])
    lines += [dict(rule='tautology', formula=('imp', d['target'], d['target'])),
              dict(rule='mp', formula=d['target'], antecedent=len(d['hypotheses'])-1,
                   implication=len(d['hypotheses']))]
    theory = copy.deepcopy(d['theory'])
    if any(A.A.parser(theory).free(a) for a in d['hypotheses']):
        probe = ('imp', ('bot',), ('bot',))
        request = dict(protocol='gcts-fol-1', theory=theory, target=probe,
                       blocks=[dict(name='discovered-sequent', premises=d['hypotheses'],
                                    conclusion=d['target'], proof=lines)],
                       proof=[dict(rule='tautology', formula=probe)])
    else:
        for j, a in enumerate(d['hypotheses']):
            theory['axioms']['premise-'+str(j)] = a
            lines[j] = dict(rule='axiom', formula=a, name='premise-'+str(j))
        request = dict(protocol='gcts-fol-1', theory=theory, target=d['target'], blocks=[], proof=lines)
    need(freeze(result['compiled']['request']) == freeze(request), 'zero-line adapter')
    need(replay(packed(request))['status'] == 'accepted', 'independent copied hypothesis')
    if d['hypotheses']:
        request = result['deduced']['request']
        target = d['target']
        for h in reversed(d['hypotheses']):
            target = ('imp', h, target)
        need(freeze(request['target']) == target and freeze(request['theory']) == d['theory']
             and not request['blocks'], 'zero-line discharged target')
        need(replay(packed(request))['status'] == 'accepted', 'independent zero-line deduction')
    return dict(status='accepted', source_rows=0, adapter_commands=len(lines))


def reuse_exact_inputs(data):
    """Reuse only byte-identical inputs with an already independently audited trace."""
    start = time.perf_counter()
    path = DOC/'quantified-wang-001.json.gz'
    audit_path = DOC/'quantified-wang-audit-001.json.gz'
    native = json.loads(gzip.decompress(path.read_bytes()))
    audit = json.loads(gzip.decompress(audit_path.read_bytes()))
    need(audit['input_sha256'] == digest(path), 'archived operational audit')
    need(audit['source_sha256'] == digest(HERE/'audit_quantified_wang.py'), 'archived auditor pin')
    for n, pin in audit['helper_sources'].items():
        need(digest(HERE/n) == pin, 'archived helper source')
    for n, pin in native['sources'].items():
        need(digest(HERE/n) == pin, 'archived measured source')
    need((native['program_sha256'], native['micro_sha256'], native['literal_table_sha256'])
         == (PINNED_PROGRAM, PINNED_MICRO, PINNED_TABLE), 'unchanged machine')
    need(native['inventory_fingerprint'] == '0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455', 'unchanged palette')
    micro = json.loads(gzip.decompress((DOC/'proof-boundary-microcode-001.json.gz').read_bytes()))
    need(hashlib.sha256(packed(micro)).hexdigest() == PINNED_MICRO, 'micro contents')
    bootstrap = json.loads((DOC/'proof-boundary-001.json').read_bytes())['cases'][0]['initial']
    rows = []
    mutations = []
    for name, archived_name in (('arithmetic', 'arithmetic'), ('hilbert-typing', 'hilbert-typing'),
                                ('ambient-y', 'ambient-y'), ('arithmetic-family', 'arithmetic-learned-6')):
        case = next(c for c in data['cases'] if c['spec']['id'] == name)
        row = next(c for c in native['cases'] if c['name'] == archived_name)
        request = case['runs']['baseline']['compiled']['request']
        need(packed(request) == packed(row['request']), 'entire canonical request equality')
        initial = copy.deepcopy(bootstrap)
        fixed, free = boundary_words(request)
        for band, word in ((micro['boundary']['problem'], fixed), (micro['boundary']['certificate'], free)):
            initial['words'][band] = word+':'
            initial['capacities'][band] = len(word)+3
        need(initial == row['initial'], 'freshly constructed exact bootstrap and input')
        expected_constructor(micro, initial, request)
        current_input = hashlib.sha256(input_bytes(initial)).hexdigest()
        need(current_input == row['input_sha256'], 'whole machine input bytes')
        for item in (row['grammar'], row['events'], row['responses']):
            need(digest(DOC/item['name']) == item['sha256']
                 and (DOC/item['name']).stat().st_size == item['bytes'], 'archived artifact bytes')
        checked = next(c for c in audit['cases'] if c['name'] == archived_name)
        need(checked['checker']['status'] == 'checked_response'
             and checked['checker']['result'] == 'accepted', 'archived independent response')
        for k in ('status', 'micro_steps', 'physical_steps'):
            need(row['literal'][k] == row['builder'][k] == row['expected'][k], 'archived actual execution')
        # Equality is mandatory even when another request is logically equivalent.
        for kind in ('target', 'reference', 'theory', 'input-capacity'):
            bad = copy.deepcopy(request)
            bad_input = copy.deepcopy(initial)
            if kind == 'target':
                bad['target'] = ['bot']
            elif kind == 'theory':
                bad['theory']['schemas'] = ['nat-induction']
            elif kind == 'reference':
                lines = bad['blocks'][0]['proof'] if bad['blocks'] else bad['proof']
                next(l for l in lines if l['rule'] == 'mp')['antecedent'] += 1
            else:
                bad_input['capacities'][0] += 1
            try:
                need(packed(bad) == packed(row['request']), 'cache request identity')
                need(hashlib.sha256(input_bytes(bad_input)).hexdigest() == row['input_sha256'], 'cache input identity')
            except ValueError:
                mutations.append(dict(case=name, kind=kind))
            else:
                raise ValueError('invalid cache reuse')
        rows.append(dict(name=name, archived_name=archived_name, request=request,
                         request_sha256=hashlib.sha256(packed(request)).hexdigest(),
                         input_sha256=current_input, status='reused_exact_input',
                         original_native_seconds=row['seconds'],
                         command_fragments=len(checked['lines']),
                         grammar=row['grammar'], events=row['events'], responses=row['responses']))
    return dict(version='movable-core-cache-001', source_sha256=digest(__file__),
                archived_native_sha256=digest(path), archived_audit_sha256=digest(audit_path),
                inventory_fingerprint=native['inventory_fingerprint'], cases=rows,
                seconds=time.perf_counter()-start, mutations_rejected=mutations,
                scope='Four byte-identical whole inputs reuse previously executed and independently derived native traces. No new native execution, changed-input transport, structural region-cell decomposition or formal universal soundness claim.')


def main():
    began = time.perf_counter()
    path = DOC/'movable-regions-001.json'
    data = json.loads(path.read_bytes())
    for n, pin in data['sources'].items():
        need(digest(HERE/n) == pin, 'frozen measured source '+n)
    base, bindings = registry()
    declarations = []
    for c in base:
        c = copy.deepcopy(c)
        c['bound'] = c.pop('length')
        declarations.append((c, None, ()))
    supplied = copy.deepcopy(declarations[0][0])
    supplied['id'] = 'supplied-target'
    supplied['target'] = supplied['hypotheses'][-1]
    declarations.append((supplied, None, ()))
    donor = data['cases'][0]
    rows = freeze(donor['runs']['baseline']['proof'])
    family = dict(name='universal-mp', proof=rows, premises=freeze(donor['spec']['hypotheses']),
                  conclusion=freeze(donor['spec']['target']), guards=tuple(sorted({
                      r['parameters']['variable'] for r in rows if r['kind'] == 'generalize'})),
                  source='universal-mp')
    need(freeze(data['family']) == family, 'fresh family provenance')
    for name, b in (('arithmetic', 'arithmetic'), ('geometry-family', 'geometry')):
        c = copy.deepcopy(next(c for c, _, _ in declarations if c['id'] == name))
        c['id'] += '-family'
        declarations.append((c, family, (bindings[b],)))
    need(len(data['cases']) == len(declarations) == 11, 'external registry')
    reports, mutations = [], []

    def rejects(name, kind, fn):
        try:
            fn()
        except (ValueError, KeyError, IndexError, TypeError):
            mutations.append(dict(case=name, kind=kind))
        else:
            raise ValueError('mutation accepted '+name+' '+kind)

    for c, (spec, fam, bs) in zip(data['cases'], declarations):
        name = spec['id']
        need(freeze(c['spec']) == freeze(spec) and freeze(c['family']) == freeze(fam)
             and freeze(c['bindings']) == freeze(bs), 'external declaration')
        rules, forms = A.A.inventory(spec, fam, bs)
        need(freeze(c['catalog']['rules']) == freeze(rules)
             and freeze(c['catalog']['formulas']) == freeze(forms), 'complete independent inventory')
        need(c['context_hash'] == A.context_hash(c['catalog'], spec), 'entire exclusion context')
        baseline = c['runs']['baseline']
        report = dict(id=name, baseline_tree=A.tree(rules, spec, baseline), positives=[])
        extracted = source_negatives(baseline['search_tree'])
        need(freeze(extracted) == freeze(baseline['negatives']), 'actual exhausted donor subtrees')
        unique, seen = [], set()
        for item in extracted:
            key = frozenset(item['pair'])
            if key not in seen:
                unique.append(item)
                seen.add(key)
        need(len(unique) == len(c['certified']), 'all selected resolved pair samples')
        pairs = []
        for item, cert in zip(unique, c['certified']):
            need(freeze({k: cert[k] for k in ('pair', 'tree')}) == freeze(item), 'exact failed-pair provenance')
            checked = A.tree(rules, spec, seeds=item['pair'], node=item['tree'])
            need(not checked['outcome'] and checked == cert['check'], 'complete independent pair exhaustion')
            pairs.append(freeze(item['pair']))
        expected = [dict(point=(-2000, n), assignments=[dict(key=a, value=0), dict(key=b, value=1)])
                    for n, (a, b) in enumerate(pairs)]
        need(freeze(c['learned_points']) == freeze(expected), 'actual sparse 0/1 encoder')
        report['certified_pairs'] = len(pairs)
        report['marked_tree'] = A.tree(rules, spec, c['runs']['marked'], pairs)
        for lane, r in c['runs'].items():
            if r['proof'] is None:
                continue
            marking = pairs if lane in ('marked', 'chronological_marked') else ()
            certificate = A.certificate(rules, spec, r, r['tiles'], marking)
            need(certificate == r['point_certificate'], 'recorded certificate')
            erasure = [dict(t, marks=[(p, v) for p, v in t['marks'] if p[0] != -2000]) for t in r['tiles']]
            need(A.certificate(rules, spec, r, erasure) == r['erased_certificate'], 'learned-mark erasure')
            report['positives'].append(dict(lane=lane, certificate=certificate,
                                            cluster=A.cluster(rules, spec, r, marking),
                                            compiler=binding(spec, r)))
            if lane in ('baseline', 'marked'):
                A.frames(rules, spec, r, marking)
            bad = copy.deepcopy(r)
            bad['endpoint'] += 1
            rejects(name, 'endpoint-'+lane, lambda: A.certificate(rules, spec, bad, bad['tiles'], marking))
            bad = copy.deepcopy(r)
            bad['tiles'][0]['marks'][0][1] = 'wrong'
            rejects(name, 'point-'+lane, lambda: A.certificate(rules, spec, bad, bad['tiles'], marking))
            bad = copy.deepcopy(r)
            bad['compiled']['request']['target'] = ['bot']
            rejects(name, 'theorem-'+lane, lambda: binding(spec, bad))
        if pairs:
            bad = copy.deepcopy(c['certified'][0]['tree'])
            if bad.get('children'):
                bad['children'] = bad['children'][:-1]
            else:
                bad['kind'] = 'empty'
                bad['point'] = None
            rejects(name, 'incomplete-negative-tree', lambda: A.tree(rules, spec, seeds=pairs[0], node=bad))
            wrong = dict(spec, bound=spec['bound']+1)
            rejects(name, 'different-exclusion-context', lambda: need(c['context_hash'] == A.context_hash(c['catalog'], wrong), 'context'))
        reports.append(report)
        print(name, 'audited', report['certified_pairs'], flush=True)
    cache = reuse_exact_inputs(data)
    (DOC/'movable-core-cache-001.json').write_bytes(packed(cache)+b'\n')
    out = dict(version='movable-regions-audit-001', input_sha256=digest(path),
               source_sha256=digest(__file__), helper_sources={n: digest(HERE/n) for n in (
                   'check_movable_regions.py', 'check_quantified_receptors.py',
                   'quantified_receptor_cases.py', 'audit_quantified_receptors.py',
                   'audit_serialized_kernel.py', 'audit_proof_boundary.py', 'proof_boundary.py')},
               cases=reports, mutations_rejected=mutations, cache_sha256=digest(DOC/'movable-core-cache-001.json'),
               seconds=time.perf_counter()-began,
               scope='All terminal region trees, actual positive factors, exact sparse mark encodings and complete pair-failure trees checked independently; all mathematical proofs and erased certificates checked. Pair certificates are scoped to the exact bounded positional system, not a complete pair-corona learner.')
    (DOC/'movable-regions-audit-001.json').write_bytes(packed(out)+b'\n')
    print('audit complete', out['seconds'], 'mutations', len(mutations), 'cache', cache['seconds'], flush=True)


if __name__ == '__main__':
    main()
