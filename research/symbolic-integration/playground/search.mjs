import {selectPointBranch} from "../../../assets/gcts-point-branching.js";

// All exported problems have integer coefficients and signed unit diagonal pivots.
export function coefficients(rows, word, columns) {
  const residual = rows.map(row => [...row]), factors = Array(word.length).fill(0);
  for (let j = word.length - 1; j >= 0; j--) {
    const column = columns[j][word[j]];
    const pivot = column[j].findIndex(value => value !== 0);
    if (pivot < 0 || Math.abs(column[j][pivot]) !== 1) throw Error("Unsupported coefficient pivot");
    factors[j] = residual[j][pivot] / column[j][pivot];
    for (let k = 0; k <= j; k++) for (let h = 0; h < 3; h++) {
      residual[k][h] -= factors[j] * column[k][h];
      if (!Number.isSafeInteger(residual[k][h])) throw Error("Inexact coefficient arithmetic");
    }
    if (residual[j].some(value => value !== 0)) return {degree:j, residual:residual[j]};
  }
  return {factors};
}

function head(rows) {
  return rows[rows.length-1].map((v,h) => v ? String(h) : "").filter(Boolean).join("+");
}

export function emptyMemory() { return {top:new Set(), pairs:new Set()}; }

export function learn(memory, task, run) {
  if (!run.word) throw Error("Only a checked solution can enter training");
  const word = run.word;
  memory.top.add(head(task.rows) + "/" + word[word.length-1]);
  for (let j=1; j<word.length; j++) memory.pairs.add(word[j] + "/" + word[j-1]);
}

function permits(memory, leading, j, h, word) {
  if (!memory) return true;
  if (j === word.length-1 && !memory.top.has(leading + "/" + h)) return false;
  if (j > 0 && word[j-1] !== null && !memory.pairs.has(h + "/" + word[j-1])) return false;
  if (j+1 < word.length && word[j+1] !== null && !memory.pairs.has(word[j+1] + "/" + h)) return false;
  return true;
}

export function search(task, columns, seed, memory=null, budget=512) {
  let state = seed >>> 0;
  const random = () => ((state = (Math.imul(state,1664525)+1013904223) >>> 0) / 4294967296);
  const events = [], seen = new Set();
  const stats = {placements:0, backtracks:0, candidates:0};
  const note = (type, word, detail={}) => events.push({type, word, ...stats, ...detail});
  if (!task.rows) {
    note("unsupported", []);
    return {word:null, events, ...stats};
  }
  const size = task.rows.length, leading = head(task.rows);
  const empty = Array(size).fill(null);
  const tiles = empty.map((_,j) => [0,1,2].map(h => ({
    id:j+"/"+h, j, h, support:["degree"+j, ...(j ? ["seam"+(j-1)] : []),
      ...(j+1 < size ? ["seam"+j] : [])]
  })));
  function visit(word, last, marks) {
    if (!word.includes(null)) {
      const key = word.join(",");
      if (seen.has(key)) return null;
      seen.add(key);
      stats.candidates++;
      const test = coefficients(task.rows, word, columns);
      note(test.factors ? "verified" : "rejected", word, test);
      return test.factors ? word : null;
    }
    const domains = new Map();
    for (let j=0; j<size; j++) {
      if (word[j] !== null) continue;
      domains.set("degree"+j, []);
      for (const tile of tiles[j]) {
        if (!permits(marks, leading, j, tile.h, word)) continue;
        for (const point of tile.support) {
          if (!domains.has(point)) domains.set(point, []);
          domains.get(point).push(tile);
        }
      }
    }
    const frontier = [...domains].map(([id,legal]) => ({id, legal, introducedAt:0}));
    const branch = selectPointBranch(frontier, random,
      {isAdjacent:tile => tile.support.some(point => last.includes(point))});
    if (branch.dead) note("dead",word,{point:branch.dead.id});
    for (const {placement:tile, frontier:point} of branch.moves) {
      if (stats.placements >= budget) break;
      const child = word.slice(); child[tile.j] = tile.h;
      stats.placements++;
      note("place",child,{j:tile.j,h:tile.h,point:point.id,forced:branch.forced,choices:branch.moves.length});
      const answer = visit(child,tile.support,marks);
      if (answer) return answer;
      stats.backtracks++;
      note("rollback",word,{j:tile.j,h:tile.h});
    }
    return null;
  }
  note("start",empty);
  for (const marks of (memory ? [memory,null] : [null])) {
    if (stats.placements >= budget) break;
    if (memory && !marks) note("fallback",empty);
    const word = visit(empty,[],marks);
    if (word) return {word,events,...stats};
  }
  note(stats.placements >= budget ? "budget" : "exhausted", empty);
  return {word:null,events,...stats};
}
