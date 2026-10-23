# Full tile family and four-dimensional perspectives

A finite patch of 7,921 tiles is generated from the H/T/P/F substitution rules in Craig S. Kaplan's `hatviz`. Its shared-vertex graph is coherently lifted to four integer lattice coefficients. The browser changes a projection of this fixed object; no tile is moved separately.

Tile family follows the entire Chevron–Hat–Turtle–Comet deformation. Other perspectives provides a two-parameter map and six four-parameter coordinate charts covering all real screen planes. Every screen image is two-dimensional. General perspectives can overlap and can give reflected tiles different shapes. Colors, reflection classes, selected tile identity, and shared edges remain attached to the fixed object. At equal edge lengths the polygon also admits periodic tilings; this particular patch retains its substitution arrangement.

This is a known geometric substitution visualization. It does not run a point-value search, GCTS, RL, or matching-rule learner. The shared algorithm contract's search scheduler and learning requirements are not invoked, and the separate `lifted-search` engine is unchanged.

## Fixed coordinates and full family

Integer coefficients \((p,q,r,s)\) encode two perpendicular triangular planes, with Cartesian coordinates

\[
U=p+q/2+i\sqrt3q/2,\qquad V=\sqrt3r/2+i(r/2+s).
\]

The coefficient basis is oblique, rather than an orthonormal cubic basis. The original family uses the orthogonal screen projection

\[
P_\theta(U,V)=\cos\theta\,U+\sin\theta\,V,\qquad 0\leq\theta\leq\pi/2.
\]

The slider fraction is \(m=1-2\theta/\pi\). Chevron, Hat, equal edges, Turtle, and Comet occur at \(m=0,1/3,1/2,2/3,1\), respectively. At the limits one edge class vanishes, so some of the fourteen fixed vertex labels coincide in the image. The limiting polygons still have positive area. The single-tile view labels all fourteen vertices relative to the first vertex of the selected tile, using MathJax. Those labels remain constant.

## Two-parameter map and lattice alignments

The map adds a relative rotation:

\[
P_{\theta,\varphi}(U,V)=\cos\theta\,U+\sin\theta e^{i\varphi}V.
\]

These screen rows are orthonormal in Cartesian coordinates. Up to a rotation of the screen, this is the complete complex-linear family, a complex projective line with two real degrees of freedom. The original family is the line \(\varphi=0\). Each vertical end of the rectangular map represents one plane, up to screen rotation. It is not the complete family of real screen planes.

Let \(\zeta=e^{i\pi/3}\) and \(z=\tan\theta e^{i\varphi}\). Apart from the nonzero overall factor, the projected coefficient lattice is

\[
\mathbb Z[\zeta]+ze^{i\pi/6}\mathbb Z[\zeta].
\]

It is a discrete rank-two lattice exactly when

\[
ze^{i\pi/6}\in\mathbb Q(\zeta),
\quad\text{equivalently}\quad
x=\sqrt3\operatorname{Re}z\in\mathbb Q,\qquad y=\operatorname{Im}z\in\mathbb Q.
\]

To see necessity, a discrete superlattice of the first triangular lattice has finite index, so both additional generators have rational coordinates in its basis. Sufficiency follows by clearing denominators. The resulting lattice is triangular: the sum of these two commensurate Eisenstein modules is a fractional ideal in the principal ideal domain of Eisenstein integers. Both limiting planes are also aligned. Otherwise the image is dense: its closure is invariant under a sixty-degree rotation, which rules out a proper positive-dimensional closed subgroup.

Thus the alignment locus is countable and dense, not a collection of continuous curves. Teal dots show only a finite sample. A named example or dot retains its exact rational data; free dragging is not certified as either rational or irrational from floating-point values. The overlay uses an exact integer lattice basis before floating-point rendering. Fine lattices require zooming in; the display reports this instead of plotting an excessive number of dots. Lattice alignment does not imply translational periodicity of the tiling.

## Four degrees of freedom

Fixing two members of an orthonormal four-frame leaves one continuous angle for the other two members (and a disconnected reflection choice). That rotation alone leaves projection onto the fixed first plane unchanged. To change the screen plane, there are four real degrees of freedom: locally its spanning vectors can be written

\[
e_1+a e_3+b e_4,\qquad e_2+c e_3+d e_4.
\]

The advanced panel uses coefficient-coordinate covectors instead. Choose any two of the four columns as pivots, put the identity in them, and enter the other four coefficients. For the first chart the matrix is

\[
C=\begin{pmatrix}1&0&a&b\\0&1&c&d\end{pmatrix}.
\]

There are six choices of pivot pair. Every rank-two matrix has a nonzero two-column minor, so these charts cover all planes. We convert the row covectors to Cartesian coordinates and apply Gram–Schmidt. This gives an actual orthogonal projection with an orthonormal screen basis, rather than a shear. Changing charts with the same four inputs generally chooses a different plane; it does not preserve the old view automatically.

In each chart, the image of the entire coefficient lattice is discrete of rank two exactly when all four free entries are rational. Indeed it contains the two identity generators; discreteness forces finite index over their lattice, and conversely denominators can be cleared. An invertible screen change during orthonormalization preserves discreteness. This gives a countable dense locus in the four-dimensional Grassmannian. These aligned lattices need not be triangular. An irrational entry rules out discreteness of rank two, but outside the complex-linear slice this need not mean density in the whole plane.

Decimals and fractions are parsed as exact rationals. The panel also accepts explicitly irrational square-root examples. For rational \(x,y\), the two-parameter family in the first matrix chart has

\[
(a,b,c,d)=(A,-B,B,A+B),\qquad A=x/3-y,\quad B=x/3+y.
\]

The original family is the line \((t,-t,t,2t)\), where \(t=\tan\theta/\sqrt3\). These are coordinates of the same plane, up to rotation of its screen basis.

## Camera framing and material marks

Fixed reflected layout uses a different fixed material point in each of the 1,009 reflected tiles. All these points lie in one affine plane in four dimensions. One global similarity makes their images stationary across the full original family, while preserving shared edges. Numerical checks cover the whole interval. The exact certificate that these points are interior to their triangulated tiles applies only between Hat and Turtle. Some points leave the projected polygon beyond that interval, so white interior marks are hidden there. No claim about every tile of an infinite tiling is made.

A non-planar polygon boundary does not determine a unique interior. The construction fixes twelve triangles spanning each reflected boundary and holds each mark's barycentric coordinates constant. See the [construction and exact finite-patch certificate](../../research/hat-turtle-fixed-points/README.md).

Steady reflected layout instead fits one orientation-preserving similarity to reflected vertex averages relative to their Hat positions. Small residual motion remains. Fixed edge directions uses the raw coordinate orientation. These are camera choices only. General perspective exploration uses its own fixed framing, without the stationary-mark camera.

`validate-view.mjs` checks labels, the least-squares camera, and edge-length ratios. Its rank witness rules out using the same local point in all identically oriented reflected tiles, but does not rule out the different material points used here.

## Validation and reproduction

- `node validate-perspectives.mjs`: full-family special stops, limiting polygons, congruence of all tiles at nine samples, exact lattice containment, orthonormality and lattice bases in all six matrix charts, and agreement between the two-parameter slice and four-parameter projections. Writes `perspectives-validation.json`.
- `python3 validate-family.py`: independent shared-edge, overlap, crossing, area and orientation checks at nine nondegenerate full-family samples. Writes `family-geometry-validation.json`. Endpoint collapsed edges are handled separately by the preceding test.
- `node validate-fixed-marks.mjs`: stationarity across 101 full-family samples. Writes `fixed-marks-validation.json`; this does not extend the interior certificate.
- `python3 ../../research/hat-turtle-fixed-points/certify.py`: exact interior certificate over the Hat–Turtle interval, using the standard Python library. Its exploratory companion `check.py` requires NumPy.

Finite samples are rendering checks, not a proof for all parameters. The lattice criteria and chart completeness follow from the arguments above.

`geometry-reference.js` and `hat-reference.js` are unmodified build-time downloads from [hatviz](https://github.com/isohedral/hatviz), under the accompanying BSD license. `generate.cjs` builds `patch.json` and checks integer lifts, shared edges, connectivity, fourteen vertices, edge-class counts, edge incidence and reconstruction of the Hat patch. The lift follows [Nan Ma and Arnaud Chéritat](https://www.math.univ-toulouse.fr/~cheritat/2023-monotile/4D-lift/index.html). The full family and limiting shape names follow the [authors' monotile site](https://cs.uwaterloo.ca/~csk/hat/).

Serve this directory over HTTP; no compilation or package installation is needed. Reduced-motion preferences pause the animation initially. `validation.json` records the original patch checks.
