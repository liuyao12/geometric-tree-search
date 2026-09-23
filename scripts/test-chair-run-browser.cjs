const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = process.env.CHAIR_TEST_URL ?? 'http://127.0.0.1:8765/3d-reptiles/';

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}),
    args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
  });
  try {
    for (const reducedMotion of ['no-preference', 'reduce']) {
      const page = await browser.newPage({ reducedMotion });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      // Inspect rendered frames without adding a debugging API to the page.
      await page.route('**/chair/app.js?*', async route => {
        const response = await route.fetch();
        await route.fulfill({ response, body: (await response.text()) + `
          window.runCheck = {
            frames: 0, violations: [], saved: new Map(),
            save(name) { this.saved.set(name, growthState); },
            restored(name) { return this.saved.get(name) === growthState; },
            savedInflation: null,
            saveInflation() {
              this.savedInflation = currentInflationState;
              this.savedTarget = controls.target.toArray();
            },
            retainedInflation() {
              const expected = this.savedInflation.leaves;
              return expected.every((tile, i) => {
                const actual = growthState.placements[i];
                return actual && actual.variantId === tile.variantId
                  && actual.origin.every((v, axis) => v === tile.origin[axis]);
              });
            },
            sameTarget() { return controls.target.toArray().every((v, i) => Math.abs(v - this.savedTarget[i]) < 1e-9); },
            sameInflation() { return this.savedInflation === currentInflationState; },
            read: () => ({ count: growthState.placements.length, running: autoRun,
              transitioning: Boolean(transition), queued: runTimer !== null,
              complete: growthState.complete, status: growthState.status,
              mode, inflationGeneration: generation })
          };
          function inspectRunFrame() {
            if (mode === 'search') {
              runCheck.frames++;
              if (root.children.length !== 1) runCheck.violations.push('overlapping patches');
              if (autoRun && runButton.disabled) runCheck.violations.push('pause disabled');
              for (const material of currentVisual.materials) {
                const expected = (material.userData.baseOpacity ?? .52)
                  * (material.userData.highlightFactor ?? 1);
                if (Math.abs(material.opacity - expected) > 1e-8) {
                  runCheck.violations.push('opacity changed'); break;
                }
              }
            }
            requestAnimationFrame(inspectRunFrame);
          }
          requestAnimationFrame(inspectRunFrame);
        ` });
      });
      await page.goto(base);
      await page.waitForFunction(() => window.runCheck);
      await page.locator('#inflate-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      await page.evaluate(() => runCheck.saveInflation());
      await page.locator('#apply-one-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).count, 9);
      assert.equal(await page.evaluate(() => runCheck.retainedInflation()), true);
      assert.equal(await page.evaluate(() => runCheck.sameTarget()), true);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).count, 8);
      assert.equal(await page.evaluate(() => runCheck.retainedInflation()), true);
      await page.locator('#apply-one-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);

      const pauseAt = async phase => {
        await page.evaluate(() => runCheck.save('pauseStart'));
        await page.locator('#run-button').click();
        const paused = await page.evaluate(phase => new Promise((resolve, reject) => {
          const deadline = performance.now() + 5000;
          function attempt() {
            const state = runCheck.read();
            const ready = phase === 'transition' ? state.transitioning : state.queued;
            if (ready) {
              const button = document.querySelector('#run-button');
              if (button.disabled) return reject(new Error('Pause is disabled'));
              button.click();
              return resolve({ before: state, after: runCheck.read() });
            }
            if (performance.now() > deadline) return reject(new Error('Did not reach ' + phase));
            requestAnimationFrame(attempt);
          }
          attempt();
        }), phase);
        assert.equal(paused.after.running, false);
        assert.equal(paused.after.queued, false);
        await page.waitForTimeout(650);
        assert.equal((await page.evaluate(() => runCheck.read())).count, paused.after.count);
        assert.equal(await page.locator('#run-button span').textContent(), 'Run');
        await page.locator('#back-button').click();
        await page.waitForFunction(() => !runCheck.read().transitioning);
        assert.equal(await page.evaluate(() => runCheck.restored('pauseStart')), true, 'Undo restores the exact pre-Run state');
      };

      if (reducedMotion === 'no-preference') await pauseAt('transition');
      await pauseAt('queued');
      // Immediate start/pause cycles must not leave stale callbacks behind.
      for (let i = 0; i < 3; i++) {
        const stoppedCount = await page.evaluate(() => {
          const button = document.querySelector('#run-button');
          button.click();
          button.click();
          if (runCheck.read().running || runCheck.read().queued) throw new Error('Did not cancel');
          return runCheck.read().count;
        });
        await page.waitForTimeout(400);
        assert.equal((await page.evaluate(() => runCheck.read())).count, stoppedCount);
      }
      await page.evaluate(() => runCheck.save('checkpointStart'));
      await page.locator('#run-button').click();
      await page.waitForFunction(() => {
        const state = runCheck.read();
        return state.complete && !state.running && !state.transitioning;
      }, {}, { timeout: 60000 });
      const checkpoint = await page.evaluate(() => runCheck.read());
      assert.equal(checkpoint.count, 64);
      assert.equal(checkpoint.status, 'consistent finite patch');
      assert.equal(checkpoint.queued, false);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal(await page.evaluate(() => runCheck.restored('checkpointStart')), true);

      // A manual step after a Run remains a separate undoable action.
      await page.evaluate(() => runCheck.save('manualStart'));
      await page.locator('#apply-one-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal(await page.evaluate(() => runCheck.restored('manualStart')), true);

      // Undo must also interrupt a running animation and discard its timer.
      await page.evaluate(() => runCheck.save('activeStart'));
      const activeCount = (await page.evaluate(() => runCheck.read())).count;
      await page.locator('#run-button').click();
      await page.waitForFunction(count => runCheck.read().count >= count + 3, activeCount);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal(await page.evaluate(() => runCheck.restored('activeStart')), true);
      await page.waitForTimeout(400);
      assert.equal((await page.evaluate(() => runCheck.read())).count, activeCount);

      await page.locator('#run-button').click();
      await page.waitForFunction(count => runCheck.read().count >= count + 2, activeCount);
      await page.locator('#inflate-button').click();
      assert.equal((await page.evaluate(() => runCheck.read())).mode, 'inflation');
      assert.equal((await page.evaluate(() => runCheck.read())).inflationGeneration, 1);
      assert.equal(await page.evaluate(() => runCheck.sameInflation()), true);
      assert.equal((await page.evaluate(() => runCheck.read())).running, false);
      assert.equal((await page.evaluate(() => runCheck.read())).queued, false);
      await page.locator('#inflate-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).inflationGeneration, 2);
      await page.evaluate(() => runCheck.saveInflation());
      await page.locator('#apply-one-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).count, 65);
      assert.equal(await page.evaluate(() => runCheck.retainedInflation()), true);
      assert.equal(await page.evaluate(() => runCheck.sameTarget()), true);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).count, 64);
      await page.locator('#inflate-button').click(); // Return to the saved 64-tile stage.
      assert.equal(await page.evaluate(() => runCheck.sameInflation()), true);
      await page.locator('#back-button').click();
      await page.waitForFunction(() => !runCheck.read().transitioning);
      assert.equal((await page.evaluate(() => runCheck.read())).inflationGeneration, 1);
      await page.locator('#chair-mode-select').selectOption('search');
      assert.equal((await page.evaluate(() => runCheck.read())).count, 8);
      assert.equal(await page.locator('#back-button').isDisabled(), true, 'Imported patch is a fresh search root');

      await page.waitForSelector('#lattice-title');
      await page.locator('summary').filter({ hasText: 'The point model and its verification' }).click();
      await page.waitForSelector('#lattice-title ~ details mjx-container');
      const model = await (await page.request.get(base + 'chair/chair44-lattice.json')).json();
      assert.equal(model.t.length, 7);
      assert.equal(model.m.length, 288);
      assert.ok(await page.evaluate(() => runCheck.frames > 10));
      assert.deepEqual(await page.evaluate(() => runCheck.violations), []);
      assert.deepEqual(errors, []);
      console.log('Passed Chair44 Run: steady opacity, enabled Pause, cancellation, resume, 64-tile checkpoint, grouped Undo, growth from 8/64-tile inflation patches, inflation return, scalar model (' + reducedMotion + ').');
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
