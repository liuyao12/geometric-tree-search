"""Authored source-level argument, separate from discovered proof certificates."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = [
    'research/gcts-rl-renewal/fol_checker.tree',
    'research/gcts-rl-renewal/boundary_syntax.tree',
    '.gcts-active/hilbert-constant-certificates-20261011/hilbert_constant_checker_v1.py',
]

ledger = {
    'status': 'authored_source_level_preservation_argument',
    'scope': 'Closed nullary constant transport of the declared six-rule symbolic relation; no native program, compiler, runtime, Wang lowering or resource correspondence theorem.',
    'sources': {name: {'sha256': hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), 'bytes': (ROOT/name).stat().st_size} for name in SOURCES},
    'conditions': [
        'Variables, binders, predicate symbols, connective tags and command indices are unchanged.',
        'Every unchanged predicate symbol is declared in the recipient signature at the same arity.',
        'Every source constant has a declared closed nullary recipient image; the declared point/line role restrictions are retained.',
        'Each named source axiom has its literal transported image under the declared recipient axiom-name map.',
        'Every dependency alias resolves to the full transported body of an earlier available declaration; exact identity, not a hash alone, is authoritative.',
        'Recipient declaration names are distinct. Any merging of identical transported bodies needs a separately specified exact alias construction and is outside this displayed declaration-list theorem.',
        'Premise lists and command input lists preserve order and multiplicity; no premise is erased when constants coincide.',
        'The theorem is one-way preservation; it transports neither failed searches nor empirical negative labels.',
    ],
    'branches': [
        {'rule': 'assumption', 'native_source_line': 456, 'host_condition': 'Natural index selects the identical ordered local premise.', 'preservation': 'Index unchanged; corresponding premise and line are both transported.', 'wire_condition': 'Nonnegative integer tag 3, distinct from negative/boolean tags.'},
        {'rule': 'axiom', 'native_source_line': 419, 'host_condition': 'Exact field set and named axiom formula.', 'preservation': 'Exact axiom-image condition and name map.', 'wire_condition': 'Exact string tag and dictionary lookup.'},
        {'rule': 'instantiate', 'native_source_line': 426, 'host_condition': 'Well-formed universal formula, closed nullary term and literal instance implication.', 'preservation': 'Closed substitution commutes with constant transport; no variable capture or fresh binder branch.', 'wire_condition': 'Formula/term/tag checks and exact fields.'},
        {'rule': 'eq_subst', 'native_source_line': 435, 'host_condition': 'Atomic incidence template with unchanged hole variable and closed operands.', 'preservation': 'Both template substitutions commute; equality and implication constructors unchanged.', 'wire_condition': 'Native branch is broader; the host template restriction is a conservative subset.'},
        {'rule': 'mp', 'native_source_line': 441, 'host_condition': 'Both indices strictly earlier; exact antecedent/implication/conclusion match.', 'preservation': 'Transport preserves an existing literal equality even when its constant map is noninjective.', 'wire_condition': 'Out-of-range prior lookup is False and cannot match a well-formed formula.'},
        {'rule': 'block', 'native_source_line': 459, 'host_condition': 'Earlier dependency, exact ordered premise inputs and conclusion.', 'preservation': 'Declaration-DAG induction supplies the mapped dependency; input indices and multiplicity unchanged.', 'wire_condition': 'references checks complete ordered lists; check_blocks rejects duplicate names.'},
    ],
    'source_ledger_checks': [
        {'topic': 'AST well-formedness', 'native_source_lines': [152,170], 'scope': 'Nullary constants are a subset of the native term grammar; formula constructors agree.'},
        {'topic': 'Closed substitution', 'native_source_lines': [264,285], 'scope': 'Closed replacement has no free variables; native alpha-renaming branch is inactive, and absent-variable shortcut leaves the same formula.'},
        {'topic': 'Ordered registry and proof', 'native_source_lines': [365,390], 'scope': 'Check declarations in order; each proof is nonempty, every formula is well formed, and the last formula equals the declared conclusion.'},
        {'topic': 'Wire syntax', 'native_source_lines': [28], 'scope': 'boundary_syntax.tree rejects duplicate keys and distinguishes natural, negative, boolean and null tags; not a JSON parser correctness theorem.'},
    ],
    'open_obligations': [
        'Mechanized source-level proof and complete serializer/decoder correspondence.',
        'Compiler, tree-machine, tape-machine and Wang microcode correctness.',
        'Fresh native acceptance and full replay of future used transported definitions.',
        'Runtime, heap and wall-budget preservation; accepted source need not fit recipient resource bounds.',
        'Any future authority adapter and complete point-candidate correspondence.',
    ],
    'searches': 0, 'native_queries': 0, 'authority_activated': False,
}
(HERE/'constant-transport-ledger.json').write_text(json.dumps(ledger, indent=2)+'\n')

html = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>A source-level argument for families of proof clusters</title>
<style>body{margin:0;background:#f3f5f4;color:#20312d;font:17px/1.65 system-ui}main{max-width:1050px;margin:28px auto;padding:34px;background:#fff;border:1px solid #d7e0dc;border-radius:12px}h1{font:600 2rem/1.2 Georgia,serif}h2{font-size:1.25rem;margin-top:32px}a{color:#236c77}.notice{padding:16px;border-left:4px solid #ac7528;background:#fff5e2}.square{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}.cell{padding:18px;border:2px solid #467a90;border-radius:9px}.cell:nth-child(even){border-color:#785693}.cell:nth-child(n+3){border-style:dashed}.label{font-weight:600}.math{overflow:auto}table{width:100%;border-collapse:collapse}td,th{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #dce3df}.scroll{overflow:auto}code{overflow-wrap:anywhere;font-size:.87em}@media(max-width:650px){main{margin:0;padding:20px}.square{grid-template-columns:1fr}}</style>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script></head>
<body><main><p><a href="index.html#goals">Research program</a></p>
<h1>How one proof cluster can become a family</h1>
<div class="notice"><strong>Authored correctness argument.</strong> This is infrastructure for proof search, not a theorem discovered by GCTS or RL. It concerns the declared symbolic rule relation. The native compiler, machine and Wang encoding require their own correspondence evidence.</div>
<p>A receptor can expose an ordered list of premises and a conclusion. A cluster that fills it carries a proof of exactly that interface. Substituting declared constant symbols throughout the cluster changes the receptor while preserving its internal derivation, under the conditions below. No coordinates or drawn Euclidean figures are involved.</p>
<h2>The precise preservation claim</h2>
<p>Let \(\Theta\) be a symbolic theory with nullary constants and the declared predicates. Let \(h\) send each constant to a declared nullary constant of the same allowed role, while leaving variables, binders, predicate symbols and connective tags unchanged. Every unchanged predicate remains declared at the same arity in \(\Theta'\), which contains the exact image of each used named axiom. The constant map may be noninjective. Choose distinct recipient declaration names, and let \(\rho\) assign each dependency to the corresponding earlier declaration with its full transported body.</p>
<div class="math">\[\operatorname{Check}_{6}(\Theta,\mathcal B)=1
\quad\Longrightarrow\quad
\operatorname{Check}_{6}(\Theta',h_{\rho}(\mathcal B))=1.\]</div>
<p>Here \(\operatorname{Check}_{6}\) means the six-rule symbolic relation specified in the ledger, and \(\mathcal B\) is a finite ordered dependency graph. Every premise occurrence and input index remains in its original order. Identifying two constants does not authorize deleting duplicate premises or changing command references. Distinct source bodies can become identical after transport; keep distinct declaration identities for this theorem. Merging identical bodies requires a separately specified exact alias construction.</p>
<div class="square" aria-label="Symbolic substitution commutes with local proof derivation; not a point-tile certificate">
<div class="cell"><span class="label">Source receptor</span><div class="math">\[\Gamma\vdash_{\Theta} F\]</div><p>Ordered premises and a checked cluster body.</p></div>
<div class="cell"><span class="label">Recipient receptor</span><div class="math">\[h(\Gamma)\vdash_{\Theta'}h(F)\]</div><p>Every symbol image and dependency alias is explicit.</p></div>
<div class="cell"><span class="label">One internal command</span><div class="math">\[F[x:=c]\]</div><p>A variable is replaced by a closed constant.</p></div>
<div class="cell"><span class="label">The corresponding command</span><div class="math">\[h(F[x:=c])=h(F)[x:=h(c)]\]</div><p>The same result follows after transport.</p></div></div>
<h2>Why the claim holds</h2>
<p>First prove the displayed substitution identity by induction on formula syntax. Constants are transported, variables are fixed, and each connective is traversed component by component. At a quantifier binding the substituted variable, both operations stop at the same binder. At any other quantifier, the closed replacement has no free variables, so it cannot be captured and no fresh binder is needed.</p>
<p>Next induct on commands within each declaration, and then on declarations in dependency order. The cases are:</p>
<div class="scroll"><table><thead><tr><th>Rule</th><th>Preserved check</th></tr></thead><tbody>
<tr><td><code>assumption</code></td><td>The unchanged index selects the corresponding occurrence of the transported ordered premise list.</td></tr>
<tr><td><code>axiom</code></td><td>The declared axiom-name map selects exactly the transported axiom formula.</td></tr>
<tr><td><code>instantiate</code></td><td>The universal-instance implication is preserved by the substitution identity.</td></tr>
<tr><td><code>eq_subst</code></td><td>The equality and both substitutions into the unchanged incidence template are preserved by the same identity.</td></tr>
<tr><td><code>mp</code></td><td>Earlier indices remain earlier. Transport preserves the literal antecedent and implication match; injectivity is unnecessary.</td></tr>
<tr><td><code>block</code></td><td>The declaration induction supplies the exact earlier mapped dependency. Its ordered input list and conclusion match the transported command.</td></tr>
</tbody></table></div>
<p>The last command is transported into the declared conclusion. This completes the source-level preservation argument. It proves a direction of valid derivation transport; it does not transport a failed search, an empirical negative guard label, or a resource bound.</p>
<h2>Relation to the fixed native checker</h2>
<p>The ledger pins the actual <a href="../../../research/gcts-rl-renewal/fol_checker.tree">checker source</a> and <a href="../../../research/gcts-rl-renewal/boundary_syntax.tree">wire wrapper</a>. Its six entries identify the source branches for exact fields, formula/term checks, named axioms, strict prior references, ordered assumptions and block availability. The host relation deliberately accepts a narrower syntax: closed nullary images and the atomic incidence equality template.</p>
<p>This is a static branch correspondence ledger, not a mechanized proof of the complete executable stack. A source-valid recipient can still exhaust its heap or time budget. Future used mapped definitions must appear in a freshly checked whole native certificate with full replay; the finite structural certificate must not be relabeled <code>native_accepted</code>.</p>
<p><a href="constant-transport-ledger.json">Exact conditions, branch locations and open obligations</a></p>
</main></body></html>'''
(HERE/'constant-transport-argument.html').write_text(html)
print(json.dumps({'ledger': str(HERE/'constant-transport-ledger.json'), 'html': str(HERE/'constant-transport-argument.html'), 'queries': 0}))
