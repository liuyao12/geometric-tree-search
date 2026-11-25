import {learnMarks, rowProblems, runRows} from "./symbol-tiles.mjs";

const $ = id => document.getElementById(id);
const math = (node, tex) => window.katex.render(tex,node,{output:"mathml",throwOnError:true});
const glyph = s => s==="^" ? "\\verb|^|" : s;
const make = tag => document.createElement(tag);
const learned = learnMarks();
let runs, active, position;
function write(token) {
  const node=make("span"); math(node,glyph(token)); return node;
}
for (const word of learned.words) {
  const node=make("span");math(node,word.replaceAll("e^x","e^{x}"));$("training").append(node);
}
function mathSentence(id, pieces) {
  const node=$(id); node.replaceChildren();
  for(const piece of pieces) {
    if(typeof piece==="string")node.append(piece);
    else {const part=make("span");math(part,piece.tex);node.append(part);}
  }
}
mathSentence("tileDef",["A symbol occupies three points on a line in ",{tex:"\\mathbb{Z}^3"},
  ", with weights ",{tex:"(\\tfrac12,1,\\tfrac12)"},". Placing centres two lattice steps apart fills every internal seam to one."]);
mathSentence("orientation",["The row has a reading direction. Reversing an equality exchanges its two sides. Reversing the spelling of ",{tex:"e^x"}," would require reversing the parser and both end caps as well."]);
mathSentence("markDef",["Each forbidden ordered pair ",{tex:"(a,b,d)"}," has a marking component. A tile with symbol ",{tex:"a"}," assigns one value ",{tex:"d"}," cells to its right. A tile with symbol ",{tex:"b"}," assigns a different value at its own centre. Those assignments disagree exactly when the pair occurs at that distance. Other components can remain unassigned."]);

function nextIndex(predicate) {return active.events.findIndex((e,i)=>i>position && predicate(e));}
const distant = e => e.type==="mark" && e.delta>=3;
function render() {
  const strip=Array(active.n).fill(null), event=active.events[position];
  let marked=false;
  for (let i=0;i<=position;i++) {
    const e=active.events[i];
    if(e.type==="start") {strip.fill(null);marked=e.marked;}
    else if(e.type==="place")strip[e.slot]=e.symbol;
    else if(e.type==="undo")strip[e.slot]=null;
  }
  const mark=event.type==="mark";
  $("cells").style.setProperty("--slots",strip.length);$("cells").replaceChildren();
  for (let i=0;i<strip.length;i++) {
    const node=make("div"), label=make("i"); label.textContent=i+1;
    node.className="symbol-cell"+(strip[i]?" filled":"");
    if(strip[i])node.append(write(strip[i]));
    if(mark && i===event.source)node.classList.add("source");
    if(mark && i===event.slot){node.classList.add("candidate");node.append(write(event.symbol));}
    if(!mark && i===event.slot)node.classList.add("current");
    node.append(label);$("cells").append(node);
  }
  $("arc").replaceChildren();
  if(mark) {
    const a=(event.source+.5)*800/strip.length,b=(event.slot+.5)*800/strip.length;
    const path=document.createElementNS("http://www.w3.org/2000/svg","path");
    path.setAttribute("d","M "+a+" 67 Q "+((a+b)/2)+" -24 "+b+" 67");
    path.setAttribute("fill","none");path.setAttribute("stroke","#f6c36e");path.setAttribute("stroke-width","3");$("arc").append(path);
  }
  $("mode").textContent=marked?"Learned marks on":"Syntax only";
  $("counter").textContent=(position+1)+" / "+active.events.length;
  $("legend").textContent=mark?"Gold is the existing symbol. Dashed gold is a candidate excluded at this step.":"Filled cells are placed symbols. Dashed cells are still open.";
  const descriptions={
    start:["Open the row",marked?"All cells are open with learned markings active.":"Only the grammar markings constrain the row."],
    place:["Place one symbol","The scheduler placed a legal symbol in cell "+(event.slot+1)+"."],
    undo:["Roll back one tile","Cell "+(event.slot+1)+" is open again. The parent keeps its remaining alternatives."],
    mark:["A distant marking overlaps","The symbol in cell "+(event.source+1)+" excludes this candidate in cell "+(event.slot+1)+", a distance of "+event.delta+" cells. This candidate fits its immediate grammar seams."],
    miss:["The derivative differs","The row is grammatical. Its derivative differs from the integrand, so search backtracks."],
    dead:["A point has no placement","GCTS found an unfilled point with an empty domain and returns to the previous choice."],
    solved:["Derivative checked","The completed row differentiates exactly to the integrand."],
    open:["Width exhausted","The tested widths contain no checked solution."]
  };
  [$("action").textContent,$("reason").textContent]=descriptions[event.type];
  $("position").value=position;$("prev").disabled=position===0;
  $("next").disabled=$("finish").disabled=position===active.events.length-1;
  $("nextMark").disabled=nextIndex(distant)<0;$("rollback").disabled=nextIndex(e=>e.type==="undo")<0;
}
function selectReplay() {
  active=runs[document.querySelector("input[name=replay]:checked").value];
  $("position").max=active.events.length-1;
  const witness=active.events.findIndex(distant);
  position=witness<0?0:witness;render();
}
function setProblem() {
  const p=rowProblems[$("problem").value], seed=Number($("seed").value);
  math($("goal"),"\\displaystyle\\int "+(p===rowProblems.control?"\\left("+p.tex+"\\right)":p.tex)+"\\,dx");
  runs={plain:runRows(p,seed,null,true),learned:runRows(p,seed,learned.marks,true)};
  $("scores").replaceChildren();
  for (const [label,run] of [["Syntax only",runs.plain],["With learned marks",runs.learned]]) {
    const tr=make("tr");for(const v of [label,run.placed,run.undone]){const td=make("td");td.textContent=v.toLocaleString();tr.append(td);}
    $("scores").append(tr);
  }
  $("measured").textContent="The learned pass used "+learned.marks.size+" pair markings. "+
    (runs.learned.marked?"It found the checked row at width "+runs.learned.n+".":"It excluded every solution at the concluding width. The unrestricted pass recovered a checked row.");
  selectReplay();
}
for(const input of document.querySelectorAll("input[name=replay]"))input.onchange=selectReplay;
$("problem").onchange=$("seed").onchange=setProblem;
$("prev").onclick=()=>{position--;render();};$("next").onclick=()=>{position++;render();};
$("position").oninput=e=>{position=Number(e.target.value);render();};
$("nextMark").onclick=()=>{position=nextIndex(distant);render();};
$("rollback").onclick=()=>{position=nextIndex(e=>e.type==="undo");render();};
$("finish").onclick=()=>{position=active.events.length-1;render();};
setProblem();
