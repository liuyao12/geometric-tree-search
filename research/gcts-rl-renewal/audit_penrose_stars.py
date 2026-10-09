"""Replay saved full-star results against externally reconstructed contexts."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import cyclotomic as ring
import penrose_complex as c
import penrose_star_search as s
import penrose_sectors as p

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[1]/"docs/research/gcts-rl-renewal/penrose-stars-001.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay(report):
    catalog = c.corner_catalog()
    stars = c.enumerate_stars(catalog)
    orbits, lookup = s.orbit_catalog(catalog, stars)
    samples = report["samples"]
    require(len(samples) == len(orbits), "missing orbit result")
    weighted = Counter()
    negative_nodes = transferred = placements = frontiers = 0
    representative_placements = representative_frontiers = 0
    for (representative, members), sample in zip(orbits, samples):
        require(tuple(sample["star"]) == representative, "changed fixed star")
        require([tuple(m) for m in sample["orbit_members"]] == members, "changed orbit coverage")
        keys = [catalog[i]["key"] for i in representative]
        require([p.placement_key(k) for k in sample["initial"]] == keys, "changed fixed initial identities")
        weighted[sample["status"]] += len(members)
        if sample["status"] == "negative":
            ok, nodes = s.check_negative(keys, sample["proof"])
            require(ok, "invalid negative exhaustion proof")
            negative_nodes += nodes
        elif sample["status"] == "positive":
            state, witnesses = s.check_positive(keys, sample)
            require(sample["frontier_witnesses"] == json.loads(json.dumps(witnesses)), "changed exposed-frontier witnesses")
            representative_placements += len(state.order)
            representative_frontiers += len(witnesses)
            require(not p.geometry_audit(sample["placements"]), "overlapping displayed finite completion")
            for target in members:
                rotation = next(r for r in range(10) if tuple(sorted(
                    lookup[(catalog[i]["start"]+r) % 10, catalog[i]["width"]] for i in representative)) == target)
                tiles, frontier = s.transformed_positive(sample, rotation, target, catalog)
                transferred += 1
                placements += tiles
                frontiers += frontier
        elif sample["status"] != "unresolved":
            raise ValueError("unknown outcome label")
    require(report["counts"] == dict(Counter(x["status"] for x in samples)), "changed outcome counts")
    require(report["represented_star_counts"] == dict(weighted), "changed represented counts")
    require(report["catalog"]["full_stars"] == len(stars) and report["catalog"]["rotation_orbits"] == len(orbits),
            "changed catalog scope")
    for field, expected in (("negative_tree_nodes", negative_nodes), ("transformed_positive_stars", transferred),
                            ("transformed_base_placements", placements), ("transformed_frontier_witnesses", frontiers)):
        require(report["independent_audit"][field] == expected, "changed audit counter: "+field)
    # A representative positive must still reject altered statement or target.
    positive = next(x for x in samples if x["status"] == "positive")
    keys = [catalog[i]["key"] for i in positive["star"]]
    tampered = json.loads(json.dumps(positive))
    tampered["required"].pop()
    rejected = 0
    try:
        s.check_positive(keys, tampered)
    except ValueError:
        rejected += 1
    tampered = json.loads(json.dumps(positive))
    tampered["frontier_witnesses"].pop()
    try:
        s.transformed_positive(tampered, 0, positive["star"], catalog)
    except ValueError:
        rejected += 1
    require(rejected == 2, "altered target or omitted frontier witness accepted")
    return {"representative_completions_checked": report["counts"].get("positive", 0),
            "representative_base_placements_checked": representative_placements,
            "representative_frontier_domains_checked": representative_frontiers,
            "transformed_completions_checked": transferred, "transformed_base_placements_checked": placements,
            "transformed_frontier_witnesses_checked": frontiers, "negative_proof_nodes_checked": negative_nodes,
            "tampered_certificates_rejected": rejected,
            "scope": "saved finite completion statements and frontier viability; no full saturation or infinite extension"}


def main():
    start = time.monotonic()
    report = json.loads(OUTPUT.read_text())
    for name, expected in report["source_sha256"].items():
        require(hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, "changed search source: "+name)
    result = replay(report)
    report["serialization_audit"] = {**result, "seconds": time.monotonic()-start,
                                      "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    OUTPUT.write_text(json.dumps(report, separators=(",", ":"))+"\n")
    print(json.dumps(report["serialization_audit"], indent=2))


if __name__ == "__main__":
    main()
