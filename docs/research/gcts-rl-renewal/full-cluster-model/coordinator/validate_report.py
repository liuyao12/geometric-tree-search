"""Check report projection bytes and links, without running search or auditors."""
import hashlib
import gzip
import json
import os
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load

HERE=Path(__file__).resolve().parent


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=[]

    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])


def main():
    manifest=load(HERE/'task-files.json');cache={}
    for e in manifest:assert pin(ROOT/e['path'])=={k:e[k] for k in ('sha256','bytes')},e['path']
    bindings=load(DEST/'source-input-bindings.json')
    for e in bindings:
        base=ROOT if e['published_path'].startswith(PREFIX) else PUB
        p=base/e['published_path']
        if e.get('archive_member'):
            if str(p) not in cache:cache[str(p)]=zipfile.ZipFile(p)
            raw=cache[str(p)].read(e['archive_member'])
            observed=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        else:observed=pin(p)
        assert observed=={k:e[k] for k in ('sha256','bytes')},e['path']
    for z in cache.values():z.close()
    origins=load(DEST/'origins.json')
    for e in origins:assert pin(ROOT/e['path'])==pin(ROOT/e['origin'])=={k:e[k] for k in ('sha256','bytes')}
    source=load(ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011/full-language-outcome-v3.json')
    visual=load(DEST/'visual-data.json')
    assert visual['descriptors']==source['descriptors']
    assert len(visual['states'])==len(source['states'])==11
    with gzip.open(ROOT/visual['source_model']['path'],'rt') as stream:model=json.load(stream)
    assert visual['formulas']==model['formula_codes']
    assert visual['recipes']==[{k:r[k] for k in ('id','primitive_witness','ordered_premise_formulas')} for r in model['recipes']]
    for v,s in zip(visual['states'],source['states']):
        assert v['label']==s['label'] and v['state']['graph']['marks']==s['state']['graph']['marks']
        assert v['state']['graph']['order']==s['state']['graph']['order'] and v['state']['hint_states']==s['state']['hint_states']
        assert len(v['state']['graph']['domains'])==len(s['state']['graph']['domains'])
        for a,b in zip(v['state']['graph']['domains'],s['state']['graph']['domains']):
            assert a=={k:value for k,value in b.items() if k!='factors'}
    raw=(DEST/'reader.html').read_text();parser=Links();parser.feed(raw)
    assert len(parser.ids)==len(set(parser.ids))
    checked=[]
    for href in parser.links:
        if href.startswith(('https:','http:')):continue
        name=href.split('#')[0].split('?')[0]
        p=Path(os.path.normpath(str(DEST/name))) if name else DEST/'reader.html'
        relative=str(p.relative_to(ROOT))
        if not name or name.endswith('/'):
            if name:p=p/'index.html';relative=str(p.relative_to(ROOT))
        task_paths={e['path'] for e in manifest}
        p=ROOT/relative if relative in task_paths or relative.startswith(PREFIX) else PUB/relative
        assert p.is_file(),href
        if href.startswith('#'):assert href[1:] in parser.ids,href
        checked.append(href)
    baseline=subprocess.check_output(['git','show','f713603b4c3766f7e729a1ee4bc4c4ec8c00f9aa:docs/research/gcts-rl-renewal/index.html'],cwd=PUB).decode()
    actual=(ROOT/'docs/research/gcts-rl-renewal/index.html').read_text()
    start=actual.index('<section class="panel" id="full-cluster-model">');end=actual.index('<section class="panel" id="cluster-lifecycle">',start)
    restored=(actual[:start]+actual[end:]).replace('RESEARCH NOTEBOOK · 105','RESEARCH NOTEBOOK · 104',1)
    assert restored==baseline,'main edit exceeds one panel and notebook counter'
    result=dict(status='passed_report_projection_hash_route_link_and_baseline_checks',task_files=len(manifest),source_bindings=len(bindings),origins=len(origins),archive_routes=sum(bool(e.get('archive_member')) for e in bindings),local_links=len(checked),visual_saved_states=11,source_domains_preserved_in_full_artifact=True,main_scope='Exactly one additive panel and notebook104→105; committed f713603 baseline.',scientific_execution=False,browser_math_and_interactions='pending live validation')
    (HERE/'local-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
