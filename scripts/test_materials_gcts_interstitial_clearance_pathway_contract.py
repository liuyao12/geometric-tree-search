#!/usr/bin/env python3
"""Contract for finite and periodic interstitial-clearance pathways."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/iqc-growth-live/app.js").read_text()
HTML = (ROOT / "apps/iqc-growth-live/index.html").read_text()
CSS = (ROOT / "apps/iqc-growth-live/style.css").read_text()
MODULE = (ROOT / "apps/iqc-growth-live/interstitial-clearance.js").read_text()


def test_pathway_is_visible_leap_linked_and_receipted():
    for element_id in (
        "voidClearanceState", "voidClearanceMetrics", "voidClearanceDistribution",
        "voidClearanceRadial", "voidClearancePath", "voidClearanceReadout",
        "voidClearanceBoundary",
        "voidNetworkState", "voidNetworkFilters", "voidNetworkReadout",
        "voidThroatThreshold", "voidThroatThresholdValue",
        "voidRadiusModel", "voidProbeSpecies", "voidTopologyMode",
    ):
        assert f'id="{element_id}"' in HTML
        assert f'$("{element_id}")' in APP
    for phrase in (
        "function structuralVoidClearanceSnapshot", "function structuralVoidClearanceSeries",
        "function renderVoidClearancePathway", "voidClearance: structuralVoidClearanceSnapshot()",
        'id: "void-clearance", group: "local"', "interstitialClearancePathway:",
        'id: "void-network", group: "mesoscale"', "selectedNetworkFilter:",
        'id: "void-throat", group: "mesoscale"', "selectedThroatThreshold:",
        'id: "void-steric", group: "mesoscale"', "selectedFrameworkRadiusModel:",
        "selectedProbeSpecies:", "optionalFrameworkEnvelope:",
        "selectedNetworkDomain:", "periodicReferenceCertificate:",
        "networkRule:", "throatRule:", "graphCarriesSegmentClearance: true",
        "function thresholdedVoidNetwork",
        "renderVoidClearancePathway();",
    ):
        assert phrase in APP
    assert ".void-clearance-pathway" in CSS
    assert ".void-clearance-plots" in CSS
    assert ".void-network-audit" in CSS
    assert ".void-throat-control" in CSS
    assert ".void-steric-controls" in CSS


def test_geometry_is_dimension_aware_invariant_and_fails_closed():
    for phrase in (
        "export function interstitialClearanceAudit", "simplexCircumcenter",
        "barycentric.some", "minimumDistance2 + 1e-9 < radius2",
        "canonicalAnchors", "nearest-neighbor tie set",
        "function emptyCenterNetwork", "sharedSiteCount >= dimension",
        "segmentMinimumSiteClearance", "throatClearance", "throatToEndpointRatio",
        "largestComponentFraction", "coreToFrontComponentCount", "cycleRank",
        "widestCoreToFrontClearance", "thresholdCoreToFrontComponentCount",
        "stericThroatClearance", "widestStericCoreToFrontClearance",
        "covalentRadiusStericModelAvailable", "Cordero et al.",
        "covalentRadiusStericUniformCoordinateScalingInvariant: false",
        "periodicWitnessedSummary", "periodicGraphAudit", "wrappedEdgeCount",
        "windingVectors", "windingRank", "percolatingAxes",
        "periodicReferenceQuotientAvailable", "periodicCurrentGrowthWrapped: false",
        "finiteObservationNoPeriodicImages: true", "pointSitesNoAtomicRadii: true",
        "translationInvariant: true", "properRotationInvariant: true",
        "atomPermutationInvariant: true", "targetUsed: false", "usedAsGrowthInput: false",
    ):
        assert phrase in MODULE


def test_pathway_cannot_be_misread_as_porosity_or_transport():
    for phrase in (
        "porosityInferred: false", "poreVolumeInferred: false",
        "accessibleFreeVolumeInferred: false", "vacancyOrInterstitialIdentityInferred: false",
        "diffusionPathInferred: false", "migrationBarrierInferred: false",
        "physicalTransportConnectivityInferred: false",
        "probeAccessibleNetworkInferred: false",
        "pressureInferred: false", "physicalTimeIntegrated: false",
    ):
        assert phrase in APP
        assert phrase in MODULE
    assert "Neither view is accessible porosity, physical transport" in HTML


def test_build_242_is_exposed():
    assert 'buildId: "20260827-269"' in APP
    assert 'app.js?v=20260827-269' in HTML
    assert 'style.css?v=20260827-269' in HTML
    assert 'interstitial-clearance.js?v=20260827-10' in APP


if __name__ == "__main__":
    test_pathway_is_visible_leap_linked_and_receipted()
    test_geometry_is_dimension_aware_invariant_and_fails_closed()
    test_pathway_cannot_be_misread_as_porosity_or_transport()
    test_build_242_is_exposed()
    print("interstitial clearance pathway contract passed")
