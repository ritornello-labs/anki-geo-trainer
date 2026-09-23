import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const engine = readFileSync(new URL('../engine/geo-engine.js', import.meta.url), 'utf8');
const css = readFileSync(new URL('../anki/shared/card.css', import.meta.url), 'utf8');

async function mount(page, bundle, target, mode = 'place', side = 'back') {
  await page.setContent(`<style>${css}</style><div class="gt-app" data-scope="${bundle.scope}" data-target="${target}" data-mode="${mode}" data-side="${side}"></div>`);
  await page.evaluate(b => { window.GT_BUNDLES = {[b.scope]: b}; }, bundle);
  await page.addScriptTag({content:engine});
  await page.waitForSelector('.gt-map');
  await page.waitForTimeout(180); // finish the fill transition before pixel evidence
}

async function topAt(page, point) {
  return page.evaluate(([x, y]) => {
    const svg = document.querySelector('.gt-map'), p = svg.createSVGPoint();
    p.x=x; p.y=y;
    const screen=p.matrixTransform(svg.getScreenCTM());
    return document.elementFromPoint(screen.x,screen.y)?.getAttribute('data-id');
  }, point);
}

for (const [scope, target] of [['russia-subjects','RU-AD'], ['europe-countries','VA'], ['africa-countries','LS']]) {
  const bundle = JSON.parse(readFileSync(new URL(`../data/bundles/${scope}.json`, import.meta.url)));
  for (const mode of ['place','point']) {
    test(`${scope} ${target}: ${mode} answer is visibly above its host`, async ({page}, info) => {
      const region = bundle.regions.find(r=>r.id===target);
      expect(region).toBeTruthy();
      await mount(page,bundle,target,mode);
      // Hit-test the rendered SVG, not just the existence of gt-answer.
      // The Which dot is over the answer, so temporarily hide that overlay.
      await page.locator('.gt-point').evaluateAll(nodes=>nodes.forEach(n=>n.style.pointerEvents='none'));
      expect(await topAt(page,region.c)).toBe(target);
      await expect(page.locator('.gt-answer')).toHaveCSS('fill','rgb(226, 77, 44)');
      if (target==='RU-AD' && mode==='place') await page.screenshot({path:info.outputPath('adygey-answer.png')});
    });
  }
}

const box = (x0,y0,x1,y1) => [[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]];
const holeBundle = {scope:'hole-test',view:{w:100,h:100},frames:[{id:'main',rect:[0,0,100,100],kmPerUnit:1}],regions:[
  {id:'island',name:'Island',frame:'main',s:10,c:[50,50],rings:[box(45,45,55,55)],pts:[[50,50]]},
  {id:'host',name:'Host',frame:'main',s:80,c:[20,20],rings:[box(5,5,95,95),box(35,35,65,65)],pts:[[20,20]]}
]};
test('host hole remains transparent and excluded from location grading',async ({page})=>{
  await mount(page,holeBundle,'host');
  expect(await topAt(page,[50,50])).toBe('island');
  expect(await topAt(page,[40,40])).toBe(null);
  await page.evaluate(()=>{ window['__gt_locate_hole-test_host']={x:50,y:50,hitId:'island'}; });
  await page.evaluate(()=>{document.querySelector('.gt-app').remove();const app=document.createElement('div');app.className='gt-app';app.dataset.scope='hole-test';app.dataset.target='host';app.dataset.mode='locate';app.dataset.side='back';document.body.appendChild(app);window.GeoTrainer.mountAll();});
  await expect(page.locator('.gt-miss')).toBeVisible();
});

test('small answer marker stays visible with legacy hole-less assets',async ({page})=>{
  const bundle=structuredClone(holeBundle);
  bundle.regions[0].small=true;
  // Test the legacy asset too: no interior hole, as in already-installed cards.
  bundle.regions[1].rings=[box(5,5,95,95)];
  await mount(page,bundle,'island');
  expect(await topAt(page,[50,50])).toBe('island');
});
