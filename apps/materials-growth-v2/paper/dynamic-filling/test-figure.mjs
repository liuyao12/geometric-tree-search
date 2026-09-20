import assert from 'node:assert/strict';
const {chromium}=await import(process.argv[3]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage();await page.goto(process.argv[2],{waitUntil:'domcontentloaded'});
 const figure=page.locator('#dynamic-filling');await figure.locator('.df-cells button').first().waitFor();
 assert.equal(await figure.locator('.df-cells button').count(),88);
 assert.equal(await figure.locator('.df-cells button[data-verified=true]').count(),6);
 const data=await page.evaluate(async()=>({results:await(await fetch('dynamic-filling/results.json')).json(),check:await(await fetch('dynamic-filling/check.json')).json()}));
 assert.deepEqual(data.results.rows.filter(r=>r.verified).map(r=>r.id).sort(),data.check.positiveWitnesses.map(r=>r.configuration).sort());
 assert.equal(data.results.weightSummary.freeParameters,4612);
 await figure.locator('[data-df-stage="0"]').click();assert.match(await figure.locator('[data-df-state]').innerText(),/^0 filled points/);
 await figure.locator('[data-df-stage="1"]').click();assert.match(await figure.locator('[data-df-points] svg').getAttribute('aria-label'),/after 1 placements/);
 await figure.locator('[data-df-stage="2"]').click();assert.match(await figure.locator('[data-df-state]').innerText(),/30 filled points.*14 active latent points/);
 await figure.locator('[data-id="oxalic-alpha-0130"]').click();assert.equal(await figure.locator('[data-df-stage="1"]').isDisabled(),true);assert.match(await figure.locator('[data-df-case]').innerText(),/does not prove/);
 await figure.locator('[data-id="oxalic-beta-0155"]').focus();await page.keyboard.press('Enter');assert.match(await figure.locator('[data-df-case]').innerText(),/416 candidate placements/);
 for(const href of await figure.locator('a').evaluateAll(nodes=>nodes.map(n=>n.href)))assert.equal((await page.request.get(href)).status(),200);
 await figure.screenshot({path:'/tmp/gcts-dynamic-report-desktop.png'});
 await page.setViewportSize({width:390,height:844});await figure.screenshot({path:'/tmp/gcts-dynamic-report-mobile.png'});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 assert.match(await figure.innerText(),/not blind growth/);
 console.log('PASS: 88 frames, six receipts, stage controls, keyboard, failure state, evidence links, desktop/mobile layout');
}finally{await browser.close();}
