#!/usr/bin/env python3

from materials_gcts_cdyb_oracle import SOURCE, generate_cdyb


def test_cdyb_oracle_is_deterministic_and_chemical() -> None:
    first = generate_cdyb(2, (20.0, 20.0, 20.0))
    second = generate_cdyb(2, (20.0, 20.0, 20.0))
    assert first == second
    assert first.count > 0
    assert set(first.symbols) == {"Cd", "Yb"}
    assert set(first.source_sites) == {"V", "B", "E1", "E2", "E3", "E4", "E5", "E6"}
    # This golden multiset was independently compared with the archived NumPy
    # notebook, including all published physical-space displacement rules.
    assert first.count == 366
    assert first.symbols.count("Cd") == 310
    assert first.symbols.count("Yb") == 56
    assert first.canonical_sha256() == "a6ca2f88f11f970bf825b04b55516800e3bf8a4d28a8a61ceec01cd1e9c0b6f5"


def test_empty_centres_are_explicit_opt_in_placeholders() -> None:
    material = generate_cdyb(2, (20.0, 20.0, 20.0))
    diagnostic = generate_cdyb(2, (20.0, 20.0, 20.0), include_empty_centres=True)
    assert diagnostic.count > material.count
    assert "Zn" not in material.symbols
    assert diagnostic.symbols.count("Zn") == diagnostic.count - material.count


def test_provenance_is_pinned_to_immutable_archive() -> None:
    assert SOURCE["archive_doi"] == "10.5281/zenodo.21470195"
    assert SOURCE["license"] == "CC-BY-4.0"
    assert SOURCE["archive_sha256"] == "b0de87a489e23b6ceed43c64728b132e20ba5aef971aee210f065ce9774cc222"


if __name__ == "__main__":
    test_cdyb_oracle_is_deterministic_and_chemical()
    test_empty_centres_are_explicit_opt_in_placeholders()
    test_provenance_is_pinned_to_immutable_archive()
    print("Cd-Yb offline oracle: deterministic chemistry/provenance passed")
