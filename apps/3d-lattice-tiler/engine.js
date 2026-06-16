// Ported from https://observablehq.com/@liuyao12/3d-lattice-tiler
// This module removes Observable runtime wrappers; app-level rendering lives in app.js.

export const createTilingStream = (() => {
  return async function* createTilingStream(config, tileSpecs, stopToken) {
    const SCALE = tileSpecs.SCALE;
    const COLOR_PALETTE = tileSpecs.COLOR_PALETTE;

    const tick = () => new Promise(resolve => {
      if (typeof requestAnimationFrame === "function") requestAnimationFrame(resolve);
      else setTimeout(resolve, 0);
    });
    const uiYieldIntervalMs = Math.max(8, +config.ui_yield_interval_ms || 24);
    let lastUiYield = performance.now();
    const yieldToBrowser = async (force = false) => {
      if (stopToken.stop) return;
      const now = performance.now();
      if (!force && now - lastUiYield < uiYieldIntervalMs) return;
      lastUiYield = now;
      await tick();
    };

    const treeTileName = (rawName) => tileSpecs.displayTileName?.(rawName) ?? String(rawName ?? "Tile");

    const keyFace = (verts) => {
      const s = [...verts].map(v => v.join(",")).sort();
      return s.join("|");
    };

    const faceSignature = (verts) => {
      const n = verts.length;
      const edges = [];
      for (let i = 0; i < n; i++) {
        const a = verts[i], b = verts[(i + 1) % n];
        edges.push([b[0] - a[0], b[1] - a[1], b[2] - a[2]]);
      }
      const lengths = edges.map(e => e[0] * e[0] + e[1] * e[1] + e[2] * e[2]);
      const dots = edges.map((e, i) => {
        const f = edges[(i + 1) % n];
        return e[0] * f[0] + e[1] * f[1] + e[2] * f[2];
      });
      const combined = lengths.map((L, i) => [L, dots[i]]);
      const rotate = (arr, k) => arr.slice(k).concat(arr.slice(0, k));
      let best = combined;
      for (let k = 1; k < n; k++) {
        const r = rotate(combined, k);
        let better = false;
        for (let i = 0; i < n; i++) {
          if (r[i][0] !== best[i][0]) { better = r[i][0] < best[i][0]; break; }
          if (r[i][1] !== best[i][1]) { better = r[i][1] < best[i][1]; break; }
        }
        if (better) best = r;
      }
      return best.map(p => `${p[0]},${p[1]}`).join("|");
    };

    const faceSignatureUndirected = (verts) => {
      const a = faceSignature(verts);
      const b = faceSignature([...verts].slice().reverse());
      return (a < b) ? a : b;
    };

    const isCyclicPermutation = (a, b) => {
      if (a.length !== b.length) return false;
      const n = a.length;
      const a0 = a[0].join(",");
      let start = -1;
      for (let i = 0; i < n; i++) if (b[i].join(",") === a0) { start = i; break; }
      if (start < 0) return false;
      for (let i = 0; i < n; i++) {
        const ai = a[i], bi = b[(start + i) % n];
        if (ai[0] !== bi[0] || ai[1] !== bi[1] || ai[2] !== bi[2]) return false;
      }
      return true;
    };

    const add3 = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const gcd = (a, b) => {
      a = Math.abs(a | 0); b = Math.abs(b | 0);
      while (b) [a, b] = [b, a % b];
      return a || 1;
    };
    // --- Build Prototiles First (to ensure correct order and cache key) ---
    const { mode_key } = config;
    const includeMirrors = !!config.include_mirrors;
    const modeDef = config.custom_system
      ? tileSpecs.buildCustomSystem(config.custom_system)
      : tileSpecs.TILING_REGISTRY[mode_key];
    if (!modeDef) throw new Error(`Unknown mode_key: ${mode_key}`);

    const baseTiles = modeDef.build();
    const prototiles = (() => {
      const out = [];
      for (const t of baseTiles) {
        out.push(t);
        if (includeMirrors && t.is_chiral) {
          const m = t.get_mirror_copy?.();
          if (m) {
            if (t.name.startsWith("reflected ")) {
              m.name = t.name.substring(10);
            } else {
              m.name = `reflected ${t.name}`;
            }
            m.__is_mirror = true;
            out.push(m);
          }
        }
      }
      return out;
    })();
    prototiles.forEach((tile, prototileIndex) => {
      tile.unique_orientations?.forEach((orient, orientIndex) => {
        orient.__orientation_id = `${prototileIndex}:${orientIndex}`;
      });
    });

    const affineRank = (verts) => {
      if (!verts?.length) return 0;
      const base = verts[0];
      const diffs = verts.slice(1).map(v => [v[0] - base[0], v[1] - base[1], v[2] - base[2]]).filter(v => v.some(Boolean));
      if (!diffs.length) return 0;
      const first = diffs[0];
      const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
      const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
      let normal = null;
      for (const diff of diffs.slice(1)) {
        const c = cross(first, diff);
        if (c.some(Boolean)) { normal = c; break; }
      }
      if (!normal) return 1;
      return diffs.some(diff => dot(normal, diff) !== 0) ? 3 : 2;
    };
    const tilingDimension = Math.max(1, ...prototiles.map(tile => affineRank(tile.verts)));
    const configuredSharedVertices = Number(config.min_shared_vertices);
    const minSharedVertices = Number.isFinite(configuredSharedVertices) && configuredSharedVertices > 0
      ? configuredSharedVertices
      : tilingDimension <= 2 ? 2 : 3;

    const isPolycubeSystem = (modeDef.category ?? []).includes("Polycubes");
    const lcm = (a, b) => Math.abs(a * b) / gcd(a, b);
    const tileAngleMaxima = prototiles.map(tile => Math.max(1, tile.solid_angle?.max_value ?? tileSpecs.LEGACY_SOLID_ANGLE_MAX));
    const MAX_SOLID_ANGLE = tileAngleMaxima.reduce((acc, value) => lcm(acc, value), 1);
    for (const tile of prototiles) tile.rescaleOccupancyWeights?.(MAX_SOLID_ANGLE);
    const protoInfo = prototiles.map(p => {
      return {
        name: p.name,
        verts: p.verts,
        faces: p.faces,
        lattice_points: isPolycubeSystem ? [] : p.occupancy_points.map(o => o.pos),
        solid_angle: p.solid_angle,
        solid_angles: tileSpecs.solidAngleValues?.(p) ?? [],
        is_chiral: !!p.is_chiral,
        is_mirror: !!p.__is_mirror
      };
    });

    let global_center = [0, 0, 0], global_radius = 5;
    const allUnscaled = [];
    protoInfo.forEach(p => p.verts.forEach(v => allUnscaled.push([v[0]/SCALE, v[1]/SCALE, v[2]/SCALE])));
    if (allUnscaled.length) {
      const mins = [Infinity, Infinity, Infinity], maxs = [-Infinity, -Infinity, -Infinity];
      for (const v of allUnscaled) {
        for (let i = 0; i < 3; i++) { mins[i] = Math.min(mins[i], v[i]); maxs[i] = Math.max(maxs[i], v[i]); }
      }
      global_center = [(mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2, (mins[2] + maxs[2]) / 2];
      const dx = maxs[0] - global_center[0], dy = maxs[1] - global_center[1], dz = maxs[2] - global_center[2];
      global_radius = Math.sqrt(dx * dx + dy * dy + dz * dz) || 2;
    }

    yield { type: "palette", colors: COLOR_PALETTE };
    yield {
      type: "prototile_info",
      tiles: protoInfo,
      scale: SCALE,
      global_center,
      global_radius,
      default_opacities: modeDef.default_viz?.opacities ?? [],
      default_internal: !!modeDef.default_viz?.internal
    };

    const state = {
      placements: [],
      frontier: new Map(),
      lattice: new Map(),
      viz_faces: new Map(),
      vertex_candidate_cache: new Map()
    };

    let faceCounter = 0;
    let nodeCounter = 0;
    let stateVersion = 0;
    const nowId = () => (++nodeCounter);
    const searchStats = {
      forced_total: 0,
      branch_choices_visited: 0,
      failed_leaves: 0,
      backtracks: 0,
      max_depth: 0
    };
    const branchStack = [];
    const MAX_PATH_COUNT = 1e12;
    const MAX_PATH_LOG = Math.log(MAX_PATH_COUNT);
    const capCount = (value) => Math.min(MAX_PATH_COUNT, Math.max(0, value));
    const pathCountLabel = (value) => String(Math.max(0, Math.round(value)));
    const logCountLabel = (logValue) => {
      if (!Number.isFinite(logValue)) return "0";
      if (logValue <= MAX_PATH_LOG) return pathCountLabel(Math.exp(logValue));
      const log10 = logValue / Math.LN10;
      let exponent = Math.floor(log10);
      let mantissa = Math.pow(10, log10 - exponent);
      if (mantissa >= 9.95) {
        mantissa = 1;
        exponent += 1;
      }
      return `~${mantissa.toFixed(1)}e${exponent}`;
    };
    const setBranchCursor = (depth, width, nextIndex) => {
      const safeWidth = Math.max(1, width | 0);
      const safeIndex = Math.max(0, Math.min(safeWidth, nextIndex | 0));
      branchStack.length = depth + 1;
      branchStack[depth] = { width: safeWidth, next_index: safeIndex };
      searchStats.max_depth = Math.max(searchStats.max_depth, depth + 1);
    };
    const estimateBranchProgress = () => {
      const active = branchStack.filter(Boolean);
      if (!active.length) {
        const forcedOnlyProgress =
          searchStats.forced_total > 0
          && searchStats.branch_choices_visited === 0
          && searchStats.backtracks === 0
          && searchStats.failed_leaves === 0;
        return {
          depth: 0,
          completed: forcedOnlyProgress ? 1 : 0,
          total: 1,
          percent: forcedOnlyProgress ? 100 : 0,
          completed_label: forcedOnlyProgress ? "1" : "0",
          total_label: "1",
          completed_capped: false,
          total_capped: false,
          widths: [],
          next_indices: []
        };
      }

      let totalLog = 0;
      const suffixProducts = new Array(active.length + 1).fill(1);
      for (let i = active.length - 1; i >= 0; i--) {
        totalLog += Math.log(active[i].width);
        suffixProducts[i] = capCount(suffixProducts[i + 1] * active[i].width);
      }

      let completed = 0;
      let completedFraction = 0;
      let prefixLog = 0;
      for (let i = 0; i < active.length; i++) {
        completed = capCount(completed + active[i].next_index * suffixProducts[i + 1]);
        prefixLog += Math.log(active[i].width);
        if (active[i].next_index > 0) {
          const termLog = Math.log(active[i].next_index) - prefixLog;
          if (termLog > -745) completedFraction += Math.exp(termLog);
        }
      }
      completedFraction = Math.max(0, Math.min(1, completedFraction));
      const total = Math.max(1, Math.round(suffixProducts[0]));
      const roundedCompleted = Math.max(0, Math.min(total, Math.round(completed)));
      const totalCapped = totalLog > MAX_PATH_LOG;
      const completedLog = completedFraction > 0 ? totalLog + Math.log(completedFraction) : -Infinity;
      const completedCapped = completedLog > MAX_PATH_LOG;
      return {
        depth: active.length,
        completed: roundedCompleted,
        total,
        percent: completedFraction >= 1 ? 100 : completedFraction * 100,
        completed_label: completedCapped ? logCountLabel(completedLog) : pathCountLabel(roundedCompleted),
        total_label: totalCapped ? logCountLabel(totalLog) : pathCountLabel(total),
        completed_capped: completedCapped,
        total_capped: totalCapped,
        widths: active.map(item => item.width),
        next_indices: active.map(item => item.next_index)
      };
    };
    const searchStatsSnapshot = () => {
      const forcedOnPath = state.placements.reduce((sum, placement) => sum + (placement.is_forced ? 1 : 0), 0);
      const branchProgress = estimateBranchProgress();
      return {
        ...searchStats,
        forced_on_path: forcedOnPath,
        progress_depth: branchProgress.depth,
        progress_completed_paths: branchProgress.completed,
        progress_total_paths: branchProgress.total,
        progress_completed_paths_label: branchProgress.completed_label,
        progress_total_paths_label: branchProgress.total_label,
        progress_paths_capped: branchProgress.completed_capped || branchProgress.total_capped,
        branch_widths: branchProgress.widths,
        branch_next_indices: branchProgress.next_indices,
        visited_nodes: branchProgress.completed,
        estimated_nodes_at_depth: branchProgress.total,
        visited_percent: branchProgress.percent
      };
    };

    const branchSet = (parent, branches) => ({ type: "branch_set", parent, branches });
    const nodeStatus = (id, status, append_text = "", extra = {}) =>
      ({ type: "node_status", id, status, text: append_text, ...extra });
    const exhaustive = !!config.exhaustive;
    const criterion = config.criterion ?? "count";
    const targetVal = Math.max(1, +config.target_val || 50);
    const rawSnapshotEvery = +config.snapshot_every;
    const snapshotEvery = rawSnapshotEvery <= 0 ? Infinity : Math.max(1, rawSnapshotEvery || 1);
    const placementDetails = !!config.placement_details;
    const shouldSnapshot = (force = false) =>
      force || (Number.isFinite(snapshotEvery) &&
        (snapshotEvery <= 1 || state.placements.length <= 2 || state.placements.length % snapshotEvery === 0));
    let bestSnapshot = null;

    const cloneSnapshot = (snap) => ({
      ...snap,
      frontier_stats: snap.frontier_stats ? { ...snap.frontier_stats } : snap.frontier_stats,
      search_stats: snap.search_stats ? { ...snap.search_stats } : snap.search_stats,
      tile_counts: (snap.tile_counts ?? []).map(item => ({ ...item })),
      placements: (snap.placements ?? []).map(item => ({
        ...item,
        translation: item.translation?.slice()
      })),
      faces: (snap.faces ?? []).map(face => ({
        ...face,
        v: (face.v ?? []).map(vertex => vertex.slice())
      }))
    });

    const isBetterSnapshot = (candidate, current) => {
      if (!current) return true;
      const candidateLayer = candidate.frontier_stats?.min_gen ?? 0;
      const currentLayer = current.frontier_stats?.min_gen ?? 0;
      const candidateTiles = candidate.tile_count ?? 0;
      const currentTiles = current.tile_count ?? 0;
      if (criterion === "layer" && candidateLayer !== currentLayer) return candidateLayer > currentLayer;
      if (candidateTiles !== currentTiles) return candidateTiles > currentTiles;
      return candidateLayer > currentLayer;
    };

    const recordBestSnapshot = (snap) => {
      if (isBetterSnapshot(snap, bestSnapshot)) bestSnapshot = cloneSnapshot(snap);
    };

    const snapshot = (node_id = null) => {
      const faces = [];
      for (const stack of state.viz_faces.values()) for (const f of stack) faces.push(f);
      const countMap = new Map();
      for (const placement of state.placements) {
        const typeIndex = placement.prototile_idx ?? 0;
        const entry = countMap.get(typeIndex) ?? {
          type_idx: typeIndex,
          name: treeTileName(prototiles[typeIndex]?.name),
          color: COLOR_PALETTE[(placement.color_id ?? typeIndex) % COLOR_PALETTE.length],
          count: 0
        };
        entry.count += 1;
        countMap.set(typeIndex, entry);
      }
      const snap = {
        type: "full_update",
        tile_count: state.placements.length,
        tile_counts: [...countMap.values()].sort((a, b) => a.type_idx - b.type_idx),
        faces,
        node_id,
        frontier_stats: calculateFrontierStats(),
        search_stats: searchStatsSnapshot()
      };
      if (placementDetails) {
        snap.placements = state.placements.map((placement, index) => ({
          index,
          prototile_idx: placement.prototile_idx ?? 0,
          name: treeTileName(prototiles[placement.prototile_idx ?? 0]?.name),
          translation: placement.translation?.slice() ?? [0, 0, 0],
          orientation_id: placement.orient?.__orientation_id ?? null,
          is_forced: !!placement.is_forced
        }));
      }
      recordBestSnapshot(snap);
      return snap;
    };
    const nodeSnapshot = (node_id) => ({ type: "node_snapshot", node_id, snapshot: snapshot(node_id) });

    const latticeGet = (pos) => state.lattice.get(pos.join(",")) ?? 0;
    const latticeAdd = (pos, w) => {
      const k = pos.join(",");
      state.lattice.set(k, (state.lattice.get(k) ?? 0) + w);
      if (state.lattice.get(k) <= 0) state.lattice.delete(k);
    };

    const candidateCachePointKey = (cacheKey) => cacheKey.split("::", 1)[0];
    let candidateInfluenceOffsets = null;
    const candidateInfluenceOffsetKeys = () => {
      if (candidateInfluenceOffsets) return candidateInfluenceOffsets;
      const offsets = new Set(["0,0,0"]);
      for (const tile of prototiles) {
        for (const orient of tile.unique_orientations) {
          for (const anchor of orient.occupancy) {
            for (const occ of orient.occupancy) {
              offsets.add([
                anchor.pos[0] - occ.pos[0],
                anchor.pos[1] - occ.pos[1],
                anchor.pos[2] - occ.pos[2]
              ].join(","));
            }
          }
        }
      }
      candidateInfluenceOffsets = [...offsets].map(key => key.split(",").map(Number));
      return candidateInfluenceOffsets;
    };
    const candidateInfluencePointKeys = (positions) => {
      if (!positions?.length) return null;
      const keys = new Set();
      const offsets = candidateInfluenceOffsetKeys();
      for (const pos of positions) {
        for (const offset of offsets) {
          keys.add([pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2]].join(","));
        }
      }
      return keys;
    };
    const invalidateCandidateCaches = (changedPositions = null) => {
      const affectedPointKeys = candidateInfluencePointKeys(changedPositions);
      if (!affectedPointKeys) {
        state.vertex_candidate_cache.clear();
        return;
      }
      for (const cacheKey of state.vertex_candidate_cache.keys()) {
        if (affectedPointKeys.has(candidateCachePointKey(cacheKey))) state.vertex_candidate_cache.delete(cacheKey);
      }
    };

    const isMoveValid = (move) => {
      const { orient, translation } = move;
      for (const pt of orient.occupancy) {
        const g = add3(pt.pos, translation);
        if (latticeGet(g) + pt.weight > MAX_SOLID_ANGLE) return { ok: false };
      }
      const gVerts = orient.verts.map(v => add3(v, translation));
      for (let f_idx = 0; f_idx < orient.faces.length; f_idx++) {
        const fIdx = orient.faces[f_idx];
        const poly = fIdx.map(i => gVerts[i]);
        const k = keyFace(poly);
          const existing = state.frontier.get(k);
        if (existing) {
          const rev = [...existing.ordered_verts].slice().reverse();
          if (!isCyclicPermutation(poly, rev)) return { ok: false };
        }
      }
      const occData = orient.occupancy.map(pt => ({ pos: add3(pt.pos, translation), weight: pt.weight }));
      return { ok: true, occData };
    };

    const sharedFrontierPoints = (move) => {
      if (move._shared_frontier_points && move._shared_frontier_version === stateVersion) return move._shared_frontier_points;
      const points = new Map();
      for (const pt of move.orient.occupancy) {
        const g = add3(pt.pos, move.translation);
        if (latticeGet(g) > 0) points.set(vecKey(g), g);
      }
      const out = [...points.values()];
      move._shared_frontier_points = out;
      move._shared_frontier_version = stateVersion;
      return out;
    };
    const candidateTouchesPoint = (move, pointKey) => {
      for (const pt of move.orient.occupancy) {
        const g = add3(pt.pos, move.translation);
        if (vecKey(g) === pointKey) return true;
      }
      return false;
    };
    const placementGeometryKey = (move) => {
      const vertsKey = move.orient.verts
        .map(vertex => vecKey(add3(vertex, move.translation)))
        .sort()
        .join("|");
      return `${move.prototile_idx}::${vertsKey}`;
    };
    // Polycubes use ordinary Z^3 vertex samples by default. The optional
    // D3 frontier mode adds face-center samples, but legal polycube moves
    // still remain translations of the original cube-vertex lattice.
    const isPolycubeMoveTranslation = (tile, translation) => {
      if (!translation.every(Number.isInteger)) return false;
      return tile.polycube_lattice === "d3" ? translation.every(value => value % 2 === 0) : true;
    };
    const checkMoveViability = (move) => {
      const validCheck = isMoveValid(move);
      if (!validCheck.ok) return null;
      if (!validCheck.occData.some(o => latticeGet(o.pos) === 0)) return null;
      const sharedPoints = sharedFrontierPoints(move);
      if (sharedPoints.length < minSharedVertices) return null;
      if (tilingDimension >= 3 && affineRank(sharedPoints) < 2) return null;
      return validCheck;
    };

    const applyMove = (move) => {
      state.placements.push(move);
      stateVersion += 1;
      const changedOccupancyPositions = move.occupancy_data.map(o => o.pos);
      for (const o of move.occupancy_data) latticeAdd(o.pos, o.weight);

      const gVerts = move.orient.verts.map(v => add3(v, move.translation));
      const neighborColors = new Set();
      const coveredGens = [];
      for (const fIdx of move.orient.faces) {
        const poly = fIdx.map(i => gVerts[i]);
        const k = keyFace(poly);
        if (state.frontier.has(k)) {
          neighborColors.add(state.frontier.get(k).color_id);
          coveredGens.push(state.frontier.get(k).gen);
        }
      }
      const newGen = coveredGens.length ? (Math.min(...coveredGens) + 1) : 0;
      const available = COLOR_PALETTE.map((_, i) => i).filter(i => !neighborColors.has(i));
      move.color_id = available.length ? available[Math.floor(Math.random() * available.length)] : 0;

      const added = [], removed = [], modified_gens = [];

      for (let f_idx = 0; f_idx < move.orient.faces.length; f_idx++) {
        const fIdx = move.orient.faces[f_idx];
        const poly = fIdx.map(i => gVerts[i]);
        const k = keyFace(poly);
        if (state.frontier.has(k)) {
          removed.push([k, state.frontier.get(k)]);
          state.frontier.delete(k);
          if (!state.viz_faces.has(k)) state.viz_faces.set(k, []);
          state.viz_faces.get(k).push({ v: poly, color: COLOR_PALETTE[move.color_id], internal: true, type_idx: move.prototile_idx });
          for (const vf of state.viz_faces.get(k)) vf.internal = true;
        } else {
          faceCounter += 1;
          state.frontier.set(k, { type: move.prototile_idx, face_idx: f_idx, ordered_verts: poly, color_id: move.color_id, id: faceCounter, gen: newGen });
          added.push(k);
          const viz = { v: poly, color: COLOR_PALETTE[move.color_id], internal: false, type_idx: move.prototile_idx };
          if (!state.viz_faces.has(k)) state.viz_faces.set(k, []);
          state.viz_faces.get(k).push(viz);
        }
      }

      invalidateCandidateCaches(changedOccupancyPositions);

      if (added.length) {
        const activeVerts = new Set();
        for (const k of added) for (const v of state.frontier.get(k).ordered_verts) activeVerts.add(v.join(","));
        const vertToKeys = new Map();
        for (const [k, entry] of state.frontier.entries()) {
          for (const v of entry.ordered_verts) {
            const kk = v.join(",");
            if (activeVerts.has(kk)) { if (!vertToKeys.has(kk)) vertToKeys.set(kk, []); vertToKeys.get(kk).push(k); }
          }
        }
        const q = [...added];
        while (q.length) {
          const curr = q.shift();
          const ce = state.frontier.get(curr);
          if (!ce) continue;
          for (const v of ce.ordered_verts) {
            for (const nk of (vertToKeys.get(v.join(",")) ?? [])) {
              if (nk === curr) continue;
              const ne = state.frontier.get(nk);
              if (ne && ne.gen > ce.gen + 1) { modified_gens.push([nk, ne.gen]); ne.gen = ce.gen + 1; q.push(nk); }
            }
          }
        }
      }
      return { added, removed, modified_gens };
    };

    const undoMove = (move, rb) => {
      for (const [k, oldGen] of (rb.modified_gens ?? [])) { const e = state.frontier.get(k); if(e) e.gen = oldGen; }
      const changedOccupancyPositions = move.occupancy_data.map(o => o.pos);
      for (const [k, val] of rb.removed) {
        state.frontier.set(k, val);
        const stack = state.viz_faces.get(k);
        if (stack) { stack.pop(); if (stack.length === 1) stack[0].internal = false; if (stack.length === 0) state.viz_faces.delete(k); }
      }
      invalidateCandidateCaches(changedOccupancyPositions);
      for (const k of rb.added) {
        state.frontier.delete(k);
        const stack = state.viz_faces.get(k);
        if (stack) { stack.pop(); if (stack.length === 0) state.viz_faces.delete(k); }
      }
      for (const o of move.occupancy_data) latticeAdd(o.pos, -o.weight);
      state.placements.pop();
      stateVersion += 1;
    };

    const p0 = prototiles[0];
    const startOrient = p0.unique_orientations[0];
    const startTrans = [-startOrient.verts[0][0], -startOrient.verts[0][1], -startOrient.verts[0][2]];
    const startOcc = startOrient.occupancy.map(pt => ({ pos: add3(pt.pos, startTrans), weight: pt.weight }));

    const frontierPointStats = () => {
      let pointCount = 0;
      for (const weight of state.lattice.values()) {
        if (weight > 0 && weight < MAX_SOLID_ANGLE) pointCount += 1;
      }
      return { point_count: pointCount };
    };
    const calculateFrontierStats = () => {
      let minGen = Infinity, minGenCount = 0;
      for (const v of state.frontier.values()) {
        if (v.gen < minGen) { minGen = v.gen; minGenCount = 1; }
        else if (v.gen === minGen) minGenCount++;
      }
      return { min_gen: minGen === Infinity ? 0 : minGen, count: minGenCount, total_faces: state.frontier.size, ...frontierPointStats() };
    };

    const startMove = { prototile_idx: 0, translation: startTrans, occupancy_data: startOcc, orient: startOrient, color_id: 0 };
    state.placements.push(startMove);
    for (const o of startMove.occupancy_data) latticeAdd(o.pos, o.weight);

    const gVerts0 = startOrient.verts.map(v => add3(v, startTrans));
    for (let f_idx = 0; f_idx < startOrient.faces.length; f_idx++) {
      const fIdx = startOrient.faces[f_idx];
      const poly = fIdx.map(i => gVerts0[i]);
      const k = keyFace(poly);
      faceCounter += 1;
      state.frontier.set(k, { type: 0, face_idx: f_idx, ordered_verts: poly, color_id: 0, id: faceCounter, gen: 0 });
      state.viz_faces.set(k, [{ v: poly, color: COLOR_PALETTE[0], internal: false, type_idx: 0 }]);
    }
    
    const rootId = nowId();
    const rootStats = calculateFrontierStats();
    yield branchSet(null, [{ id: rootId, text: treeTileName(p0.name), frontier_stats: rootStats }]);
    yield nodeStatus(rootId, "working", "", { color_id: 0, frontier_stats: rootStats });
    yield snapshot(rootId);
    await tick();

    const branchCap = Math.max(1, +config.branch_cap || Infinity);
    const nodeLimit = Math.max(1, +config.node_limit || Infinity);
    const candidateCap = Math.max(1, +config.candidate_cap || Infinity);
    const timeLimitMs = Math.max(1, +config.time_limit_ms || Infinity);
    const moveOrder = config.move_order ?? "coverage";
    const faceOrder = config.face_order ?? "coverage";
    const branchDetails = !!config.branch_details;
    const startedAt = performance.now();
    const safetyMax = 2000;
    const overNodeLimit = () => Number.isFinite(nodeLimit) && nodeCounter >= nodeLimit;
    const overTimeLimit = () => Number.isFinite(timeLimitMs) && performance.now() - startedAt >= timeLimitMs;
    const overBudget = () => overNodeLimit() || overTimeLimit();
    const budgetText = () => overNodeLimit() ? "Node limit" : "Time limit";
    const goalMet = () => {
      if (criterion === "count") return state.placements.length >= targetVal;
      if (criterion === "layer") return calculateFrontierStats().min_gen >= targetVal;
      return false;
    };

    const moveCoverage = (m) => {
      if (m._coverage != null && m._coverage_version === stateVersion) return m._coverage;
      const shared = sharedFrontierPoints(m);
      const coverage = shared.reduce((sum, point) => sum + Math.min(MAX_SOLID_ANGLE, latticeGet(point)) / MAX_SOLID_ANGLE, 0);
      m._coverage = coverage;
      m._coverage_version = stateVersion;
      return coverage;
    };
    const rootOrientations = prototiles.map(t => t.unique_orientations?.[0] ?? null);
    const sameRootOrientation = (move) => move.orient === rootOrientations[move.prototile_idx] ? 1 : 0;
    const vecSub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
    const vecNeg = (a) => [-a[0], -a[1], -a[2]];
    const vecAdd = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const vecEq = (a, b) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
    const vecKey = (a) => a.join(",");
    const placementFrame = (placement) => `${placement.prototile_idx}::${placement.orient.__orientation_id ?? ""}`;
    let translationCacheVersion = -1;
    let translationCache = new Map();
    const observedTranslations = () => {
      if (translationCacheVersion === stateVersion) return translationCache;
      const byFrame = new Map();
      const out = new Map();
      for (const placement of state.placements) {
        const frame = placementFrame(placement);
        if (!byFrame.has(frame)) byFrame.set(frame, []);
        byFrame.get(frame).push(placement.translation);
      }
      for (const [frame, translations] of byFrame.entries()) {
        const vectors = new Set();
        for (let i = 0; i < translations.length; i++) {
          for (let j = i + 1; j < translations.length; j++) {
            const v = vecSub(translations[j], translations[i]);
            vectors.add(vecKey(v));
            vectors.add(vecKey(vecNeg(v)));
          }
        }
        out.set(frame, vectors);
      }
      translationCacheVersion = stateVersion;
      translationCache = out;
      return translationCache;
    };
    let pairTranslationCacheVersion = -1;
    let pairTranslationCache = new Map();
    let vectorCountCacheVersion = -1;
    let vectorCountCache = new Map();
    let positionSetCacheVersion = -1;
    let positionSetCache = new Set();
    let vertexSetCacheVersion = -1;
    let vertexSetCache = new Set();
    const observedPairTranslations = () => {
      if (pairTranslationCacheVersion === stateVersion) return pairTranslationCache;
      const out = new Map();
      for (let i = 0; i < state.placements.length; i++) {
        const a = state.placements[i];
        const aFrame = placementFrame(a);
        for (let j = 0; j < state.placements.length; j++) {
          if (i === j) continue;
          const b = state.placements[j];
          const key = `${aFrame}=>${placementFrame(b)}`;
          if (!out.has(key)) out.set(key, new Set());
          out.get(key).add(vecKey(vecSub(b.translation, a.translation)));
        }
      }
      pairTranslationCacheVersion = stateVersion;
      pairTranslationCache = out;
      return pairTranslationCache;
    };
    const observedVectorCounts = () => {
      if (vectorCountCacheVersion === stateVersion) return vectorCountCache;
      const out = new Map();
      for (let i = 0; i < state.placements.length; i++) {
        for (let j = 0; j < state.placements.length; j++) {
          if (i === j) continue;
          const key = vecKey(vecSub(state.placements[j].translation, state.placements[i].translation));
          out.set(key, (out.get(key) ?? 0) + 1);
        }
      }
      vectorCountCacheVersion = stateVersion;
      vectorCountCache = out;
      return vectorCountCache;
    };
    const placementPositionSet = () => {
      if (positionSetCacheVersion === stateVersion) return positionSetCache;
      positionSetCache = new Set(state.placements.map(placement => vecKey(placement.translation)));
      positionSetCacheVersion = stateVersion;
      return positionSetCache;
    };
    const placementVertexSet = () => {
      if (vertexSetCacheVersion === stateVersion) return vertexSetCache;
      const vertices = new Set();
      for (const placement of state.placements) {
        for (const vertex of placement.orient.verts) vertices.add(vecKey(vecAdd(vertex, placement.translation)));
      }
      vertexSetCache = vertices;
      vertexSetCacheVersion = stateVersion;
      return vertexSetCache;
    };
    const sharedVertexCount = (move) => {
      if (move._shared_vertex_count != null && move._shared_vertex_version === stateVersion) return move._shared_vertex_count;
      const existingVertices = placementVertexSet();
      const count = move.orient.verts.reduce((sum, vertex) => sum + (existingVertices.has(vecKey(vecAdd(vertex, move.translation))) ? 1 : 0), 0);
      move._shared_vertex_count = count;
      move._shared_vertex_version = stateVersion;
      return count;
    };
    const periodicContinuation = (move) => {
      const frame = placementFrame(move);
      const seen = observedTranslations().get(frame);
      if (!seen?.size) return 0;
      for (const placement of state.placements) {
        if (placement.prototile_idx !== move.prototile_idx || placement.orient !== move.orient) continue;
        if (seen.has(vecKey(vecSub(move.translation, placement.translation)))) return 1;
      }
      return 0;
    };
    const pairPeriodicContinuation = (move) => {
      const targetFrame = placementFrame(move);
      const pairs = observedPairTranslations();
      if (!pairs.size) return 0;
      const hits = new Set();
      for (const placement of state.placements) {
        const key = `${placementFrame(placement)}=>${targetFrame}`;
        const seen = pairs.get(key);
        if (!seen?.size) continue;
        const delta = vecKey(vecSub(move.translation, placement.translation));
        if (seen.has(delta)) hits.add(`${key}::${delta}`);
      }
      return hits.size;
    };
    const vectorRepeatScore = (move) => {
      const counts = observedVectorCounts();
      if (!counts.size) return 0;
      const hits = new Set();
      for (const placement of state.placements) {
        const delta = vecKey(vecSub(move.translation, placement.translation));
        if (counts.has(delta)) hits.add(delta);
      }
      return hits.size;
    };
    const parallelogramCompletionScore = (move) => {
      const positions = placementPositionSet();
      if (positions.size < 3) return 0;
      const translations = state.placements.map(placement => placement.translation);
      const hits = new Set();
      for (let i = 0; i < translations.length; i++) {
        for (let j = i + 1; j < translations.length; j++) {
          const fourth = vecSub(vecAdd(translations[i], translations[j]), move.translation);
          const fourthKey = vecKey(fourth);
          if (!positions.has(fourthKey)) continue;
          const key = [
            vecKey(translations[i]),
            vecKey(translations[j]),
            fourthKey
          ].sort().join("|");
          hits.add(key);
        }
      }
      return hits.size;
    };
    const axisNormalForFace = (verts) => {
      if (!verts || verts.length < 3) return null;
      const p0 = verts[0];
      for (let i = 1; i < verts.length - 1; i++) {
        const a = vecSub(verts[i], p0);
        const b = vecSub(verts[i + 1], p0);
        const cross = [
          a[1] * b[2] - a[2] * b[1],
          a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0]
        ];
        const abs = cross.map(Math.abs);
        const axis = abs.indexOf(Math.max(...abs));
        if (!abs[axis]) continue;
        if (abs.some((value, idx) => idx !== axis && value !== 0)) return null;
        const normal = [0, 0, 0];
        normal[axis] = Math.sign(cross[axis]);
        return normal;
      }
      return null;
    };
    const faceCenter = (verts) => {
      const center = [0, 0, 0];
      for (const v of verts) for (let i = 0; i < 3; i++) center[i] += v[i];
      for (let i = 0; i < 3; i++) {
        center[i] /= verts.length;
        if (Math.abs(center[i] - Math.round(center[i])) > 1e-9) return null;
        center[i] = Math.round(center[i]);
      }
      return center;
    };
    const neighborCellDirs = [
      [2, 0, 0], [-2, 0, 0],
      [0, 2, 0], [0, -2, 0],
      [0, 0, 2], [0, 0, -2]
    ];
    const facePocketInfo = (faceKey) => {
      const entry = state.frontier.get(faceKey);
      if (!entry) return { score: 0, weight: 0 };
      const normal = axisNormalForFace(entry.ordered_verts);
      const center = faceCenter(entry.ordered_verts);
      if (!normal || !center) return { score: 0, weight: 0 };
      const plus = vecAdd(center, normal);
      const minus = vecSub(center, normal);
      const plusWeight = latticeGet(plus);
      const minusWeight = latticeGet(minus);
      const outsideDir = plusWeight <= minusWeight ? normal : vecNeg(normal);
      const outside = vecAdd(center, outsideDir);
      const insideStep = vecNeg(outsideDir).map(n => n * 2);
      let score = 0;
      let weight = 0;
      for (const dir of neighborCellDirs) {
        if (vecEq(dir, insideStep)) continue;
        const neighborWeight = latticeGet(vecAdd(outside, dir));
        if (neighborWeight > 0) {
          score += 1;
          weight += Math.min(MAX_SOLID_ANGLE, neighborWeight) / MAX_SOLID_ANGLE;
        }
      }
      return { score, weight, outside };
    };
    const reflectedFeatureKey = (feature, centerSums, axes) => {
      const center = feature.center.slice();
      const normal = feature.normal.slice();
      for (const axis of axes) {
        center[axis] = centerSums[axis] - center[axis];
        normal[axis] = -normal[axis];
      }
      return `${center.join(",")}::${normal.join(",")}`;
    };
    const frontierSymmetryInfo = () => {
      const features = [];
      const mins = [Infinity, Infinity, Infinity];
      const maxs = [-Infinity, -Infinity, -Infinity];
      for (const entry of state.frontier.values()) {
        const center = faceCenter(entry.ordered_verts);
        if (!center) continue;
        const normal = axisNormalForFace(entry.ordered_verts);
        if (!normal) continue;
        const pocket = facePocketInfo(keyFace(entry.ordered_verts));
        const feature = { center, normal: pocket.outside ? vecSub(pocket.outside, center) : normal };
        features.push(feature);
        for (let i = 0; i < 3; i++) {
          mins[i] = Math.min(mins[i], center[i]);
          maxs[i] = Math.max(maxs[i], center[i]);
        }
      }
      if (!features.length) return { score: 0, best_ratio: 0, average_ratio: 0, balance: 0, face_count: 0 };
      const centerSums = mins.map((min, i) => min + maxs[i]);
      const keys = new Set(features.map(feature => `${feature.center.join(",")}::${feature.normal.join(",")}`));
      const transforms = [[0], [1], [2], [0, 1, 2]];
      const ratios = transforms.map(axes => {
        let paired = 0;
        for (const feature of features) {
          if (keys.has(reflectedFeatureKey(feature, centerSums, axes))) paired += 1;
        }
        return paired / features.length;
      });
      const spans = maxs.map((max, i) => max - mins[i]);
      const maxSpan = Math.max(...spans, 1);
      const minSpan = Math.min(...spans);
      const balance = minSpan / maxSpan;
      const bestRatio = Math.max(...ratios);
      const averageRatio = ratios.reduce((sum, value) => sum + value, 0) / ratios.length;
      return {
        score: bestRatio + 0.25 * averageRatio + 0.1 * balance,
        best_ratio: bestRatio,
        average_ratio: averageRatio,
        balance,
        face_count: features.length
      };
    };
    const previewMoveStats = (move) => {
      const rb = applyMove(move);
      const stats = calculateFrontierStats();
      undoMove(move, rb);
      return stats;
    };
    const previewMoveSymmetry = (move) => {
      if (move._symmetry_info) return move._symmetry_info;
      const rb = applyMove(move);
      const info = frontierSymmetryInfo();
      undoMove(move, rb);
      move._symmetry_info = info;
      return info;
    };
    const moveScore = (move) => {
      const coverage = moveCoverage(move);
      const repeat = () => sameRootOrientation(move);
      const periodic = () => periodicContinuation(move);
      const pairPeriodic = () => pairPeriodicContinuation(move);
      const vectorRepeat = () => vectorRepeatScore(move);
      const parallelogram = () => parallelogramCompletionScore(move);
      if (moveOrder === "symmetric") {
        const symmetry = previewMoveSymmetry(move);
        return [
          symmetry.score,
          symmetry.best_ratio,
          symmetry.balance,
          periodic(),
          repeat(),
          coverage
        ];
      }
      if (moveOrder === "crystal") return [
        parallelogram(),
        vectorRepeat(),
        pairPeriodic(),
        periodic(),
        repeat(),
        coverage
      ];
      if (moveOrder === "periodic") return [periodic(), repeat(), coverage];
      if (moveOrder === "repeat") return [repeat(), coverage];
      if (moveOrder === "layer" || moveOrder === "balanced") {
        if (!move._preview_stats) move._preview_stats = previewMoveStats(move);
        const stats = move._preview_stats;
        const symmetry = moveOrder === "balanced" ? previewMoveSymmetry(move) : null;
        return [
          stats.min_gen,
          -stats.count,
          -(stats.point_count ?? stats.count ?? 0),
          moveOrder === "balanced" ? symmetry.score : 0,
          moveOrder === "balanced" ? symmetry.best_ratio : 0,
          moveOrder === "balanced" ? repeat() : 0,
          moveOrder === "balanced" ? pairPeriodic() : 0,
          moveOrder === "balanced" ? periodic() : 0,
          coverage
        ];
      }
      return [coverage, repeat()];
    };
    const compareMoves = (a, b) => {
      const as = moveScore(a);
      const bs = moveScore(b);
      for (let i = 0; i < Math.max(as.length, bs.length); i++) {
        const diff = (bs[i] ?? 0) - (as[i] ?? 0);
        if (diff) return diff;
      }
      return 0;
    };
    const isBetterScore = (candidate, current) => {
      if (!current) return true;
      for (let i = 0; i < Math.max(candidate.length, current.length); i++) {
        const diff = (candidate[i] ?? 0) - (current[i] ?? 0);
        if (diff) return diff > 0;
      }
      return false;
    };
    const describeMove = (move) => branchDetails ? {
      prototile_idx: move.prototile_idx,
      translation: move.translation,
      coverage: moveCoverage(move),
      same_root_orientation: sameRootOrientation(move),
      periodic_continuation: periodicContinuation(move),
      pair_periodic_continuation: pairPeriodicContinuation(move),
      vector_repeat: vectorRepeatScore(move),
      parallelogram_completion: parallelogramCompletionScore(move),
      target_face_pocket: move._target_face_pocket ?? null,
      symmetry: move._symmetry_info ?? null,
      score: moveScore(move),
      preview_frontier_stats: move._preview_stats ?? null
    } : {};

    const cellCoord = (pos) => {
      const out = pos.map(value => (value - 1) / 2);
      return out.every(Number.isInteger) ? out : null;
    };
    const modulo = (value, size) => ((value % size) + size) % size;
    const polycubeSeedData = () => {
      if (prototiles.length !== 1) return null;
      const tile = prototiles[0];
      const shapes = [];
      const minPeriod = [1, 1, 1];
      for (let orientIndex = 0; orientIndex < tile.unique_orientations.length; orientIndex++) {
        const orient = tile.unique_orientations[orientIndex];
        const start = orient.verts[0].map(value => -value);
        const cells = [];
        for (const pt of orient.occupancy) {
          if (pt.weight !== MAX_SOLID_ANGLE) continue;
          const shifted = add3(pt.pos, start);
          const c = cellCoord(shifted);
          if (!c) return null;
          cells.push(c);
        }
        const unique = new Set(cells.map(vecKey));
        if (!cells.length || unique.size !== cells.length) return null;
        for (let axis = 0; axis < 3; axis++) {
          const values = cells.map(c => c[axis]);
          minPeriod[axis] = Math.max(minPeriod[axis], Math.max(...values) - Math.min(...values) + 1);
        }
        shapes.push({ orientIndex, orient, start, cells });
      }
      const rootCellCount = shapes[0]?.cells.length ?? 0;
      if (!rootCellCount || rootCellCount > 30) return null;
      return { shapes, cellCount: rootCellCount, minPeriod };
    };
    const torusPlacementCells = (shape, shift, dims) => {
      const out = [];
      const seen = new Set();
      for (const cell of shape.cells) {
        const wrapped = [
          modulo(cell[0] + shift[0], dims[0]),
          modulo(cell[1] + shift[1], dims[1]),
          modulo(cell[2] + shift[2], dims[2])
        ];
        const key = vecKey(wrapped);
        if (seen.has(key)) return null;
        seen.add(key);
        out.push(key);
      }
      return out;
    };
    const solvePeriodicPolycubeCell = () => {
      const seed = polycubeSeedData();
      if (!seed) return null;
      const { shapes, cellCount, minPeriod } = seed;
      const started = performance.now();
      const timeLimitMs = Math.max(50, +config.crystal_seed_time_ms || 1200);
      const maxNodes = Math.max(1000, +config.crystal_seed_node_limit || 500000);
      let nodesUsed = 0;
      const dimsList = [];
      for (let x = minPeriod[0]; x <= 8; x++) {
        for (let y = minPeriod[1]; y <= 8; y++) {
          for (let z = minPeriod[2]; z <= 8; z++) {
            const volume = x * y * z;
            if (volume % cellCount !== 0) continue;
            const tileCount = volume / cellCount;
            if (tileCount < 2 || tileCount > 32) continue;
            dimsList.push([x, y, z]);
          }
        }
      }
      dimsList.sort((a, b) => {
        const av = a[0] * a[1] * a[2], bv = b[0] * b[1] * b[2];
        if (av !== bv) return av - bv;
        return Math.max(...a) - Math.max(...b);
      });

      const solveDims = (dims) => {
        const [dx, dy, dz] = dims;
        const allCells = [];
        for (let x = 0; x < dx; x++) for (let y = 0; y < dy; y++) for (let z = 0; z < dz; z++) allCells.push(`${x},${y},${z}`);
        const rootCells = torusPlacementCells(shapes[0], [0, 0, 0], dims);
        if (!rootCells) return null;
        const rootSet = new Set(rootCells);
        const placements = [{ shape: shapes[0], shift: [0, 0, 0], cells: rootCells, root: true }];
        for (const shape of shapes) {
          for (let x = 0; x < dx; x++) {
            for (let y = 0; y < dy; y++) {
              for (let z = 0; z < dz; z++) {
                if (shape.orientIndex === 0 && x === 0 && y === 0 && z === 0) continue;
                const cells = torusPlacementCells(shape, [x, y, z], dims);
                if (!cells || cells.some(cell => rootSet.has(cell))) continue;
                placements.push({ shape, shift: [x, y, z], cells });
              }
            }
          }
        }
        const byCell = new Map(allCells.map(cell => [cell, []]));
        placements.forEach((placement, index) => {
          placement.cells.forEach(cell => byCell.get(cell)?.push(index));
        });
        const covered = new Set(rootCells);
        const solution = [placements[0]];
        const dfs = () => {
          nodesUsed += 1;
          if (nodesUsed > maxNodes || performance.now() - started > timeLimitMs) return false;
          if (covered.size === allCells.length) return true;
          let bestList = null;
          for (const cell of allCells) {
            if (covered.has(cell)) continue;
            const legal = (byCell.get(cell) ?? []).filter(index =>
              placements[index].cells.every(candidateCell => !covered.has(candidateCell))
            );
            if (!legal.length) return false;
            if (!bestList || legal.length < bestList.length) {
              bestList = legal;
              if (legal.length === 1) break;
            }
          }
          bestList.sort((ia, ib) => {
            const a = placements[ia], b = placements[ib];
            return a.shape.orientIndex - b.shape.orientIndex
              || a.shift[0] - b.shift[0]
              || a.shift[1] - b.shift[1]
              || a.shift[2] - b.shift[2];
          });
          for (const index of bestList) {
            const placement = placements[index];
            if (placement.cells.some(cell => covered.has(cell))) continue;
            placement.cells.forEach(cell => covered.add(cell));
            solution.push(placement);
            if (dfs()) return true;
            solution.pop();
            placement.cells.forEach(cell => covered.delete(cell));
          }
          return false;
        };
        return dfs() ? {
          dims,
          nodes: nodesUsed,
          placements: solution.map(placement => ({
            orientIndex: placement.shape.orientIndex,
            orient: placement.shape.orient,
            start: placement.shape.start,
            shift: placement.shift.slice(),
            root: !!placement.root
          }))
        } : null;
      };

      for (const dims of dimsList) {
        if (performance.now() - started > timeLimitMs || nodesUsed > maxNodes) break;
        const solved = solveDims(dims);
        if (solved) return solved;
      }
      return null;
    };
    const buildPeriodicSeedSequence = (cell) => {
      if (!cell?.placements?.length) return null;
      const period = cell.dims.map(size => size * 2);
      const targetTiles = criterion === "count" ? targetVal : Math.min(safetyMax, targetVal * cell.placements.length * 12);
      const cellsNeeded = Math.max(1, Math.ceil(targetTiles / cell.placements.length));
      const repeatRadius = Math.max(1, Math.ceil((Math.cbrt(cellsNeeded) - 1) / 2));
      const candidates = [];
      for (let rx = -repeatRadius; rx <= repeatRadius; rx++) {
        for (let ry = -repeatRadius; ry <= repeatRadius; ry++) {
          for (let rz = -repeatRadius; rz <= repeatRadius; rz++) {
            const repeatOffset = [rx * cell.dims[0], ry * cell.dims[1], rz * cell.dims[2]];
            for (const placement of cell.placements) {
              if (placement.root && rx === 0 && ry === 0 && rz === 0) continue;
              const shift = vecAdd(placement.shift, repeatOffset);
              const translation = vecAdd(placement.start, shift.map(value => value * 2));
              const distance = translation[0] * translation[0] + translation[1] * translation[1] + translation[2] * translation[2];
              candidates.push({
                prototile_idx: 0,
                orient: placement.orient,
                translation,
                is_forced: true,
                _periodic_seed: true,
                _periodic_distance: distance,
                _periodic_cell_dims: cell.dims,
                _periodic_period: period
              });
            }
          }
        }
      }
      const remaining = new Map();
      for (const move of candidates) {
        const key = `${move.orient.__orientation_id ?? ""}::${vecKey(move.translation)}`;
        if (!remaining.has(key)) remaining.set(key, move);
      }
      const sequence = [];
      const rollbacks = [];
      while (!goalMet() && state.placements.length < safetyMax && remaining.size) {
        let bestKey = null;
        let bestMove = null;
        let bestScore = null;
        for (const [key, move] of remaining.entries()) {
          const validity = isMoveValid(move);
          if (!validity.ok) continue;
          delete move._coverage;
          const coverage = moveCoverage(move);
          if (coverage <= 0) continue;
          const score = [coverage, -move._periodic_distance];
          if (isBetterScore(score, bestScore)) {
            bestKey = key;
            bestMove = { ...move, occupancy_data: validity.occData };
            bestScore = score;
          }
        }
        if (!bestMove) break;
        remaining.delete(bestKey);
        const rb = applyMove(bestMove);
        rollbacks.push([bestMove, rb]);
        sequence.push(bestMove);
      }
      const ok = goalMet();
      while (rollbacks.length) {
        const [move, rb] = rollbacks.pop();
        undoMove(move, rb);
      }
      return ok ? sequence : null;
    };
    async function* tryPeriodicSeed(parentId) {
      if (moveOrder !== "crystal" || exhaustive) return false;
      const cell = solvePeriodicPolycubeCell();
      if (!cell) {
        if (branchDetails) yield { type: "periodic_seed_debug", status: "no_cell" };
        return false;
      }
      const sequence = buildPeriodicSeedSequence(cell);
      if (!sequence?.length) {
        if (branchDetails) yield { type: "periodic_seed_debug", status: "no_sequence", cell: { dims: cell.dims, nodes: cell.nodes, placements: cell.placements.length } };
        return false;
      }
      if (branchDetails) yield { type: "periodic_seed_debug", status: "sequence", cell: { dims: cell.dims, nodes: cell.nodes, placements: cell.placements.length }, sequence_length: sequence.length };
      let currentParent = parentId;
      for (let i = 0; i < sequence.length; i++) {
        await yieldToBrowser();
        if (stopToken.stop || overBudget()) return false;
        const move = sequence[i];
        const validity = isMoveValid(move);
        if (!validity.ok) return false;
        move.occupancy_data = validity.occData;
        move.is_forced = true;
        searchStats.forced_total += 1;
        const nodeId = nowId();
        setBranchCursor(i, 1, 0);
        const rb = applyMove(move);
        move._periodic_rollback = rb;
        const stats = calculateFrontierStats();
        yield branchSet(currentParent, [{
          id: nodeId,
          text: treeTileName(prototiles[move.prototile_idx].name),
          is_forced: true,
          frontier_stats: stats,
          periodic_cell: cell.dims
        }]);
        yield nodeStatus(nodeId, "success", `[${state.placements.length}] periodic cell`, { color_id: move.color_id, frontier_stats: stats });
        if (shouldSnapshot()) {
          yield snapshot(nodeId);
          await tick();
        } else {
          yield nodeSnapshot(nodeId);
        }
        setBranchCursor(i, 1, 1);
        currentParent = nodeId;
        if (goalMet()) return true;
      }
      return goalMet();
    }

    async function* search(parentId, depth = 0) {
      if (stopToken.stop) return false;
      if (overBudget()) {
        yield nodeStatus(parentId, "fail", budgetText());
        return false;
      }
      const forcedBatch = [];
      const doReturn = async function* (retval) {
        if (retval && !exhaustive) return true;
        while (forcedBatch.length) { const [mv, rb] = forcedBatch.pop(); undoMove(mv, rb); }
        return retval;
      };
      if (goalMet()) {
        yield nodeStatus(parentId, "success");
        return yield* doReturn(true);
      }
      const node_candidate_cache = new Map();
      const frontierPointNorm = (option) => Math.abs(option.point[0]) + Math.abs(option.point[1]) + Math.abs(option.point[2]);
      const frontierPointOptions = () => {
        const options = [];
        for (const [pointKey, weight] of state.lattice.entries()) {
          if (weight <= 0 || weight >= MAX_SOLID_ANGLE) continue;
          options.push({ pointKey, point: pointKey.split(",").map(Number), weight });
        }
        return options.sort((left, right) => frontierPointNorm(left) - frontierPointNorm(right) || left.weight - right.weight || left.pointKey.localeCompare(right.pointKey));
      };
      const screenCachedVertexCandidates = (option, candidates, maxCandidates) => {
        const dedup = new Map();
        const localCandidateCap = Math.min(maxCandidates, candidateCap);
        for (const candidate of candidates ?? []) {
          if (!candidateTouchesPoint(candidate, option.pointKey)) continue;
          const validity = checkMoveViability(candidate);
          if (!validity) continue;
          const key = candidate.dedup_key ?? placementGeometryKey(candidate);
          if (!dedup.has(key)) dedup.set(key, { ...candidate, occupancy_data: validity.occData });
          if (Number.isFinite(localCandidateCap) && dedup.size >= localCandidateCap) break;
        }
        return [...dedup.values()];
      };

      const candidatesForVertexOption = async (option, maxCandidates = 2) => {
        const cacheKey = `${option.pointKey}::${maxCandidates}`;
        const cached = state.vertex_candidate_cache.get(cacheKey);
        if (cached) {
          const screened = screenCachedVertexCandidates(option, cached, maxCandidates);
          if (screened.length) {
            state.vertex_candidate_cache.set(cacheKey, screened);
            return screened;
          }
        }
        const dedup = new Map();
        for (let prototile_idx = 0; prototile_idx < prototiles.length; prototile_idx++) {
          const tile = prototiles[prototile_idx];
          await yieldToBrowser();
          for (const orient of tile.unique_orientations) {
            await yieldToBrowser();
            for (const anchor of orient.occupancy) {
              const translation = [option.point[0] - anchor.pos[0], option.point[1] - anchor.pos[1], option.point[2] - anchor.pos[2]];
              if (tile.is_polycube ? !isPolycubeMoveTranslation(tile, translation) : !translation.every(Number.isInteger)) continue;
              const mv = { prototile_idx, translation, orient };
              const chk = checkMoveViability(mv);
              if (!chk) continue;
              const dKey = placementGeometryKey(mv);
              if (!dedup.has(dKey)) {
                dedup.set(dKey, { ...mv, occupancy_data: chk.occData, dedup_key: dKey, _source_point_key: option.pointKey });
                if (dedup.size >= maxCandidates) {
                  const out = [...dedup.values()];
                  state.vertex_candidate_cache.set(cacheKey, out);
                  return out;
                }
              }
            }
          }
        }
        const out = [...dedup.values()];
        state.vertex_candidate_cache.set(cacheKey, out);
        return out;
      };
      const nodeCandidatesForVertexOption = async (option, maxCandidates = 2) => {
        const cacheKey = `${option.pointKey}::${maxCandidates}`;
        const cached = node_candidate_cache.get(cacheKey);
        if (cached) {
          const screened = screenCachedVertexCandidates(option, cached, maxCandidates);
          if (screened.length) {
            node_candidate_cache.set(cacheKey, screened);
            return screened;
          }
        }
        const candidates = await candidatesForVertexOption(option, maxCandidates);
        node_candidate_cache.set(cacheKey, candidates);
        return candidates;
      };
      const analyzeFrontierVertices = async () => {
        const options = [];
        const uniqueCandidatesForOption = (candidates) => {
          const dedup = new Map();
          for (const candidate of candidates ?? []) {
            const key = candidate.dedup_key ?? placementGeometryKey(candidate);
            if (!dedup.has(key)) dedup.set(key, candidate);
          }
          return [...dedup.values()];
        };
        for (const option of frontierPointOptions()) {
          const candidates = await nodeCandidatesForVertexOption(option, candidateCap);
          option.all_candidates = candidates;
          option.unique_candidates = uniqueCandidatesForOption(candidates);
          option.candidates = option.unique_candidates.slice(0, 2);
          options.push(option);
        }
        const uniqueCandidates = new Set();
        for (const option of options) {
          for (const candidate of option.unique_candidates) uniqueCandidates.add(candidate.dedup_key ?? placementGeometryKey(candidate));
        }
        const candidate_count = uniqueCandidates.size;
        const deadEnd = options.find(option => option.unique_candidates.length === 0);
        if (deadEnd) return { options, deadEnd, candidate_count };
        const forced = options.filter(option => option.unique_candidates.length === 1).sort((left, right) => frontierPointNorm(left) - frontierPointNorm(right) || left.pointKey.localeCompare(right.pointKey));
        if (forced.length) return { options, forced, candidate_count };
        if (!options.length) return { options, branches: [], candidate_count: 0 };
        return { options, branches: options.slice().sort((left, right) => frontierPointNorm(left) - frontierPointNorm(right) || left.unique_candidates.length - right.unique_candidates.length || left.pointKey.localeCompare(right.pointKey)), candidate_count };
      };
      let forcedCount = 0;
      let branchAnalysis = null;
      while (true) {
        await yieldToBrowser();
        if (stopToken.stop) return false;
        if (overBudget()) {
          yield nodeStatus(parentId, "fail", budgetText());
          return yield* doReturn(false);
        }
        if (frontierPointOptions().length === 0) {
          yield nodeStatus(parentId, "success"); return yield* doReturn(true);
        }

        const analysis = await analyzeFrontierVertices();
        const frontierDual = (() => {
          const candidateMap = new Map();
          const frontier_points = [];
          for (const option of analysis?.options ?? []) {
            const candidateKeys = new Set();
            for (const candidate of option.unique_candidates ?? option.all_candidates ?? option.candidates ?? []) {
              const key = candidate.dedup_key ?? placementGeometryKey(candidate);
              candidateKeys.add(key);
              if (!candidateMap.has(key)) {
                candidateMap.set(key, {
                  key,
                  prototile_idx: candidate.prototile_idx,
                  translation: candidate.translation?.slice() ?? [0, 0, 0],
                  frontier_points: []
                });
              }
              candidateMap.get(key).frontier_points.push(option.pointKey);
            }
            frontier_points.push({
              point_key: option.pointKey,
              point: option.point.slice(),
              weight: option.weight,
              candidate_keys: [...candidateKeys]
            });
          }
          const candidates = [...candidateMap.values()].map(candidate => ({
            ...candidate,
            frontier_points: [...new Set(candidate.frontier_points)]
          }));
          return {
            frontier_points,
            candidates,
            association_count: frontier_points.reduce((sum, point) => sum + point.candidate_keys.length, 0)
          };
        })();
        const analysisStats = {
          ...calculateFrontierStats(),
          point_count: analysis?.options?.length ?? frontierPointStats().point_count,
          candidate_count: analysis?.candidate_count ?? 0,
          association_count: frontierDual.association_count
        };
        if (overBudget()) { yield nodeStatus(parentId, "fail", budgetText()); return yield* doReturn(false); }
        if (analysis.deadEnd) {
          searchStats.failed_leaves += 1;
          yield nodeStatus(parentId, "fail", "Dead End", { frontier_stats: analysisStats, frontier_dual: frontierDual });
          return yield* doReturn(false);
        }
        yield nodeStatus(parentId, "working", "", { frontier_stats: analysisStats, frontier_dual: frontierDual });
        if (analysis.forced?.length) {
          const option = analysis.forced[0];
          const mv = option.unique_candidates[0];
          mv.is_forced = true;
          searchStats.forced_total += 1;
          const rb = applyMove(mv);
          forcedBatch.push([mv, rb]);
          forcedCount += 1;
          if (shouldSnapshot()) {
            yield snapshot(null);
            await tick();
          }
          if (goalMet() || state.placements.length >= safetyMax) {
            yield nodeStatus(parentId, "success");
            return yield* doReturn(true);
          }
          continue;
        }
        branchAnalysis = analysis;
        break;
      }

      if (forcedCount > 0) {
        const postForcedStats = { ...calculateFrontierStats(), candidate_count: 0 };
        const forcedNodeId = nowId();
        if (shouldSnapshot()) {
          yield snapshot(forcedNodeId);
          await tick();
        } else {
          yield nodeSnapshot(forcedNodeId);
        }
        yield branchSet(parentId, [{ id: forcedNodeId, text: `+ ${forcedCount} forced`, is_forced: true, frontier_stats: postForcedStats }]);
        yield nodeStatus(forcedNodeId, "success", "", { frontier_stats: postForcedStats });
      }

      const branchOptions = branchAnalysis?.branches ?? [];
      let bestOption = null;
      let bestOptionMoves = [];
      if (branchOptions.length) {
        let bestFaceScore = null;
        for (const option of branchOptions) {
          await yieldToBrowser();
          const moves = option.unique_candidates ?? await nodeCandidatesForVertexOption(option, candidateCap);
          if (!moves.length) continue;
          let bestCoverage = -1;
          for (const m of moves) bestCoverage = Math.max(bestCoverage, moveCoverage(m));
          const score = faceOrder === "pocket"
            ? [-frontierPointNorm(option), option.weight, -moves.length, bestCoverage]
            : faceOrder === "constrained"
              ? [-frontierPointNorm(option), -moves.length, bestCoverage]
              : [-frontierPointNorm(option), bestCoverage, -moves.length];
          if (isBetterScore(score, bestFaceScore)) {
            bestFaceScore = score;
            bestOption = option;
            bestOptionMoves = moves;
          }
        }
        if (!bestOption) {
          for (const option of branchOptions) {
            await yieldToBrowser();
            const moves = option.unique_candidates ?? await nodeCandidatesForVertexOption(option, candidateCap);
            if (moves.length) { bestOption = option; bestOptionMoves = moves; break; }
          }
        }
      }

      if (!bestOption) {
        searchStats.failed_leaves += 1;
        yield nodeStatus(parentId, "fail", "Dead End");
        return yield* doReturn(false);
      }

      let bestMoves = bestOptionMoves.sort(compareMoves);
      if (!exhaustive && Number.isFinite(branchCap) && bestMoves.length > branchCap) {
        bestMoves = bestMoves.slice(0, branchCap);
      }
      const payload = bestMoves.map(move => ({ id: nowId(), text: "", ...describeMove(move) }));
      for (let i = 0; i < bestMoves.length; i++) bestMoves[i].node_id = payload[i].id;
      setBranchCursor(depth, bestMoves.length, 0);
      
      yield branchSet(parentId, payload);

      let anySuccess = false;
      for (let i = 0; i < bestMoves.length; i++) {
        await yieldToBrowser();
        if (overBudget()) {
          yield nodeStatus(parentId, "fail", budgetText());
          return yield* doReturn(false);
        }
        const mv = bestMoves[i];
        mv.is_forced = false;
        setBranchCursor(depth, bestMoves.length, i);
        searchStats.branch_choices_visited += 1;
        searchStats.max_depth = Math.max(searchStats.max_depth, depth + 1);
        const rb = applyMove(mv);
        const postMoveStats = calculateFrontierStats();
        
        yield nodeStatus(mv.node_id, "working", `[${state.placements.length}] ${treeTileName(prototiles[mv.prototile_idx].name)} (${i+1}/${bestMoves.length})`, { color_id: mv.color_id, frontier_stats: postMoveStats });
        if (shouldSnapshot()) {
          yield snapshot(mv.node_id);
          await tick();
        } else {
          yield nodeSnapshot(mv.node_id);
        }

        const child = yield* search(mv.node_id, depth + 1);
        if (child) {
          anySuccess = true;
          yield nodeStatus(mv.node_id, "success");
          if (!exhaustive) return yield* doReturn(true);
        } else {
          searchStats.backtracks += 1;
          yield nodeStatus(mv.node_id, "fail");
        }
        undoMove(mv, rb);
        setBranchCursor(depth, bestMoves.length, i + 1);
      }

      if (anySuccess && exhaustive) { yield nodeStatus(parentId, "success"); return yield* doReturn(true); }
      yield nodeStatus(parentId, "fail");
      return yield* doReturn(false);
    }

    const success = (yield* tryPeriodicSeed(rootId)) || (yield* search(rootId));
    yield nodeStatus(rootId, success ? "success" : "fail");
    const finalSnapshot = success ? snapshot(null) : (bestSnapshot ? { ...cloneSnapshot(bestSnapshot), node_id: null } : snapshot(null));
    yield finalSnapshot;
    await tick();
    yield {
      type: "finished",
      tile_count: finalSnapshot.tile_count,
      search_stats: finalSnapshot.search_stats,
      success,
      best_effort: !success && (finalSnapshot.tile_count ?? 0) > state.placements.length
    };
  };
})();

export const tileSpecs = (() => {
  const SCALE = 1;
  const POLYCUBE_D3_COORD_SCALE = 2;
  const POLYCUBE_SOLID_ANGLE_MAX = 8;
  let activePolycubeLattice = "z3";
  const LEGACY_SOLID_ANGLE_MAX = 48;

  const COLOR_PALETTE = [
    "#e74c3c","#3498db","#f1c40f","#2ecc71","#9b59b6",
    "#e67e22","#1abc9c","#34495e","#d35400","#7f8c8d"
  ];

  // --- Z^3 lattice signed-permutation isometries: all 48 (det = ±1)
  const Z3_MATRICES_ALL = (() => {
    const perms = (arr) => {
      if (arr.length <= 1) return [arr.slice()];
      const out = [];
      for (let i = 0; i < arr.length; i++) {
        const rest = arr.slice(0, i).concat(arr.slice(i + 1));
        for (const p of perms(rest)) out.push([arr[i], ...p]);
      }
      return out;
    };

    const det3 = (M) =>
      M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1]) -
      M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0]) +
      M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]);

    const mats = [];
    for (const p of perms([0,1,2])) {
      const P = [[0,0,0],[0,0,0],[0,0,0]];
      for (let i = 0; i < 3; i++) P[i][p[i]] = 1;

      for (const sx of [-1,1]) for (const sy of [-1,1]) for (const sz of [-1,1]) {
        const S = [[sx,0,0],[0,sy,0],[0,0,sz]];
        const M = [
          [P[0][0]*S[0][0] + P[0][1]*S[1][0] + P[0][2]*S[2][0],
           P[0][0]*S[0][1] + P[0][1]*S[1][1] + P[0][2]*S[2][1],
           P[0][0]*S[0][2] + P[0][1]*S[1][2] + P[0][2]*S[2][2]],
          [P[1][0]*S[0][0] + P[1][1]*S[1][0] + P[1][2]*S[2][0],
           P[1][0]*S[0][1] + P[1][1]*S[1][1] + P[1][2]*S[2][1],
           P[1][0]*S[0][2] + P[1][1]*S[1][2] + P[1][2]*S[2][2]],
          [P[2][0]*S[0][0] + P[2][1]*S[1][0] + P[2][2]*S[2][0],
           P[2][0]*S[0][1] + P[2][1]*S[1][1] + P[2][2]*S[2][1],
           P[2][0]*S[0][2] + P[2][1]*S[1][2] + P[2][2]*S[2][2]],
        ];
        const det = det3(M);
        mats.push({ M, det });
      }
    }
    return mats;
  })();

  const Z3_MATRICES_DET1 = Z3_MATRICES_ALL.filter(x => x.det === 1);

  const add3 = (a,b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]];
  const sub3 = (a,b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const dot3 = (a,b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const cross3 = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const norm3 = (a) => Math.sqrt(dot3(a, a));
  const normalize3 = (a) => {
    const n = norm3(a);
    return n === 0 ? a : [a[0]/n, a[1]/n, a[2]/n];
  };

  // Generic function to compute solid angle of a cone spanned by three vectors
  const computeSolidAngle = (v1, v2, v3) => {
    const u = normalize3(v1);
    const v = normalize3(v2);
    const w = normalize3(v3);
    const triple = dot3(u, cross3(v, w));
    const uv = dot3(u, v);
    const vw = dot3(v, w);
    const wu = dot3(w, u);
    const denom = 1 + uv + vw + wu;
    if (Math.abs(denom) < 1e-12) return 0;
    const numerator = Math.abs(triple);
    const ratio = numerator / denom;
    const clampedRatio = Math.max(-1e12, Math.min(1e12, ratio));
    const omega = 2 * Math.atan(clampedRatio);
    return Math.abs(omega) < 1e-12 ? 0 : omega;
  };

  const computeDihedralAngle = (v1, v2, v3, v4) => {
    const a = sub3(v3, v1);
    const b = sub3(v2, v1);
    const c = sub3(v4, v1);
    const n1 = cross3(a, b);
    const n2 = cross3(b, c);
    const n1_norm = norm3(n1);
    const n2_norm = norm3(n2);
    if (n1_norm < 1e-12 || n2_norm < 1e-12) return 0;
    const cosAngle = dot3(n1, n2) / (n1_norm * n2_norm);
    const clampedCos = Math.max(-1, Math.min(1, cosAngle));
    const angle = Math.acos(clampedCos);
    return Math.PI - angle;
  };

  const computeNormalizedAngleWeight = (angle, fullAngle, maxValue = LEGACY_SOLID_ANGLE_MAX) => {
    const exact = (angle / fullAngle) * maxValue;
    const rounded = Math.round(exact);
    return rounded;
  };

  const getTetrahedronWeights = () => {
    const verts = [[0,0,0],[1,1,0],[1,0,1],[0,1,1]];
    const v0 = verts[0];
    const v1 = sub3(verts[1], v0);
    const v2 = sub3(verts[2], v0);
    const v3 = sub3(verts[3], v0);
    const solidAngle = computeSolidAngle(v1, v2, v3);
    const dihedralAngle = computeDihedralAngle(verts[0], verts[1], verts[2], verts[3]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    return {
      vertexWeight: computeNormalizedAngleWeight(solidAngle, fullSphere),
      edgeWeight: computeNormalizedAngleWeight(dihedralAngle, fullCircle),
      faceWeight: 24,
      interiorWeight: LEGACY_SOLID_ANGLE_MAX
    };
  };

  const getTetragonalDisphenoidWeights = () => {
    const verts = [[0,0,1],[0,0,-1],[1,1,0],[1,-1,0]];
    const v0 = verts[0];
    const v1 = sub3(verts[1], v0);
    const v2 = sub3(verts[2], v0);
    const v3 = sub3(verts[3], v0);
    const solidAngle = computeSolidAngle(v1, v2, v3);
    const longDihedral = computeDihedralAngle(verts[0], verts[1], verts[2], verts[3]);
    const shortDihedral = computeDihedralAngle(verts[0], verts[2], verts[1], verts[3]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    return {
      vertexWeight: computeNormalizedAngleWeight(solidAngle, fullSphere),
      longEdgeWeight: computeNormalizedAngleWeight(longDihedral, fullCircle),
      shortEdgeWeight: computeNormalizedAngleWeight(shortDihedral, fullCircle),
      faceWeight: 24,
      interiorWeight: LEGACY_SOLID_ANGLE_MAX
    };
  };

  const computeTetrahedronWeights = (verts, isTetragonalDisphenoid = false) => {
    if (isTetragonalDisphenoid) return getTetragonalDisphenoidWeights();
    return getTetrahedronWeights();
  };

  const computeHullFaces = (verts) => {
    const pts = verts.map(v => v.slice());
    const N = pts.length;
    const sum = pts.reduce((acc,v)=>add3(acc,v), [0,0,0]);
    const faces = [];
    const seen = new Set();

    for (let i=0;i<N;i++) for (let j=i+1;j<N;j++) for (let k=j+1;k<N;k++) {
      const p1 = pts[i], p2 = pts[j], p3 = pts[k];
      const n = cross3(sub3(p2,p1), sub3(p3,p1));
      if (n[0]===0 && n[1]==0 && n[2]===0) continue;
      const Np1_minus_sum = sub3([N*p1[0],N*p1[1],N*p1[2]], sum);
      let nn = n;
      if (dot3(nn, Np1_minus_sum) < 0) nn = [-nn[0],-nn[1],-nn[2]];

      let ok = true;
      const onPlane = [];
      for (let m=0;m<N;m++) {
        const d = dot3(sub3(pts[m], p1), nn);
        if (d > 0) { ok = false; break; }
        if (d === 0) onPlane.push(m);
      }
      if (!ok || onPlane.length < 3) continue;

      const facePts = onPlane.map(idx => pts[idx]);
      const c = facePts.reduce((acc,v)=>add3(acc,v), [0,0,0]).map(x => x / facePts.length);
      const nz = (() => {
        const len = Math.sqrt(nn[0]*nn[0]+nn[1]*nn[1]+nn[2]*nn[2]);
        return [nn[0]/len, nn[1]/len, nn[2]/len];
      })();
      let xax = sub3(facePts[0].map(Number), c);
      const xlen = Math.sqrt(xax[0]*xax[0]+xax[1]*xax[1]+xax[2]*xax[2]) || 1;
      xax = [xax[0]/xlen, xax[1]/xlen, xax[2]/xlen];
      const yax = cross3(nz, xax);

      const withAng = onPlane.map((idx) => {
        const v = sub3(pts[idx].map(Number), c);
        const ang = Math.atan2(dot3(v, yax), dot3(v, xax));
        return { idx, ang };
      }).sort((a,b)=>a.ang-b.ang);

      const ordered = withAng.map(o => o.idx);
      const h = ordered.slice().sort((a,b)=>a-b).join(",");
      if (!seen.has(h)) {
        seen.add(h);
        faces.push(ordered);
      }
    }
    return faces;
  };

  const computeTetrahedronOccupancy = (vertsScaled, faces, isTetragonalDisphenoid = false) => {
    const unitVerts = vertsScaled.map(v => [v[0]/SCALE, v[1]/SCALE, v[2]/SCALE]);
    const fullSphere = 4 * Math.PI;
    const fullCircle = 2 * Math.PI;
    const vertexWeights = unitVerts.map((vertex, index) => {
      const others = unitVerts.filter((_, otherIndex) => otherIndex !== index).map(other => sub3(other, vertex));
      return computeNormalizedAngleWeight(computeSolidAngle(others[0], others[1], others[2]), fullSphere);
    });
    const edgeWeight = (i, j) => {
      const opposite = [0, 1, 2, 3].filter(index => index !== i && index !== j);
      return computeNormalizedAngleWeight(computeDihedralAngle(unitVerts[i], unitVerts[j], unitVerts[opposite[0]], unitVerts[opposite[1]]), fullCircle);
    };

    const minB = [Infinity, Infinity, Infinity];
    const maxB = [-Infinity, -Infinity, -Infinity];
    for (const v of vertsScaled) {
      for (let i = 0; i < 3; i++) {
        minB[i] = Math.min(minB[i], v[i]);
        maxB[i] = Math.max(maxB[i], v[i]);
      }
    }

    const occ = [];
    const vertKeyToIndex = new Map(vertsScaled.map((v, index) => [v.join(','), index]));
    const edgeMidpointWeights = new Map();
    for (let i = 0; i < vertsScaled.length; i++) {
      for (let j = i + 1; j < vertsScaled.length; j++) {
        const mid = [
          (vertsScaled[i][0] + vertsScaled[j][0]) / 2,
          (vertsScaled[i][1] + vertsScaled[j][1]) / 2,
          (vertsScaled[i][2] + vertsScaled[j][2]) / 2
        ];
        if (mid.every(Number.isInteger)) edgeMidpointWeights.set(mid.join(','), edgeWeight(i, j));
      }
    }

    for (let x = minB[0]; x <= maxB[0]; x++) {
      for (let y = minB[1]; y <= maxB[1]; y++) {
        for (let z = minB[2]; z <= maxB[2]; z++) {
          const p = [x, y, z];
          const key = p.join(',');

          if (vertKeyToIndex.has(key)) {
            occ.push([p, vertexWeights[vertKeyToIndex.get(key)], null, null, "vertex"]);
            continue;
          }

          if (edgeMidpointWeights.has(key)) {
            occ.push([p, edgeMidpointWeights.get(key), null, null, "edge"]);
            continue;
          }

          const EPS = 1e-7;
          const pu = [p[0]/SCALE, p[1]/SCALE, p[2]/SCALE];
          const [v0, v1, v2, v3] = unitVerts;

          const v0v1 = sub3(v1, v0);
          const v0v2 = sub3(v2, v0);
          const v0v3 = sub3(v3, v0);
          const v0p = sub3(pu, v0);

          const d00 = dot3(v0v1, v0v1);
          const d01 = dot3(v0v1, v0v2);
          const d02 = dot3(v0v1, v0v3);
          const d03 = dot3(v0v1, v0p);
          const d11 = dot3(v0v2, v0v2);
          const d12 = dot3(v0v2, v0v3);
          const d13 = dot3(v0v2, v0p);
          const d22 = dot3(v0v3, v0v3);
          const d23 = dot3(v0v3, v0p);

          const denom = d00 * (d11 * d22 - d12 * d12) -
                       d01 * (d01 * d22 - d12 * d02) +
                       d02 * (d01 * d12 - d11 * d02);

          if (Math.abs(denom) < 1e-12) continue;

          const invDenom = 1 / denom;
          const u = (d11 * d22 - d12 * d12) * d03 - (d01 * d22 - d12 * d02) * d13 + (d01 * d12 - d11 * d02) * d23;
          const v = -(d01 * d22 - d12 * d02) * d03 + (d00 * d22 - d02 * d02) * d13 - (d00 * d12 - d01 * d02) * d23;
          const w = (d01 * d12 - d11 * d02) * d03 - (d00 * d12 - d01 * d02) * d13 + (d00 * d11 - d01 * d01) * d23;

          const baryU = u * invDenom;
          const baryV = v * invDenom;
          const baryW = w * invDenom;
          const baryT = 1 - baryU - baryV - baryW;

          if (baryU > -EPS && baryV > -EPS && baryW > -EPS && baryT > -EPS &&
              baryU < 1+EPS && baryV < 1+EPS && baryW < 1+EPS && baryT < 1+EPS) {
            const nearZero = [baryU, baryV, baryW, baryT].filter(value => Math.abs(value) < EPS).length;
            if (nearZero === 1) occ.push([p, LEGACY_SOLID_ANGLE_MAX / 2, null, null, "face"]);
            else if (nearZero === 0) occ.push([p, LEGACY_SOLID_ANGLE_MAX, null, null, "interior"]);
          }
        }
      }
    }
    return occ;
  };

  const triangleSolidAngle = (a, b, c) => {
    const la = norm3(a), lb = norm3(b), lc = norm3(c);
    if (la < 1e-12 || lb < 1e-12 || lc < 1e-12) return 0;
    const numerator = dot3(a, cross3(b, c));
    const denominator = la * lb * lc + dot3(a, b) * lc + dot3(b, c) * la + dot3(c, a) * lb;
    return 2 * Math.atan2(numerator, denominator);
  };

  const orientConvexFaces = (verts, faces) => {
    const center = verts.reduce((acc, v) => add3(acc, v), [0, 0, 0]).map(value => value / verts.length);
    return faces.map(face => {
      if (face.length < 3) return face.slice();
      const a = verts[face[0]], b = verts[face[1]], c = verts[face[2]];
      const normal = cross3(sub3(b, a), sub3(c, a));
      return dot3(normal, sub3(center, a)) > 0 ? face.slice().reverse() : face.slice();
    });
  };

  const convexPlanes = (verts, faces) => {
    const oriented = orientConvexFaces(verts, faces);
    return oriented
      .filter(face => face.length >= 3)
      .map(face => {
        const a = verts[face[0]], b = verts[face[1]], c = verts[face[2]];
        const n = cross3(sub3(b, a), sub3(c, a));
        return { face, n, d: dot3(n, a) };
      });
  };

  const pointInConvexPolyhedron = (point, planes, eps = 1e-9) => {
    for (const plane of planes) {
      if (dot3(plane.n, point) - plane.d > eps) return false;
    }
    return true;
  };

  const convexSolidAngleAtPoint = (point, verts, orientedFaces, center, planes) => {
    const activeNormals = planes
      .filter(plane => Math.abs(dot3(plane.n, point) - plane.d) < 1e-9)
      .map(plane => normalize3(plane.n));
    let nudged = point.slice();
    if (activeNormals.length) {
      const outward = normalize3(activeNormals.reduce((sum, n) => add3(sum, n), [0, 0, 0]));
      nudged = point.map((value, axis) => value + outward[axis] * 1e-6);
    }
    let omega = 0;
    for (const face of orientedFaces) {
      if (face.length < 3) continue;
      const base = sub3(verts[face[0]], nudged);
      for (let i = 1; i < face.length - 1; i++) {
        omega += triangleSolidAngle(
          base,
          sub3(verts[face[i]], nudged),
          sub3(verts[face[i + 1]], nudged)
        );
      }
    }
    return Math.abs(omega);
  };

  const vertexConeSolidAngle = (point, verts, planes) => {
    const activeAtPoint = planes.filter(plane => Math.abs(dot3(plane.n, point) - plane.d) < 1e-9);
    const rays = [];
    const seen = new Set();
    for (const vertex of verts) {
      const delta = sub3(vertex, point);
      const length = norm3(delta);
      if (length < 1e-9) continue;
      const sharedPlanes = activeAtPoint.filter(plane => Math.abs(dot3(plane.n, vertex) - plane.d) < 1e-9).length;
      if (sharedPlanes < 2) continue;
      const ray = delta.map(value => value / length);
      const key = ray.map(value => Math.round(value * 1e9)).join(",");
      if (seen.has(key)) continue;
      seen.add(key);
      rays.push(ray);
    }
    if (rays.length < 3) return null;
    const axis = normalize3(rays.reduce((sum, ray) => add3(sum, ray), [0, 0, 0]));
    if (norm3(axis) < 1e-9) return null;
    let basisU = cross3(axis, [1, 0, 0]);
    if (norm3(basisU) < 1e-9) basisU = cross3(axis, [0, 1, 0]);
    basisU = normalize3(basisU);
    const basisV = normalize3(cross3(axis, basisU));
    const ordered = rays
      .map(ray => ({ ray, angle: Math.atan2(dot3(ray, basisV), dot3(ray, basisU)) }))
      .sort((a, b) => a.angle - b.angle)
      .map(item => item.ray);
    let omega = 0;
    for (let i = 0; i < ordered.length; i++) {
      omega += computeSolidAngle(axis, ordered[i], ordered[(i + 1) % ordered.length]);
    }
    return Math.abs(omega);
  };

  const computeConvexOccupancy = (verts, faces, maxValue = LEGACY_SOLID_ANGLE_MAX) => {
    const minB = [Infinity, Infinity, Infinity];
    const maxB = [-Infinity, -Infinity, -Infinity];
    for (const v of verts) for (let i = 0; i < 3; i++) {
      minB[i] = Math.min(minB[i], v[i]);
      maxB[i] = Math.max(maxB[i], v[i]);
    }
    const orientedFaces = orientConvexFaces(verts, faces);
    const planes = convexPlanes(verts, orientedFaces);
    const center = verts.reduce((acc, v) => add3(acc, v), [0, 0, 0]).map(value => value / verts.length);
    const occ = [];
    for (let x = Math.ceil(minB[0]); x <= Math.floor(maxB[0]); x++) {
      for (let y = Math.ceil(minB[1]); y <= Math.floor(maxB[1]); y++) {
        for (let z = Math.ceil(minB[2]); z <= Math.floor(maxB[2]); z++) {
          const p = [x, y, z];
          if (!pointInConvexPolyhedron(p, planes)) continue;
          const active = planes.filter(plane => Math.abs(dot3(plane.n, p) - plane.d) < 1e-9);
          let weight;
          let kind;
          if (active.length === 0) {
            weight = maxValue;
            kind = "interior";
          } else if (active.length === 1) {
            weight = maxValue / 2;
            kind = "face";
          } else if (active.length === 2) {
            const n0 = normalize3(active[0].n);
            const n1 = normalize3(active[1].n);
            const cos = Math.max(-1, Math.min(1, dot3(n0, n1)));
            weight = computeNormalizedAngleWeight(Math.PI - Math.acos(cos), 2 * Math.PI, maxValue);
            kind = "edge";
          } else {
            const omega = vertexConeSolidAngle(p, verts, planes) ?? convexSolidAngleAtPoint(p, verts, orientedFaces, center, planes);
            weight = Math.max(1, Math.min(maxValue, computeNormalizedAngleWeight(omega, 4 * Math.PI, maxValue)));
            kind = "vertex";
          }
          if (weight > 0) occ.push([p, weight, null, null, kind]);
        }
      }
    }
    return occ;
  };

  const createScaledTileData = (unitVerts, faceTemplate, autoHull=false, isTetragonalDisphenoid=false) => {
    const vertsScaled = unitVerts.map(v => v.map(c => Math.round(c * SCALE)));
    const faces = autoHull ? computeHullFaces(vertsScaled) : faceTemplate.map(f => f.v.slice());
    const faceData = autoHull
      ? faces.map(f => ({ v: f, type: "default" }))
      : faceTemplate.map(f => ({ v: f.v.slice(), type: f.type }));
    let occ;
    if (unitVerts.length === 4 && faceTemplate.length === 4 && faceTemplate.every(f => f.v.length === 3)) {
      occ = computeTetrahedronOccupancy(vertsScaled, faces, isTetragonalDisphenoid);
    } else {
      occ = computeConvexOccupancy(vertsScaled, faceData.map(f => f.v));
    }
    return { v: vertsScaled, f_data: faceData, occ, skip_winding: false, solid_angle: { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX } };
  };

  const generatePolycubeData = (voxels, options = {}) => {
    const lattice = options.polycube_lattice ?? activePolycubeLattice;
    const useD3Frontier = lattice === "d3";
    const polycubeCoordScale = useD3Frontier ? POLYCUBE_D3_COORD_SCALE : 1;
    const voxelSet = new Set(voxels.map(v => v.map(Number).join(",")));
    const vox = voxels.map(v => v.map(Number));
    const uniqueVerts = new Set();
    for (const v of vox) {
      for (const dx of [0,1]) for (const dy of [0,1]) for (const dz of [0,1]) {
        uniqueVerts.add([v[0]+dx, v[1]+dy, v[2]+dz].join(","));
      }
    }
    const vertsList = [...uniqueVerts].map(s => s.split(",").map(Number))
      .sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
    const vertMap = new Map(vertsList.map((v,i)=>[v.join(","), i]));
    const faceDefs = [
      [[ 1,0,0],  [[1,0,0],[1,1,0],[1,1,1],[1,0,1]]],
      [[-1,0,0],  [[0,0,0],[0,0,1],[0,1,1],[0,1,0]]],
      [[ 0,1,0],  [[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],
      [[ 0,-1,0], [[0,0,0],[1,0,0],[1,0,1],[0,0,1]]],
      [[ 0,0,1],  [[0,0,1],[1,0,1],[1,1,1],[0,1,1]]],
      [[ 0,0,-1], [[0,0,0],[0,1,0],[1,1,0],[1,0,0]]],
    ];
    const faces = [];
    for (const v of vox) {
      const [vx,vy,vz] = v;
      for (const [nrm, deltas] of faceDefs) {
        const nb = [vx+nrm[0], vy+nrm[1], vz+nrm[2]].join(",");
        if (!voxelSet.has(nb)) {
          const idxs = deltas.map(([dx,dy,dz]) => vertMap.get([vx+dx,vy+dy,vz+dz].join(",")));
          faces.push(idxs);
        }
      }
    }
    const scaledVerts = vertsList.map(v => v.map(c => (c * polycubeCoordScale * SCALE)|0));
    const occ = new Map();
    const addOcc = (pos, weight) => {
      const key = pos.map(c => c * polycubeCoordScale * SCALE).join(",");
      occ.set(key, (occ.get(key) ?? 0) + weight);
    };
    for (const v of vox) {
      const [x, y, z] = v;
      for (const dx of [0,1]) for (const dy of [0,1]) for (const dz of [0,1]) {
        addOcc([x + dx, y + dy, z + dz], 1);
      }
      if (useD3Frontier) {
        for (const fixed of [0, 1]) {
          addOcc([x + fixed, y + 0.5, z + 0.5], 4);
          addOcc([x + 0.5, y + fixed, z + 0.5], 4);
          addOcc([x + 0.5, y + 0.5, z + fixed], 4);
        }
      }
    }
    const polycubeKind = (weight) => {
      if (weight >= POLYCUBE_SOLID_ANGLE_MAX) return "interior";
      if (weight >= 4) return "face";
      if (weight >= 2) return "edge";
      return "vertex";
    };
    const occList = [...occ.entries()].map(([k,weight]) => [k.split(",").map(Number), weight, null, null, polycubeKind(weight)]);
    const faceData = faces.map(f => ({ v: f.slice(), type: "default" }));
    return { v: scaledVerts, f_data: faceData, occ: occList, skip_winding: true, polycube_lattice: lattice, solid_angle: { kind: "rational", max_value: POLYCUBE_SOLID_ANGLE_MAX } };
  };

  class Prototile3D {
    constructor(name, vertices, face_data, occupancy_map, skip_winding=false, is_mirror=false, solid_angle={ kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX }, metadata = {}) {
      this.name = name;
      this.is_mirror = is_mirror;
      this.verts = vertices.map(v => v.slice());
      this.faces = face_data.map(f => f.v.slice());
      this.face_types = face_data.map(f => f.type);
      this.occupancy_points = (occupancy_map || []).map(([pt,w,symbolic,display_symbolic,kind]) => ({ pos: pt.slice(), weight: w, symbolic, display_symbolic, kind }));
      this.solid_angle = { kind: solid_angle.kind ?? "numeric", max_value: solid_angle.max_value ?? LEGACY_SOLID_ANGLE_MAX, symbols: [...(solid_angle.symbols ?? [])] };
      this.polycube_lattice = metadata.polycube_lattice ?? null;
      this.is_polycube = this.solid_angle.max_value === POLYCUBE_SOLID_ANGLE_MAX;
      if (!skip_winding) this._fixWinding();
      this.unique_orientations = [];
      this.is_chiral = false;
      this._calcSymmetries();
      if (!is_mirror) this._checkChirality();
    }
    _fixWinding() {
      const inside = this.occupancy_points.length ? this.occupancy_points[0].pos : [
        Math.round(this.verts.reduce((s,v)=>s+v[0],0)/this.verts.length),
        Math.round(this.verts.reduce((s,v)=>s+v[1],0)/this.verts.length),
        Math.round(this.verts.reduce((s,v)=>s+v[2],0)/this.verts.length),
      ];
      const newFaces = [];
      for (const f of this.faces) {
        if (f.length < 3) { newFaces.push(f); continue; }
        const v0 = this.verts[f[0]], v1 = this.verts[f[1]], v2 = this.verts[f[2]];
        let n = cross3(sub3(v1,v0), sub3(v2,v0));
        const inward = sub3(inside, v0);
        if (dot3(n, inward) > 0) newFaces.push(f.slice().reverse());
        else newFaces.push(f.slice());
      }
      this.faces = newFaces;
    }
    _calcSymmetries() {
      const mul = (M,v) => ([
        M[0][0]*v[0]+M[0][1]*v[1]+M[0][2]*v[2],
        M[1][0]*v[0]+M[1][1]*v[1]+M[1][2]*v[2],
        M[2][0]*v[0]+M[2][1]*v[1]+M[2][2]*v[2],
      ]);
      const buildFrom = (matList) => {
        const seen = new Set();
        const out = [];
        for (let iso_idx = 0; iso_idx < matList.length; iso_idx++) {
          const { M, det } = matList[iso_idx];
          let tVerts = this.verts.map(v => mul(M,v));
          const shift = [Infinity,Infinity,Infinity];
          for (const v of tVerts) for (let i=0;i<3;i++) shift[i]=Math.min(shift[i], v[i]);
          tVerts = tVerts.map(v => [v[0]-shift[0], v[1]-shift[1], v[2]-shift[2]]);
          const vIndex = new Map(tVerts.map((v,i)=>[v.join(","), i]));
          const tOcc = this.occupancy_points.map(pt => {
            const mp = mul(M, pt.pos);
            return { pos: [mp[0]-shift[0], mp[1]-shift[1], mp[2]-shift[2]], weight: pt.weight, symbolic: pt.symbolic, display_symbolic: pt.display_symbolic, kind: pt.kind };
          });
          const newFaces = [];
          const newFaceTypes = [];
          for (let fi = 0; fi < this.faces.length; fi++) {
            const face = this.faces[fi];
            const mapped = face.map(oldIdx => {
              const mv = mul(M, this.verts[oldIdx]);
              const key = [mv[0]-shift[0], mv[1]-shift[1], mv[2]-shift[2]].join(",");
              return vIndex.get(key);
            });
            const fixed = (det === -1) ? mapped.slice().reverse() : mapped;
            newFaces.push(fixed);
            newFaceTypes.push(this.face_types[fi]);
          }
          const vHash = tVerts.map(v=>v.join(",")).sort().join("|");
          const oHash = tOcc.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
          const fHash = newFaces.map(f => f.slice().sort((a,b)=>a-b).join(",")).sort().join("|");
          const geomHash = `${vHash}@@${oHash}@@${fHash}`;
          if (seen.has(geomHash)) continue;
          seen.add(geomHash);
          out.push({
            iso_idx,
            det,
            verts: tVerts,
            faces: newFaces,
            face_types: newFaceTypes,
            occupancy: tOcc,
            vertsForFace: (fIdx) => fIdx.map(i => tVerts[i])
          });
        }
        return out;
      };
      this.orientations24 = buildFrom(Z3_MATRICES_DET1);
      this.unique_orientations = this.orientations24;
    }
    _checkChirality() {
      const mirror = this.verts.map(v => [-v[0], v[1], v[2]]);
      const minv = [Infinity,Infinity,Infinity];
      for (const v of mirror) for (let i=0;i<3;i++) minv[i]=Math.min(minv[i], v[i]);
      const tVerts = mirror.map(v => sub3(v, minv));
      const tOcc = this.occupancy_points.map(pt => ({ pos: sub3([-pt.pos[0], pt.pos[1], pt.pos[2]], minv), weight: pt.weight, symbolic: pt.symbolic, display_symbolic: pt.display_symbolic, kind: pt.kind }));
      const vHash = tVerts.map(v=>v.join(",")).sort().join("|");
      const oHash = tOcc.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
      const mirrorHash = `${vHash}@@${oHash}`;
      const baseNoFaces = new Set();
      for (const o of this.unique_orientations) {
        const vh = o.verts.map(v=>v.join(",")).sort().join("|");
        const oh = o.occupancy.map(p=>`${p.pos.join(",")}:${p.weight}`).sort().join("|");
        baseNoFaces.add(`${vh}@@${oh}`);
      }
      this.is_chiral = !baseNoFaces.has(mirrorHash);
    }
    rescaleOccupancyWeights(targetMax) {
      const sourceMax = this.solid_angle?.max_value ?? LEGACY_SOLID_ANGLE_MAX;
      if (targetMax === sourceMax) return;
      const scale = targetMax / sourceMax;
      const convert = (weight) => {
        const scaled = weight * scale;
        const rounded = Math.round(scaled);
        return Math.abs(scaled - rounded) < 1e-9 ? rounded : scaled;
      };
      this.occupancy_points = this.occupancy_points.map(pt => ({ ...pt, weight: convert(pt.weight) }));
      for (const orient of this.unique_orientations ?? []) {
        orient.occupancy = orient.occupancy.map(pt => ({ ...pt, weight: convert(pt.weight) }));
      }
      this.solid_angle = { ...this.solid_angle, max_value: targetMax };
    }
    get_mirror_copy() {
      if (!this.is_chiral) return null;
      const mirrorVerts = this.verts.map(v => [-v[0], v[1], v[2]]);
      const minv = [Infinity,Infinity,Infinity];
      for (const v of mirrorVerts) for (let i=0;i<3;i++) minv[i]=Math.min(minv[i], v[i]);
      const tVerts = mirrorVerts.map(v => sub3(v, minv));
      const mirrorOcc = this.occupancy_points.map(p => [sub3([-p.pos[0],p.pos[1],p.pos[2]], minv), p.weight, p.symbolic, p.display_symbolic, p.kind]);
      const faceData = this.faces.map((f,i)=>({ v: f.slice(), type: this.face_types[i] }));
      return new Prototile3D(`reflected ${this.name}`, tVerts, faceData, mirrorOcc, false, true, this.solid_angle, { polycube_lattice: this.polycube_lattice });
    }
  }

  const make_tile = (name, data) => {
    return new Prototile3D(name, data.v, data.f_data, data.occ, !!data.skip_winding, false, data.solid_angle, { polycube_lattice: data.polycube_lattice });
  };

  const withSymbolicSolidAngles = (occ, rules) => occ.map(([pos, weight, _symbol, _display, kind]) => {
    const symbolic = rules(weight, kind);
    return [pos, weight, symbolic?.symbol ?? symbolic, symbolic?.display ?? symbolic, kind];
  });

  const gen_tetrahedron_data = () => {
    const verts = [[0,0,0],[1,1,0],[1,0,1],[0,1,1]];
    const data = createScaledTileData(
      verts,
      [ { v:[0,1,2], type:"default" }, { v:[0,2,3], type:"default" }, { v:[0,3,1], type:"default" }, { v:[1,3,2], type:"default" } ],
      false, false
    );
    data.occ = withSymbolicSolidAngles(data.occ, weight => {
      if (weight === LEGACY_SOLID_ANGLE_MAX) return { symbol: "1", display: "1" };
      if (weight <= 3) return { symbol: "α", display: "(3 arccos(1/3) - π)/(4π)" };
      return { symbol: "(1 + 4α)/6", display: "(1 + 4((3 arccos(1/3) - π)/(4π)))/6" };
    });
    data.solid_angle = { kind: "symbolic", max_value: LEGACY_SOLID_ANGLE_MAX, symbols: ["α = (3 arccos(1/3) - π)/(4π)"] };
    return data;
  };

  const gen_tetragonal_disphenoid_data = () => {
    const verts = [[0,0,1],[0,0,-1],[1,1,0],[1,-1,0]];
    return createScaledTileData(
      verts,
      [ { v:[0,2,3], type:"default" }, { v:[1,3,2], type:"default" }, { v:[0,3,1], type:"default" }, { v:[0,1,2], type:"default" } ],
      false, true
    );
  };

  const gen_octahedron_data = () => {
    const data = createScaledTileData(
      [[ 1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],
      [
        {v:[0,2,4], type:"default"}, {v:[2,1,4], type:"default"}, {v:[1,3,4], type:"default"}, {v:[3,0,4], type:"default"},
        {v:[0,5,2], type:"default"}, {v:[2,5,1], type:"default"}, {v:[1,5,3], type:"default"}, {v:[3,5,0], type:"default"},
      ], false
    );
    const vertexWeight = computeNormalizedAngleWeight(4 * Math.asin(1 / 3), 4 * Math.PI);
    const edgeWeight = computeNormalizedAngleWeight(Math.acos(-1 / 3), 2 * Math.PI);
    const occ = new Map();
    for (const v of data.v) occ.set(v.join(','), [vertexWeight, 'vertex']);
    for (let i = 0; i < data.v.length; i++) {
      for (let j = i + 1; j < data.v.length; j++) {
        const a = data.v[i], b = data.v[j];
        const d2 = (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2;
        if (d2 === 8) occ.set([(a[0]+b[0])/2, (a[1]+b[1])/2, (a[2]+b[2])/2].join(','), [edgeWeight, 'edge']);
      }
    }
    occ.set('0,0,0', [LEGACY_SOLID_ANGLE_MAX, 'interior']);
    data.occ = [...occ.entries()].map(([key, item]) => {
      const [weight, kind] = item;
      return [key.split(',').map(Number), weight,
        weight === LEGACY_SOLID_ANGLE_MAX ? "1" : (weight === vertexWeight ? "(1 - 8α)/6" : "(1 - 2α)/3"),
        weight === LEGACY_SOLID_ANGLE_MAX ? "1" : (weight === vertexWeight ? "(1 - 8((3 arccos(1/3) - π)/(4π)))/6" : "(1 - 2((3 arccos(1/3) - π)/(4π)))/3"),
        kind
      ];
    });
    data.solid_angle = { kind: "symbolic", max_value: LEGACY_SOLID_ANGLE_MAX, symbols: ["α = (3 arccos(1/3) - π)/(4π)"] };
    return data;
  };

  const gen_corner_tetra_data = () =>
    createScaledTileData(
      [[0,0,0],[1,0,0],[0,1,0],[0,0,1]],
      [
        { v:[0,2,1], type:"default" },
        { v:[0,1,3], type:"default" },
        { v:[0,3,2], type:"default" },
        { v:[1,2,3], type:"default" }
      ], false
    );

  const gen_big_corner_tetra_data = () => {
    const verts = [
      [0,0,0], [2,0,0], [0,2,0], [0,0,2],
      [1,1,0], [1,0,1], [0,1,1], [1,0,0], [0,1,0], [0,0,1]
    ];
    const faces = [
      // z = 0 face
      [0,7,8], [7,1,4], [8,4,2], [7,4,8],
      // y = 0 face
      [0,9,7], [9,3,5], [7,5,1], [9,5,7],
      // x = 0 face
      [0,8,9], [8,2,6], [9,6,3], [8,6,9],
      // slanted face x + y + z = 2
      [1,4,5], [4,2,6], [5,6,3], [4,6,5]
    ];
    const scaledVerts = verts.map(v => v.map(c => Math.round(c * SCALE)));
    const cornerOnly = [[0,0,0],[2,0,0],[0,2,0],[0,0,2]].map(v => v.map(c => Math.round(c * SCALE)));
    const cornerFaces = [[0,2,1], [0,1,3], [0,3,2], [1,2,3]];
    return {
      v: scaledVerts,
      f_data: faces.map(v => ({ v, type: "default" })),
      occ: computeTetrahedronOccupancy(cornerOnly, cornerFaces, false),
      skip_winding: false,
      solid_angle: { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX }
    };
  };

  const gen_cuboctahedron_data = () => {
    const set = new Set();
    for (const x of [-1,1]) for (const y of [-1,1]) set.add([x,y,0].join(","));
    for (const x of [-1,1]) for (const z of [-1,1]) set.add([x,0,z].join(","));
    for (const y of [-1,1]) for (const z of [-1,1]) set.add([0,y,z].join(","));
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_elongated_square_bipyramid = () => {
    const verts = [];
    for (const x of [-1,1]) for (const y of [-1,1]) for (const z of [-1,1]) verts.push([x,y,z]);
    verts.push([0,0,2],[0,0,-2]);
    return createScaledTileData(verts, [], true);
  };

  const gen_n_cross_data = (arm) => {
    const vox = [[0,0,0]];
    const dirs = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
    for (const d of dirs) for (let i=1;i<=arm;i++) vox.push([i*d[0], i*d[1], i*d[2]]);
    return generatePolycubeData(vox);
  };

  const gen_n_semicross_data = (arm) => {
    const vox = [[0,0,0]];
    const dirs = [[1,0,0],[0,1,0],[0,0,1]];
    for (const d of dirs) for (let i=1;i<=arm;i++) vox.push([i*d[0], i*d[1], i*d[2]]);
    return generatePolycubeData(vox);
  };

  const gen_double_ring_data = () =>
    generatePolycubeData([ [0,0,0],[0,0,1], [1,0,0],[1,1,0],[1,1,1],[0,1,1], [-1,0,0],[-1,-1,0],[-1,-1,1],[0,-1,1] ]);
  const gen_buckled_ring_data = () => generatePolycubeData([[0,0,0],[1,0,0],[1,1,0],[1,1,1],[0,1,1],[0,0,1]]);
  const gen_large_buckled_ring_data = () => generatePolycubeData([ [0,0,0],[1,0,0],[2,0,0],[2,1,0],[2,2,0], [2,2,1],[2,2,2],[1,2,2],[0,2,2],[0,1,2],[0,0,2],[0,0,1] ]);
  const gen_tuning_fork = () => {
    const vox = [];
    for (let x=0;x<3;x++) for (let y=0;y<12;y++) {
      if (!(x===1 && (y<3 || (6<=y && y<9)))) vox.push([x,y,0]);
    }
    return generatePolycubeData(vox);
  };
  const gen_twisted_h_data = () => generatePolycubeData([[0,0,0],[0,0,1],[1,0,1],[-1,0,1],[0,0,-1],[0,1,-1],[0,-1,-1]]);
  const gen_cube_data = () => generatePolycubeData([[0,0,0]]);
  const gen_s_tetracube = () => generatePolycubeData([[0,0,0],[1,0,0],[1,1,0],[1,1,1]]);
  const gen_knuckle_pentacube = () => generatePolycubeData([[0,0,0],[1,0,0],[-1,0,0],[0,1,0],[0,0,1]]);

  const gen_rhombic_robust = () => {
    const set = new Set();
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    for (const p of perms([2,0,0])) { set.add(p.join(",")); set.add(p.map(x=>-x).join(",")); }
    for (const sx of [-1,1]) for (const sy of [-1,1]) for (const sz of [-1,1]) set.add([sx,sy,sz].join(","));
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_trunc_oct_robust = () => {
    const set = new Set();
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    for (const p of perms([2,1,0])) {
      for (const s1 of [-1,1]) for (const s2 of [-1,1]) {
        const pt = [0,0,0]; pt[p[0]] = 2*s1; pt[p[1]] = 1*s2; set.add(pt.join(","));
      }
    }
    return createScaledTileData([...set].map(s => s.split(",").map(Number)), [], true);
  };

  const gen_elongated_dodecahedron = () => {
    const verts = [[2,0,0],[-2,0,0],[0,2,0],[0,-2,0],[0,0,4],[0,0,-4]];
    for (const x of [-1,1]) for (const y of [-1,1]) for (const z of [-1,1]) verts.push([x,y,2*z]);
    return createScaledTileData(verts, [], true);
  };

  const gen_hex_prism = () => {
    const perms = (arr) => {
      if (arr.length<=1) return [arr.slice()];
      const out=[];
      for (let i=0;i<arr.length;i++) {
        const rest=arr.slice(0,i).concat(arr.slice(i+1));
        for (const p of perms(rest)) out.push([arr[i],...p]);
      }
      return out;
    };
    const verts = [];
    for (const p of perms([1,-1,0])) verts.push([p[0]+1,p[1]+1,p[2]+1]);
    for (const p of perms([1,-1,0])) verts.push([p[0]-1,p[1]-1,p[2]-1]);
    return createScaledTileData(verts, [], true);
  };

  const gen_orthoscheme_robust = () => {
    const data = createScaledTileData(
      [[0,0,0],[2,0,0],[2,2,0],[2,2,2],[1,1,0],[2,1,1]],
      [
        {v:[0,1,4], type:"default"}, {v:[1,2,4], type:"default"},
        {v:[1,2,5], type:"default"}, {v:[2,3,5], type:"default"},
        {v:[0,1,3], type:"default"}, {v:[0,2,3], type:"default"},
      ], false
    );
    data.solid_angle = { kind: "rational", max_value: LEGACY_SOLID_ANGLE_MAX };
    return data;
  };

  const gen_gyrobifastigium_data = () => {
    const verts = [[1,1,0],[1,-1,0],[-1,-1,0],[-1,1,0],[0,1,2],[0,-1,2],[1,0,-2],[-1,0,-2]];
    return createScaledTileData(verts, [], true);
  };

  const gen_trunc_tetra_friauf = () => {
    const tips = [[0,0,0],[3,3,0],[3,0,3],[0,3,3]];
    const verts = [];
    for (let i=0;i<4;i++) for (let j=0;j<4;j++) if (j!==i) {
      const a=tips[i], b=tips[j];
      verts.push([a[0]+((b[0]-a[0])/3), a[1]+((b[1]-a[1])/3), a[2]+((b[2]-a[2])/3)]);
    }
    const uniq = new Map();
    for (const v of verts) uniq.set(v.join(","), v);
    const temp = createScaledTileData([...uniq.values()], [], true);
    temp.f_data = temp.f_data.map(f => ({ ...f, type: (f.v.length===3 ? "TRI_FACE" : "HEX_FACE") }));
    return temp;
  };

  const gen_escher_solid_data = () => {
    const core = gen_rhombic_robust();
    const verts = core.v.map(v => v.slice());
    const faces = [];
    const occ = new Map();
    const addOcc = (items) => {
      for (const [pos, weight] of items ?? []) {
        const key = pos.join(",");
        occ.set(key, (occ.get(key) ?? 0) + weight);
      }
    };
    addOcc(core.occ);

    for (const face of core.f_data) {
      const base = face.v.map(index => verts[index]);
      const center = base
        .reduce((sum, v) => add3(sum, v), [0, 0, 0])
        .map(c => Math.round(c / base.length));
      const apex = center.map(c => c * 2);
      const apexIndex = verts.length;
      verts.push(apex);

      for (let i = 0; i < face.v.length; i++) {
        faces.push({
          v: [face.v[i], face.v[(i + 1) % face.v.length], apexIndex],
          type: "ESCHER_SPIKE_WALL"
        });
      }

      const localVerts = base.map(v => v.slice()).concat([apex]);
      const localFaces = [
        [0, 1, 2, 3],
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
      ];
      addOcc(computeConvexOccupancy(localVerts, localFaces));
    }

    return {
      v: verts,
      f_data: faces,
      occ: [...occ.entries()].map(([key, weight]) => [key.split(",").map(Number), weight]),
      skip_winding: false
    };
  };

  const gen_letter_o_data = () => {
    const vox = [];
    for (let x = 0; x < 3; x++) for (let y = 0; y < 4; y++) {
      if (x === 1 && (y === 1 || y === 2)) continue;
      vox.push([x, y, 0]);
    }
    const data = generatePolycubeData(vox);
    const hollowSet = new Set(['1,1,0', '1,2,0']);
    const voxelSet = new Set(vox.map(v => v.join(',')));
    const dirs = [[1,0,0], [-1,0,0],[0,1,0], [0,-1,0],[0,0,1], [0,0,-1]];
    const faceInfo = new Map();
    const getFaceType = (vx, vy, vz, dx, dy, dz, neighbor) => {
      if (hollowSet.has(neighbor)) {
        if ((vy === 0 && dy === 1) || (vy === 3 && dy === -1)) return "inner_single";
        else return "inner_double";
      }
      const isOnPerimeter = (vx === 0 && dx === -1) || (vx === 2 && dx === 1) || (vy === 0 && dy === -1) || (vy === 3 && dy === 1) || (vz === 0 && dz === -1) || (vz === 0 && dz === 1);
      if (isOnPerimeter) return "outer_rim"; else return "outer_side";
    };
    for (const v of vox) {
      const [vx, vy, vz] = v;
      for (let d = 0; d < dirs.length; d++) {
        const [dx, dy, dz] = dirs[d];
        const nb = [vx + dx, vy + dy, vz + dz];
        const nbKey = nb.join(',');
        if (hollowSet.has(nbKey) || !voxelSet.has(nbKey)) {
          const faceType = getFaceType(vx, vy, vz, dx, dy, dz, nbKey);
          const key = `${vx},${vy},${vz},${dx},${dy},${dz}`;
          faceInfo.set(key, { voxel: v, normal: [dx, dy, dz], type: faceType });
        }
      }
    }
    const faceCenter = (faceIndices, vertices) => {
      const verts = faceIndices.map(i => vertices[i]);
      const sum = verts.reduce((acc, v) => [acc[0]+v[0], acc[1]+v[1], acc[2]+v[2]], [0,0,0]);
      return sum.map(c => c / verts.length);
    };
    const estimateNormal = (faceIndices, vertices) => {
      if (faceIndices.length < 3) return [0,0,0];
      const v0 = vertices[faceIndices[0]], v1 = vertices[faceIndices[1]], v2 = vertices[faceIndices[2]];
      const e1 = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]];
      const e2 = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]];
      const nx = e1[1]*e2[2] - e1[2]*e2[1], ny = e1[2]*e2[0] - e1[0]*e2[2], nz = e1[0]*e2[1] - e1[1]*e2[0];
      const len = Math.sqrt(nx*nx + ny*ny + nz*nz);
      if (len < 0.0001) return [0,0,0];
      return [nx/len, ny/len, nz/len];
    };
    for (let i = 0; i < data.f_data.length; i++) {
      const face = data.f_data[i];
      const center = faceCenter(face.v, data.v);
      const normal = estimateNormal(face.v, data.v);
      let matched = false;
      for (const [key, info] of faceInfo.entries()) {
        const [vx, vy, vz, dx, dy, dz] = key.split(',').map(Number);
        const facePos = [vx + (dx > 0 ? 1 : dx < 0 ? 0 : 0.5), vy + (dy > 0 ? 1 : dy < 0 ? 0 : 0.5), vz + (dz > 0 ? 1 : dz < 0 ? 0 : 0.5)].map(p => p * 2);
        const dist = Math.sqrt(Math.pow(center[0] - facePos[0], 2) + Math.pow(center[1] - facePos[1], 2) + Math.pow(center[2] - facePos[2], 2));
        const dot = normal[0]*dx + normal[1]*dy + normal[2]*dz;
        if (dist < 1.0 && dot > 0.7) { face.type = info.type; matched = true; break; }
      }
      if (!matched) {
        const voxelCenter = center.map(c => Math.round(c / 2));
        const isNearPerimeter = voxelCenter[0] === 0 || voxelCenter[0] === 3 || voxelCenter[1] === 0 || voxelCenter[1] === 4 || voxelCenter[2] === 0 || voxelCenter[2] === 1;
        if (isNearPerimeter) face.type = "outer_rim"; else face.type = "outer_side";
      }
    }
    return data;
  };

  const gen_1cross_plus_data = () => generatePolycubeData([[0,0,0],[1,0,0], [-1,0,0],[0,1,0], [0,-1,0],[0,0,1], [0,0,-1],[2,0,0]]);

  // --- Barlow Packing Generators (FCC/HCP Voronoi Cells) ---
  const gen_barlow_polyhedra = () => {
    // 1. Rhombic Dodecahedron (FCC)
    // Vertices scaled x3 to avoid fractions during reflection
    // Standard RD vertices: perms of (±2,0,0) -> (±6,0,0) and (±1,±1,±1) -> (±3,±3,±3)
    const rd_verts = [
      [3,3,3], [-3,-3,-3], // Poles
      [6,0,0], [0,6,0], [0,0,6], // Top Shoulders
      [-6,0,0], [0,-6,0], [0,0,-6], // Bottom Shoulders
      [3,3,-3], [3,-3,3], [-3,3,3], // Top Waist (Equator)
      [-3,-3,3], [-3,3,-3], [3,-3,-3] // Bottom Waist
    ];
    const rd_data = createScaledTileData(rd_verts, [], true);
    
    // 2. Trapezo-Rhombic Dodecahedron (HCP)
    // Construct by taking Top Half of RD and Reflecting it across x+y+z=0
    // Reflection formula: v' = v - 2 * (dot(v,n)/dot(n,n)) * n, where n=[1,1,1], dot(n,n)=3
    // v' = v - 2/3 * sum(v) * [1,1,1]
    const trd_verts = [];
    
    // Add Top Half (including equator)
    trd_verts.push([3,3,3]); // Pole
    trd_verts.push([6,0,0], [0,6,0], [0,0,6]); // Top Shoulders
    trd_verts.push([3,3,-3], [3,-3,3], [-3,3,3]); // Top Waist (Equator)

    // Reflect Top Half to create Bottom Half
    const reflect = (v) => {
      const sum = v[0]+v[1]+v[2];
      const k = (2 * sum) / 3;
      return [v[0]-k, v[1]-k, v[2]-k];
    };
    trd_verts.push(reflect([3,3,-3]), reflect([3,-3,3]), reflect([-3,3,3])); // Bottom Waist
    trd_verts.push(reflect([6,0,0]), reflect([0,6,0]), reflect([0,0,6])); // Bottom Shoulders
    trd_verts.push(reflect([3,3,3])); // Bottom Pole

    const trd_data = createScaledTileData(trd_verts, [], true);
    trd_data.f_data.forEach(f => {
      if (f.v.length === 4) f.type = "TRD_TRAP"; else f.type = "TRD_RHOMB";
    });

    return { rd: rd_data, trd: trd_data };
  };

  // --- Registry (complete) ---
  const TILING_REGISTRY = {
    "1_cross": { name:"1-Cross (Heptacube)", category:["Polycubes"], build: () => [make_tile("1-Cross", gen_n_cross_data(1))] },
    "2_cross": { name:"2-Cross (Tridecacube)", category:["Polycubes"], build: () => [make_tile("2-Cross", gen_n_cross_data(2))] },
    "3_cross": { name:"3-Cross (Nonadecacube)", category:["Polycubes"], build: () => [make_tile("3-Cross", gen_n_cross_data(3))] },
    "t_cross": { name:"T-Cross", category:["Polycubes"], build: () => [make_tile("T-Cross", (() => {
      const arm = 3;
      const vox = new Set();
      const dirs = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
      vox.add([0,0,0].join(","));
      const basis = [[0,1,0],[0,0,1],[1,0,0]];
      for (const d of dirs) {
        for (let i=1;i<=arm;i++) vox.add([i*d[0],i*d[1],i*d[2]].join(","));
        const end = [arm*d[0],arm*d[1],arm*d[2]];
        const bar = basis.find(b => Math.abs(dot3(b,d)) < 0.1);
        vox.add([end[0]+bar[0], end[1]+bar[1], end[2]+bar[2]].join(","));
        vox.add([end[0]-bar[0], end[1]-bar[1], end[2]-bar[2]].join(","));
      }
      return generatePolycubeData([...vox].map(s => s.split(",").map(Number)));
    })())] },
    "1_semicross": { name:"1-Semicross (Tripod)", category:["Polycubes"], build: () => [make_tile("1-Semi", gen_n_semicross_data(1))] },
    "2_semicross": { name:"2-Semicross (Corner)", category:["Polycubes"], build: () => [make_tile("2-Semi", gen_n_semicross_data(2))] },
    "buckled_ring": { name:"Buckled Ring", category:["Polycubes"], build: () => [make_tile("BuckledRing", gen_buckled_ring_data())] },
    "large_buckled_ring": { name:"Large Buckled Ring", category:["Polycubes"], build: () => [make_tile("LargeRing", gen_large_buckled_ring_data())] },
    "double_ring": { name:"Double Buckled Ring", category:["Polycubes"], build: () => [make_tile("DoubleRing", gen_double_ring_data())] },
    "tuning_fork": { name:"Tuning Fork (Reinhardt)", category:["Polycubes"], build: () => [make_tile("Fork", gen_tuning_fork())] },
    "twisted_h": { name:"Letter H (Twisted)", category:["Polycubes"], build: () => [make_tile("TwistedH", gen_twisted_h_data())] },
    "cube": { name:"Cube", category:["Fedorov Solids","Polycubes"], build: () => [make_tile("Cube", gen_cube_data())] },
    "letter_o": {
      name: "Letter O", category: ["Polycubes"],
      build: () => [make_tile("LetterO", gen_letter_o_data())]
    },
    "1_cross_plus": { name:"1-Cross + 1", category:["Polycubes"], build: () => [make_tile("1CrossPlus", gen_1cross_plus_data())] },
    "hex_prism": { name:"Hexagonal Prism", category:["Fedorov Solids"], build: () => [make_tile("HexPrism", gen_hex_prism())] },
    "rhombic": { name:"Rhombic Dodecahedron", category:["Fedorov Solids"], build: () => [make_tile("RhombicDod", gen_rhombic_robust())] },
    "elongated_dod": { name:"Elongated Dodecahedron", category:["Fedorov Solids"], build: () => [make_tile("ElongatedDod", gen_elongated_dodecahedron())] },
    "trunc_oct": { name:"Truncated Octahedron", category:["Fedorov Solids"], build: () => [make_tile("TruncOct", gen_trunc_oct_robust())] },
    "twist": { name:"Twist (Tetracube)", category:["Polycubes"], build: () => [make_tile("Twist", gen_s_tetracube())] },
    "knuckle": { name:"Knuckle (Pentacube)", category:["Polycubes"], build: () => [make_tile("Knuckle", gen_knuckle_pentacube())] },
    "tet_oct": { name:"Tetrahedron + Octahedron", category:["Platonic Solids"], build: () => [ make_tile("Tetrahedron", gen_tetrahedron_data()), make_tile("Octahedron", gen_octahedron_data()) ] },
    "tetragonal_disphenoid": { name:"Tetragonal Disphenoid (B₃ alcove)", category:["Space Fillers"], build: () => [make_tile("Disphenoid", gen_tetragonal_disphenoid_data())] },
    "corner_tetra": { name:"Corner Tetrahedron", category:["Space Fillers"], build: () => [make_tile("CornerTetra", gen_corner_tetra_data())] },
    "big_corner_tetra": { name:"Big Corner Tetrahedron", category:["Space Fillers"], build: () => [make_tile("BigCornerTetra", gen_big_corner_tetra_data())] },
    "diamond_lattice": {
      name:"Double FCC Lattice (Diamond)", category:["Platonic Solids"],
      build: () => [ make_tile("Tetrahedron", gen_tetrahedron_data()), make_tile("Octahedron", gen_octahedron_data()), make_tile("CornerTetra", gen_corner_tetra_data()) ],
      default_viz: { opacities:[0.9,0.1,0.1], internal:true }
    },
    "perovskite": { name:"Perovskite (Cuboctahedron + Octa)", category:["Platonic Solids"], build: () => [ make_tile("Cuboctahedron", gen_cuboctahedron_data()), make_tile("Octahedron", gen_octahedron_data()) ], default_viz: { opacities:[0.5,0.9], internal:true } },
    "orthoscheme": { name:"Orthoscheme (B̃₃ alcove)", category:["Space Fillers"], build: () => [make_tile("Orthoscheme", gen_orthoscheme_robust())], default_viz: { opacities:[0.6], internal:true } },
    "elongated_sq_bipyramid": { name:"Elongated Bipyramid (J15)", category:["Space Fillers"], build: () => [make_tile("Johnson15", gen_elongated_square_bipyramid())] },
    "gyrobifastigium": { name:"Gyrobifastigium (J26)", category:["Space Fillers"], build: () => [make_tile("Johnson26", gen_gyrobifastigium_data())] },
    "laves_c15": { name:"Laves C15 (Truncated Tetra + Tetra))", category:["Platonic Solids"], build: () => [ make_tile("TruncTetra", gen_trunc_tetra_friauf()), make_tile("Tetra", gen_tetrahedron_data()) ], default_viz: { opacities:[0.4,1.0], internal:true } },
    "escher_compound": {
      name:"Escher Solid", category:["Space Fillers"],
      build: () => [make_tile("EscherSolid", gen_escher_solid_data())],
      default_viz: { opacities:[0.85], internal:true }
    },
    "fcc_pure": {
      name: "FCC (Pure Rhombic Dodecahedron)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd } = gen_barlow_polyhedra();
        return [make_tile("Rhombic_Dodecahedron_(FCC)", rd)];
      },
      default_viz: { opacities: [0.9], internal: true }
    },
    "hcp_pure": {
      name: "HCP (Pure Trapezo-Rhombic Dodecahedron)",
      category: ["Sphere Packings"],
      build: () => {
        const { trd } = gen_barlow_polyhedra();
        return [make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd)];
      },
      default_viz: { opacities: [0.9], internal: true }
    },
    "barlow_fcc": {
      name: "Barlow Packing (Root: FCC)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd, trd } = gen_barlow_polyhedra();
        return [
          make_tile("Rhombic_Dodecahedron_(FCC)", rd),
          make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd)
        ];
      },
      default_viz: { opacities: [0.8, 0.8], internal: true }
    },
    "barlow_hcp": {
      name: "Barlow Packing (Root: HCP)",
      category: ["Sphere Packings"],
      build: () => {
        const { rd, trd } = gen_barlow_polyhedra();
        return [
          make_tile("Trapezo_Rhombic_Dodecahedron_(HCP)", trd),
          make_tile("Rhombic_Dodecahedron_(FCC)", rd)
        ];
      },
      default_viz: { opacities: [0.8, 0.8], internal: true }
    }
  };

  const latticeFaceSignature = (verts) => {
    const mins = [Infinity, Infinity, Infinity];
    for (const v of verts) for (let i = 0; i < 3; i++) mins[i] = Math.min(mins[i], v[i]);
    return verts
      .map(v => [v[0] - mins[0], v[1] - mins[1], v[2] - mins[2]].join(","))
      .sort()
      .join("|");
  };

  const tileFaceSignatures = (tile) => {
    const signatures = new Set();
    for (const orient of tile.unique_orientations ?? []) {
      for (const face of orient.faces ?? []) {
        signatures.add(latticeFaceSignature(face.map(i => orient.verts[i])));
      }
    }
    return [...signatures].sort();
  };

  const displayTileNameMap = new Map([
    ["Tetra", "Tetrahedron"],
    ["Octa", "Octahedron"],
    ["BuckledRing", "Buckled Ring"],
    ["LargeRing", "Large Buckled Ring"],
    ["DoubleRing", "Double Buckled Ring"],
    ["Fork", "Tuning Fork"],
    ["TwistedH", "Letter H"],
    ["LetterO", "Letter O"],
    ["1CrossPlus", "1-Cross + 1"],
    ["HexPrism", "Hexagonal Prism"],
    ["RhombicDod", "Rhombic Dodecahedron"],
    ["ElongatedDod", "Elongated Dodecahedron"],
    ["TruncOct", "Truncated Octahedron"],
    ["Disphenoid", "Tetragonal Disphenoid"],
    ["CornerTetra", "Corner Tetrahedron"],
    ["BigCornerTetra", "Big Corner Tetrahedron"],
    ["Johnson15", "Elongated Bipyramid"],
    ["Johnson26", "Gyrobifastigium"],
    ["TruncTetra", "Truncated Tetrahedron"],
    ["EscherSolid", "Escher Solid"],
    ["Rhombic_Dodecahedron_(FCC)", "Rhombic Dodecahedron"],
    ["Trapezo_Rhombic_Dodecahedron_(HCP)", "Trapezo-Rhombic Dodecahedron"]
  ]);

  const displayTileName = (name) => {
    const sourceName = String(name ?? "Tile");
    const reflected = sourceName.startsWith("reflected ");
    const baseName = reflected ? sourceName.slice("reflected ".length) : sourceName;
    const cleaned = displayTileNameMap.get(baseName)
      ?? baseName
        .replace(/_\((FCC|HCP)\)$/i, "")
        .replace(/\s*\((FCC|HCP|Root:\s*(FCC|HCP))\)\s*$/i, "")
        .replace(/_/g, " ");
    return `${reflected ? "reflected " : ""}${cleaned}`;
  };

  const canonicalFigureName = displayTileName;

  const solidAngleValues = (tile) => {
    const maxValue = tile?.solid_angle?.max_value ?? LEGACY_SOLID_ANGLE_MAX;
    return (tile?.occupancy_points ?? [])
      .map(point => ({ weight: point.weight, symbolic: point.symbolic, display_symbolic: point.display_symbolic, kind: point.kind }))
      .filter(item => Number.isFinite(item.weight))
      .sort((a, b) => a.weight - b.weight)
      .map(item => ({ weight: item.weight, max_value: maxValue, value: item.weight / maxValue, symbolic: item.symbolic, display_symbolic: item.display_symbolic, kind: item.kind }));
  };

  const tileGeometryKey = (tile) => {
    const verts = (tile.verts ?? []).map(v => v.join(",")).sort().join("|");
    const faces = (tile.faces ?? [])
      .map(face => face.map(i => tile.verts[i].join(",")).sort().join(";"))
      .sort()
      .join("|");
    const occupancy = (tile.occupancy_points ?? [])
      .map(point => `${point.pos.join(",")}:${point.weight}`)
      .sort()
      .join("|");
    return `${verts}@@${faces}@@${occupancy}`;
  };

  const metadata = {};
  for (const [k,v] of Object.entries(TILING_REGISTRY)) {
    const tiles = v.build();
    metadata[k] = { name: v.name, category: v.category || [], is_chiral: !!tiles[0]?.is_chiral, default_viz: v.default_viz || {} };
  }
  const categories = new Map();
  for (const [k,meta] of Object.entries(metadata)) {
    for (const c of (meta.category || ["Other"])) {
      if (!categories.has(c)) categories.set(c, []);
      categories.get(c).push({ id: k, name: meta.name });
    }
  }
  const options = [...categories.entries()]
    .sort((a,b)=>a[0].localeCompare(b[0]))
    .map(([group, tiles]) => ({ group, tiles: tiles.sort((a,b)=>a.name.localeCompare(b.name)) }));

  const figureCatalog = [];
  const figureDedupe = new Map();
  const figureAliases = new Map();
  for (const [modeKey, entry] of Object.entries(TILING_REGISTRY)) {
    const tiles = entry.build();
    tiles.forEach((tile, tileIndex) => {
      const sourceId = `${modeKey}::${tileIndex}`;
      const name = canonicalFigureName(tile.name);
      const key = `${name}@@${tileGeometryKey(tile)}`;
      let figure = figureDedupe.get(key);
      if (!figure) {
        figure = {
          id: sourceId,
          mode_key: modeKey,
          tile_index: tileIndex,
          name,
          system_name: entry.name,
          system_names: [entry.name],
          category: [...(entry.category || ["Other"])],
          is_chiral: !!tile.is_chiral,
          solid_angle: tile.solid_angle,
          solid_angles: solidAngleValues(tile),
          signatures: tileFaceSignatures(tile),
          aliases: [sourceId]
        };
        figureDedupe.set(key, figure);
        figureCatalog.push(figure);
      } else {
        figure.aliases.push(sourceId);
        if (!figure.system_names.includes(entry.name)) figure.system_names.push(entry.name);
        for (const category of (entry.category || ["Other"])) {
          if (!figure.category.includes(category)) figure.category.push(category);
        }
        figure.is_chiral = figure.is_chiral || !!tile.is_chiral;
      }
      figureAliases.set(sourceId, figure);
    });
  }

  const figuresShareLatticeFace = (a, b) => {
    const signatures = new Set(a.signatures ?? []);
    return (b.signatures ?? []).some(sig => signatures.has(sig));
  };
  for (const figure of figureCatalog) {
    figure.compatible_ids = figureCatalog
      .filter(other => figuresShareLatticeFace(figure, other))
      .map(other => other.id);
  }

  const figureMetadata = figureAliases;

  const addMirrorsIfChiral = (tiles) => {
    const out = tiles.slice();
    for (const t of tiles) {
      if (t.is_chiral) {
        const m = t.get_mirror_copy();
        if (m) out.push(m);
      }
    }
    return out;
  };

  const normalizeVoxels = (voxels) => {
    const unique = new Map();
    for (const voxel of voxels ?? []) {
      if (!Array.isArray(voxel) || voxel.length < 3) continue;
      const v = voxel.slice(0, 3).map(n => Math.trunc(Number(n)));
      if (v.some(n => !Number.isFinite(n))) continue;
      unique.set(v.join(","), v);
    }
    const out = [...unique.values()];
    if (!out.length) return [[0, 0, 0]];
    const mins = [Infinity, Infinity, Infinity];
    for (const v of out) for (let i = 0; i < 3; i++) mins[i] = Math.min(mins[i], v[i]);
    return out.map(v => [v[0] - mins[0], v[1] - mins[1], v[2] - mins[2]]);
  };

  const buildPolycubeTile = (name, voxels, options = {}) =>
    make_tile(name || "CustomPolycube", generatePolycubeData(normalizeVoxels(voxels), options));

  const buildCustomSystem = (customSystem = {}) => {
    const figureRefs = [...new Map(
      [...new Set(customSystem.figure_refs ?? [])]
        .map(id => figureMetadata.get(id))
        .filter(Boolean)
        .map(ref => [ref.id, ref])
    ).values()];
    const tileIds = [...new Set(customSystem.tile_ids ?? [])].filter(id => TILING_REGISTRY[id]);
    const customPolycubes = customSystem.polycubes ?? [];
    const customName = customSystem.name || "Mixed system";
    const polycubeLattice = customSystem.polycube_lattice === "d3" ? "d3" : "z3";
    const buildWithPolycubeLattice = (builder) => {
      const previous = activePolycubeLattice;
      activePolycubeLattice = polycubeLattice;
      try {
        return builder();
      } finally {
        activePolycubeLattice = previous;
      }
    };
    return {
      name: customName,
      category: ["Mixed"],
      default_viz: { opacities: [], internal: false },
      build: () => buildWithPolycubeLattice(() => {
        const built = [];
        if (figureRefs.length) {
          for (const ref of figureRefs) {
            const tiles = TILING_REGISTRY[ref.mode_key].build();
            const tile = tiles[ref.tile_index];
            if (tile) built.push(tile);
          }
        } else {
          for (const id of tileIds) built.push(...TILING_REGISTRY[id].build());
        }
        customPolycubes.forEach((poly, index) => {
          const name = poly?.name || `CustomPolycube${index + 1}`;
          built.push(buildPolycubeTile(name, poly?.voxels ?? [[0, 0, 0]], { polycube_lattice: polycubeLattice }));
        });
        return built.length ? built : TILING_REGISTRY.cube.build();
      })
    };
  };

  return {
    SCALE,
    POLYCUBE_SOLID_ANGLE_MAX,
    LEGACY_SOLID_ANGLE_MAX,
    COLOR_PALETTE,
    TILING_REGISTRY,
    metadata,
    options,
    figureCatalog,
    displayTileName,
    solidAngleValues,
    addMirrorsIfChiral,
    buildPolycubeTile,
    buildCustomSystem
  };
})();
