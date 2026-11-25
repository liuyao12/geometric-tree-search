import {count, parse, verifyMovie, VERSION} from "./engine.mjs";
import {drawKnot, movieDrawings, planarDrawing, verifyDrawing} from "./drawing.mjs";
import {descriptions} from "./move-detail.mjs";
import {KnotGame, puzzles} from "./play-state.mjs";

const $=id=>document.getElementById(id);
let game, reversed=false, markedCrossing=null, frame=null;
const diagrams=new Map();
function drawing(key) {
  if(!diagrams.has(key)){
    const d=planarDrawing(parse(key));verifyDrawing(d);diagrams.set(key,d);
  }
  return diagrams.get(key);
}
function name(move) {return descriptions[move.kind].title;}
function visits() {
  $("word").replaceChildren();
  for(const v of game.word){
    const b=document.createElement("button");b.className="secondary";
    b.textContent=(v.over?"O":"U")+v.id+(v.sign>0?"+":"-");
    b.setAttribute("aria-pressed",String(v.id===markedCrossing));
    b.setAttribute("aria-label",(v.over?"Over":"Under")+" at crossing "+v.id);
    b.onclick=()=>{markedCrossing=v.id===markedCrossing?null:v.id;highlight();};
    $("word").append(b);
  }
  if(markedCrossing!==null){
    const positions=game.word.flatMap((v,i)=>v.id===markedCrossing?[i+1]:[]);
    $("crossing").textContent="Crossing "+markedCrossing+" occurs at visits "+positions.join(" and ")+".";
  }else $("crossing").textContent=game.word.length?"Amber strands show the selected move.":"This diagram has no crossings.";
}
function highlight(){
  drawKnot($("current"),frame?.before??drawing(game.key),{
    affected:markedCrossing!==null?new Set([markedCrossing]):frame?.affected,
    changedStrands:markedCrossing!==null?new Set():frame?.beforeStrands,labels:true});
  visits();
}
function preview(){
  const move=game.choices[Number($("choice").value)];
  frame=null;
  if(move){
    const cert={version:VERSION,crossingCap:game.cap,source:game.key,target:move.key,steps:[{kind:move.kind,after:move.key}]};
    [frame]=movieDrawings(cert);
    drawKnot($("preview"),frame.after,{affected:frame.affected,changedStrands:frame.afterStrands,labels:true});
    $("description").textContent=descriptions[move.kind].text;
    $("previewLabel").textContent="After this move · "+count(move.after)+" crossings";
  }else{
    drawKnot($("preview"),drawing(game.key));
    $("description").textContent=game.solved?"Your path replays to the target.":"There are no moves under this crossing limit.";
    $("previewLabel").textContent=game.solved?"Verified endpoint":"Current endpoint";
  }
  highlight();
}
function render() {
  markedCrossing=null;$("choice").replaceChildren();
  game.choices.forEach((m,i)=>{
    const o=document.createElement("option");o.value=i;
    const ids=m.kind.endsWith("+")?m.patch.map(k=>k+1):[...new Set(m.patch.map(k=>game.word[Math.floor(k/2)].id))];
    o.textContent=name(m)+(ids.length?" · "+(m.kind.endsWith("+")?"gap ":"crossing ")+ids.join(", "):"")+" · option "+(i+1);
    $("choice").append(o);
  });
  $("choice").disabled=$("apply").disabled=!game.choices.length;$("undo").disabled=$("save").disabled=!game.steps.length;
  $("heading").textContent=game.solved?"Target reached":"Your diagram";
  $("progress").textContent=game.steps.length+(game.steps.length===1?" move":" moves")+(game.solved?" · verified":"");
  $("currentLabel").textContent="Current · "+count(game.word)+(count(game.word)===1?" crossing":" crossings");
  $("bounds").textContent="This puzzle allows up to "+game.cap+" crossings. The menu lists distinct resulting diagrams.";
  $("history").replaceChildren();$("empty").hidden=!!game.steps.length;
  for(const step of game.steps){const li=document.createElement("li");li.textContent=name(step);$("history").append(li);}
  drawKnot($("target"),drawing(game.target));preview();
}
function reset() {
  const puzzle=puzzles.find(p=>p.id===$("puzzle").value);
  game=new KnotGame(puzzle,reversed);render();
}
for(const p of puzzles){const o=document.createElement("option");o.value=p.id;o.textContent=p.title;$("puzzle").append(o);}
const query=new URLSearchParams(location.search).get("puzzle");
if(puzzles.some(p=>p.id===query))$("puzzle").value=query;
$("puzzle").onchange=()=>{reversed=false;reset();};
$("reverse").onclick=()=>{reversed=!reversed;reset();};
$("reset").onclick=reset;
$("choice").onchange=()=>{markedCrossing=null;preview();};
$("apply").onclick=()=>{const m=game.choices[Number($("choice").value)];game.play(m.kind,m.key);render();};
$("undo").onclick=()=>{game.undo();render();};
$("save").onclick=()=>{
  const cert=game.certificate();verifyMovie(cert);
  const url=URL.createObjectURL(new Blob([JSON.stringify(cert,null,2)],{type:"application/json"}));
  const a=document.createElement("a");a.href=url;a.download="my-reidemeister-path.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
reset();
