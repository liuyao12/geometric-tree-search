# Hat–turtle projection animation

A finite patch of 7,921 hats is generated from the H/T/P/F substitution rules in Craig S. Kaplan's `hatviz`. Its shared-vertex graph is coherently lifted to four integer lattice coordinates. The browser continuously varies one linear projection of that fixed patch; it never separately reshapes or repositions tiles.

- Plane view displays a genuine tiling patch throughout the deformation.
- Lifted view uses a third orthonormal projected coordinate and a fixed camera tilt. Projected boundaries may overlap in this view. Polygon fills are a visualization choice.
- Colors, reflection classes and selected tile identity remain fixed.
- The equal-edge midpoint admits periodic tilings as well; the animation retains its original substitution patch.
- This page is a known geometric substitution visualization, not a point-value search, GCTS, RL, matching-rule learner, or certificate of a new tiling. The shared algorithm contract's search scheduler and marking-learning requirements are therefore not invoked; no engine has been changed.

## Geometry

Integer coordinates \((p,q,r,s)\) encode two triangular lattices:

\[
u=(p+q/2,\sqrt{3}q/2),\qquad v=(\sqrt{3}r/2,r/2+s).
\]

The screen plane uses

\[
P_\theta(u,v)=\cos\theta\,u+\sin\theta\,v,
\qquad \pi/6\leq\theta\leq\pi/3.
\]

These are orthogonal projections with respect to the Euclidean metric of the two triangular planes; the integer coefficient basis is oblique. The animation does not claim that this coefficient basis is an orthonormal cubic basis. The hat appears at \(\theta=\pi/3\), the turtle at \(\theta=\pi/6\).

For the third displayed direction, the viewer uses

\[
z=\frac{-\sin\theta(u_x+u_y)+\cos\theta(v_x+v_y)}{\sqrt2}.
\]

This direction is orthogonal to both screen-plane directions. A fixed camera tilt then reveals the lifted patch.

## Provenance and reproduction

`geometry-reference.js` and `hat-reference.js` are unmodified downloads from https://github.com/isohedral/hatviz (2026-10-20), under the accompanying BSD 3-Clause license. They are build-time references, not runtime dependencies. `generate.cjs` builds `patch.json`; run it with Node.js. Its checks include integer edge lifts, all shared-edge consistency equations, connectivity, fourteen vertices and the two edge-class counts per tile, edge incidence at most two, and reconstruction of the reference hat patch. See `validation.json` for independent geometry and browser checks.

The lift follows Nan Ma and Arnaud Chéritat: https://www.math.univ-toulouse.fr/~cheritat/2023-monotile/4D-lift/index.html

Serve this directory over HTTP and open `index.html`. No compilation or package installation is needed. Browser controls include playback, endpoints and midpoint, dragging, zoom, whole-patch fit, tile selection, and a lifted view. Reduced-motion preferences pause playback initially.

## Single tile and steadier framing

The single-tile view labels all fourteen vertices with their integer triangular-basis coordinates, relative to the selected tile's first vertex. MathJax typesets the labels and coordinate explanation. Labels are constant through the animation. The lattice coefficient basis is explicitly distinguished from orthonormal Cartesian coordinates.

Steady reflected layout is a global, orientation-preserving similarity fitted to the reflected tiles' vertex-average reference points over the entire patch. It removes overall rotation, translation and scale change; it does not move tiles separately. This keeps the main spacing visually steady while preserving congruence and shared edges. Residual local motion is disclosed in the UI. It is not an exact locking of every reflected tile.

The fit minimizes

\[
\sum_i\left|g\,z_i(\theta)+t-z_i(\pi/3)\right|^2,
\qquad g,t\in\mathbb C.
\]

The reference points are used only to choose the camera. There is no claim that vertex averages or area centroids are a privileged geometric center.

`validate-view.mjs` independently checks all relative coordinate labels, the residual of the least-squares camera, and preservation of edge-length ratios. Its rank witness rules out using the **same local point** in every identically oriented reflected copy. It does not rule out choosing different local points in different copies.

## Exact stationary interior marks

The default framing now uses a different fixed material point in each reflected tile's four-dimensional triangulated surface. All 1,009 marks in this finite patch lie in one affine plane. A single similarity of the screen then keeps every mark stationary throughout the plane-view animation. Shared edges remain shared. This is exact geometry, with floating-point rendering.

The choice of surface matters: a non-planar boundary does not define a unique interior. We fix twelve triangles spanning each reflected tile's boundary, then keep each point's barycentric coordinates in its triangle constant. The exact verifier checks that all triangles remain oriented without degenerating throughout the entire hat–turtle interval, and that each mark is strictly interior to its triangle. The lift stays fixed; its image changes.

See [the construction and exact finite-patch certificate](../../research/hat-turtle-fixed-points/README.md). No assertion about every tile of an infinite tiling is made. Lifted view includes an additional varying depth coordinate and does not lock these marks on screen.

Run `node validate-fixed-marks.mjs` for a numerical rendering check. Run `python3 ../../research/hat-turtle-fixed-points/certify.py` for the exact certificate (standard Python library only). The exploratory `check.py` additionally requires NumPy.
