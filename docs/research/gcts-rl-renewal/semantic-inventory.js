'use strict';
const stable=x=>Array.isArray(x)?x.map(stable):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])])):x;
const packed=x=>JSON.stringify(stable(x)),eq=(a,b)=>packed(a)===packed(b),key=p=>p.join(','),close=(a,b)=>Math.abs(a-b)<1e-11;
function formula(a){
 const f=formula,k=a[0],name=s=>String(s).replace(/[^A-Za-z0-9]/g,'');
 if(k==='meta')return 'X_{'+(a[1]+1)+'}';if(k==='var')return name(a[1]);if(k==='bot')return '\\bot';
 if(k==='fun'){if(a[1]==='zero')return '0';if(a[1]==='succ')return 'S('+f(a[2][0])+')';if(!a[2].length)return a[1]==='l'?'\\ell':name(a[1]);if(['add','mul'].includes(a[1]))return '('+f(a[2][0])+(a[1]==='add'?'+':'\\cdot ')+f(a[2][1])+')';return '\\operatorname{'+name(a[1])+'}('+a[2].map(f).join(',')+')';}
 if(k==='pred')return '\\operatorname{'+name(a[1])+'}'+(a[2].length?'('+a[2].map(f).join(',')+')':'');
 if(k==='eq')return f(a[1])+'='+f(a[2]);if(k==='all')return '\\forall '+name(a[1])+'\\;('+f(a[2])+')';
 if(k==='not')return '\\neg('+f(a[1])+')';if(['imp','and','or'].includes(k))return '('+f(a[1])+{imp:'\\Rightarrow ',and:'\\land ',or:'\\lor '}[k]+f(a[2])+')';
 throw Error('Unknown formula syntax');
}
const references=c=>c.rule==='mp'?[c.antecedent,c.implication]:c.rule==='generalize'?[c.source]:c.rule==='block'?c.inputs:[];
function coreOutput(v,triple){
 const A=v.inventory.symbols,Q=v.inventory.states;
 const decode=s=>{if(!Number.isInteger(s)||s<0||s>=A*(Q+1))throw Error('Bad symbol');return s<A?null:[Math.floor((s-A)/A),(s-A)%A];};
 const h=triple.map(decode),b=triple[1];if(h.filter(Boolean).length>1)throw Error('Multiple heads');
 const delta=x=>{const r=v.transition_rows[x[0]];if(!r)throw Error('Unbound native transition');return r[x[1]];};
 if(h[1]){if(h[1][0]===v.inventory.accept)return b;const a=delta(h[1]);if(!a)throw Error('Missing native action');return a[2]===0?A+A*a[0]+a[1]:a[1];}
 for(const [i,d] of [[0,1],[2,-1]])if(h[i]&&h[i][0]!==v.inventory.accept){const a=delta(h[i]);if(a&&a[2]===d)return A+A*a[0]+b;}
 return b;
}
function free(a,bound=new Set()){
 if(a[0]==='var')return bound.has(a[1])?[]:[a[1]];
 if(a[0]==='all')return free(a[2],new Set([...bound,a[1]]));
 if(['fun','pred'].includes(a[0]))return a[2].flatMap(x=>free(x,bound));
 if(['eq','imp','and','or'].includes(a[0]))return [...free(a[1],bound),...free(a[2],bound)];
 return a[0]==='not'?free(a[1],bound):[];
}
function validateTraining(v){
 const t=v.training;if(t.episodes.length!==24||t.rate!==.4||!eq(t.features,v.policy.features))throw Error('Training protocol changed');
 let weights=Array(10).fill(0),baseline=0,events=0,episodeIndex=0;
 const sameWeights=(a,b)=>Array.isArray(a)&&a.length===10&&a.every((w,k)=>close(w,b[k]));
 for(const e of t.episodes){
  if(e.id!==episodeIndex++||!sameWeights(e.weights_before,weights)||(e.id===0&&!eq(e.weights_before,Array(10).fill(0)))||e.search.seed!==63000+e.id||!e.search.stochastic)throw Error('Fresh zero-start episode changed');
  const gradient=Array(10).fill(0);
  for(const a of e.search.events){
   if(!sameWeights(a.weights,weights)||a.items.length!==a.features.length||a.items.length!==a.probabilities.length)throw Error('Episode pool changed');
   const scores=a.features.map(phi=>phi.reduce((n,x,k)=>n+x*weights[k],0)),top=Math.max(...scores),raw=scores.map(x=>Math.exp(x-top)),sum=raw.reduce((a,b)=>a+b,0),prob=raw.map(x=>x/sum);
   if(!scores.every((s,j)=>close(s,a.scores[j]))||!prob.every((p,j)=>close(p,a.probabilities[j])))throw Error('Actual softmax changed');
   let at=prob.length-1,cumulative=0;if(!(a.uniform>=0&&a.uniform<1))throw Error('Missing stochastic draw');for(let j=0;j<prob.length;j++){cumulative+=prob[j];if(a.uniform<cumulative){at=j;break;}}
   if(a.index!==at)throw Error('Sampled action changed');
   gradient.forEach((_,k)=>gradient[k]+=a.features[at][k]-prob.reduce((s,p,j)=>s+p*a.features[j][k],0));events++;
  }
  gradient.forEach((g,k)=>gradient[k]=g/Math.max(1,e.search.events.length));
  const work=(e.search.metrics.validation_checks??0)+(e.search.metrics.sample_pair_tests??0),growth=e.accepted?(2+e.arity)*e.search.proof.length:0;
  const reward=growth/Math.max(1,e.search.metrics.attempts??0)-.25*Math.min(1,work/100000),advantage=reward-baseline;
  if(!close(reward,e.learning.reward)||!close(baseline,e.learning.baseline_before)||!close(advantage,e.learning.advantage)||!gradient.every((g,k)=>close(g,e.learning.gradient[k])))throw Error('Gradient or reward changed');
  weights=weights.map((w,k)=>w+.4*advantage*gradient[k]);baseline=.9*baseline+.1*reward;
  if(!weights.every((w,k)=>close(w,e.weights_after[k]))||!close(baseline,e.baseline_after))throw Error('Actual update changed');
 }
 if(!weights.every((w,k)=>close(w,t.weights[k])&&close(w,v.policy.weights[k])&&close(w,v.audit.training.weights[k]))||!close(baseline,t.baseline))throw Error('Frozen policy changed');
 return events;
}
function validatePointProjection(p){
 const t=p.trace,marks=new Map(),totals=new Map(),seen=new Set(),roots=new Set(t.roots.map(key));
 for(const c of t.selected){if(seen.has(key(c.key)))throw Error('Repeated selected tile');seen.add(key(c.key));for(const [point,value] of c.occupancy){const q=key(point);if(!roots.has(q)||value!==12)throw Error('Unit root changed');totals.set(q,(totals.get(q)??0)+value);}for(const [point,value] of c.marks){const q=key(point);if(marks.has(q)&&marks.get(q)!==value)throw Error('Selected marking disagreement');marks.set(q,value);}}
 if(totals.size!==roots.size||[...totals.values()].some(v=>v!==12)||!eq([...seen].sort(),t.placements.map(key).sort()))throw Error('Entire selected rectangle changed');
 const port=(j,value,ch='formula')=>[...new TextEncoder().encode(packed(value)),256].map((v,i)=>[[4*j+Number(ch==='command'),100+i],v]);
 for(let j=0;j<t.proof.length;j++){
  const cs=t.selected.filter(c=>c.key[0]===j),C=cs.find(c=>c.key[1]===0),G=cs.find(c=>c.key[1]===1),cmd=t.proof[j],skeleton={...cmd};delete skeleton.inputs;
  if(!C||!G||!eq(C.command,skeleton)||!eq(G.command,skeleton))throw Error('Point command/guard binding changed');
  for(const [point,value] of [...port(j,skeleton,'command'),...port(j,cmd.formula)])if(marks.get(key(point))!==value)throw Error('Full formula or command word changed');
  const requirements=G.requirements.concat(cs.filter(c=>c.kind==='lemma_input').flatMap(c=>c.requirements));
  requirements.forEach(([i,f])=>{if(!(i>=0&&i<j)||!eq(f,t.proof[i].formula))throw Error('Distant earlier formula changed');for(const [point,value] of port(i,f))if(marks.get(key(point))!==value)throw Error('Full distant formula word changed');});
  if(cmd.rule==='block'){
   const def=t.inventory.definitions.find(d=>d.name===cmd.name);if(!def||!eq(def.definition.conclusion,cmd.formula)||!eq(cs.filter(c=>c.kind==='lemma_input').sort((a,b)=>a.input-b.input).map(c=>c.source),cmd.inputs))throw Error('Actual lemma input factors changed');
   if(!eq(cmd.inputs.map(i=>t.proof[i].formula),def.definition.premises))throw Error('Lemma premise agreement changed');
  }
 }
}
function validateView(v){
 if(v.version!=='semantic-inventory-reader-001'||v.audit.status!=='passed'||v.inventory.fingerprint!=='0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455'||v.inventory.symbols!==60||v.inventory.states!==462276)throw Error('Fixed palette/audit changed');
 if(v.cases.length!==8||v.donors.length!==3||v.policy.library.length!==4||v.observations.length!==96||v.proofs.length!==9)throw Error('Coverage changed');
 const coverage=new Set(v.observations.map(o=>[o.case,o.mode,o.repetition].join(':')));if(coverage.size!==96)throw Error('Repeated observation');
 if(v.first_decisions.length!==4)throw Error('First-decision coverage changed');
 for(const name of ['renamed-five','renamed-six']){
  const pair=['fixed','learned'].map(mode=>v.first_decisions.find(d=>d.case===name&&d.mode===mode));
  if(pair.some(d=>!d)||!eq(pair[0].event.chosen,pair[1].event.chosen)||!eq(pair[0].event.point,pair[1].event.point)||!eq(pair[0].event.items,pair[1].event.items))throw Error('Same-boundary contrast changed');
  pair.forEach((d,k)=>{
   const a=d.event,w=k?v.policy.weights:[.7,.3,1.,.8,.2,-.1,.2,.2,.4,0.],scores=a.features.map(phi=>phi.reduce((s,x,j)=>s+x*w[j],0));
   if(!eq(a.weights,w)||!scores.every((s,j)=>close(s,a.scores[j]))||a.index!==scores.reduce((best,s,j)=>s>scores[best]?j:best,0)||a.items[a.index].kind!==(k?'sampled':'primitive')||a.features[a.index][7]!==Number(!k))throw Error('First selected ordering changed');
  });
 }
 let count=0;
 for(const p of v.proofs){
  const assertion=[...v.cases,...v.donors,v.promotion].find(c=>c.id===p.case);
  if(!assertion||!eq(assertion.theory,p.request.theory)||!eq(assertion.target,p.request.target)||p.request.proof.length!==assertion.length)throw Error('Input assertion changed');
  for(const k of ['micro_steps','physical_steps'])if(String(p.builder[k])!==String(p.literal[k])||String(p.builder[k])!==String(p.checker[k]))throw Error('Full native expansion changed');
  if(p.builder.status!=='accepted'||p.literal.status!=='accepted'||p.checker.result!=='accepted'||p.trace.status!=='native_proof_discovered'||!eq(p.trace.proof,p.request.proof)||!eq(p.trace.verification.request,p.request)||p.trace.verification.result.status!=='accepted'||p.trace.verification.result.start!==88986)throw Error('Whole native acceptance changed');
  validatePointProjection(p);
  const scopes=[...p.request.blocks.map(b=>({name:b.name,target:b.conclusion,premises:b.premises,proof:b.proof})),{name:'root',target:p.request.target,premises:[],proof:p.request.proof}];let position=0,registry=[];
  for(const scope of scopes){
   const forbidden=[...new Set(scope.premises.flatMap(a=>free(a)))].sort();
   scope.proof.forEach((cmd,j)=>{
    const l=p.lines[position++];count++;if(!l||l.outcome!=='line-checked'||l.label.scope!==scope.name||l.label.line!==j||l.label.rule!==cmd.rule||!eq(l.label.formula,cmd.formula))throw Error('Native line label changed');
    for(const [ctx,n] of [[l.input,j],[l.output,j+1]])if(!ctx||!eq(ctx.target,scope.target)||!eq(ctx.theory,p.request.theory)||!eq(ctx.assumptions,scope.premises)||!eq(ctx.registry,registry)||!eq([...ctx.forbidden].sort(),forbidden)||!eq(ctx.proved,scope.proof.slice(0,n).map(c=>c.formula))||!eq(ctx.pending,scope.proof.slice(n)))throw Error('Native local/root context changed');
    if(references(cmd).some(i=>!Number.isInteger(i)||i<0||i>=j))throw Error('Circular proof reference');
    if(l.q!==1688||l.out!==1688||l.micro_steps<=0||l.physical_height<=0)throw Error('Actual line receptor changed');
    const patch=l.patch;if(patch.width!==9||patch.height!==3||patch.rows.length!==4||patch.tiles.length!==27||patch.trajectory[0][0]!==6746||patch.prefix_physical_steps!==l.input_head+patch.marker+1||patch.prefix_physical_steps+3>l.physical_height)throw Error('Native entry crop changed');
    const seen=new Set();for(const tile of patch.tiles){const at=tile.x+','+tile.y,triple=patch.rows[tile.y].slice(tile.x,tile.x+3),n=coreOutput(v,triple);if(seen.has(at)||tile.x<0||tile.x>=9||tile.y<0||tile.y>=3||!eq(tile.triple,triple)||tile.identity!==triple.join(':')||tile.S!==triple[1]||tile.N!==n||n!==patch.rows[tile.y+1][tile.x+1]||!eq(tile.W,triple.slice(0,2))||!eq(tile.E,triple.slice(1)))throw Error('Native square seam changed');seen.add(at);}
   });
   if(scope.name!=='root')registry.unshift({name:scope.name,premises:scope.premises,conclusion:scope.target});
  }
  if(position!==p.lines.length)throw Error('Extra native lines');
 }
 const events=validateTraining(v);return {proofs:v.proofs.length,lines:count,tiles:27*count,training_events:events,observations:96};
}
async function validatePins(v){
 const cryptoObject=typeof window!=='undefined'?window.crypto:require('crypto').webcrypto;
 const digest=async x=>Array.from(new Uint8Array(await cryptoObject.subtle.digest('SHA-256',new TextEncoder().encode(packed(x))))).map(x=>x.toString(16).padStart(2,'0')).join('');
 for(const p of v.proofs)if(await digest(p.request)!==p.request_sha256||p.trace.verification.request_sha256!==p.request_sha256)throw Error('Full request pin changed');
 for(const family of v.policy.library)if(await digest({parameters:family.parameters,template:family.template})!==family.id)throw Error('Family identity changed');
 if(v.policy.training.sha256!==v.training_sha256)throw Error('Training provenance changed');
}
if(typeof module!=='undefined')module.exports={validateView,validateTraining,validatePointProjection,validatePins,coreOutput,formula};
if(typeof document!=='undefined'){
 const el=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),math=a=>'\\('+formula(a)+'\\)';let view,chosen=4,scope='root',index=0;
 const type=()=>window.MathJax?.typesetPromise?.().catch(e=>el('load').textContent=e.message);
 const current=()=>view.proofs[chosen],scoped=p=>scope==='root'?{name:'root',premises:[],conclusion:p.request.target,proof:p.request.proof}:p.request.blocks.find(b=>b.name===scope);
 const alias=(p,name)=>name==='root'?'Root proof':'Lemma '+(p.request.blocks.findIndex(b=>b.name===name)+1);
 const english=(p,c)=>{
  if(c.rule==='axiom')return 'Use the given theory premise “'+c.name+'”.';
  if(c.rule==='assumption')return 'Use local hypothesis '+(c.index+1)+'.';
  if(c.rule==='mp')return 'Line '+(c.antecedent+1)+' establishes the antecedent. Apply the implication on line '+(c.implication+1)+' to obtain this conclusion.';
  if(c.rule==='generalize')return 'Quantify '+c.variable+' universally in the result on line '+(c.source+1)+'. The variable is absent from all open local hypotheses.';
  if(c.rule==='refl')return 'A term equals itself.';
  if(c.rule==='tautology')return 'This is a checked propositional tautology.';
  if(c.rule==='block')return 'Apply '+alias(p,c.name).toLowerCase()+' to earlier '+(c.inputs.length===1?'line ':'lines ')+c.inputs.map(i=>i+1).join(', ')+'. Each formula matches the ordered interface premise.';
  throw Error('Unknown discovered rule');
 };
 function pointPicture(p){
  if(scope!=='root'){el('point-picture').innerHTML='';el('point-caption').textContent='This is a native local lemma proof. The root point search chooses the call; its local body is checked by the Wang machine below. It was not separately searched in this ground specialization.';el('marks').textContent='';return;}
  const cs=p.trace.selected.filter(c=>c.slot===index),w=560,s=70;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 240" role="img" aria-label="Selected command, guard and premise reference point tiles with colored marking layers">';
  cs.sort((a,b)=>a.key[1]-b.key[1]).forEach((c,i)=>{const x=12+i*s;svg+='<rect x="'+x+'" y="15" width="60" height="60" fill="#f2eff5" stroke="#acb9ad"/><rect x="'+(x+2)+'" y="17" width="56" height="6" fill="'+(c.key[1]<2?'#b98528':'#368c91')+'"/><rect x="'+(x+2)+'" y="67" width="56" height="6" fill="'+(c.key[1]<2?'#8654a0':'#357bad')+'"/><circle cx="'+(x+30)+'" cy="45" r="4" fill="#23856b"/><text x="'+(x+30)+'" y="36" text-anchor="middle" font-size="11">'+(c.key[1]===0?'C':c.key[1]===1?'G':'B'+(c.input+1))+'</text><text x="'+(x+30)+'" y="59" text-anchor="middle" font-size="9">'+(c.kind==='lemma_input'?'Line '+(c.source+1):c.kind==='unused_input'?'inactive':c.command.rule)+'</text>';});
  const requirements=cs.flatMap(c=>c.requirements),unique=[...new Map(requirements.map(([i,f])=>[i,{i,f}])).values()];
  unique.forEach(({i,f},r)=>{const bytes=[...new TextEncoder().encode(packed(f)),256],y=104+r*24;svg+='<text x="12" y="'+(y+9)+'" font-size="11">Line '+(i+1)+'</text>';bytes.forEach((v,k)=>{const x=85+k*4;if(x<w-8)svg+='<rect x="'+x+'" y="'+y+'" width="3" height="10" fill="hsl('+(275+v%25)+' 55% '+(36+v%20)+'%)"/>';});svg+='<path d="M 77 '+(y+5)+' V 84 H '+(152+r*s)+' V 77" fill="none" stroke="#8654a0" stroke-width="2"/>';});
  el('point-picture').innerHTML=svg+'</svg>';el('point-caption').textContent=cs.length+' selected unit-occupancy placements at root line '+(index+1)+'. '+requirements.length+' distant full-formula requirements. The word strips draw each value when it fits; the exact complete assignments are below. Position and byte axes are compressed in this schematic.';
  el('marks').textContent=JSON.stringify(cs,null,2);
 }
 const nativeColor=(v,layer)=>{let n=0;for(const x of Array.isArray(v)?v:[v])n=(Math.imul(n,31)+x)>>>0;return 'hsl('+((layer==='vertical'?205:140)+n%30)+' 58% '+(38+n%24)+'%)';};
 function nativePicture(line){const p=line.patch,s=75,ox=38,oy=22;let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+(ox+p.width*s+15)+' '+(oy+p.height*s+20)+'" role="img" aria-label="Actual primitive Wang squares at the selected native line entry"><text x="4" y="14" font-size="12">time ↑</text>';for(const t of p.tiles){const x=ox+t.x*s,y=oy+(p.height-1-t.y)*s;svg+='<rect class="native-tile" x="'+(x+1)+'" y="'+(y+1)+'" width="73" height="73" fill="'+(t.triple.some(v=>v>=60)?'#fff3d9':'#f8faf5')+'" stroke="#acb9ad"/><rect x="'+(x+8)+'" y="'+(y+2)+'" width="59" height="7" fill="'+nativeColor(t.N,'vertical')+'"/><rect x="'+(x+8)+'" y="'+(y+66)+'" width="59" height="7" fill="'+nativeColor(t.S,'vertical')+'"/><rect x="'+(x+2)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.W,'horizontal')+'"/><rect x="'+(x+66)+'" y="'+(y+10)+'" width="7" height="55" fill="'+nativeColor(t.E,'horizontal')+'"/><text x="'+(x+37)+'" y="'+(y+29)+'" text-anchor="middle" font-size="9" font-family="monospace">N '+t.N+'</text><text x="'+(x+37)+'" y="'+(y+52)+'" text-anchor="middle" font-size="9" font-family="monospace">S '+t.S+'</text>';}el('literal').innerHTML=svg+'</svg>';}
 function read(){
  const p=current(),s=scoped(p),c=s.proof[index],line=p.lines.find(l=>l.label.scope===scope&&l.label.line===index);if(!line)throw Error('Missing native line');
  el('reading').innerHTML='<div class="formula">'+math(c.formula)+'</div><p>'+esc(english(p,c))+'</p>';
  if(c.rule==='block'){const def=p.request.blocks.find(b=>b.name===c.name);el('call-interface').innerHTML='<p>Ordered premises:</p>'+def.premises.map((a,j)=>'<p>Earlier line '+(c.inputs[j]+1)+' '+math(a)+'</p>').join('')+'<p>Conclusion '+math(def.conclusion)+'</p><button id="read-lemma-button">Read '+esc(alias(p,c.name))+'</button>';el('read-lemma-button').onclick=()=>{scope=c.name;el('scope-control').value=scope;showScope();};}else el('call-interface').innerHTML='';
  const context=ctx=>'<p>'+ctx.proved.length+' earlier checked facts; '+ctx.assumptions.length+' local hypotheses; '+ctx.registry.length+' registered lemmas.</p>'+ctx.proved.map(a=>'<div class="formula">'+math(a)+'</div>').join('');
  el('input-context').innerHTML=context(line.input);el('output-context').innerHTML='<p>Append the checked conclusion:</p><div class="formula">'+math(c.formula)+'</div><p>'+line.output.proved.length+' facts are now available.</p>';
  el('expansion').textContent='This native line has '+line.micro_steps.toLocaleString()+' selected-symbol steps and '+line.physical_height.toLocaleString()+' literal transitions. The full response checker derives them all; the picture shows the three-transition entry crop.';
  el('certificate-links').innerHTML='<a href="'+p.grammar.name+'">Whole response grammar</a> · <a href="'+p.events.name+'">Actual native checkpoints</a> · <a href="'+p.responses.name+'">Derived interfaces</a> · <a href="'+p.trace.source.name+'">Complete search evidence</a>.';
  document.querySelectorAll('.proof-line').forEach((row,j)=>row.classList.toggle('selected',j===index));pointPicture(p);nativePicture(line);type();
 }
 function showScope(){const p=current(),s=scoped(p);index=s.proof.length-1;el('theorem').innerHTML='<p>'+esc(alias(p,scope))+' conclusion:</p><div class="formula">'+math(s.conclusion)+'</div>';el('premises').innerHTML=(scope==='root'?Object.entries(p.request.theory.axioms).map(([name,a])=>'<p>Given “'+esc(name)+'” '+math(a)+'</p>').join(''):s.premises.map((a,j)=>'<p>Local hypothesis '+(j+1)+' '+math(a)+'</p>').join(''))||'<p>No input hypotheses in this scope.</p>';el('lines').innerHTML=s.proof.map((c,j)=>'<div class="proof-line"><span>Line '+(j+1)+' · '+esc(c.rule)+'</span><div class="formula">'+math(c.formula)+'</div><p>'+esc(english(p,c))+'</p></div>').join('');el('proof-line-control').innerHTML=s.proof.map((c,j)=>'<option value="'+j+'">Line '+(j+1)+' · '+c.rule+'</option>').join('');el('proof-line-control').value=String(index);read();}
 function show(){const p=current();scope='root';el('scope-control').innerHTML='<option value="root">Root proof</option>'+p.request.blocks.map((b,j)=>'<option value="'+b.name+'">Lemma '+(j+1)+' · '+b.proof.length+' lines</option>').join('');el('provenance').textContent=p.trace.case.scope+' Discovery: '+p.trace.mode+' ordering, '+(p.trace.metrics?.attempts??'solver')+' placements. Provenance: '+p.sources.join(', ')+'.';showScope();}
 function showFamily(){const j=Number(el('family-control').value),f=view.policy.library[j];el('family-interface').innerHTML='<p>Family '+(j+1)+' · '+f.parameters+' formula parameters</p>'+f.template.premises.map((a,i)=>'<p>Premise '+(i+1)+' '+math(a)+'</p>').join('')+'<div class="formula">Conclusion '+math(f.template.conclusion)+'</div>';el('family-lines').innerHTML=f.template.proof.map((c,i)=>'<p>Line '+(i+1)+' · '+c.rule+(c.call?' · call Family '+(view.policy.library.findIndex(d=>d.id===c.call.family)+1):'')+' '+math(c.formula)+'</p>').join('');el('family-origin').textContent='Discovered in '+f.provenance.case+', native query '+f.provenance.query+'. '+f.dependencies.length+' earlier family dependencies. Formula parameters change the interface; each actual specialization is checked in the native machine.';el('family-raw').textContent=JSON.stringify(f,null,2);let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 240" role="img" aria-label="Actual four-family dependency hierarchy">';view.policy.library.forEach((a,i)=>{const x=i===3?275:20,y=i===3?78:10+72*i;svg+='<rect x="'+x+'" y="'+y+'" width="135" height="48" fill="'+(i===j?'#eadcf2':'#f1f5ed')+'" stroke="#8654a0"/><text x="'+(x+67)+'" y="'+(y+20)+'" text-anchor="middle" font-size="12">Family '+(i+1)+'</text><text x="'+(x+67)+'" y="'+(y+37)+'" text-anchor="middle" font-size="10">'+a.template.proof.length+' body lines</text>';a.dependencies.forEach(id=>{const k=view.policy.library.findIndex(d=>d.id===id);svg+='<path d="M 155 '+(34+72*k)+' H '+x+'" stroke="#368c91" stroke-width="3"/>';});});el('hierarchy-picture').innerHTML=svg+'</svg>';type();}
 function showProposal(){const e=view.training.episodes[Number(el('episode-control').value)],a=e.search.events[Number(el('decision-control').value)],j=Number(el('proposal-control').value);if(!a){el('policy-probs').innerHTML='';el('proposal-raw').textContent='This episode required no policy decision.';return;}el('policy-probs').innerHTML=a.items.map((item,k)=>'<tr class="'+(k===a.index?'chosen':'')+'"><td>'+(k+1)+'</td><td>'+(item?item.kind:'defer')+'</td><td>'+(item?item.members.length:0)+'</td><td><span class="bar" style="width:'+Math.round(200*a.probabilities[k])+'px"></span>'+(100*a.probabilities[k]).toFixed(2)+'%</td><td>'+(k===a.index?'Chosen':'')+'</td></tr>').join('');el('proposal-raw').textContent=JSON.stringify({decision:a.id,chosen:a.index+1,proposal:j+1,item:a.items[j],features:Object.fromEntries(view.policy.features.map((n,k)=>[n,a.features[j][k]])),probability:a.probabilities[j],uniform:a.uniform},null,2);}
 function showDecision(){const e=view.training.episodes[Number(el('episode-control').value)],a=e.search.events[Number(el('decision-control').value)];el('proposal-control').innerHTML=a?a.items.map((item,j)=>'<option value="'+j+'">'+(j+1)+' · '+(item?item.kind:'Defer')+(j===a.index?' · chosen':'')+'</option>').join(''):'<option value="">No proposal</option>';if(a)el('proposal-control').value=String(a.index);showProposal();}
 function showEpisode(){const e=view.training.episodes[Number(el('episode-control').value)];el('episode-summary').textContent='Episode '+(e.id+1)+' · '+e.case+' · '+(e.accepted?'native accepted':'unfinished')+' · '+(e.search.metrics.attempts??0)+' placements · '+e.search.events.length+' sampled decisions · reward '+e.learning.reward.toFixed(6)+'. '+(e.cached_native_acceptance?'Exact training acceptance was reused.':'Native feedback was freshly executed.');el('decision-control').innerHTML=e.search.events.map((a,j)=>'<option value="'+j+'">Decision '+(j+1)+' · '+a.chosen.length+' prior placements</option>').join('')||'<option value="">No policy decision</option>';el('weights-table').innerHTML=view.policy.features.map((n,k)=>'<tr><td><code>'+esc(n)+'</code></td><td>'+e.weights_before[k].toFixed(6)+'</td><td>'+e.learning.gradient[k].toFixed(6)+'</td><td>'+e.weights_after[k].toFixed(6)+'</td></tr>').join('');showDecision();}
 function extras(){
  el('family-control').innerHTML=view.policy.library.map((f,j)=>'<option value="'+j+'">Family '+(j+1)+' · '+f.parameters+' formula parameters</option>').join('');el('family-control').value='3';showFamily();
  el('episode-control').innerHTML=view.training.episodes.map((e,j)=>'<option value="'+j+'">Episode '+(j+1)+' · '+esc(e.case)+'</option>').join('');showEpisode();
  const es=view.training.episodes,max=Math.max(...es.map(e=>e.search.metrics.attempts??0));let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 220" role="img" aria-label="Actual placement attempts in all twenty-four training episodes"><text x="40" y="16" font-size="12">Original placement attempts · all episodes native accepted</text><path d="M 40 28 V 180 H 820" fill="none" stroke="#b5c0ad"/>';es.forEach((e,j)=>{const h=140*(e.search.metrics.attempts??0)/max,x=45+j*32;svg+='<rect x="'+x+'" y="'+(180-h)+'" width="22" height="'+h+'" fill="#8654a0"/><text x="'+(x+11)+'" y="199" text-anchor="middle" font-size="9">'+(j+1)+'</text>';});el('training-picture').innerHTML=svg+'</svg>';
  const median=ns=>{const s=ns.sort((a,b)=>a-b);return (s[0]+s[1])/2;},methods=['base','zero','fixed','learned','no-family','z3'];
  el('medians').innerHTML=view.cases.flatMap(c=>methods.map(m=>{const os=view.observations.filter(o=>o.case===c.id&&o.mode===m);return '<tr><td>'+esc(c.id)+'</td><td>'+m+'</td><td>'+esc([...new Set(os.map(o=>o.status))].join(' / '))+'</td><td>'+os.map(o=>o.metrics?.attempts??'—').join(' / ')+'</td><td>'+median(os.map(o=>o.cold_seconds)).toFixed(3)+'</td></tr>';})).join('');
  el('observations').innerHTML=view.observations.map(o=>'<tr><td>'+esc(o.case)+'</td><td>'+o.mode+' / '+o.repetition+'</td><td>'+esc(o.status)+'</td><td>'+o.queries+'</td><td>'+o.cold_seconds.toFixed(3)+'</td><td><a href="'+o.artifact.name+'">Full raw record</a></td></tr>').join('');
  el('first-choices').innerHTML=view.first_decisions.map(d=>{const a=d.event,item=a.items[a.index];return '<tr><td>'+esc(d.case)+'</td><td>'+d.mode+'</td><td>'+(item?item.kind:'defer')+'</td><td>'+a.features[a.index][7]+'</td><td>'+(item?item.members.length:0)+'</td><td>'+a.scores[a.index].toFixed(6)+'</td></tr>';}).join('');
  el('comparison').textContent='Fixed ordering discovers the five-link and six-link proofs. Learned ordering reaches 5,000 placements in both repeats of both cases. Z3 also finds both. The small symbolic and equality cases demonstrate correctness and reuse, not a learned performance advantage.';
  el('training-costs').textContent='Fresh discovery and registration: '+view.training.discovery_seconds.toFixed(3)+' s. Training rollouts and feedback: '+view.training.training_seconds.toFixed(3)+' s. Full training worker: '+view.costs.training_stage_seconds.toFixed(3)+' s; '+view.training.queries+' native queries.';
  el('costs').textContent='Compilation '+view.costs.compile_seconds.toFixed(3)+' s; complete production including native materialization '+view.costs.production_seconds.toFixed(3)+' s; independent audit '+view.costs.audit_seconds.toFixed(3)+' s.';
  const a=view.audit;el('audit-details').textContent='Passed independent audit: '+a.queries+' native queries, '+a.point_nodes.toLocaleString()+' visited point nodes, '+a.policy_events.toLocaleString()+' policy decisions and '+a.hints.toLocaleString()+' hints. '+a.mutations+' corruptions rejected. Complete finite differential check: '+a.finite_equivalence.words.toLocaleString()+' command words, '+a.finite_equivalence.accepted+' accepted exact regions. All '+view.proofs.length+' displayed certificates include local and root native derivations.';
 }
 el('assertion-control').onchange=()=>{chosen=Number(el('assertion-control').value);show();};el('scope-control').onchange=()=>{scope=el('scope-control').value;showScope();};el('proof-line-control').onchange=()=>{index=Number(el('proof-line-control').value);read();};el('family-control').onchange=showFamily;el('episode-control').onchange=showEpisode;el('decision-control').onchange=showDecision;el('proposal-control').onchange=showProposal;
 fetch('semantic-inventory-reader-001.json?v=20261011-si1').then(r=>{if(!r.ok)throw Error('Reader data unavailable');return r.json();}).then(async v=>{const checked=validateView(v);await validatePins(v);view=v;el('load').textContent='Verified reader projection: '+checked.proofs+' proofs, '+checked.lines+' native lines, '+checked.tiles+' actual Wang squares, 24 fresh episodes and 96 observations.';el('assertion-control').innerHTML=v.proofs.map((p,j)=>'<option value="'+j+'">'+(p.role==='frozen_evaluation'?'Held out · ':'Donor · ')+esc(p.case)+'</option>').join('');el('assertion-control').value=String(chosen);show();extras();}).catch(e=>el('load').textContent='Reader validation stopped: '+e.message);
}
