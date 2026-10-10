'use strict';
const geometryEqual=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function validateGeometryRow(p){
 if(p.tiles.length!==p.length)throw Error('Incomplete row');
 const occupancy=new Map(),marks=new Map();
 p.tiles.forEach((t,j)=>{
  if(t.slot!==j||t.formula[0]!=='imp'||!geometryEqual(t.formula[1],p.hypothesis)||!geometryEqual(t.formula,p.formulas[t.formula_id]))throw Error('Changed formula or hypothesis');
  if(t.refs.length!==t.input_ids.length||t.refs.some((k,i)=>!Number.isInteger(k)||k<0||k>=j||p.tiles[k].formula_id!==t.input_ids[i]))throw Error('Bad earlier formula contact');
  const expected=new Map();expected.set([2*j,1].join(','),t.formula_id);expected.set([2*j,2].join(','),t.candidate);expected.set([2*j,4].join(','),0);
  t.refs.forEach((k,i)=>{expected.set([2*k,1].join(','),t.input_ids[i]);expected.set([2*k,4].join(','),0);});
  if(t.weights.length!==1||!geometryEqual(t.weights[0],[[2*j,0],12]))throw Error('Changed occupancy');
  const actual=new Map(t.marks.map(x=>[x[0].join(','),x[1]]));
  if(actual.size!==t.marks.length||actual.size!==expected.size||[...expected].some(([k,v])=>actual.get(k)!==v))throw Error('Changed marking layer');
  t.weights.forEach(([q,v])=>occupancy.set(q.join(','),(occupancy.get(q.join(','))||0)+v));
  t.marks.forEach(([q,v])=>{const k=q.join(',');if(marks.has(k)&&marks.get(k)!==v)throw Error('Disagreeing marks');marks.set(k,v);});
  const line=p.request.proof[t.root_line];if(!line||!geometryEqual(line.formula,t.formula))throw Error('Changed proof-line translation');
 });
 if([...occupancy.values()].some(v=>v!==12)||!geometryEqual(p.tiles.at(-1).formula[2],p.goal)||!geometryEqual(p.request.proof.at(-1).formula,p.target)||!geometryEqual(p.primitive.at(-1).formula,p.target)||p.native.status!=='accepted')throw Error('Changed conclusion or acceptance');
 return true;
}
function geometryName(x){return /^p[0-9]+$/.test(x)?'P_{'+x.slice(1)+'}':x.toUpperCase();}
function geometryFormula(a){
 const k=a[0];
 if(k==='var')return geometryName(a[1]);
 if(k==='all')return '\\forall '+geometryName(a[1])+'\\;('+geometryFormula(a[2])+')';
 if(k==='pred'){
  const x=a[2].map(geometryFormula),tri=y=>'\\triangle '+y.join(''),seg=y=>'\\overline{'+y.join('')+'}',angle=y=>'\\angle '+y.join('');
  if(a[1]==='Triangle')return '\\operatorname{Noncollinear}('+x.join(',')+')';
  if(a[1]==='SegEq')return seg(x.slice(0,2))+'\\equiv '+seg(x.slice(2));
  if(a[1]==='AngleEq')return angle(x.slice(0,3))+'='+angle(x.slice(3));
  if(a[1]==='Congruent')return tri(x.slice(0,3))+'\\cong '+tri(x.slice(3));
  return '\\operatorname{'+a[1].replace(/[^a-zA-Z]/g,'')+'}('+x.join(',')+')';
 }
 if(k==='imp'||k==='and')return '('+geometryFormula(a[1])+(k==='imp'?'\\Rightarrow ':'\\land ')+geometryFormula(a[2])+')';
 throw Error('Unsupported geometric formula');
}
function geometryEnglish(a){
 if(a[0]==='all')return 'For every point '+a[1].toUpperCase()+', ['+geometryEnglish(a[2])+']';
 if(a[0]==='and')return '['+geometryEnglish(a[1])+'] and ['+geometryEnglish(a[2])+']';
 if(a[0]==='imp')return 'if ['+geometryEnglish(a[1])+'], then ['+geometryEnglish(a[2])+']';
 const x=a[2].map(t=>t[1].toUpperCase()),s=y=>y.join('');
 if(a[1]==='Triangle')return 'points '+x.join(', ')+' are noncollinear';
 if(a[1]==='SegEq')return 'segment '+s(x.slice(0,2))+' has the same length as segment '+s(x.slice(2));
 if(a[1]==='AngleEq')return 'angle '+s(x.slice(0,3))+' equals angle '+s(x.slice(3));
 if(a[1]==='Congruent')return 'triangle '+s(x.slice(0,3))+' is congruent to triangle '+s(x.slice(3))+' in that vertex order';
 return 'relation '+a[1]+' holds of '+x.join(', ');
}
if(typeof module!=='undefined')module.exports={validateGeometryRow,geometryFormula,geometryEnglish};
if(typeof document!=='undefined'){
 const el=x=>document.getElementById(x),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const math=a=>'\\('+geometryFormula(a)+'\\)',titles={'I.5':'Isosceles triangles have equal base angles','I.6':'Equal base angles imply equal opposite sides','triangle-order':'Noncollinearity survives reversing the vertex order'};
 let data,p,selected=0;
 function typeset(nodes){if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise(nodes).catch(e=>{el('load').textContent='Math rendering error: '+e.message;});}
 function reason(t){
  const r=t.recipe,refs=t.refs.map(i=>'cell '+(i+1)).join(' and ');
  if(r.kind==='primitive')return 'Extract this fact from the stated hypotheses by propositional logic.';
  if(r.kind==='copy')return 'Repeat the statement from '+refs+'.';
  const bindings=Object.entries(r.bindings).map(([a,b])=>geometryName(a)+'\\mapsto '+geometryName(b)).join(',\\;');
  if(r.operation==='geometry-join')return 'Continue '+r.axiom+' with '+refs+'; discharge the next explicit condition. Vertex assignment: \\('+bindings+'\\).';
  return 'Apply '+r.axiom+(refs?' to '+refs:'')+'. Vertex assignment: \\('+bindings+'\\).'+((r.axiom==='SAS'||r.axiom==='ASA')?' The remaining conditions are recorded as an implication.':'');
 }
 function diagram(){
  const t=p.tiles[selected],focus=t.formula[2],kind=focus[0]==='pred'?focus[1]:'',segment=kind==='SegEq'||kind==='Congruent',angle=kind==='AngleEq'||kind==='Congruent';
  const stroke=segment?'#246aa2':'#78897e',arc=angle?'#aa7418':'#c5d2c8';
  if(p.id==='triangle-order'){
   el('diagram').innerHTML='<svg viewBox="0 0 300 300" role="img" aria-label="A scalene triangle illustrating noncollinearity"><path d="M116 48 L46 245 L254 245 Z" fill="#e1ebe2" stroke="#246aa2" stroke-width="3"/></svg><span class="vertex" style="left:39%;top:9%">\\(A\\)</span><span class="vertex" style="left:10%;top:84%">\\(B\\)</span><span class="vertex" style="left:90%;top:84%">\\(C\\)</span>';
   return;
  }
  el('diagram').innerHTML='<svg viewBox="0 0 300 300" role="img" aria-label="Illustrative triangle with equal legs and base angles"><path d="M150 48 L46 245 L254 245 Z" fill="#e1ebe2" stroke="#738579" stroke-width="2"/><path d="M46 245 L150 48 L254 245" fill="none" stroke="'+stroke+'" stroke-width="4"/><path d="M60 196 l16 9 M224 205 l16 -9" stroke="'+stroke+'" stroke-width="3"/><path d="M70 245 A24 24 0 0 0 58 224 M230 245 A24 24 0 0 1 242 224" fill="none" stroke="'+arc+'" stroke-width="4"/></svg><span class="vertex" style="left:50%;top:9%">\\(A\\)</span><span class="vertex" style="left:10%;top:84%">\\(B\\)</span><span class="vertex" style="left:90%;top:84%">\\(C\\)</span>';
 }
 function tileSvg(){
  const n=p.length,size=Math.min(100,860/n),left=(1040-n*size)/2,cy=270,xy=q=>[left+size/2+q[0]*size/2,cy-q[1]*size/2],active=p.tiles[selected],shown=el('view').value==='isolated'?[active]:p.tiles;
  const text=(x,y,s)=>'<text x="'+x+'" y="'+y+'" text-anchor="middle">'+esc(s)+'</text>';
  let shapes='',ports='',lines='';
  p.tiles.forEach((t,i)=>{const [x,y]=xy([2*i,0]),on=shown.includes(t);shapes+='<rect x="'+(x-size/2)+'" y="'+(y-size/2)+'" width="'+size+'" height="'+size+'" fill="'+(i===selected?'#e2ecf5':'#f0f4ee')+'" stroke="'+(i===selected?'#246aa2':'#a7b8aa')+'" stroke-width="'+(i===selected?3:1)+'"/>'+text(x,y+24,'Cell '+(i+1));if(on)shapes+='<circle cx="'+x+'" cy="'+y+'" r="4" fill="#303d38"/>';});
  const origin=xy([2*selected,0]);
  active.refs.forEach(j=>{const q=xy([2*j,1]);lines+='<path d="M'+origin[0]+' '+(origin[1]-8)+' C'+origin[0]+' 136 '+q[0]+' 136 '+q[0]+' '+q[1]+'" fill="none" stroke="#246aa2" stroke-width="2" stroke-dasharray="6 4"/>';});
  const union=new Map();
  shown.forEach(t=>t.marks.forEach(([q,v])=>{const key=q.join(',');if(union.has(key)&&union.get(key).v!==v)throw Error('Display mark mismatch');union.set(key,{q,v});}));
  union.forEach(({q,v})=>{
   const [x,y]=xy(q),layer=q[1],chosen=active.marks.some(([r])=>geometryEqual(q,r)),w=chosen?3:1.5;
   if(layer===1)ports+='<circle cx="'+x+'" cy="'+y+'" r="12" fill="#e3eff8" stroke="#246aa2" stroke-width="'+w+'"/>'+text(x,y+30,'F'+v);
   if(layer===2)ports+='<rect x="'+(x-8)+'" y="'+(y-8)+'" width="16" height="16" fill="#e0ede5" stroke="#28745c" stroke-width="'+w+'"/>'+text(x,y-16,'O'+v);
   if(layer===4)ports+='<path d="M'+x+' '+(y-10)+' l10 10 -10 10 -10 -10 Z" fill="#fff2cd" stroke="#aa7418" stroke-width="'+w+'"/>'+text(x,y-17,'R'+v);
  });
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1040 365" role="img" aria-label="Fixed directed proof squares with blue formula, green ownership and gold resource markings"><style>text{font:12px system-ui;fill:#30423a}</style>'+shapes+lines+ports+text(520,345,'Logical reading: hypotheses at the left; conclusion at the right. No rotations or reflections.')+'</svg>';
 }
 function selectCell(i){
  selected=i;el('cell').value=String(i);el('tile-svg').innerHTML=tileSvg();diagram();
  const t=p.tiles[i];
  el('selected-reading').innerHTML='<strong>Cell '+(i+1)+' · blue formula ID F'+t.formula_id+'</strong><div class="equation">'+math(t.formula)+'</div><p>'+esc(geometryEnglish(t.formula[2]))+'.</p><p>'+reason(t)+'</p>';
  el('tile-values').textContent=JSON.stringify({candidate:t.candidate,slot:t.slot,t_values:t.weights.map(([q,v])=>[q,v/12]),m_values:t.marks,earlier_cells:t.refs.map(j=>j+1)},null,2);
  document.querySelectorAll('.reading').forEach((x,j)=>x.classList.toggle('active',j===i));
  typeset([el('selected-reading'),el('diagram')]);
 }
 function proofLines(){
  const primitive=el('proof-level').value==='primitive',lines=primitive?p.primitive:p.request.proof;
  el('proof-count').textContent=lines.length+' checked '+(primitive?'primitive':'compiled')+' lines. References are one-based and clickable. Primitive expansion contains no block calls or open assumptions.';
  const ref=j=>'<button class="reference" type="button" data-ref="'+j+'">line '+(j+1)+'</button>';
  el('proof-lines').innerHTML=lines.map((l,i)=>{
   let why=l.rule;
   if(l.rule==='mp')why='Modus ponens: '+ref(l.antecedent)+' and '+ref(l.implication)+'.';
   else if(l.rule==='generalize')why='Universal generalization from '+ref(l.source)+'.';
   else if(l.rule==='block')why='Checked compiled rule'+(l.inputs.length?' using '+l.inputs.map(ref).join(', '):'')+'.';
   else if(l.rule==='axiom')why='Declared geometric axiom: '+esc(l.name)+'.';
   else if(l.rule==='instantiate')why='Universal instantiation.';
   else if(l.rule==='tautology')why='Propositional tautology.';
   return '<div class="proof-line" id="proof-line-'+i+'"><span>'+(i+1)+'</span><div><div class="equation">'+math(l.formula)+'</div><p>'+esc(geometryEnglish(l.formula))+'.</p><p class="small">'+why+'</p></div></div>';
  }).join('');
  el('proof-lines').querySelectorAll('[data-ref]').forEach(b=>b.addEventListener('click',()=>{const row=el('proof-line-'+b.dataset.ref);document.querySelectorAll('.proof-line.flash').forEach(x=>x.classList.remove('flash'));row.classList.add('flash');row.scrollIntoView({behavior:'smooth',block:'nearest'});}));
  typeset([el('proof-lines')]);
 }
 function choose(i){
  p=data.proofs[i];validateGeometryRow(p);selected=0;
  el('theorem-title').textContent=titles[p.id];el('solver').textContent='Proof discovered by '+(p.lane==='gcts'?'GCTS':'classical arc-consistency search');
  el('target').innerHTML=math(p.target);el('hypotheses').innerHTML='Hypotheses: '+math(p.hypothesis);
  el('theorem-words').textContent=p.id==='I.5'?'If two sides of a nondegenerate triangle have the same length, the opposite base angles are equal.':p.id==='I.6'?'If the two base angles of a nondegenerate triangle are equal, their opposite sides have the same length.':'Reversing the order in which three noncollinear points are named preserves noncollinearity.';
  el('proof-origin').textContent=p.length+' searched proof cells; '+p.primitive_lines+' independently checked primitive lines; complete native acceptance. This proof uses '+p.lane.toUpperCase()+', with no supplied proof sequence.';
  el('cell').innerHTML=p.tiles.map((t,j)=>'<option value="'+j+'">Cell '+(j+1)+' · F'+t.formula_id+'</option>').join('');
  el('row-reading').innerHTML=p.tiles.map((t,j)=>'<article class="reading"><button type="button" data-cell="'+j+'">Cell '+(j+1)+'</button><div><div class="equation">'+math(t.formula[2])+'</div><p>'+esc(geometryEnglish(t.formula[2]))+'.</p><p class="small">'+reason(t)+'</p></div></article>').join('');
  el('row-reading').querySelectorAll('[data-cell]').forEach(b=>b.addEventListener('click',()=>{selectCell(Number(b.dataset.cell));el('tile-svg').scrollIntoView({behavior:'smooth',block:'start'});}));
  el('closure').innerHTML='Checked closure: '+math(p.target);
  el('axioms').innerHTML=Object.entries(p.theory.axioms).map(([name,a])=>'<div class="axiom"><strong>'+esc(name)+'</strong><div class="equation">'+math(a)+'</div></div>').join('');
  el('certificate').textContent=JSON.stringify(p.request,null,2);
  selectCell(0);proofLines();typeset([el('target'),el('hypotheses'),el('row-reading'),el('closure'),el('axioms')]);
 }
 async function main(){
  const response=await fetch('euclidean-reader-001.json?v=20261009-e1.1');if(!response.ok)throw Error('Dataset HTTP '+response.status);data=await response.json();
  if(data.audit.status!=='passed')throw Error('Full audit required');data.proofs.forEach(validateGeometryRow);
  el('load').textContent='Three audited proofs · '+data.proofs.reduce((s,p)=>s+p.length,0)+' actual cells · colored marking layers.';
  el('theorem').innerHTML=data.proofs.map((p,i)=>'<option value="'+i+'">'+esc(p.id)+': '+esc(titles[p.id])+'</option>').join('');
  el('theorem').addEventListener('change',()=>choose(Number(el('theorem').value)));
  el('cell').addEventListener('change',()=>selectCell(Number(el('cell').value)));
  el('previous').addEventListener('click',()=>selectCell(Math.max(0,selected-1)));el('next').addEventListener('click',()=>selectCell(Math.min(p.length-1,selected+1)));
  el('view').addEventListener('change',()=>selectCell(selected));el('proof-level').addEventListener('change',proofLines);
  const status=x=>x==='finite_exact_proof_tiling'?'Checked proof':x==='unknown_search_budget'?'Budget cutoff':'Finite envelope exhausted';
  el('comparison-table').innerHTML='<table><thead><tr><th>Statement / control</th><th>Solver</th><th>Outcome</th><th>States</th><th>Attempts</th><th>Build + search seconds</th></tr></thead><tbody>'+data.results.map(r=>'<tr><td>'+esc(r.id)+'</td><td>'+esc(r.lane.toUpperCase())+'</td><td>'+status(r.status)+'</td><td>'+r.states+'</td><td>'+r.attempts+'</td><td>'+r.seconds.toFixed(4)+'</td></tr>').join('')+'</tbody></table>';
  el('assessment').textContent='The marked point representation supports sound automatic proof search and readable certificates. GCTS discovers the elementary vertex-order lemma, but reaches its budget on I.5 and I.6; classical search discovers both. This pilot shows no distinctive GCTS advantage. More effective geometry clusters and ordering must earn their cost on further matched tests.';
  choose(0);
  fetch('symbol-renaming-001.json?v=20261009-e1.1').then(response=>{if(!response.ok)throw Error('HTTP '+response.status);return response.json();}).then(control=>{
   if(control.independent_audit.status!=='passed'||control.source.sha256!==data.source.sha256||control.cases.some(r=>r.native.status!=='accepted'))throw Error('Unverified control');
   el('renaming-status').textContent='Checked renaming: all three proofs remain accepted after replacing the four geometric predicate names and all axiom names. Every point candidate and resource marking is identical. A fresh GCTS search for the elementary lemma follows exactly the same complete search tree.';
   el('renaming-formula').innerHTML='The first theorem with arbitrary relation names: '+math(control.cases[0].request.target);typeset([el('renaming-formula')]);
  }).catch(error=>{el('renaming-status').textContent='Symbol-renaming control unavailable: '+error.message;});
 }
 main().catch(e=>{el('load').textContent='Reader stopped: '+e.message;});
}
