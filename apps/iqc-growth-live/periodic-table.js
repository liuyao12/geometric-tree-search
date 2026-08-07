const rows = [
  [["H", 1], ["He", 18]],
  [["Li", 1], ["Be", 2], ["B", 13], ["C", 14], ["N", 15], ["O", 16], ["F", 17], ["Ne", 18]],
  [["Na", 1], ["Mg", 2], ["Al", 13], ["Si", 14], ["P", 15], ["S", 16], ["Cl", 17], ["Ar", 18]],
  ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"].map((symbol, index) => [symbol, index + 1]),
  ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"].map((symbol, index) => [symbol, index + 1]),
  [["Cs", 1], ["Ba", 2], ["Hf", 4], ["Ta", 5], ["W", 6], ["Re", 7], ["Os", 8], ["Ir", 9], ["Pt", 10], ["Au", 11], ["Hg", 12], ["Tl", 13], ["Pb", 14], ["Bi", 15], ["Po", 16], ["At", 17], ["Rn", 18]],
  [["Fr", 1], ["Ra", 2], ["Rf", 4], ["Db", 5], ["Sg", 6], ["Bh", 7], ["Hs", 8], ["Mt", 9], ["Ds", 10], ["Rg", 11], ["Cn", 12], ["Nh", 13], ["Fl", 14], ["Mc", 15], ["Lv", 16], ["Ts", 17], ["Og", 18]],
  ["La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"].map((symbol, index) => [symbol, index + 3]),
  ["Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"].map((symbol, index) => [symbol, index + 3]),
];

const atomicOrder = "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split(" ");
const categorySets = {
  alkali: new Set("Li Na K Rb Cs Fr".split(" ")),
  alkaline: new Set("Be Mg Ca Sr Ba Ra".split(" ")),
  metalloid: new Set("B Si Ge As Sb Te Po".split(" ")),
  nonmetal: new Set("H C N O P S Se".split(" ")),
  halogen: new Set("F Cl Br I At Ts".split(" ")),
  noble: new Set("He Ne Ar Kr Xe Rn Og".split(" ")),
  lanthanide: new Set("La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu".split(" ")),
  actinide: new Set("Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr".split(" ")),
  post: new Set("Al Ga In Sn Tl Pb Bi Nh Fl Mc Lv".split(" ")),
};

function categoryFor(symbol) {
  for (const [category, members] of Object.entries(categorySets)) if (members.has(symbol)) return category;
  return "transition";
}

const gases = new Set("H He N O F Ne Cl Ar Kr Xe Rn".split(" "));
const liquids = new Set("Br Hg".split(" "));

function phaseFor(symbol) {
  if (gases.has(symbol)) return "gas";
  if (liquids.has(symbol)) return "liquid";
  return "solid";
}

export const PERIODIC_ELEMENTS = rows.flatMap((row, rowIndex) => row.map(([symbol, column]) => ({
  symbol,
  atomicNumber: atomicOrder.indexOf(symbol) + 1,
  row: rowIndex + 1,
  column,
  category: categoryFor(symbol),
  phase: phaseFor(symbol),
})));
