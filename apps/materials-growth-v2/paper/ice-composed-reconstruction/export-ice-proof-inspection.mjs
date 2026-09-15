// Export support indices only; independently match the primary-source frame
// to the coordinate array used by the registered search before publishing.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {basename} from 'node:path';
import {pathToFileURL} from 'node:url';
const [dictionaryPath,coordinatesPath,visualPath,resultPath,stateCheckPath,proofCheckPath,out,dataModule]=process.argv.slice(2);
const read=p=>JSON.parse(readFileSync(p)),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const dictionary=read(dictionaryPath),coordinates=read(coordinatesPath),visual=read(visualPath),result=read(resultPath),check=read(stateCheckPath),proof=read(proofCheckPath);
assert.equal(check.sourceHashes[basename(resultPath)],sha(resultPath));assert.equal(check.sourceHashes[basename(coordinatesPath)],sha(coordinatesPath));assert.equal(check.sourceHashes[basename(dictionaryPath)],sha(dictionaryPath));assert.equal(proof.resultHash,sha(resultPath));
const c=visual.configurations.find(c=>c.id==='c01400'),source=coordinates.configurations.find(row=>row.id===c.id),d=dictionary.configurations.find(row=>row.id===c.id),verified=check.results[0];assert(verified.complete&&verified.enabled&&verified.id===c.id);
const {readSourceFrame,coverage}=await import(pathToFileURL(dataModule));
const frame=await readSourceFrame(c,{fetcher:(url,options)=>fetch(url,{...options,signal:AbortSignal.timeout(20000)})});
assert.deepEqual(frame.atoms.map(a=>a.position),source.positions);assert.deepEqual(frame.atoms.map(a=>a.species),source.species);assert.deepEqual(frame.cell,source.cell);
const supports=result.selected.map(id=>d.occurrences[Number(id.split(':')[0])].ids),totals=coverage({supports},c.atoms);assert(totals.every(t=>t===2));assert.equal(supports.length,verified.selectedPlacements);
const state={supports,totals,complete:true,commonValues:verified.checkedFieldPairs,supportComponents:verified.supportComponents,runHash:sha(resultPath),checkHash:sha(stateCheckPath),proofCheckHash:sha(proofCheckPath),search:true,massFraction:1};
writeFileSync(out,JSON.stringify({id:c.id,atoms:c.atoms,sourceOrder:c.sourceOrder,firstFrameHash:c.firstFrameHash,visualHash:sha(visualPath),exporterHash:sha(new URL(import.meta.url)),state,limits:'Verified finite registered filling with four support components. Support reveal is not the full restarted search history. Source coordinates fetched and checked, not bundled.'}),{flag:'wx'});
console.log(JSON.stringify({id:c.id,atoms:c.atoms,placements:supports.length,sourceMappingVerified:true,coordinateArraysExported:false}));
