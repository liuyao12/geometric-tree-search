"""UI-only minimal successor; reads frozen reader source, never scientific data."""
from pathlib import Path
OUT=Path('.gcts-active/automatic-geometry-reader-source-v3-20261011')
OLD=Path('.gcts-active/automatic-geometry-reader-source-v2-20261011')
s=(OLD/'viewer.js').read_text()
a="""    for (const q of graph.marks) if (q[0] === 1) {
      need(q[2] >= 0 && q[2] < data.formula_codes.length, 'Every blue snapshot constraint uses an exact formula code'); formulaLatex(data.formula_codes[q[2]]);
    }"""
b="""    for (const q of graph.marks) if (q[0] === 1) {
      if (q[1] < 0) {
        need(q[2] === -1, 'Exterior blue boundary mark must be the exact exclusion sentinel -1');
      } else {
        need(q[2] >= 0 && q[2] < data.formula_codes.length, 'Every interior blue snapshot constraint uses an exact formula code'); formulaLatex(data.formula_codes[q[2]]);
      }
    }"""
assert s.count(a)==1;s=s.replace(a,b)
a="""      if (q[0] === 1) {
        paragraph(mark, snapshot.selected.has(q[1]) ? 'Selected output constraint' : 'Pending output receptor; no selected square at this row');
        math(mark, formulaLatex(data.formula_codes[q[2]])); paragraph(mark, formulaEnglish(data.formula_codes[q[2]]));
        mark.hidden = !formulaLayer;
      } else if (q[0] >= 2) { paragraph(mark, 'Saved ordered reference-offset marking'); mark.hidden = !referenceLayer; }"""
b="""      if (q[0] === 1) {
        if (q[1] < 0) {
          paragraph(mark, 'Exterior boundary exclusion sentinel');
          // This literal assigned mark is not a formula code. Keep every exterior point visible.
        } else {
          paragraph(mark, snapshot.selected.has(q[1]) ? 'Selected output constraint' : 'Pending output receptor; no selected square at this row');
          math(mark, formulaLatex(data.formula_codes[q[2]])); paragraph(mark, formulaEnglish(data.formula_codes[q[2]]));
          mark.hidden = !formulaLayer;
        }
      } else if (q[0] >= 2) { paragraph(mark, 'Saved ordered reference-offset marking'); mark.hidden = !referenceLayer; }"""
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("      paragraph(mark, 'Saved reference count: ' + q[3]);", "      math(mark, '\\\\operatorname{refcount}(' + q[0] + ',' + q[1] + ')=' + q[3]);")
(OUT/'viewer.js').write_text(s)
s=(OLD/'reader-source-controls.js').read_text()
s=s.replace("  // Actual fixed target-style mark is assigned even with zero occupancy.", "  // Synthetic exterior boundary assignments follow the source schema; no formula decoding.")
s=s.replace("  marks.set('1,23', [1, 23, 1, 1]);", "  for (let row = -23; row < 0; row++) marks.set('1,' + row, [1, row, -1, 1]);\n  marks.set('1,23', [1, 23, 1, 1]);")
s=s.replace("assert.strictEqual(snap.marks.length, laterFirst.projection.graph.marks.length);", "assert.strictEqual(snap.marks.length, laterFirst.projection.graph.marks.length);\nassert.strictEqual(snap.marks.filter(mark => mark[0] === 1 && mark[1] < 0 && mark[2] === -1).length, 23);")
s=s.replace("  s => { s.projection.graph.order.push([0, 18, []]); }", "  s => { s.projection.graph.order.push([0, 18, []]); },\n  s => { s.projection.graph.marks.find(mark => mark[0] === 1 && mark[1] === -1)[2] = 0; },\n  s => { s.projection.graph.marks.find(mark => mark[0] === 1 && mark[1] === -1)[2] = -2; },\n  s => { s.projection.graph.marks.find(mark => mark[0] === 1 && mark[1] === 23)[2] = -1; }")
s=s.replace("  await api.mount({...data, observations: [observation]});", "  let sentinelDecodes = 0;\n  const guardedCodes = new Proxy(data.formula_codes, {get(target, property, receiver) {\n    if (property === '-1') { sentinelDecodes++; throw new Error('Exterior sentinel must never be decoded as a formula'); }\n    return Reflect.get(target, property, receiver);\n  }});\n  await api.mount({...data, formula_codes: guardedCodes, observations: [observation]});")
s=s.replace("  assert(text(ids['trace-view']).includes('All assigned snapshot marking points'));", "  assert(text(ids['trace-view']).includes('All assigned snapshot marking points'));\n  assert.strictEqual(text(ids['trace-view']).split('Exterior boundary exclusion sentinel').length - 1, 23);")
s=s.replace("  assert.strictEqual(ids['trace-event'].value, '0');\n  console.log", "  assert.strictEqual(ids['trace-event'].value, '0');\n  assert.strictEqual(text(ids['trace-view']).split('Exterior boundary exclusion sentinel').length - 1, 23);\n  assert.strictEqual(sentinelDecodes, 0);\n  console.log")
s=s.replace('passed_bounded_display_only_v2_controls','passed_bounded_display_only_v3_controls')
s=s.replace("    exact_core_certificate_semantics_fixture: true, synthetic_dom_only: true,", "    exact_core_certificate_semantics_fixture: true, exterior_sentinels_preserved: 23, exterior_invalid_variants_rejected: 3, sentinel_formula_decodes: sentinelDecodes, synthetic_dom_only: true,")
(OUT/'reader-source-controls.js').write_text(s)
