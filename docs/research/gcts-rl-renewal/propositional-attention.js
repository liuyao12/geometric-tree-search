/* A checked view of an existing discovery, plus deliberately changed references.
   No search, trained attention model, or new proof is claimed by this viewer. */
(function(){'use strict';
const DATA_SHA='34b8f4315441f720cdb042b4f1bc610f1bbbb5040dda51b56462ea77ff763b3e';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const need=(p,s)=>{if(!p)throw Error(s);};
const point=p=>p.join(',');
const imp=(a,b)=>['imp',a,b];
function word(a){
  need(Array.isArray(a),'Formula array');
  if(a.length===1&&['P','Q'].includes(a[0]))return a[0];
  if(a.length===2&&a[0]==='not')return 'n'+word(a[1]);
  if(a.length===3&&a[0]==='imp')return 'i'+word(a[1])+word(a[2]);
  throw Error('Formula outside the declared alphabet');
}
function tex(a){word(a);return a.length===1?a[0]:a[0]==='not'?'\\neg ('+tex(a[1])+')':'('+tex(a[1])+' \\Rightarrow '+tex(a[2])+')';}
function marks(j,a){return [[[2*j,1],0],...[...word(a)+'e'].map((v,r)=>[[2*j,2+r],v])];}
function compile(j,rule,refs){
  need(refs.length===rule.inputs.length&&refs.every(r=>Number.isInteger(r)&&r>=0&&r<j),'Earlier references');
  const map=new Map(),internal=[];
  for(const [slot,a] of [[j,rule.output],...refs.map((r,i)=>[r,rule.inputs[i]])])for(const [p,v] of marks(slot,a)){
    const k=point(p);if(map.has(k)&&map.get(k)[1]!==v)internal.push({point:p,first:map.get(k)[1],second:v});
    else map.set(k,[p,v]);
  }
  return {occupancy:[[[2*j,0],12]],marks:[...map.values()].sort((a,b)=>a[0][0]-b[0][0]||a[0][1]-b[0][1]),internal};
}
function schema(kind,a){
  try{
    if(kind==='H1')return a[0]==='imp'&&a[2][0]==='imp'&&same(a[1],a[2][2]);
    if(kind==='H2'){const [x,y]=[a[1],a[2]],A=x[1],B=x[2][1],C=x[2][2];return same(a,imp(imp(A,imp(B,C)),imp(imp(A,B),imp(A,C))));}
    if(kind==='H3'){const [A,B]=a[2].slice(1);return same(a,imp(imp(['not',B],['not',A]),imp(A,B)));}
  }catch(e){return false;}return false;
}
function inspect(data){
  need(Array.isArray(data.authored_proofs)&&data.authored_proofs.length===0,'Discovery provenance');
  const c=data.cases.find(c=>c.id==='identity-P');need(c&&c.hypotheses.length===0&&c.length===5&&c.library===false,'Fixed primitive request');
  const r=c.runs.point;need(r.status==='finite_exact_proof_tiling'&&r.proof.length===5,'Existing successful discovery');
  const rules=data.basis.rules,tiles=[...r.point_tiles].sort((a,b)=>a.key[0]-b.key[0]);
  need(tiles.length===5&&r.placements.length===5&&new Set(r.placements.map(k=>JSON.stringify(k))).size===5,'Exact cell inventory');
  need(same(r.initial_marks,[...marks(4,c.target)].sort((a,b)=>a[0][0]-b[0][0]||a[0][1]-b[0][1])),'Requested boundary');
  const assigned=new Map(r.initial_marks.map(([p,v])=>[point(p),v]));let assignments=r.initial_marks.length;
  r.proof.forEach((row,j)=>{
    word(row.formula);const t=tiles[j];need(t.key[0]===j&&r.placements.some(k=>same(k,t.key)),'Used placement binding');
    const rule=rules[t.key[1]];need(rule&&row.kind===rule.kind&&same(row.formula,rule.output)&&same(row.refs,t.key[2]),'Ground rule binding');
    if(row.kind==='mp')need(row.refs.length===2&&row.refs.every(i=>Number.isInteger(i)&&i>=0&&i<j)&&same(r.proof[row.refs[1]].formula,imp(r.proof[row.refs[0]].formula,row.formula))&&same(rule.inputs,[r.proof[row.refs[0]].formula,r.proof[row.refs[1]].formula]),'Sound modus ponens');
    else need(!row.refs.length&&!rule.inputs.length&&schema(row.kind,row.formula),'Axiom schema');
    const expected=compile(j,rule,row.refs);need(!expected.internal.length&&same(expected.occupancy,t.occupancy)&&same(expected.marks,t.marks),'Complete actual point tile');
    for(const [p,v] of t.marks){const k=point(p);need(!assigned.has(k)||assigned.get(k)===v,'Exact global agreement');assigned.set(k,v);assignments++;}
  });
  need(same(r.proof[4].formula,c.target)&&same(r.proof[4].refs,[0,3]),'Actual final inference');
  const rule=rules[tiles[4].key[1]],A=rule.inputs[0],B=rule.output;
  need(rule.kind==='mp'&&same(rule.inputs[1],imp(A,B)),'Inference schema, not arbitrary equalities');
  return {case:c,result:r,tiles,rule,A,B,assignments};
}
function trial(view,reference){
  need(Number.isInteger(reference)&&reference>=0&&reference<4,'Reference selector');
  const tile=compile(4,view.rule,[reference,3]),prefix=new Map();
  for(const t of view.tiles.slice(0,4))for(const [p,v] of t.marks){const k=point(p);need(!prefix.has(k)||prefix.get(k)===v,'Checked prefix');prefix.set(k,v);}
  const conflicts=tile.marks.filter(([p,v])=>prefix.has(point(p))&&prefix.get(point(p))!==v).map(([p,v])=>({point:p,actual:prefix.get(point(p)),demanded:v}));
  return {reference,tile,conflicts,accepted:!tile.internal.length&&!conflicts.length,prefix};
}
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const math=s=>'\\('+s+'\\)';
function draw(view,test){
  const ports=[...new Set([test.reference,3,4])].sort((a,b)=>a-b),map=new Map(test.tile.marks.map(([p,v])=>[point(p),v]));
  const maxY=Math.max(...test.tile.marks.map(([p])=>p[1]),...ports.filter(j=>j<4).map(j=>word(view.result.proof[j].formula).length+2));
  const width=ports.length*220,height=(maxY+1)*21+85;
  let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+width+' '+height+'" role="img" aria-label="Exact source and requested values at the selected distant formula ports">';
  ports.forEach((j,column)=>{
    const x=110+220*column,output=j===4;
    svg+='<text x="'+x+'" y="17" text-anchor="middle" font-size="14" fill="#34443d">Line '+(j+1)+(output?' · conclusion':' · premise')+'</text>';
    svg+='<text x="'+(x-20)+'" y="39" text-anchor="middle" font-size="11">'+(output?'target':'source')+'</text><text x="'+(x+22)+'" y="39" text-anchor="middle" font-size="11">rule</text>';
    const actual=new Map(marks(j,output?view.B:view.result.proof[j].formula).map(([p,v])=>[point(p),v]));
    for(let y=1;y<=maxY;y++){
      const p=[2*j,y],k=point(p),av=actual.get(k),dv=map.get(k),bad=test.conflicts.some(c=>point(c.point)===k)||test.tile.internal.some(c=>point(c.point)===k);
      if(av===undefined&&dv===undefined)continue;
      svg+='<text x="'+(x-82)+'" y="'+(58+y*21)+'" font-family="monospace" font-size="10" fill="#637167">['+p.join(',')+']</text>';
      for(const [offset,value,isDemand] of [[-30,av,false],[10,dv,true]]){
        const fill=value===undefined?'#eef1ef':bad&&isDemand?'#b44565':y===1?'#995fa9':output?'#27866e':isDemand?'#347eb0':'#dce9f4';
        const ink=value===undefined||(!isDemand&&y!==1&&!output)?'#34443d':'white';
        svg+='<rect x="'+(x+offset)+'" y="'+(44+y*21)+'" width="26" height="19" rx="3" fill="'+fill+'"/><text x="'+(x+offset+13)+'" y="'+(58+y*21)+'" text-anchor="middle" font-family="monospace" font-size="12" fill="'+ink+'">'+esc(value===undefined?'*':value)+'</text>';
      }
    }
  });
  svg+='<text x="'+width/2+'" y="'+(height-12)+'" text-anchor="middle" font-size="11" fill="#637167">Bracketed pairs are literal point data; * means unassigned.</text></svg>';return svg;
}
async function start(){
  const $=id=>document.getElementById(id);if(!$('attention-reference'))return;
  try{
    const response=await fetch('propositional-receptors-001.json?v=20261010-pa1');need(response.ok,'Published discovery unavailable');
    const bytes=await response.arrayBuffer(),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');need(digest===DATA_SHA,'Exact discovery artifact hash');
    const data=JSON.parse(new TextDecoder().decode(bytes)),view=inspect(data);
    $('attention-proof').innerHTML=view.result.proof.map((r,j)=>'<div class="attention-proof-row"><b>Line '+(j+1)+'</b><span>'+math(tex(r.formula))+'</span><small>'+esc(r.kind==='mp'?'Modus ponens: lines '+r.refs.map(i=>i+1).join(', '):r.kind+' axiom')+'</small></div>').join('');
    $('attention-reference').innerHTML=view.result.proof.slice(0,4).map((r,j)=>'<option value="'+j+'">Line '+(j+1)+(j===0?' · actual discovered reference':' · changed reference')+'</option>').join('');
    $('attention-instance').innerHTML=math('A='+tex(view.A)+',\\qquad B='+tex(view.B));
    $('attention-provenance').textContent='Pinned existing discovery checked: all five primitive rules, backward references, actual tiles, boundary, occupancy and marking agreement. No new search or attention training is performed by this view.';
    async function render(){
      const test=trial(view,Number($('attention-reference').value));$('attention-diagram').innerHTML=draw(view,test);
      $('attention-verdict').className='attention-verdict '+(test.accepted?'accepted':'rejected');
      $('attention-verdict').textContent=test.accepted?'Compatible: this is the actual final inference.':test.tile.internal.length?'Rejected before placement: two premises demand different values at the same point.':'Rejected: the referenced formula disagrees with the rule’s distant marking.';
      const bad=test.tile.internal[0]||test.conflicts[0];
      $('attention-conflict').innerHTML=bad?'First conflict at '+math('('+bad.point.join(',')+')')+': <code>'+esc(test.tile.internal.length?bad.first:bad.actual)+'</code> and <code>'+esc(test.tile.internal.length?bad.second:bad.demanded)+'</code>.':'The final tile has positive occupancy only at '+math('(8,0)')+'; its premise ports are '+math('(0,r)')+' and '+math('(6,r)')+'. Each assigned character and scope value agrees.';
      $('attention-exact').textContent=JSON.stringify({changed_reference:test.reference,key:[4,view.tiles[4].key[1],[test.reference,3]],occupancy:test.tile.occupancy,marks:test.tile.marks,internal_conflicts:test.tile.internal,conflicts_with_prefix:test.conflicts},null,2);
      if(window.MathJax?.startup?.promise){await MathJax.startup.promise;MathJax.typesetClear?.([$ ('attention-conflict')]);await MathJax.typesetPromise([$ ('attention-conflict')]);}
    }
    $('attention-reference').addEventListener('change',()=>render().catch(e=>{$('attention-verdict').textContent=e.message;}));await render();
    if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise([$ ('attention-proof'),$ ('attention-instance')]);}
    $('attention-panel').setAttribute('aria-busy','false');
  }catch(e){$('attention-provenance').textContent='Unable to validate the reference view: '+e.message;$('attention-panel').setAttribute('data-error','true');$('attention-panel').setAttribute('aria-busy','false');}
}
if(typeof module!=='undefined')module.exports={DATA_SHA,word,tex,marks,compile,inspect,trial};else start();
})();
