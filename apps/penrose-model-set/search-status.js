// Consume every worker event, not just the last event of each displayed batch.
export function createSearchStatus() {
  let streak = 0, state = { kind: 'ready' };
  return {
    accept(event) {
      if (!event) return;
      if (event.type === 'add' && event.forced) {
        state = { kind: 'forced', count: ++streak };
      } else if (['try', 'add'].includes(event.type) && event.branchCount > 1) {
        streak = 0;
        state = { kind: 'branch', count: event.branchCount, frontier: event.frontier };
      } else if (event.type === 'dead' || event.type === 'remove') {
        streak = 0;
        state = { kind: event.type === 'dead' ? 'dead' : 'backtrack', frontier: event.frontier };
      }
      // A forced trial does not increment or interrupt the placement streak.
    },
    snapshot() { return { ...state }; }
  };
}
export function activityText(activity, coordinate) {
  if (!activity || activity.kind === 'ready') return 'ready';
  if (activity.kind === 'forced') return `${activity.count} forced move${activity.count === 1 ? '' : 's'}`;
  if (activity.kind === 'branch') return `${activity.count}-way branching at [${coordinate(activity.frontier)}]`;
  if (activity.kind === 'dead') return `dead end at [${coordinate(activity.frontier)}]`;
  return 'backtracking';
}
