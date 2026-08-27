import { blockedCreationResponseSurrogate, blockedCreationResponseValidation,
  buildCreationResponseAssociation, creationResponseHorizonSweep, creationResponseLeapProfile,
  LOCAL_CREATION_CONTEXT_FEATURE_IDS }
  from "./creation-response-association.js?v=20260826-13";


function progress(step, total, label) {
  self.postMessage({ type: "progress", step, total, label });
}

self.addEventListener("message", (event) => {
  const records = event.data?.records;
  const outcomeIds = event.data?.outcomeIds;
  if (!Array.isArray(records) || !Array.isArray(outcomeIds)) {
    self.postMessage({ type: "error", message: "response worker needs records and outcome IDs" }); return;
  }
  try {
    const total = 1 + outcomeIds.length * 5;
    let step = 0;
    progress(++step, total, "grouped rank associations");
    const audit = buildCreationResponseAssociation(records);
    const associations = audit.associations.map(({ points, ...summary }) => summary);
    const blockedValidation = {};
    const leapProfiles = {};
    const blockedSurrogates = {};
    const contextualBlockedSurrogates = {};
    const localContextBlockedSurrogates = {};
    const localContextHorizonSweeps = {};
    outcomeIds.forEach((outcomeId) => {
      progress(++step, total, `${outcomeId} · chronological validation`);
      blockedValidation[outcomeId] = blockedCreationResponseValidation(records, outcomeId,
        { minimumSamplesPerSplit: 8 });
      const selected = audit.associations.find((entry) => entry.outcomeId === outcomeId);
      leapProfiles[outcomeId] = selected
        ? creationResponseLeapProfile(records, selected.termId, outcomeId) : null;
      progress(++step, total, `${outcomeId} · score-only surrogate`);
      blockedSurrogates[outcomeId] = blockedCreationResponseSurrogate(records, outcomeId,
        { minimumSamplesPerSplit: 12 });
      progress(++step, total, `${outcomeId} · structural-context surrogate`);
      contextualBlockedSurrogates[outcomeId] = blockedCreationResponseSurrogate(records, outcomeId,
        { minimumSamplesPerSplit: 12, includeStructuralContext: true });
      progress(++step, total, `${outcomeId} · local-context surrogate`);
      localContextBlockedSurrogates[outcomeId] = blockedCreationResponseSurrogate(records, outcomeId,
        { minimumSamplesPerSplit: 12, includeStructuralContext: true,
          contextFeatureIds: LOCAL_CREATION_CONTEXT_FEATURE_IDS });
      progress(++step, total, `${outcomeId} · blocked horizon sweep`);
      localContextHorizonSweeps[outcomeId] = creationResponseHorizonSweep(records, outcomeId,
        { minimumSamplesPerSplit: 12 });
    });
    self.postMessage({ type: "result", result: {
      associations, blockedValidation, leapProfiles, blockedSurrogates,
      contextualBlockedSurrogates, localContextBlockedSurrogates, localContextHorizonSweeps,
      available: audit.available, placementSamples: audit.placementSamples,
      emittedSitePresentations: audit.emittedSitePresentations,
    } });
  } catch (error) {
    self.postMessage({ type: "error", message: error?.message || String(error) });
  }
});
