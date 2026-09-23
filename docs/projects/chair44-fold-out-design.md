# Chair44 red/green edge fold-out: prototype 01

[Open the interactive design](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/chair/fold-out/).
It includes a motion slider, a cross-section, a dimensioned drawing, and
[downloadable parts](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/chair/fold-out/prototype.zip).

This is a complete **single convex-corner mechanism coupon**, not a full
Chair44 tile. The green-side piece pivots around the shared edge and becomes
the red protrusion. A rounded profile makes the turn possible without sweeping
through solid housing. It is a proposal for a physical test; no print or
hardware fit has yet been measured.

## Why the piece is rounded

The previous centered pyramids have the correct relationship between their
start and end positions: a quarter-turn around a red/green edge maps one to
the other. That does not make their entire motion collision-free. An inset
pyramid making the short turn passes through other solid material.

Here the removed piece is a quarter-cylinder whose axis is the shared edge.
The housing cavity follows its circular sweep. Turning through $90^\circ$
places the chunk on the red side, leaving the curved green recess. In the ideal
model, before adding clearance, bearings, and a bore, the removed and added
volumes are congruent. The piece keeps its volume throughout the motion.

This changes the relief from the pyramid shape tested by the existing tiler.
No equivalence of their full tilings has been established. The new edge-reaching
features also fall outside the disjoint panel-neighborhood assumption used in
the earlier occupancy reduction. Reusing that solver unchanged would not test
this shape correctly.

## Dimensions

The shaft is along the model's $y$-axis. The original convex corner occupies
$x\leq0$ and $z\leq0$; its two faces meet on the shaft axis.

| Part or feature | Nominal dimension |
|---|---|
| Corner block | $40\times40\times40\,\mathrm{mm}$, plus bearing ears |
| Rotor outer radius | $10.00\,\mathrm{mm}$ |
| Housing cavity radius | $10.30\,\mathrm{mm}$ |
| Rotor axial interval | $12.00\leq y\leq28.00\,\mathrm{mm}$ |
| Cavity axial interval | $11.70\leq y\leq28.30\,\mathrm{mm}$ |
| Axle | Diameter $2.00\,\mathrm{mm}$; length $44.00\,\mathrm{mm}$ |
| Housing bore | Diameter $2.20\,\mathrm{mm}$ |
| Rotor bore | Diameter $2.40\,\mathrm{mm}$ |
| Rotor hubs | Radius $2.50\,\mathrm{mm}$; axial length $2.00\,\mathrm{mm}$ each |
| Housing bearings | Radius $3.50\,\mathrm{mm}$; axial length $3.00\,\mathrm{mm}$ each |

The rotor has two full annular hubs so that it stays captured on the shaft.
The housing has full bearing ears at its axial ends. These project beyond the
ideal tile faces and are intentional prototype hardware, not a proposed final
mathematical tile boundary.

## Assembly

1. Print the housing and rotor from their separate STL files. Coordinates are
   in millimetres. Each supplied STL stands with the shaft axis vertical in
   the slicer. Inspect supports for the upper cavity shoulder and bearing ears.
2. Clean the bores and cavity, then place the rotor in the corner bay.
3. Align both rotor hubs with the housing bearings and insert a straight
   $2\,\mathrm{mm}$ shaft. A printable pin is included for a fit trial.
4. Check the full turn before securing anything. Fix the shaft in the housing
   bearings without gluing the rotor hubs if continued movement is desired.
   To make a fixed folded sample, lock a rotor hub to the shaft only after
   setting the final position.

The nominal clearances are starting dimensions, not a guarantee for a printer,
material, or process. The editable OpenSCAD file exposes the bore and clearance
parameters. Print one mechanism before replicating it.

The A4 SVG drawing contains a $100\,\mathrm{mm}$ scale bar. Print at actual size
and measure that bar before relying on paper dimensions.

## Geometric verification

The mesh generator verifies positive volume, nondegenerate triangles, and two
oppositely directed incident faces on every edge. It repeats these checks after
reading the exported STL coordinates, including their floating-point rounding.

| Mesh | Triangles | Approximate volume |
|---|---:|---:|
| Housing | $2860$ | $62751.18\,\mathrm{mm}^3$ |
| Rotor | $2192$ | $1283.36\,\mathrm{mm}^3$ |
| Printable pin | $256$ | $138.01\,\mathrm{mm}^3$ |

The angular mesh has $128$ segments around a full circle. The faceted cavity's
inradius exceeds the rotor's maximum radius at every rotation angle:

$$
10.30\cos\!\left(\frac{\pi}{128}\right)-10.00
>0.2968\,\mathrm{mm}.
$$

The rotor lies strictly within the cleared axial interval, with nominal
$0.30\,\mathrm{mm}$ end gaps. Housing outside that interval cannot touch it.
Within the interval, housing occupies only the original corner quadrant beyond
the cavity. The rotor and its hubs stay inside the smaller radius. Thus the
bound covers the whole sweep, not only sampled frames.

The corresponding minimum faceted bore clearances from the shaft are greater
than $0.0996\,\mathrm{mm}$ in the housing and $0.1996\,\mathrm{mm}$ in the rotor.
An additional sweep samples every quarter-degree from $0^\circ$ through
$90^\circ$, exercising $2{,}373{,}936$ mesh vertex transforms.
These checks cover nominal rigid geometry, not printing variation, friction,
stiffness, wear, or assembly with neighboring tiles.

## Files and reproduction

The [design pack](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/chair/fold-out/prototype.zip)
contains `body.stl`, `rotor.stl`, `pin.stl`, `prototype.scad`, `drawing.svg`,
`verification.json`, and these notes as `README.md`.

The STL generator and browser viewer share
[model.js](../../3d-reptiles/chair/fold-out/model.js). The supplied OpenSCAD source
provides an editable solid construction with the same nominal dimensions;
OpenSCAD compilation is not part of the recorded mesh checks.

```sh
node scripts/build-chair-fold-out.mjs
node scripts/test-chair-fold-out-browser.cjs
```

The browser test uses a local server at port `8765`; `CHAIR_FOLD_URL` selects
another URL and `CHROME_PATH` can select a browser executable. It checks the
fold controls, pause/resume, the cross-section, and mobile layout.

## Next design boundary

This coupon covers one outside corner. A concave socket has different surrounding
material and requires its own housing and motion check. A complete Chair44
version must also account for neighboring rotors, bearing hardware, and the
changed curved boundary before running new tiling tests. The existing
[centered pyramid result](chair44-centered-relief.md) does not certify this design.
