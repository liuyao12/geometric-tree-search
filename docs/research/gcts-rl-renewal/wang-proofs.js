'use strict';
const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function name(s){return String(s).replace(/[^a-zA-Z0-9]/g,'');}
function term(t){if(t[0]==='var')return name(t[1]);const args=t[2];if(t[1]==='zero')return '0';if(t[1]==='succ'){const a=term(args[0]);return /^\d+$/.test(a)?String(Number(a)+1):`\\operatorname{S}(${a})`;}if(t[1]==='add')return `(${term(args[0])}+${term(args[1])})`;if(t[1]==='mul')return `(${term(args[0])}\\cdot ${term(args[1])})`;return `\\operatorname{${name(t[1])}}${args.length?`(${args.map(term).join(',')})`:''}`;}
function formula(a){if(a[0]==='eq')return `${term(a[1])}=${term(a[2])}`;if(a[0]==='all')return `\\forall ${name(a[1])}\\;(${formula(a[2])})`;if(a[0]==='bot')return '\\bot';if(a[0]==='pred')return `\\operatorname{${name(a[1])}}${a[2].length?`(${a[2].map(term).join(',')})`:''}`;if(a[0]==='not')return `\\neg(${formula(a[1])})`;return `(${formula(a[1])}${{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[a[0]]}${formula(a[2])})`;}
const math=a=>`\\(${esc(formula(a))}\\)`,termMath=t=>`\\(${esc(term(t))}\\)`;
const numberWords=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen','twenty'];
function numeralValue(t){if(t[0]!=='fun')return null;if(t[1]==='zero'&&t[2].length===0)return 0;if(t[1]==='succ'&&t[2].length===1){const n=numeralValue(t[2][0]);return n===null?null:n+1;}return null;}
function englishTerm(t){
 const n=numeralValue(t);if(n!==null)return numberWords[n]||`the numeral \\(${n}\\)`;if(t[0]==='var')return termMath(t);
 const child=x=>{const text=englishTerm(x);return x[0]==='fun'&&numeralValue(x)===null&&x[2].length?`[${text}]`:text;};
 if(t[1]==='succ')return `the successor of ${child(t[2][0])}`;
 if(t[1]==='add')return `${child(t[2][0])} plus ${child(t[2][1])}`;
 if(t[1]==='mul')return `${child(t[2][0])} times ${child(t[2][1])}`;
 return t[2].length?`the value of the function \\(\\operatorname{${esc(name(t[1]))}}\\) at ${t[2].map(child).join(', ')}`:`the constant \\(\\operatorname{${esc(name(t[1]))}}\\)`;
}
function englishFormula(a){
 if(a[0]==='eq')return `${englishTerm(a[1])} equals ${englishTerm(a[2])}`;
 if(a[0]==='all')return `for every value of \\(${esc(name(a[1]))}\\), [${englishFormula(a[2])}]`;
 if(a[0]==='imp')return `if [${englishFormula(a[1])}], then [${englishFormula(a[2])}]`;
 if(a[0]==='not')return `it is not the case that [${englishFormula(a[1])}]`;
 if(a[0]==='and')return `both [${englishFormula(a[1])}] and [${englishFormula(a[2])}] hold`;
 if(a[0]==='or')return `at least one of [${englishFormula(a[1])}] and [${englishFormula(a[2])}] holds, possibly both`;
 if(a[0]==='bot')return 'a contradiction holds';
 if(a[0]==='pred')return `the predicate \\(\\operatorname{${esc(name(a[1]))}}\\) holds${a[2].length?` of ${a[2].map(englishTerm).join(', ')}`:''}`;
 return 'See the literal formal statement.';
}
function englishSentence(a){const s=englishFormula(a);return s[0].toUpperCase()+s.slice(1)+'.';}
let data,tileData,currentReading,current=0,line=0,tileIndex=0,views=[],trail=[],typeset=Promise.resolve();const pageSize=20;
const explanations={axiom:'Use the named axiom from the displayed theory.',tautology:'Introduce a classically valid propositional formula; its first-order subformulas are treated as propositional atoms.',refl:'Introduce reflexivity of equality for the displayed term.',instantiate:'Introduce the universal-instantiation implication. Applying it to a proved universal statement takes a later modus-ponens step.',distribute:'Introduce the universal-distribution implication, with its variable side condition checked.',eq_subst:'Introduce the equality-substitution implication for the displayed template, variable and terms.',mp:'Apply modus ponens: the antecedent reference proves the premise, and the implication reference proves the implication to this conclusion.',generalize:'Universally generalize the referenced proved formula in the displayed variable; all local-assumption side conditions are checked.',assumption:'Use an explicit local premise of this lemma definition. This is not an added axiom of the external theorem.',block:'Apply this previously checked lemma to the referenced input lines. Open its definition to inspect every local step.',induction:'Introduce the registered natural-number induction schema instance. No searched example in this notebook currently uses this rule.'};
function typesetParts(parts){typeset=typeset.then(async()=>{if(window.MathJax?.startup?.promise){await window.MathJax.startup.promise;await window.MathJax.typesetPromise(parts.map(el));}}).catch(e=>el('load').textContent=`Math rendering failed: ${e.message}`);}
function theorem(){return data.theorems[current];}
function view(){return views.find(v=>v.id===el('proof-view').value);}
function references(item){if(item.rule==='mp')return [{label:'Antecedent',index:item.antecedent},{label:'Implication',index:item.implication}];if(item.rule==='generalize')return [{label:'Source',index:item.source}];if(item.rule==='block')return item.inputs.map((index,i)=>({label:`Input ${i+1}`,index}));return [];}
function jump(next){line=Math.max(0,Math.min(view().proof.length-1,Number(next)));el('line-select').value=String(line);renderLine();}
function setView(id,resetTrail=true){el('proof-view').value=id;if(resetTrail)trail=[];line=0;el('line-select').replaceChildren();view().proof.forEach((_,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Line ${i+1}`;el('line-select').append(o);});renderLine();}
function renderLine(){
 const t=theorem(),v=view(),item=v.proof[line],refs=references(item),page=Math.floor(line/pageSize),start=page*pageSize,end=Math.min(v.proof.length,start+pageSize);
 el('line-select').value=String(line);el('line-title').textContent=`Line ${line+1} of ${v.proof.length} · ${item.rule} · ${v.label}`;el('line-formula').innerHTML=math(item.formula);el('line-english').innerHTML=englishSentence(item.formula);el('rule-explanation').textContent=explanations[item.rule]||'See the literal checked rule parameters below.';
 el('references').innerHTML=refs.length?refs.map(r=>`<button type="button" data-reference="${r.index}">${esc(r.label)}: line ${r.index+1}</button>`).join(''):'<span class="small">This rule has no earlier-line references.</span>';
 el('references').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>jump(Number(button.dataset.reference))));
 const parameters=[];if(item.name)parameters.push(`<p>Checked name: <code>${esc(item.name)}</code></p>`);if(item.variable)parameters.push(`<p>Variable: \\(${esc(name(item.variable))}\\)</p>`);if(item.universal)parameters.push(`<p>Universal formula: ${math(item.universal)}</p>`);if(item.term)parameters.push(`<p>Substitution term: ${termMath(item.term)}</p>`);if(item.template)parameters.push(`<p>Template: ${math(item.template)}</p>`);if(item.left)parameters.push(`<p>Left term: ${termMath(item.left)} · right term: ${termMath(item.right)}</p>`);if(item.rule==='assumption')parameters.push(`<p>Local premise ${item.index+1}: ${math(v.definition.premises[item.index])}</p>`);el('rule-parameters').innerHTML=parameters.join('');
 el('block-link').innerHTML=(item.rule==='block'?'<button id="open-definition" type="button">Open this lemma definition</button>':'')+(trail.length?'<button id="return-call" type="button">Return to the calling line</button>':'');
 if(item.rule==='block')el('open-definition').addEventListener('click',()=>{trail.push({view:v.id,line});setView(`block:${item.name}`,false);});if(trail.length)el('return-call').addEventListener('click',()=>{const back=trail.pop();setView(back.view,false);jump(back.line);});
 el('view-detail').textContent=v.id==='expanded'?`All ${v.proof.length} primitive root lines are independently checked. Every lemma is expanded and earlier-line references use this one global root numbering.`:v.id==='root'?`${v.proof.length} high-level root lines. Every block call names a checked definition. Line references use this root numbering.`:`${v.proof.length} local definition lines; ${v.definition.premises.length} explicit local premises. Local assumptions are supplied by the caller. References use this definition's own numbering.`;
 el('line-list').innerHTML=v.proof.slice(start,end).map((p,i)=>`<div class="proof-line ${start+i===line?'active':''}" data-index="${start+i}"><div><button type="button" data-line="${start+i}">Line ${start+i+1}</button><br><code>${esc(p.rule)}</code></div><div><div class="equation">${math(p.formula)}</div><p class="line-english-small">${englishSentence(p.formula)}</p></div></div>`).join('');el('line-list').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>jump(Number(button.dataset.line))));
 el('page-label').textContent=`Lines ${start+1}–${end} of ${v.proof.length}`;el('previous-page').disabled=page===0;el('next-page').disabled=end===v.proof.length;el('previous').disabled=line===0;el('next').disabled=line===v.proof.length-1;el('raw-line').textContent=JSON.stringify(item,null,2);
 el('lemma-interface').innerHTML=v.definition?`<p><strong>Local premises</strong><br>${v.definition.premises.length?v.definition.premises.map(math).join('<br>'):'None.'}</p><p><strong>Conclusion</strong><br>${math(v.definition.conclusion)}</p>`:'';
 typesetParts(['line-formula','line-english','rule-parameters','line-list','lemma-interface']);
}

function tileRow(){return tileData.theorems.find(t=>t.id===theorem().id);}

const arithmeticReadings={AZ:'Adding zero leaves the number unchanged.',AS:'Use the recursive rule for addition.',MZ:'Multiplying by zero gives zero.',MS:'Use the recursive rule for multiplication.'};
function cellReading(step){
 if(step.kind==='start')return `Start with ${termMath(step.formula[2])}; every expression equals itself.`;
 const context=step.change.path.length?' inside the surrounding expression':'',reverse=step.instance.direction===-1?' Use it in reverse.':'';
 return `${arithmeticReadings[step.label]||'Use the displayed equality axiom.'}${reverse} Replace ${termMath(step.change.before)} with ${termMath(step.change.after)}${context}.`;
}
function readingEquation(items,clustered){
 let chain=term(currentReading.starting_expression);
 for(const s of items){
  if(clustered?s.start&&s.cells.length===1:s.kind==='start')continue;
  const after=clustered?s.after:s.formula[2],label=clustered?`tile ${s.tileIndex+1}`:`cell ${s.slot+1}`;
  chain+=` \\mathrel{\\underset{\\text{${label}}}{=}} ${term(after)}`;
 }
 return `\\(${esc(chain)}\\)`;
}
function renderTileReading(){
 const clustered=el('translation-detail').value==='clusters',items=clustered?currentReading.groups:currentReading.chain;
 el('tile-reading-chain').innerHTML=readingEquation(items,clustered);
 el('tile-reading-steps').innerHTML=items.map(s=>{
  const first=clustered?currentReading.steps.find(c=>c.slot===s.cells[0]):s,tile=tileRow().tiles[s.tileIndex],label=clustered?`Tile ${s.tileIndex+1}`:`Cell ${s.slot+1}`,port=clustered?`Cells ${s.cells.map(j=>j+1).join(', ')}`:`Formula port F${s.formula_id}`;
  const reading=clustered&&s.kind==='searched cluster'?`Apply this checked cluster: replace ${termMath(s.before)} with ${termMath(s.after)}. Its ${s.cells.length} internal cell steps can be read in the cell view.`:cellReading(first);
  return `<div class="tile-reading-step ${s.tileIndex===tileIndex?'active':''}" data-reading-tile="${s.tileIndex}"><div><button type="button" data-highlight-tile="${s.tileIndex}">${label}</button><p class="small">${esc(port)}<br>${esc(tile.kind)}</p></div><div><div class="equation">${math(s.formula)}</div><p class="tile-statement">${englishSentence(s.formula)}</p><p>${reading}</p>${first.references.length?`<p class="small">Uses the formula at cell ${first.references[0]+1}.</p>`:''}</div></div>`;
 }).join('');
 el('tile-reading-steps').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{tileIndex=Number(b.dataset.highlightTile);renderTile();}));
 el('tile-reading-close').innerHTML=currentReading.closing_variables.length?`The variables ${currentReading.closing_variables.map(v=>`\\(${esc(name(v))}\\)`).join(', ')} were arbitrary. The checker then universally generalizes this equation to ${math(theorem().target)}. These closing inferences are recorded after the tile row.`:'';
 typesetParts(['tile-reading-chain','tile-reading-steps','tile-reading-close']);
}

function renderTile(){
 const row=tileRow(),t=row.tiles[tileIndex],owned=new Set(t.members.map(k=>k[0])),ids=[...new Set(t.marks.filter(([p])=>p[1]===1).map(([,v])=>v))];
 el('tile-select').value=String(tileIndex);el('tile-svg').innerHTML=wangTileSvg(row,tileIndex,el('tile-view').value==='isolated');el('tile-previous').disabled=tileIndex===0;el('tile-next').disabled=tileIndex===row.tiles.length-1;
 const candidate=typeof t.candidate==='number'?String(t.candidate):JSON.stringify(t.candidate),remote=t.marks.filter(([p])=>p[1]===1&&!owned.has(p[0]/2));
 const selectedSteps=currentReading.steps.filter(s=>s.tileIndex===tileIndex);
 el('tile-selected-reading').innerHTML='<p class="english-label">THE HIGHLIGHTED TILE IN MATHEMATICAL LANGUAGE</p>'+selectedSteps.map(s=>`<div class="tile-decoded-cell" data-decoded-cell="${s.slot}"><p class="small">Cell ${s.slot+1} · formula port <code>F${s.formula_id}</code></p><div class="equation">${math(s.formula)}</div><p>${englishSentence(s.formula)}</p><p class="small">${cellReading(s)}</p></div>`).join('');
 el('tile-detail').innerHTML=`<p><strong>Tile ${tileIndex+1}: ${esc(t.kind)}</strong> · actual search placement ${t.search_step}</p><p>Candidate ID: <code>${esc(candidate)}</code> · occupies cells ${t.members.map(k=>k[0]+1).join(', ')} · ${remote.length} distant formula ${remote.length===1?'contact':'contacts'}.</p>`+(t.item?`<p>Cluster level ${t.item.level} · checked template <code>${esc(t.item.template)}</code>. Open the exact values below for its complete descriptor.</p>`:'')+ids.map(id=>`<div class="tile-formulas"><code>F${id}</code><div class="equation">${math(row.formulas[id])}</div></div>`).join('');
 el('tile-proof-links').innerHTML=t.root_lines.length?t.root_lines.map(i=>`<button type="button" data-tile-line="${i}">Read proof line ${i+1} for this tile</button>`).join(''):'<p class="small">This placed tile is outside the compact goal chain.</p>';
 el('tile-proof-links').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{setView('root');jump(Number(b.dataset.tileLine));el('reader').scrollIntoView({behavior:'smooth',block:'start'});}));
 el('tile-values').innerHTML='<table><thead><tr><th>Point</th><th>Channel</th><th>Exact value</th></tr></thead><tbody>'+t.weights.map(([p,v])=>`<tr><td>\\((${p.join(',')})\\)</td><td>Occupancy</td><td>\\(t=${v}/12=${v/12}\\)</td></tr>`).join('')+t.marks.map(([p,v])=>`<tr><td>\\((${p.join(',')})\\)</td><td>${p[1]===1?(owned.has(p[0]/2)?'Formula at an occupied cell':'Distant premise formula; this tile has \\(t=0\\) here'):'Cluster ownership'}</td><td>${p[1]===1?`<code>F${v}</code>: ${math(row.formulas[v])}`:`<code>${esc(v)}</code>`}</td></tr>`).join('')+'</tbody></table>';
 el('raw-tile').textContent=JSON.stringify(t,null,2);renderTileReading();typesetParts(['tile-selected-reading','tile-detail','tile-values']);
}
function chooseTiles(){
 const row=tileRow();currentReading=readWangTiles(row,theorem());el('tiles-heading').textContent=`Tiles for ${theorem().label}`;el('tiles-target').innerHTML=math(theorem().target);el('tile-provenance').textContent=`${row.tiles.length} actual selected placements cover ${row.length} cells, drawn from ${row.candidate_universe.toLocaleString()} legal positional candidates. Displayed tiles bind the exact accepted certificate shown below.`;
 el('tile-row-meaning').innerHTML=`This assembled row proves: <strong>${englishSentence(theorem().target)}</strong>`;
 el('tile-row-formula').innerHTML=readingEquation(currentReading.chain,false);
 el('tile-row-argument').innerHTML=currentReading.chain.map(s=>cellReading(s)).join(' ')+` Therefore, ${math(currentReading.conclusion)}.`;
 el('tile-select').replaceChildren();row.tiles.forEach((t,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`Tile ${i+1} · ${t.kind} · placement ${t.search_step}`;el('tile-select').append(o);});const first=row.tiles.findIndex(t=>t.kind==='searched cluster');tileIndex=first<0?row.tiles.length-1:first;renderTile();typesetParts(['tiles-target','tile-row-meaning','tile-row-formula','tile-row-argument']);
}

function choose(index,scroll=false){
 current=index;const t=theorem();views=[{id:'root',label:'High-level root certificate',proof:t.request.proof},{id:'expanded',label:'Fully expanded primitive root',proof:t.expanded_proof},...t.request.blocks.map((b,i)=>({id:`block:${b.name}`,label:`Lemma ${i+1} · ${b.proof.length} local lines`,proof:b.proof,definition:b}))];
 el('proof-view').replaceChildren();views.forEach(v=>{const o=document.createElement('option');o.value=v.id;o.textContent=v.label;el('proof-view').append(o);});el('reader-heading').textContent=t.label;el('theorem-target').innerHTML=math(t.target);
 el('provenance').textContent=`Discovered by ${t.discovered_by==='donor-gcts'?'fresh donor GCTS':t.discovered_by} · ${t.origin} · ${t.search.nodes} visited states / ${t.search.base_attempts} expanded placement attempts · complete native acceptance (${t.native.steps.toLocaleString()} instructions) · ${t.expanded_lines} independently checked primitive lines. No proof sequence was supplied.`;
 el('theory').innerHTML='<p><strong>External theory axioms</strong></p>'+Object.entries(t.theory.axioms).map(([n,a])=>`<p><code>${esc(n)}</code><br>${math(a)}</p>`).join('')+`<p>Registered schemas: ${t.theory.schemas.length?t.theory.schemas.map(esc).join(', '):'none in this searched example'}.</p>`;
 el('certificate-links').innerHTML=`<a href="${esc(t.certificate_file)}">Exact accepted certificate JSON</a> · <a href="${esc(t.source_artifact.file)}">Parent search evidence</a><br>Problem SHA-256: <code>${esc(t.problem_sha256)}</code><br>Certificate SHA-256: <code>${esc(t.certificate_sha256)}</code>`;
 el('theorem-list').querySelectorAll('.theorem-card').forEach((card,i)=>card.classList.toggle('selected',i===current));setView('root');chooseTiles();typesetParts(['theorem-target','theory']);if(scroll)el('reader').scrollIntoView({behavior:'smooth',block:'start'});
}
async function start(){
 const responses=await Promise.all(['wang-proofs-001.json','wang-tiles-001.json'].map(file=>fetch(`${file}?v=20261009-r33.6`)));for(const r of responses)if(!r.ok)throw Error(`HTTP ${r.status}`);const raw=await Promise.all(responses.map(r=>r.text()));data=JSON.parse(raw[0]);tileData=JSON.parse(raw[1]);const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw[0])),pin=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');if(pin!==tileData.proof_reader.sha256||tileData.parent.sha256!==data.parent.sha256)throw Error('Tile/proof evidence binding mismatch');if(tileData.theorems.length!==data.theorems.length||data.theorems.some(t=>{const row=tileData.theorems.find(r=>r.id===t.id);return !row||row.certificate_sha256!==t.certificate_sha256||row.problem_sha256!==t.problem_sha256;}))throw Error('Tile/certificate binding mismatch');el('verified-count').textContent=data.held_out_verified;el('donor-count').textContent=data.donors_verified;el('expanded-count').textContent=data.expanded_primitive_lines.toLocaleString();
 el('theorem-list').innerHTML=data.theorems.map((t,i)=>`<article class="theorem-card" data-theorem="${esc(t.id)}"><div class="equation">${math(t.target)}</div><p class="small">${esc(t.origin)} · ${t.expanded_lines} primitive lines · complete native acceptance</p><button type="button" data-theorem-index="${i}">Read this proof</button><button type="button" data-theorem-index="${i}" data-show-tiles="true">See its tiles</button></article>`).join('');el('theorem-list').querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{choose(Number(button.dataset.theoremIndex),!button.dataset.showTiles);if(button.dataset.showTiles)el('tiles').scrollIntoView({behavior:'smooth',block:'start'});}));
 el('control-list').innerHTML=data.controls.map(control=>`<p>${math(control.problem.target)} · ${esc(control.problem.label)}: all declared finite controls exhaust this particular cell/term envelope. This is not a displayed positive theorem.</p>`).join('')+data.pending.map(control=>`<p>${math(control.problem.target)} · no positive point-search certificate in this fresh run. Unknown requests remain unknown.</p>`).join('');
 el('proof-view').addEventListener('change',()=>setView(el('proof-view').value));el('line-select').addEventListener('change',()=>jump(Number(el('line-select').value)));el('previous').addEventListener('click',()=>jump(line-1));el('next').addEventListener('click',()=>jump(line+1));el('previous-page').addEventListener('click',()=>jump((Math.floor(line/pageSize)-1)*pageSize));el('next-page').addEventListener('click',()=>jump((Math.floor(line/pageSize)+1)*pageSize));
 el('translation-detail').addEventListener('change',renderTileReading);el('tile-select').addEventListener('change',()=>{tileIndex=Number(el('tile-select').value);renderTile();});el('tile-view').addEventListener('change',renderTile);el('tile-previous').addEventListener('click',()=>{tileIndex--;renderTile();});el('tile-next').addEventListener('click',()=>{tileIndex++;renderTile();});el('load').textContent='';choose(0);typesetParts(['theorem-list','control-list']);await typeset;const anchor=location.hash&&el(location.hash.slice(1));if(anchor)anchor.scrollIntoView({block:'start'});
}
start().catch(e=>el('load').textContent=`Proof evidence unavailable: ${e.message}`);
