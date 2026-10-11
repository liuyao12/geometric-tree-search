"""Minimal display-only notation successor; no actual data/scientific imports."""
from pathlib import Path
OLD=Path('.gcts-active/automatic-geometry-reader-source-v3-20261011');OUT=Path('.gcts-active/automatic-geometry-reader-source-v4-20261011')
s=(OLD/'viewer.js').read_text()
a="  function termEnglish(ast) {"
b=r"""  function englishMath(value, command) {
    return '\(\' + command + '{' + escapeTex(value) + '}\)';
  }
  function termEnglish(ast) {"""
b=b.replace(chr(92),chr(92)*2)
assert s.count(a)==1;s=s.replace(a,b)
replacements=[
("'the object ' + ast[1]", "'the object ' + englishMath(ast[1], 'mathit')"),
("'the value of ' + ast[1]", "'the value of ' + englishMath(ast[1], 'operatorname')"),
("'the constant ' + ast[1]", "'the constant ' + englishMath(ast[1], 'operatorname')"),
("'The predicate ' + ast[1]", "'The predicate ' + englishMath(ast[1], 'operatorname')"),
("'For every choice of object ' + ast[1]", "'For every choice of object ' + englishMath(ast[1], 'mathit')"),
("' ' + String(command.name) + '.'", "' ' + englishMath(String(command.name), 'text') + '.'"),
("' over ' + String(command.variable)", "' over ' + englishMath(String(command.variable), 'mathit')"),
("'Apply the declared recipe ' + String(command.name)", "'Apply the declared recipe ' + englishMath(String(command.name), 'text')"),
("'Use the saved primitive rule ' + String(rule)", "'Use the saved primitive rule ' + englishMath(String(rule), 'text')")]
for a,b in replacements:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
(OUT/'viewer.js').write_text(s)
s=(OLD/'reader-source-controls.js').read_text()
a="let rejected = 0;"
b=r"""const englishControls = [
  [api.formulaEnglish(p), String.raw`\(\operatorname{P}\)`, String.raw`\(\mathit{A}\)`],
  [api.formulaEnglish(['eq', ['fun', 'c', []], v]), String.raw`\(\operatorname{c}\)`],
  [api.formulaEnglish(['pred', 'R', [['fun', 'f', [v]]]]), String.raw`\(\operatorname{f}\)`],
  [api.formulaEnglish(['all', 'x', p]), String.raw`\(\mathit{x}\)`],
  [api.formulaEnglish(['pred', 'P_\\{}$', [['var', 'A_\\{}$']]]), String.raw`\(\operatorname{P\_\backslash{}\{\}\$}\)`, String.raw`\(\mathit{A\_\backslash{}\{\}\$}\)`],
  [api.ruleEnglish({rule: 'generalize', variable: 'x_'}, [0], {}), String.raw`\(\mathit{x\_}\)`],
  [api.ruleEnglish({rule: 'axiom', name: 'A_$'}, [], {}), String.raw`\(\text{A\_\$}\)`],
  [api.ruleEnglish({rule: 'block', name: 'lemma_$'}, [0], {}), String.raw`\(\text{lemma\_\$}\)`],
  [api.ruleEnglish({rule: 'unknown_$'}, [], {}), String.raw`\(\text{unknown\_\$}\)`]
];
for (const [english, ...expected] of englishControls) for (const fragment of expected) assert(english.includes(fragment), english);
let rejected = 0;"""
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('passed_bounded_display_only_v3_controls','passed_bounded_display_only_v4_controls')
s=s.replace("    exact_core_certificate_semantics_fixture: true, exterior_sentinels_preserved: 23", "    exact_core_certificate_semantics_fixture: true, english_latex_controls: englishControls.length, english_identifiers_escaped: true, exterior_sentinels_preserved: 23")
(OUT/'reader-source-controls.js').write_text(s)
