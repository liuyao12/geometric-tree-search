import { makeIcosahedralPatch } from "../../assets/icosahedral-exact.js";

self.onmessage = ({ data }) => {
  try {
    const patch = makeIcosahedralPatch({ radius: data.radius });
    const replacer = (_, x) => typeof x === "bigint" ? String(x) : x;
    self.postMessage({ ok: true, count: patch.tiles.length, counts: patch.counts,
      regular: patch.regularity.certified,
      sample: JSON.parse(JSON.stringify(patch.tiles[0], replacer)),
      json: JSON.stringify(patch, replacer, 2) });
  } catch (error) { self.postMessage({ ok: false, error: error.message }); }
};
