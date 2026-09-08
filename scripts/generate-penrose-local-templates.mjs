import {writeFileSync} from 'node:fs';
import {MIXED_TEMPLATES} from '../assets/penrose-mixed-templates.js';
import {canonical} from '../assets/cyclotomic-five.js';
import {onSegment} from '../assets/penrose-polygon.js';
// Export the existing boundary rules as problem input. No bar interiors or
// extensions are exported or made accessible to the online learner.
const templates=MIXED_TEMPLATES.map(t=>({kind:t.kind,presentation:t.presentation,exactPoints:t.exactPoints,weights:t.weights,labels:t.exactPoints.map((from,i)=>{const to=t.exactPoints[(i+1)%t.exactPoints.length];return{code:'ports',from,to,ports:t.bars.flatMap(b=>[b.from,b.to].filter(p=>onSegment(p,from,to)).map(point=>({point,axis:canonical({coeff:Array.from({length:5},(_,k)=>+(k===b.family)),denominator:1})}))) };})}));
writeFileSync(new URL('../assets/penrose-local-templates.js',import.meta.url),'// Boundary-only problem data exported by scripts/generate-penrose-local-templates.mjs.\n// P1/P2 rules originate in the existing transferred decorations, not independent arrows.\nexport const LOCAL_TEMPLATES='+JSON.stringify(templates)+';\n');
