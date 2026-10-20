# Fixed material points in the hat–turtle lift

For every one of the 1,009 reflected tiles in the displayed 7,921-tile patch, a different fixed point on its four-dimensional triangulated surface can be chosen so that all their projected images are stationary under one common changing planar similarity. This is an exact result for this finite patch. It is not a proof for an infinite tiling.

## What a point inside a non-planar polygon means

The fourteen boundary vertices are fixed in four dimensions. Their changing projections give the hat–turtle family. A boundary alone does not specify a filled surface. We choose a fixed triangulated disk spanning the boundary. An interior point is a fixed barycentric combination of the three vertices of one triangle. Thus it is a fixed four-dimensional point, even while its planar image changes shape.

The common triangulation, with zero-based local vertex indices, is:

```
(0,1,3) (1,2,3) (0,3,4) (0,4,13) (4,5,13) (5,6,8)
(6,7,8) (5,8,9) (5,9,12) (9,10,12) (10,11,12) (5,12,13)
```

Every projected triangle has the same strict orientation throughout the closed parameter interval. Along with the simple boundary and the oriented disk incidence, this gives a valid filled tile throughout the deformation. All chosen points have strictly positive barycentric weights, so their images stay strictly inside their tiles.

## One affine plane, one camera

Write the two triangular coordinate planes as complex numbers:

\[
U=p+\frac q2+i\frac{\sqrt3 q}{2},\qquad
V=\frac{\sqrt3 r}{2}+i\left(\frac r2+s\right).
\]

The projection is

\[
z_\theta=\cos\theta\,U+\sin\theta\,V,
\qquad \frac\pi6\leq\theta\leq\frac\pi3.
\]

Use the affine plane

\[
V=\alpha U+\beta,\qquad
\alpha=\frac{\sqrt3-i\sqrt5}{4},\qquad
\beta=\frac{\sqrt3}{2}+\frac74i.
\]

The slope follows the asymptotic plane described by [Arnaud Chéritat](https://www.math.univ-toulouse.fr/~cheritat/2023-monotile/4D-lift/page-2.html), expressed in this app's coordinate convention. The offset and the tile-specific intersection points are the finite-patch construction checked here. The slope's asymptotic interpretation alone does not prove those intersections exist.

For a point on this affine plane,

\[
z_\theta=(\cos\theta+\alpha\sin\theta)U+\beta\sin\theta.
\]

Consequently the single screen transformation

\[
F_\theta(z)=
\frac{\tfrac12+\tfrac{\sqrt3}{2}\alpha}
     {\cos\theta+\alpha\sin\theta}
\left(z-\beta\sin\theta\right)
+\frac{\sqrt3}{2}\beta
\]

satisfies

\[
F_\theta(z_\theta)=z_{\pi/3}
\]

for **every** point on that plane, throughout the interval. The denominator is nonzero because the imaginary part of the slope is nonzero and the sine is positive. Complex multiplication is a rotation and uniform scaling. Thus one shared rotation, scaling and translation fixes the images of all these points; individual tiles are never translated separately. The stationary appearance uses this camera normalization, rather than the original projection with fixed edge directions.

## Exact verification

`certify.py` uses rational arithmetic in the field

\[
\mathbb Q(\sqrt5).
\]

It checks that the above affine plane intersects the chosen triangulated surface in every reflected tile. In integer coefficient coordinates the plane equations reduce to

\[
4r-2p-q-\sqrt5\,q=4,
\]

\[
4r+8s-3q+\sqrt5(2p+q)=14.
\]

For each tile, the verifier solves these equations inside a triangle using exact barycentric weights. The certificate records each weight as two rational numbers, representing the rational part and the coefficient of the square root. Every weight is strictly positive; the smallest is approximately \(0.08414\).

The verifier also checks the oriented disk's edge incidence and proves triangle orientation over the entire interval, rather than sampling animation frames. After division by the positive cosine-squared factor and square root, each signed triangle area is a quadratic in the tangent parameter. Endpoint and stationary-point checks are exact. The smallest bound in this patch is \(1/3\).

Run from any directory:

```
python3 research/hat-turtle-fixed-points/certify.py
```

when the working directory is the repository root. This regenerates `certificate.json` and the browser's compact `fixed-marks.json`, and requires only the Python standard library. `check.py` and `common_triangulation.py` are exploratory scripts; the former requires NumPy. The separate browser-math check is:

```
node apps/hat-turtle-projection/validate-fixed-marks.mjs
```

## Scope and algorithm contract

These are copy-specific points, not a universal center shared by every congruent tile. A rank obstruction to choosing the same local reference point in all identically oriented copies does not apply to this construction.

The result concerns the supplied finite substitution patch and a stated choice of filled surface. It does not establish intersections in every reflected tile of an infinite lift or a canonical surface independent of triangulation. The app's tilted three-dimensional view adds a varying depth coordinate; the stationary-image statement applies to Plane view.

This is a geometric analysis of a known substitution patch. It adds no tiling search engine, point-value solver, GCTS marking, RL proposal, pruning rule, or scheduler. The shared algorithm contract's search conformance requirements are therefore not invoked.
