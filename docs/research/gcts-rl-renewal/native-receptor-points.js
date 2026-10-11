'use strict';
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
function formula(a){
 const f=formula,k=a[0],name=s=>String(s).replace(/[^A-Za-z0-9]/g,'');
 if(k==='var')return name(a[1]);
 if(k==='bot')return '\\bot';
 if(k==='fun'){
  if(a[1]==='zero')return '0';if(a[1]==='succ')return 'S('+f(a[2][0])+')';if(!a[2].length)return a[1]==='l'?'\\ell':name(a[1]);
  if(a[1]==='add'||a[1]==='mul')return '('+f(a[2][0])+(a[1]==='add'?'+':'\\cdot ')+f(a[2][1])+')';
  return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';
 }
 if(k==='pred')return '\\operatorname{'+name(a[1])+'}'+(a[2].length?'('+a[2].map(f).join(',')+')':'');
 if(k==='eq')return f(a[1])+'='+f(a[2]);
 if(k==='all')return '\\forall '+name(a[1])+'\\;('+f(a[2])+')';
 if(k==='not'&&a[1][0]==='all'&&a[1][2][0]==='not')return '\\exists '+name(a[1][1])+'\\;('+f(a[1][2][1])+')';
 if(k==='not')return '\\neg('+f(a[1])+')';
 if(['imp','and','or'].includes(k))return '('+f(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+f(a[2])+')';
 throw Error('Unknown syntax');
}
const reason={axiom:'Use the named axiom from the input theory.',refl:'A term equals itself.',tautology:'This formula is a checked propositional tautology.',instantiate:'Instantiate a universal formula using capture-avoiding substitution.',mp:'Apply the earlier implication to its earlier antecedent.',generalize:'Universally quantify the variable; it is absent from every open premise.',eq_subst:'Substitute equal terms in the indicated formula.',distribute:'Move the quantifier across an implication with the variable condition checked.',induction:'Use the explicitly authorized natural-number induction schema.',assumption:'Use an input premise of this local block.',block:'Apply a previously checked lemma to the matching earlier premises.'};
const SAME=(a,b)=>eq(a,b);
function validateReceptors(v){
 if(v.version!=='native-receptor-points-reader-001'||v.audit.status!=='passed'||v.inventory.fingerprint!=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455'||v.inventory.symbols!==60||v.inventory.states!==462276)throw Error('Fixed palette/audit changed');
 if(v.cases.length!==10||v.observations.length!==20||v.proofs.length!==6)throw Error('Experiment coverage changed');
 for(const p of v.proofs){
  const c=v.cases.find(c=>c.id===p.case);if(!c||!SAME(c.target,p.request.target)||!SAME(c.theory,p.request.theory)||p.request.blocks.length||p.request.proof.length!==c.length||p.lines.length!==c.length)throw Error('Assertion/proof binding changed');
  if(p.builder.status!=='accepted'||p.literal.status!=='accepted'||p.checker.result!=='accepted'||p.builder.micro_steps!==p.literal.micro_steps||p.builder.micro_steps!==p.checker.micro_steps||p.builder.physical_steps!==p.literal.physical_steps||p.builder.physical_steps!==p.checker.physical_steps)throw Error('Full native acceptance changed');
  const tr=p.trace;if(tr.status!=='native_proof_discovered'||tr.case.id!==p.case||!SAME(tr.proof,p.request.proof)||!SAME(tr.records[tr.verification_query].request,p.request)||tr.records[tr.verification_query].result.status!=='accepted'||!tr.search.root_restored||tr.compiled.status!=='complete')throw Error('Point discovery binding changed');
  validatePointTrace(tr);
  const final=tr.records[tr.verification_query];if(tr.verification_query!==tr.compiled.basis.length||final.purpose!=='searched_certificate_without_point_markings'||final.query_target!=='fixed_assertion'||final.result.start!==88986)throw Error('Marking-erased whole-check boundary changed');
  p.lines.forEach((l,j)=>{
   const cmd=p.request.proof[j];if(l.outcome!=='line-checked'||l.label.scope!=='root'||l.label.line!==j||l.label.rule!==cmd.rule||!SAME(l.label.formula,cmd.formula)||!SAME(l.input.pending,p.request.proof.slice(j))||!SAME(l.input.proved,p.request.proof.slice(0,j).map(c=>c.formula))||!SAME(l.output.proved,p.request.proof.slice(0,j+1).map(c=>c.formula))||!SAME(l.output.pending,p.request.proof.slice(j+1)))throw Error('Actual line context changed');
   for(const ctx of [l.input,l.output])if(!SAME(ctx.theory,p.request.theory)||!SAME(ctx.target,p.request.target)||ctx.assumptions.length||ctx.registry.length||ctx.forbidden.length)throw Error('Actual theory/scope changed');
   if(l.q!==1688||l.out!==1688||l.micro_steps<=0||l.physical_height<=0||l.literal_width<=0)throw Error('Fragment receptor changed');
   const patch=l.patch;if(patch.width!==9||patch.height!==3||patch.rows.length!==4||patch.tiles.length!==27||patch.trajectory[0][0]!==6746||patch.prefix_physical_steps!==l.input_head+patch.marker+1||patch.prefix_physical_steps+3>l.physical_height)throw Error('Native crop changed');
   const seen=new Set();for(const t of patch.tiles){const at=t.x+','+t.y;if(seen.has(at)||t.x<0||t.x>=9||t.y<0||t.y>=3)throw Error('Tile occupancy changed');seen.add(at);const triple=patch.rows[t.y].slice(t.x,t.x+3),n=coreOutput(v,triple);if(!SAME(t.triple,triple)||t.identity!==triple.join(':')||t.S!==triple[1]||t.N!==n||n!==patch.rows[t.y+1][t.x+1]||!SAME(t.W,triple.slice(0,2))||!SAME(t.E,triple.slice(1)))throw Error('Native point values changed');}
  });
 }
 return {proofs:v.proofs.length,lines:v.proofs.reduce((n,p)=>n+p.lines.length,0),tiles:v.proofs.reduce((n,p)=>n+p.lines.length*27,0),queries:v.audit.queries,observations:v.observations.length};
}
function stable(x){if(Array.isArray(x))return x.map(stable);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])]));return x;}
const packed=x=>JSON.stringify(stable(x)),eq=(a,b)=>packed(a)===packed(b),pointKey=p=>p.join(',');
function validatePointTrace(tr){
 const m=tr.model,spec=tr.case,formulaPort=(j,a,ch='formula')=>[...new TextEncoder().encode(packed(a)),256].map((v,k)=>[[4*j+(ch==='command'?1:0),100+k],v]);
 const all=new Map(),basis=[],seen=new Set(),variables=new Set();
 const term=t=>{if(t[0]==='var')variables.add(t[1]);else t[2].forEach(term);};
 const visit=a=>{const k=packed(a);if(seen.has(k))return;seen.add(k);basis.push(a);if(a[0]==='all'){variables.add(a[1]);visit(a[2]);}else if(['imp','and','or'].includes(a[0])){visit(a[1]);visit(a[2]);}else if(a[0]==='not')visit(a[1]);else if(a[0]==='eq'){term(a[1]);term(a[2]);}else if(a[0]==='pred')a[2].forEach(term);};visit(spec.target);Object.values(spec.theory.axioms).forEach(visit);
 // The grammar uses bytewise ordering; locale collation is not that order.
 basis.sort((a,b)=>packed(a)<packed(b)?-1:packed(a)>packed(b)?1:0);
 if(!eq(basis,tr.compiled.basis)||!eq([...variables].sort(),tr.compiled.variables))throw Error('Syntactic basis changed');
 if(tr.compiled.queries.length!==basis.length||tr.records.length!==basis.length+1||!eq(tr.compiled.tautologies,basis.filter((f,j)=>tr.records[j].result.status==='accepted')))throw Error('Native guard catalog changed');
 basis.forEach((f,j)=>{const r=tr.records[j];if(tr.compiled.queries[j]!==j||r.id!==j||r.purpose!=='tautology_instance'||r.basis_index!==j||r.result.start!==88986||!['accepted','rejected'].includes(r.result.status)||!eq(r.request,{protocol:'gcts-fol-1',theory:spec.theory,blocks:[],proof:[{rule:'tautology',formula:f}],target:f}))throw Error('Guard query binding changed');});
 const domains=Array.from({length:spec.length},(_,j)=>{
  const rows=[];for(const f of j+1===spec.length?[spec.target]:basis){for(const name of Object.keys(spec.theory.axioms).sort())rows.push({rule:'axiom',formula:f,name});for(const variable of [...variables].sort())for(let source=0;source<j;source++)rows.push({rule:'generalize',formula:f,variable,source});for(let antecedent=0;antecedent<j;antecedent++)for(let implication=0;implication<j;implication++)rows.push({rule:'mp',formula:f,antecedent,implication});for(const rule of ['refl','tautology'])rows.push({rule,formula:f});}rows.sort((a,b)=>{for(const [u,v] of [[a.rule,b.rule],[packed(a.formula),packed(b.formula)],[packed(a),packed(b)]])if(u!==v)return u<v?-1:1;return 0;});return rows;
 });if(!eq(domains,m.domains)||!eq(domains.map(d=>d.length),m.command_counts)||m.complete_words!==domains.reduce((n,d)=>n*d.length,1))throw Error('Original command grammar changed');
 const taut=new Set(tr.compiled.tautologies.map(packed)),expected=[];
 function add(key,c,requirements){const j=key[0],role=key[1],marks=new Map(),entries=[...formulaPort(j,c,'command'),...formulaPort(j,c.formula),...requirements.flatMap(([i,a])=>formulaPort(i,a))];for(const [p,v] of entries){const k=pointKey(p);if(marks.has(k)&&marks.get(k)!==v)return;marks.set(k,v);}expected.push({key,occupancy:[[[4*j,role],12]],marks:[...marks].map(([p,v])=>[p.split(',').map(Number),v]).sort((a,b)=>a[0][0]-b[0][0]||a[0][1]-b[0][1]),slot:j,kind:role?'guard':'command',command:c,requirements});}
 domains.forEach((rows,j)=>rows.forEach((c,k)=>{add([j,0,k,0],c,[]);const f=c.formula,r=c.rule;if(r==='axiom'&&eq(spec.theory.axioms[c.name],f)||r==='refl'&&f[0]==='eq'&&eq(f[1],f[2])||r==='tautology'&&taut.has(packed(f)))add([j,1,k,0],c,[]);if(r==='generalize'&&f[0]==='all'&&f[1]===c.variable)add([j,1,k,0],c,[[c.source,f[2]]]);if(r==='mp')basis.forEach((a,n)=>{if(a[0]==='imp'&&eq(a[2],f))add([j,1,k,n],c,[[c.antecedent,a[1]],[c.implication,a]]);});}));
 const keyCompare=(a,b)=>{for(let i=0;i<4;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;};expected.sort((a,b)=>keyCompare(a.key,b.key));if(!eq(expected,m.placements))throw Error('Complete point inventory or distant marks changed');expected.forEach(c=>all.set(pointKey(c.key),c));
 const roots=Array.from({length:spec.length},(_,j)=>[[4*j,0],[4*j,1]]).flat();if(!eq(roots,m.roots))throw Error('Untouched root obligations changed');const marks=new Map(formulaPort(spec.length-1,spec.target).map(([p,v])=>[pointKey(p),v]));let nodes=0,accepted=null;
 const legal=(c,selected,values)=>!selected.has(pointKey(c.key))&&!selected.has('root:'+pointKey(c.occupancy[0][0]))&&c.marks.every(([p,v])=>!values.has(pointKey(p))||values.get(pointKey(p))===v);
 function walk(t,selected,values,path){nodes++;const census=roots.filter(p=>!selected.has('root:'+pointKey(p))).map(p=>({point:p,generation:0,keys:expected.filter(c=>eq(c.occupancy[0][0],p)&&legal(c,selected,values)).map(c=>c.key)}));if(!eq(census,t.census))throw Error('Complete displayed graph changed');const dead=census.find(p=>!p.keys.length),forced=census.find(p=>p.keys.length===1),branch=[...census].sort((a,b)=>a.keys.length-b.keys.length||a.point[0]-b.point[0]||a.point[1]-b.point[1])[0];const choice=dead||forced||branch,kind=dead?'dead':forced?'forced':choice?'branch':'empty';if(t.kind!==kind||!eq(t.point,choice?.point??null))throw Error('Scheduler changed');if(kind==='dead'){if(t.children.length)throw Error('Dead child');return false;}if(kind==='empty'){accepted=path;if(t.children.length)throw Error('Extra finished child');return true;}for(let i=0;i<t.children.length;i++){const child=t.children[i];if(!eq(child.key,choice.keys[i]))throw Error('Original alternative removed');const c=all.get(pointKey(child.key)),s=new Set(selected),v=new Map(values);s.add(pointKey(c.key));s.add('root:'+pointKey(c.occupancy[0][0]));c.marks.forEach(([p,x])=>v.set(pointKey(p),x));const ok=walk(child.tree,s,v,[...path,c.key]);if(ok){if(i+1!==t.children.length)throw Error('Choices after acceptance');return true;}}if(t.children.length!==choice.keys.length)throw Error('Incomplete displayed successful tree');return false;}
 if(!walk(tr.search.tree,new Set(),marks,[])||!eq(accepted,tr.search.placements)||nodes!==tr.search.metrics.nodes)throw Error('Point solution changed');
 const decoded=accepted.filter(k=>k[1]===0).sort(keyCompare).map(k=>all.get(pointKey(k)).command);if(!eq(decoded,tr.proof))throw Error('Point-to-command decoding changed');
 return {nodes,placements:expected.length};
}
if(typeof module!=='undefined')module.exports={validateReceptors,validatePointTrace,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),math=a=>'\\('+formula(a)+'\\)';let view,chosen=2,index=0,nodes=[];
 const refs=c=>c.rule==='mp'?[c.antecedent,c.implication]:c.rule==='generalize'?[c.source]:[];
 const english=c=>reason[c.rule]+(c.rule==='axiom'?' Input premise “'+c.name+'”.':refs(c).length?' Earlier '+(refs(c).length===1?'line ':'lines ')+refs(c).map(i=>i+1).join(' and ')+'.':'');
 const nativeColor=(v,l)=>{let n=0;for(const x of Array.isArray(v)?v:[v])n=(Math.imul(n,31)+x)>>>0;return 'hsl('+((l==='vertical'?205:140)+n%30)+' 58% '+(38+n%24)+'%)';};
 function pointPicture(p){
  const mode=el('layer').value,s=78,n=p.request.proof.length;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 '+(30+s*n)+'" role="img" aria-label="Exact formula markings linking command and guard point tiles"><text x="24" y="16" font-size="12">Command</text><text x="145" y="16" font-size="12">Rule guard</text><text x="275" y="16" font-size="12">Formula port</text>';
  p.request.proof.forEach((c,j)=>{const y=30+j*s,active=j===index;
   for(const [x,kind] of [[24,'command'],[145,'guard']])svg+='<rect x="'+x+'" y="'+y+'" width="57" height="57" fill="'+(active?'#eee3f2':'#f3f6ef')+'" stroke="#c2cdbb"/><circle cx="'+(x+28)+'" cy="'+(y+28)+'" r="4" fill="#23856b"/><rect x="'+(x+2)+'" y="'+(y+2)+'" width="53" height="6" fill="'+(mode==='formula'?'#d9dfd6':'#b98528')+'"/><rect x="'+(x+2)+'" y="'+(y+49)+'" width="53" height="6" fill="'+(mode==='command'?'#d9dfd6':'#8654a0')+'"/><text x="'+(x+28)+'" y="'+(y+20)+'" text-anchor="middle" font-size="10">'+(kind==='command'?'C':'G')+(j+1)+'</text><text x="'+(x+28)+'" y="'+(y+42)+'" text-anchor="middle" font-size="9">'+esc(c.rule)+'</text>';
   svg+='<path d="M 81 '+(y+28)+' H 145" stroke="'+(mode==='formula'?'#d9dfd6':'#b98528')+'" stroke-width="3"/><path d="M 202 '+(y+28)+' H 270" stroke="'+(mode==='command'?'#d9dfd6':'#8654a0')+'" stroke-width="3"/>';const bytes=[...new TextEncoder().encode(packed(c.formula)),256],shown=bytes.slice(0,7).concat(256);
   shown.forEach((v,k)=>svg+='<rect x="'+(270+k*9)+'" y="'+(y+21)+'" width="7" height="14" fill="'+(mode==='command'?'#d9dfd6':'hsl('+(275+v%25)+' 55% '+(36+v%20)+'%)')+'"/>');
   svg+='<text x="270" y="'+(y+49)+'" font-size="10" font-family="monospace">'+bytes.length+' point values</text>';
   if(active)refs(c).forEach((i,k)=>{const x=385+20*k;svg+='<path d="M 343 '+(30+i*s+28)+' H '+x+' V '+(y+28)+' H 343" stroke="'+(mode==='command'?'#d9dfd6':'#8654a0')+'" stroke-width="3" fill="none"/><circle cx="343" cy="'+(30+i*s+28)+'" r="4" fill="#8654a0"/><circle cx="343" cy="'+(y+28)+'" r="4" fill="#8654a0"/>';});
  });el('point-picture').innerHTML=svg+'</svg>';
 }
 function nativePicture(p){
  const patch=p.lines[index].patch,s=75,ox=38,oy=22;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+(ox+patch.width*s+15)+' '+(oy+patch.height*s+20)+'" role="img" aria-label="Actual original native Wang squares at the selected proof line"><text x="4" y="14" font-size="12">time ↑</text>';
  for(const t of patch.tiles){const x=ox+t.x*s,y=oy+(patch.height-1-t.y)*s;svg+='<g><rect class="native-tile" x="'+(x+1)+'" y="'+(y+1)+'" width="73" height="73" fill="'+(t.triple.some(v=>v>=60)?'#fff3d9':'#f8faf5')+'" stroke="#acb9ad"/><rect x="'+(x+8)+'" y="'+(y+2)+'" width="59" height="7" fill="'+nativeColor(t.N,'vertical')+'"/><rect x="'+(x+8)+'" y="'+(y+66)+'" width="59" height="7" fill="'+nativeColor(t.S,'vertical')+'"/><rect x="'+(x+2)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.W,'horizontal')+'"/><rect x="'+(x+66)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.E,'horizontal')+'"/><circle cx="'+(x+37.5)+'" cy="'+(y+37.5)+'" r="3" fill="#242a28"/><text x="'+(x+37.5)+'" y="'+(y+25)+'" text-anchor="middle" font-size="9" font-family="monospace">N '+t.N+'</text><text x="'+(x+37.5)+'" y="'+(y+57)+'" text-anchor="middle" font-size="9" font-family="monospace">S '+t.S+'</text></g>';}el('literal').innerHTML=svg+'</svg>';
 }
 function showNode(){const node=nodes[Number(el('node-control').value)],t=node.tree;el('node-summary').textContent=t.kind+' · '+t.census.length+' frontier points · '+t.census.reduce((n,p)=>n+p.keys.length,0)+' complete incidences · '+node.path.length+' previous placements. Selected point: '+JSON.stringify(t.point)+'.';el('graph-table').innerHTML=t.census.map(p=>'<tr><td><code>'+JSON.stringify(p.point)+'</code></td><td>'+p.generation+'</td><td>'+p.keys.length+'</td><td>'+(eq(p.point,t.point)?t.kind:'—')+'</td></tr>').join('');}
 function read(){
  const p=view.proofs[chosen],l=p.lines[index],c=p.request.proof[index],selected=p.trace.search.placements.find(k=>k[0]===index&&k[1]===1),guard=p.trace.model.placements.find(a=>eq(a.key,selected));
  el('reading').innerHTML='<div class="formula">'+math(c.formula)+'</div><p>'+esc(english(c))+'</p><p class="small">This selected guard assigns '+guard.marks.length+' exact marking points, including '+guard.requirements.length+' earlier formula words. All are checked by point-value agreement.</p>';
  el('marks').textContent=JSON.stringify({key:guard.key,occupancy:guard.occupancy,command:guard.command,earlier_requirements:guard.requirements.map(([i,f])=>({source_line:i+1,formula:f,encoded_word:[...new TextEncoder().encode(packed(f)),256]})),all_marking_points:guard.marks},null,2);
  el('input').innerHTML='<p>'+l.input.proved.length+' earlier checked facts.</p>'+l.input.proved.map(a=>'<div class="formula">'+math(a)+'</div>').join('');el('output').innerHTML='<p>Append the formula. '+l.output.proved.length+' facts are available.</p><div class="formula">'+math(c.formula)+'</div>';el('expansion').textContent='The complete native line expands to '+l.micro_steps.toLocaleString()+' selected-symbol operations and '+l.physical_height.toLocaleString()+' literal transitions. The response checker derives the entire expansion; only the entry crop is drawn.';el('artifacts').innerHTML='Whole accepting certificate: <a href="'+p.grammar.name+'">response grammar</a> · <a href="'+p.events.name+'">actual checkpoints</a> · <a href="'+p.responses.name+'">derived interfaces</a>.';pointPicture(p);nativePicture(p);window.MathJax?.typesetPromise?.([el('reading'),el('input'),el('output')]).catch(e=>el('load').textContent=e.message);
 }
 function show(){
  const p=view.proofs[chosen],c=view.cases.find(a=>a.id===p.case);index=p.lines.length-1;el('theorem').innerHTML='<div class="formula">'+math(p.request.target)+'</div><p>'+esc(c.scope)+'</p>';el('premises').innerHTML=Object.entries(p.request.theory.axioms).map(([n,a])=>'<p><code>'+esc(n)+'</code> '+math(a)+'</p>').join('')||'<p>No input axioms.</p>';el('lines').innerHTML=p.request.proof.map((cmd,j)=>'<div class="proof-line"><span>Line '+(j+1)+'</span><div class="formula">'+math(cmd.formula)+'</div><p>'+esc(english(cmd))+'</p></div>').join('');el('proof-line-control').innerHTML=p.lines.map((l,j)=>'<option value="'+j+'">Line '+(j+1)+' · '+l.label.rule+'</option>').join('');el('proof-line-control').value=String(index);nodes=[];const collect=(t,path)=>{nodes.push({tree:t,path});t.children.forEach(c=>collect(c.tree,[...path,c.key]));};collect(p.trace.search.tree,[]);el('node-control').innerHTML=nodes.map((n,j)=>'<option value="'+j+'">Node '+(j+1)+' · '+n.tree.kind+' · '+n.path.length+' placements</option>').join('');showNode();read();window.MathJax?.typesetPromise?.([el('theorem'),el('premises'),el('lines')]).catch(e=>el('load').textContent=e.message);
 }
 async function boot(){try{
  const r=await fetch('native-receptor-points-reader-001.json?v=20261010-nrp1');if(!r.ok)throw Error('HTTP '+r.status);view=await r.json();const checked=validateReceptors(view);el('load').textContent='Independent audit passed · '+checked.proofs+' discovered proofs · '+checked.lines+' native proof lines · '+view.audit.point_nodes+' complete point nodes · '+checked.queries+' replayed native queries';el('case').innerHTML=view.proofs.map((p,j)=>'<option value="'+j+'">'+esc(view.cases.find(c=>c.id===p.case).title)+'</option>').join('');el('case').value=String(chosen);
  el('results').innerHTML=view.observations.map(o=>'<tr><td>'+esc(o.case)+'</td><td>'+(o.mode==='points'?'GCTS points':'Native prefix')+'</td><td>'+o.status.replaceAll('_',' ')+'</td><td>'+o.queries+'</td><td>'+(o.mode==='points'&&o.metrics?(o.metrics.attempts??0):'—')+'</td><td>'+o.cold_seconds.toFixed(3)+'</td><td>'+o.worker_stage_seconds.toFixed(3)+'</td><td><a href="'+o.artifact.name+'">Trace</a></td></tr>').join('');el('costs').textContent='Code compilation '+view.costs.compile_seconds.toFixed(3)+' s; full production and accepting certificate materialization '+view.costs.production_seconds.toFixed(3)+' s; independent audit '+view.costs.audit_seconds.toFixed(3)+' s.';
  const get=(id,mode)=>view.observations.find(o=>o.case===id&&o.mode===mode);el('comparison').textContent='For the three-line propositional task, GCTS used '+get('two-premise','points').queries+' native queries and '+get('two-premise','points').cold_seconds.toFixed(3)+' cold seconds; prefix checking used '+get('two-premise','prefix').queries+' queries and '+get('two-premise','prefix').cold_seconds.toFixed(3)+' seconds. The seven-line chain completed in '+get('chain-3','points').cold_seconds.toFixed(3)+' seconds; the prefix control remained unknown after '+get('chain-3','prefix').queries+' queries. Ground reflexivity was slower with the point catalog. Completion versus an unfinished control does not define a speed ratio.';
  const finite=view.audit.finite_equivalence.filter(a=>a.status.startsWith('all_words'));el('audit-details').textContent='The independent auditor checked all '+view.audit.point_nodes+' visited GCTS nodes, reran all '+view.audit.queries+' recorded native computations, and rejected '+view.audit.mutations+' altered bindings. For '+finite.length+' small envelopes it checked '+finite.reduce((n,a)=>n+a.words,0)+' complete original command words against a separate logical kernel.';
  el('case').addEventListener('change',()=>{chosen=Number(el('case').value);show();});el('proof-line-control').addEventListener('change',()=>{index=Number(el('proof-line-control').value);read();});el('layer').addEventListener('change',()=>pointPicture(view.proofs[chosen]));el('node-control').addEventListener('change',showNode);show();
 }catch(e){el('load').textContent='Validation failed: '+e.message;console.error(e);}}boot();
}
