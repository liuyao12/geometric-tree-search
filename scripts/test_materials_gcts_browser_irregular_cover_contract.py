"""Browser integration contract for exact irregular support covers."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = ROOT / "apps" / "iqc-growth-live"


def test_browser_uses_one_occurrence_cover_through_search() -> None:
    source = (APP / "app.js").read_text(encoding="utf-8")
    learner = (APP / "irregular-cover.js").read_text(encoding="utf-8")

    assert 'import { discoverIrregularCover } from "./irregular-cover.js?v=20260824-1"' in source
    assert "function buildIrregularClusterCover(source)" in source
    assert "return buildIrregularClusterCover(source)" in source
    assert "occurrenceBased: true" in source
    assert "function learnCoverOverlapMarking(source)" in source
    assert "function learnIrregularOverlapGrammar(source)" in source
    assert "function supportOccurrenceFrame(source, placement)" in source
    assert "function makeCoverOccurrence(source, placement, index)" in source
    assert "if (learnedCover?.occurrenceBased) return learnCoverOverlapMarking(source)" in source
    assert "if (learnedCover?.occurrenceBased) return learnIrregularOverlapGrammar(source)" in source
    assert "overlapGrammar.coverBased || overlapGrammar.molecular" in source
    assert "return learnedCover?.occurrenceBased || learnedCover?.molecular ? learnedCover.types" in source
    assert "center-free bond-lens supports" in source
    assert "proper-rotation-invariant colored metric plus chirality signatures" in source
    assert "chirality: type.chirality" in source
    assert "chirality: cluster.chirality ?? null" in source
    assert 'const chirality = cluster.chirality ? ` · χ ${cluster.chirality}` : ""' in source
    assert "Residual gaps participate in exact known-window replay but are not promoted" in source
    assert "function updateClusterGalleryInspector(galleryIndex)" in source
    assert "complete-cover evidence" in source
    assert "proper-pose support" in source
    assert "connection capacity" in source
    assert 'card.setAttribute("role", "button")' in source
    assert 'card.addEventListener("keydown"' in source

    assert "export function discoverIrregularCover" in learner
    assert 'kind: "bond-lens"' in learner
    assert "coloredMetricSignature" in learner
    assert "function chiralityToken" in learner
    assert 'return signs.has(1) ? "+" : "-"' in learner
    assert 'chirality: group.signature.split("|chi:").at(-1)' in learner
    assert "chooseCoverOccurrences(coordinationGroups" in learner
    assert "chooseCoverOccurrences(lensGroups" in learner
    assert "addRecurrenceWitnesses" in learner
    assert "addRecurringSteinerOccurrences" in learner
    assert "boundedReplayConnectors" in learner
    assert "residualComponents" in learner
    assert "complete: covered.size === atomCount" in learner


if __name__ == "__main__":
    test_browser_uses_one_occurrence_cover_through_search()
    print("browser irregular-cover integration contract: passed")
