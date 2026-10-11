#!/usr/bin/env python3
"""Build the chair boundary-mode Notes from executed audit and FEM receipts."""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parent
DOCS=ROOT.parents[1]/'docs/projects'


def main():
    construction=json.loads((ROOT/'chair-boundary-field.json').read_text())
    projection=json.loads((ROOT/'chair-modal-projection.json').read_text())
    assert construction['status']==projection['status']=='passed'
    head=(DOCS/'l-triomino-boundary-modes.html').read_text().split('</head>')[0]
    head=re.sub(r'<title>.*?</title>','<title>3D chair Notes: one prescribed field and aperiodic matching</title>',head)
    head=re.sub(r'<meta name="description".*?>','<meta name="description" content="One prescribed scalar Neumann field on the seven-cube chair encodes Chair44 matching; infinite expansions and sixty numerical 3D modes.">',head)
    head+=r'''
<style>.chair-controls{display:flex;gap:15px;flex-wrap:wrap;margin:18px 0;font:14px system-ui,sans-serif}.chair-controls label{display:flex;flex-direction:column;gap:6px}.chair-controls select,.chair-controls button{padding:10px;border:1px solid #adc4b9;border-radius:5px;background:white;font:14px system-ui,sans-serif;max-width:100%}.chair-viewer{border:1px solid #adc4b9;border-radius:12px;padding:24px;background:white}.chair-views{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.chair-view{min-width:0}.chair-view canvas{display:block;max-width:100%;touch-action:none;cursor:grab}.chair-viewer svg{width:100%;height:auto;display:block;background:#f7f9f3;border:1px solid #dae2d8;border-radius:8px}.chair-viewer circle[role=button]{cursor:pointer}.chair-viewer circle:focus{stroke:#273d36;stroke-width:3}.chair-axis{text-align:center;margin:2px 0 15px}.chair-detail{background:#edf2e9;padding:12px 18px;margin-top:16px}.chair-detail p{margin:8px 0}#chair-viewer-status{font:14px/1.6 system-ui,sans-serif}.chair-view figcaption{font:13px/1.5 system-ui,sans-serif;margin:8px 0}.chair-view h4{margin:14px 0 8px;font:600 15px system-ui,sans-serif}@media(max-width:650px){.chair-views{grid-template-columns:1fr}.chair-viewer{padding:14px}}</style>
</head><body><main>
<nav><a href="spectral-tiling-study.html">Spectral tiling Notes</a> / Current 3D chair study</nav>
<p class="eyebrow">Seven-cube chair · updated 11 October 2026</p>
<h1>One prescribed field on the 3D chair</h1>
<p class="lead">A scalar boundary profile can carry both the direction and color information of Chair44. One fixed smooth Neumann field, transported with the chair, therefore encodes the known aperiodic matching rule. This exact construction uses infinitely many ordinary eigenmodes.</p>
<div class="tools"><a href="#result">Precise result</a><a href="#carrier">The boundary carrier</a><a href="#proof">Why matching is equivalent</a><a href="#spectrum">3D modes and coefficients</a><a href="#finite">Finite-mode limits</a><a href="#sources">Sources and audit</a></div>
<h2 id="result">The result and its scope</h2>
<div class="callout"><p>Allow integer translations and all twenty-four proper cubic rotations of the exact seven-cube chair, excluding reflections. Each copy carries the same prescribed total field in its own coordinates, with fixed amplitude. Require scalar values to agree on every shared unit boundary panel. This has exactly the Chair44 arrow-rule tilings. The cited Chair44 theorem supplies infinite existence and excludes every nonzero translational period of the decorated tiling. <a href="#ref-gs">[1]</a></p></div>
<p>Here the rule encodes the chair's own hierarchy of supertiles. A single prototype field replaces an arbitrary menu of independently colored tiles. The ordinary boundary condition is homogeneous Neumann, \(\partial_\nu u=0\); restricting the modal coefficients to this prescribed field is an additional matching constraint. Arbitrary superpositions, or the Neumann condition alone, do not force aperiodicity.</p>
<div class="scroll"><table><thead><tr><th>Question</th><th>Current answer</th></tr></thead><tbody>
<tr><td>Exact seven-cube geometry?</td><td>Yes, with no bumps or dents.</td></tr>
<tr><td>How many prescribed fields?</td><td>One in local coordinates; its \(24\) proper rotations are distinct.</td></tr>
<tr><td>Boundary condition?</td><td>Exact homogeneous Neumann on every boundary panel.</td></tr>
<tr><td>Infinite tilings, with no translation period?</td><td>Inherited through an exact transfer of the cited Chair44 rule.</td></tr>
<tr><td>Exact finite eigenmode sum?</td><td>No for this compact-profile carrier; another finite construction remains unresolved.</td></tr>
<tr><td>Arbitrary rotations, translations or reflections?</td><td>Outside the declared model; no geometric registration or reflection-transfer theorem is claimed.</td></tr>
<tr><td>Erasing the fields?</td><td>The bare chair admits periodic tilings. This study does not establish whether every admitted arrangement remains nonperiodic after field erasure.</td></tr>
</tbody></table></div>
<h2 id="carrier">A scalar profile remembers an arrow and its color</h2>
<p>The chair is the interior of the union of the closed unit cubes</p>
\[ \overline\Omega=\bigcup_{c\in C}\bigl(c+[0,1]^3\bigr),\qquad C=\{0,1\}^3\setminus\{(1,1,1)\}. \]
<p>It has volume \(7\) and \(24\) exposed unit panels. The given decoration assigns each panel an outward unit normal \(n\), a nonzero diagonal tangent arrow \(a\), and a color. Set</p>
\[ \sigma=\begin{cases}1,&\text{red},\\-1,&\text{green},\\0,&\text{blue},\end{cases}\qquad b=\sigma n,\qquad d=b\times a,\qquad |a|^2=2. \]
<p>Across a common panel, the arrow rule requires equal tangent arrows and either red/green or blue/blue colors. Opposite outward normals turn this complementary-color requirement into equality of \(b\). This normal vector can be carried by the tangent vector \(d\), because</p>
\[ b=\frac{a\times d}{2}. \]
<p>For tangential displacement \(y\) from the panel center, use</p>
\[ B(y)=\begin{cases}\exp\!\left(1-\dfrac1{1-16|y|^2}\right),&|y|&lt;1/4,\\0,&|y|\ge1/4,\end{cases}\qquad F_{a,b}(y)=B(y)\bigl(a\cdot y+16|y|^2(d\cdot y)\bigr). \]
<p>The linear and cubic terms independently carry two tangent vectors. This is one scalar profile; the displayed red/blue intensity of the function is not the source arrow's color.</p>
<h3>The full field and its boundary condition</h3>
<p>For each panel center \(p_j\), let \(r_j(x)=(x-p_j)\cdot n_j\) and \(y_j(x)=x-p_j-r_j(x)n_j\). Define</p>
\[ K(z)=\begin{cases}\exp\!\left(1-\dfrac1{1-z^2}\right),&|z|&lt;1,\\0,&|z|\ge1,\end{cases}\qquad u(x)=\sum_{j=1}^{24}F_{a_j,b_j}\bigl(y_j(x)\bigr)K\bigl(4r_j(x)\bigr). \]
<p>Each open support fits inside a ball with squared radius \(1/8\). Distinct panel centers have squared separation at least \(1/2\), so those open balls are disjoint, even in the equality case. The squared distance from each center to any other panel is at least \(1/4\), so its support avoids every other boundary panel. On its own panel the trace is exactly \(F_{a_j,b_j}\), and its normal derivative is zero since \(K'(0)=0\). All fields vanish near unit-panel edges and corners.</p>
<h2 id="proof">Why boundary equality is exactly the given matching rule</h2>
<ol>
<li>On the common disk, divide equal traces by the positive common factor \(B\). Equality becomes equality of a polynomial with linear and cubic homogeneous parts.</li>
<li>Varying the radius along every tangent direction identifies those parts separately, giving \(a=a'\) and \(d=d'\). Both coefficient vectors are tangent, so no invisible normal component remains.</li>
<li>The recovery identity then gives \(b=b'\), exactly the original arrow and complementary-color rule. The converse follows directly from the formula.</li>
<li>For a proper rotation \(R\), \((Rb)\times(Ra)=R(b\times a)\). The radial bumps and dot products also commute with rotation. Thus each oriented field is the scalar pullback of the same prototype; no independent vector channel travels between tiles.</li>
<li>The local correspondence holds on every capacity-legal patch, hence on every full tiling. The known Chair44 hierarchy theorem applies to the decoded arrows and excludes a decorated translation period. The infinite conclusion does not follow merely from the finite audit.</li>
</ol>
<p>The exact audit checks all \(864\) facing-panel direction/color cases and all \(3{,}000\) relative rotation/translation cases in the full face-neighbor range. It recovers exactly \(44\) legal face neighbors. The field matches on the substitution patches with \(1,8,64,512\) chairs. <a href="../../research/spectral-tiling/chair-boundary-field.json">Construction and contact receipt</a>.</p>
<p>Equal scalar values give equal tangential derivatives, and the two zero normal derivatives cancel flux. The prescribed collar profiles also have identical even normal extensions across a matched seam. These are static multiple-frequency fields, not solutions of one global Helmholtz equation.</p>
<h2 id="spectrum">Which modes occur?</h2>
\[ -\Delta\phi_k=\mu_k\phi_k,\qquad\partial_\nu\phi_k=0,\qquad u=\sum_{k=0}^{\infty}c_k\phi_k,\qquad c_k=\int_\Omega u\phi_k\,dx. \]
<p>The ordinary Neumann eigenbasis is orthonormal in \(L^2(\Omega)\). This smooth field has convergence in the Neumann form norm, equivalent to \(H^1\), and its boundary traces converge in \(H^{1/2}\). Every collar is odd under tangential inversion, so its integral is zero. Consequently the coefficient of the constant mode is exactly \(c_0=0\).</p>
<p>There is also a regular exact subfamily:</p>
\[ \phi_m(x)=\frac{2^{r(m)/2}}{\sqrt7}\prod_{i=1}^{3}\cos(\pi m_ix_i),\qquad \mu_m=\pi^2\sum_{i=1}^{3}m_i^2,\qquad m\in\mathbb N_0^3, \]
<p>where \(r(m)\) counts nonzero coordinates. Every boundary plane has an integer coordinate, so the normal sine derivative vanishes. Orthogonality and the norm follow by subtracting the missing unit cube from the full cube. This is a subfamily of the chair spectrum, not its full basis or aperiodicity test. The FEM computation uses low members as independent numerical controls.</p>
<p>The numerical eigenfunctions have arbitrary signs and noncanonical bases inside multiple eigenspaces. Individual coefficients depend on those choices; the squared norm captured by a whole eigenspace does not.</p>
<div class="chair-viewer" id="chair-viewer">
<p id="chair-viewer-status" role="status">Loading exact field and numerical modes…</p>
<div class="chair-controls"><label for="chair-mode">Select a numerical mode<select id="chair-mode"></select></label><label for="chair-scale">Horizontal scale<select id="chair-scale"><option value="pi2">Divided by squared pi</option><option value="raw">Eigenvalue</option></select></label><label for="chair-range">Spectrum range<select id="chair-range"><option value="low">Lowest modes</option><option value="full">All computed modes</option></select></label></div>
<svg id="chair-spectrum" viewBox="0 0 932 160" role="group" aria-label="Neumann eigenvalues on a proportional real axis"></svg><p id="chair-axis-label" class="chair-axis"></p>
<div class="chair-views"><div class="chair-view"><h4>Prescribed total field</h4><div id="chair-exact-view"></div><figcaption>Surface samples from the exact formula. Drag to rotate; each copy carries this field in its local coordinates.</figcaption></div><div class="chair-view"><h4>Selected numerical eigenfunction</h4><div id="chair-numerical-view"></div><figcaption id="chair-numerical-caption"></figcaption></div></div>
<div class="chair-controls"><button id="chair-reset-camera" type="button">Reset camera</button></div><div id="chair-mode-detail" class="chair-detail" aria-live="polite"></div>
<p class="small">The plots show surface traces. The numerical mesh contains the full solid, but interior slices are not displayed. Numerical Neumann conditions are imposed weakly; the plotted piecewise-linear normal derivative need not vanish pointwise.</p></div>
<h3>What the truncations retain</h3>
<p>Two nested tetrahedral meshes have \(NODES0\) and \(NODES1\) nodes. They have exact volume \(7\), and the largest positive-mode relative matrix residual is below \(1.1\times10^{-13}\). The largest last-refinement relative eigenvalue movement is about \(MOVEMENT\%\), without a continuum error enclosure. For the finer mesh:</p>
<div class="scroll"><table><thead><tr><th>Modes retained</th><th>Sampled squared mass norm captured</th><th>Largest sampled boundary error / target peak</th></tr></thead><tbody>NUMERIC</tbody></table></div>
<p>The localized carriers put substantial weight beyond this low spectrum. These finite numerical projections do not give an exact matching palette or a certified tolerant one. The sampled target itself is a piecewise-linear interpolant of formula values.</p>
<h2 id="finite">Finite-mode limits and a different tolerance rule</h2>
<p>The target is nonzero and vanishes on an open set in the connected interior of the chair. A finite sum of Laplacian eigenfunctions is real analytic in that interior, so it cannot equal this field. The exact carrier necessarily has infinitely many modes. This does not rule out another exact finite-mode construction, which remains unresolved here.</p>
<p>A separate finite-mode existence result uses a fixed \(L^2\) tolerance on each shared unit panel, without extra constraints at isolated edges or vertices. The oriented trace alphabet is finite, and the profile identity gives a positive minimum separation \(d\) between distinct symbols. Trace convergence supplies one finite continuum cutoff \(N\) with error below \(d/4\) on every panel of every oriented state. Intended neighbors then have discrepancy below \(d/2\); forbidden neighbors have discrepancy above \(d/2\). Accepting exactly those contacts within the tolerance preserves the original discrete rule.</p>
<p>All finite sums still satisfy Neumann conditions. This changed rule gives approximate seams, rather than continuous gluing. No cutoff has been computed or certified, and the displayed FEM truncations are not asserted to meet it.</p>
<h2 id="sources">Sources and reproducibility</h2>
<ol class="refs"><li id="ref-gs">Goodman–Strauss. <a href="https://arxiv.org/html/2609.24779v1#S2">Notes on a strongly aperiodic monotile in \(E^3\)</a>, Section 2 and Figures 2 and 5. The cited preprint supplies the arrow decoration and its hierarchy theorem; the scalar boundary-field transfer is derived here.</li><li>Tsiokos. <a href="https://arxiv.org/html/2609.19214v1">A strongly aperiodic monotile in three dimensions</a>. Original Chair44 construction.</li></ol>
<p class="small"><a href="../../research/spectral-tiling/chair_boundary_field.mjs">Exact carrier and audit</a> · <a href="../../research/spectral-tiling/chair_modal_projection.py">Tetrahedral modes and projections</a> · <a href="../../research/spectral-tiling/chair-modal-projection.json">Numerical receipt</a> · <a href="../../research/spectral-tiling/verify_chair_field.py">Independent verifier</a> · <a href="../../research/spectral-tiling/chair-field-verification.json">Verification receipt</a>. The given arrow table is the repository's existing <a href="../../3d-reptiles/chair/chair44.js">Chair44 transcription</a>. No tiling engine or learned marking is modified. This is a specialized continuum transfer, without a GCTS frontier-search conformance claim.</p>
<footer><a href="sphinx-boundary-modes.html">Sphinx construction</a> · <a href="l-triomino-boundary-modes.html">L-triomino construction</a> · <a href="spectral-tiling-study.html">Broader spectral Notes</a>.</footer>
'''
    fine=projection['mesh_runs'][-1]
    rows=''.join(r'<tr><td>\('+str(t['modes'])+r'\)</td><td>\('+f"{100*t['sampled_squared_mass_fraction']:.2f}"+r'\%\)</td><td>\('+f"{100*t['maximum_sampled_boundary_error_over_target_peak']:.2f}"+r'\%\)</td></tr>' for t in fine['truncations'])
    for key,value in [('NODES0',f"{projection['mesh_runs'][0]['diagnostics']['nodes']:,}"),('NODES1',f"{fine['diagnostics']['nodes']:,}"),('MOVEMENT',f"{100*projection['maximum_last_refinement_relative_eigenvalue_change']:.2f}"),('NUMERIC',rows)]:
        head=head.replace(key,value)
    page=head+'\n<script id="chair-field-data" type="application/json">'+json.dumps(construction,separators=(',',':'))+'</script>\n<script type="module" src="../../research/spectral-tiling/chair-field-viewer.js?v=1"></script>\n</main></body></html>\n'
    path=DOCS/'chair-boundary-modes.html';path.write_text(page)
    print(json.dumps({'page':str(path.relative_to(ROOT.parents[1])),'bytes':len(page.encode()),'prototype_fields':1,'numerical_modes':60}))


if __name__=='__main__':main()
