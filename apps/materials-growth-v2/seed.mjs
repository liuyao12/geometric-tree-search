export function centralSeed(atoms) {
  if (!atoms.length) throw Error("Empty observation");
  const center = [0, 1, 2].map(
    (k) => atoms.reduce((n, a) => n + a.position[k], 0) / atoms.length,
  );
  let index = 0;
  for (let i = 1; i < atoms.length; i++)
    if (
      Math.hypot(...atoms[i].position.map((v, k) => v - center[k])) <
      Math.hypot(...atoms[index].position.map((v, k) => v - center[k])) - 1e-10
    )
      index = i;
  return {
    index,
    origin: [...atoms[index].position],
    atom: { species: atoms[index].species, position: [0, 0, 0] },
  };
}
