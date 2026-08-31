export const LEAPFROG_COUPLING_MODES = Object.freeze({
  structural: { label: "Structural leap", requireInterfaceTransport: false, requireEventPhysics: false },
  interface: { label: "Interface-coupled leap", requireInterfaceTransport: true, requireEventPhysics: false },
  event: { label: "Event-resolved leap", requireInterfaceTransport: true, requireEventPhysics: true },
});

function text(value, label) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${label} is required`);
  return value.trim();
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonical(value[key])]));
  return value;
}

export function leapfrogCycleFingerprint(value) {
  const source = JSON.stringify(canonical(value));
  let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index); hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function node(id, label, status, detail, required, evidenceDigest = null) {
  return { id, label, status, detail, required, evidenceDigest };
}

export function buildLeapfrogPhysicsCycle(input) {
  const mode = text(input?.mode, "coupling mode");
  const contract = LEAPFROG_COUPLING_MODES[mode];
  if (!contract) throw new Error(`unsupported leap-frog coupling mode ${mode}`);
  const stageReady = input.pipelineStage === 4 && input.targetFree === true;
  const geometryDigest = text(String(input.geometryStateDigest), "geometry state digest");
  const materialEvidenceCount = Math.max(0, Number(input.materialEvidenceCount) || 0);
  const transport = input.interfaceTransport || {};
  const transportCurrent = transport.validated === true && transport.boundStateDigest === geometryDigest;
  const transportStatus = transportCurrent ? "ready"
    : transport.validated ? "stale" : contract.requireInterfaceTransport ? "missing" : "optional";
  const frontier = input.frontier || {};
  const frontierAvailable = stageReady && frontier.available === true;
  const checkpoint = input.eventCheckpoint || {};
  const checkpointCurrent = checkpoint.present === true && checkpoint.generationCurrent === true;
  const responseReady = checkpointCurrent && checkpoint.validated === true;
  const eventReady = responseReady && (!contract.requireEventPhysics || checkpoint.eventSelected === true);
  const stateCoherence = input.stateCoherence || {};
  const stateCoherent = stateCoherence.compatible === true;
  const prerequisitesForFrontier = stageReady && (!contract.requireInterfaceTransport || transportCurrent);
  let nextAction;
  if (!stageReady) nextAction = "enter-target-free-growth";
  else if (contract.requireInterfaceTransport && !transportCurrent) nextAction = "recalculate-interface-transport";
  else if (contract.requireEventPhysics && !checkpointCurrent) nextAction = "freeze-action-frontier";
  else if (checkpointCurrent && !responseReady) nextAction = "calculate-action-physics";
  else if (contract.requireEventPhysics && !eventReady) nextAction = "select-kinetic-event";
  else if ((mode === "interface" || eventReady) && !stateCoherent) nextAction = "resolve-coupling-state";
  else if (!frontierAvailable && !checkpointCurrent) nextAction = "await-geometric-frontier";
  else nextAction = "commit-structural-leap";
  const commitReady = nextAction === "commit-structural-leap";
  const nodes = [
    node("geometry", "Exact colored geometry", stageReady ? "ready" : "waiting",
      `${input.atomCount || 0} atoms · revision ${input.geometryRevision || 0} · state ${geometryDigest}`, true, geometryDigest),
    node("material", "Persistent material evidence", materialEvidenceCount ? "ready" : "optional",
      materialEvidenceCount ? `${materialEvidenceCount} reference-bound response layer${materialEvidenceCount === 1 ? "" : "s"}`
        : "γ(n̂), v(n̂), force, and trajectory evidence are optional", false),
    node("transport", "Current-interface transport", transportStatus,
      transportCurrent ? `J(x,n̂) bound to current state ${geometryDigest}`
        : transport.validated ? "validated J(x,n̂) belongs to an earlier interface"
          : "no validated current-interface J(x,n̂)", contract.requireInterfaceTransport,
      transport.responseDigest || null),
    node("frontier", "Frozen exact action frontier",
      checkpointCurrent ? "ready" : prerequisitesForFrontier && frontierAvailable ? "available" : "waiting",
      checkpointCurrent ? `${checkpoint.candidateCount || 0} actions · batch ${checkpoint.candidateBatchDigest || "frozen"}`
        : frontierAvailable ? `${frontier.candidateCount || 0} geometric candidates can be frozen`
          : "waiting for a target-free geometric frontier", contract.requireEventPhysics,
      checkpoint.candidateBatchDigest || null),
    node("event", "Candidate-resolved event physics",
      eventReady && stateCoherent ? "ready" : eventReady ? "stale"
        : checkpointCurrent ? "missing" : contract.requireEventPhysics ? "waiting" : "optional",
      eventReady ? `response ${checkpoint.responseDigest || "validated"} matches the frozen action batch`
        : responseReady ? "validated rates are available; select maximum-rate HTST or seeded KMC"
          : checkpointCurrent ? "barriers/prefactors are not yet validated for this batch"
          : "no action-level calculation checkpoint is active", contract.requireEventPhysics,
      checkpoint.responseDigest || null),
    node("leap", "Exact GCTS leap", commitReady ? "ready" : "blocked",
      commitReady ? "all selected coupling requirements are current" : `next: ${nextAction.replaceAll("-", " ")}`, true),
  ];
  const invalidationAfterCommit = {
    retained: ["reference-bound material evidence and learned geometric grammar"],
    invalidated: ["current-interface transport map", "frozen candidate batch", "candidate-resolved barriers and prefactors"],
    nextGeometryRevision: (Number(input.geometryRevision) || 0) + 1,
  };
  const receiptCore = { schema: 1, mode, geometryStateDigest: geometryDigest, stageReady,
    materialEvidenceCount, transportCurrent, frontierAvailable, checkpointCurrent, responseReady, eventReady,
    stateCoherent, stateCoherenceFingerprint: stateCoherence.stateFingerprint || null,
    stateCoherenceMismatches: [...(stateCoherence.mismatches || [])],
    commitReady, nextAction, nodes, invalidationAfterCommit,
    targetUsed: false, dynamicsLeapfrogged: true, physicalTimeIntegrated: false };
  return { ...receiptCore, cycleFingerprint: leapfrogCycleFingerprint(receiptCore),
    claimBoundary: "The cycle enforces evidence lifetime and refresh order around exact GCTS states. It does not execute an external solver, infer missing physics, make an incomplete event catalog complete, or turn browser wall time into material time." };
}

export function couplingModeGate(cycle) {
  if (!cycle || typeof cycle !== "object") throw new TypeError("a leap-frog cycle is required");
  return { allowed: cycle.commitReady === true, nextAction: cycle.nextAction,
    reason: cycle.commitReady ? "selected coupling contract is current" : `blocked · ${cycle.nextAction.replaceAll("-", " ")}`,
    targetUsed: false };
}
