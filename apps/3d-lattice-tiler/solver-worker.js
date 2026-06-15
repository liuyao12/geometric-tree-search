import { createTilingStream, tileSpecs } from "./engine.js?v=20260615-geometric-solid-angles";

const SNAPSHOT_INTERVAL_MS = 80;

let activeSeq = 0;
let stopToken = { stop: false };
let streamIter = null;
let paused = false;
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
  while (paused && seq === activeSeq && !stopToken.stop) {
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
  if (message?.type === "full_update" || message?.type === "node_snapshot") {
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
  const { type, seq, config } = event.data ?? {};

  if (type === "start") {
    stopCurrentRun();
    activeSeq = seq;
    stopToken = { stop: false };
    paused = false;
    runStream(seq, config);
    return;
  }

  if (type === "stop") {
    stopCurrentRun();
    return;
  }

  if (seq !== activeSeq) return;

  if (type === "pause") {
    paused = true;
    return;
  }

  if (type === "resume") {
    paused = false;
    wakeRunner();
    return;
  }

};
