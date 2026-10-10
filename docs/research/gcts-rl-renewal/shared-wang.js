'use strict';
const FIXED_INVENTORY='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455';
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function coreOutput(v,triple){
 const A=v.inventory.symbols,Q=v.inventory.states;
 const decode=s=>{if(!Number.isInteger(s)||s<0||s>=A*(Q+1))throw Error('Bad symbol');return s<A?null:[Math.floor((s-A)/A),(s-A)%A];};
 const [a,b,c]=triple,h=triple.map(decode);
 if(h.filter(Boolean).length>1)throw Error('Multiple heads');
 const delta=x=>{const row=v.transition_rows[x[0]];if(!row)throw Error('Unbound table row');return row[x[1]];};
 if(h[1]){
  if(h[1][0]===v.inventory.accept)return b;
  const action=delta(h[1]);if(!action)throw Error('Undefined central action');
  return action[2]===0?A+A*action[0]+action[1]:action[1];
 }
 for(const [i,d] of [[0,1],[2,-1]])if(h[i]&&h[i][0]!==v.inventory.accept){const action=delta(h[i]);if(action&&action[2]===d)return A+A*action[0]+b;}
 return b;
}
function validateSharedReader(v){
 if(v.audit.status!=='passed'||v.inventory.fingerprint!==FIXED_INVENTORY||v.cases.length!==2)throw Error('Shared identity');
 const A=v.inventory.symbols,Q=v.inventory.states;
 if(A!==60||Q!==462276||v.inventory.tile_types!==264143617200)throw Error('Changed inventory');
 v.cases.forEach(p=>{
  if(p.inventory_fingerprint!==FIXED_INVENTORY||p.literal.status!=='accepted'||p.selected.status!=='accepted')throw Error('Unaccepted query');
  for(const k of ['micro_steps','physical_steps','micro_fnv64'])if(p.literal[k]!==p.selected[k])throw Error('Execution mismatch');
  if(!eq(p.target,p.request.target)||!eq(p.theory,p.request.theory)||!eq(p.primitive.at(-1).formula,p.target)||!eq(p.request.proof.at(-1).formula,p.target))throw Error('Changed theorem');
  p.tiles.forEach((t,j)=>{
   if(t.slot!==j||!eq(p.request.proof[t.root_line]?.formula,t.formula))throw Error('Changed readable cell');
   if(t.refs.some(k=>!Number.isInteger(k)||k<0||k>=j))throw Error('Changed earlier receptor');
   if(t.recipe.kind==='block'){
    const block=t.recipe.definition;if(!eq(block.conclusion,t.formula)||block.premises.length!==t.refs.length||t.refs.some((k,i)=>!eq(block.premises[i],p.tiles[k].formula)))throw Error('Changed lemma interface');
    const command=p.request.proof[t.root_line];if(command.rule!=='block'||command.name!==block.name||!eq(command.inputs,t.refs.map(k=>p.tiles[k].root_line)))throw Error('Changed block command');
   }else if(t.recipe.kind==='primitive'&&!eq(t.recipe.witness.formula,t.formula))throw Error('Changed primitive');
  });
  const patch=p.patch,seen=new Set();
  if(patch.tiles.length!==patch.width*patch.height||patch.rows.length!==patch.height+1)throw Error('Incomplete crop');
  patch.tiles.forEach(t=>{
   if(!Number.isInteger(t.x)||!Number.isInteger(t.y)||t.x<0||t.y<0||t.x>=patch.width||t.y>=patch.height)throw Error('Crop placement');
   const key=`${t.x},${t.y}`;if(seen.has(key))throw Error('Repeated occupancy');seen.add(key);
   const [a,b,c]=patch.rows[t.y].slice(t.x,t.x+3),n=coreOutput(v,[a,b,c]);
   if(!eq(t.triple,[a,b,c])||t.identity!==[a,b,c].join(':')||t.S!==b||t.N!==n||patch.rows[t.y+1][t.x+1]!==n||!eq(t.W,[a,b])||!eq(t.E,[b,c]))throw Error('Changed literal Wang tile');
  });
 });return true;
}
function formula(a){
 const f=formula,k=a[0],name=s=>String(s).replace(/[^A-Za-z0-9]/g,'');
 if(k==='var')return name(a[1]);
 if(k==='bot')return '\\bot';
 if(k==='fun'){
  if(a[1]==='zero')return '0';if(a[1]==='succ')return 'S('+f(a[2][0])+')';
  if(a[1]==='add'||a[1]==='mul')return '('+f(a[2][0])+(a[1]==='add'?'+':'\\cdot ')+f(a[2][1])+')';
  return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 }
 if(k==='pred')return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 if(k==='eq')return f(a[1])+'='+f(a[2]);
 if(k==='all')return '\\forall '+name(a[1])+'\\;('+f(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+name(a[1][1])+'\\;('+f(a[1][2][1])+')';
 if(k==='not')return '\\neg('+f(a[1])+')';
 if(['imp','and','or'].includes(k))return '('+f(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+f(a[2])+')';
 throw Error('Unknown syntax');
}
const reason={axiom:'Use the named axiom from the input theory.',refl:'A term equals itself.',tautology:'This formula is a checked propositional tautology.',instantiate:'Instantiate a universal formula using capture-avoiding substitution.',mp:'Apply the earlier implication to its earlier antecedent.',generalize:'Universally quantify the variable; it is absent from every open premise.',eq_subst:'Substitute equal terms in the indicated formula.',distribute:'Move the quantifier across an implication with the variable condition checked.',induction:'Use the explicitly authorized natural-number induction schema.',assumption:'Use an input premise of this local block.',block:'Apply a previously checked lemma to the matching earlier premises.'};
if(typeof module!=='undefined')module.exports={validateSharedReader,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let view,chosen=0,selected=6;
 const math=a=>'\\('+formula(a)+'\\)';
 const typeset=()=>window.MathJax?.typesetPromise?.([el('theorem'),el('semantic-reading'),el('primitive')]).catch(e=>{el('load').textContent='Math rendering error: '+e.message;});
 function symbol(s){const A=view.inventory.symbols;return s<A?view.inventory.alphabet[s]:`${Math.floor((s-A)/A)}:${view.inventory.alphabet[(s-A)%A]}`;}
 function color(value,layer){const words=Array.isArray(value)?value:[value];let n=17;for(const w of words)n=(Math.imul(n,31)+w)>>>0;return `hsl(${layer==='vertical'?205+n%30:140+n%35} 58% ${38+n%24}%)`;}
 function draw(){
  const p=view.cases[chosen].patch,size=77,ox=43,oy=26,mode=el('mark-view').value;
  let svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ox+p.width*size+20} ${oy+p.height*size+28}" role="img" aria-label="Exact local Wang tiles, time upward; blue symbol and green pair marking layers"><text x="6" y="15" fill="#536157" font-size="12">time ↑</text>`;
  p.tiles.forEach((t,j)=>{
   const x=ox+t.x*size,y=oy+(p.height-1-t.y)*size,head=t.triple.some(s=>s>=view.inventory.symbols);
   const edge=(v,layer)=>mode==='all'||mode===layer?color(v,layer):'#e0e5de';
   svg+=`<g class="literal-cell" tabindex="0" role="button" aria-label="Square ${t.x}, ${t.y}${head?', head neighborhood':''}" data-cell="${j}"><rect x="${x+1}" y="${y+1}" width="${size-2}" height="${size-2}" fill="${head?'#fff3d9':'#f8faf6'}" stroke="${j===selected?'#935bae':'#aebbb0'}" stroke-width="${j===selected?4:1}"/><rect x="${x+7}" y="${y+2}" width="${size-14}" height="7" fill="${edge(t.N,'vertical')}"/><rect x="${x+7}" y="${y+size-9}" width="${size-14}" height="7" fill="${edge(t.S,'vertical')}"/><rect x="${x+2}" y="${y+9}" width="7" height="${size-18}" fill="${edge(t.W,'horizontal')}"/><rect x="${x+size-9}" y="${y+9}" width="7" height="${size-18}" fill="${edge(t.E,'horizontal')}"/><circle cx="${x+size/2}" cy="${y+size/2}" r="3" fill="#242a28"/><text x="${x+size/2}" y="${y+26}" text-anchor="middle" font-size="10" font-family="monospace" fill="#274453">${esc(symbol(t.N))}</text><text x="${x+size/2}" y="${y+size-18}" text-anchor="middle" font-size="10" font-family="monospace" fill="#274453">${esc(symbol(t.S))}</text></g>`;
  });
  svg+='</svg>';el('patch-svg').innerHTML=svg;
  el('patch-svg').querySelectorAll('[data-cell]').forEach(node=>{const click=()=>{selected=Number(node.dataset.cell);draw();};node.addEventListener('click',click);node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();click();}});});
  const t=p.tiles[selected],format=v=>Array.isArray(v)?'['+v.map(symbol).join(', ')+']':symbol(v);
  el('literal-detail').innerHTML=`<b>Selected literal square · cell ${t.x}, ${t.y}</b><p>Tile identity <code>${esc(t.identity)}</code>. Input neighborhood <code>${esc(t.triple.map(symbol).join(' | '))}</code>.</p><div class="table-scroll"><table><tbody>${[['South · input',t.S],['North · output',t.N],['West · overlap',t.W],['East · overlap',t.E]].map(([label,value])=>`<tr><td>${label}</td><td><code>${esc(format(value))}</code></td><td><code>${esc(JSON.stringify(value))}</code></td></tr>`).join('')}</tbody></table></div><p class="tiny">The same numerical code has the same color wherever it appears in its layer. Color shades are a display map; exact integer and ordered-pair equality decide matching.</p>`;
  el('crop-note').textContent=`This ${p.width} by ${p.height} crop begins after ${p.prefix_steps.toLocaleString()} literal transitions, at physical input cell ${p.payload_cell.toLocaleString()}. Every pictured center is occupied once; the actual trajectory supplies its lateral context. Acceptance occurs much later.`;
 }
 function primitiveLines(lines){return lines.map((l,j)=>`<div><b>Line ${j+1}</b> · <code>${esc(l.rule)}</code><div class="formula-read">${math(l.formula)}</div><p class="tiny">${esc(reason[l.rule]||'Checked derived operation')}${l.rule==='mp'?` Premises: lines ${l.antecedent+1} and ${l.implication+1}.`:''}</p></div>`).join('');}
 function readCell(j){
  const p=view.cases[chosen],t=p.tiles[j],r=t.recipe;
  el('semantic-strip').querySelectorAll('button').forEach((n,k)=>n.classList.toggle('selected',k===j));
  let english;
  if(chosen===0)english=j===0?'Start with the expression equal to itself.':j===1?'Use the successor equation for addition, with the second argument zero.':'Replace addition of zero inside the successor using the zero equation.';
  else english=j===0?'An incidence hypothesis implies itself.':'Instantiate the incidence-typing axiom, extract its point assertion, and retain the same hypothesis.';
  el('semantic-reading').innerHTML=`<div class="read-row"><strong>Readable cell ${j+1}</strong><div class="formula-read">${math(t.formula)}</div><p>${english}</p><p class="tiny">${t.refs.length?'Earlier receptors: '+t.refs.map(k=>'cell '+(k+1)).join(', ')+'.':'No earlier receptors.'} Root command: line ${t.root_line+1}.</p>${r.kind==='block'?`<details><summary>Expand this checked logical block · ${r.definition.proof.length} local lines</summary><div class="line-list">${primitiveLines(r.definition.proof)}</div></details>`:''}</div>`;typeset();
 }
 function showCase(){
  const p=view.cases[chosen];selected=6;draw();el('theorem').textContent=math(p.target);
  el('search-reading').textContent=`Fresh GCTS used ${p.search.nodes} states and ${p.search.attempts} placement attempts (${p.search.seconds.toFixed(3)} seconds including catalog construction and proof decoding). The row has ${p.tiles.length} semantic cells; closed universal generalizations are explicit root commands after the row.`;
  el('semantic-strip').innerHTML=p.tiles.map((t,j)=>`<button class="proof-cell" data-proof-cell="${j}"><b>Cell ${j+1}</b><code>${esc(t.recipe.kind==='primitive'?t.recipe.witness.rule:t.recipe.kind)}</code><span>${t.refs.length?'from '+t.refs.map(k=>k+1).join(', '):'no premise'}</span></button>`).join('');
  el('semantic-strip').querySelectorAll('button').forEach((b,j)=>b.addEventListener('click',()=>readCell(j)));
  el('primitive').innerHTML=primitiveLines(p.primitive);el('request-json').textContent=JSON.stringify(p.request,null,2);readCell(0);
 }
 async function boot(){
  try{
   const response=await fetch('shared-wang-reader-001.json?v=20261010-w1');if(!response.ok)throw Error('Reader HTTP '+response.status);view=await response.json();validateSharedReader(view);
   el('inventory-id').textContent=view.inventory.fingerprint;el('state-count').textContent=view.inventory.states.toLocaleString();el('symbol-count').textContent=view.inventory.symbols.toLocaleString();el('tile-count').textContent=view.inventory.tile_types.toLocaleString();
   el('load').innerHTML='<span class="badge">Independent audit passed · one unchanged palette · two accepted proofs</span>';
   el('result-table').innerHTML='<table><thead><tr><th>Fresh statement</th><th>GCTS states / attempts</th><th>Primitive lines</th><th>Selected-symbol operations</th><th>Literal transitions</th><th>Literal check</th></tr></thead><tbody>'+view.cases.map(p=>`<tr><td>${p.kind==='arithmetic'?'Adding one gives successor':'An incident object is a point'}</td><td>${p.search.nodes} / ${p.search.attempts}</td><td>${p.primitive.length}</td><td>${p.selected.micro_steps.toLocaleString()}</td><td>${p.literal.physical_steps.toLocaleString()}</td><td>${p.literal.wall_seconds.toFixed(3)} s</td></tr>`).join('')+'</tbody></table>';
   el('audit-reading').textContent=`The independent audit checked all ${view.audit.table_law.expanded_defined_transitions.toLocaleString()} defined literal transitions, both complete fresh proof searches, both input constructors, all ${view.cases.reduce((s,p)=>s+p.patch.tiles.length,0)} displayed squares and full independent symbol executions. It rejected ${view.audit.tile_mutations_rejected} changed tile readings. Audit: ${view.audit.seconds.toFixed(3)} seconds; fresh production: ${view.total_seconds.toFixed(3)} seconds, including ${view.compile_seconds.toFixed(3)} seconds of native compilation.`;
   el('controls').innerHTML='<p>'+view.controls.map(c=>`<code>${esc(c.name)}</code>: ${esc(c.status)}`).join('<br>')+'</p>';
   el('case-select').addEventListener('change',()=>{chosen=Number(el('case-select').value);showCase();});el('mark-view').addEventListener('change',draw);showCase();
  }catch(e){el('load').textContent='Validation failed: '+e.message;console.error(e);}
 }
 boot();
}
