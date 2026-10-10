'use strict';
const sameHilbert=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function validateHilbertRow(p){
 if(p.tiles.length!==p.length)throw Error('Incomplete row');
 const marks=new Map();
 p.tiles.forEach((t,j)=>{
  if(t.slot!==j||!sameHilbert(t.formula,p.formulas[t.formula_id]))throw Error('Changed formula or hypothesis');
  if(t.refs.length!==t.input_ids.length||t.refs.some((k,i)=>!Number.isInteger(k)||k<0||k>=j||p.tiles[k].formula_id!==t.input_ids[i]))throw Error('Bad earlier contact');
  const expected=new Map([[`${2*j},1`,t.formula_id],[`${2*j},2`,t.candidate],[`${2*j},4`,0]]);
  t.refs.forEach((k,i)=>{expected.set(`${2*k},1`,t.input_ids[i]);expected.set(`${2*k},4`,0);});
  if(t.weights.length!==1||!sameHilbert(t.weights[0],[[2*j,0],12]))throw Error('Changed occupancy');
  const actual=new Map(t.marks.map(([q,v])=>[q.join(','),v]));
  if(actual.size!==t.marks.length||actual.size!==expected.size||[...expected].some(([k,v])=>actual.get(k)!==v))throw Error('Changed marking layer');
  t.marks.forEach(([q,v])=>{const k=q.join(',');if(marks.has(k)&&marks.get(k)!==v)throw Error('Disagreeing marks');marks.set(k,v);});
  if(!sameHilbert(p.request.proof[t.root_line]?.formula,t.formula))throw Error('Changed decoded proof line');
 });
 if(!sameHilbert(p.tiles.at(-1).formula[2],p.goal)||!sameHilbert(p.request.proof.at(-1).formula,p.target)||!sameHilbert(p.primitive.at(-1).formula,p.target)||p.native.status!=='accepted')throw Error('Changed conclusion or acceptance');
 return true;
}
function hilbertName(x){
 if(x==='u')return '\\ell';if(x==='v')return 'm';if(x==='equalityHole')return 'z';
 if(/^l[0-9]+$/.test(x))return '\\ell_{'+x.slice(1)+'}';
 if(/^p[0-9]+$/.test(x))return 'P_{'+x.slice(1)+'}';
 return /^(fresh|[a-zA-Z]+)([0-9]+)$/.test(x)?'\\operatorname{'+x.replace(/[0-9]+$/,'')+'}_{'+x.match(/[0-9]+$/)[0]+'}':x.replace(/[^a-zA-Z0-9]/g,'');
}
function hilbertFormula(a){
 const k=a[0];
 if(k==='var')return hilbertName(a[1]);
 if(k==='bot')return '\\bot';
 if(k==='eq')return hilbertFormula(a[1])+'='+hilbertFormula(a[2]);
 if(k==='all')return '\\forall '+hilbertName(a[1])+'\\;('+hilbertFormula(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+hilbertName(a[1][1])+'\\;('+hilbertFormula(a[1][2][1])+')';
 if(k==='not')return '\\neg('+hilbertFormula(a[1])+')';
 if(k==='pred')return '\\operatorname{'+a[1].replace(/[^a-zA-Z]/g,'')+'}('+a[2].map(hilbertFormula).join(',')+')';
 if(['imp','and','or'].includes(k))return '('+hilbertFormula(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+hilbertFormula(a[2])+')';
 throw Error('Unsupported formula');
}
function hilbertEnglish(a){
 const name=x=>x==='u'?'the first line':x==='v'?'the second line':x.toUpperCase();
 if(a[0]==='var')return name(a[1]);
 if(a[0]==='bot')return 'a contradiction';
 if(a[0]==='eq')return name(a[1][1])+' and '+name(a[2][1])+' are the same object';
 if(a[0]==='all')return 'for every object assigned to '+name(a[1])+', ['+hilbertEnglish(a[2])+']';
 if(a[0]==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return 'there is an object '+name(a[1][1])+' such that ['+hilbertEnglish(a[1][2][1])+']';
 if(a[0]==='not'&&a[1][0]==='eq')return name(a[1][1][1])+' and '+name(a[1][2][1])+' are distinct objects';
 if(a[0]==='not')return 'it is false that ['+hilbertEnglish(a[1])+']';
 if(a[0]==='and')return hilbertEnglish(a[1])+'; and '+hilbertEnglish(a[2]);
 if(a[0]==='or')return '['+hilbertEnglish(a[1])+'] or ['+hilbertEnglish(a[2])+']';
 if(a[0]==='imp')return 'if ['+hilbertEnglish(a[1])+'], then ['+hilbertEnglish(a[2])+']';
 const xs=a[2].map(x=>name(x[1]));
 if(a[1]==='Point')return xs[0]+' is a point';
 if(a[1]==='Line')return xs[0]+' is a line';
 if(a[1]==='Inc')return xs[0]+' lies on '+xs[1];
 return 'relation '+a[1]+' holds of '+xs.join(', ');
}
if(typeof module!=='undefined')module.exports={validateHilbertRow,hilbertFormula,hilbertEnglish};
if(typeof document!=='undefined'){
 const el=x=>document.getElementById(x),esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const math=a=>'\\('+hilbertFormula(a)+'\\)',conditional=math;
 const titles={'line-has-point':'Every line contains a point','unique-joining-line':'Two distinct points have a unique joining line'};
 let data,p,selected=0;
 const typeset=nodes=>{if(window.MathJax?.typesetPromise)MathJax.typesetPromise(nodes).catch(e=>{el('load').textContent=e.message;});};
 function reason(t){
  const r=t.recipe,refs=t.refs.map(j=>'cell '+(j+1)).join(' and ');
  if(r.kind==='copy')return 'Repeat '+refs+'.';
  if(r.kind==='primitive')return r.witness.rule==='generalize'?'Universally generalize '+r.witness.variable+' in '+refs+'. This is a theorem with no open assumptions; temporary witness conditions remain inside its formula.':'Propositional logic collects the conditions in this formula.';
  const op=r.operation,q=r.inference;
  if(op==='exists-introduce')return 'Existential introduction from '+refs+': the free parameter '+q.variable+' supplies an instance. No concrete object is chosen by an oracle.';
  if(op==='exists-eliminate')return 'Eliminate a temporary witness '+q.variable+' using '+refs+'. The variable is absent from both the outer context and the conclusion. The input is already universally quantified.';
  if(op==='forall-scope')return 'Move the quantified conditional in '+refs+' into the outer context. The quantified variable is absent from that context.';
  if(op==='forall-distribute')return 'Distribute the universal quantifier from '+refs+' through a context that does not contain its variable.';
  if(op==='propositional')return 'Combine or rearrange the complete conditional formulas from '+refs+' by propositional logic.';
  if(op==='axiom-clause'){
   const assignment=Object.entries(q.row.bindings).map(([a,b])=>hilbertName(a)+'\\mapsto '+hilbertName(b)).join(',\\;');
   return 'Use '+q.row.axiom+' with '+refs+'. Assignment: \\('+assignment+'\\). Each outer binder is instantiated with capture avoidance.';
  }
  throw Error('Unsupported inference');
 }
 function svg(){
  const width=Math.max(960,100*p.length+80),size=100,left=(width-size*p.length)/2,xy=q=>[left+50+q[0]*50,265-q[1]*50],active=p.tiles[selected],shown=el('view').value==='isolated'?[active]:p.tiles;
  const text=(x,y,s)=>`<text x="${x}" y="${y}" text-anchor="middle">${esc(s)}</text>`;
  let shapes='',paths='',ports='';
  p.tiles.forEach((t,j)=>{const [x,y]=xy([2*j,0]);shapes+=`<rect x="${x-50}" y="${y-50}" width="100" height="100" fill="${j===selected?'#e2ecf5':'#f0f4ee'}" stroke="${j===selected?'#246aa2':'#a7b8aa'}" stroke-width="${j===selected?3:1}"/>`+text(x,y+24,'Cell '+(j+1));if(shown.includes(t))shapes+=`<circle cx="${x}" cy="${y}" r="4" fill="#303d38"/>`;});
  const [ox,oy]=xy([2*selected,0]);active.refs.forEach(j=>{const [x,y]=xy([2*j,1]);paths+=`<path d="M${ox} ${oy-8} C${ox} 125 ${x} 125 ${x} ${y}" fill="none" stroke="#246aa2" stroke-width="2" stroke-dasharray="6 4"/>`;});
  const union=new Map();shown.forEach(t=>t.marks.forEach(([q,v])=>union.set(q.join(','),{q,v})));
  union.forEach(({q,v})=>{const [x,y]=xy(q),w=active.marks.some(([r])=>sameHilbert(q,r))?3:1.5;
   if(q[1]===1)ports+=`<circle cx="${x}" cy="${y}" r="12" fill="#e3eff8" stroke="#246aa2" stroke-width="${w}"/>`+text(x,y+30,'F'+v);
   if(q[1]===2)ports+=`<rect x="${x-8}" y="${y-8}" width="16" height="16" fill="#e0ede5" stroke="#28745c" stroke-width="${w}"/>`+text(x,y-16,'O'+v);
   if(q[1]===4)ports+=`<path d="M${x} ${y-10} l10 10 -10 10 -10 -10 Z" fill="#fff2cd" stroke="#aa7418" stroke-width="${w}"/>`+text(x,y-17,'R'+v);
  });
  return '<svg viewBox="0 0 '+width+' 360" role="img" aria-label="Fixed directed Hilbert proof squares with colored point markings"><style>text{font:12px system-ui;fill:#30423a}</style>'+shapes+paths+ports+text(width/2,345,'Proof direction: hypotheses to conclusion. Translation only; no rotation or reflection.')+'</svg>';
 }
 function select(j){
  selected=j;el('cell').value=String(j);el('tile-svg').innerHTML=svg();const t=p.tiles[j];
  el('selected-reading').innerHTML='<strong>Cell '+(j+1)+' · formula ID F'+t.formula_id+'</strong><div class="equation">'+conditional(t.formula)+'</div><p>Complete statement: '+esc(hilbertEnglish(t.formula))+'.</p><p>'+reason(t)+'</p>';
  el('tile-values').textContent=JSON.stringify({t_values:t.weights.map(([q,v])=>[q,v/12]),m_values:t.marks,formula:t.formula,earlier_cells:t.refs.map(j=>j+1)},null,2);typeset([el('selected-reading')]);
 }
 function proofLines(){
  const lines=el('proof-level').value==='primitive'?p.primitive:p.request.proof;
  el('proof-count').textContent=lines.length+' checked lines. The complete formulas are shown here; references point to earlier lines. There are no open assumptions in the primitive proof.';
  const ref=j=>`<button class="reference" data-ref="${j}" type="button">line ${j+1}</button>`;
  el('proof-lines').innerHTML=lines.map((l,i)=>{
   const why=l.rule==='mp'?'Modus ponens: '+ref(l.antecedent)+' and '+ref(l.implication):l.rule==='generalize'?'Universal generalization from '+ref(l.source):l.rule==='block'?'Checked compiled inference'+(l.inputs.length?' using '+l.inputs.map(ref).join(', '):''):l.rule==='axiom'?'Declared axiom '+esc(l.name):l.rule==='eq_subst'?'Logical equality substitution':l.rule==='instantiate'?'Universal instantiation':l.rule==='tautology'?'Propositional tautology':esc(l.rule);
   return `<div class="proof-line" id="proof-line-${i}"><span>${i+1}</span><div><div class="equation">${math(l.formula)}</div><p>${esc(hilbertEnglish(l.formula))}.</p><p class="small">${why}.</p></div></div>`;
  }).join('');
  el('proof-lines').querySelectorAll('[data-ref]').forEach(b=>b.addEventListener('click',()=>{const row=el('proof-line-'+b.dataset.ref);document.querySelectorAll('.proof-line.flash').forEach(x=>x.classList.remove('flash'));row.classList.add('flash');row.scrollIntoView({behavior:'smooth',block:'nearest'});}));typeset([el('proof-lines')]);
 }
 function choose(i){
  p=data.proofs[i];validateHilbertRow(p);el('theorem-title').textContent=titles[p.id];el('target').innerHTML=math(p.target);el('hypotheses').innerHTML='\\(\\mathcal H\\;:= '+hilbertFormula(p.hypothesis)+'\\)';
  el('theorem-words').textContent=p.id==='line-has-point'?'For each line, some point lies on it. The proof uses two nested existence claims in Hilbert I.3.':'Any two distinct points have a joining line; any other line through both points is the same line. The proof combines existence I.1 and uniqueness I.2.';
  el('proof-origin').textContent=p.length+' cells selected by '+p.lane.toUpperCase()+'; '+p.primitive_lines+' independently replayed primitive lines; complete native acceptance. '+p.encoding;
  el('cell').innerHTML=p.tiles.map((t,j)=>`<option value="${j}">Cell ${j+1} · F${t.formula_id}</option>`).join('');
  el('row-reading').innerHTML=p.tiles.map((t,j)=>`<article class="reading"><button type="button" data-cell="${j}">Cell ${j+1}</button><div><div class="equation">${math(t.formula)}</div><p>${esc(hilbertEnglish(t.formula))}.</p><p class="small">${reason(t)}</p></div></article>`).join('');
  el('row-reading').querySelectorAll('[data-cell]').forEach(b=>b.addEventListener('click',()=>select(Number(b.dataset.cell))));
  el('closure').textContent=p.variables.length+' generalizations close the theorem after the proof row. They are checked primitive steps, not additional occupancy cells.';
  el('axioms').innerHTML=Object.entries(p.theory.axioms).map(([n,a])=>`<div class="axiom"><strong>${esc(n)}</strong><p class="small">${esc(p.metadata[n].source)}</p><div class="equation">${math(a)}</div></div>`).join('');
  el('certificate').textContent=JSON.stringify(p.request,null,2);select(0);proofLines();typeset([el('target'),el('hypotheses'),el('row-reading'),el('axioms')]);
 }
 async function main(){
  const response=await fetch('hilbert-quantified-reader-001.json?v=20261010-q1');if(!response.ok)throw Error('Dataset HTTP '+response.status);data=await response.json();
  if(data.audit.status!=='passed'||data.model_controls.status!=='passed')throw Error('Full independent audit required');data.proofs.forEach(validateHilbertRow);
  el('load').textContent='Two audited witness proofs · 22 directed cells · explicit quantifier scope checks.';
  el('theorem').innerHTML=data.proofs.map((p,i)=>`<option value="${i}">${esc(titles[p.id])}</option>`).join('');
  el('theorem').addEventListener('change',()=>choose(Number(el('theorem').value)));el('cell').addEventListener('change',()=>select(Number(el('cell').value)));el('view').addEventListener('change',()=>select(selected));el('proof-level').addEventListener('change',proofLines);
  el('previous').addEventListener('click',()=>select(Math.max(0,selected-1)));el('next').addEventListener('click',()=>select(Math.min(p.length-1,selected+1)));
  el('comparison-table').innerHTML='<table><thead><tr><th>Statement/control</th><th>Solver</th><th>Result</th><th>States</th><th>Catalog + search (s)</th><th>Native check (s)</th><th>Total cold (s)</th></tr></thead><tbody>'+data.results.map(r=>`<tr><td>${esc(r.id)}</td><td>${r.lane.toUpperCase()}</td><td>${r.status==='finite_exact_proof_tiling'?'Checked proof':r.status==='unknown_search_budget'?'Budget cutoff':'Finite grammar exhausted'}</td><td>${r.states}</td><td>${(r.catalog_seconds+r.search_seconds).toFixed(4)}</td><td>${r.native_seconds.toFixed(3)}</td><td>${r.cold_seconds.toFixed(3)}</td></tr>`).join('')+'</tbody></table>';
  el('models').innerHTML=data.model_controls.cases.map(m=>'<div class="axiom"><strong>'+esc(m.id)+'</strong><p>Axioms: '+Object.entries(m.axioms).map(([n,v])=>esc(n)+': '+(v?'true':'false')).join('; ')+'.</p><p>Every line has a point: '+m.theorems['line-has-point']+'; unique joining line: '+m.theorems['unique-joining-line']+'.</p></div>').join('');
  choose(0);
 }
 main().catch(e=>{el('load').textContent='Reader stopped: '+e.message;});
}
