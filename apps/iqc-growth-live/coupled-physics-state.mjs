function sha(value, label) {
  if (value == null) return null;
  const normalized = String(value).trim().toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(normalized)) throw new TypeError(`${label} must be 64 hexadecimal characters`);
  return normalized;
}

function temperature(value, label) {
  if (value == null) return null;
  const normalized = Number(value);
  if (!Number.isFinite(normalized) || normalized <= 0) throw new TypeError(`${label} must be positive Kelvin`);
  return normalized;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort()
    .map((key) => [key, canonical(value[key])]));
  return value;
}

export function coupledStateFingerprint(value) {
  const source = JSON.stringify(canonical(value)); let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index); hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function channel(id, label, raw, required) {
  const validated = raw?.validated === true;
  const enabled = raw?.enabled !== false;
  const active = required || (validated && enabled);
  return { id, label, required, active, validated,
    currentGeometry: raw?.currentGeometry !== false,
    stateSha256: sha(raw?.couplingStateSha256, `${label} coupling state`),
    temperatureKelvin: temperature(raw?.temperatureKelvin, `${label} temperature`),
    evidenceSha256: sha(raw?.evidenceSha256, `${label} evidence`) };
}

export function buildCoupledPhysicsState(input = {}) {
  const mode = String(input.mode || "structural");
  if (!["structural", "interface", "event"].includes(mode)) throw new Error(`unsupported coupling mode ${mode}`);
  const channels = [
    channel("transport", "interface transport J(x,n̂)", input.interfaceTransport,
      mode === "interface" || mode === "event"),
    channel("attachment", "orientation attachment v(n̂)", input.attachmentKinetics, false),
    channel("event", "candidate barriers + prefactors", input.eventKinetics, mode === "event"),
  ];
  const active = channels.filter((entry) => entry.active);
  const mismatches = [];
  active.forEach((entry) => {
    if (!entry.validated) mismatches.push(`${entry.id}:unvalidated`);
    if (!entry.currentGeometry) mismatches.push(`${entry.id}:stale-geometry`);
    if (!entry.stateSha256) mismatches.push(`${entry.id}:missing-state-digest`);
  });
  const stateDigests = [...new Set(active.map((entry) => entry.stateSha256).filter(Boolean))];
  if (stateDigests.length > 1) mismatches.push("coupling-state-digest-mismatch");
  const temperatures = active.map((entry) => entry.temperatureKelvin).filter((value) => value != null);
  const referenceTemperature = temperatures[0] ?? null;
  if (temperatures.some((value) => Math.abs(value - referenceTemperature)
      > Math.max(1e-9, referenceTemperature * 1e-9))) mismatches.push("temperature-mismatch");
  const comparableChannelCount = active.filter((entry) => entry.stateSha256).length;
  const compatible = active.length > 0 && mismatches.length === 0;
  const core = { schema: 1, mode, channels, activeChannelCount: active.length,
    comparableChannelCount, compatible, mismatches,
    sharedStateSha256: compatible ? stateDigests[0] || null : null,
    sharedTemperatureKelvin: compatible ? referenceTemperature : null,
    targetUsed: false, geometryUsedAsThermodynamicState: false,
    missingStateInferred: false, evidenceCombinedWhenIncompatible: false };
  return { ...core, stateFingerprint: coupledStateFingerprint(core),
    claimBoundary: compatible
      ? "Active external physics channels explicitly identify one shared driving-state digest; supplied temperatures agree where present. This proves provenance compatibility, not physical-model completeness or equilibrium."
      : "External responses are not combined until every active channel is current, validated, and names the same explicit driving-state digest. Geometry, labels, and matching temperatures do not manufacture a missing state identity." };
}

export function coupledStateGate(state, { strict = false } = {}) {
  if (!state || typeof state !== "object") throw new TypeError("coupled physics state is required");
  const allowed = !strict || state.compatible === true;
  return { allowed, strict, mismatches: [...(state.mismatches || [])], targetUsed: false,
    reason: allowed ? state.compatible ? "active external evidence is state-coherent" : "coherence is diagnostic in structural mode"
      : `state coherence blocked · ${(state.mismatches || []).join(", ") || "no comparable active evidence"}` };
}
