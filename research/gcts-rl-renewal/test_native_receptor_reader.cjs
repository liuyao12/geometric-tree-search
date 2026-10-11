'use strict';
const fs=require('fs'),path=require('path'),{validateReceptors}=require('../../docs/research/gcts-rl-renewal/native-receptor-points.js');
const p=path.join(__dirname,'../../docs/research/gcts-rl-renewal/native-receptor-points-reader-001.json'),v=JSON.parse(fs.readFileSync(p)),checks=validateReceptors(v),mutations=[];
function reject(name,edit){const b=structuredClone(v);edit(b);let failed=false;try{validateReceptors(b);}catch(e){failed=true;}if(!failed)throw Error('Mutation admitted: '+name);mutations.push(name);}
reject('palette fingerprint',b=>b.inventory.fingerprint='bad');reject('missing observation',b=>b.observations.pop());reject('original assertion',b=>b.proofs[0].request.target=['bot']);reject('native acceptance',b=>b.proofs[0].literal.status='rejected');reject('full operation count',b=>b.proofs[0].literal.micro_steps++);reject('final target role',b=>b.proofs[0].trace.records[b.proofs[0].trace.verification_query].query_target='prefix_final_formula');reject('source proof',b=>b.proofs[0].trace.proof[0].rule='tautology');reject('root rollback',b=>b.proofs[0].trace.search.root_restored=false);reject('line formula',b=>b.proofs[0].lines[0].label.formula=['bot']);reject('earlier facts',b=>b.proofs[0].lines[0].input.proved.push(['bot']));reject('pending commands',b=>b.proofs[0].lines[0].input.pending=[]);reject('new fact',b=>b.proofs[0].lines[0].output.proved=[]);reject('open premise',b=>b.proofs[0].lines[0].input.assumptions.push(['bot']));reject('context theory',b=>b.proofs[0].lines[0].input.theory.axioms.bad=['bot']);reject('native entry',b=>b.proofs[0].lines[0].q++);reject('crop timeline',b=>b.proofs[0].lines[0].patch.prefix_physical_steps++);reject('crop count',b=>b.proofs[0].lines[0].patch.tiles.pop());reject('original tile',b=>b.proofs[0].lines[0].patch.tiles[0].N++);reject('seam',b=>b.proofs[0].lines[0].patch.rows[1][1]++);reject('horizontal receptor',b=>b.proofs[0].lines[0].patch.tiles[0].W[0]++);reject('duplicate occupancy',b=>{const t=b.proofs[0].lines[0].patch.tiles;t[1].x=t[0].x;t[1].y=t[0].y;});
reject('missing original command',b=>b.proofs[0].trace.model.domains[0].pop());
reject('removed distant value',b=>b.proofs[2].trace.model.placements.at(-1).marks.pop());
reject('changed complete graph',b=>b.proofs[2].trace.search.tree.census[0].keys.pop());
reject('changed generation',b=>b.proofs[2].trace.search.tree.census[0].generation=9);
reject('invented native guard',b=>b.proofs[2].trace.compiled.tautologies.push(b.proofs[2].request.target));
reject('native guard query status',b=>b.proofs[2].trace.records[0].result.status='unknown_steps');
reject('missing original alternative',b=>b.proofs[2].trace.search.tree.children.pop());
reject('false guard occupancy',b=>b.proofs[2].trace.model.placements[0].occupancy[0][1]=6);
reject('missing untouched root',b=>b.proofs[2].trace.model.roots.pop());
reject('changed position identity',b=>b.proofs[2].trace.model.placements[0].key[0]=5);
console.log(JSON.stringify({status:'passed',checks,mutations_rejected:mutations},null,2));
