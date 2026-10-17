"""Saved data, exact source copies and HTML packaging; no scientific replay."""
import hashlib
import json
from pathlib import Path
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search')
BASE=ROOT/'.gcts-active';HERE=Path(__file__).resolve().parent
PUB=Path('/private/tmp/gcts-split-controls-publish-20261015')
REL=Path('docs/research/gcts-rl-renewal/receptor-family-components');DEST=PUB/REL
BASELINE='042ae46b841000824809857b78a625c64c9e9ab2'

def read(path):return json.loads(Path(path).read_bytes())
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(ref):
    path=Path(ref['path']);assert path==path.resolve()and pin(path)==ref;return path
def save(path,value):
    with path.open('x')as file:json.dump(value,file,sort_keys=True,indent=2);file.write('\n')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PUB,text=True).strip()==BASELINE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=PUB)
    result_path=HERE/'ROOT-RF-component-readout-v1.json';result=read(result_path)
    assert result['scientific_replay']is result['new_theorem_accepted']is result['logical_proof_accepted']is False
    assert result['engine_promoted']is result['family_library_activated']is result['RL_accepted']is result['GCTS_advantage_claimed']is False
    assert result['current_engine_qualified_case_count']==8 and result['current_engine_required_case_count']==12
    accepted=result['component_controls_accepted']
    assert result['qualified_component_case_count']==(12 if accepted else 0)
    assert not accepted or result['terminal_exit_code']==0 and result['ROOT_resource_accepted']is True
    caller=read(checked(result['source_contract']))
    folders=[
        'receptor-family-bridge-ROOT-20261016',
        'receptor-family-expander-source-20261016','receptor-family-expander-independent-source-20261016',
        'receptor-family-expansion-checker-source-20261016','receptor-family-expansion-checker-independent-source-20261016',
        'receptor-family-six-rule-adapter-source-20261016','receptor-family-six-rule-adapter-independent-source-20261016',
        'receptor-family-bridge-controls-ROOT-source-20261016','receptor-family-bridge-controls-independent-source-20261016',
        'receptor-family-bridge-cold-ROOT-source-20261016','receptor-family-bridge-cold-independent-source-20261016',
        'receptor-family-bridge-saved-independent-source-20261016',
        'receptor-family-components-reader-ROOT-source-20261016']
    skip={'ROOT_package_component_report_v1.py'}
    paths={p for name in folders for p in(BASE/name).rglob('*')if p.is_file()
        and'__pycache__'not in p.parts and p.name not in skip}
    for refs in(caller['sources'],caller['inputs'],caller['original_model_sources'],caller['original_model_inputs']):
        paths.update(checked(ref)for ref in refs.values())
    paths.update([ROOT/'docs/basic-tiling-algorithm.md',
        BASE/'arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT_external_once_v1.py',
        BASE/'arithmetic-Q-full52-integration-source-20261015/Q_native_terminal_meter_v2.py',
        BASE/'unit-row-fresh-projection-ROOT-20261016/ROOT-MR-qualification-disposition-v1.json',
        BASE/'routing-and-receptors-report-ROOT-20261016/ROOT-progress-checkpoint-v1.json',
        Path(__file__).resolve()])
    def add_caps(value):
        if type(value)is dict:
            if set(value)=={'path','sha256','bytes'}:
                path=checked(value)
                if BASE in path.parents or path==ROOT/'docs/basic-tiling-algorithm.md':paths.add(path)
            else:
                for child in value.values():add_caps(child)
        elif type(value)is list:
            for child in value:add_caps(child)
    for ref in caller['component_contracts'].values():add_caps(read(checked(ref)))
    add_caps(caller)
    # Preserve exact reviewed contract ancestry, without recursively copying all historical result trees.
    for name in('ROOT-component-composition-audit-v1.json','ROOT-caller-Source-review-v1.json',
                 'ROOT-saved-reader-Source-review-v2.json'):
        add_caps(read(HERE/name))
    assert not DEST.exists();DEST.mkdir(parents=True)
    evidence=[];public={}
    oldroots=['routing-and-receptors','fresh-projection','decision-context','forced-search-diagnostics','routed-engine']
    for path in sorted(paths):
        rel=Path('measurement/basic-tiling-algorithm.md')if path==ROOT/'docs/basic-tiling-algorithm.md'else path.relative_to(BASE)
        raw=path.read_bytes();href=None
        for oldroot in oldroots:
            prior=PUB/'docs/research/gcts-rl-renewal'/oldroot/'evidence'/rel
            if prior.is_file()and prior.read_bytes()==raw:
                href='../'+oldroot+'/evidence/'+str(rel);break
        reused=href is not None
        if not reused:
            target=DEST/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            assert target.read_bytes()==raw;href='evidence/'+str(rel)
        public[str(path)]=href;evidence.append(dict(href=href,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),reused_exact_published_file=reused))
    save(DEST/'evidence-manifest.json',dict(schema='ROOT-receptor-family-components-evidence-manifest-v1',files=evidence,scientific_replay=False))
    links=[('Root bounded component result and coverage limits',result_path),
        ('Complete current composition Source review',HERE/'ROOT-caller-Source-review-v1.json'),
        ('Independent caller Source review',BASE/'receptor-family-bridge-cold-independent-source-20261016/typed-Source-review-v2.json'),
        ('Generic matcher and primitive expander',Path(caller['sources']['family_expander']['path'])),
        ('Independent expansion checker',Path(caller['sources']['family_checker']['path'])),
        ('Current native six-rule point adapter',Path(caller['sources']['family_adapter']['path'])),
        ('All twelve executable component cases',Path(caller['sources']['component_cases']['path'])),
        ('Preserved adapter negative: physical distinctness',BASE/'receptor-family-six-rule-adapter-independent-source-20261016/source-negative-v2.json'),
        ('Preserved test-helper negative and repaired review',BASE/'receptor-family-bridge-controls-independent-source-20261016/typed-Source-review-v2.json'),
        ('Independent saved-result reader review',BASE/'receptor-family-bridge-saved-independent-source-20261016/typed-Source-review-v2.json'),
        ('Native terminal measurement',HERE/'RF-external-v1/native-terminal.json')]
    data=dict(schema='ROOT-receptor-family-components-public-report-v1',
        component_controls_accepted=accepted,qualified_component_case_count=result['qualified_component_case_count'],
        native_launch_to_postprobe_ns=result['native_launch_to_postprobe_ns'],aggregate_B_bytes=result['aggregate_B_bytes'],
        complete_Date_seconds=result['complete_Date_seconds'],current_engine_qualification=[8,12],
        new_theorem_accepted=False,RL_accepted=False,GCTS_advantage_claimed=False,
        evidence=[dict(label=label,href=public[str(path)],sha256=pin(path)['sha256'],bytes=pin(path)['bytes'])for label,path in links])
    if accepted:
        data['expanded_result_href']=public[result['expanded_result']['path']]
        expanded=read(checked(result['expanded_result']))
        fixture=next(r['result']for r in expanded['family_bridge_component']['component']['records']
            if r['label']=='actual-pending-cluster')
        data['point_fixture']=dict(source_result=result['expanded_result'],source_record='actual-pending-cluster',
            formula_A=fixture['input_ports'][0]['formula'],
            members=[{k:m['tile'][k]for k in('global_t_values','global_m_values')}for m in fixture['members']])
    else:data['raw_error']=result.get('raw_error','Original failure record retained.')
    save(DEST/'report-data.json',data)
    assets=BASE/'receptor-family-components-reader-ROOT-source-20261016'
    for name in('reader.html','reader.css','reader.js'):(DEST/name).write_bytes((assets/name).read_bytes())
    js=(DEST/'reader.js').read_text().replace("fetch('report-data.json'","fetch('report-data.json?v="+pin(DEST/'report-data.json')['sha256'][:12]+"'")
    (DEST/'reader.js').write_text(js)
    html=(DEST/'reader.html').read_text()
    for name in('reader.css','reader.js'):html=html.replace(name+'"',name+'?v='+pin(DEST/name)['sha256'][:12]+'"')
    (DEST/'reader.html').write_text(html)
    index=PUB/'docs/research/gcts-rl-renewal/index.html';baseline=index.read_bytes();old=baseline.decode()
    assert old.count('RESEARCH NOTEBOOK · 194')==1 and'id="receptor-family-components"'not in old
    outcome=('All \\(12\\) component assertions pass in one bounded native run.'if accepted
        else'The first bounded native component run does not qualify the new bridge; its failure is retained.')
    panel='<section class="panel" id="receptor-family-components"><p class="eyebrow">PARALLEL IMPLEMENTATION · REUSABLE LEMMA FAMILIES</p><h2>A lemma family now has an executable interface.</h2><p>Three separately authored components implement joint typed receptor matching, independent primitive expansion checking and admission into the original six-rule marked point model. '+outcome+' Cross review caught unused-input conflicts, nested physical source collapse and failure exception masking. These are human-specified infrastructure fixtures; no new theorem, RL result or speed advantage is claimed. Earlier engine qualification remains \\(8/12\\).</p><p><a href="receptor-family-components/reader.html#parallel">Inspect the parallel contributions, conditional tile interface and full saved result</a>.</p></section>'
    current=old.replace('RESEARCH NOTEBOOK · 194','RESEARCH NOTEBOOK · 195').replace('<section class="panel" id="routing-receptors">',panel+'\n\n<section class="panel" id="routing-receptors">',1)
    assert current.replace(panel+'\n\n','',1).replace('RESEARCH NOTEBOOK · 195','RESEARCH NOTEBOOK · 194')==old
    index.write_text(current)
    protected=pin(ROOT/'docs/research/gcts-rl-renewal/index.html')
    assert protected['sha256']=='d04878220b6c43b16bbc1ff6cd17d24d824e2c3049a2b47600f0e26eec0cd770'
    save(HERE/'ROOT-index-separation-evidence-v1.json',dict(schema='ROOT-protected-versus-publishing-index-separation-v1',
        protected_Root_index=protected,publishing_index=pin(index),publishing_index_baseline=dict(sha256=hashlib.sha256(baseline).hexdigest(),bytes=len(baseline)),
        publishing_baseline_commit=BASELINE,exact_inverse_of_one_panel_and_counter=True,Root_index_edited=False,
        authorization='User AGENTS.md requests task-owned publication to this established GitHub Pages destination.',panel=panel))
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in('href','src')and v)
    parser=Links();parser.feed((DEST/'reader.html').read_text())
    for ref in parser.links:
        value=urlsplit(ref)
        if not value.scheme and value.path:assert(DEST/unquote(value.path)).resolve().is_file(),ref
    for ref in[x['href']for x in evidence]+[x['href']for x in data['evidence']]:assert(DEST/urlsplit(ref).path).resolve().is_file()
    files=[dict(path=str(p.relative_to(PUB)),**{k:v for k,v in pin(p).items()if k!='path'})for p in[index,*sorted(p for p in DEST.rglob('*')if p.is_file())]]
    save(HERE/'publication-task-manifest-v1.json',dict(schema='ROOT-receptor-family-components-publication-manifest-v1',baseline=BASELINE,files=files))
    (HERE/'stage-paths-v1.nul').write_bytes(b''.join(x['path'].encode()+b'\0'for x in files))
    qa=dict(task_files=len(files),task_bytes=sum(x['bytes']for x in files),evidence_files=len(evidence),
        new_raw_files=sum(not x['reused_exact_published_file']for x in evidence),raw_evidence_exact=True,
        links_valid=True,protected_Root_index=protected,scientific_replay=False)
    save(HERE/'ROOT-local-QA-v1.json',qa);print(json.dumps(qa))

if __name__=='__main__':main()
