// Exact existential projection of binary marking variants. Each candidate's
// xor list is a template bit pattern, allowed up to a common flip. A global
// point coloring exists iff all relative-bit equations are consistent.
// Full refresh handles distant dependencies when parity components merge.
export function binaryQuotientClass(Base){return class extends Base{
 parityPrefix(){
  const key=JSON.stringify([...this.placed.keys()]);if(this.parityCache?.key===key)return this.parityCache;
  const parent=new Map(),offset=new Map();
  const find=p=>{if(!parent.has(p)){parent.set(p,p);offset.set(p,0);}let bit=0;while(parent.get(p)!==p){bit^=offset.get(p);p=parent.get(p);}return [p,bit];};
  const join=(a,b,bit)=>{const [ra,xa]=find(a),[rb,xb]=find(b);if(ra===rb){if((xa^xb)!==bit)throw Error('Inconsistent placed parity');}else{parent.set(ra,rb);offset.set(ra,xa^xb^bit);}};
  for(const id of this.placed.keys()){
   const entries=this.candidates.get(id).xor||[];
   for(const e of entries){if(![0,1].includes(e.bit))throw Error('Nonbinary marking');if(entries.length)join(entries[0].point,e.point,entries[0].bit^e.bit);}
  }
  return this.parityCache={key,find};
 }
 reason(c){
  const base=super.reason(c);if(base)return base;
  const {find}=this.parityPrefix(),wanted=new Map();
  for(const e of c.xor||[]){
   if(![0,1].includes(e.bit))throw Error('Nonbinary marking');
   const [root,offset]=find(e.point),value=e.bit^offset;
   if(wanted.has(root)&&wanted.get(root)!==value)return 'binary-marking-inconsistent';wanted.set(root,value);
  }
  return null;
 }
 refresh(){return super.refresh(new Set(this.points.keys()));}
};}
