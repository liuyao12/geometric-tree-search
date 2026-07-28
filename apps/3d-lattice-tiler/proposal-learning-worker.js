import { trainProposalProgram } from "./proposal-training.js?v=20260728-rgb-cells-v22";

let activeSequence = 0;
let stopToken = { stop: false };

const post = (sequence, payload) => {
  if (sequence === activeSequence) self.postMessage({ sequence, ...payload });
};

self.onmessage = async event => {
  const { type, sequence, config, options } = event.data ?? {};
  if (type === "stop") {
    stopToken.stop = true;
    return;
  }
  if (type !== "start") return;

  stopToken.stop = true;
  activeSequence = sequence;
  stopToken = { stop: false };
  try {
    const result = await trainProposalProgram(config, options, {
      stopToken,
      onProgress: progress => post(sequence, { type: "progress", progress })
    });
    if (stopToken.stop || sequence !== activeSequence) return;
    post(sequence, { type: "finished", result });
  } catch (error) {
    post(sequence, { type: "error", error: error?.message ?? String(error) });
  }
};
