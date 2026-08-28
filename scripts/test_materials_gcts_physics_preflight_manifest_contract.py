from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "apps" / "iqc-growth-live"
APP = (APP_DIR / "app.js").read_text(encoding="utf-8")
HTML = (APP_DIR / "index.html").read_text(encoding="utf-8")
CSS = (APP_DIR / "style.css").read_text(encoding="utf-8")
ATLAS = (APP_DIR / "evidence-atlas.js").read_text(encoding="utf-8")
COMPRESSION = (APP_DIR / "physics-compression-map.js").read_text(encoding="utf-8")
README = (APP_DIR / "README.md").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "projects" / "materials-recursive-gcts-benchmark.md").read_text(encoding="utf-8")


def test_preflight_is_visible_before_action_execution():
    for identifier in ("growthPhysicsPreflightState", "growthPhysicsPreflightFilters",
                       "growthPhysicsPreflightMatrix", "growthPhysicsPreflightDetail"):
        assert f'id="{identifier}"' in HTML
        assert f'$("{identifier}")' in APP
    assert "before the first structural leap" in HTML
    assert "function renderGrowthPhysicsPreflight" in APP
    assert "renderGrowthPhysicsPreflight();" in APP
    assert ".growth-physics-preflight" in CSS


def test_preflight_preserves_evidence_classes_and_routes():
    assert "function currentPhysicsPreflightManifest" in APP
    assert "physicsTranslationRecords(null).map(physicsManifestRecord)" in APP
    assert "physicsEvidenceBucket(record)" in APP
    for evidence_class in ("structural", "hypothesis", "open"):
        assert evidence_class in APP
    assert "PHYSICS_CONTROL_ROUTES[selected.id]" in APP
    assert "openPhysicsControlRoute(selected.id)" in APP
    assert "Focus the exact control without changing its value." in APP


def test_preflight_receipt_is_coordinate_free_and_hashed():
    assert "const physicsPreflightManifestSha256 = await receiptSha256" in APP
    assert "physicsPreflightManifest: { ...physicsPreflightManifest" in APP
    assert "frozenBeforeFirstStructuralAction: Boolean(frozenPhysicsPreflightManifest)" in APP
    for gate in ("generatedBeforeActionExecution: true", "coordinatesEmbedded: false",
                 "candidateGeometryEmbedded: false", "candidateSetInspected: false",
                 "targetUsed: false", "physicalTimeModeled: false"):
        assert gate in APP
    assert "function physicsProtocolControlVector()" in APP
    assert "controlVector: physicsProtocolControlVector()" in APP
    assert "capturedBeforeCandidateEnumeration: true" in APP


def test_process_scale_compression_map_is_complete_and_fail_visible():
    assert 'id="growthPhysicsCompressionMap"' in HTML
    assert '$("growthPhysicsCompressionMap")' in APP
    assert "buildPhysicsCompressionMap(records)" in APP
    assert "compressionMap: buildPhysicsCompressionMap(records)" in APP
    assert "unclassifiedRecordIds" in COMPRESSION
    assert "structuralStatesAreNotPhysicalTime: true" in COMPRESSION
    assert "hypothesesAreNotLearnedPhysics: true" in COMPRESSION
    for lane in ("structural evidence", "local attachment", "interface + morphology",
                 "imposed environment", "unresolved physics"):
        assert lane in COMPRESSION
    assert ".physics-compression-map" in CSS
    assert '"calculation-stress", "stress-strain-response"' in COMPRESSION
    manifest_start = APP.index("function physicsTranslationRecords(")
    manifest_end = APP.index("\nfunction physicsEvidenceBucket(", manifest_start)
    manifest_ids = set(re.findall(r'\{ id: "([^"]+)"', APP[manifest_start:manifest_end]))
    assigned_blocks = re.findall(r"recordIds: Object\.freeze\(\[(.*?)\]\)", COMPRESSION, re.S)
    assigned_ids = set(re.findall(r'"([^"]+)"', "\n".join(assigned_blocks)))
    assert manifest_ids == assigned_ids


def test_each_physical_layer_has_an_interactive_execution_lineage():
    assert "function renderPhysicsLineageFlow" in APP
    assert "buildPhysicsLineagePath(record)" in APP
    assert "executionLineage: physicsExecutionLineage(record)" in APP
    assert "hardAdmissionCanChange" in COMPRESSION
    assert "candidateGeometryCanChange" in COMPRESSION
    assert "initialStateCanChange" in COMPRESSION
    assert "rankingCanChange" in COMPRESSION
    assert "searchOrderCanChange" in COMPRESSION
    assert "candidateSetInspectedBeforeExecution: false" in COMPRESSION
    assert "targetUsed: false" in COMPRESSION
    assert "physicalTimeModeled: false" in COMPRESSION
    for label in ("physical evidence", "geometric encoding", "search effect",
                  "finite evidence", "claim boundary"):
        assert label in COMPRESSION
    assert ".physics-lineage-flow" in CSS


def test_execution_effect_atlas_composes_with_scale_and_evidence_filters():
    assert 'id="growthPhysicsEffectFilters"' in HTML
    assert '$("growthPhysicsEffectFilters")' in APP
    assert "buildPhysicsEffectMatrix(records)" in APP
    assert "effectMatrix: buildPhysicsEffectMatrix(records)" in APP
    assert "PHYSICS_EFFECT_COLUMNS" in COMPRESSION
    assert "mutuallyNonexclusiveEffects: true" in COMPRESSION
    assert "everyRecordClassified" in COMPRESSION
    for effect in ("hardAdmission", "candidateGeometry", "initialState", "ranking",
                   "searchOrder", "diagnostic"):
        assert effect in COMPRESSION
        assert f'data-physics-effect-filter="{effect}"' in HTML
    assert ".physics-effect-filters" in CSS
    assert ".physics-effect-rail" in CSS
    assert "No physical layer matches this scale × evidence × execution-effect intersection." in APP


def test_readiness_atlas_separates_configuration_data_diagnostics_and_external_physics():
    assert 'id="growthPhysicsReadinessFilters"' in HTML
    assert '$("growthPhysicsReadinessFilters")' in APP
    assert "PHYSICS_READINESS_STATES" in COMPRESSION
    assert "physicsExecutionReadiness" in COMPRESSION
    assert "readinessCounts" in COMPRESSION
    for readiness in ("executing", "configurable", "missingEvidence", "evidenceOnly", "external"):
        assert readiness in COMPRESSION
        assert f'data-physics-readiness-filter="{readiness}"' in HTML
    assert "controlRouteAvailable: Boolean(route)" in APP
    assert "controlRouteLabel: route?.label || null" in APP
    assert ".physics-readiness-filters" in CSS
    assert "Requires an external solver or a new trainable geometric state variable." in COMPRESSION


def test_non_webgl_fallback_keeps_the_scientific_portal_alive():
    assert "function fallbackViewportRenderer" in APP
    assert "function materialsViewportRenderer" in APP
    assert "return fallbackViewportRenderer();" in APP
    assert "scientific controls · plots · receipts remain active" in APP
    assert "scientificControlsAvailable: true" in APP
    assert "scientificCalculationsChangedByFallback: false" in APP
    assert ".viewport-renderer-fallback" in CSS


def test_public_narrative_and_build_are_versioned():
    assert "physics-to-geometry preflight classifies every current channel" in ATLAS
    assert "Build 177" in README
    assert "Build 177" in DOCS
    assert "If WebGL cannot be created" in README
    assert 'buildId: "20260827-268"' in APP
    assert 'app.js?v=20260827-268' in HTML
    assert 'style.css?v=20260827-268' in HTML
    assert 'physics-compression-map.js?v=20260827-7' in APP
    assert 'evidence-atlas.js?v=20260827-24' in HTML
    assert "Build 207" in README
    assert "Build 207" in DOCS
