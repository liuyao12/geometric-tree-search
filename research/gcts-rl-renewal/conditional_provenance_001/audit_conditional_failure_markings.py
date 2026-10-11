"""Independent literal reconstruction of conditional teachers and extra ports.

Does not import the conditional producer, learner, teacher or point constructor.
Reuses the independent full-domain/tree auditor of Notebook 63 and its checked
prefix-vocabulary adaptation. No producer exclusion decision is trusted.
"""
import collections, copy, json
from audit_semantic_inventory import rebuild, need, same, pin, initial, legal, advance, encode
from audit_prefix_failure_markings import (fixed_vocabulary_prefix, bound_context,
    semantic, decorations, extended_tree)


def plain(record):
    return {k:v for k,v in semantic(record).items() if k not in ('conditional_overlay','combined_overlay')}


def teacher(parent, probe):
    left,right = probe['slots']
    a,b = probe['formulas']
    spec = probe['spec']
    need(0<=left<right<parent.spec['length'] and spec['length']==right+1
         and spec['target']==b and spec['theory']==parent.spec['theory'],
         'two-row original prefix context')
    record = fixed_vocabulary_prefix(spec,parent.compiled,parent.inventory)
    need(same(plain(record),plain(probe['model'])), 'independently rebuilt undecorated pair teacher')
    state = initial(spec,record)
    for p,v in encode(left,'formula',a):
        need(p not in state['marks'] or state['marks'][p]==v,'distinct row-word boundary')
        state['marks'][p]=v
    need(same(sorted(state['marks'].items()),probe['model']['initial_marks']),
         'exactly two full fixed words including terminators')
    full = rebuild(parent.spec,parent.compiled,parent.inventory)
    required = {decorations(c):tuple(c['key']) for c in full['placements']
        if c['key'][0]<=right and not(c['key'][0]==right and c['key'][1]<2
                                      and c['command']['formula']!=b)}
    pairs=[]
    for c in record['placements']:
        word=decorations(c)
        need(word in required,'original candidate lift for every teacher placement')
        pairs.append((tuple(c['key']),required.pop(word)))
        need(all(p[0]<=4*c['key'][0]+2 for p,v in c['marks']),
             'candidate requirements never read a later row')
    need(not required and same(pairs,probe['lift']['pairs']) and pin(pairs)==probe['lift']['sha256'],
         'complete decorated prefix bijection')
    need(record['roots']==[p for p in full['roots'] if p[0]<4*(right+1)],
         'all original roots in prefix')
    checked=extended_tree(spec,record,probe['search'],parent.inventory,None,
                          sorted(state['marks'].items()))
    labels={'finite_marked_proof_region':'positive','exhausted_finite_marked_region':'negative',
            'unknown_search_budget':'unknown'}
    need(probe['label']==labels[probe['search']['status']],'unknown is not a negative pair')
    return dict(status='passed',label=probe['label'],lift_sha256=pin(pairs),**checked)


def check_learning(parent,learning):
    full=rebuild(parent.spec,parent.compiled,parent.inventory)
    need(same(plain(full),plain(parent.record())),'original complete parent independently rebuilt')
    need(same(bound_context(parent),learning['context']) and pin(bound_context(parent))==learning['context_sha256'],
         'pair grammar, theory, vocabulary and lemma context')
    row_pairs=learning['row_pairs']
    need(row_pairs==sorted(row_pairs) and len(set(map(tuple,row_pairs)))==len(row_pairs)
         and all(0<=a<b<parent.spec['length'] for a,b in row_pairs),'declared finite row-pair set')
    formulas={json.dumps(f,sort_keys=True,separators=(',',':'),ensure_ascii=False):f
              for f in parent.compiled['basis']}
    groups=collections.defaultdict(lambda:collections.defaultdict(list))
    for c in full['placements']:
        if c['key'][1]!=0:continue
        word=json.dumps(c['command']['formula'],sort_keys=True,separators=(',',':'),ensure_ascii=False)
        groups[c['key'][0]][word].append(c['key'])
    expected=[]
    for left,right in row_pairs:
        for aw,aks in sorted(groups[left].items()):
            for bw,bks in sorted(groups[right].items()):
                expected.append(dict(id=len(expected),slots=[left,right],
                    formulas=[formulas[aw],formulas[bw]],command_keys=[aks,bks]))
    need(same(expected,learning['catalog']) and len(expected)==len(learning['probes']),
         'complete Cartesian catalog, no sampled pair omissions')
    counts=collections.Counter();nodes=0
    for row,probe in zip(expected,learning['probes']):
        for key,value in row.items():need(same(probe[key],value),'complete pair row '+key)
        need(all(probe['search']['limits'][k]==v for k,v in learning['limits'].items()),
             'predeclared teacher limits')
        checked=teacher(parent,probe)
        counts[checked['label']]+=1;nodes+=checked['nodes']
        if 'independent_check' in probe:need(probe['independent_check']==checked,'actual immediate audit')
    need(dict(counts)==learning['counts'],'all conditional results retained')
    return dict(version='conditional-failure-certificate-001',status='passed',
        learning_sha256=pin(learning),context_sha256=pin(bound_context(parent)),
        pairs=len(expected),counts=dict(counts),nodes=nodes,
        scope='Independently reconstructed complete teachers, two-word boundaries, causal restriction and every visited graph. Negative pairs prove only redundant conjunction constraints in this finite grammar. Not an infinite or unrestricted logical certificate.')


def check_overlay(parent,learning,certificate,record):
    need(certificate['status']=='passed' and certificate['learning_sha256']==pin(learning)
         and certificate['context_sha256']==pin(bound_context(parent)), 'pre-activation conditional certificate')
    full=rebuild(parent.spec,parent.compiled,parent.inventory)
    original={tuple(c['key']):c for c in full['placements']}
    values={tuple(c['key']):dict((tuple(p),v) for p,v in c['marks']) for c in full['placements']}
    expected={k:dict(v) for k,v in values.items()};exterior={};failures=[]
    for probe in learning['probes']:
        if probe['label']!='negative':continue
        need(probe['search']['status']=='exhausted_finite_marked_region','exhaustion before conjunction exclusion')
        words=[encode(j,'formula',f) for j,f in zip(probe['slots'],probe['formulas'])]
        groups=[{k for k,marks in values.items() if all(marks.get(tuple(p))==v for p,v in w)} for w in words]
        both=groups[0]&groups[1]
        pair=(3,200000+2*probe['id']);single=(3,200001+2*probe['id'])
        if both:exterior[single]=0
        assigned=[]
        for k in sorted(groups[0]|groups[1]):
            point,value=(single,1) if k in both else (pair,0 if k in groups[0] else 1)
            need(point not in expected[k] and all(tuple(p)!=point for p,v in original[k]['occupancy']),
                 'fresh private marking-only point')
            expected[k][point]=value;assigned.append(dict(key=k,point=point,value=value))
        failures.append(dict(probe=probe['id'],slots=probe['slots'],formulas=probe['formulas'],
            pair_point=pair,single_point=single,left_keys=sorted(groups[0]-both),
            right_keys=sorted(groups[1]-both),joint_keys=sorted(both),assignments=assigned))
    projected=dict(full,placements=[dict(c,marks=sorted(expected[tuple(c['key'])].items())) for c in full['placements']])
    need(same(plain(projected),plain(record)),'exact conditional values and unchanged t/candidate universe')
    overlay=record['conditional_overlay']
    need(overlay['certificate']==certificate and overlay['learning_sha256']==pin(learning)
         and overlay['context_sha256']==pin(bound_context(parent))
         and same(overlay['exterior'],sorted(exterior.items())) and same(overlay['failures'],failures),
         'complete conditional all-writer support and provenance')
    root=initial(parent.spec,full);root['marks'].update(exterior)
    need(same(record['initial_marks'],sorted(root['marks'].items())), 'all fixed single-writer exclusions')
    lookup={tuple(c['key']):c for c in record['placements']};positives=0
    for probe in learning['probes']:
        if probe['label']!='positive':continue
        lift={tuple(a):tuple(b) for a,b in probe['lift']['pairs']}
        s=initial(probe['spec'],probe['model'])
        s['marks']={tuple(p):v for p,v in probe['model']['initial_marks']}
        s['marks'].update(exterior)
        for k in probe['search']['placements']:
            c=lookup[lift[tuple(k)]];need(legal(c,s),'each positive pair prefix survives all constraints')
            s=advance(c,s)
        need(set(s['totals'])==set(s['roots']) and all(v==12 for v in s['totals'].values()),'positive whole prefix')
        positives+=1
    return dict(status='passed',negative_pairs=len(failures),single_exclusion_ports=len(exterior),
        positive_prefixes_rechecked=positives,
        affected_candidates=len({tuple(a['key']) for f in failures for a in f['assignments']}),
        assignments=sum(len(f['assignments']) for f in failures),
        joint_writers=sum(len(f['joint_keys']) for f in failures),
        scope='Literal extra point values independently rebuilt; positive prefixes preserved. A shared candidate writing both forbidden words is rejected by a separate fixed point, without internally inconsistent tile data.')


def check_combined(parent,unary,pair,record):
    full=rebuild(parent.spec,parent.compiled,parent.inventory)
    originals={tuple(c['key']):c for c in full['placements']}
    expected={k:dict((tuple(p),v) for p,v in c['marks']) for k,c in originals.items()}
    root=initial(parent.spec,full);fixed={}
    for layer in (unary,pair):
        need(set(tuple(c['key']) for c in layer['placements'])==set(originals),'combined full identities')
        for c in layer['placements']:
            k=tuple(c['key']);need(same(c['occupancy'],originals[k]['occupancy']),'combined same t-data')
            for p,v in c['marks']:
                p=tuple(p);need(p not in expected[k] or expected[k][p]==v,'compatible combined marking values')
                expected[k][p]=v
        for p,v in layer['initial_marks']:
            p=tuple(p);need(p not in root['marks'] or root['marks'][p]==v,'compatible combined fixed values')
            root['marks'][p]=v
            if p[0]%4==3:fixed[p]=v
    projected=dict(full,placements=[dict(c,marks=sorted(expected[tuple(c['key'])].items())) for c in full['placements']])
    need(same(plain(projected),plain(record)),'exact combined literal point data')
    need(same(record['initial_marks'],sorted(root['marks'].items())),'combined root values')
    overlay=record['combined_overlay']
    need(overlay['unary_certificate']==unary['failure_overlay']['certificate']
         and overlay['pair_certificate']==pair['conditional_overlay']['certificate']
         and overlay['unary_record_sha256']==pin(unary) and overlay['pair_record_sha256']==pin(pair)
         and same(overlay['exterior'],sorted(fixed.items())),'combined checked provenance')
    return dict(status='passed',placements=len(originals),fixed_ports=len(fixed),
                scope='Exact union of both separately audited point layers, with no t-data or candidate change.')
