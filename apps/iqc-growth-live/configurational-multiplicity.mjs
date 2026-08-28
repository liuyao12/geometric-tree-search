function finiteSupport(rule) {
  const value = Number(rule?.fitCount ?? 0);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function typeKey(value) {
  return value === null || value === undefined ? "unknown" : String(value);
}

export function continuationMultiplicityAtlas(rules) {
  if (!Array.isArray(rules)) throw new Error("continuation rules must be an array");
  const grouped = new Map();
  rules.forEach((rule, index) => {
    const support = finiteSupport(rule);
    if (!support) return;
    const from = typeKey(rule.from);
    const records = grouped.get(from) || [];
    records.push({ id: String(rule.id ?? index), to: typeKey(rule.to), support });
    grouped.set(from, records);
  });
  const byType = {};
  [...grouped.entries()].sort(([first], [second]) => first.localeCompare(second)).forEach(([from, records]) => {
    records.sort((first, second) => first.id.localeCompare(second.id));
    const totalSupport = records.reduce((sum, record) => sum + record.support, 0);
    const probabilities = records.map((record) => record.support / totalSupport);
    const entropyNats = -probabilities.reduce((sum, probability) =>
      sum + probability * Math.log(probability), 0);
    const effectiveActionCount = Math.exp(entropyNats);
    byType[from] = Object.freeze({
      parentType: from,
      supportedActionCount: records.length,
      properPoseClassCount: records.length,
      childTypeCount: new Set(records.map((record) => record.to)).size,
      totalTrainingSupport: totalSupport,
      entropyNats,
      normalizedEntropy: records.length > 1 ? entropyNats / Math.log(records.length) : 0,
      effectiveActionCount,
      maximumActionProbability: Math.max(...probabilities),
      actions: Object.freeze(records.map((record, index) => Object.freeze({
        ...record, probability: probabilities[index],
      }))),
    });
  });
  const values = Object.values(byType);
  const maximumEffectiveActionCount = Math.max(1, ...values.map((record) => record.effectiveActionCount));
  const atlas = Object.fromEntries(Object.entries(byType).map(([key, record]) => [key, Object.freeze({
    ...record,
    relativeMultiplicity: record.effectiveActionCount / maximumEffectiveActionCount,
  })]));
  return Object.freeze({
    byType: Object.freeze(atlas),
    representedParentTypes: values.length,
    supportedRuleCount: values.reduce((sum, record) => sum + record.supportedActionCount, 0),
    maximumEffectiveActionCount,
    fitSupportOnly: true,
    heldoutUsed: false,
    targetUsed: false,
  });
}

export function continuationMultiplicityScore(atlas, parentType, mode = "none") {
  if (!atlas?.byType) throw new Error("continuation multiplicity atlas is required");
  const record = atlas.byType[typeKey(parentType)] || null;
  if (!record) return Object.freeze({ mode, score: -1, deadEnd: true,
    supportedActionCount: 0, properPoseClassCount: 0, childTypeCount: 0,
    totalTrainingSupport: 0, entropyNats: 0, normalizedEntropy: 0,
    effectiveActionCount: 0, relativeMultiplicity: 0, maximumActionProbability: 0,
    fitSupportOnly: true, heldoutUsed: false, targetUsed: false });
  const relative = record.relativeMultiplicity;
  const score = mode === "diversify" ? 2 * relative - 1
    : mode === "funnel" ? 1 - 2 * (record.effectiveActionCount - 1)
      / Math.max(1e-12, atlas.maximumEffectiveActionCount - 1)
      : mode === "balanced" ? 1 - 4 * Math.abs(relative - .5) : 0;
  return Object.freeze({ ...record, mode, score: Math.max(-1, Math.min(1, score)),
    deadEnd: false, fitSupportOnly: true, heldoutUsed: false, targetUsed: false });
}
