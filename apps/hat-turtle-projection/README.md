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
