"""Display the audited forward-control point tiles beside each exact formula.

Presentation only. This supplies neither a target proof nor a search policy.
The frozen 99-file arithmetic export and its native unknowns are unchanged.
"""
import gzip
import hashlib
import html
import json
import argparse
from pathlib import Path

from induction_receptors_export import explanation, math

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/research/gcts-rl-renewal'
OUT = ROOT / '.gcts-active/proof-program-continuation-20261011'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(checked_workspace=False):
    evidence_path = DOC / 'left_successor_forward_control_point_encoding.json.gz'
    evidence = json.loads(gzip.decompress(evidence_path.read_bytes()))
    audit = json.loads((DOC / 'left_successor_forward_control_point_audit.json').read_text())
    assert audit['status'] == 'passed_exact_control_word_point_encoding'
    actual = evidence[0]['actual_word']
    proof = actual['search']['proof']
    assert len(proof) == 11
    indexed = {tuple(p['key']): p for p in actual['model']['placements']}
    selected = [indexed[tuple(key)] for key in actual['search']['placements']]
    assert len(selected) == 44
    rows = []
    checks = []
    names = ['C', 'G', 'I1', 'I2']
    classes = ['command', 'guard', 'first-input', 'second-input']
    for j, command in enumerate(proof):
        tiles = sorted((p for p in selected if p['slot'] == j), key=lambda p:p['occupancy'][0][0][1])
        assert len(tiles) == 4
        assert [p['occupancy'] for p in tiles] == [[[[4*j,k],12]] for k in range(4)]
        inputs = command.get('inputs', [command['source']] if 'source' in command else [])
        cards = []
        for k, tile in enumerate(tiles):
            if k == 0:
                label = 'command ' + str(tile['key'][2])
            elif k == 1:
                label = 'interface ' + str(tiles[0]['marks'][0][1])
            elif k - 2 < len(inputs):
                source = inputs[k-2] + 1
                label = '<a href="#line-' + str(source) + '">line ' + str(source) + '</a>'
            else:
                label = 'unused'
            cls = classes[k] if k < 2 or k - 2 < len(inputs) else 'unused'
            cards.append('<div class="tile '+cls+'"><code>'+names[k]+'</code><span>'+label+'</span></div>')
        formula = math(command['formula'])
        words = explanation(command, actual['model']['inference_rules']).replace('local lines', 'lines')
        local_link = '<a href="left_successor.html#proof-'+str(j+1)+'">Inspect the admitted local derivation</a>' if command['rule'] == 'block' else ''
        payload = dict(command=command,placements=[dict(key=p['key'],occupancy=p['occupancy'],marks=p['marks']) for p in tiles])
        rows.append('<article class="proof-row" id="line-'+str(j+1)+'"><div class="row-title">Line '+str(j+1)+'</div><div class="row-body"><div class="tile-strip">'+''.join(cards)+'</div><div class="translation"><div class="formula">'+formula+'</div><p>'+html.escape(words)+'</p><p class="small">'+local_link+'</p></div></div><details><summary>Exact command, occupancy and extended markings</summary><pre>'+html.escape(json.dumps(payload,indent=2))+'</pre></details></article>')
        checks.append(dict(line=j+1,formula=command['formula'],inputs=inputs,tiles=payload['placements']))
    text = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Left-successor candidate · tiles translated line by line</title>
<link rel="stylesheet" href="report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>body{margin:0}main{max-width:1160px;margin:auto;padding:32px 24px}h1{line-height:1.15}.status{border-left:4px solid #b78225;background:#fff5df;padding:16px 20px}.small{font-size:.92rem}.proof-row{padding:20px 0;border-top:1px solid #d5d9d4;scroll-margin-top:20px}.row-title{font-weight:700;color:#3b5e50;margin-bottom:12px}.row-body{display:grid;grid-template-columns:360px minmax(0,1fr);gap:24px;align-items:start}.tile-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}.tile{aspect-ratio:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border:1px solid #3d4b56;border-radius:4px;color:white;font-size:.8rem;gap:7px;padding:2px}.tile code{background:transparent;color:inherit;font-size:1rem}.tile a{color:inherit;text-decoration:underline}.command{background:#7e57c2}.guard{background:#d29a23;color:#222}.first-input{background:#258763}.second-input{background:#d4793a}.unused{background:#f1f2f3;border:1px dashed #71808c;color:#4e5861}.formula{overflow:auto;font-size:1.06rem;padding-bottom:5px}.translation p{margin:8px 0}.legend{display:flex;gap:18px;flex-wrap:wrap}details{margin-top:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:440px;overflow:auto}@media(max-width:850px){.row-body{grid-template-columns:1fr}.tile-strip{max-width:390px}main{padding:24px 16px}}</style></head><body><main>
<p><a href="index.html#parallel-research">Research program</a> · <a href="left_successor.html#forward-control">Complete arithmetic comparison</a></p>
<p class="eyebrow">AUTOMATIC FORWARD CONTROL · EXACT POINT TILES · WHOLE NATIVE CHECK UNKNOWN</p><h1>The tiles, and what each line says.</h1>
<p class="status">This candidate was extracted automatically by ordinary forward chaining. All eight bounded GCTS searches remained unresolved. Its exact point tiling and local inference interfaces passed independent audits; both complete native certificate variants reached a workspace limit. This reader presents a native-unknown candidate, not an accepted whole Wang proof or a GCTS discovery.</p>
<p>Each row displays its actual four selected point tiles beside the exact output formula and its English explanation. The green and orange inputs link to the earlier lines they read. Expand a row to inspect every occupancy value and distant marking. The frozen candidate and measurements are unchanged.</p>
<p>The glyphs show the high-level point encoding. Placements have fixed orientation and move by translation. These glyphs are distinct from the universal checker’s primitive Wang squares. Each selected placement fills one required point with exact normalized occupancy \(t=1\), encoded in \(12\) integer units; its marking values must agree at every shared point, including points beyond its occupancy support.</p>
<p class="legend"><span>Purple <code>C</code>: command</span><span>Gold <code>G</code>: admitted interface</span><span>Green <code>I1</code>: first source</span><span>Orange <code>I2</code>: second source</span><span>Dashed gray: explicitly unused</span></p><section id="reader">'''
    text += ''.join(rows)
    text += r'''</section><p><a href="left_successor.html#primitive">Read all \(67\) mechanically compiled primitive commands</a> · <a href="left_successor.html#costs">Inspect preparation, search and verification costs</a></p>
<p>The only input arithmetic axioms define addition at zero and at a successor on the right; the natural-number induction schema is enabled. The conclusion is \(\forall x\,\forall y\,(S(x)+y=S(x+y))\). A supplied target-driven finite grammar limits the experiment; the induction predicate was not learned by RL. Neither inventory uses the transferred left-zero theorem in this candidate.</p>
<p><a href="left_successor_forward_control_point_encoding.json.gz">Complete source point encoding</a> · <a href="left_successor_forward_control_point_audit.json">Independent point audit</a> · <a href="left_successor_forward_control_audit.json">Complete closure and native replay audit</a> · <a href="left_successor_frozen_evidence.zip">Frozen source and native evidence</a></p></main></body></html>'''
    workspace_binding = None
    if checked_workspace:
        audit_path = DOC / 'left_successor_workspace_native_audit.json'
        workspace_audit = json.loads(audit_path.read_text())
        original = json.loads(gzip.decompress((DOC / 'left_successor_forward_control_native.json.gz').read_bytes()))
        accepted = json.loads(gzip.decompress((DOC / 'left_successor_workspace_native_native.json.gz').read_bytes()))
        assert workspace_audit['status'] == 'passed_complete_larger_workspace_native_replay'
        assert len(original) == len(accepted) == len(workspace_audit['observations']) == 2
        for old, new, replay in zip(original, accepted, workspace_audit['observations']):
            assert old['request'] == new['request']
            assert old['request_sha256'] == new['request_sha256'] == replay['request_sha256']
            assert old['result']['status'] == 'unknown_space_budget'
            assert new['result']['status'] == replay['status'] == 'accepted'
            assert new['result']['micro_steps'] == replay['micro_steps']
            assert replay['heap_capacity'] == 262144 and replay['all_input_output_matched']
            assert not replay['out_of_frame_bands']
        text = text.replace('WHOLE NATIVE CHECK UNKNOWN', 'WHOLE NATIVE ACCEPTANCE IN LARGER WORKSPACE')
        old_status = 'This candidate was extracted automatically by ordinary forward chaining. All eight bounded GCTS searches remained unresolved. Its exact point tiling and local inference interfaces passed independent audits; both complete native certificate variants reached a workspace limit. This reader presents a native-unknown candidate, not an accepted whole Wang proof or a GCTS discovery.'
        new_status = 'This proof was extracted automatically by ordinary forward chaining. All eight bounded GCTS searches remain unresolved. Both complete native variants now have independently replayed acceptance in a separately declared larger workspace: the same eleven-row request and its exact primitive-command expansion. The checker and tile palette are unchanged. The original smaller-workspace unknowns remain recorded. This is ordinary-control discovery; no GCTS or RL discovery is claimed. <a href="left_successor_workspace.html?v=20261011-ws1#result">Inspect the two acceptances and boundary change</a>.'
        assert text.count(old_status) == 1
        text = text.replace(old_status, new_status)
        workspace_binding = dict(audit_sha256=digest(audit_path),
            request_sha256s=[r['request_sha256'] for r in accepted],
            heap_capacity=262144, original_native_outcomes_preserved=True)
    # TeX source outside JavaScript needs single backslashes.
    script_end = text.index('</script>', text.index('window.MathJax')) + len('</script>')
    text = text[:script_end] + text[script_end:].replace(chr(92) * 2, chr(92))
    target = DOC / 'left-successor-reader.html'
    target.write_text(text)
    source = Path(__file__)
    receipt = dict(status='exact-row-data-verified-awaiting-browser',rows=11,tiles=44,
        source_evidence_sha256=digest(evidence_path),formula_checks=checks,
        checked_workspace=workspace_binding,
        files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=digest(p)) for p in [target,source]])
    (OUT / 'row-reader.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(rows=11,tiles=44,html_bytes=target.stat().st_size)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checked-workspace', action='store_true')
    main(parser.parse_args().checked_workspace)
