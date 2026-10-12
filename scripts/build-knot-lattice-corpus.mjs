import { readFileSync,writeFileSync } from 'node:fs';
import { gridLift,unitLoop,bounds,translationKey,mirror,searchInput } from '../research/knot-classifier/lattice-state.mjs';
const data=JSON.parse(readFileSync(process.argv[2],'utf8')),counts={},records=[];
for(const record of data.records) {
  const vertices=record.grid?gridLift(record.grid):[[0,0,0],[1,0,0],[1,1,0],[0,1,0]];
  const measurement=bounds(vertices);
  records.push({...record,vertices,unitEdges:measurement.edges});
  counts[record.crossings]=(counts[record.crossings]||0)+1;
  // Search input carries geometry only; all source names/labels are evaluator data.
  if(Object.keys(searchInput({ ...record,vertices })).join(',')!=='vertices')throw Error('Metadata leaked into search input.');
  if(unitLoop(mirror(vertices)).length!==measurement.edges)throw Error('Invalid mirror.');
}
const corpus={...data,version:'cubic-lattice-reference-v1',symmetries:'Translation, cyclic root and traversal reversal identify stored geometry; reflection remains separate.',records};
writeFileSync(process.argv[3],JSON.stringify(corpus)+'\n');
const summary={version:corpus.version,source:corpus.source,scope:corpus.scope,records:records.length,primeRecords:records.length-1,counts,
  geometry:'Exact closed self-avoiding integer polygons; vertical grid strands lifted one lattice unit above horizontal strands.',
  edgeRange:[Math.min(...records.map(r=>r.unitEdges)),Math.max(...records.map(r=>r.unitEdges))],
  allEmbedded:true,allMirrorsEmbedded:true,searchLabelsRemoved:true,
  uniqueLiteralEmbeddings:new Set(records.map(r=>translationKey(r.vertices))).size,
  classificationResults:0,claim:'A validated reference corpus, not successful classification.',
  inputLimit:'Crossing label bounds the reference knot type, not lattice edge count or intermediate projection complexity.'};
writeFileSync(new URL('../research/knot-classifier/lattice-corpus-validation.json',import.meta.url),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary));
