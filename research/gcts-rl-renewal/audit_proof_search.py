"""Replay saved proof-search evidence against separately declared problems.

The report does not supply its own trusted program, axioms or target: this audit
imports the fixed benchmark declaration from run_proof_search. Replay uses word
semantics, direct TM transitions and point sums/agreement, never graph domains.
"""
import copy,hashlib,json,time
from pathlib import Path
from rewrite_machine import ProofMachine,check_derivation
import proof_search
from run_proof_search import THEORY,CASES,OUTPUT,machine_digest

def main():
    start=time.monotonic();data=json.loads(OUTPUT.read_text());checked=[];rejections=0;placements=0
    for r in data['evaluation']:
        i=r['problem_id'];source,target,capacity,certificate_length,height=CASES[i]
        m=ProofMachine(THEORY,target);problem=data['problems'][i]
        assert problem['machine_sha256']==machine_digest(m)
        if r.get('verified'):
            assert proof_search.replay(m,source,capacity,certificate_length,height,r)
            placements+=r['width']*r['height'];checked.append({'problem_id':i,'lane':r['lane']})
            changed=copy.deepcopy(r);kind=changed['certificate']['tile_types_used'][0]
            kind[-1]=(kind[-1]+1)%len(changed['certificate']['symbols'])
            assert not proof_search.replay(m,source,capacity,certificate_length,height,changed);rejections+=1
            changed=copy.deepcopy(r);changed['certificate']['initial'][0]=-1
            assert not proof_search.replay(m,source,capacity,certificate_length,height,changed);rejections+=1
            other=ProofMachine(THEORY,source if source!=target else ())
            assert not proof_search.replay(other,source,capacity,certificate_length,height,r);rejections+=1
            assert not proof_search.replay(m,('b',)+source,capacity,certificate_length,height,r);rejections+=1
        proposal=r.get('proposal')
        if proposal and proposal['status']=='checked_rewrite_proposal':
            assert check_derivation(THEORY,source,target,proposal['commands'],capacity)[0]
            assert m.run(source,capacity,tuple(proposal['tokens']),10000)['status']=='accept'
    for episode in data['training']['episodes']:
        if episode['status']=='checked_rewrite_proposal':
            assert check_derivation(THEORY,tuple(episode['source']),tuple(episode['target']),episode['commands'],8)[0]
    hashes=data['source_sha256']
    for name in ('rewrite_machine.py','lazy_wang.py','proof_search.py','run_proof_search.py','test_proof_machine.py'):
        assert hashes[name]==hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest(),name
    data['independent_audit']={'checked_rectangles':checked,'point_placements_checked':placements,
                               'tampered_certificates_rejected':rejections,'seconds':time.monotonic()-start,
                               'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               'trusted_boundary':'fixed theory, statements and bounds imported independently; proofs cannot register their own axioms or target',
                               'paths':'independent directed word semantics, operational TM replay and all point sums/agreement; no symbolic domain code'}
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('independent generic proof audit',len(checked),'rectangles',placements,'points',rejections,'tamper rejections',
          round(data['independent_audit']['seconds'],3),'seconds',flush=True)

if __name__=='__main__':main()
