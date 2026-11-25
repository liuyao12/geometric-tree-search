import {emptyMemory, learn, search} from "./search.mjs";

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const data = await fetch(new URL("./problems.json",import.meta.url)).then(r => {
  if (!r.ok) throw Error("Could not load the integral collection.");
  return r.json();
});
const sym = ["e^t", "\\sin t", "\\cos t"];
const symbol = ["\\exp", "\\sin", "\\cos"];
function math(el, tex) {
  window.katex.render(tex, el, {output:"mathml",throwOnError:true});
}
function element(name, text="", cls="") {
  const el = document.createElement(name); el.textContent=text; el.className=cls; return el;
}
function primitive(word,factors) {
  const terms=[];
  for(let j=word.length-1;j>=0;j--) {
    const c=factors[j]; if(!c) continue;
    const power=j===0?"":j===1?"t":"t^{"+j+"}";
    terms.push((c<0?"-":terms.length?"+":"")+(Math.abs(c)===1?"":Math.abs(c))+power+"\\,"+sym[word[j]]);
  }
  return terms.join("") || "0";
}
function title(p) {
  if(p.id.startsWith("train-")){
    const [,degree,h]=p.id.split("-");
    return ["Constant weight","Linear weight","Quadratic weight"][degree]+" · "+({exp:"exponential",sin:"sine",cos:"cosine"}[h]);
  }
  if(p.group==="shift") return p.id==="mixed-sin"?"Mixed terms · repeated sine":"Mixed terms · repeated cosine";
  const [g,j,h]=p.id.split("-");
  return ({3:"Cubic",4:"Quartic"}[j])+" "+({exp:"exponential",sin:"sine",cos:"cosine"}[h])+" · "+g+" substitution";
}
let memory=emptyMemory(), training=[], task, cold, warm, run, cursor=0, mode="cold", timer=null;
function stop(){clearInterval(timer);timer=null;$("play").textContent="Play";}
function buttonMode(value) {
  mode=value;document.querySelector('input[value="'+value+'"]').checked=true;
}
function nextLesson() {
  if(training.length===data.training.length) return;
  const problem=data.training[training.length], checked=search(problem,data.columns,0);
  learn(memory,problem,checked);training.push({problem,checked});
}
function compareRow(label,result) {
  const tr=element("tr");
  for(const value of [label,result.placements,result.backtracks]) tr.append(element("td",String(value)));
  return tr;
}
function chips(id,entries) {
  const dest=$(id);dest.replaceChildren();
  if(!entries.size){dest.append(element("span","No observations yet.","empty"));return;}
  const wrap=element("div","","chips");dest.append(wrap);
  for(const entry of entries) {
    const [a,b]=entry.split("/"); const chip=element("span","","chip");
    math(chip,symbol[Number(a)]+"\\;\\to\\;"+symbol[Number(b)]);wrap.append(chip);
  }
}
function showMemory(){
  $("trained").textContent=training.length+" of 9";
  $("reset").disabled=!training.length;
  $("trainOne").disabled=$("trainAll").disabled=training.length===9;
  chips("pairs",memory.pairs);chips("tops",memory.top);
  $("lessons").replaceChildren();
  for(const {problem,checked} of training){
    const row=element("div","","lesson"), formula=element("span");math(formula,"\\int "+problem.formula+"\\,dx");
    const replay=element("button","Replay");
    replay.setAttribute("aria-label","Replay training search for "+title(problem));
    replay.onclick=()=>{$("problem").value=problem.id;$("seed").value="0";buttonMode("cold");reload();};
    row.append(formula,element("small",checked.placements+" placements"),replay);$("lessons").append(row);
  }
  if(!training.length)$("lessons").append(element("p","Train an example to inspect its search."));
  $("lastLesson").replaceChildren();
  if(training.length){
    const {problem,checked}=training[training.length-1];const f=element("span");
    math(f,"\\int "+problem.formula+"\\,dx");
    $("lastLesson").append("Last learned from ", f, " after "+checked.placements+" placements.");
  }
}
function activeRun(jump) {
  stop(); run=mode==="cold"?cold:warm;cursor=0;
  if(jump==="end") cursor=run.events.length-1;
  else if(jump){const i=run.events.findIndex(e=>e.type===jump);if(i>=0)cursor=i;}
  $("position").max=run.events.length-1; draw();
}
function reload(jump="") {
  task=[...data.problems,...data.training].find(p=>p.id===$("problem").value);
  const seed=Number($("seed").value);
  cold=search(task,data.columns,seed);
  warm=training.length?search(task,data.columns,seed,memory):cold;
  math($("integral"),"\\displaystyle \\int "+task.formula+"\\,dx");
  $("sub").replaceChildren();
  if(task.substitution) math($("sub"),"t="+task.substitution);
  $("comparison").replaceChildren(compareRow("Untrained",cold),compareRow("With experience",warm));
  const delta=cold.placements-warm.placements;
  $("difference").textContent=!task.rows?"The substitution reader could not start either run.":
    !training.length?"Train an example to compare the runs.":
    !warm.word||!cold.word?"At least one run reached its search limit.":
    delta===0?"Both runs used the same number of placements.":
    "Experience used "+Math.abs(delta)+(delta>0?" fewer":" more")+" placements on this problem.";
  showMemory();activeRun(jump);
}
const headings={start:"Ready to search",place:"Tile placed",rejected:"Derivative mismatch",rollback:"Tile removed",
  dead:"No compatible tile",fallback:"Reopening the search",verified:"Derivative verified",
  exhausted:"Grammar exhausted",budget:"Placement budget reached",unsupported:"Substitution unavailable"};
function draw() {
  const e=run.events[cursor], n=run.events.length;
  $("phase").textContent=e.type==="unsupported"?"Input stage":
    (mode==="warm"&&training.length&&!run.events.slice(0,cursor+1).some(x=>x.type==="fallback"))?"Learned markings":"Unrestricted";
  $("eventName").textContent=headings[e.type];$("eventName").className=["rollback","rejected","dead"].includes(e.type)?"bad":"";
  $("eventCount").textContent="Event "+(cursor+1)+" / "+n;$("position").value=cursor;
  $("slots").replaceChildren();
  for(let j=e.word.length-1;j>=0;j--){
    const h=e.word[j],slot=element("div","","slot"),degree=element("small"),face=element("span","","face");
    degree.textContent="Degree "+j;
    if(h===null){face.textContent="Open";}else{
      slot.classList.add("filled");slot.dataset.h=h;
      math(face,(j===0?"":j===1?"t\\,":"t^{"+j+"}\\,")+sym[h]);
    }
    if(j===e.j)slot.classList.add(e.type==="rollback"?"undone":"now");
    slot.append(degree,face);$("slots").append(slot);
  }
  const why=$("explanation"),w=$("witness");w.replaceChildren();
  const explanations={
    start:"The degree slots are open. Each placement fixes one function.",
    place:e.forced?"Only one tile fits this frontier point.":"The selected frontier point has "+e.choices+" placements, including this one.",
    rollback:"The tile at degree "+e.j+" has been removed. The search resumes from the restored board.",
    rejected:"Even after matching coefficients, this residual remains at degree "+e.degree+".",
    verified:"The chosen coefficients reproduce every term of the integrand on differentiation.",
    dead:"The learned constraints leave a frontier point with no compatible placement.",
    fallback:"The learned pass ran out of alternatives. The board is restored and all functions are available again.",
    exhausted:"Every available candidate has been checked.",budget:"This run used all 512 placements.",
    unsupported:"Simplification erased the inner exponential. This reader cannot recover a substitution for this input."
  };
  why.textContent=explanations[e.type];
  if(e.type==="verified") math(w,"F(x)="+primitive(e.word,e.factors)+"+C");
  if(e.type==="rejected") {
    const letters=[0,1,2], pieces=[];
    for(const h of letters){const a=e.residual[h];if(!a)continue;
      pieces.push((a<0?"-":pieces.length?"+":"")+(Math.abs(a)===1?"":Math.abs(a)) + sym[h]);}
    const p=e.degree===0?"":e.degree===1?"t":"t^{"+e.degree+"}";
    math(w,p+"\\left("+pieces.join("")+"\\right)\\not\\equiv 0");
  }
  $("placed").textContent=e.placements;$("rolls").textContent=e.backtracks;$("checks").textContent=e.candidates;
  $("prev").disabled=cursor===0;$("next").disabled=$("end").disabled=cursor===n-1;
  $("backtrack").disabled=!run.events.slice(cursor+1).some(v=>v.type==="rollback");
  $("play").disabled=n===1;
}
function seek(i){stop();cursor=Math.max(0,Math.min(i,run.events.length-1));draw();}
const groups={transfer:"Held-out integrals",shift:"When experience misleads"};
for(const [group,label] of Object.entries(groups)){
  const optgroup=element("optgroup");optgroup.label=label;
  for(const p of data.problems.filter(p=>p.group===group)){const o=element("option",title(p));o.value=p.id;optgroup.append(o);}
  $("problem").append(optgroup);
}
const practice=element("optgroup");practice.label="Training examples";
for(const p of data.training){const o=element("option",title(p));o.value=p.id;practice.append(o);}
$("problem").append(practice);
$("problem").value=data.problems.some(p=>p.id===params.get("case"))?params.get("case"):"quadratic-3-sin";
if(["0","1024","4096","8192"].includes(params.get("seed")))$("seed").value=params.get("seed");
const count=Number(params.get("seen")||0);
for(let j=0;j<Math.min(9,count);j++)nextLesson();
if(training.length)buttonMode("warm");
$("trainOne").onclick=()=>{nextLesson();buttonMode("warm");reload();};
$("trainAll").onclick=()=>{while(training.length<9)nextLesson();buttonMode("warm");reload();};
$("reset").onclick=()=>{memory=emptyMemory();training=[];buttonMode("cold");reload();};
$("problem").onchange=$("seed").onchange=()=>reload();
document.querySelectorAll("[name=mode]").forEach(r=>r.onchange=()=>{buttonMode(r.value);activeRun();});
$("position").oninput=()=>seek(Number($("position").value));
$("prev").onclick=()=>seek(cursor-1);$("next").onclick=()=>seek(cursor+1);
$("end").onclick=()=>seek(run.events.length-1);
$("backtrack").onclick=()=>seek(run.events.findIndex((e,i)=>i>cursor&&e.type==="rollback"));
$("play").onclick=()=>{if(timer){stop();return;}if(cursor===run.events.length-1)seek(0);
  $("play").textContent="Pause";timer=setInterval(()=>{cursor++;draw();if(cursor>=run.events.length-1)stop();},330);};
math($("domain"),"x>0");reload(params.get("jump")||"rejected");
