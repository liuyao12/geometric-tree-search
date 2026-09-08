import {pointCompletion,createLocalPairTeacher} from './cyclotomic-local-certificate.js';
import {createPairPointMarking} from './cyclotomic-pair-marking.js';
import {latticeKey,embedding} from './cyclotomic-five.js';
import {createFrontierGraph} from './tiling-frontier-graph.js';
import {createObstructionMarking} from './cyclotomic-obstruction-marking.js';
const priority=(key,seed)=>{let h=(2166136261^seed)>>>0;for(const c of key)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h;};
// Generic adapter: a finite catalog, exact base pair predicate and t support.
// Known-marking benchmarks may provide extraAllowed, but that predicate is
// deliberately unavailable to the learner and must not be used in learned mode.
export function createObstructionSearch({problem,learn=false,markingKind='pairs',train=true,initialCertificates=[],extraAllowed=null,targetCount=30,targetCorona=null,nodeLimit=10000,seed=1}){
  if(learn&&extraAllowed)throw Error('Learned mode cannot use a marking oracle');
  if(targetCorona!==null&&(!Number.isInteger(targetCorona)||targetCorona<1))throw Error('Corona target must be a positive integer');
  const {seedTile,movesAt,pairAllowed,footprint,pose,anchor,fullWeight}=problem;
  const active=[],ids=new Set(),totals=new Map(),positions=new Map(),depths=new Map(),frames=[];
  const weightAt=(t,p)=>{const i=t.vertices.indexOf(latticeKey(p));return i<0?0:t.weights[i];};
  const zero={coeff:[0,0,0,0],denominator:1},slots=movesAt(zero),capacityMasks=new Map();
  const capacityMask=total=>{if(!capacityMasks.has(total))capacityMasks.set(total,slots.reduce((m,t,i)=>weightAt(t,zero)+total>fullWeight?m|(1n<<BigInt(i)):m,0n));return capacityMasks.get(total);};
  let learner=learn&&markingKind==='pairs'?createPairPointMarking(problem):null;
  const proofLearner=learn&&train?createObstructionMarking({movesAt,pairAllowed,pose,anchor,slotCount:slots.length,capacityMask,unfinished:t=>t>0&&t<fullWeight,weightAt,pointTotal:p=>totals.get(latticeKey(p))||0,translate:problem.translate,onPairProof:markingKind==='pairs'?(a,b,p)=>learner.learnPair(a,b,p):null}):null;
  if(learn&&markingKind!=='pairs')learner=proofLearner;
  const localTeacher=learn&&train&&markingKind==='pairs'?createLocalPairTeacher(problem):null;
  if(initialCertificates.length&&!learner)throw Error('Certificates require learned mode');
  for(const proof of initialCertificates){
    const a=problem.resolve(proof.a.type,proof.a.origin),b=problem.resolve(proof.b.type,proof.b.origin),p=proof.point;
    if(!p)throw Error('Proof has no obstruction point');const total=weightAt(a,p)+weightAt(b,p);
    if(!pairAllowed(a,b)||!(total>0&&total<fullWeight)||(proof.method==='point-closure'?pointCompletion(problem,[a,b],p,{nodeLimit:0}).status!=='impossible':movesAt(p).some(c=>weightAt(c,p)+total<=fullWeight&&pairAllowed(a,c)&&pairAllowed(b,c))))throw Error('Invalid pair obstruction certificate');
    learner.learnPair(a,b,p,proof.method);
  }
  const stats={proposals:0,backtracks:0,forcedMoves:0,branches:0,deadPoints:0,peak:0,baseChecks:0,benchmarkChecks:0};
  let status='ready',stopped=false,event=null,minimumFrontierGeneration=0;
  function capacity(t){return!ids.has(t.id)&&!t.vertices.some((v,i)=>(totals.get(v)||0)+t.weights[i]>fullWeight);}
  function pair(a,b){stats.baseChecks++;if(!pairAllowed(a,b))return false;if(extraAllowed){stats.benchmarkChecks++;if(!extraAllowed(a,b))return false;}return true;}
  const graph=createFrontierGraph({enumerate:p=>movesAt(p.exact),footprint,
    legal:t=>capacity(t)&&!learner?.rejects(t)&&active.every(a=>pair(t,a)),
    compatibleWithAddition:(t,a)=>capacity(t)&&!learner?.rejects(t)&&pair(t,a)});
  const attach=delta=>{if(frames.length)frames.at(-1).push(...delta);};
  function refresh(){if(learner)attach(graph.refine(t=>!learner.rejects(t)));}
  function frontier(){const points=[];for(const[key,total]of totals)if(total>0&&total<fullWeight)points.push({key,total,exact:positions.get(key),depth:Math.min(...depths.get(key))});minimumFrontierGeneration=points.length?Math.min(...points.map(p=>p.depth)):null;return points;}
  function put(t){const near=t.vertices.flatMap(v=>depths.get(v)||[]);t.generation=near.length?Math.min(...near)+1:0;active.push(t);ids.add(t.id);t.vertices.forEach((v,i)=>{totals.set(v,(totals.get(v)||0)+t.weights[i]);positions.set(v,t.exactPoints[i]);if(!depths.has(v))depths.set(v,[]);depths.get(v).push(t.generation);});learner?.rebuild(active);}
  function remove(t){active.pop();ids.delete(t.id);t.vertices.forEach((v,i)=>{const total=totals.get(v)-t.weights[i];if(total)totals.set(v,total);else{totals.delete(v);positions.delete(v);}depths.get(v).pop();if(!depths.get(v).length)depths.delete(v);});learner?.rebuild(active);frontier();}
  const distance=p=>{const q=embedding(p.exact);return q.x*q.x+q.y*q.y;};
  const compare=(a,b)=>a.depth-b.depth||distance(a)-distance(b)||a.key.localeCompare(b.key);
  function* dfs(){while(true){
    refresh();const choice=graph.choose(compare);
    if(choice?.dead){stats.deadPoints++;const before=learner?.revision;proofLearner?.learn(choice.point.exact,active);if(learner?.revision===before)localTeacher?.learn(choice.point.exact,active,learner);learner?.rebuild(active);refresh();yield{type:'dead',frontier:choice.point.key};return false;}
    if(targetCorona===null?active.length>=targetCount:minimumFrontierGeneration===null||minimumFrontierGeneration>=targetCorona){status='target reached';return true;}
    if(stopped||stats.proposals>=nodeLimit){status='budget reached';stopped=true;return false;}
    if(!choice)return false;
    const options=choice.candidates.sort((a,b)=>priority(a.id,seed)-priority(b.id,seed)||a.id.localeCompare(b.id)),t={...options[0]};
    if(choice.forced)stats.forcedMoves++;else stats.branches++;
    stats.proposals++;yield{type:'try',tile:t,forced:choice.forced,branchCount:options.length,frontier:choice.point.key};
    put(t);const delta=graph.push(t,frontier());frames.push(delta);refresh();stats.peak=Math.max(stats.peak,active.length);yield{type:'add',tile:t,forced:choice.forced};
    if(yield*dfs())return true;if(stopped)return false;
    remove(t);graph.pop(frames.pop());stats.backtracks++;
    // A completely exhausted child is excluded only in this parent context.
    // This refinement, unlike globally learned masks, rolls back with the frame.
    attach(graph.refine(c=>c.id!==t.id&&!learner?.rejects(c)));yield{type:'remove',tile:t};
  }}
  function* run(){put({...seedTile});graph.build(frontier());stats.peak=1;status='searching';yield{type:'add',tile:active[0]};if(!(yield*dfs())&&!stopped)status='frontier exhausted';}
  const iterator=run();return{next(){const r=iterator.next();if(r.value)event=r.value;return r;},inspectGraph:()=>graph.inspect(),progress:()=>({minimumFrontierGeneration,deadPoints:graph.summary().deadPoints}),
    snapshot:()=>({tiles:active.slice(),stats:{...stats},status,event,minimumFrontierGeneration,graph:graph.summary(),learning:learner?{...learner.snapshot(),localTeacher:localTeacher?.snapshot()||null,proofSource:proofLearner?{...proofLearner.snapshot(),tables:undefined}:null}:null}),
    // Independent checker includes the local failed-child exclusions already
    // represented by the graph, so it verifies soundness, not equal domains.
    audit(){for(const p of graph.inspect())for(const id of p.candidates){const t=graph.candidateRecords().find(r=>r.tile.id===id).tile;if(!capacity(t)||!active.every(a=>pairAllowed(t,a))||learner?.rejects(t))throw Error('Stale legal candidate');}return true;}
  };
}
