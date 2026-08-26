function rounded(value, digits = 5) {
  const scale = 10 ** digits;
  return Math.round(Number(value) * scale) / scale;
}

/** Resolve the frozen, target-free score and gate ledger for one emitted placement. */
export function buildSiteCreationPhysicsAudit(decisionEvidence) {
  if (!decisionEvidence) return {
    available: false, status: "supplied site · no GCTS creation decision",
    activeTerms: [], diagnosticTerms: [], admissionGates: [], targetUsed: false,
  };
  const terms = Array.isArray(decisionEvidence.physicsTerms) ? decisionEvidence.physicsTerms : [];
  const gates = Array.isArray(decisionEvidence.admissionGates) ? decisionEvidence.admissionGates : [];
  if (terms.some((term) => !term?.id || !Number.isFinite(term.raw)
      || !Number.isFinite(term.weight) || !Number.isFinite(term.contribution))) {
    throw new Error("site creation physics terms must be finite frozen score records");
  }
  if (gates.some((gate) => !gate?.id || typeof gate.passed !== "boolean")) {
    throw new Error("site creation admission gates must be explicit boolean records");
  }
  const normalized = terms.map((term) => ({ id: term.id, label: term.label,
    raw: rounded(term.raw), weight: rounded(term.weight), contribution: rounded(term.contribution),
    role: term.role, claimBoundary: term.claimBoundary,
    active: Math.abs(term.weight) > 1e-12 }));
  const activeTerms = normalized.filter((term) => term.active).sort((first, second) =>
    Math.abs(second.contribution) - Math.abs(first.contribution) || first.id.localeCompare(second.id));
  const diagnosticTerms = normalized.filter((term) => !term.active).sort((first, second) => first.id.localeCompare(second.id));
  const admissionGates = gates.map((gate) => ({ id: gate.id, label: gate.label,
    passed: gate.passed, observed: gate.observed, requirement: gate.requirement }));
  const signedContribution = activeTerms.reduce((sum, term) => sum + term.contribution, 0);
  return {
    available: true,
    status: `${activeTerms.length} active rank terms · ${diagnosticTerms.length} diagnostic · ${admissionGates.length} hard gates`,
    activeTerms, diagnosticTerms, admissionGates,
    signedContribution: rounded(signedContribution),
    allHardGatesPassed: admissionGates.every((gate) => gate.passed),
    markingScore: Number.isFinite(decisionEvidence.markingScore) ? rounded(decisionEvidence.markingScore) : null,
    targetUsed: false, scoreIsEnergy: false, scoreIsProbability: false,
    dynamicalTrajectoryIntegrated: false, physicalTimeIntegrated: false,
  };
}
