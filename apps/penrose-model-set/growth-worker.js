import { createPenroseGrowth } from "../../assets/penrose-growth.js?v=20260907-contacts";

import { createMixedGrowth } from "../../assets/penrose-mixed-growth.js?v=20260907-contacts";

import { createSearchStatus } from "./search-status.js?v=20260907-activity";

let activity, search, done = false, computeMs = 0;
self.onmessage = ({ data }) => {
  try {
    if (data.type === "inspect") {
      self.postMessage({ type: "inspection", key: data.key, contacts: search.candidateContacts(data.extent) }); return;
    }
    let pausedCorona = null;
    if (data.type === "init") {
      const kinds = data.options.tileKinds || ["thick", "thin"];
      const classic = kinds.length === 2 && kinds.includes("thick") && kinds.includes("thin");
      search = (classic ? createPenroseGrowth : createMixedGrowth)(data.options); done = false; computeMs = 0;
      activity = createSearchStatus(); activity.accept(search.next().value);
    } else if (data.type === "advance" && search && !done) {
      const start = performance.now();
      for (let i = 0; i < Math.min(200, Math.max(1, data.events)); i++) {
        const step = search.next(); done = step.done; activity.accept(step.value);
        if (step.value?.type === "add" && Number.isInteger(data.targetCorona) && search.progress().minimumFrontierGeneration >= data.targetCorona && search.progress().deadPoints === 0) {
          pausedCorona = data.targetCorona; break;
        }
        if (done || performance.now() - start > 12) break;
      }
      computeMs += performance.now() - start;
    }
    self.postMessage({ ...search.snapshot(), done, computeMs, pausedCorona, activity: activity.snapshot() });
  } catch (error) {
    self.postMessage(data.type === "inspect" ? {type:"inspection",key:data.key,error:error.message} : { error: error.message, done: true });
  }
};
