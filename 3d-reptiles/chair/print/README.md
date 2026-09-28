# Chair44 print model

This is the current centered-pyramid relief, with apex \((2,1,1)\) for a base
triangle \((0,0,0),(3,0,0),(3,3,0)\). Touching dents are joined, and their
internal walls are removed. This is one solid part, not separate pyramids.

- **98 connected planar faces**, represented by **284 triangles**.
- Overall bounding box: \(48 \times 48 \times 48\) mm.
- Small-cube side: \(18\) mm.
- Geometric volume: \(40824\) cubic millimeters.
- Closed, consistently oriented surface with manifold vertex links.

## Files

- `chair44-centered-48mm.3mf`: one model with explicit millimeter units, ready to import into a slicer.
- `chair44-centered-48mm.stl`: the same mesh; select **millimeters** if asked for units.
- `chair44-centered.scad`: standalone editable OpenSCAD source. Change
  `overall_width_mm` to resize uniformly, then render and export.
- `verification.json`: mesh counts, dimensions, volume and round-trip checks.

Import the 3MF or STL into your slicer as a model. Choose the actual printer,
material, build orientation and support settings there; these files contain
no machine-specific G-code or slicer settings. The geometry includes undercuts
and pointed protrusions; review support placement and removal before printing.

This export preserves the exact ideal fit. It includes no added mating clearance;
print a small mating trial before ordering many copies. The CAD source changes
size only; it does not silently alter the apex or relief shape. Surface colors
from the web visualization are not included in these single-material files.

## Sliding and assembly

The exact exported geometry passes continuous straight-insertion checks for
all sixteen mating pairs in the canonical eight-tile supertile, with only two
copies present. Seven pairs have nonparallel faces that guide the final slide.
However, in the completed supertile every copy is locked against translation
when the other seven are fixed. One-at-a-time straight sliding cannot complete
that arrangement. Coordinated motion of all seven outer copies around the
fixed center has a verified geometric path; rotation-assisted insertion was
not tested. At the next level, eight rigid eight-tile supertiles are obstructed:
each outer cluster is translation-locked to the central cluster even as a pair,
so coordinated translation cannot assemble that level. This concerns assembled
clusters, not uniformly enlarged copies of this STL. These checks do not
establish assembly for arbitrary solver patches.

See the [assembly verification and reproducible tests](https://github.com/liuyao12/geometric-tree-search/blob/main/docs/projects/chair44-print-assembly.md).
These are ideal geometric checks; try two printed copies before ordering a set.

## Reproduction and verification

Run `NODE_BINARY=/path/to/node python3 scripts/export-chair44-print.py` from the
repository. Use `--width-mm` and `--output` for a different size or destination.
The exporter checks outward winding, paired edges, vertex links, connected
planar-face count and volume, then reopens the STL and 3MF and checks them again.
The separate `scripts/verify-chair-tetra-geometry.py` audits the exact boundary,
including the absence of coincident boundary-face patches.

Formats follow the [3MF Core specification](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md)
and [OpenSCAD face-order convention](https://files.openscad.org/documentation/manual/Primitive_Solids.html).
