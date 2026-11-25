import {tasks, zero, monomial, add, primitiveMove, applyMove, admit, libraryMoves, FairSearch} from "./rewrite-search.mjs";

const $=id=>document.getElementById(id);
const symbols=["x","e^x","\\sin{x}","\\cos{x}"];
const names=["x","exponential","sine","cosine"];
const el=(tag,text="")=>Object.assign(document.createElement(tag),{textContent:text});
function math(dest,tex){window.katex.render(tex,dest,{output:"mathml",throwOnError:true});}
function tex(poly){
  return poly.terms.slice().reverse().map(([key,coeff],i)=>{
    const a=coeff<0n?-coeff:coeff,ps=key.split(",").map(Number);
    const factors=ps.map((p,j)=>{
      if(!p)return "";if(p===1)return symbols[j];
      if(j===1)return "e^{"+p+"x}";
      if(j>=2)return (j===2?"\\sin":"\\cos")+"^{"+p+"}{x}";
      return "x^{"+p+"}";
    }).filter(Boolean).join("\\,");
    const magnitude=poly.den!==1n?"\\frac{"+a+"}{"+poly.den+"}":a!==1n||!factors?String(a):"";
    return (coeff<0n?"-":i?"+":"")+magnitude+factors;
  }).join("")||"0";
}
const integral=p=>"\\int "+(p.terms.length>1?"\\left("+tex(p)+"\\right)":tex(p))+"\\,dx";
function boardTex(total,r){
  if(!r.terms.length)return tex(total)+"+C";
  return (total.terms.length?tex(total)+"+":"")+integral(r);
}
function line(dest,label,eq){
  const wrap=el("div"),p=el("div");p.className="proof-line";math(p,eq);
  wrap.append(el("small",label),p);dest.append(wrap);
}
const key="tessera-exact-differential-library-v1";
const entries=new Map(), stored=new Map();
let persistent=true;
function restoreLibrary(){
  let records;
  try {records=JSON.parse(localStorage.getItem(key)||"[]");} catch {persistent=false;return;}
  if(!Array.isArray(records))return;
  for(const [id,,target] of tasks){
    const record=records.find(r=>r?.id===id);if(!record)continue;
    try {
      const moves=record.moves.map(terms=>{
        let p=zero;
        for(const [k,n,d] of terms)p=add(p,monomial(k.split(",").map(Number),BigInt(n),BigInt(d)));
        return primitiveMove(p);
      });
      entries.set(id,admit(target,moves));stored.set(id,record);
    } catch { /* Only successfully replayed records become available. */ }
  }
}
restoreLibrary();
let task, path=[], history=[], residual, total, factors=[], solver, rows=[];
function freshSearch(){
  solver=new FairSearch(residual,$("useLibrary").checked?[...entries.values()]:[]);
  rows=[];
}
function resetBoard(){
  task=tasks.find(t=>t[0]===$("task").value);
  path=[];history=[];residual=task[2];total=zero;factors=[];
  $("num").value=1;$("den").value=1;freshSearch();draw();
}
function currentMove(){
  const n=Number($("num").value),d=Number($("den").value);
  if(!factors.length||!Number.isInteger(n)||!n||Math.abs(n)>99||!Number.isInteger(d)||d<1||d>99)return null;
  const powers=[0,0,0,0];for(const j of factors)powers[j]++;
  return primitiveMove(monomial(powers,n,d));
}
function play(moves){
  for(const m of moves){
    const before=residual;residual=applyMove(residual,m);
    total=add(total,m.primitive);
    history.push({before,total,residual});path.push(m);
  }
  if(!residual.terms.length)admit(task[2],path);
  freshSearch();draw();
}
function preview(){
  const m=currentMove();$("apply").disabled=!m||!residual.terms.length;
  $("pop").disabled=!factors.length;
  for(const b of $("factorButtons").children)b.disabled=factors.length>=12||!residual.terms.length;
  if(m)math($("preview"),"G="+tex(m.primitive)+",\\qquad dG="+
    (m.change.terms.length>1?"\\left("+tex(m.change)+"\\right)":tex(m.change))+"\\,dx");
  else $("preview").textContent=factors.length?"Enter a nonzero signed numerator and a positive denominator.":"Choose a first factor.";
}
function searchView(){
  $("cost").textContent="Cost "+solver.cost;
  $("rounds").replaceChildren();
  for(const r of rows){
    const tr=el("tr");for(const v of [r.cost,r.parents,r.tested,r.fresh])tr.append(el("td",String(v)));
    $("rounds").append(tr);
  }
  const solved=solver.solution!==null,atLimit=solver.cost>=7;
  $("advance").disabled=$("run").disabled=solved||atLimit;
  $("playProof").hidden=!solver.solution?.length;
  $("searchState").textContent=!residual.terms.length?"The board is solved.":solved?
    "A checked proof was found at total cost "+solver.cost+".":atLimit?"Open through cost seven. Longer proofs remain possible.":
    solver.cost?"Still open. The shorter branches remain available for costlier continuations.":"Ready to explore the current remainder.";
  $("found").replaceChildren();
  if(solver.solution?.length)for(const [i,m] of solver.solution.entries())
    line($("found"),"Move "+(i+1)+(m.source==="saved"?" · saved proof":" · extract differential"),"G="+tex(m.primitive));
}
function draw(){
  math($("target"),"\\displaystyle "+integral(task[2]));
  math($("boardEq"),"\\displaystyle "+boardTex(total,residual));
  $("nMoves").textContent=path.length+(path.length===1?" move":" moves");
  $("undo").disabled=!path.length;preview();$("history").replaceChildren();
  if(!path.length)$("history").append(el("p","Your moves will appear here."));
  for(const [i,m] of path.entries()){
    line($("history"),"Move "+(i+1)+(m.source==="saved"?" · saved proof":" · add and subtract the differential"),
      integral(history[i].before)+"="+boardTex(m.primitive,history[i].residual));
  }
  $("save").disabled=!!residual.terms.length||entries.has(task[0]);
  $("savedNote").textContent=entries.has(task[0])?"This integral has a saved proof.":residual.terms.length?"":"Verified by differentiation.";
  $("memoryInfo").textContent=entries.size?(persistent?"Verified proofs are saved in this browser.":"Verified proofs are available for this visit."):"Finish a game and save its proof to reuse it in another integral.";
  $("library").replaceChildren();
  for(const [id,entry] of entries){
    line($("library"),tasks.find(t=>t[0]===id)[1],integral(entry.target)+"="+tex(entry.primitive)+"+C");
    const [m]=libraryMoves(residual,[entry]);if(m&&residual.terms.length){
      const b=el("button","Use on this remainder");b.onclick=()=>play([m]);$("library").append(b);
    }
  }
  searchView();
}
for(const [id,name] of tasks){const o=el("option",name);o.value=id;$("task").append(o);}
const requested=new URLSearchParams(location.search).get("task");
if(tasks.some(t=>t[0]===requested))$("task").value=requested;
for(const [j,s] of symbols.entries()){
  const b=el("button");math(b,s);b.setAttribute("aria-label","Append "+names[j]);
  b.onclick=()=>{factors.push(j);preview();};$("factorButtons").append(b);
}
$("task").onchange=resetBoard;
$("num").oninput=$("den").oninput=preview;
$("pop").onclick=()=>{factors.pop();preview();};
$("apply").onclick=()=>{const m=currentMove();if(m)play([m]);};
$("undo").onclick=()=>{const last=history.pop();path.pop();residual=last.before;total=history.at(-1)?.total??zero;freshSearch();draw();};
$("advance").onclick=()=>{rows.push(solver.advance());searchView();};
$("run").onclick=()=>{while(solver.solution===null&&solver.cost<7)rows.push(solver.advance());searchView();};
$("playProof").onclick=()=>{if(solver.solution?.length)play(solver.solution);};
$("useLibrary").onchange=()=>{freshSearch();searchView();};
$("save").onclick=()=>{
  entries.set(task[0],admit(task[2],path));
  stored.set(task[0],{id:task[0],moves:path.map(m=>m.primitive.terms.map(([k,n])=>[k,String(n),String(m.primitive.den)]))});
  try{localStorage.setItem(key,JSON.stringify([...stored.values()]));}catch{persistent=false;}
  freshSearch();draw();
};
math($("ruleEq"),"\\int r\\,dx=\\int \\!\\bigl(G'+(r-G')\\bigr)\\,dx=G+\\int(r-G')\\,dx");
resetBoard();
