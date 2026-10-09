"""Fresh unmarked one-coronas of every full root-star rotation orbit.

Uses the existing complete point graph. The exact star catalog declares fixed
seed contexts; no polygon predicate, historical witness, marking or policy
enters search. This is an extension pilot, not an infinite construction.
"""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import random
import resource
import time
from zoneinfo import ZoneInfo
import cyclotomic as ring
import penrose_complex as complex_model
import penrose_sectors as p

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[1]/"docs/research/gcts-rl-renewal"
OUTPUT = DOCS/"penrose-stars-001.json"


def initial_state(model, keys):
    state = p.State()
    for key in keys:
        state.place(model.placement(key), seed=True)
    return state


def search(model, keys, seed, node_limit=2000, seconds=3):
    start = time.monotonic()
    metrics_before = model.metrics.copy()
    initial = initial_state(model, keys)
    required = initial.active.copy()
    core = {v for v, _ in required}
    rng = random.Random(seed)
    counts = Counter()
    witness = None
    best = initial

    def visit(state, graph):
        nonlocal witness, best
        counts["nodes"] += 1
        counts["peak_frontier_points"] = max(counts["peak_frontier_points"], len(graph.domains))
        counts["peak_candidate_nodes"] = max(counts["peak_candidate_nodes"], len(graph.edges))
        if counts["nodes"] > node_limit or time.monotonic()-start > seconds:
            raise p.Limit()
        mode, point, choices = graph.decision(state, core)
        if mode == "dead":
            return {"dead": point}
        if len(state.order) > len(best.order):
            best = state
        if required <= state.totals:
            witness = state
            return None
        if mode == "empty":
            raise ValueError("required obligations disappeared")
        counts["forced" if mode == "forced" else "branches"] += 1
        alternatives = list(choices)
        rng.shuffle(alternatives)
        children = []
        for key in alternatives:
            counts["placement_attempts"] += 1
            child, cg = state.copy(), graph.copy()
            cg.update(child, child.place(model.placement(key)))
            proof = visit(child, cg)
            if witness is not None:
                return None
            children.append({"placement": key, "proof": proof})
            counts["backtracks"] += 1
        return {"kind": mode, "point": point, "children": children}

    proof = None
    try:
        proof = visit(initial, p.Graph(model, initial))
        status = "positive" if witness is not None else "negative"
    except (p.Limit, RecursionError):
        status = "unresolved"
    final = witness or best
    return {"status": status, "seed": seed, "initial": keys, "required": sorted(required),
            "placements": final.order, "tile_generations": final.tile_generations,
            "counts": dict(counts), "metrics": dict(model.metrics-metrics_before),
            "new_base_placements_in_final": len(final.order)-len(keys),
            "proof": proof, "seconds": time.monotonic()-start}


def point(raw):
    v, sector = raw
    v = tuple(v)
    if len(v) != 4 or any(type(x) is not int for x in v) or type(sector) is not int or not 0 <= sector < 10:
        raise ValueError("exact sector point required")
    return v, sector


def check_negative(keys, proof, model=None):
    """Independent full-domain exhaustion check with the declared scheduler."""
    model = p.Model() if model is None else model
    initial = initial_state(model, keys)
    required = initial.active.copy()
    core = {v for v, _ in required}
    nodes = 0

    def visit(state, node):
        nonlocal nodes
        nodes += 1
        domains = p.exhaustive_domains(model, state)
        if "dead" in node:
            q = point(node["dead"])
            return q in domains and not domains[q]
        if required <= state.totals or not domains or any(not cs for cs in domains.values()):
            return False
        forced = sorted(q for q, cs in domains.items() if len(cs) == 1)
        q = forced[0] if forced else min(domains, key=lambda q: (state.generations[q], q[0] not in core, len(domains[q]), q))
        if point(node["point"]) != q or node["kind"] != ("forced" if forced else "branch"):
            return False
        children = node["children"]
        alternatives = [p.placement_key(c["placement"]) for c in children]
        if len(alternatives) != len(set(alternatives)) or set(alternatives) != domains[q]:
            return False
        for key, child in zip(alternatives, children):
            next_state = state.copy()
            next_state.place(model.placement(key))
            if not visit(next_state, child["proof"]):
                return False
        return True

    try:
        return visit(initial, proof), nodes
    except (ValueError, TypeError, KeyError, IndexError, RecursionError):
        return False, nodes


def check_positive(keys, sample):
    initial_keys = [p.placement_key(k) for k in keys]
    placements = [p.placement_key(k) for k in sample["placements"]]
    if placements[:len(keys)] != initial_keys:
        raise ValueError("changed fixed seed context")
    model = p.Model()
    initial = initial_state(model, keys)
    required = initial.active.copy()
    if {point(q) for q in sample["required"]} != required:
        raise ValueError("changed completion target")
    if not p.verify_patch(model, placements, required):
        raise ValueError("invalid positive point witness")
    state = p.State()
    for i, key in enumerate(placements):
        state.place(model.placement(key), seed=i < len(keys))
    if state.tile_generations != sample["tile_generations"]:
        raise ValueError("changed placement generations")
    domains = p.exhaustive_domains(model, state)
    if any(not cs for cs in domains.values()):
        raise ValueError("dead exposed frontier in positive witness")
    return state, [(q, min(cs)) for q, cs in sorted(domains.items())]


def orbit_catalog(catalog, stars):
    lookup = {(c["start"], c["width"]): i for i, c in enumerate(catalog)}
    groups = {}
    for star in stars:
        images = {tuple(sorted(lookup[(catalog[i]["start"]+r) % 10, catalog[i]["width"]]
                               for i in star["corners"])): r for r in reversed(range(10))}
        representative = min(images)
        groups.setdefault(representative, sorted(images))
    if sum(map(len, groups.values())) != len(stars):
        raise ValueError("rotation orbit coverage failed")
    return sorted(groups.items()), lookup


def rotate_key(raw, rotation):
    kind, r, translation = p.placement_key(raw)
    return kind, (r+rotation) % 10, ring.mul(translation, complex_model.DIRECTIONS[rotation])


def transformed_positive(sample, rotation, target_indices, catalog):
    """Replays full point witness and one legal candidate for every exposed slot.

    Seed aliases are replaced by the externally declared canonical identities
    of the rotated physical star. All aliases have identical unmarked support.
    No complete-domain claim depends on this witness-only transfer check.
    """
    model = p.Model()
    keys = [catalog[i]["key"] for i in target_indices]
    transformed = keys+[rotate_key(k, rotation) for k in sample["placements"][len(keys):]]
    required = {p.point_action(point(q), rotation, ring.ZERO) for q in sample["required"]}
    if not p.verify_patch(model, transformed, required):
        raise ValueError("invalid rotated completion")
    state = p.State()
    for i, key in enumerate(transformed):
        state.place(model.placement(key), seed=i < len(keys))
    witnesses = []
    for q, key in sample["frontier_witnesses"]:
        transformed_point = p.point_action(point(q), rotation, ring.ZERO)
        candidate = rotate_key(key, rotation)
        tile = model.placement(candidate)
        if transformed_point not in tile.positive or not state.legal(tile):
            raise ValueError("invalid transformed frontier viability witness")
        witnesses.append(transformed_point)
    if len(witnesses) != len(set(witnesses)) or set(witnesses) != state.active-state.totals:
        raise ValueError("omitted transformed frontier obligation")
    return len(transformed), len(witnesses)


def main():
    start = time.monotonic()
    catalog = complex_model.corner_catalog()
    stars = complex_model.enumerate_stars(catalog)
    orbits, lookup = orbit_catalog(catalog, stars)
    samples = []
    model = p.Model()
    for i, (representative, members) in enumerate(orbits):
        if i % 10 == 0:
            model = p.Model()
        keys = [catalog[j]["key"] for j in representative]
        sample = search(model, keys, 93000+i)
        sample.update({"star": representative, "orbit_members": members})
        samples.append(sample)
        print("full-star extension", i+1, "of", len(orbits), sample["status"], sample["counts"], flush=True)
    search_seconds = time.monotonic()-start
    audit_start = time.monotonic()
    negative_nodes = transformed_count = transferred_tiles = transferred_frontiers = 0
    weighted = Counter()
    for sample in samples:
        keys = [catalog[i]["key"] for i in sample["star"]]
        weighted[sample["status"]] += len(sample["orbit_members"])
        if sample["status"] == "negative":
            ok, count = check_negative(keys, sample["proof"])
            if not ok:
                raise ValueError("failed independent negative proof")
            negative_nodes += count
        elif sample["status"] == "positive":
            state, witnesses = check_positive(keys, sample)
            sample["frontier_witnesses"] = witnesses
            sample["independent_polygon_overlaps"] = p.geometry_audit(sample["placements"])
            if sample["independent_polygon_overlaps"]:
                raise ValueError("geometrically overlapping displayed completion")
            for target in sample["orbit_members"]:
                rotation = next(r for r in range(10) if tuple(sorted(
                    lookup[(catalog[i]["start"]+r) % 10, catalog[i]["width"]] for i in sample["star"])) == tuple(target))
                tiles, frontiers = transformed_positive(sample, rotation, target, catalog)
                transformed_count += 1
                transferred_tiles += tiles
                transferred_frontiers += frontiers
    report = {
        "date": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(),
        "initial_marking": None, "policy": None, "historical_witness_imported": False,
        "known_arrows_imported": False, "known_substitution_imported": False,
        "configuration": {"node_limit": 2000, "seconds_per_orbit": 3, "cache_reset_every_orbits": 10,
                          "scheduler": "global dead, forced, earliest generation; initial-core, degree and exact-key ties",
                          "target": "all ten sector slots at every vertex of the fixed full-root-star cluster",
                          "unknown": "node/time/recursion cutoffs are unresolved"},
        "catalog": {"full_stars": len(stars), "rotation_orbits": len(orbits),
                    "orbit_size_histogram": dict(Counter(len(m) for _, m in orbits)),
                    "scope": "all root-star sector partitions; physical aliases canonicalized only in seed catalog"},
        "counts": dict(Counter(s["status"] for s in samples)), "represented_star_counts": dict(weighted),
        "samples": samples, "search_and_catalog_seconds": search_seconds,
        "independent_audit": {"negative_tree_nodes": negative_nodes, "transformed_positive_stars": transformed_count,
                              "transformed_base_placements": transferred_tiles,
                              "transformed_frontier_witnesses": transferred_frontiers,
                              "seconds": time.monotonic()-audit_start,
                              "scope": "independent representative domains; exact transferred coverage and frontier witnesses; finite only"},
        "total_seconds": time.monotonic()-start,
        "peak_process_memory_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_sha256": {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                          for name in ("penrose_star_search.py", "penrose_complex.py", "penrose_sectors.py", "cyclotomic.py")},
    }
    OUTPUT.write_text(json.dumps(report, separators=(",", ":"))+"\n")
    print("checked full-star pilot", report["counts"], dict(weighted), "seconds", round(report["total_seconds"], 2), flush=True)


if __name__ == "__main__":
    main()
