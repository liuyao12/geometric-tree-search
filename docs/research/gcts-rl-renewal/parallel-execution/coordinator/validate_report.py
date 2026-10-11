"""Read-only report/hash/link validation. No search or inference execution."""
import hashlib
import json
import re
import time
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PUB = Path('/private/tmp/gcts-family-router-publish-20261010')
PREFIX = 'docs/research/gcts-rl-renewal/parallel-execution/'


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.scripts, self.proof_rows = set(), [], [], 0
        self.script = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'duplicate id: ' + a['id']
            self.ids.add(a['id'])
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'article' and 'proof-row' in a.get('class', '').split():
            self.proof_rows += 1
        if tag == 'script' and not a.get('src'):
            self.script = ''

    def handle_data(self, s):
        if self.script is not None:
            self.script += s

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(self.script)
            self.script = None


def main():
    started = time.perf_counter()
    manifest = json.loads((HERE / 'task-files.json').read_text())
    for e in manifest:
        b = (ROOT / e['path']).read_bytes()
        assert sha(b) == e['sha256'] and len(b) == e['bytes'], e['path']
    bindings = json.loads((ROOT / PREFIX / 'source-input-bindings.json').read_text())
    archive_cache = {}
    task_paths = {e['path'] for e in manifest}
    def route(path, link=False):
        return ROOT / path if path.startswith(PREFIX) or (link and path in task_paths) else PUB / path
    for e in bindings:
        p = route(e['published_path'])
        if e['archive_member']:
            if str(p) not in archive_cache:
                archive_cache[str(p)] = zipfile.ZipFile(p)
            b = archive_cache[str(p)].read(e['archive_member'])
        else:
            b = p.read_bytes()
        assert len(b) == e['bytes'] and sha(b) == e['sha256'], e['path']
    reader_path = ROOT / PREFIX / 'reader.html'
    s = reader_path.read_text()
    parser = Reader()
    parser.feed(s)
    checked_links = 0
    for href in parser.links:
        u = urlsplit(href)
        if u.scheme or u.netloc:
            continue
        if not u.path:
            if u.fragment:
                assert unquote(u.fragment) in parser.ids, href
        else:
            p = (reader_path.parent / unquote(u.path)).resolve()
            if p.is_dir():
                p = p / 'index.html'
            relative = str(p.relative_to(ROOT))
            target = route(relative,link=True)
            if target.is_dir():
                target = target / 'index.html'
            assert target.exists(), href
            if u.fragment and target.suffix == '.html':
                other = Reader(); other.feed(target.read_text())
                assert unquote(u.fragment) in other.ids, href
        checked_links += 1
    assert s.count(r'\(') == s.count(r'\)')
    assert s.count(r'\[') == s.count(r'\]')
    assert '<sup' not in s and '<sub' not in s
    assert parser.proof_rows == 9, parser.proof_rows
    assert s.count('class="mark formula-mark"') == 11
    assert s.count('class="mark reference-mark"') == 2
    main_text = (ROOT / 'docs/research/gcts-rl-renewal/index.html').read_text()
    old = (PUB / 'docs/research/gcts-rl-renewal/index.html').read_text()
    restored = re.sub(r'<section class="panel" id="parallel-execution">.*?</section>\n', '', main_text, count=1, flags=re.S)
    restored = restored.replace('RESEARCH NOTEBOOK · 103', 'RESEARCH NOTEBOOK · 102', 1)
    assert restored == old, 'unrelated main report edit'
    for a in archive_cache.values():
        a.close()
    receipt = {'status':'passed_local_report_hash_links_and_projection_checks',
               'task_files':len(manifest),'source_input_bindings':len(bindings),
               'local_links_checked':checked_links,'colored_generic_placements':8,
               'separate_remote_catalog_probe':1,'formula_tags':11,'reference_tags':2,
               'main_report_change':'one additive panel and notebook number only',
               'reader_sha256':sha(reader_path.read_bytes()),
               'seconds_before_write':time.perf_counter()-started,
               'inline_browser_execution':'not checked here; live UI check remains required'}
    (HERE / 'local-validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
