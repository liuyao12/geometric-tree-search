import { discover, learnSections } from "./learning.mjs?v=sample-audit-1";
import { MaterialExperiment } from "./material.mjs?v=observed-overlaps-1";
import { compareStructure } from "./metrics.mjs";
import { CoronaCheckpoints } from "./coronas.mjs";
let grammar,
  marking,
  experiment,
  paused = true,
  checkpoints = new CoronaCheckpoints(),
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
  return {
    ...state,
    coronas: checkpoints.progress(experiment.engine),
    metrics: compareStructure(reference, generated),
  };
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
      const checkpoint = checkpoints.check(experiment.engine);
      if (checkpoint) {
        event = checkpoint;
        paused = true;
        break;
      }
    } while (performance.now() < until);
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
      if (!paused) return;
      clearTimeout(timer);
      if (!experiment) {
        checkpoints = new CoronaCheckpoints();
        experiment = new MaterialExperiment(grammar, marking, data.options);
      }
      paused = false;
      experiment.continueWithMoreMemory();
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
