import * as THREE from 'three';
// Oracle/search inspection geometry for the legacy renderer. Owns no solver
// state and can be removed without disturbing the real tiling's scene/trail.
export class LearningScene {
 constructor(scene){this.group=new THREE.Group();scene.add(this.group);this.group.visible=false;}
 clear(){for(const child of [...this.group.children]){this.group.remove(child);child.geometry?.dispose();child.material?.dispose();}this.group.visible=false;}
 set(frame,scale=1){
  this.clear();const {model,placements}=frame;
  const palette=['#299c9b','#7398dc','#b79bce','#cfaa65'];
  placements.forEach((p,index)=>{
   const o=model.orientations[p.oi],positions=[];
   for(const face of o.faces??[]){
    if(face.length<3)continue;
    const vertices=face.map(i=>new THREE.Vector3(...o.vertices[i])),origin=vertices[0],u=vertices[1].clone().sub(origin).normalize();let normal=new THREE.Vector3();
    for(let j=2;j<vertices.length&&normal.lengthSq()<1e-12;j++)normal.crossVectors(u,vertices[j].clone().sub(origin));
    if(normal.lengthSq()<1e-12)continue;normal.normalize();const v=new THREE.Vector3().crossVectors(normal,u);
    const contour=vertices.map(pt=>{const d=pt.clone().sub(origin);return new THREE.Vector2(d.dot(u),d.dot(v));});
    for(const triangle of THREE.ShapeUtils.triangulateShape(contour,[]))for(const j of triangle)positions.push(...o.vertices[face[j]].map((x,a)=>(x+p.translation[a])/scale));
   }
   if(!positions.length)return;
   const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();
   this.group.add(new THREE.Mesh(geometry,new THREE.MeshPhongMaterial({color:palette[index%palette.length],side:THREE.DoubleSide,transparent:true,opacity:.72,depthWrite:false})));
   this.group.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry,15),new THREE.LineBasicMaterial({color:'#315760'})));
  });
  const totals=new Map();for(const p of placements)for(const c of model.orientations[p.oi].cells){const pos=c.pos.map((x,i)=>x+p.translation[i]),k=pos.join();totals.set(k,{pos,total:(totals.get(k)?.total??0)+c.weight});}
  const points=[...totals.values()].filter(p=>p.total<model.capacity).map(p=>({pos:p.pos,color:'#d39a28'}));
  if(frame.deadPoint)points.push({pos:frame.deadPoint,color:'#ed5353'});
  for(const p of frame.inspection?.points??[])if(p.overlap)points.push({pos:p.pos,color:p.conflict?'#ed5353':'#369ee7'});
  if(points.length){const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(points.flatMap(p=>p.pos.map(x=>x/scale)),3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(points.flatMap(p=>new THREE.Color(p.color).toArray()),3));this.group.add(new THREE.Points(geometry,new THREE.PointsMaterial({size:6,sizeAttenuation:false,vertexColors:true,depthTest:false})));}
  this.group.visible=true;
 }
}
