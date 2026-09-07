import { identifyClusters, trainMarking } from "./continuous-learning.mjs";
import { ContinuousSearch } from "./continuous-search.mjs";
let grammar = null,
  search = null,
  running = false,
  deadline = 0,
  task = 0;
const send = (type, payload = {}) => postMessage({ type, ...payload });
async function drain(iterator, kind, token) {
  let result;
  let last = performance.now();
  while (!(result = iterator.next()).done) {
    if (token !== task) return null;
    if (kind === "training" || performance.now() - last > 30) {
      send(kind, result.value);
      await new Promise((r) => setTimeout(r, kind === "training" ? 35 : 0));
      last = performance.now();
    }
  }
  return result.value;
}
function snapshot(events = []) {
  send("search", {
    atoms: search.spatial.records,
    receipt: search.receipt(),
    events,
    rlStates: search.values.size,
  });
}
function tick() {
  if (!running || !search) return;
  const start = performance.now(),
    events = [];
  while (performance.now() - start < 25 && performance.now() < deadline) {
    const e = search.advance();
    events.push(e, ...search.events.splice(0));
    if (e.type === "paused" || e.type === "exhausted") {
      running = false;
      break;
    }
  }
  if (performance.now() >= deadline) running = false;
  snapshot(events);
  if (running) setTimeout(tick, 0);
  else send("paused");
}
self.onmessage = async ({ data }) => {
  try {
    if (data.type === "identify") {
      running = false;
      const token = ++task;
      grammar = await drain(
        identifyClusters(data.atoms, data.options),
        "discovery",
        token,
      );
      if (grammar) send("identified", { grammar });
    }
    if (data.type === "train") {
      const token = ++task;
      const model = await drain(
        trainMarking(grammar, data.options),
        "training",
        token,
      );
      if (model) send("trained", { model });
    }
    if (data.type === "initialize") {
      running = false;
      search = new ContinuousSearch(grammar, data.options);
      snapshot();
    }
    if (data.type === "run") {
      if (!search) throw Error("Initialize the search first.");
      if (running) return;
      running = true;
      deadline = performance.now() + data.milliseconds;
      tick();
    }
    if (data.type === "step") {
      if (!search) throw Error("Initialize the search first.");
      const events = [];
      let e;
      do {
        e = search.advance();
        events.push(e, ...search.events.splice(0));
      } while (e.type === "evaluating");
      snapshot(events);
    }
    if (data.type === "pause") {
      running = false;
      send("paused");
    }
    if (data.type === "budget" && search) {
      search.setAtomBudget(data.maximumAtoms);
      snapshot();
    }
    if (data.type === "best") {
      if (search)
        send("best", { atoms: search.best, receipt: search.receipt() });
    }
    if (data.type === "view" && search) snapshot();
  } catch (error) {
    running = false;
    send("error", { message: error.message, stack: error.stack });
  }
};
