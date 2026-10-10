'use strict';
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function tex(a){if(a.length===1)return a[0];if(a[0]==='pred')return a[1];if(a[0]==='not')return '\\neg ('+tex(a[1])+')';return '('+tex(a[1])+'\\Rightarrow '+tex(a[2])+')';}
function word(a){return a.length===1?a[0]:a[0]==='not'?'n'+word(a[1]):'i'+word(a[1])+word(a[2]);}
function checkRows(rows,target,hyp=[]){const vals=new Map(hyp.map((a,j)=>[j-hyp.length,a]));const imp=(a,b)=>['imp',a,b];const not=a=>['not',a];
 rows.forEach((r,j)=>{let ok=false,a=r.formula;
 if(r.kind==='mp')ok=r.refs.length===2&&r.refs.every(k=>Number.isInteger(k)&&k<j&&vals.has(k))&&equal(vals.get(r.refs[1]),imp(vals.get(r.refs[0]),a));
 else if(r.kind==='lemma')ok=!r.refs.length&&equal(a,imp(r.parameter,r.parameter))&&checkRows(r.expansion,a);
 else if(!r.refs.length){try{if(r.kind==='H1')ok=equal(a,imp(a[1],imp(a[2][1],a[1])));if(r.kind==='H2'){const x=a[1][1],y=a[1][2][1],z=a[1][2][2];ok=equal(a,imp(imp(x,imp(y,z)),imp(imp(x,y),imp(x,z))));}if(r.kind==='H3'){const x=a[2][1],y=a[2][2];ok=equal(a,imp(imp(not(y),not(x)),imp(x,y)));}}catch{}}
 if(!ok)throw Error('Invalid displayed inference');vals.set(j,a);});
 if(!rows.length||!equal(rows.at(-1).formula,target))throw Error('Changed target');return true;
}
function validate(v){if(v.version!=='factored-receptors-reader-001'||v.cases.length!==6||v.native.result!=='accepted'||v.native.lines.length!==5||v.native.inventory_fingerprint!=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455')throw Error('Changed experiment');
 for(const c of v.cases){for(const [lane,r] of Object.entries(c.runs)){if(!r.proof)continue;checkRows(r.proof,c.target,c.hypotheses);if(['factored','factored-rl','ground'].includes(lane)){
 if(r.point_tiles.length!==c.length||r.placements.length!==c.length)throw Error('Incomplete points');const seen=new Set();
 r.point_tiles.forEach((t,k)=>{const j=t.key[0],row=r.proof[j];if(seen.has(j)||!equal(t.key,r.placements[k])||!equal(t.key[2],row.refs)||!equal(t.occupancy,[[[2*j,0],12]]))throw Error('Changed occupancy');seen.add(j);
 const ports=[[j,row.formula],...row.refs.map(i=>[i,i<0?c.hypotheses[i+c.hypotheses.length]:r.proof[i].formula])],marks=new Map();
 for(const [i,a] of ports){marks.set(JSON.stringify([2*i,1]),0);Array.from(word(a)+'e').forEach((s,k)=>marks.set(JSON.stringify([2*i,2+k]),s));}
 if(t.marks.length!==marks.size)throw Error('Changed mark support');const unique=new Set();for(const [p,s] of t.marks){const key=JSON.stringify(p);if(unique.has(key)||marks.get(key)!==s)throw Error('Changed mark value');unique.add(key);}
 });}}
 if(c.runs.ground.status!=='not_run_declared_candidate_cap'&&!equal(c.runs.ground.proof,c.runs.factored.proof))throw Error('Changed matched proof');}
 const conditional=v.cases.find(c=>c.id==='double-negation-premise'),rows=conditional.runs.factored.proof,fol=a=>a.length===1?['pred',a[0],[]]:[a[0],...a.slice(1).map(fol)];
 const formulas=[...conditional.hypotheses.map(fol),...rows.map(r=>fol(r.formula))];
 v.native.lines.forEach((l,j)=>{const cmd=l.input.pending[0];
 if(l.label.line!==j||l.label.scope!=='root'||!equal(l.label.formula,formulas[j])||!equal(cmd.formula,formulas[j])||!equal(l.input.target,fol(conditional.target))||!equal(l.input.proved,formulas.slice(0,j))||!equal(l.output.proved,formulas.slice(0,j+1))||!equal(l.input.theory.axioms['premise-0'],fol(conditional.hypotheses[0])))throw Error('Changed native context');
 if(j===0){if(cmd.rule!=='axiom'||cmd.name!=='premise-0')throw Error('Changed premise');}
 else {const r=rows[j-1];if(cmd.rule!==(r.kind==='mp'?'mp':'tautology')||(r.kind==='mp'&&(cmd.antecedent!==r.refs[0]+1||cmd.implication!==r.refs[1]+1)))throw Error('Changed compiled reference');}
 });
 return true;
}
if(typeof module!=='undefined')module.exports={tex,word,checkRows,validate};
if(typeof document!=='undefined'){
const $=id=>document.getElementById(id),math=s=>'\\('+s+'\\)',esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let data,cases;
function label(j,h){return j<0?'hypothesis '+(j+h+1):'line '+(j+1);}
function english(r,h){return r.kind==='mp'?'Apply modus ponens to '+label(r.refs[0],h)+' and '+label(r.refs[1],h)+'.':r.kind==='lemma'?'Use the freshly discovered identity family; its five primitive lines are checked.':{H1:'Use the weakening axiom schema.',H2:'Use the implication-distribution axiom schema.',H3:'Use the classical contraposition axiom schema.'}[r.kind];}
function showMarks(c,j){const r=c.runs.factored, tile=r.point_tiles.find(t=>t.key[0]===j), layer=$('layer').value, marks=tile.marks.filter(([p])=>layer==='all'||(layer==='scope'?p[1]===1:p[1]>=2));
 const ports=[...new Set(marks.map(([p])=>p[0]/2))].sort((a,b)=>a-b);const span=ports.at(-1)-ports[0],wide=Math.max(280,span*85+110),maxY=Math.max(2,...marks.map(([p])=>p[1])),height=maxY*20+110;
 const xpos=k=>ports.length===1?wide/2:55+(k-ports[0])*85;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+wide+' '+height+'" role="img" aria-label="Actual finite-alphabet marking support for selected inference">';
 for(const k of ports){svg+='<text x="'+xpos(k)+'" y="20" text-anchor="middle" font-size="12" fill="#34443d">'+label(k,c.hypotheses.length)+'</text>';if(k===j)svg+='<rect x="'+(xpos(k)-13)+'" y="29" width="26" height="15" fill="#34443d"/><text x="'+xpos(k)+'" y="41" text-anchor="middle" font-size="10" fill="white">12</text>';}
 for(const [p,v] of marks){const k=p[0]/2,fill=p[1]===1?'#995fa9':k===j?'#27866e':'#347eb0';svg+='<rect x="'+(xpos(k)-13)+'" y="'+(30+p[1]*20)+'" width="26" height="18" rx="2" fill="'+fill+'"/><text x="'+xpos(k)+'" y="'+(43+p[1]*20)+'" text-anchor="middle" font-family="monospace" font-size="12" fill="white">'+esc(v)+'</text>';}
 if(ports.includes(j))for(const k of ports.filter(k=>k!==j))svg+='<path d="M '+xpos(j)+' '+(height-48)+' L '+xpos(k)+' '+(height-48)+'" stroke="#347eb0" stroke-dasharray="4 4" fill="none"/>';
 svg+='<text x="'+wide/2+'" y="'+(height-18)+'" text-anchor="middle" font-size="11" fill="#59675d">Exact values; dashed lines explain references</text></svg>';
 $('marks').innerHTML=svg;$('exact').textContent=JSON.stringify(tile,null,2);
}
async function render(){const c=cases[Number($('case').value)],r=c.runs.factored,j=Number($('line').value);
 $('statement').innerHTML=math((c.hypotheses.length?c.hypotheses.map(tex).join(',\\;'):'')+'\\;\\vdash\\;'+tex(c.target));
 $('proof').innerHTML=(c.hypotheses.length?'<p class="muted">Hypothesis: '+c.hypotheses.map(a=>math(tex(a))).join(', ')+'</p>':'')+r.proof.map((row,i)=>`<div class="line ${i===j?'active':''}"><b>Line ${i+1} · ${esc(row.kind)}</b><p class="formula">${math(tex(row.formula))}</p><p>${english(row,c.hypotheses.length)}</p></div>`).join('');showMarks(c,j);
 $('order').textContent='Actual placement order: '+r.placements.map(k=>label(k[0],c.hypotheses.length)).join(', ')+'. Logical references remain backward.';
 $('frames').innerHTML=(c.frames||[]).map((f,i)=>`<details><summary>Placement ${i+1} · ${f.kind} · ${label(f.key[0],0)}</summary><table><tr><th>Frontier point</th><th>Complete candidates</th><th>Factor records</th></tr>${f.domains.map(d=>`<tr><td><code>${d.point.join(',')}</code></td><td>${d.count.toLocaleString()}</td><td>${d.factor_records.toLocaleString()}</td></tr>`).join('')}</table><pre>${esc(JSON.stringify(f.domains.map(d=>({point:d.point,first_blocks:d.sample_blocks})),null,2))}</pre></details>`).join('');
 await window.MathJax?.typesetPromise?.([$('statement'),$('proof')]);}
async function choose(){const c=cases[Number($('case').value)];$('line').innerHTML=c.runs.factored.proof.map((r,j)=>`<option value="${j}">Line ${j+1} · ${r.kind}</option>`).join('');await render();}
function measurement(r){if(!('seconds' in r))return 'Not run: declared candidate cap';const found=!!r.proof;return (found?'Found':r.status.startsWith('exhausted')?'Exhausted':'Unknown at budget')+'<br>'+((r.seconds||0)+(r.build_seconds||0)).toFixed(6)+' s'+(r.metrics?.nodes?'<br>'+r.metrics.nodes+' states':'')+(found?'<br>'+r.proof.length+' commands':'');}
async function start(){try{const res=await fetch('factored-receptors-reader-001.json?v=20261010-f1');if(!res.ok)throw Error('Reader unavailable');data=await res.json();validate(data);cases=data.cases.filter(c=>c.runs.factored.proof);
 $('case').innerHTML=cases.map((c,j)=>`<option value="${j}">${esc(c.title)}</option>`).join('');$('case').value='1';
 $('bench').innerHTML=data.cases.map(c=>`<tr><td>${esc(c.title)}<br>${c.rules.toLocaleString()} rules / ${c.candidate_universe.toLocaleString()} candidate placements</td>${['ground','factored','factored-rl','chronological','saturation'].map(k=>'<td>'+measurement(c.runs[k])+'</td>').join('')}</tr>`).join('');
 $('audit').textContent=`Search production ${data.seconds.toFixed(3)} s; independent audit ${data.audit.seconds.toFixed(3)} s; ${data.audit.mutations} mutations rejected; ${data.audit.policy_proposal_steps} frozen-policy proposal steps independently checked. Process peak memory ${(data.peak_process_rss_bytes/1e6).toFixed(1)} MB across all lanes. Reused policy training ${data.reused_policy_training_seconds.toFixed(3)} s, charged separately.`;
 const n=data.native;$('native').innerHTML=`<p>The new conditional proof accepts in the unchanged literal core. Builder ${n.builder.wall_seconds.toFixed(3)} s; response derivation ${n.checker.wall_seconds.toFixed(3)} s; actual literal run ${n.literal.wall_seconds.toFixed(3)} s; independent operational audit ${n.audit_seconds.toFixed(3)} s.</p>`+n.lines.map(l=>`<div class="line"><b>Machine command ${l.label.line+1} · ${esc(l.label.rule)}</b><p class="formula">${math(tex(l.label.formula))}</p><p class="muted">${l.input.proved.length} prior facts become ${l.output.proved.length}; ${l.physical_height.toLocaleString()} exact literal transitions in this command fragment.</p></div>`).join('')+`<p><a href="${n.grammar.name}">Full grammar</a> · <a href="${n.events.name}">Actual checkpoints</a> · <a href="${n.responses.name}">Derived responses</a></p>`;
 $('load').textContent='Independent search and operational audits passed · five discovered proofs available.';
 await choose();await window.MathJax?.typesetPromise?.([$('native')]);$('case').addEventListener('change',choose);$('line').addEventListener('change',render);$('layer').addEventListener('change',render);
 }catch(e){$('load').textContent='Validation failed: '+e.message;console.error(e);}}start();}
