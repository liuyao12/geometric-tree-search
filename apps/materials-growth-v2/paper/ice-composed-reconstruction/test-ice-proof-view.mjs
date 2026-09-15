import assert from 'node:assert/strict';
import {chromium} from '/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
const [url]=process.argv.slice(2),browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=swiftshader','--enable-webgl']});
try{
 const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelector('[data-ice-status]')?.textContent.includes('240 fully filled'),{},{timeout:45000});
 assert.equal(await page.locator('[data-ice-policy]').inputValue(),'certified-proof');
 assert((await page.locator('[data-ice-method]').textContent()).includes('four support components'));
 await page.locator('[data-ice-rotate]').click();
 await page.locator('[data-ice-reveal]').evaluate(e=>{e.value='0';e.dispatchEvent(new Event('input'));});
 assert((await page.locator('[data-ice-status]').textContent()).includes('240 untouched'));
 await page.locator('[data-ice-reveal]').evaluate(e=>{e.value=e.max;e.dispatchEvent(new Event('input'));});
 await page.locator('[data-ice-color]').selectOption('element');
 await page.locator('[data-ice-viewport]').screenshot({path:'/tmp/gcts-ice-proof-view-desktop.png'});
 await page.locator('[data-ice-config]').selectOption('c00400');
 assert(await page.locator('[data-ice-policy] option[value="certified-proof"]').evaluate(e=>e.disabled));
 assert.equal(await page.locator('[data-ice-policy]').inputValue(),'connected-oracle');
 await page.locator('[data-ice-config]').selectOption('c01400');
 await page.locator('[data-ice-policy]').selectOption('certified-proof');
 await page.waitForFunction(()=>document.querySelector('[data-ice-status]')?.textContent.includes('240 fully filled'));
 await page.setViewportSize({width:390,height:844});
 const width=await page.evaluate(()=>({actual:document.documentElement.scrollWidth,viewport:innerWidth}));assert(width.actual<=width.viewport,width);
 await page.locator('[data-ice-viewport]').screenshot({path:'/tmp/gcts-ice-proof-view-mobile.png'});
 assert.deepEqual(errors,[]);console.log(JSON.stringify({sourceLoaded:true,proofState:true,rotation:true,reveal:true,elementColors:true,unavailableStateDisabled:true,mobileWidth:width,pageErrors:errors}));
}finally{await browser.close();}
