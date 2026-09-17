// Usage: node test-report-visuals.mjs URL /absolute/path/to/playwright/index.mjs
import assert from 'node:assert/strict';
const {chromium}=await import(process.argv[3]);
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=swiftshader','--enable-webgl']});
try{
 const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.argv[2],{waitUntil:'domcontentloaded'});
 await page.waitForSelector('.rv-dot');assert.equal(await page.locator('.rv-dot').count(),100);assert.equal(await page.locator('.rv-dot[data-pass=false]').count(),0);
 await page.locator('[data-rv-mode=retained]').click();assert.equal(await page.locator('.rv-dot[data-pass=false]').count(),75);
 await page.locator('[data-rv-mode=complete]').click();
 await page.locator('#report-visual-overview').screenshot({path:'/tmp/gcts-report-overview.png'});
 await page.waitForFunction(()=>document.querySelector('[data-ice-status]').textContent.includes('fully filled'),{timeout:90000});
 const ice=page.locator('[data-ice-viewport] canvas');assert.equal(await page.locator('#rv-scene-slot canvas').count(),1);
 async function drag(canvas,pan=false){await canvas.scrollIntoViewIfNeeded();const b=await canvas.boundingBox();const before=await canvas.evaluate(c=>c.toDataURL());if(pan)await page.keyboard.down('Shift');await page.mouse.move(b.x+b.width*.5,b.y+b.height*.5);await page.mouse.down();await page.mouse.move(b.x+b.width*.5+65,b.y+b.height*.5+30,{steps:12});await page.mouse.up();if(pan)await page.keyboard.up('Shift');assert.notEqual(await canvas.evaluate(c=>c.toDataURL()),before);}
 await drag(ice);await drag(ice,true);await page.locator('[data-ice-mode=pan]').click();assert.equal(await page.locator('[data-ice-mode=pan]').getAttribute('aria-pressed'),'true');await drag(ice);await page.locator('[data-ice-reset]').click();
 await page.locator('#ice-inspection').screenshot({path:'/tmp/gcts-report-ice.png'});
 const silicon=page.locator('#prelim-canvas');await drag(silicon);await drag(silicon,true);await page.locator('#prelim-reset').click();assert.equal(await page.locator('#prelim-yaw').count(),0);
 await page.setViewportSize({width:390,height:844});await page.locator('#report-visual-overview').scrollIntoViewIfNeeded();
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile page overflows');
 await page.locator('.rv-results').screenshot({path:'/tmp/gcts-report-mobile.png'});
 assert.deepEqual(errors,[]);console.log('PASS: receipt matrix, orbit/pan in both scenes, reset controls, mobile width, no page errors');
}finally{await browser.close();}
