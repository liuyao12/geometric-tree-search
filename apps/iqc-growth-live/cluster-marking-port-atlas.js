const finiteVector = (value) => Array.isArray(value) && value.length === 3
  && value.every(Number.isFinite);

function normalized(value) {
  if (!finiteVector(value)) return null;
  const length = Math.hypot(...value);
  return length > 1e-12 ? value.map((entry) => entry / length) : null;
}

const dot = (first, second) => first.reduce((sum, value, index) => sum + value * second[index], 0);

function nearestChannel(direction, axes, activeChannels) {
  if (activeChannels <= 1 && !normalized(axes[0])) return 0;
  let selected = 0;
  let best = -Infinity;
  axes.slice(0, activeChannels).forEach((axis, index) => {
    const unit = normalized(axis);
    const score = unit ? dot(direction, unit) : -Infinity;
    if (score > best) { best = score; selected = index; }
  });
  return selected;
}

function mergeDirection(group, direction, weight) {
  const sum = group.directionSum.map((value, index) => value + direction[index] * weight);
  const unit = normalized(sum) || group.direction;
  group.directionSum = sum;
  group.direction = unit;
}

/**
 * Build a display/audit atlas from connection observations in intrinsic
 * cluster frames. Channels retain representation capacity; observed port
 * directions retain geometry. A one-channel scalar model therefore remains
 * directional whenever directional connection evidence exists.
 *
 * Unsupported sectors are negative *training/model sectors*: they are not
 * rejected physical trajectories and never authorize candidate geometry.
 */
export function buildClusterMarkingPortAtlas({
  prototypeCount,
  activeChannelsByPrototype,
  channelAxes,
  observations,
  mergeCosine = Math.cos(Math.PI / 12),
}) {
  const count = Math.max(0, Math.round(Number(prototypeCount) || 0));
  const axes = Array.isArray(channelAxes) ? channelAxes.map((axis) => [...axis]) : [];
  const byPrototype = Array.from({ length: count }, (_, prototype) => ({
    prototype,
    compatiblePorts: [],
    unsupportedSectors: [],
    invalidObservations: 0,
    directionalObservationCount: 0,
    scalarDirectional: false,
  }));

  (observations || []).forEach((observation) => {
    const prototype = Number(observation?.prototype);
    const direction = normalized(observation?.direction);
    if (!Number.isInteger(prototype) || prototype < 0 || prototype >= count) return;
    const atlas = byPrototype[prototype];
    if (!direction) { atlas.invalidObservations++; return; }
    const activeChannels = Math.max(1, Math.min(axes.length || 1,
      Number(activeChannelsByPrototype?.[prototype]) || axes.length || 1));
    const channel = nearestChannel(direction, axes, activeChannels);
    const weight = Math.max(1, Number(observation.observations) || 1);
    const shared = Math.max(0, Number(observation.shared) || 0);
    let group = atlas.compatiblePorts.find((candidate) => candidate.channel === channel
      && dot(candidate.direction, direction) >= mergeCosine);
    if (!group) {
      group = {
        channel,
        direction: [...direction],
        directionSum: direction.map((entry) => entry * weight),
        observations: 0,
        sharedSum: 0,
        sharedMaximum: 0,
        status: "compatible-port",
      };
      atlas.compatiblePorts.push(group);
    } else mergeDirection(group, direction, weight);
    group.observations += weight;
    group.sharedSum += shared * weight;
    group.sharedMaximum = Math.max(group.sharedMaximum, shared);
    atlas.directionalObservationCount += weight;
  });

  byPrototype.forEach((atlas, prototype) => {
    const activeChannels = Math.max(1, Math.min(axes.length || 1,
      Number(activeChannelsByPrototype?.[prototype]) || axes.length || 1));
    const maximumModesPerChannel = activeChannels === 1 ? 4 : 2;
    atlas.rawDirectionalModes = atlas.compatiblePorts.length;
    atlas.maximumModesPerChannel = maximumModesPerChannel;
    atlas.compatiblePorts = [...new Set(atlas.compatiblePorts.map((port) => port.channel))]
      .sort((first, second) => first - second).flatMap((channel) => {
        const groups = atlas.compatiblePorts.filter((port) => port.channel === channel)
          .sort((first, second) => second.observations - first.observations
            || first.direction.join(",").localeCompare(second.direction.join(",")));
        const retained = groups.slice(0, maximumModesPerChannel);
        groups.slice(maximumModesPerChannel).forEach((extra) => {
          const target = retained.slice().sort((first, second) =>
            dot(second.direction, extra.direction) - dot(first.direction, extra.direction))[0];
          if (!target) return;
          target.directionSum = target.directionSum.map((value, index) => value + extra.directionSum[index]);
          target.direction = normalized(target.directionSum) || target.direction;
          target.observations += extra.observations;
          target.sharedSum += extra.sharedSum;
          target.sharedMaximum = Math.max(target.sharedMaximum, extra.sharedMaximum);
        });
        return retained;
      });
    atlas.compatiblePorts.forEach((port) => {
      port.sharedMean = port.sharedSum / Math.max(1, port.observations);
      delete port.sharedSum;
      delete port.directionSum;
      port.direction = port.direction.map((value) => Number(value.toFixed(12)));
    });
    atlas.compatiblePorts.sort((first, second) => first.channel - second.channel
      || second.observations - first.observations
      || first.direction.join(",").localeCompare(second.direction.join(",")));
    for (let channel = 0; channel < activeChannels; channel++) {
      const axis = normalized(axes[channel]);
      if (!axis || atlas.compatiblePorts.some((port) => port.channel === channel)) continue;
      atlas.unsupportedSectors.push({
        channel,
        direction: axis.map((value) => Number(value.toFixed(12))),
        status: "unsupported-training-sector",
        observations: 0,
      });
    }
    atlas.scalarDirectional = activeChannels === 1
      && !normalized(axes[0]) && atlas.compatiblePorts.length > 0;
    atlas.hasDirectionalEvidence = atlas.compatiblePorts.length > 0;
    atlas.sphericalFallbackUsed = false;
  });

  return {
    schema: 1,
    geometrySource: "train-observed connection directions in intrinsic proper cluster frames",
    unsupportedMeaning: "channel sector without a compatible port observation; not a physical potential or rejected trajectory",
    candidateGeometryChanged: false,
    physicalPotential: false,
    mergeCosine,
    prototypes: byPrototype,
  };
}

export function clusterMarkingPortSummary(atlas, prototype) {
  const record = atlas?.prototypes?.[prototype];
  if (!record) return null;
  return {
    compatiblePorts: record.compatiblePorts.length,
    compatibleObservations: record.directionalObservationCount,
    unsupportedSectors: record.unsupportedSectors.length,
    rawDirectionalModes: record.rawDirectionalModes,
    maximumModesPerChannel: record.maximumModesPerChannel,
    scalarDirectional: record.scalarDirectional,
    sphericalFallbackUsed: record.sphericalFallbackUsed,
    invalidObservations: record.invalidObservations,
  };
}
