import { createPenroseGrowth } from "../../assets/penrose-growth.js?v=20260907-corona";

let search, done = false, computeMs = 0;
self.onmessage = ({ data }) => {
  try {
    let pausedCorona = null;
    if (data.type === "init") {
      search = createPenroseGrowth(data.options); done = false; computeMs = 0;
      search.next();
    } else if (data.type === "advance" && search && !done) {
      const start = performance.now();
      for (let i = 0; i < Math.min(200, Math.max(1, data.events)); i++) {
        const step = search.next(); done = step.done;
        if (step.value?.type === "add" && Number.isInteger(data.targetCorona) && search.progress().minimumFrontierGeneration >= data.targetCorona) {
          pausedCorona = data.targetCorona; break;
        }
        if (done || performance.now() - start > 12) break;
      }
      computeMs += performance.now() - start;
    }
    self.postMessage({ ...search.snapshot(), done, computeMs, pausedCorona });
  } catch (error) {
    self.postMessage({ error: error.message, done: true });
  }
};
