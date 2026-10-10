'use strict';
/* Decode actual tile ports into an equation argument in logical cell order. */
function readWangTiles(row,proof){
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),cells=new Map();
 row.tiles.forEach((tile,tileIndex)=>tile.outputs.forEach(output=>{
  const slot=output.slot;if(cells.has(slot))throw Error('Two outputs at one reading cell');
  if(!tile.weights.some(([p,v])=>same(p,[2*slot,0])&&v===12)||!tile.marks.some(([p,v])=>same(p,[2*slot,1])&&v===output.formula_id))throw Error('Reading differs from tile point values');
  if(!tile.members.some(k=>k[0]===slot&&k[1]===output.rule_id&&same(k[2],output.references)))throw Error('Reading differs from tile members');
  cells.set(slot,{...output,tileIndex,formula:row.formulas[output.formula_id]});
 }));
 if(cells.size!==row.length)throw Error('Incomplete tile row reading');
 function difference(a,b,path=[]){
  if(same(a,b))throw Error('No changed subexpression');
  if(a[0]==='fun'&&b[0]==='fun'&&a[1]===b[1]&&a[2].length===b[2].length){
   const changed=a[2].map((t,i)=>same(t,b[2][i])?-1:i).filter(i=>i>=0);
   if(changed.length===1){const i=changed[0];return difference(a[2][i],b[2][i],path.concat(i));}
  }
  return {before:a,after:b,path};
 }
 function match(pattern,value,variables,bindings){
  if(pattern[0]==='var'&&variables.has(pattern[1])){if(bindings.has(pattern[1]))return same(bindings.get(pattern[1]),value);bindings.set(pattern[1],value);return true;}
  if(pattern[0]!==value[0]||pattern[1]!==value[1])return false;
  if(pattern[0]==='var')return same(pattern,value);
  return pattern[2].length===value[2].length&&pattern[2].every((t,i)=>match(t,value[2][i],variables,bindings));
 }
 function axiomInstance(label,before,after){
  let a=proof.theory.axioms[label];if(!a)throw Error('Missing equality axiom for tile reading');
  const variables=new Set();while(a[0]==='all'){variables.add(a[1]);a=a[2];}
  if(a[0]!=='eq')throw Error('Tile reading requires an equality axiom');
  for(const direction of [1,-1]){const bindings=new Map(),first=direction===1?1:2,second=direction===1?2:1;
   if(match(a[first],before,variables,bindings)&&match(a[second],after,variables,bindings))return {direction,axiom:proof.theory.axioms[label],bindings:Object.fromEntries(bindings)};
  }
  throw Error('Changed subexpression is not an instance of the named axiom');
 }
 const steps=[...cells.values()].sort((a,b)=>a.slot-b.slot);
 for(const step of steps){
  if(step.formula[0]!=='eq')throw Error('This reader supports equation tiles');
  if(!step.references.length){if(step.label!=='refl'||!same(step.formula[1],step.formula[2]))throw Error('Unrecognized starting tile');step.kind='start';continue;}
  if(step.references.length!==1||step.references[0]>=step.slot||!cells.has(step.references[0]))throw Error('Reading requires one earlier proof-cell premise');
  const source=cells.get(step.references[0]);
  if(!row.tiles[step.tileIndex].marks.some(([p,v])=>same(p,[2*source.slot,1])&&v===source.formula_id))throw Error('Premise port value differs from the reading');
  if(!same(source.formula[1],step.formula[1]))throw Error('Left expression changed in tile reading');
  const change=difference(source.formula[2],step.formula[2]);step.kind='rewrite';step.premise_formula=source.formula;step.change=change;step.instance=axiomInstance(step.label,change.before,change.after);
 }
 /* Follow actual premise ports; a placed tile need not be on the goal chain. */
 const chain=[];let cursor=steps[steps.length-1];
 if(cursor.formula_id!==row.target_id)throw Error('Reading target port mismatch');
 while(cursor){chain.push(cursor);cursor=cursor.references.length?cells.get(cursor.references[0]):null;}
 chain.reverse();
 const groups=[];
 for(let i=0;i<chain.length;){
  const first=chain[i],tile=row.tiles[first.tileIndex];let j=i+1;while(j<chain.length&&chain[j].tileIndex===first.tileIndex)j++;
  const covered=chain.slice(i,j),last=covered[covered.length-1];
  groups.push({tileIndex:first.tileIndex,kind:tile.kind,cells:covered.map(s=>s.slot),before:first.kind==='start'?first.formula[2]:first.premise_formula[2],after:last.formula[2],formula:last.formula,start:first.kind==='start',root_lines:tile.root_lines});i=j;
 }
 const closing_variables=[];let target=proof.target;
 while(target[0]==='all'){closing_variables.push(target[1]);target=target[2];}
 const conclusion=chain[chain.length-1].formula;
 if(!same(target,conclusion))throw Error('Tile row does not establish the theorem body');
 for(let i=0;i<closing_variables.length;i++){
  const line=proof.request.proof[proof.request.proof.length-1-i];
  if(line.rule!=='generalize'||line.variable!==closing_variables[i])throw Error('Missing checked universal closing step');
 }
 return {steps,chain,groups,closing_variables,starting_expression:chain[0].formula[2],conclusion};
}
if(typeof module!=='undefined')module.exports={readWangTiles};
