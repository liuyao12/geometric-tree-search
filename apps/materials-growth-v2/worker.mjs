import { discover, learnSections } from "./learning.mjs";
import { MaterialExperiment } from "./material.mjs";
import { compareStructure } from "./metrics.mjs";
let grammar,
  marking,
  experiment,
  paused = true,
  deadline = 0,
  timer,
  revision = 0;
const send = (kind, data = {}) => postMessage({ kind, ...data });
const yieldUI = (ms = 0) => new Promise((resolve) => setTimeout(resolve, ms));
function snapshot(full = false) {
  const state = experiment.snapshot(full),
    origin = state.seedOrigin.origin;
  const reference = grammar.atoms.map((a) => ({
    ...a,
    position: a.position.map((v, k) => v - origin[k]),
  }));
  const generated =
    state.options.seedMode === "single"
      ? state.atoms
      : state.atoms.map((a) => ({
          ...a,
          position: a.position.map((v, k) => v - origin[k]),
        }));
  return { ...state, metrics: compareStructure(reference, generated) };
}
async function runGenerator(generator, token) {
  for (;;) {
    const next = generator.next();
    if (next.done) return next.value;
    if (token !== revision) throw Error("Cancelled");
    send(next.value.kind, next.value);
    await yieldUI(next.value.kind === "learning" ? 55 : 0);
  }
}
function tick() {
  if (paused) return;
  try {
    const until = performance.now() + 35;
    let event;
    do {
      event = experiment.step();
      if (["unknown", "complete", "exhausted", "budget"].includes(event.kind)) {
        paused = true;
        break;
      }
    } while (performance.now() < until && performance.now() < deadline);
    if (performance.now() >= deadline) paused = true;
    if (paused || !tick.last || performance.now() - tick.last > 600) {
      send("snapshot", { state: snapshot(), paused, event });
      tick.last = performance.now();
    }
    if (!paused) timer = setTimeout(tick, 0);
  } catch (error) {
    paused = true;
    send("error", { message: error.message });
  }
}
onmessage = async ({ data }) => {
  try {
    if (data.kind === "pause") {
      paused = true;
      clearTimeout(timer);
      if (experiment) send("snapshot", { state: snapshot(), paused });
      return;
    }
    if (data.kind === "discover") {
      paused = true;
      clearTimeout(timer);
      experiment = null;
      marking = null;
      const token = ++revision;
      grammar = await runGenerator(discover(data.atoms, data.options), token);
      send("discovered", { grammar });
    }
    if (data.kind === "learn") {
      paused = true;
      clearTimeout(timer);
      experiment = null;
      marking = await runGenerator(
        learnSections(grammar, data.options),
        ++revision,
      );
      send("learned", { marking });
    }
    if (data.kind === "grow") {
      if (!experiment)
        experiment = new MaterialExperiment(grammar, marking, data.options);
      paused = false;
      deadline = performance.now() + data.seconds * 1000;
      tick();
    }
    if (data.kind === "export" && experiment)
      send("artifact", { state: snapshot(true) });
    if (data.kind === "reset") {
      revision++;
      paused = true;
      clearTimeout(timer);
      experiment = null;
    }
  } catch (error) {
    send("error", { message: error.message });
  }
};
