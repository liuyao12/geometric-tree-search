import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const require = createRequire(import.meta.url);
const { marked } = await import(pathToFileURL(process.argv[2] || require.resolve('marked')).href);
const source = new URL('../research/knot-classifier/README.md', import.meta.url);
const math = [];
const text = readFileSync(source, 'utf8').replace(/\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/g, value => {
  const token = `KNOTMATHTOKEN${math.length}END`; math.push(value); return token;
});
const escape = x => x.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const body = marked.parse(text).replace(/KNOTMATHTOKEN(\d+)END/g, (_, n) => escape(math[Number(n)]));
const config = { tex: { inlineMath: [['\\(', '\\)']], displayMath: [['\\[', '\\]']] }, options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] } };
writeFileSync(new URL('../research/knot-classifier/plan.html', import.meta.url), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Knots as Reidemeister tiles · Research plan</title><link rel="stylesheet" href="../../apps/knot-movie/style.css"><script>window.MathJax=${JSON.stringify(config)};</script><script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>main{max-width:1100px}main>p,li{line-height:1.85;color:#c6d4d9}h1{font-size:52px}h2{margin-top:50px}table{display:block;overflow-x:auto;border-collapse:collapse;font-size:12px;line-height:1.65}td,th{padding:12px;border:1px solid #36454e;min-width:150px}th{text-align:left}code{font-size:.88em}pre{max-height:none}mjx-container[display=true]{overflow-x:auto;overflow-y:hidden;padding:8px 0}</style></head><body><main><a href="../../apps/knot-movie/">← Reidemeister Tile Lab</a>${body}</main></body></html>\n`);
