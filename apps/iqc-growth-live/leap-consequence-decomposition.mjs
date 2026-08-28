export const LEAP_CONSEQUENCE_COMPONENTS = Object.freeze({
  total: Object.freeze({
    id: "total",
    label: "total retained leap",
    axisLabel: "before → retained",
    shortBoundary: "Rigid attachment and any accepted bounded settling are combined.",
  }),
  attachment: Object.freeze({
    id: "attachment",
    label: "rigid GCTS attachment",
    axisLabel: "before → as placed",
    shortBoundary: "Only the committed whole-cluster placement is compared; no post-placement displacement is included.",
  }),
  settling: Object.freeze({
    id: "settling",
    label: "bounded geometric settling",
    axisLabel: "as placed → retained",
    shortBoundary: "Only the local constraint-projection correction, if accepted, is compared; atom count and cluster topology remain fixed.",
  }),
});

export function resolveLeapConsequenceComparison(leap, requested = "total", current = null) {
  if (!leap) return {
    mode: "total",
    ...LEAP_CONSEQUENCE_COMPONENTS.total,
    before: current,
    after: current,
    componentAvailable: false,
    settlingAccepted: false,
    explanation: "Seed state; no structural leap has been retained yet.",
  };
  const mode = requested in LEAP_CONSEQUENCE_COMPONENTS ? requested : "total";
  const componentAvailable = Boolean(leap.asPlaced);
  if (mode === "attachment" && componentAvailable) return {
    mode,
    ...LEAP_CONSEQUENCE_COMPONENTS[mode],
    before: leap.before,
    after: leap.asPlaced,
    componentAvailable: true,
    settlingAccepted: Boolean(leap.relaxation?.accepted),
    explanation: "The exact antichain has been committed, but its newly emitted sites are still at their rigid learned poses.",
  };
  if (mode === "settling" && componentAvailable) {
    const accepted = Boolean(leap.relaxation?.accepted);
    return {
      mode,
      ...LEAP_CONSEQUENCE_COMPONENTS[mode],
      before: leap.asPlaced,
      after: leap.after,
      componentAvailable: true,
      settlingAccepted: accepted,
      explanation: accepted
        ? "Only newly emitted sites move, within the declared displacement cap; hard geometry, boundary, and topology gates are rechecked before commit."
        : `No displacement was committed${leap.relaxation?.reason ? `: ${leap.relaxation.reason}` : "; the retained state equals the as-placed state"}.`,
    };
  }
  return {
    mode: "total",
    ...LEAP_CONSEQUENCE_COMPONENTS.total,
    before: leap.before,
    after: leap.after,
    componentAvailable,
    settlingAccepted: Boolean(leap.relaxation?.accepted),
    explanation: componentAvailable
      ? "The complete retained update combines the rigid whole-cluster antichain with any accepted bounded geometric correction."
      : "This retained leap predates the explicit as-placed checkpoint, so only its total before/after comparison is available.",
  };
}
