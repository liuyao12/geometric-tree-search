#!/usr/bin/env node
import { makeIcosahedralPatch } from "../assets/icosahedral-exact.js";

const input = process.argv[2] ?? "1";
if (!/^\d+$/.test(input)) throw new TypeError("Usage: node scripts/export-icosahedral-exact.mjs [nonnegative-radius]");
const patch = makeIcosahedralPatch({ radius: Number(input) });
// Golden.toJSON emits canonical [a,b,d] strings. Six-dimensional integer
// lifts and grid levels are strings too, never lossy JSON numeric values.
console.log(JSON.stringify(patch, (_, value) => typeof value === "bigint" ? String(value) : value, 2));
