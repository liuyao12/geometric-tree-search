import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {scrambleLattice} from '../research/knot-classifier/lattice-scramble.mjs';
const args=process.argv.slice(2),get=(n,d)=>args.find(a=>a.startsWith(`--${n}=`))?.slice(n.length+3)??d;
const directory=get('directory','/private/tmp/knot-blind35');mkdirSync(directory,{recursive:true});
const records=JSON.parse(readFileSync('research/knot-classifier/lattice-corpus-12.json')).records.filter(r=>r.crossings>=3&&r.crossings<=8);
if(records.length!==35)throw Error('Expected complete 35-prime corpus.');
const started=performance.now(),steps=8,maxEdges=240,references=[],cases=[];
for(const [i,r]of records.entries()){
 const seed=31013+i*7919,reference=scrambleLattice(r.vertices,{steps,seed,maxEdges});
 references.push({evaluatorKnot:r.id,crossings:r.crossings,seed,vertices:reference.vertices,provenance:reference.provenance});
 for(let j=0;j<3;j++){
  const inputSeed=81017+i*104729+j*15485863,input=scrambleLattice(r.vertices,{steps,seed:inputSeed,maxEdges});
  cases.push({evaluatorKnot:r.id,crossings:r.crossings,seedIndex:j,inputSeed,vertices:input.vertices,provenance:input.provenance});
 }
 console.log(JSON.stringify({preparedType:i+1,knot:r.id,queries:cases.length}));
}
function shuffle(array,seed){let state=seed>>>0;for(let i=array.length-1;i>0;i--){state=(1664525*state+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[array[i],array[j]]=[array[j],array[i]];}return array;}
shuffle(references,515151);shuffle(cases,424242);
const manifest={version:'blind-lattice-prime35-v1',incomplete:true,region:null,stepsPerIndependentScramble:steps,seedCount:3,referenceOrderSeed:515151,queryOrderSeed:424242,references,cases,preparationMs:performance.now()-started,bounds:{maxDepth:16,maxEdges,nodeCap:5000,stateCap:100000,maxMs:6000,extensionProbeNodeCap:512,rootProbeNodeCap:64,seed:31},scope:'All 35 prime reference types through eight crossings, one independently eight-move-scrambled bank embedding per type and three fresh independent eight-move input scrambles per type. Fixed seeded bank and query permutations. No discarded/replaced case. Histories and evaluator labels stay outside the classifier; only vertex arrays enter it. Move locations unrestricted. Sixteen moves is a declared finite horizon, not minimum scramble distance or a crossing cap.'};
writeFileSync(`${directory}/manifest.json`,JSON.stringify(manifest)+'\n');console.log(JSON.stringify({prepared:true,preparationMs:manifest.preparationMs}));
