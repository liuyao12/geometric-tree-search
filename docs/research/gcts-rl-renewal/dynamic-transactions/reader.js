"use strict";
const saved = JSON.parse(document.getElementById("saved-data").textContent);
const picker = document.getElementById("state-picker");
const tex = x => "\\(" + x + "\\)";
function showState(){
  const state = saved.production_states.find(s => s.name === picker.value);
  const box = document.getElementById("row-counts");
  box.replaceChildren();
  if(!state){document.getElementById("decision-text").textContent="This state was not completed in the owned attempt.";return;}
  const max = Math.max(1,...state.full_counts.map(c=>c[1]));
  const selected = new Set(state.selected_keys.map(k=>k[1]));
  state.full_counts.forEach((c,row)=>{
    const line=document.createElement("div");line.className="row-count"+(selected.has(row)?" filled":c[1]===0?" dead":"");
    const label=document.createElement("span");label.textContent=tex("r="+row);
    const rail=document.createElement("div");rail.className="rail";
    const bar=document.createElement("div");bar.className="bar";bar.style.width=(Math.log1p(c[1])/Math.log1p(max)*100)+"%";rail.append(bar);
    const count=document.createElement("span");count.textContent=tex(c[1]);line.append(label,rail,count);box.append(line);
  });
  const d=state.decision;
  document.getElementById("decision-text").textContent="Global decision: "+d[0]+", row "+tex(d[1]) +", degree "+tex(d[2])+", generation "+tex(d[3])+".";
  if(window.MathJax?.typesetPromise) window.MathJax.typesetPromise([box,document.getElementById("decision-text")]);
}
picker.addEventListener("change",showState);showState();
