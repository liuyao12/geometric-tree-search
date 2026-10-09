"""Exhaustively audit the finite hypotheses of the saturated-star theorem."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time
from zoneinfo import ZoneInfo
import cyclotomic as ring
import penrose_complex as complex_model
import penrose_sectors as search_model

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[1]/"docs/research/gcts-rl-renewal"
OUTPUT = DOCS/"penrose-complex-001.json"


def normalized(value):
    return json.loads(json.dumps(value))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def cyclic_partition_sets(catalog):
    """Independent completeness check by all compositions and cyclic cuts.

    Does not use the mask-frontier enumerator, Model/Graph, or its domains.
    A full star cuts the ten-sector circle into consecutive intervals.
    Starting at any boundary lists a composition of ten by widths one to four.
    """
    lookup = {(c["start"], c["width"]): i for i, c in enumerate(catalog)}
    require(len(lookup) == 40, "corner intervals do not uniquely determine faces")
    sets = set()

    def compositions(left, widths):
        if not left:
            for cut in range(10):
                start = cut
                indices = []
                for width in widths:
                    indices.append(lookup[start, width])
                    start = (start+width) % 10
                sets.add(tuple(sorted(indices)))
            return
        for width in range(1, min(4, left)+1):
            compositions(left-width, widths+[width])

    compositions(10, [])
    return sets


def check_catalog_and_stars(report):
    catalog = complex_model.corner_catalog()
    require(report["prototype_vertices"] == normalized(complex_model.VERTICES), "changed declared templates")
    require(report["corners"] == normalized(catalog), "changed or omitted physical corners/aliases")
    aliases = [tuple((k, r, tuple(t))) for c in catalog for k, r, t in c["aliases"]]
    require(len(aliases) == 80 and len(set(aliases)) == 80, "incomplete orientation aliases")
    require(ring.power(complex_model.ETA, 10) == ring.ONE, "invalid rotation group")
    require(len(set(complex_model.DIRECTIONS)) == 10, "rotation group aliases")
    model = search_model.Model()
    for key in aliases:
        independent = complex_model.placement(key)
        actual = model.placement(key)
        require(independent["slots"] == actual.positive, "actual point support differs from theorem model")
        require(independent["vertices"] == actual.vertices, "actual outlines differ from theorem model")
    stars = report["stars"]
    expected = cyclic_partition_sets(catalog)
    got = [tuple(star["corners"]) for star in stars]
    require(len(got) == len(set(got)) and set(got) == expected, "incomplete star catalog")
    seams = polygon_pairs = 0
    lookup = {(c["start"], c["width"]): i for i, c in enumerate(catalog)}
    rotations = 0
    for star in stars:
        certificate = complex_model.star_certificate(star["corners"], catalog)
        require(star == normalized(certificate), "changed star ownership or edge certificate")
        seams += len(certificate["seams"])
        keys = [catalog[i]["key"] for i in star["corners"]]
        require(not search_model.geometry_audit(keys), "overlapping local star polygons")
        polygon_pairs += len(keys)*(len(keys)-1)//2
        for rotation in range(10):
            indices = tuple(sorted(lookup[(catalog[i]["start"]+rotation) % 10,
                                          catalog[i]["width"]] for i in star["corners"]))
            require(indices in expected, "star catalog is not rotation-closed")
            for old, new in zip(star["corners"],
                                [lookup[(catalog[i]["start"]+rotation) % 10, catalog[i]["width"]]
                                 for i in star["corners"]]):
                transformed = {ring.mul(v, complex_model.DIRECTIONS[rotation]) for v in catalog[old]["vertices"]}
                require(transformed == set(catalog[new]["vertices"]), "sector rotation differs from geometric rotation")
            rotations += 1
    require(report["template_bounds"] == complex_model.template_audit(), "changed metric completeness bounds")
    control = complex_model.periodic_controls(catalog)
    require(report["comparison_controls"] == normalized(control), "changed analytic controls")
    shift = tuple(control["second_layer_shift"])
    require(search_model.overlaps(search_model.polygon(("thick", 0, ring.ZERO)),
                                  search_model.polygon(("thick", 0, shift))), "disconnected overlap control failed")
    return {"raw_corner_aliases_checked": 80, "physical_corners_checked": len(catalog),
            "full_stars_checked": len(stars), "radial_unit_seams_checked": seams,
            "rotation_contacts_checked": rotations, "local_polygon_pairs_checked": polygon_pairs,
            "local_polygon_overlaps": 0, "star_sizes": dict(sorted(Counter(s["faces"] for s in stars).items()))}


def replay_historical_stars(report):
    historical_path = DOCS/"penrose-001.json"
    historical = json.loads(historical_path.read_text())
    require(hashlib.sha256(historical_path.read_bytes()).hexdigest() == report["historical_artifact_sha256"],
            "historical artifact changed")
    for name in ("penrose_sectors.py", "cyclotomic.py"):
        require(hashlib.sha256((HERE/name).read_bytes()).hexdigest() == historical["source_sha256"][name],
                "historical engine provenance changed")
    catalog = complex_model.corner_catalog()
    lookup = {tuple(sorted(c["vertices"])): i for i, c in enumerate(catalog)}
    allowed = {tuple(s["corners"]) for s in report["stars"]}
    full_count = exposed_count = placements_count = 0
    histogram = Counter()
    for sample in historical["pair_labels"]["samples"]:
        require(sample["status"] == "positive", "unexpected historical outcome")
        full, exposed = complex_model.complete_vertices(sample["placements"])
        required = {tuple(v) for v, _ in sample["required_points"]}
        require(required <= set(full), "historical target has an incomplete star")
        for v, keys in full.items():
            indices = []
            for kind, rotation, translation in keys:
                local = complex_model.placement((kind, rotation, complex_model.sub(translation, v)))
                indices.append(lookup[tuple(sorted(local["vertices"]))])
            indices = tuple(sorted(indices))
            require(indices in allowed, "historical full vertex has an undeclared star")
            complex_model.star_certificate(indices, catalog)
            histogram[indices] += 1
        full_count += len(full)
        exposed_count += exposed
        placements_count += len(sample["placements"])
    return {"historical_patches_replayed": len(historical["pair_labels"]["samples"]),
            "historical_placements_replayed": placements_count, "complete_vertices_replayed": full_count,
            "incomplete_exposed_vertices": exposed_count, "distinct_realized_full_stars": len(histogram),
            "scope": "reused finite witnesses only; no full saturation or infinite continuation certificate"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path, help="replay a saved artifact without changing it")
    args = parser.parse_args()
    start = time.monotonic()
    if args.check:
        report = json.loads(args.check.read_text())
        for name in ("penrose_complex.py", "audit_penrose_complex.py", "penrose_sectors.py", "cyclotomic.py"):
            require(hashlib.sha256((HERE/name).read_bytes()).hexdigest() == report["source_sha256"][name],
                    "finite-hypothesis source provenance changed: "+name)
        require(hashlib.sha256((DOCS/"penrose-faithfulness.html").read_bytes()).hexdigest() == report["proof_document_sha256"],
                "analytic proof document changed")
    else:
        catalog = complex_model.corner_catalog()
        report = {
            "date": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
            "result": "analytic connected saturated-star faithfulness theorem with checked finite hypotheses",
            "theorem_assumptions": ["nonempty vertex-connected placement set", "globally capacity-legal sectors",
                                    "all ten sectors full at every generated vertex", "declared unit rhombs and rotations"],
            "theorem_conclusion": "the component develops bijectively onto the Euclidean plane as an edge-to-edge rhomb tiling",
            "proof_scope": "written analytic proof, not a formally checked first-order proof or discovered continuation",
            "prototype_vertices": normalized(complex_model.VERTICES), "corners": normalized(catalog),
            "stars": normalized(complex_model.enumerate_stars(catalog)),
            "template_bounds": complex_model.template_audit(),
            "comparison_controls": normalized(complex_model.periodic_controls(catalog)),
            "historical_artifact_sha256": hashlib.sha256((DOCS/"penrose-001.json").read_bytes()).hexdigest(),
            "proof_document_sha256": hashlib.sha256((DOCS/"penrose-faithfulness.html").read_bytes()).hexdigest(),
            "source_sha256": {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                              for name in ("penrose_complex.py", "audit_penrose_complex.py", "penrose_sectors.py", "cyclotomic.py")},
            "external_theorem": {"author": "Urs Lang", "title": "Lecture Notes on Riemannian Geometry",
                                  "result": "Proposition 4.9, page 50", "version": "June 16, 2020",
                                  "url": "https://metaphor.ethz.ch/x/2020/fs/401-3532-08L/sc/DG2_16June2020.pdf#page=54"},
        }
    local = check_catalog_and_stars(report)
    historical = replay_historical_stars(report)
    if args.check:
        require(report["independent_audit"] == normalized({**local, **historical}), "changed audit counts")
    else:
        report["independent_audit"] = {**local, **historical}
        report["audit_seconds"] = time.monotonic()-start
        OUTPUT.write_text(json.dumps(report, separators=(",", ":"))+"\n")
    print(json.dumps({**local, **historical, "seconds": round(time.monotonic()-start, 3)}, indent=2))


if __name__ == "__main__":
    main()
