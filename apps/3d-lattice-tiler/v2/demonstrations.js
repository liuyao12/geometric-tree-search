// Measured presets only. No labels, patches or learned assignments are bundled.
export const DEMONSTRATIONS=[
  {
    "tile": "a2_hat_prism",
    "name": "Hat slab",
    "winningModes": [
      {
        "mode": "gcts",
        "minimumRatio": 26.68062656338685,
        "seconds": [
          3.451322125999999,
          3.52682112399998,
          4.4976455000001
        ]
      },
      {
        "mode": "both",
        "minimumRatio": 7.967397233643722,
        "seconds": [
          7.755187000000006,
          4.561628958000044,
          15.06138033299998
        ]
      }
    ],
    "summary": "Fixed-window preset: radius 18, reflections, tile-point marking. Cold GCTS completed all three seeds in 3.5\u20134.5s; at least 26.6\u00d7 faster than fixed-window free-range under the 120s limit."
  }
];
export function demonstrationConfig(tile){
 if(!DEMONSTRATIONS.some(d=>d.tile===tile))throw Error('No measured demonstration for this tile');
 return {tile,radius:18,mirrors:true,seed:1,timeMs:120000,nodes:1000000,pairNodes:500,markingExtent:0};
}
