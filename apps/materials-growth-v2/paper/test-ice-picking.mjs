import assert from 'node:assert/strict';
import * as T from '../../3d-lattice-tiler/vendor/three.module.min.js';
const mesh=new T.InstancedMesh(new T.SphereGeometry(1,18,12),new T.MeshBasicMaterial(),2);
mesh.computeBoundingSphere(); // A camera render can calculate this before data load.
mesh.setMatrixAt(0,new T.Matrix4().makeTranslation(5,0,0));
mesh.setMatrixAt(1,new T.Matrix4().makeTranslation(9,0,0));
const ray=new T.Raycaster(new T.Vector3(5,0,10),new T.Vector3(0,0,-1));
assert.equal(ray.intersectObject(mesh).length,0);
mesh.computeBoundingSphere();
assert.equal(ray.intersectObject(mesh)[0].instanceId,0);
console.log(JSON.stringify({staleBoundFailureReproduced:true,refreshedAtomPicking:true}));
