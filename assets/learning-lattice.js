// Both domains use exact integer A2 coordinates and capacity twelve.
export const LEARNING_LATTICES=Object.freeze({A2:'Full lattice','turtle-sublattice':'Sublattice'});
export function learningLattice(lattice='A2') {
 if(!Object.hasOwn(LEARNING_LATTICES,lattice))throw new Error('Unknown learning lattice');
 return lattice;
}
export const onTurtleSublattice=([x,y,z])=>(x-y)%3===0&&(y-z)%3===0;
export function learningPointFilter(lattice='A2') {
 return learningLattice(lattice)==='A2'?null:onTurtleSublattice;
}
export function restrictLearningOrientation(orientation,lattice='A2') {
 const filter=learningPointFilter(lattice);
 return filter?{...orientation,occupancy:new Map([...orientation.occupancy].filter(([,e])=>filter(e.point)))}:orientation;
}
