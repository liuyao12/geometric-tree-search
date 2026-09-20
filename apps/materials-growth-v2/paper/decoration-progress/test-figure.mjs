import assert from 'node:assert/strict';
const {chromium}=await import(process.argv[3]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage();await page.goto(process.argv[2],{waitUntil:'domcontentloaded'});
 const figure=page.locator('#decoration-progress');await figure.locator('.dp-cell').first().waitFor();
 for(const [lane,verified,unknown] of [['baseline',6,0],['poses',9,1],['union',10,1]]){
  await figure.locator(`[data-lane="${lane}"]`).click();
  assert.equal(await figure.locator('.dp-cell').count(),88);
  assert.equal(await figure.locator('.dp-cell[data-status=verified]').count(),verified);
  assert.equal(await figure.locator('.dp-cell[data-status=unknown]').count(),unknown);
 }
 await figure.locator('[data-id="oxalic-beta-0135"]').focus();await page.keyboard.press('Enter');
 assert.match(await figure.locator('[data-dp-detail]').innerText(),/Verified: 16 atom sites \+ 14 activated latent sites/);
 await figure.locator('[data-id="oxalic-beta-0163"]').click();assert.match(await figure.locator('[data-dp-detail]').innerText(),/Unknown/);
 await figure.locator('[data-id="oxalic-alpha-0130"]').click();assert.match(await figure.locator('[data-dp-detail]').innerText(),/does not prove/);
 assert.match(await figure.innerText(),/No material family is yet validated end to end/);
 const evidence=await page.evaluate(async()=>await(await fetch('decoration-progress/results.json')).json());
 for(const lane of evidence.lanes){const receipt=await(await page.request.get(new URL(`decoration-progress/${lane.id}-check.json`,process.argv[2]).href)).json();assert.deepEqual(lane.rows.filter(r=>r.status==='verified').map(r=>r.id).sort(),receipt.positiveWitnesses.map(r=>r.configuration).sort());}
 for(const href of await figure.locator('a').evaluateAll(nodes=>nodes.map(n=>n.href)))assert.equal((await page.request.get(href)).status(),200);
 await figure.screenshot({path:'/tmp/gcts-decoration-progress-desktop.png'});
 await page.setViewportSize({width:390,height:844});await figure.screenshot({path:'/tmp/gcts-decoration-progress-mobile.png'});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 console.log('PASS: 6/9/10 receipts, 88 frames each, keyboard, unknown/failure states, links, desktop/mobile layout');
}finally{await browser.close();}
