import { createTilingStream, tileSpecs } from "./engine.js?v=20260819-internal-period-v92";

const MESSAGE_BATCH_INTERVAL_MS = 32;
const MESSAGE_BATCH_LIMIT = 256;

let activeSeq = 0;
let stopToken = { stop: false };
let streamIter = null;
let pauseReasons = new Set();
let resumeWaiter = null;
let pendingMessages = [];
let messageTimer = null;

const postForSeq = (seq, payload) => {
  if (seq !== activeSeq) return;
  self.postMessage({ seq, ...payload });
};

const wakeRunner = () => {
  if (!resumeWaiter) return;
  const resume = resumeWaiter;
  resumeWaiter = null;
  resume();
};

const waitWhilePaused = async (seq) => {
  while (pauseReasons.size && seq === activeSeq && !stopToken.stop) {
    await new Promise(resolve => { resumeWaiter = resolve; });
  }
};

const flushMessages = (seq) => {
  if (messageTimer) {
    clearTimeout(messageTimer);
    messageTimer = null;
  }
  if (!pendingMessages.length) return;
  const messages = pendingMessages;
  pendingMessages = [];
  postForSeq(seq, { type: "solver_messages", messages });
};

const queueSolverMessage = (seq, message) => {
  // Metadata-only snapshots have no renderable geometry and are superseded by
  // placement deltas or the next full snapshot.
  if (message?.type === "node_snapshot") return;

  if (message?.type === "full_update") {
    // A full snapshot supersedes every queued geometry delta before it while
    // retaining search-tree and learning telemetry.
    pendingMessages = pendingMessages.filter(item =>
      item?.type !== "full_update" && item?.type !== "placement_delta"
    );
  } else if (message?.type === "node_status" && message.status === "working") {
    for (let index = pendingMessages.length - 1; index >= 0; index--) {
      const prior = pendingMessages[index];
      if (prior?.type === "node_status" && prior.status === "working" && prior.id === message.id) {
        pendingMessages.splice(index, 1);
        break;
      }
    }
  }

  if (message?.type === "finished") {
    flushMessages(seq);
    postForSeq(seq, { type: "solver_message", message });
    return;
  }

  pendingMessages.push(message);
  if (pendingMessages.length >= MESSAGE_BATCH_LIMIT) {
    flushMessages(seq);
  } else if (!messageTimer) {
    messageTimer = setTimeout(() => flushMessages(seq), MESSAGE_BATCH_INTERVAL_MS);
  }
};

const stopCurrentRun = () => {
  stopToken.stop = true;
  streamIter = null;
  pendingMessages = [];
  pauseReasons.clear();
  if (messageTimer) {
    clearTimeout(messageTimer);
    messageTimer = null;
  }
  wakeRunner();
};

const runStream = async (seq, config) => {
  try {
    streamIter = createTilingStream(config, tileSpecs, stopToken);
    while (seq === activeSeq && !stopToken.stop && streamIter) {
      await waitWhilePaused(seq);
      if (seq !== activeSeq || stopToken.stop || !streamIter) break;

      const { value, done } = await streamIter.next();
      if (seq !== activeSeq || stopToken.stop) break;

      if (done) {
        postForSeq(seq, { type: "solver_idle" });
        break;
      }

      queueSolverMessage(seq, value);
      if (value?.type === "finished") break;
    }
  } catch (error) {
    postForSeq(seq, {
      type: "solver_error",
      error: error?.message ?? String(error)
    });
  } finally {
    if (seq === activeSeq) {
      flushMessages(seq);
      streamIter = null;
      postForSeq(seq, { type: "solver_idle" });
    }
  }
};

self.onmessage = (event) => {
  const { type, seq, config, reason = "ui" } = event.data ?? {};

  if (type === "start") {
    stopCurrentRun();
    activeSeq = seq;
    stopToken = { stop: false };
    pauseReasons.clear();
    runStream(seq, config);
    return;
  }

  if (type === "stop") {
    stopCurrentRun();
    return;
  }

  if (seq !== activeSeq) return;

  if (type === "pause") {
    pauseReasons.add(reason);
    return;
  }

  if (type === "resume") {
    pauseReasons.delete(reason);
    wakeRunner();
    return;
  }

};
