"""Prospective complete contextual grammar and proof-backed receptor motifs.

No target proof word, chosen induction variable, learner or native-admission
token is supplied. The old generic grammar is reused without modification.
"""
import copy
from certificate_boundary_search import canonical
from left_successor_catalog import core as generic_core, prospective_points
from left_successor_compact import compact

def core(spec, inventory):
    c=generic_core(spec, inventory)
    names={d['name']:'commutativityReceptor'+d['name'][len('leftSuccessorReceptor'):] for d in c['definitions'] if d['name'].startswith('leftSuccessorReceptor')}
    for d in c['definitions']:d['name']=names.get(d['name'],d['name'])
    for r in c['rules']:
        if r['command']['rule']=='block':r['command']['name']=names.get(r['command']['name'],r['command']['name'])
    c['rules'].sort(key=canonical);c['definitions'].sort(key=lambda d:d['name'])
    c['primitive_storage']='Not enumerated here. Arbitrary primitive-scheme combinations are outside this declared contextual grammar. Native primitive expansions of every actual local interface are preserved.'
    return c

def compact_core(c):
    d=copy.deepcopy(c);d['definitions']=[compact(x) for x in c['definitions']]
    d['preparation_transform']='Earlier exact-formula DAG sharing and dependency slicing inside each fixed local-premise context. Same interface; separate native admission required.'
    return d

def motif_families(c):
    """All eligible two-row lemma-root/rewrite receptors, without a proof path.

    Each root and rewrite row expands to four existing point placements. The
    other rewrite input is an external receptor, not an inferred hypothesis.
    """
    roots={canonical(r['conclusion']):i for i,r in enumerate(c['rules']) if r['description']['operation']=='transferred-searched-theorem'}
    families=[]
    for i,r in enumerate(c['rules']):
        if len(r['premises'])!=2 or r['description']['operation'] not in ('rewrite','conditional-rewrite'):continue
        root=roots.get(canonical(r['premises'][1]))
        if root is None:continue
        families.append(dict(root_rule=root,rewrite_rule=i,lemma_premise=1,external_premise=0,scope='Proof-backed deterministic cluster family, not RL or a learned exclusion.'))
    return families

def motif_count(c, length):
    # At rewrite row j, the lemma root k and other source s can independently
    # occupy every strict-prior row. s=k is internally inconsistent (the two
    # distinct formula markings overlap); retain this raw count as a cost.
    families=motif_families(c);raw=0;consistent=0
    for j in range(length):
        for f in families:
            if j+1==length and c['rules'][f['rewrite_rule']]['conclusion']!=c['spec']['target']:continue
            raw+=j*j;consistent+=j*(j-1)
    return dict(length=length,families=len(families),raw_parameter_instances=raw,internally_consistent_instances=consistent,base_placements_per_cluster=8,materialized=False,lazy_generator='Every family, rewrite row j, lemma root k<j, external source s<j; validate actual t/m union. No top-k list substitutes for base degree counts.')
