const defaultFrontierKey = (item, index) =>
  item?.pointKey ?? item?.point_key ?? item?.key ?? String(index);
const defaultCandidateKey = (candidate, index) =>
  candidate?.dedup_key ?? candidate?.pk ?? candidate?.key ?? String(index);

const normalizeConfig = (config = {}) => ({
  frontierKey: config.frontierKey ?? defaultFrontierKey,
  frontierNode: config.frontierNode ?? (() => ({})),
  candidateKey: config.candidateKey ?? defaultCandidateKey,
  candidateNode: config.candidateNode ?? (() => ({})),
  previewLimit: config.previewLimit ?? 2
});

const appendCandidateNode = (candidateMap, candidateKey, candidate, pointKey, config) => {
  if (!candidateMap.has(candidateKey)) {
    candidateMap.set(candidateKey, {
      key: candidateKey,
      ...config.candidateNode(candidate, candidateKey),
      frontier_points: []
    });
  }
  candidateMap.get(candidateKey).frontier_points.push(pointKey);
};

const buildGraphPayload = (options, frontierPoints, candidateMap) => {
  const candidates = [...candidateMap.values()].map(candidate => ({
    ...candidate,
    frontier_points: [...new Set(candidate.frontier_points)]
  }));
  return {
    options,
    frontier_points: frontierPoints,
    candidates,
    candidate_count: candidates.length,
    association_count: frontierPoints.reduce((sum, point) => sum + point.candidate_keys.length, 0)
  };
};

const addFrontierOption = (item, index, rawCandidates, candidateMap, config) => {
  const pointKey = config.frontierKey(item, index);
  const seenCandidates = new Set();
  const uniqueCandidates = [];
  const candidateKeys = [];

  for (let candidateIndex = 0; candidateIndex < rawCandidates.length; candidateIndex += 1) {
    const candidate = rawCandidates[candidateIndex];
    const candidateKey = config.candidateKey(candidate, candidateIndex, item);
    if (seenCandidates.has(candidateKey)) continue;
    seenCandidates.add(candidateKey);
    uniqueCandidates.push(candidate);
    candidateKeys.push(candidateKey);
    appendCandidateNode(candidateMap, candidateKey, candidate, pointKey, config);
  }

  const previewLimit = Number.isFinite(config.previewLimit) ? config.previewLimit : uniqueCandidates.length;
  const option = {
    ...item,
    point_key: pointKey,
    candidate_keys: candidateKeys,
    all_candidates: rawCandidates,
    unique_candidates: uniqueCandidates,
    candidates: uniqueCandidates.slice(0, previewLimit)
  };
  const frontierPoint = {
    ...config.frontierNode(item, pointKey, index),
    point_key: pointKey,
    candidate_keys: candidateKeys
  };
  return { option, frontierPoint };
};

export function buildFrontierCandidateGraphSync(frontierItems, getCandidates, config = {}) {
  const normalized = normalizeConfig(config);
  const options = [];
  const frontierPoints = [];
  const candidateMap = new Map();

  frontierItems.forEach((item, index) => {
    const rawCandidates = getCandidates(item, index) ?? [];
    const { option, frontierPoint } = addFrontierOption(item, index, rawCandidates, candidateMap, normalized);
    options.push(option);
    frontierPoints.push(frontierPoint);
  });

  return buildGraphPayload(options, frontierPoints, candidateMap);
}

export async function buildFrontierCandidateGraph(frontierItems, getCandidates, config = {}) {
  const normalized = normalizeConfig(config);
  const options = [];
  const frontierPoints = [];
  const candidateMap = new Map();

  for (let index = 0; index < frontierItems.length; index += 1) {
    const item = frontierItems[index];
    const rawCandidates = await getCandidates(item, index) ?? [];
    const { option, frontierPoint } = addFrontierOption(item, index, rawCandidates, candidateMap, normalized);
    options.push(option);
    frontierPoints.push(frontierPoint);
  }

  return buildGraphPayload(options, frontierPoints, candidateMap);
}

export function classifyFrontierCandidateGraph(graph, optionOrder) {
  const options = graph.options ?? [];
  const rank = (items) => optionOrder ? items.slice().sort(optionOrder) : items.slice();
  const candidateList = (option) => option.unique_candidates ?? option.candidates ?? [];
  const deadEnd = options.find(option => candidateList(option).length === 0);
  const forced = deadEnd ? [] : rank(options.filter(option => candidateList(option).length === 1));
  const branches = deadEnd || forced.length ? [] : rank(options.filter(option => candidateList(option).length > 0));
  return { ...graph, deadEnd, forced, branches };
}
