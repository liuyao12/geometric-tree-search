/* Node checks exercise the same independent projection checker as the reader. */
const fs=require('fs'),path=require('path'),cryptoNode=require('crypto');
const root=path.resolve(__dirname,'../..'),docs=path.join(root,'docs/research/gcts-rl-renewal'),out=path.join(root,'.gcts-active/first-order-20261011');
const reader=require(path.join(docs,'first-order.js')),bytes=fs.readFileSync(path.join(docs,'first-order-reader-001.json')),data=JSON.parse(bytes);
const sha=b=>cryptoNode.createHash('sha256').update(b).digest('hex');
(async()=>{let checks=await reader.verified(data),tests=[];async function reject(name,edit){let d=structuredClone(data);edit(d);try{await reader.verified(d);}catch(e){tests.push({name,rejected:true,reason:e.message});return;}throw Error('corruption accepted: '+name);}
const first=d=>d.cases[0],eq=d=>d.cases.find(c=>c.spec.id==='equality-predicate'),capture=d=>d.cases.find(c=>c.spec.id==='capture-avoiding');
await reject('changed quantified term pool',d=>first(d).compiled.catalog.terms.pop());
await reject('incorrectly captured bound variable',d=>{let c=capture(d);c.compiled.catalog.schemes[0].formula=['imp',c.spec.theory.axioms.universal,['all','y',['pred','R',[['var','y'],['var','y']]]]];});
await reject('wrong equality template',d=>eq(d).compiled.admitted_schemes[0].variable='wrong');
await reject('omitted admitted scheme',d=>first(d).compiled.admitted_schemes.pop());
await reject('unresolved compiler query claimed complete',d=>{let id=first(d).compiled.queries.at(-1);d.native[id].result.status='unknown_test_budget';});
await reject('missing distant premise word',d=>{let t=first(d).observations[0].tiles.find(t=>t.requirements.length);t.marks.pop();});
await reject('missing whole word terminator',d=>first(d).observations[0].tiles[0].marks.pop());
await reject('wrong command type identity',d=>first(d).observations[0].tiles.find(t=>t.kind==='command').key[2]++);
await reject('changed initial target',d=>first(d).initial_marks.pop());
await reject('wrong native proof query',d=>first(d).observations[0].native_query=0);
await reject('future premise receptor',d=>{let t=first(d).observations[0].tiles.find(t=>t.requirements.length);t.requirements[0][0]=100;});
await reject('changed assigned value',d=>first(d).observations[0].tiles[0].marks[0][1]++);
await reject('unknown search carries acceptance',d=>{let o=first(d).observations[0];o.proof=null;o.tiles=[];o.status='unknown_search_budget';});
await reject('false exact acceptance reuse',d=>first(d).observations[0].cached_native_acceptance=true);
await reject('duplicate recorded lane',d=>first(d).observations.push(structuredClone(first(d).observations[0])));
await reject('native semantic request SHA mismatch',d=>d.native[0].request_sha256='0'.repeat(64));
let result={status:'passed',...checks,corruptions:tests,reader_sha256:sha(bytes),script_sha256:sha(fs.readFileSync(path.join(docs,'first-order.js'))),test_source_sha256:sha(fs.readFileSync(__filename))};fs.writeFileSync(path.join(out,'reader-corruptions.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',...checks,corruptions:tests.length}));})().catch(e=>{console.error(e);process.exitCode=1;});
