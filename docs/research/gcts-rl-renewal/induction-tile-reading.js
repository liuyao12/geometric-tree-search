'use strict';
/* Human-readable steps must be bound to actual formula ports and certificates. */
function readInductionTiles(record){
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),need=(v,s)=>{if(!v)throw Error(s);};
 const cells=new Map(record.tiles.map(t=>[t.slot,t]));
 need(cells.size===record.problem.length&&record.tiles.length===cells.size,'Complete unique proof cells');
 const subst=(a,x,t)=>a[0]==='var'?(a[1]===x?t:a):a[0]==='fun'?['fun',a[1],a[2].map(v=>subst(v,x,t))]:a[0]==='eq'?['eq',subst(a[1],x,t),subst(a[2],x,t)]:a[0]==='all'?['all',a[1],a[1]===x?a[2]:subst(a[2],x,t)]:[a[0],...a.slice(1).map(v=>subst(v,x,t))];
 const close=(a,names)=>names.reduceRight((v,x)=>['all',x,v],a);
 const at=(a,path)=>path.reduce((v,i)=>{need(v[0]==='fun'&&Number.isInteger(i)&&i>=0&&i<v[2].length,'Valid rewrite location');return v[2][i];},a);
 const put=(a,path,b)=>{if(!path.length)return b;const [i,...rest]=path;need(a[0]==='fun'&&i>=0&&i<a[2].length,'Valid replacement');return ['fun',a[1],a[2].map((v,j)=>i===j?put(v,rest,b):v)];};
 const steps=[...cells.values()].sort((a,b)=>a.slot-b.slot).map(tile=>{
  const formula=record.formulas[tile.formula_id],r=tile.reason,inputs=tile.refs.map(j=>{
   need(Number.isInteger(j)&&j<tile.slot&&cells.has(j),'Earlier premise cell');return cells.get(j);
  });
  need(tile.weights.length===1&&same(tile.weights[0],[[2*tile.slot,0],12]),'Exact cell occupancy');
  need(tile.marks.some(([p,v])=>same(p,[2*tile.slot,1])&&v===tile.formula_id),'Actual output marking');
  need(tile.input_ids.length===inputs.length&&inputs.every((t,i)=>t.formula_id===tile.input_ids[i]&&tile.marks.some(([p,v])=>same(p,[2*t.slot,1])&&v===t.formula_id)),'Actual premise markings');
  const line=record.request.proof[tile.root_line];need(line&&same(line.formula,formula),'Root certificate output');
  const inFormula=inputs.map(t=>record.formulas[t.formula_id]);
  if(r.kind==='block'){
   const def=record.request.blocks.find(b=>b.name===line.name);
   need(line.rule==='block'&&same(line.inputs,inputs.map(t=>t.root_line))&&def&&same(def.premises,inFormula)&&same(def.conclusion,formula),'Exact checked block interface');
  }else if(r.kind==='primitive')need(line.rule===r.witness.rule&&same(r.witness.formula,formula),'Primitive rule binding');
  else need(r.kind==='copy','Declared inference kind');
  let kind=r.operation||r.witness?.rule||r.kind,change=null,hypothesis=null,variable=null;
  if(kind==='refl')need(!inputs.length&&formula[0]==='eq'&&same(formula[1],formula[2]),'Reflexivity seed');
  else if(kind==='conditional-reflexivity'){
   need(!inputs.length&&formula[0]==='imp'&&formula[2][0]==='eq'&&same(formula[2][1],formula[2][2]),'Conditional reflexivity seed');hypothesis=formula[1];
  }else if(kind==='rewrite'||kind==='conditional-rewrite'){
   need(inputs.length===1,'One rewrite premise');let p=inFormula[0],q=formula;
   if(kind==='conditional-rewrite'){need(p[0]==='imp'&&q[0]==='imp'&&same(p[1],q[1])&&same(q[1],r.context.hypothesis),'Fixed hypothesis scope');hypothesis=q[1];p=p[2];q=q[2];}
   need(p[0]==='eq'&&q[0]==='eq'&&same(p[1],q[1])&&same(p[1],r.context.original)&&same(p[2],r.move.before)&&same(q[2],r.move.after),'Contextual rewrite output');
   let a=r.axiom==='fixed-induction-hypothesis'?hypothesis:record.problem.theory.axioms[r.axiom];need(a,'Declared axiom or fixed hypothesis');
   const names=[];while(a[0]==='all'){names.push(a[1]);a=a[2];}
   need(a[0]==='eq'&&same(Object.keys(r.move.bindings).sort(),names.slice().sort()),'Exact quantified bindings');
   for(const x of names)a=subst(a,x,r.move.bindings[x]);
   need(r.move.direction===1||r.move.direction===-1,'Rewrite direction');
   const before=a[r.move.direction===1?1:2],after=a[r.move.direction===1?2:1];
   need(same(at(p[2],r.move.path),before)&&same(put(p[2],r.move.path,after),q[2]),'Named equality instance at the actual location');
   change={before,after,path:r.move.path,axiom:r.axiom,direction:r.move.direction};
  }else if(kind==='generalize'){
   variable=r.witness.variable;need(inputs.length===1&&same(formula,['all',variable,inFormula[0]])&&line.source===inputs[0].root_line&&line.variable===variable,'Checked generalization');
  }else if(kind==='induction'){
   const names=[];let body=record.problem.target;while(body[0]==='all'){names.push(body[1]);body=body[2];}
   variable=r.variable;need(names.includes(variable)&&record.problem.theory.schemas.includes('nat-induction'),'Authorized induction alternative');
   const others=names.filter(x=>x!==variable),z=['fun','zero',[]],s=['fun','succ',[['var',variable]]];
   const base=close(subst(body,variable,z),others),step=close(['all',variable,['imp',body,subst(body,variable,s)]],others);
   need(same(inFormula,[base,step])&&same(formula,record.problem.target),'Base and successor obligations establish the target');
  }else need(kind==='copy'&&inputs.length===1&&same(formula,inFormula[0]),'Copy preserves the formula');
  return {...tile,formula,kind,change,hypothesis,variable};
 });
 need(steps.every((s,i)=>s.slot===i)&&same(steps[steps.length-1].formula,record.problem.target),'Exact final theorem');
 return steps;
}
if(typeof module!=='undefined')module.exports={readInductionTiles};
