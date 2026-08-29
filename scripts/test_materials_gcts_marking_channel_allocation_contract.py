#!/usr/bin/env python3
"""Static contract for Build 292's per-prototype marking allocation microscope."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
README = (ROOT / "apps/iqc-growth-live/README.md").read_text()


def test_allocation_is_visible_and_linked_to_cluster_scenes():
    assert 'id="markingCapacityAllocation"' in HTML
    assert '$("markingCapacityAllocation")' in APP
    assert "function markingChannelDemandRecords" in APP
    assert "function renderMarkingCapacityAllocation" in APP
    assert "dataset.markingCapacityPrototype" in APP
    assert 'data-cluster-family-filter="${record.family}"' in APP
    assert "updateClusterGalleryInspector(galleryIndex)" in APP
    assert ".marking-capacity-allocation" in CSS
    assert ".marking-capacity-allocation > button.shortfall" in CSS


def test_pose_port_rank_and_channel_accounting_remain_distinct():
    for fragment in (
        "poseCount: atlas?.orientations",
        "poseSupport: atlas ? poseAtlasEntryStatus(atlas)",
        "properSymmetryGaugeCount",
        "portRoles",
        "coupledRank",
        "requiredChannels",
        "activeChannels",
        "allocatedChannels: model.channels",
        "isometryClasses",
        "fitSamples",
        "holdoutSamples",
        "pose × port rank + compatibility / failure",
        "prototypeDemand: markingChannelDemandRecords(model)",
        "prototypeDemand: row.prototypeDemand.map",
    ):
        assert fragment in APP
    assert "Channels are not raw rotation bins" in HTML
    assert "targetUsed: false" in APP
    assert "physicalEnergy: false" in APP


def test_build_and_narrative_are_current():
    assert "Build 292 · pose–port channel allocation microscope" in README
    assert 'buildId: "20260828-315"' in APP
    assert 'app.js?v=20260828-315' in HTML
    assert 'style.css?v=20260828-315' in HTML


if __name__ == "__main__":
    test_allocation_is_visible_and_linked_to_cluster_scenes()
    test_pose_port_rank_and_channel_accounting_remain_distinct()
    test_build_and_narrative_are_current()
    print("marking channel allocation contract passed")
