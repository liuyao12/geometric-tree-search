/* Saved evidence only. This reader runs no proof search or checker. */
'use strict';
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const math=s=>el('span','\\('+s+'\\)','math');
const safe=s=>String(s).replace(/[^a-zA-Z0-9]/g,'');
function term(a){
  if(a[0]==='var')return '\\mathit{'+safe(a[1])+'}';
  if(a[0]==='fun')return '\\operatorname{'+safe(a[1])+'}'+(a[2].length?'('+a[2].map(term).join(',')+')':'');
  throw Error('Unsupported term constructor');
}
function formula(a){
  if(a[0]==='pred')return '\\operatorname{'+safe(a[1])+'}('+a[2].map(term).join(',')+')';
  if(a[0]==='eq')return term(a[1])+'='+term(a[2]);
  if(a[0]==='not')return '\\neg('+formula(a[1])+')';
  if(['and','or','imp'].includes(a[0]))return '('+formula(a[1])+({and:'\\land',or:'\\lor',imp:'\\to'}[a[0]])+formula(a[2])+')';
  if(['all','exists'].includes(a[0]))return (a[0]==='all'?'\\forall':'\\exists')+'\\mathit{'+safe(a[1])+'}\\,('+formula(a[2])+')';
  throw Error('Unsupported formula constructor');
}
function explanation(row){
  const refs=row.refs,p=el('p');
  if(row.rule==='assumption')p.append('Retain original hypothesis ',math(String(row.command.index)),'.');
  else if(row.rule==='axiom')p.append('Introduce the declared theory axiom.');
  else if(row.rule==='instantiate')p.append('Introduce this universal-instantiation implication. The next application still requires modus ponens.');
  else if(row.rule==='eq_subst')p.append('Introduce this equality-substitution instance.');
  else if(row.rule==='mp')p.append('Apply modus ponens: row ',math(String(refs[0])),' supplies the antecedent and row ',math(String(refs[1])),' supplies the implication.');
  else p.append('Read the exact primitive command below.');
  return p;
}
function layers(){
  document.querySelectorAll('.blue-layer').forEach(e=>e.hidden=!document.querySelector('#blue').checked);
  document.querySelectorAll('.purple-layer').forEach(e=>e.hidden=!document.querySelector('#purple').checked);
}
async function start(){
  const response=await fetch('visual-data.json');if(!response.ok)throw Error('Saved proof data unavailable');
  const saved=await response.json(),box=document.querySelector('#proof-view');
  box.dataset.proofStatus=saved.acceptance;
  for(const row of saved.rows){
    const line=el('div',undefined,'tile-line');line.id='proof-row-'+String(row.row);
    const square=el('div',undefined,'square');square.append(math('t(0,'+row.row+')=1'));
    const blue=el('div',undefined,'blue-layer');
    blue.append(math('m(1,'+row.row+')='+row.code));
    row.refs.forEach((ref,i)=>{const mark=el('div');mark.append(math('m(1,'+ref+')='+row.input_codes[i]));blue.append(mark);});square.append(blue);
    const purple=el('div',undefined,'purple-layer');
    row.refs.forEach((ref,port)=>{const mark=el('div');mark.append(math('m('+(2+port)+','+row.row+')='+(ref-row.row)));purple.append(mark);});square.append(purple);
    const text=el('div',undefined,'row-text');text.append(math('\\text{Row }'+row.row+':\\quad '+formula(row.formula)),explanation(row));
    const meaning=el('p');meaning.append(row.original_hypothesis?'Original context hypothesis.':'Selected by the actual primitive executor: '+row.selection+'.');text.append(meaning);
    if(row.refs.length){const sources=el('p');sources.append('Ordered source rows: ');row.refs.forEach((ref,i)=>{if(i)sources.append(', ');const a=el('a');a.href='#proof-row-'+String(ref);a.append(math(String(ref)));sources.append(a);});text.append(sources);}
    const details=el('details');details.append(el('summary','Exact placement, markings and primitive command'),el('pre',JSON.stringify(row,null,2)));text.append(details);line.append(square,text);box.append(line);
  }
  document.querySelector('#blue').addEventListener('change',layers);document.querySelector('#purple').addEventListener('change',layers);layers();
  if(window.MathJax?.typesetPromise)await MathJax.typesetPromise([box]);
  box.dataset.rowsRendered=String(saved.rows.length);
}
start().catch(e=>document.querySelector('#proof-view').append(el('p','Reader error: '+e.message,'reader-error')));
