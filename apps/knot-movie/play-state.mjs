import {canonical, examples, moves, parse, verifyMovie, VERSION} from "./engine.mjs";
import {trefoilIdentification} from "./cases.mjs";

export const puzzles = [
  {id:"slide", title:"Slide past a crossing", cap:3, source:"O1+ O2- O3+ U1+ U2- U3+", target:"O1+ O2- U2- U3+ O3+ U1+"},
  {id:"curl", title:"Straighten a curl", cap:3, source:examples.curl, target:""},
  {id:"bigon", title:"Pull a crossing pair apart", cap:3, source:examples.bigon, target:""},
  {id:"trefoil", title:"Find the standard trefoil", cap:6, ...trefoilIdentification}
];
export class KnotGame {
  constructor(puzzle,reverse=false) {
    this.cap=puzzle.cap;
    this.source=canonical(parse(reverse?puzzle.target:puzzle.source));
    this.target=canonical(parse(reverse?puzzle.source:puzzle.target));
    this.steps=[];
    this.load(this.source);
  }
  load(key) {
    this.key=key;
    this.word=parse(key);
    this.solved=key===this.target;
    this.choices=this.solved?[]:moves(this.word,this.cap);
  }
  play(kind,after) {
    const choice=this.choices.find(m=>m.kind===kind && m.key===after);
    if(!choice)throw Error("This local move is unavailable on the current diagram.");
    const step={kind,before:this.key,after};
    this.steps.push(step);this.load(after);
    if(this.solved)verifyMovie(this.certificate());
  }
  undo() {
    const step=this.steps.pop();
    if(step)this.load(step.before);
  }
  certificate() {
    return {version:VERSION,source:this.source,target:this.key,crossingCap:this.cap,steps:this.steps.slice()};
  }
}
