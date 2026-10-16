"""Saved metadata/raw bytes and HTML only; no scientific payload evaluation."""
import hashlib,json,subprocess
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search');BASE=ROOT/'.gcts-active'
HERE=Path(__file__).resolve().parent;ACT=BASE/'unit-row-routing-phase-diagnostic-ROOT-20261016'
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015');REL=Path('docs/research/gcts-rl-renewal/routing-and-receptors');DEST=PUB/REL
BASELINE='7c8f33d61e90d38ea9670c4b8e48216de73ce65c'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(r):
    p=Path(r['path']);assert p==p.resolve()and pin(p)==r;return p
def save(p,v):
    with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PUB,text=True).strip()==BASELINE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=PUB)
    rp=ACT/'ROOT-RP-diagnostic-readout-v1.json';r=read(rp)
    assert pin(rp)['sha256']=='bb99226dfd7215ea86c4b3ca54d0cd145b09e7861617030a116cbb7396ee3d3b'
    assert r['terminal_exit_code']==0 and r['complete_marker_line_count']==16 and r['qualified_case_count']==0 and r['reported_case_count']is None
    for key in('qualification_accepted','engine_promoted','scientific_payload_decoded','logical_proof_accepted','RL_accepted','GCTS_advantage_claimed','scientific_replay'):assert r[key]is False
    f=BASE/'receptor-lemma-family-design-source-20261016';hand=read(f/'handoff-v1.json');contract=read(checked(hand['contract']));audit=read(checked(hand['audit']))
    for ref in audit['sources'].values():checked(ref)
    peerpath=BASE/'receptor-lemma-family-design-independent-source-20261016/typed-Source-review-v1.json';peer=read(peerpath)
    assert peer['reviewer_identity']=='/root/hilbert_advice_controls'
    # The conceptual peer's complete exact capsule and conditions are retained, not interpreted as activation.
    assert pin(peerpath)['sha256']=='d3616610a83e74c63eab7a3986e60f060fce1c3986c98013382952679b10bcf0'
    rootreview=HERE/'ROOT-receptor-design-review-v1.json'
    save(rootreview,dict(schema='ROOT-receptor-family-design-review-v1',author_identity='/root/arithmetic_induction',reviewer_identity='/root',contract=hand['contract'],audit=hand['audit'],peer=pin(peerpath),source_only=True,scientific_calls=0,scientific_acceptance=False,whole_contract_and_visual_read=True,source_pins19_authenticated=True,design_only_pass=True,concrete_design_blockers=[],implementation_complete=False,library_activated=False,new_theorem_accepted=False,limitations=['Structural descriptor schema is not an implemented semantic validator.','Legacy block envelope differs from current six-rule primitive rows; full expansion and actual host checks are required.','All-port capture-safe matching, complete union, original fallback/global order and exact rollback remain implementation gates.','Human two-MP illustration is infrastructure design only; automatically extracted families and independently checked new search proofs are later experiments.']))
    folders=('unit-row-routing-phase-diagnostic-ROOT-20261016','unit-row-routing-phase-diagnostic-cold-source-20261016','unit-row-routing-phase-diagnostic-cold-independent-source-20261016','unit-row-routing-phase-diagnostic-saved-ROOT-source-20261016','unit-row-routing-phase-diagnostic-saved-independent-source-20261016','receptor-lemma-family-design-source-20261016','receptor-lemma-family-design-independent-source-20261016','routing-and-receptors-reader-ROOT-source-20261016')
    paths={p for name in folders for p in(BASE/name).rglob('*')if p.is_file()and'__pycache__'not in p.parts}
    caller=read(BASE/'unit-row-routing-phase-diagnostic-cold-source-20261016/Source-contract-v1.json')
    for group in(caller['sources'],caller['inputs'],caller['original_model_sources'],caller['original_model_inputs'],audit['sources']):paths.update(checked(x)for x in group.values())
    for key in('parent_source','parent_source_contract','component_source_contract','parent_checkpoint'):paths.add(checked(caller[key]))
    paths.update(checked(x)for x in caller['component_reviews'].values())
    paths.update((rootreview,Path(__file__).resolve(),BASE/'unit-row-fresh-projection-ROOT-20261016/ROOT-MR-qualification-disposition-v1.json',BASE/'arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py',BASE/'arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py'))
    assert not DEST.exists();DEST.mkdir(parents=True);evidence=[];public={}
    oldroots=('fresh-projection','decision-context','forced-search-diagnostics','routed-engine')
    for p in sorted(paths):
        rel=Path('measurement/basic-tiling-algorithm.md')if p==ROOT/'docs/basic-tiling-algorithm.md'else p.relative_to(BASE)if BASE in p.parents else Path('project-source')/p.relative_to(ROOT)
        raw=p.read_bytes();href=None
        for oldroot in oldroots:
            prior=PUB/'docs/research/gcts-rl-renewal'/oldroot/'evidence'/rel
            if prior.is_file()and prior.read_bytes()==raw:href='../'+oldroot+'/evidence/'+str(rel);break
        reused=href is not None
        if not reused:
            target=DEST/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);assert target.read_bytes()==raw;href='evidence/'+str(rel)
        public[str(p)]=href;evidence.append(dict(href=href,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),reused_exact_published_file=reused))
    save(DEST/'evidence-manifest.json',dict(schema='ROOT-routing-and-receptors-evidence-manifest-v1',files=evidence,scientific_replay=False))
    familydest=DEST/'families';familydest.mkdir()
    for name in('design-reader.html','receptor-family-contract-v1.json','audit-findings-v1.json','human-two-mp-family-v1.json','handoff-v1.json'):(familydest/name).write_bytes((f/name).read_bytes())
    links=[('Bounded routing diagnostic: saved readout',rp),('Root assessment and next experiment',ACT/'ROOT-next-step-assessment-v1.json'),('Current unchanged control qualification',BASE/'unit-row-fresh-projection-ROOT-20261016/ROOT-MR-qualification-disposition-v1.json'),('Typed receptor-family contract',f/'receptor-family-contract-v1.json'),('Source audit: implemented paths and missing integration',f/'audit-findings-v1.json'),('Independent conceptual family review',peerpath),('Root family design review',rootreview),('Independent routing caller review',BASE/'unit-row-routing-phase-diagnostic-cold-independent-source-20261016/typed-Source-review-v1.json'),('Independent saved-reader review and preserved negative',BASE/'unit-row-routing-phase-diagnostic-saved-independent-source-20261016/typed-Source-review-v2.json')]
    data=dict(schema='ROOT-routing-and-receptors-public-report-v1',native_launch_to_postprobe_ns=r['native_launch_to_postprobe_ns'],native_worker_lifetime_ns=r['native_worker_lifetime_ns'],aggregate_B_bytes=r['aggregate_B_bytes'],complete_marker_line_count=16,intervals=r['inclusive_group_intervals'],current_controls_qualified=8,total_controls_required=12,diagnostic_qualified_case_count=0,scientific_payload_decoded=False,qualification_accepted=False,new_theorem_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,evidence=[dict(label=label,href=public[str(p)],sha256=pin(p)['sha256'],bytes=pin(p)['bytes'])for label,p in links])
    save(DEST/'report-data.json',data)
    assets=BASE/'routing-and-receptors-reader-ROOT-source-20261016'
    for name in('reader.html','reader.css','reader.js'):(DEST/name).write_bytes((assets/name).read_bytes())
    (DEST/'reader.js').write_text((DEST/'reader.js').read_text().replace("fetch('report-data.json'","fetch('report-data.json?v="+pin(DEST/'report-data.json')['sha256'][:12]+"'"))
    html=(DEST/'reader.html').read_text()
    for name in('reader.css','reader.js'):html=html.replace(name+'"',name+'?v='+pin(DEST/name)['sha256'][:12]+'"')
    (DEST/'reader.html').write_text(html)
    index=PUB/'docs/research/gcts-rl-renewal/index.html';baseline=index.read_bytes();text=baseline.decode()
    assert text.count('RESEARCH NOTEBOOK · 193')==1 and'id="routing-receptors"'not in text
    panel='<section class="panel" id="routing-receptors"><p class="eyebrow">PARALLEL RESEARCH · REUSABLE LEMMA FAMILIES</p><h2>Make the inventory compatible with the primitive engine.</h2><p>Parallel Source work identifies the missing bridge: older lemma-block commands cannot be imported as current six-rule authority. A reviewed receptor-family design requires joint input matching, scope checks and complete primitive expansion, then proposes preferences under the unchanged scheduler and fallback. One bounded routing diagnostic reaches all fixed observation writes in \\(2.623\\) seconds; the earlier delay does not recur and its cause remains unresolved. This observation adds no qualification: current controls remain \\(8\\) of \\(12\\). No new theorem, RL result or speed advantage is claimed.</p><p><a href="routing-and-receptors/reader.html#parallel">Inspect the parallel responsibilities, family design and exact diagnostic evidence</a>.</p></section>'
    current=text.replace('RESEARCH NOTEBOOK · 193','RESEARCH NOTEBOOK · 194').replace('<section class="panel" id="fresh-projection">',panel+'\n\n<section class="panel" id="fresh-projection">',1)
    index.write_text(current)
    assert current.replace(panel+'\n\n','',1).replace('RESEARCH NOTEBOOK · 194','RESEARCH NOTEBOOK · 193')==text
    protected=pin(ROOT/'docs/research/gcts-rl-renewal/index.html');assert protected['sha256']=='d04878220b6c43b16bbc1ff6cd17d24d824e2c3049a2b47600f0e26eec0cd770'
    save(HERE/'ROOT-index-separation-evidence-v1.json',dict(schema='ROOT-protected-versus-publishing-index-separation-v1',protected_Root_index=protected,publishing_index=pin(index),publishing_index_baseline=dict(sha256=hashlib.sha256(baseline).hexdigest(),bytes=len(baseline)),publishing_baseline_commit=BASELINE,exact_inverse_of_one_panel_and_counter=True,Root_index_edited=False,authorization='User AGENTS.md requests task-owned publication to this established GitHub Pages destination.',panel=panel))
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in('href','src')and v)
    for page in(DEST/'reader.html',familydest/'design-reader.html'):
        parser=Links();parser.feed(page.read_text())
        for ref in parser.links:
            u=urlsplit(ref)
            if not u.scheme and u.path:assert(page.parent/unquote(u.path)).resolve().is_file(),ref
    for ref in[x['href']for x in evidence]+[x['href']for x in data['evidence']]:assert(DEST/urlsplit(ref).path).resolve().is_file()
    files=[dict(path=str(p.relative_to(PUB)),**{k:v for k,v in pin(p).items()if k!='path'})for p in[index,*sorted(p for p in DEST.rglob('*')if p.is_file())]]
    save(HERE/'publication-task-manifest-v1.json',dict(schema='ROOT-routing-and-receptors-publication-manifest-v1',baseline=BASELINE,files=files))
    (HERE/'stage-paths-v1.nul').write_bytes(b''.join(x['path'].encode()+b'\0'for x in files))
    qa=dict(task_files=len(files),task_bytes=sum(x['bytes']for x in files),evidence_files=len(evidence),new_raw_files=sum(not x['reused_exact_published_file']for x in evidence),raw_evidence_exact=True,links_valid=True,protected_Root_index=protected,scientific_replay=False)
    save(HERE/'ROOT-local-QA-v1.json',qa);print(json.dumps(qa))
if __name__=='__main__':main()
