import { createTilingStream, tileSpecs } from "./engine.js?v=20260706-live-deltas";

const SNAPSHOT_INTERVAL_MS = 260;

let activeSeq = 0;
let stopToken = { stop: false };
let streamIter = null;
let pauseReasons = new Set();
let resumeWaiter = null;
let pendingSnapshot = null;
let snapshotTimer = null;

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

const flushSnapshot = (seq) => {
  if (snapshotTimer) {
    clearTimeout(snapshotTimer);
    snapshotTimer = null;
  }
  if (!pendingSnapshot) return;
  const message = pendingSnapshot;
  pendingSnapshot = null;
  postForSeq(seq, { type: "solver_message", message });
};

const queueSolverMessage = (seq, message) => {
  if (message?.type === "full_update") {
    if ((message.tile_count ?? 0) <= 1) {
      flushSnapshot(seq);
      postForSeq(seq, { type: "solver_message", message });
      return;
    }
    pendingSnapshot = message;
    if (!snapshotTimer) {
      snapshotTimer = setTimeout(() => flushSnapshot(seq), SNAPSHOT_INTERVAL_MS);
    }
    return;
  }

  if (message?.type === "finished") flushSnapshot(seq);
  postForSeq(seq, { type: "solver_message", message });
};

const stopCurrentRun = () => {
  stopToken.stop = true;
  streamIter = null;
  pendingSnapshot = null;
  pauseReasons.clear();
  if (snapshotTimer) {
    clearTimeout(snapshotTimer);
    snapshotTimer = null;
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
      flushSnapshot(seq);
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
