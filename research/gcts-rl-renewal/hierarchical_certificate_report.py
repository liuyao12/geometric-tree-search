"""Static reader of audited post-search representations; no scientific reruns."""
import gzip
import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path
from induction_receptors_export import math, explanation

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/proof-program-matched-boundaries-20261011'
DOC = ROOT / 'docs/research/gcts-rl-renewal/certificate-hierarchy'


def load(path):
    with gzip.open(path, 'rt') as source:
        return json.load(source)


def esc(value):
    return html.escape(str(value), quote=True)


def quantity(value):
    return r'\(' + esc(value) + r'\)'


def words(command):
    if command['rule'] == 'block':
        refs = ', '.join('line ' + str(i + 1) for i in command['inputs'])
        return 'Use checked local lemma ' + command['name'] + (' with ' + refs if refs else ', with no local inputs') + '.'
    return explanation(command, [])


def proof(lines):
    return '<ol class="proof">' + ''.join('<li><div class="formula">' + math(c['formula']) +
                                          '</div><p>' + esc(words(c)) + '</p></li>' for c in lines) + '</ol>'


def main():
    DOC.mkdir(parents=True, exist_ok=True)
    rep = json.loads((OUT / 'representation/audit.json').read_text())
    renamed = json.loads((OUT / 'short-identifiers/audit.json').read_text())
    encoded = json.loads((OUT / 'movable-encoding/audit.json').read_text())
    review = json.loads((OUT / 'representation-review.json').read_text())
    assert rep['status'] == 'passed_full_context_compaction_and_both_capacity_replays'
    assert renamed['status'] == 'passed_full_bijective_renaming_and_capacity_replay'
    assert encoded['status'] == 'passed_complete_movable_encoding_byte_audit'
    original = load(ROOT / '.gcts-active/commutativity-cluster-search-20261011/certificates.json.gz')['candidates'][0]
    transformation = load(OUT / 'representation/transformation.json.gz')
    packet = load(OUT / 'short-identifiers/observation.json.gz')
    assert original['original_request'] == transformation['request']
    assert len(packet['request']['proof']) == 13 and len(packet['request']['blocks']) == 9
    counts = [('Flattened shared certificate', 152, 596873), ('Original lemma hierarchy', 185, 291874),
              ('Hierarchy after context sharing', 185, 291589), ('Hierarchy with short block identifiers', 185, 263826)]
    bars = ''.join('<div class="plotrow"><div class="label">' + esc(name) + '</div><div class="track">'
                   '<div class="limit"></div><div class="bar" style="width:' + str(cells / 596873 * 100) + '%"></div>'
                   '</div><div>' + quantity(cells) + '</div></div>' for name, commands, cells in counts)
    rows = ''.join('<tr><td>' + esc(name) + '</td><td>' + quantity(commands) + '</td><td>' + quantity(cells) +
                   '</td><td>exceeds the fixed boundary</td></tr>' for name, commands, cells in counts)
    page = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Proof hierarchy and certificate memory</title><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>body{margin:0;background:#f3f6f9;color:#203648;font:17px/1.6 system-ui}main{max-width:1100px;margin:24px auto;padding:30px;background:white}h1{line-height:1.2}section{margin:34px 0}.notice{padding:16px;background:#fff1da;border-left:5px solid #b07c24}.formula,.scroll{overflow:auto;max-width:100%}.formula{padding:12px;background:#f5f7fa}.proof>li{padding:12px 0;border-bottom:1px solid #ccd8e1}table{border-collapse:collapse;width:100%}td,th{padding:9px;text-align:left;border-bottom:1px solid #ccd8e1}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{overflow-wrap:anywhere}summary{cursor:pointer;padding:10px;font-weight:600}details{margin:12px 0}.plotrow{display:grid;grid-template-columns:260px minmax(100px,1fr) 110px;gap:12px;align-items:center;margin:14px 0}.track{position:relative;height:28px;background:#edf1f5}.bar{height:100%;background:#658db5}.plotrow:last-child .bar{background:#8a6eaa}.limit{position:absolute;left:43.920%;top:-6px;bottom:-6px;width:2px;background:#b07c24;z-index:2}a{color:#1a638a}@media(max-width:650px){main{padding:18px;margin:0}.plotrow{grid-template-columns:1fr 85px}.label{grid-column:1/-1}}</style></head><body><main><p><a href="../#certificate-hierarchy">Research program</a> · <a href="../commutativity_cluster_results.html#reader">Original discovered proof and colored row tiles</a></p><h1>Keep the lemmas. Reduce the certificate memory.</h1>'''
    page += '<div class="notice">This is a representation study of the already automatically discovered <strong>ordinary-forward</strong> proof. No GCTS target proof, RL training or new theorem was discovered here. Native execution remains pending.</div>'
    page += '<section id="comparison"><h2>The same conclusion, different stored representations</h2><div class="formula">' + math(packet['request']['target']) + '</div><p>The original arithmetic theory, formulas and every local premise remain unchanged. The hierarchy retains the original ' + quantity(9) + ' checked lemma declarations and ' + quantity(13) + ' root commands. A separate independent interpreter replays every tree instruction and every final heap pair for each measured representation.</p>' + bars
    page += '<p>The orange marker is the fixed ' + quantity(262144) + '-cell heap ceiling. Every measured representation exceeds it. These are complete canonical native-heap estimates, not native executions.</p><div class="scroll"><table><thead><tr><th>Representation</th><th>Stored commands</th><th>Required heap cells</th><th>Fixed-boundary result</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
    page += '<p>Keeping lemma declarations uses less heap than the previously published flattened certificate. Generic context-local sharing removes no commands from this particular hierarchy: its canonical request remains identical. The small difference between the first two hierarchical runs comes from normalization of nested object-field order in the postfix input encoding. It is not proof shortening. Canonical JSON hashes alone do not identify that wire order; the auditor reconstructs all actual input words and constructor data.</p>'
    page += '<p>Bijective internal declaration renaming changes long block identifiers to <code>b0</code> through <code>b8</code>. Only declaration names and their block-call references change. Ordered premises, all command formulas, command order, line references, eigenvariable contexts, axiom names and the complete theory and target are checked unchanged. All four actual renaming corruptions reject. This is authored certificate infrastructure, not a learned marking or search-speed result.</p></section>'
    page += '<section id="boundary"><h2>A separately declared movable blank boundary</h2><p>The short-name certificate requires ' + quantity(263826) + ' cells, still ' + quantity(1682) + ' above the original limit. A new preparation phase chooses the smallest ' + quantity(4096) + '-cell multiple covering that exact requirement plus ' + quantity(64) + ' spare cells: ' + quantity(266240) + '. The boundary therefore grows by ' + quantity(4096) + ' cells. The original fixed-boundary unknown is preserved.</p><p>The unchanged machine starts at parser state <code>88986</code>. An independent encoder checks every fixed/free word, head, band capacity, physical coordinate and all ' + quantity(encoded['input_bytes']) + ' input bytes. This phase performs zero native queries. A later separately frozen whole native execution and complete independent tape replay are still required; no native or Wang proof acceptance is inferred from input preparation.</p></section>'
    page += '<section id="reader"><h2>Read the retained root derivation</h2><p>These are the original automatically selected formulas. The displayed short names refer to the exact local definitions below. Line numbering restarts inside each lemma. The <a href="../commutativity_cluster_results.html#reader">original reader</a> shows the selected colored point tiles and richer search-rule explanations; its flattened certificate is a different, equivalent stored representation.</p>' + proof(packet['request']['proof']) + '</section>'
    page += '<section id="lemmas"><h2>Open every retained lemma</h2>'
    for block, alias in zip(packet['request']['blocks'], packet['aliases']):
        page += '<details><summary>' + esc(block['name']) + ' — ' + esc(len(block['proof'])) + ' local commands</summary><p>Original inventory identity: <code>' + esc(alias['old']) + '</code></p><p>Full local premises: ' + (' ; '.join(math(f) for f in block['premises']) if block['premises'] else 'none') + '.</p><div class="formula">Conclusion: ' + math(block['conclusion']) + '</div>' + proof(block['proof']) + '</details>'
    page += '</section><section id="costs"><h2>Measured costs and limits</h2><div class="scroll"><table><thead><tr><th>Phase</th><th>Internal seconds</th><th>Driver peak RSS bytes</th></tr></thead><tbody>'
    names = [('Hierarchy producer', 'representation/summary.json'), ('Complete hierarchy replay', 'representation/audit.json'),
             ('Short-name producer', 'short-identifiers/summary.json'), ('Complete renaming replay', 'short-identifiers/audit.json'),
             ('Moved-boundary input preparation', 'movable-encoding/summary.json'), ('Independent full byte audit', 'movable-encoding/audit.json')]
    for name, path in names:
        value = json.loads((OUT / path).read_text())
        page += '<tr><td>' + esc(name) + '</td><td>' + quantity(f'{value["seconds"]:.6f}') + '</td><td>' + quantity(value['peak_rss_bytes']) + '</td></tr>'
    page += '</tbody></table></div><p>Each capacity producer and replay has a separately frozen ' + quantity(180) + '-second, ' + quantity(512) + '-MiB gate and a ' + quantity(20000000) + '-tree-instruction limit per request. Input preparation and byte audit each have a ' + quantity(30) + '-second gate. All complete measured phases stay within their gates. SIGALRM wall interruption and final kernel peak RSS are credited; no OS hard memory limit is claimed.</p><p>Internal timers include binding checks, transformation, execution and observation serialization, ending before the final small receipt write. Interpreter startup, manual infrastructure development and final receipt writes are not separately measured. Prior discovery, ' + quantity(94) + ' native local admissions, ordinary-control search, flattening and the original heap unknown remain separately charged in the previous report. The original short-name audit source was never run: source review caught its wire-order assumption, and v2 was frozen before its first audit execution.</p></section>'
    files = []
    for scope in ('representation', 'short-identifiers', 'movable-encoding'):
        for path in sorted((OUT / scope).iterdir()):
            if path.is_file():
                relative = Path(scope) / path.name
                target = DOC / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                files.append(target)
    shutil.copyfile(OUT / 'representation-review.json', DOC / 'independent-review.json')
    files.append(DOC / 'independent-review.json')
    page += '<section id="evidence"><h2>Exact evidence and remaining obligations</h2><p><a href="representation/audit.json">Full hierarchy replay</a> · <a href="short-identifiers/audit.json">Exact renaming and capacity replay</a> · <a href="movable-encoding/audit.json">Every input byte</a> · <a href="independent-review.json">Independent source review</a> · <a href="evidence.zip">Frozen sources, inputs and receipts</a></p><p>Formal serializer/compiler/native/Wang correctness and primitive-placement aggregate correspondence remain open. This study demonstrates a representation benefit from retaining lemmas, a technique already used by ordinary proof systems. It supplies no evidence that GCTS or RL finds proofs more efficiently. The shared native checker and computational tile palette remain unchanged.</p></section></main></body></html>'
    (DOC / 'reader.html').write_text(page)
    files.append(DOC / 'reader.html')
    archive_paths = {str(Path(__file__).relative_to(ROOT)), 'research/gcts-rl-renewal/induction_receptors_export.py',
                     str((OUT / 'representation-review.json').relative_to(ROOT)), 'docs/basic-tiling-algorithm.md'}
    for scope in ('representation', 'short-identifiers', 'movable-encoding'):
        for path in (OUT / scope).iterdir():
            if path.is_file():
                archive_paths.add(str(path.relative_to(ROOT)))
                if path.name.endswith('plan.json'):
                    value = json.loads(path.read_text())
                    for key in ('source_sha256', 'input_sha256'):
                        for rel, expected in value.get(key, {}).items():
                            assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected
                            archive_paths.add(rel)
    with zipfile.ZipFile(DOC / 'evidence.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for rel in sorted(archive_paths):
            archive.write(ROOT / rel, rel)
    files.append(DOC / 'evidence.zip')
    sources = ['hierarchical_certificate_capacity.py', 'hierarchical_certificate_capacity_audit.py',
               'certificate_block_identifiers.py', 'short_identifier_capacity.py',
               'short_identifier_capacity_audit.py', 'short_identifier_capacity_audit_v2.py',
               'short_identifier_encoding.py', 'hierarchical_certificate_report.py']
    files.extend(Path(__file__).parent / name for name in sources)
    manifest = dict(status='prepared_audited_post_search_representations', native_queries=0,
                    reader='certificate-hierarchy/reader.html#comparison', files=[dict(path=str(p.relative_to(ROOT)),
                    bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    (OUT / 'representation-integration.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(status=manifest['status'], files=len(files), archive_entries=len(archive_paths),
                         archive_bytes=(DOC / 'evidence.zip').stat().st_size, reader_bytes=len(page.encode()))))


if __name__ == '__main__':
    main()
