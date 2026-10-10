'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const r=require('../../docs/research/gcts-rl-renewal/shared-wang.js');
const docs=path.resolve(__dirname,'../../docs/research/gcts-rl-renewal'),v=JSON.parse(fs.readFileSync(path.join(docs,'shared-wang-reader-001.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(fs.readFileSync(path.join(docs,v.source.file))),v.source.sha256);assert(r.validateSharedReader(v));
let rejected=0,tiles=0,lines=0;
const mutate=change=>{const bad=structuredClone(v);change(bad);assert.throws(()=>r.validateSharedReader(bad));rejected++;};
for(let c=0;c<v.cases.length;c++){
 const p=v.cases[c];
 for(let i=0;i<p.patch.tiles.length;i++){
  tiles++;for(const f of ['N','S','W','E','identity','triple','x','y'])mutate(q=>q.cases[c].patch.tiles[i][f]=null);
 }
 for(let i=0;i<p.tiles.length;i++){
  for(const change of [t=>t.formula=['bot'],t=>t.root_line=-1,t=>t.slot++,t=>t.refs.push(99)])mutate(q=>change(q.cases[c].tiles[i]));
  if(p.tiles[i].recipe.kind==='block')mutate(q=>q.cases[c].tiles[i].recipe.definition.conclusion=['bot']);
 }
 for(const change of [p=>p.inventory_fingerprint='changed',p=>p.literal.status='unknown_step_budget',p=>p.target=['bot'],p=>p.selected.micro_steps++,p=>p.patch.tiles.pop(),p=>p.primitive.at(-1).formula=['bot']])mutate(q=>change(q.cases[c]));
 for(const l of p.primitive){assert(r.formula(l.formula));lines++;}
}
mutate(q=>q.inventory.tile_types--);mutate(q=>q.inventory.fingerprint='changed');
assert.equal(tiles,130);assert.equal(lines,39);
console.log(JSON.stringify({cases:2,literal_squares:tiles,readable_cells:5,primitive_lines:lines,mutations_rejected:rejected}));
