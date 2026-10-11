#!/usr/bin/env python3
"""Build the sphinx research page from executed construction/projection data."""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parent
DOCS=ROOT.parents[1]/'docs/projects'


def main():
    construction=json.loads((ROOT/'sphinx-boundary-palette.json').read_text())
    projection=json.loads((ROOT/'sphinx-modal-projection.json').read_text())
    assert construction['status']==projection['status']=='passed'
    head=(DOCS/'l-triomino-boundary-modes.html').read_text().split('</head>')[0]
    head=re.sub(r'<title>.*?</title>','<title>Sphinx Notes: boundary matching and modes</title>',head)
    head=re.sub(r'<meta name="description".*?>','<meta name="description" content="Exact Neumann fields on the sphinx encode an aperiodic finite palette; infinite modal expansions, numerical eigenfunctions and the separate substitution problem.">',head)
    head+='\n<link rel="stylesheet" href="../../research/spectral-tiling/spectrum-viewer.css">\n'
    head+='''<style>.field-controls{font:14px system-ui,sans-serif;margin:18px 0}.field-controls select{max-width:100%;padding:10px;border:1px solid #b4c9c2;border-radius:5px;background:white;font:15px system-ui,sans-serif}.field-demo{border:1px solid #b4c9c2;background:white;border-radius:10px;padding:20px}.field-demo canvas{display:block;max-width:100%;height:auto;margin:auto}.field-demo p{overflow-x:auto;overflow-y:hidden;padding-bottom:5px}.field-demo figcaption{margin-top:10px}.coefficient-box{padding:12px 16px;background:#edf1e9;margin-top:14px}.coefficient-box p{font:14px/1.6 system-ui,sans-serif;margin:6px 0}</style></head><body><main>'''
    rows=''.join('<tr>'+''.join(r'<td>\('+str(x)+r'\)</td>' for x in [i]+list(colors))+'</tr>'
                 for i,colors in enumerate(construction['source_color_tuples_W_E_S_N'],1))
    edges=''.join(r'<tr><td>\(e_'+str(i)+r'\)</td><td>\('+str(tuple(p))+r'\to'+str(tuple(q))+r'\)</td></tr>'
                  for i,(p,q) in enumerate(construction['geometry']['unit_edges_ccw']))
    fine=projection['mesh_runs'][-1]
    numeric=''.join(r'<tr><td>\('+str(t['modes'])+r'\)</td><td>\('+f"{100*t['sampled_target_mass_fraction']:.2f}"+r'\%\)</td><td>\('+f"{100*t['maximum_sampled_boundary_value_error_over_peak']:.2f}"+r'\%\)</td></tr>'
                    for t in fine['states'][0]['truncations'])
    movement=100*projection['maximum_last_refinement_relative_eigenvalue_change']
    nodes=[r['diagnostics']['nodes'] for r in projection['mesh_runs']]
    body=r'''
<nav><a href="spectral-tiling-study.html">Spectral tiling Notes</a> / Current sphinx study</nav>
<p class="eyebrow">Sphinx · updated 11 October 2026</p>
<h1>The sphinx: boundary matching and modes</h1>
<p class="lead">An explicit palette of twenty-two smooth Neumann fields forces aperiodicity of the decorated sphinx tiling. Each field has an infinite expansion in ordinary sphinx eigenmodes. Finite sums suffice under a separate tolerance rule. Enforcing the sphinx substitution itself, or using finitely many modes with exact matching, remains unfinished work.</p>
<div class="tools"><a href="#result">Precise result</a><a href="#fields">Exact fields</a><a href="#proof">Why matching forces aperiodicity</a><a href="#modal">Modes and coefficients</a><a href="#tolerance">Finite-mode tolerance result</a><a href="#hierarchy">The sphinx substitution route</a></div>
<h2 id="result">What is established</h2>
<div class="callout"><p>Place exact sphinx hexiamonds on the triangular lattice. Allow the six rotations by multiples of \(\pi/3\), exclude reflections, and require each tile to carry one of twenty-two fixed total fields. Requiring scalar boundary values to match admits infinite tilings and excludes every nonzero translation period of the <strong>decorated tiling</strong>.</p></div>
<p>The ordinary boundary condition is homogeneous Neumann for every field: \(\partial_\nu u=0\). The allowed palette is an additional discrete restriction on modal coefficients. Neumann conditions alone, or permission to choose arbitrary superpositions, do not force aperiodicity.</p>
<p>In this construction the tile outlines still repeat. The field states carry the nonperiodic information. It encodes the known Jeandel–Rao system through pairs of sphinxes; it does not enforce the sphinx substitution. A construction whose underlying sphinx arrangement is forced to follow that hierarchy is the second route below.</p>
<div class="scroll"><table><thead><tr><th>Question</th><th>Current answer</th></tr></thead><tbody>
<tr><td>Every physical tile an exact sphinx?</td><td>Yes; no auxiliary geometric tiles in this construction.</td></tr>
<tr><td>Dirichlet or Neumann boundary condition?</td><td>Exact homogeneous Neumann, on every boundary segment.</td></tr>
<tr><td>Infinite existence and forced aperiodicity?</td><td>Yes for the finite decorated palette, under the declared placement rules.</td></tr>
<tr><td>Finite palette of fields?</td><td>Yes, twenty-two.</td></tr>
<tr><td>Finite number of eigenmodes per field?</td><td>The exact profiles require infinitely many; finite sums suffice under the separate tolerance rule below.</td></tr>
<tr><td>One frequency, or matching separately at every frequency?</td><td>No such result is established.</td></tr>
<tr><td>Forcing the natural sphinx hierarchy?</td><td>Published matching rules exist, but their boundary-only modal transfer is not completed here.</td></tr>
</tbody></table></div>
<h2 id="fields">Independent values on the eight unit segments</h2>
<p>Use the triangular-lattice basis \(b_1=(1,0)\), \(b_2=(1/2,\sqrt3/2)\). Axial coordinates \((a,b)\) mean \(ab_1+bb_2\). The polygon vertices, in counterclockwise order, are</p>
\[ (0,0),\ (3,0),\ (2,1),\ (1,1),\ (0,2). \]
<p>Its area is \(3\sqrt3/2\), and it consists of six unit equilateral triangles. Split its boundary into eight unit segments, keeping their counterclockwise directions.</p>
<details><summary>All eight segment coordinates</summary><div class="scroll"><table><thead><tr><th>Segment</th><th>Directed endpoints, in axial coordinates</th></tr></thead><tbody>EDGES</tbody></table></div></details>
<p>Define the even compact bump and asymmetric profile</p>
\[ K(z)=\begin{cases}\exp\!\left(1-\dfrac{1}{1-z^2}\right),&|z|&lt;1,\\0,&|z|\ge1,\end{cases}\qquad
G_\sigma(s)=K\bigl(4(s-\tfrac12)\bigr)e^{2\sigma(s-1/2)},\quad\sigma\in\{-1,1\}. \]
<p>For physical segment endpoints \(p_j,q_j\), outward unit normal \(\nu_j\), and unit tangent \(\tau_j=q_j-p_j\), set</p>
\[ s_j(x)=(x-p_j)\cdot\tau_j,\qquad r_j(x)=-(x-p_j)\cdot\nu_j,\qquad
u_{a,\sigma}(x)=\sum_{j=0}^{7}a_jG_\sigma\bigl(s_j(x)\bigr)K\bigl(8r_j(x)\bigr). \]
<p>The middle-half support stays away from every vertex. The exact squared distance from a support segment to any other side is at least \(3/64\); the squared separation between distinct support segments is at least \(1/16\). Inward collars of width \(1/8\) therefore avoid other sides and have disjoint open supports. On segment \(j\), the boundary value is exactly \(a_jG_\sigma\), and its normal derivative is exactly zero because \(K'(0)=0\). Every field is smooth up to the boundary and zero near the corners.</p>
\[ G_{-1}(s)=G_1(1-s),\qquad \frac{G_1(s)}{G_{-1}(s)}=e^{4(s-1/2)}\quad(1/4&lt;s&lt;3/4). \]
<p>Thus equal nonzero profiles determine both their amplitude and their direction. Equal boundary values also give equal tangential derivatives; zero outward flux on both sides supplies flux cancellation. The glued fields are static multiple-eigenvalue superpositions.</p>
<h3>The finite coefficient palette</h3>
<p>For each index \(t\) with colors \((w,e,s,n)\), use</p>
\[ V_r(c)=1+4r+c\quad(r=0,1),\qquad H_r(c)=9+4r+c\quad(r=0,1,2),\qquad I_j(t)=100+3(t-1)+j\quad(j=0,1,2). \]
\[ A_t=u_{a_t^A,1},\quad a_t^A=(H_0(s),H_1(s),H_2(s),I_0(t),I_1(t),I_2(t),V_1(w),V_0(w)), \]
\[ B_t=u_{a_t^B,-1},\quad a_t^B=(H_2(n),H_1(n),H_0(n),I_2(t),I_1(t),I_0(t),V_0(e),V_1(e)). \]
<p>The eleven color quadruples are Jeandel–Rao's Figure 4; their Theorem 3 establishes infinite existence and aperiodicity for that matching system. <a href="#ref-jr">[1]</a> The encoding on exact sphinx shapes and its reduction are derived here.</p>
<details><summary>The eleven source color quadruples</summary><div class="scroll"><table><thead><tr><th>\(t\)</th><th>\(w\)</th><th>\(e\)</th><th>\(s\)</th><th>\(n\)</th></tr></thead><tbody>COLORS</tbody></table></div></details>
<p>All amplitudes are fixed physical values. Independent normalization, sign changes, or arbitrary additional linear combinations would change the permitted palette.</p>
<figure><img src="../../research/spectral-tiling/sphinx-boundary-palette.png" loading="lazy" alt="All twenty-two exact Neumann field states on the sphinx, with each unit boundary amplitude labeled."><figcaption>The entire palette. One shared power color scale makes the smaller external values visible; it does not change their listed amplitudes. These fields are sampled from their exact formulas.</figcaption></figure>
<h2 id="proof">Why boundary equality forces aperiodicity</h2>
<figure><img src="../../research/spectral-tiling/sphinx-boundary-forced-pair.png" loading="lazy" alt="Two sphinxes form a parallelogram; three uniquely labeled connector profiles force the pair."><figcaption>The first pair. In axial coordinates the partner is placed by \(x\mapsto(3,2)-x\). Orange segments carry internal connector labels; teal segments carry external color and position labels.</figcaption></figure>
<ol>
<li><strong>The connector forces a unique mate.</strong> Each \(I_0(t)\) occurs once per state and cannot match any external amplitude. Its value forces the same index. The segment normals force a relative half-turn, and profile reversal forces the opposite field role. Aligning that segment fixes the translation: \(A_t\) can only mate with \(B_t\) placed by \(x\mapsto(3,2)-x\).</li>
<li><strong>Every tile belongs to one legal pair.</strong> The two sets of six elementary triangles are disjoint and fill the parallelogram spanned by \(3b_1\) and \(2b_2\). The other two internal traces agree. The pairing is reciprocal, so every legal plane tiling partitions into these pairs.</li>
<li><strong>Pairs align and cannot stagger.</strong> Direction-specific amplitude ranges, asymmetric profiles, and position indices restrict legal contacts to a common orientation and axial offsets \((\pm3,0)\) or \((0,\pm2)\). The connected edge-contact graph forces one common parallelogram lattice. All six relative rotations and every possible integer edge-sharing translation are included in the audit.</li>
<li><strong>The decoded matching problem is exact.</strong> Read the four colors of each pair. Trace matching becomes exactly east-to-west and north-to-south color equality. Conversely, any tiling of the cited eleven-state system expands into a legal sphinx-field tiling.</li>
<li><strong>A decorated period would give a forbidden decoded period.</strong> A translation preserving tiles and fields preserves the recognizable pairs and their lattice, and hence gives a nonzero integer period of the decoded system. The cited theorem excludes it and supplies at least one infinite tiling.</li>
</ol>
<p>The <a href="../../research/spectral-tiling/sphinx-boundary-palette.json">exact contact receipt</a> verifies every forced mate and all \(13{,}310\) candidate contacts between oriented pairs. Exactly \(136\) directed contacts pass, all belonging to the intended matching table. This checks the finite reduction; the infinite conclusion uses the source theorem.</p>
<div class="callout caution"><p><strong>Scope of the result.</strong> Erasing the fields gives a periodic arrangement of sphinx pairs, with periods \(3b_1\) and \(2b_2\). Reflected fields and freely rotated or nonlattice placements are outside the model. No minimum palette size, intrinsic spectral test, or natural sphinx-substitution claim follows from this construction.</p></div>
<h2 id="modal">How these fields use the sphinx spectrum</h2>
\[ -\Delta\phi_k=\mu_k\phi_k,\qquad\partial_\nu\phi_k=0,\qquad
u=\sum_{k=0}^{\infty}c_k\phi_k,\qquad c_k=\int_\Omega u\phi_k. \]
<p>Use an orthonormal ordinary Neumann eigenbasis on the exact sphinx. Since the constructed fields belong to \(H^1(\Omega)\), their sums converge in the Neumann form norm, equivalent to the \(H^1\) norm. Boundary traces converge in \(H^{1/2}(\partial\Omega)\). The prescribed smooth target traces give the exact matching rule.</p>
<p>A finite eigenmode sum is real analytic along an open straight side, by even reflection of each Neumann Helmholtz eigenfunction. Our nonzero profile vanishes on open intervals of that same side, so the identity theorem excludes a finite representation. This obstruction concerns the present compact-profile encoding; a different finite-mode palette with exact matching is still possible in principle and remains unresolved here.</p>
<div class="field-demo"><div class="field-controls"><label for="palette-state">Allowed total field state </label><select id="palette-state"></select></div>
<canvas id="palette-field" width="600" height="369" role="img" aria-label="Exact total boundary field on the sphinx"></canvas>
<p id="palette-amplitudes" class="small"></p><p id="palette-truncation" class="small"></p>
<p class="small">The exact total field uses a fixed absolute color scale, with a power transform. The individual eigenfunction below uses its own peak normalization for display.</p></div>
<h3 id="spectrum">Click the spectrum to inspect a numerical mode</h3>
<p>These \(180\) Neumann FEM modes are the same basis used for the projections below. Horizontal positions are proportional to eigenvalues; nearby nodes are stacked for selection. Click a node to see its numerical eigenfunction and its coefficient in the selected total field. Coefficients refer to mass-normalized FEM vectors; individual coefficients depend on the chosen basis inside a multiple eigenspace.</p>
VIEWER
<figure><img src="../../research/spectral-tiling/sphinx-modal-truncations.png" loading="lazy" alt="Exact sphinx field samples compared with the first sixty-four and one hundred eighty Neumann FEM modes."><figcaption>Exact sampled targets and finite FEM projections, on one absolute color scale. Truncation disturbs the boundary values; these approximate palettes have no proved tiling or aperiodicity property.</figcaption></figure>
<p>For \(A_1\), the finer mesh gives:</p>
<div class="scroll"><table><thead><tr><th>Retained modes</th><th>Fraction of sampled squared \(L^2\) norm captured</th><th>Largest sampled boundary error / target peak</th></tr></thead><tbody>NUMERIC</tbody></table></div>
<p>Two meshes have \(NODES0\) and \(NODES1\) nodes. The largest last-refinement relative eigenvalue movement among the retained modes is about \(MOVEMENT\%\); positive-mode relative matrix residuals are below \(1.6\times10^{-12}\). These diagnostics do not enclose continuum errors. Capturing about \(96\%\) of the sampled squared norm still leaves about \(16\%\) maximum sampled boundary error for \(A_1\). Exact matching cannot be inferred from that approximation. FEM Neumann conditions are imposed weakly; the plotted piecewise-linear normal derivative need not vanish pointwise.</p>
<h3 id="tolerance">A finite-mode result with a different matching rule</h3>
<p>Replace exact value equality by a fixed \(L^2\) tolerance on each shared unit segment; isolated vertex contacts impose no extra condition in this model. Under this changed rule, sufficiently large finite sums of <em>continuum</em> Neumann eigenmodes can preserve the full matching table and hence still force decorated aperiodicity. This is an existence deduction, without a computed or certified cutoff.</p>
<p>There are finitely many oriented unit-trace symbols in the exact palette. Distinct symbols have positive \(L^2\) distance by the profile identity above. Let their minimum separation be \(d&gt;0\). Spectral convergence in \(H^1\), followed by the trace theorem, supplies one finite cutoff \(N\) for which every state and every segment has trace error below \(d/4\). For an intended match the two truncated traces then differ by less than \(d/2\); for a forbidden match they differ by more than \(d/2\):</p>
\[ \text{compatible: }\ \|\gamma u_N-\gamma v_N\|_{L^2}&lt;d/2,
\qquad \text{incompatible: }\ \|\gamma u_N-\gamma v_N\|_{L^2}&gt;d/2. \]
<p>Thus the tolerance \(d/2\) recovers precisely the proved discrete contact rules, and all finite sums still satisfy Neumann conditions. This does not yield continuous gluing across the seams. It also does not certify the displayed FEM truncations: continuum coefficient and trace-error bounds are required to give an actual cutoff. Exact finite-mode equality remains unresolved.</p>
<h2 id="hierarchy">A second route: enforce the sphinx substitution itself</h2>
<p>Goodman–Strauss proves that a colored tile set enforces the sphinx substitution. It recomposes the geometry into sphinx-like bodies, edge tiles and vertex tiles. <a href="#ref-gs">[2, pp. 2–6]</a> Its diagrams carry skeleton position and orientation, the supertile's position in its parent, and vertex-wire termination information. The termination channel prevents signals from extending indefinitely without the required hierarchical junction.</p>
<p>This is stronger geometric information than the paired construction above. Transferring it to fields on <em>exact</em> sphinx boundaries requires a complete finite table including edge and vertex compatibility, followed by a proof that every allowed field tiling decodes to the original auxiliary system and conversely. Dropping the auxiliary pieces or assigning colors from the seven illustrated sphinx-like bodies alone does not establish that equivalence. That transfer has not been completed or counted here.</p>
<p>The analytic carrier is available: put each finite compatibility symbol into its own tangential subinterval, using even inward bumps to preserve Neumann conditions. Vertex information can be transmitted along near-vertex subintervals while keeping the field zero at the actual corner. What remains is the verified combinatorial recoding, rather than a new way to expand boundary profiles in modes.</p>
<p>The elementary-triangle eigenfamilies already in the broader Notes describe a regular part of the sphinx spectrum. They glue compatibly under their reflection transport, but the existence of such global functions does not select the substitution or exclude periodic sphinx tilings.</p>
<h2 id="sources">Sources and reproducibility</h2>
<ol class="refs">
<li id="ref-jr">Jeandel and Rao. <a href="https://arxiv.org/html/1506.06492v4#S4.F4">An aperiodic set of 11 Wang tiles</a>. Figure 4 and Theorem 3 supply the matching system encoded by the sphinx pairs.</li>
<li id="ref-gs">Goodman–Strauss. <a href="https://arxiv.org/html/1608.07168v1">Matching Rules for the Sphinx Tiling Substitution</a>. The auxiliary colored-tile construction is a source for the separate hierarchy route, not the theorem behind our twenty-two-state palette.</li>
</ol>
<p class="small"><a href="../../research/spectral-tiling/sphinx_boundary_palette.py">Exact construction and contact audit</a> · <a href="../../research/spectral-tiling/sphinx_modal_projection.py">Two-mesh mode projections</a> · <a href="../../research/spectral-tiling/sphinx-modal-projection.json">Coefficients and numerical receipt</a> · <a href="../../research/spectral-tiling/verify_sphinx.py">Independent verifier</a> · <a href="../../research/spectral-tiling/sphinx-verification.json">Verification receipt</a>. This is a specialized continuum construction and contact audit, with no GCTS frontier-search conformance claim.</p>
<footer>Current focus: sphinx boundary matching. <a href="l-triomino-boundary-modes.html">Earlier L-triomino construction</a> · <a href="spectral-tiling-study.html">Broader spectral Notes</a>.</footer>
'''
    old=(DOCS/'spectral-tiling-study.html').read_text()
    start=old.index('<div class="spectrum-viewer" id="spectrum-viewer"')
    viewer=old[start:old.index('<noscript>',start)]
    # The original viewer's trailing note closes this outer div after noscript.
    viewer=viewer[:viewer.rindex('<p class="spectrum-note">')]
    viewer=viewer.replace('<option value="remainder">Without identified family matches</option><option value="all">All computed modes</option>',
                          '<option value="all">All computed modes</option><option value="remainder">Without the known constant</option>')
    viewer=re.sub(r'<p class="spectrum-note">The initial filter.*?</p>','',viewer)
    viewer=viewer.replace('<div id="spectrum-mode-detail" aria-live="polite"></div>',
                          '<div id="spectrum-mode-detail" aria-live="polite"></div><div id="palette-coefficient" class="coefficient-box" aria-live="polite"></div>')
    viewer+='<p class="spectrum-note">Each eigenfunction is displayed divided by its largest absolute nodal value. Its sign and basis inside a multiple eigenspace are noncanonical. These are uncertified FEM estimates; last-refinement movements are diagnostics, not continuum error bounds.</p></div>'
    for key,value in [('EDGES',edges),('COLORS',rows),('NUMERIC',numeric),('VIEWER',viewer),
                      ('NODES0',f'{nodes[0]:,}'),('NODES1',f'{nodes[1]:,}'),('MOVEMENT',f'{movement:.2f}')]:
        body=body.replace(key,value)
    payload={'states':construction['palette'],'polygon':construction['geometry']['physical_polygon'],
             'edges':construction['geometry']['unit_edges_ccw'],'projections':fine['states']}
    page=head+body+'\n<script id="mode-data" type="application/json">'+json.dumps(projection['eigenfunction_viewer'],separators=(',',':'))+'</script>'
    page+='\n<script id="palette-data" type="application/json">'+json.dumps(payload,separators=(',',':'))+'</script>'
    page+='\n<script src="../../research/spectral-tiling/spectrum-viewer.js?v=sphinx-boundary"></script>'
    page+='\n<script src="../../research/spectral-tiling/sphinx-palette-viewer.js?v=1"></script>\n</main></body></html>\n'
    (DOCS/'sphinx-boundary-modes.html').write_text(page)
    print(json.dumps({'page':'docs/projects/sphinx-boundary-modes.html','states':len(payload['states']),'modes':180,'bytes':len(page.encode())}))


if __name__=='__main__':main()
