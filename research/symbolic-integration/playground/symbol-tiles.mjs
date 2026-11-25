import {selectPointBranch} from "../../../assets/gcts-point-branching.js";
import {zero, add, monomial, derivative, tasks} from "./rewrite-search.mjs";

// Each transition is one variant of one symbol. Neighbouring half-points
// carry its incoming and outgoing grammar states. e ^ x occupies three cells.
const variants = [];
function tile(from, symbol, to) {
  variants.push({from, symbol, to, variant: variants.length});
}
for (const from of ["start", "term", "factor"]) {
  tile(from, "x", "factor");
  tile(from, "e", "power");
}
for (const from of ["start", "factor"]) {
  tile(from, "+", "term");
  tile(from, "-", "term");
}
tile("power", "^", "exponent");
tile("exponent", "x", "factor");

export function readWord(word) {
  let state = "start", sum = zero, sign = 1, x = 0, exp = 0;
  function finishTerm() {
    sum = add(sum, monomial([x, exp, 0, 0], sign));
    x = 0; exp = 0;
  }
  for (const symbol of word) {
    const next = variants.find(tile => tile.from === state && tile.symbol === symbol);
    if (!next) throw Error("Invalid symbol at grammar seam");
    if (symbol === "+" || symbol === "-") {
      if (state === "factor") finishTerm();
      sign = symbol === "-" ? -1 : 1;
    } else if (symbol === "x") {
      if (state === "exponent") exp++; else x++;
    }
    state = next.to;
  }
  if (state !== "factor") throw Error("Incomplete expression");
  finishTerm();
  return sum;
}

const maxOffset = 7;
const pairKey = (distance, a, b) => distance + ":" + a + b;
function eachPair(word, visit) {
  for (let i = 0; i < word.length; i++)
    for (let j = i + 2; j < word.length && j <= i + maxOffset; j++)
      visit(pairKey(j-i, word[i], word[j]));
}

function clash(slot, candidate, board, marks) {
  for (let j = Math.max(0, slot-maxOffset); j <= Math.min(board.length-1, slot+maxOffset); j++) {
    const other = board[j], delta = Math.abs(slot-j);
    if (!other || delta < 2) continue;
    const key = slot < j ? pairKey(delta, candidate.symbol, other.symbol)
                         : pairKey(delta, other.symbol, candidate.symbol);
    if (marks.has(key)) return {source:j, slot, symbol:candidate.symbol, other:other.symbol, delta};
  }
  return null;
}

// Solve one finite strip of length n. The two endpoint caps each contribute
// a half. All centres (odd) and seams (even) have target value one and age zero.
export function searchRow(target, n, {seed=0, marks, onEvent, onChecked}={}) {
  let randomState = seed >>> 0;
  const random = () => (randomState = (Math.imul(randomState,1664525)+1013904223)>>>0)/4294967296;
  const board = Array(n).fill(null);
  const candidates = board.map((_, slot) => variants.filter(v =>
    (slot !== 0 || v.from === "start") && (slot !== n-1 || v.to === "factor")
  ).map(v => ({...v, slot, id:slot*variants.length+v.variant})));
  const stats = {placed:0, undone:0, checked:0, removed:0};

  function visit(depth, last) {
    if (depth === n) {
      const word = board.map(v => v.symbol).join("");
      const ok = derivative(readWord(word)).key === target.key;
      stats.checked++;
      onChecked?.(word, ok);
      if (!ok) onEvent?.({type:"miss"});
      return ok ? word : null;
    }
    const frontier = Array.from({length:2*n+1}, (_,id) => ({id, introducedAt:0, legal:[]}));
    const open = new Set();
    let witness;
    for (let i = 0; i < n; i++) {
      if (board[i]) continue;
      const points = frontier.slice(2*i, 2*i+3);
      for (const p of points) open.add(p);
      for (const candidate of candidates[i]) {
        if ((board[i-1] && board[i-1].to !== candidate.from) ||
            (board[i+1] && board[i+1].from !== candidate.to)) continue;
        if (marks?.size) {
          const conflict = clash(i, candidate, board, marks);
          if (conflict) { stats.removed++; witness ??= conflict; continue; }
        }
        for (const p of points) p.legal.push(candidate);
      }
    }
    if (witness && onEvent) onEvent({type:"mark", ...witness});
    const branch = selectPointBranch([...open], random, {
      isAdjacent: v => last !== null && Math.abs(v.slot-last) === 1
    });
    if (branch.dead) {
      onEvent?.({type:"dead", point:branch.dead.id});
      return null;
    }
    for (const {placement:v} of branch.moves) {
      board[v.slot] = v;
      stats.placed++;
      onEvent?.({type:"place",slot:v.slot,symbol:v.symbol});
      const result = visit(depth+1, v.slot);
      if (result !== null) return result;
      board[v.slot] = null;
      stats.undone++;
      onEvent?.({type:"undo",slot:v.slot,symbol:v.symbol});
    }
    return null;
  }
  return {word:visit(0,null), ...stats};
}

const x = monomial([1,0,0,0]), e = monomial([0,1,0,0]), one = monomial([0,0,0,0]);
const twiceX = add(x,x);
// Only these integrands and length bounds are shown to the training searches.
export const lessons = [
  [one,1], [e,3], [twiceX,2], [add(e,one),5], [add(e,one,-1n),5],
  [add(twiceX,e),6], [add(twiceX,e,-1n),6], [add(e,tasks[0][2]),4]
];
export function learnMarks() {
  const wins = new Set(), misses = new Map(), words = [];
  for (const [target, max] of lessons) {
    const seenWords = new Set();
    for (let n = 1; n <= max; n++) {
      const {word} = searchRow(target,n,{onChecked:(word,ok) => {
        if (seenWords.has(word)) return;
        seenWords.add(word);
        eachPair(word, key => {
          if (ok) wins.add(key); else misses.set(key,(misses.get(key)??0)+1);
        });
      }});
      if (word !== null) { words.push(word); break; }
    }
  }
  return {words, marks:new Set([...misses].filter(([k,count]) => count>=3 && !wins.has(k)).map(([k])=>k))};
}

export const rowProblems = {
  product: {target:tasks[0][2], max:8, tex:"x e^x"},
  control: {target:add(one,twiceX,-1n), max:4, tex:"1-2x"}
};

// Markings are empirical. Both passes get their turn at each word length.
export function runRows(problem, seed, marks, record=false) {
  let placed=0, undone=0, checked=0;
  for (let n=1; n<=problem.max; n++) {
    const events=[];
    for (const pass of (marks?.size ? [marks, null] : [null])) {
      if (record) events.push({type:"start", marked:!!pass, n});
      const run=searchRow(problem.target, n, {seed, marks:pass,
        onEvent:record ? event=>events.push(event) : undefined});
      placed+=run.placed; undone+=run.undone; checked+=run.checked;
      if (run.word || (n===problem.max && !pass)) {
        if(record)events.push({type:run.word?"solved":"open"});
        return {word:run.word, n, placed, undone, checked, events, marked:!!pass};
      }
    }
  }
}
