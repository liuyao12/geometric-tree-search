import { createPenroseGrowth } from "../../assets/penrose-growth.js?v=20260907-extent";

let search, done = false, computeMs = 0;
self.onmessage = ({ data }) => {
  try {
    if (data.type === "init") {
      search = createPenroseGrowth(data.options); done = false; computeMs = 0;
      search.next();
    } else if (data.type === "advance" && search && !done) {
      const start = performance.now();
      for (let i = 0; i < Math.min(200, Math.max(1, data.events)); i++) {
        done = search.next().done;
        if (done || performance.now() - start > 12) break;
      }
      computeMs += performance.now() - start;
    }
    self.postMessage({ ...search.snapshot(), done, computeMs });
  } catch (error) {
    self.postMessage({ error: error.message, done: true });
  }
};
