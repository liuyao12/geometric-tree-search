// Finite vector-valued tile markings, with a permutation representation on
// basis vectors. Runtime compatibility is equality with a global section.
const key = p => p.join(',');
const plus = (a,b) => a.map((x,i)=>x+b[i]);
const minus = (a,b) => a.map((x,i)=>x-b[i]);
const oid = o => `${o.type}:${o.index}`;
const signature = cells => cells.map(p=>`${key(p.pos)}:${p.weight}`).sort().join('|');
const minimum = cells => [0,1,2].map(i=>Math.min(...cells.map(p=>p.pos[i])));
function pairKey(a,b,d) {
  const forward = `${a}|${b}|${key(d)}`, reverse = `${b}|${a}|${key(d.map(x=>-x))}`;
  return forward < reverse ? forward : reverse;
}

export class VectorMarkings {
  constructor(prepared, capacity, {extent=0, maxSlots=4096}={}) {
    this.orientations=prepared.flat(); this.capacity=capacity;
    this.extent=Math.max(0,Math.min(2,Math.floor(extent)));
    this.forbidden=new Set(); this.fields=new Map(); this.section=new Map();
    this.rank=0; this.revision=0; this.conflicts=0; this.maxSlots=maxSlots;
    this.slotCount=0; this.representation=[]; this.transforms=this.symmetries();
    this.exact=Number.isSafeInteger(capacity) && this.orientations.every(o=>o.orientation.occupancy.every(p=>Number.isSafeInteger(p.weight)&&p.weight>0&&p.pos.every(Number.isSafeInteger)));
    this.rebuild();
  }
  observeDeadPoint(point, placements) {
    if(!this.exact)return false;
    const weights=new Map(),owners=new Map(),active=new Map();
    for(const p of placements) {
      active.set(`${oid(p)}@${key(p.translation)}`,p);
      for(const c of p.orientation.occupancy) {
        const k=key(plus(c.pos,p.translation));weights.set(k,(weights.get(k)||0)+c.weight);
        if(!owners.has(k))owners.set(k,[]);owners.get(k).push(p);
      }
    }
    if((weights.get(key(point))||0)>=this.capacity)return false;
    const blockers=new Set();
    for(const o of this.orientations)for(const anchor of o.orientation.occupancy) {
      const translation=minus(point,anchor.pos),used=active.get(`${oid(o)}@${key(translation)}`);
      if(used){blockers.add(used);continue;}
      const cell=o.orientation.occupancy.find(c=>(weights.get(key(plus(c.pos,translation)))||0)+c.weight>this.capacity);
      if(!cell)return false;
      for(const p of owners.get(key(plus(cell.pos,translation)))||[])blockers.add(p);
    }
    return this.learnPair([...blockers]);
  }
  // Include every lattice point-group operation that preserves each species'
  // supplied orientation orbit. The induced action permutes marking bases.
  symmetries() {
    const lookup=new Map();
    for(const o of this.orientations) {
      const origin=minimum(o.orientation.occupancy);
      lookup.set(`${o.type}|${signature(o.orientation.occupancy.map(p=>({...p,pos:minus(p.pos,origin)})))}`,{o,origin});
    }
    const permutations=[[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]], result=[];
    for(const perm of permutations) for(let mask=0;mask<8;mask++) {
      const transform=p=>perm.map((j,i)=>p[j]*(mask&(1<<i)?-1:1));
      const map=new Map();
      for(const o of this.orientations) {
        const cells=o.orientation.occupancy.map(p=>({...p,pos:transform(p.pos)})), origin=minimum(cells);
        const match=lookup.get(`${o.type}|${signature(cells.map(p=>({...p,pos:minus(p.pos,origin)})))}`);
        if(!match) break;
        map.set(oid(o),{id:oid(match.o),shift:minus(origin,match.origin)});
      }
      if(map.size===this.orientations.length) result.push({transform,map});
    }
    return result;
  }
  // Only called with a certified dead-point blocker pair. Close its orbit so
  // the learned fields, not just the geometric search, remain equivariant.
  learnPair(blockers) {
    if(blockers.length!==2 || this.forbidden.size>=4096) return false;
    const [a,b]=blockers; let changed=false;
    for(const {transform,map} of this.transforms) {
      const aa=map.get(oid(a)),bb=map.get(oid(b));
      const d=minus(plus(transform(b.translation),bb.shift),plus(transform(a.translation),aa.shift));
      const k=pairKey(aa.id,bb.id,d);
      if(!this.forbidden.has(k)) {this.forbidden.add(k);changed=true;}
    }
    return changed;
  }
  rebuild(placements=[]) {
    const slots=[], byOrientation=new Map();
    for(const o of this.orientations) {
      const points=new Map();
      for(const p of o.orientation.occupancy)
        for(let x=-this.extent;x<=this.extent;x++) for(let y=-this.extent;y<=this.extent;y++) for(let z=-this.extent;z<=this.extent;z++) {
          const pos=plus(p.pos,[x,y,z]); points.set(key(pos),pos);
        }
      const list=[...points.values()].map(pos=>({pos}));
      for(const s of list) {s.id=slots.length;slots.push(s);}
      byOrientation.set(oid(o),list);
    }
    this.slotCount=slots.length;
    // A resource bound reduces pruning only: the constant field is always
    // sound. It never removes a geometric branch or licenses a negative.
    const trivial=slots.length>this.maxSlots || !this.exact;
    const parent=slots.map((_,i)=>i), size=slots.map(()=>1);
    const find=i=> {while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
    const union=(a,b)=>{a=find(a);b=find(b);if(a===b)return;if(size[a]<size[b])[a,b]=[b,a];parent[b]=a;size[a]+=size[b];};
    if(!trivial) for(let ai=0;ai<this.orientations.length;ai++) for(let bi=ai;bi<this.orientations.length;bi++) {
      const a=this.orientations[ai],b=this.orientations[bi], aId=oid(a),bId=oid(b);
      const weights=new Map(a.orientation.occupancy.map(p=>[key(p.pos),p.weight]));
      const legality=new Map();
      for(const u of byOrientation.get(aId)) for(const v of byOrientation.get(bId)) {
        const d=minus(u.pos,v.pos),dk=key(d);
        if(!legality.has(dk)) {
          const distinct=aId!==bId || d.some(Boolean);
          const allowed=distinct && !this.forbidden.has(pairKey(aId,bId,d))
            && b.orientation.occupancy.every(p=>(weights.get(key(plus(p.pos,d)))||0)+p.weight<=this.capacity);
          legality.set(dk,allowed);
        }
        // Enforce equality for a SUPERSET of all pairs that could occur in
        // an infinite tiling. Every derived marking therefore preserves it.
        if(legality.get(dk)) union(u.id,v.id);
      }
    }
    const bases=new Map();
    this.fields.clear();
    for(const [id,list] of byOrientation) this.fields.set(id,list.map(s=>{
      const root=trivial?0:find(s.id);if(!bases.has(root))bases.set(root,bases.size);
      return {pos:s.pos,basis:bases.get(root)};
    }));
    this.rank=bases.size; this.trivial=trivial;
    // Verify and expose the point-group representation on R^rank. Fields
    // store e_basis sparsely; this is full-vector equality, not wildcards.
    this.representation=this.transforms.map(({transform,map})=>{
      const permutation=Array(this.rank).fill(-1);
      for(const [id,field] of this.fields) {
        const target=map.get(id), other=new Map(this.fields.get(target.id).map(s=>[key(s.pos),s.basis]));
        for(const s of field) {
          const basis=other.get(key(minus(transform(s.pos),target.shift)));
          if(basis===undefined || (permutation[s.basis]!==-1 && permutation[s.basis]!==basis)) throw Error('Non-equivariant marking construction');
          permutation[s.basis]=basis;
        }
      }
      if(new Set(permutation).size!==this.rank) throw Error('Invalid marking representation');
      return permutation;
    });
    this.section.clear();this.conflicts=0;this.revision++;
    for(const p of placements)this.add(p);
  }
  entries(move) {return this.fields.get(oid(move)).map(s=>({key:key(plus(s.pos,move.translation)),basis:s.basis}));}
  compatible(move) {
    if(this.conflicts)return false;
    return this.entries(move).every(s=>{
      const cell=this.section.get(s.key);return !cell || (cell.size===1 && cell.has(s.basis));
    });
  }
  add(move) {
    for(const s of this.entries(move)) {
      let cell=this.section.get(s.key);if(!cell){cell=new Map();this.section.set(s.key,cell);}
      const before=cell.size;cell.set(s.basis,(cell.get(s.basis)||0)+1);
      if(before===1&&cell.size===2)this.conflicts++;
    }
  }
  remove(move) {
    for(const s of this.entries(move)) {
      const cell=this.section.get(s.key),before=cell.size,n=cell.get(s.basis)-1;
      if(n)cell.set(s.basis,n);else cell.delete(s.basis);
      if(before===2&&cell.size===1)this.conflicts--;
      if(!cell.size)this.section.delete(s.key);
    }
  }
  stats() {return {marking_rank:this.rank,marking_slots:this.slotCount,marking_revision:this.revision,
    marking_certified_pairs:this.forbidden.size,global_section_points:this.section.size,
    global_section_conflicts:this.conflicts,marking_resource_fallback:this.trivial,
    marking_memory_bytes:this.slotCount*32+this.section.size*48+this.forbidden.size*80};}
}
