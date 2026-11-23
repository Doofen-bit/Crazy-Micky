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
    pg.locator('#story').screenshot(path=str(OUT / 'story.png'))
    b.close()
print('saved to', OUT)
