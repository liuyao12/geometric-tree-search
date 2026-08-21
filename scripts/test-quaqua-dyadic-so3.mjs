import assert from "node:assert/strict";
import {
  exactDyadicSO3,
  multiplyMatrices,
  physicalToQCoordinates,
  verifyDyadicSO3
} from "../3d-reptiles/dyadic-so3.js";

const sqrt3 = Math.sqrt(3);
const identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
const quarterTurn = [[1, 0, 0], [0, 0, -1], [0, 1, 0]];
const thirdTurn = [[-0.5, -sqrt3 / 2, 0], [sqrt3 / 2, -0.5, 0], [0, 0, 1]];

assert.deepEqual(exactDyadicSO3(identity), {
  exponent: 0,
  denominator: 1,
  numerators: identity
});
assert.deepEqual(exactDyadicSO3(quarterTurn), {
  exponent: 0,
  denominator: 1,
  numerators: quarterTurn
});
assert.deepEqual(exactDyadicSO3(thirdTurn), {
  exponent: 1,
  denominator: 2,
  numerators: [[-1, -3, 0], [1, -1, 0], [0, 0, 2]]
});

const word = multiplyMatrices(multiplyMatrices(thirdTurn, quarterTurn), thirdTurn);
const exactWord = exactDyadicSO3(word);
assert.ok(exactWord);
assert.equal(verifyDyadicSO3(exactWord.numerators, exactWord.denominator), true);

const qThird = physicalToQCoordinates(thirdTurn);
assert.deepEqual(qThird.map(row => row.map(value => Math.round(value * 2))), [[-1, -3, 0], [1, -1, 0], [0, 0, 2]]);

console.log("quaquaversal dyadic SO(3) arithmetic passed", exactWord);
