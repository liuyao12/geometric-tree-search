'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../..'),file=path.join(root,'docs/research/gcts-rl-renewal/semantic-inventory-reader-001.json');
const api=require(path.join(root,'docs/research/gcts-rl-renewal/semantic-inventory.js'));
async function main(){
 const v=JSON.parse(fs.readFileSync(file,'utf8')),result=api.validateView(v);await api.validatePins(v);const rejected=[];
 async function mutation(name,edit){const b=structuredClone(v);edit(b);let failed=false;try{api.validateView(b);await api.validatePins(b);}catch(e){failed=true;}assert(failed,'admitted '+name);rejected.push(name);}
 await mutation('changed-final-assertion',b=>b.proofs[0].request.target=['bot']);
 await mutation('changed-local-hypothesis',b=>{const p=b.proofs.find(p=>p.request.blocks.length);p.request.blocks[0].premises=[['bot']];});
 await mutation('changed-prior-native-fact',b=>b.proofs[0].lines[1].input.proved=[['bot']]);
 await mutation('lost-registered-interface',b=>{const p=b.proofs.find(p=>p.request.blocks.length);const l=p.lines.find(l=>l.label.scope==='root');l.input.registry.pop();});
 await mutation('future-root-reference',b=>{const p=b.proofs.find(p=>p.request.proof.some(c=>c.rule==='block'));p.request.proof.find(c=>c.rule==='block').inputs[0]=99;});
 await mutation('lost-input-factor',b=>{const p=b.proofs.find(p=>p.trace.selected.some(c=>c.kind==='lemma_input'));p.trace.selected.splice(p.trace.selected.findIndex(c=>c.kind==='lemma_input'),1);});
 await mutation('changed-distant-word',b=>{const p=b.proofs[0];p.trace.selected.find(c=>c.kind==='guard').marks[0][1]=999;});
 await mutation('changed-native-square',b=>b.proofs[0].lines[0].patch.tiles[0].N++);
 await mutation('changed-physical-expansion',b=>b.proofs[0].literal.physical_steps++);
 await mutation('seeded-policy-start',b=>b.training.episodes[0].weights_before[0]=1);
 await mutation('changed-softmax',b=>b.training.episodes.find(e=>e.search.events.length).search.events[0].probabilities[0]=.9);
 await mutation('changed-gradient',b=>b.training.episodes[0].learning.gradient[0]=9);
 await mutation('invented-template',b=>b.policy.library[0].template.proof[0].rule='induction');
 await mutation('changed-request-pin',b=>b.proofs[0].request_sha256='0'.repeat(64));
 await mutation('lost-cold-observation',b=>b.observations.pop());
 await mutation('invented-first-choice',b=>b.first_decisions[0].event.scores[0]=999);
 assert(api.formula(['all','x',['eq',['var','x'],['var','x']]]).includes('\\forall'));
 console.log(JSON.stringify({status:'passed',...result,mutations_rejected:rejected}));
}
main().catch(e=>{console.error(e.stack);process.exit(1);});
