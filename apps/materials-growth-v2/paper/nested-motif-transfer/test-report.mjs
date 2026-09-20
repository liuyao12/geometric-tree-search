import assert from 'node:assert/strict';
const {chromium}=await import(process.argv[3]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage();await page.goto(process.argv[2],{waitUntil:'domcontentloaded'});
 const figure=page.locator('#nested-motif-transfer');await figure.scrollIntoViewIfNeeded();
 assert.match(await figure.innerText(),/not learned connections/);
 const data=await page.evaluate(async()=>{const r=await fetch('nested-motif-transfer/check.json');return r.json();});
 assert.deepEqual(data.summary.map(r=>r.fullyMatched),[44,44]);assert.equal(data.sharedAcrossTrainingPhases,24);
 await page.locator('#offatom-interface-test summary').click();
 const interfaces=await page.evaluate(async()=>{const r=await fetch('nested-motif-transfer/interface-check.json');return r.json();});
 assert.equal(interfaces.frozenModelFailureCounts.matched,17);assert.equal(interfaces.frozenModelFailureCounts.anchorCoincidenceFails,82);
 const continuous=await page.evaluate(async()=>{const r=await fetch('nested-motif-transfer/continuous-check.json');return r.json();});
 assert.deepEqual(continuous.summary.map(r=>r.refittedMatched),[22,32]);
 assert.match(await page.locator('#offatom-interface-test').innerText(),/unconstrained in GCTS/);
 for(const href of await figure.locator('a').evaluateAll(nodes=>nodes.map(n=>n.href))){assert.equal((await page.request.get(href)).status(),200);}
 await figure.screenshot({path:'/tmp/gcts-nested-report-desktop.png'});
 await page.setViewportSize({width:390,height:844});await figure.screenshot({path:'/tmp/gcts-nested-report-mobile.png'});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 console.log('PASS: published counts, evidence links, desktop/mobile layout');
}finally{await browser.close();}
