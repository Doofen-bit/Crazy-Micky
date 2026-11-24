"""Capture high-resolution element screenshots of the running site for the slide deck.
Run `python -m http.server 8000 --bind 127.0.0.1 --directory site` first."""
from pathlib import Path
from playwright.sync_api import sync_playwright
OUT = Path(__file__).resolve().parents[1] / 'docs/figures/slides'
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=2)
    pg.goto('http://127.0.0.1:8000', wait_until='networkidle')
    pg.wait_for_function('window.__explorer?.rows > 0')
    pg.locator('.intro').screenshot(path=str(OUT / 'hero.png'))
    pg.locator('#experiment').screenshot(path=str(OUT / 'experiment.png'))
    pg.locator('.overview-panel').screenshot(path=str(OUT / 'overview.png'))
    pg.locator('.volcano-panel').screenshot(path=str(OUT / 'volcano.png'))
    pg.locator('#glossary').screenshot(path=str(OUT / 'glossary.png'))
    pg.locator('.gloss[data-gloss="padj"]').hover(); pg.wait_for_timeout(200)
    pg.screenshot(path=str(OUT / 'gloss_hover.png'), clip={'x': 0, 'y': 0, 'width': 1440, 'height': 1000})
    pg.locator('[data-tour="gene"]').click(); pg.wait_for_selector('.sample-point'); pg.wait_for_timeout(300)
    pg.locator('.expression-panel').screenshot(path=str(OUT / 'expression.png'))
    pg.locator('[data-tour="process"]').click(); pg.wait_for_function('window.__explorer.state.term !== null'); pg.wait_for_timeout(300)
    pg.locator('.network-panel').screenshot(path=str(OUT / 'network.png'))
    pg.locator('.volcano-panel').screenshot(path=str(OUT / 'volcano_linked.png'))
    pg.locator('.grid').screenshot(path=str(OUT / 'dashboard_linked.png'))
    g = pg.locator('.grid').bounding_box()
    fr = [[(pg.locator(f'.{v}-panel').bounding_box()['x'] - g['x']) / g['width'], (pg.locator(f'.{v}-panel').bounding_box()['y'] - g['y']) / g['height']] for v in ['overview', 'volcano', 'expression', 'network']]
    (OUT / 'panel_boxes.json').write_text(__import__('json').dumps(fr))
    pg.locator('#brain3d').scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    pg.locator('.brain-wrap').screenshot(path=str(OUT / 'brain.png'))
    pg.locator('#takeaway').screenshot(path=str(OUT / 'takeaway.png'))
    pg.locator('.exp-steps li').nth(0).screenshot(path=str(OUT / 'primer_stress.png'))
    for k in range(4): pg.locator('.exp-steps svg.scene').nth(k).screenshot(path=str(OUT / f'scene{k + 1}.png'))
    pg.locator('.exp-steps li').nth(1).screenshot(path=str(OUT / 'primer_sort.png'))
    pg.locator('#story').screenshot(path=str(OUT / 'story.png'))
    b.close()
print('saved to', OUT)
