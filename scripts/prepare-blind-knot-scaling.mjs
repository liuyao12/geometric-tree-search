import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {scrambleLattice} from '../research/knot-classifier/lattice-scramble.mjs';
const args=process.argv.slice(2),get=(n,d)=>args.find(a=>a.startsWith(`--${n}=`))?.slice(n.length+3)??d;
const directory=get('directory','/private/tmp/knot-blind12');mkdirSync(directory,{recursive:true});
const raw=readFileSync('research/knot-classifier/lattice-corpus-12.json'),records=JSON.parse(raw).records.filter(r=>r.crossings>=3&&r.crossings<=12);
if(records.length!==2977)throw Error('Incomplete 12-crossing prime corpus');
// Predeclare the first and last corpus type of each new crossing cohort.
const chosen=[9,10,11,12].flatMap(n=>{const group=records.filter(r=>r.crossings===n);return[group[0].id,group.at(-1).id];});
const started=performance.now(),references=[],cases=[],steps=8,maxEdges=240;
for(const [i,r]of records.entries()){
 const selected=chosen.includes(r.id),seed=selected?57011+i*7919:null;
 const reference=selected?scrambleLattice(r.vertices,{steps,seed,maxEdges}):{vertices:r.vertices,provenance:null};
 references.push({evaluatorKnot:r.id,crossings:r.crossings,seed,vertices:reference.vertices,provenance:reference.provenance});
 if(selected)for(let j=0;j<3;j++){
  const inputSeed=97003+i*104729+j*15485863,input=scrambleLattice(r.vertices,{steps,seed:inputSeed,maxEdges});
  cases.push({evaluatorKnot:r.id,crossings:r.crossings,seedIndex:j,inputSeed,vertices:input.vertices,provenance:input.provenance});
 }
 if(selected)console.log(JSON.stringify({prepared:r.id,queries:cases.length}));
}
function shuffle(array,seed){for(let i=array.length-1;i>0;i--){seed=(1664525*seed+1013904223)>>>0;const j=Math.floor(seed/4294967296*(i+1));[array[i],array[j]]=[array[j],array[i]];}return array;}
shuffle(references,717171);shuffle(cases,626262);
const manifest={version:'blind-lattice-scale12-v1',incomplete:true,stage:'scale12',region:null,corpusSha256:createHash('sha256').update(raw).digest('hex'),selectedTypes:chosen,stepsPerIndependentScramble:steps,seedCount:3,referenceOrderSeed:717171,queryOrderSeed:626262,references,cases,preparationMs:performance.now()-started,bounds:{searchSeeds:get('search-seeds','31,73,131,197').split(',').map(Number),wholeWindowChildren:true,maxDepth:16,maxEdges,nodeCap:Number(get('node-cap','5000')),stateCap:100000,maxMs:Number(get('max-ms','120000')),extensionProbeNodeCap:512,rootProbeNodeCap:64,seed:31},scope:'Complete 2977-prime bank through 12 crossings. Representative pilot queries for first and last corpus types at each crossing count 9 through 12, three fresh independent eight-step scrambles per selected type. The eight selected bank representatives also independently scrambled eight steps; the remaining 2969 bank embeddings are canonical. Fixed permutations, no discarded/replaced cases. Labels, counts, seeds and histories stay outside the classifier. All lattice move locations remain unrestricted. This is not exhaustive query coverage of the 2977 types.'};
writeFileSync(`${directory}/manifest.json`,JSON.stringify(manifest)+'\n');console.log(JSON.stringify({prepared:true,preparationMs:manifest.preparationMs,bank:references.length,queries:cases.length}));
