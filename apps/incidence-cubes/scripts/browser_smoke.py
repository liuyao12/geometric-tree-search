"""Smoke-test the actual HTML/CSS/JS without depending on external network access.
Requires Python Playwright and Chromium. Set CHROMIUM for a system executable.
"""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
html = (ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'style.css').read_text()+'</style>')
html = html.replace('<script defer src="engine.js"></script><script defer src="app.js"></script>','')
# Supply the local evidence file to the page's regular status loader.
fetch_stub = 'window.fetch=async()=>new Response('+json.dumps((ROOT/'verification.json').read_text())+',{status:200,headers:{"Content-Type":"application/json"}});'
html = html.replace('</body>','<script>'+fetch_stub+(ROOT/'engine.js').read_text()+'</script><script>'+(ROOT/'app.js').read_text()+'</script></body>')
results=[]
with sync_playwright() as p:
    options={'headless':True}
    executable=os.environ.get('CHROMIUM')
    if executable: options['executable_path']=executable
    browser=p.chromium.launch(**options)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='load');page.wait_for_timeout(100)
    page.locator('#follow').uncheck()
    page.locator('#complete').click()
    assert '12 edge identities' in page.locator('#readout').inner_text()
    assert '6 face-pencil checks' in page.locator('#readout').inner_text()
    page.locator('#inspect').select_option('edge:0')
    assert '2 real contact points' in page.locator('#readout').inner_text()
    page.locator('input[aria-label="a12"]').evaluate("e=>{e.value='0.70';e.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert abs(page.evaluate('incidenceApp.state.params.couplings[0]')-.70)<1e-12
    page.locator('#inspect').select_option('face:1')
    assert page.locator('.face-chip.active').count()==1
    results.append('Penrose completion, edge contacts, face selection and slider')
    page.locator('#tab-fomin').click()
    assert not page.locator('#chord-toggle').is_visible()
    assert '6 coherent faces' in page.locator('#readout').inner_text()
    page.locator('#reset').click();page.locator('#complete').click()
    assert page.evaluate('incidenceApp.getData().thirdError')<1e-8
    results.append('Fomin completion and visibility of mode-specific controls')
    page.locator('#tab-surface').click()
    assert not page.locator('#complete').is_visible()
    page.locator('#perturb').click()
    assert '2 face ratios differ' in page.locator('#readout').inner_text()
    assert 'exactly' in page.locator('#readout').inner_text()
    page.locator('#coherent').click()
    assert 'All six faces are coherent' in page.locator('#readout').inner_text()
    results.append('Exact surface perturbation and reset')
    page.locator('#tab-bridge').click()
    assert page.locator('.coeff-cell').count()==6
    assert not page.locator('#inspect').is_visible()
    page.locator('input[aria-label="pencil t"]').evaluate("e=>{e.value='1.20';e.dispatchEvent(new Event('input',{bubbles:true}))}")
    assert page.evaluate('incidenceApp.state.t')==1.2
    page.locator('#tab-bridge').focus();page.keyboard.press('ArrowRight')
    assert page.evaluate('incidenceApp.state.mode')=='penrose'
    results.append('Bridge hyperbola range and keyboard tab navigation')
    page.evaluate("window.scrollTo({top:420,behavior:'instant'})");page.wait_for_timeout(100)
    box=page.locator('#demo').bounding_box();assert box and box['y']>=0 and box['y']<100
    page.screenshot(path=str(ROOT.parent/'incidence-cubes-preview.png'))
    results.append('Desktop sticky panel, screenshot inspected separately')
    # Scroll following remains explicit and stops once a tab is clicked.
    page.locator('#follow').check()
    page.evaluate("document.querySelector('#surface').scrollIntoView({behavior:'instant'})");page.wait_for_timeout(200)
    assert page.evaluate('incidenceApp.state.mode')=='surface'
    page.locator('#tab-penrose').click();assert not page.locator('#follow').is_checked()
    results.append('Scroll-synchronized mode with manual override')
    for width,height in [(1000,800),(820,900),(390,844)]:
        page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500)
    page.screenshot(path=str(ROOT.parent/'incidence-cubes-mobile-preview.png'))
    results.append('No horizontal overflow at 1440, 1000, 820 and 390 pixels')
    assert not errors,errors
    browser.close()
record={'status':'passed','checks':results,'javascriptErrors':errors,'method':'Actual local assets assembled in Chromium; verification loader supplied with local verification.json. Not a live-site or Lean test.'}
(ROOT/'browser-test-results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
