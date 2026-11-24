from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    responses=[];page.on('response',lambda r:responses.append((r.url,r.status)))
    page.goto('http://127.0.0.1:8000',wait_until='networkidle')
    page.wait_for_function('window.__explorer?.rows > 0')
    assert page.locator('.overview-cell').count()==8
    assert page.locator('.panel').count()==4
    baseline=page.evaluate('window.__explorer')
    assert baseline['context']['id']=='SCN_zt16_resilient_vs_control'
    page.screenshot(path=str(ROOT/'docs/dashboard-overview.png'),full_page=True)
    # Plain-language layer: glossary entries, hover definitions, guided story and example-gene shortcut.
    assert page.locator('#glossary-list > div').count()>=12
    page.locator('.gloss').first.hover();assert not page.locator('#tooltip').is_hidden()
    assert page.locator('#expression .empty .example').count()==1
    page.locator('.guide [data-tour="context"]').click();page.wait_for_function("document.querySelector('#story').textContent.includes('Step 1')")
    page.locator('[data-tour="gene"]').click();page.wait_for_function('window.__explorer.state.gene !== null')
    assert 'Step 2' in page.locator('#story').inner_text()
    page.locator('[data-tour="process"]').click();page.wait_for_function('window.__explorer.state.term !== null')
    assert 'Step 3' in page.locator('#story').inner_text()
    page.locator('#reset').click();page.wait_for_function('window.__explorer.state.gene === null && window.__explorer.state.term === null')
    assert page.locator('#story').is_hidden()
    # Instructor-feedback features: 3D brain locator, sideways volcano, linear zoomed profile, edge strength, takeaway.
    assert page.locator('#brain3d').count()==1
    page.locator('.brain-key[data-region="Hb"]').click();page.wait_for_function('window.__explorer.context.id === "Hb_zt16_resilient_vs_control"')
    page.locator('.brain-key[data-region="SCN"]').click();page.wait_for_function('window.__explorer.context.id === "SCN_zt16_resilient_vs_control"')
    assert 'UP-REGULATED' in page.locator('#volcano-axis').inner_html()
    page.locator('#candidates button').first.click();page.wait_for_selector('.sample-point')
    assert page.locator('.axis-break').count()==1, 'Kcnk2 profile should use a zoomed linear axis'
    widths={page.evaluate('el=>el.getAttribute("stroke-width")',e) for e in page.locator('.edge').element_handles()}
    assert len(widths)>=2, widths
    assert page.locator('#fact-night').inner_text().endswith('%') and page.locator('#fact-ratio').inner_text().endswith('×')
    page.locator('#reset').click();page.wait_for_function('window.__explorer.state.gene === null')
    page.locator('#candidates button').first.click()
    page.wait_for_function('window.__explorer.state.gene !== null')
    page.wait_for_selector('.sample-point')
    chosen=page.evaluate('window.__explorer.state.gene')
    assert page.locator('.sample-point').count()==47
    page.locator('#term-buttons button').first.click()
    page.wait_for_function('window.__explorer.state.term !== null')
    page.screenshot(path=str(ROOT/'docs/dashboard-linked.png'),full_page=True)
    for panel in ['overview','volcano','expression','network']:
        page.locator(f'.{panel}-panel').screenshot(path=str(ROOT/f'docs/view-{panel}.png'))
    page.locator('#clear-term').click();page.wait_for_function('window.__explorer.state.term === null')
    page.locator('.network-gene').nth(1).click();page.wait_for_function(f'window.__explorer.state.gene !== {chosen}')
    chosen=page.evaluate('window.__explorer.state.gene')
    page.locator('[data-context="Hb_zt10_resilient_vs_control"]').click()
    page.wait_for_function('window.__explorer.context.id === "Hb_zt10_resilient_vs_control"')
    assert page.evaluate('window.__explorer.state.gene')==chosen
    assert page.locator('.sample-point').count()==46
    page.locator('#contrast').select_option('susceptible_vs_control')
    page.wait_for_function('window.__explorer.context.id === "Hb_zt10_susceptible_vs_control"')
    page.locator('#alpha').select_option('.01');page.locator('#lfc').select_option('2')
    page.wait_for_function('window.__explorer.state.alpha === .01 && window.__explorer.state.lfc === 2')
    # Every context/contrast is loaded at least once, ensuring correct asset paths.
    for contrast in ['resilient_vs_control','susceptible_vs_control','resilient_vs_susceptible']:
        page.locator('#contrast').select_option(contrast)
        for region in ['SCN','Hb']:
            for zt in [4,10,16,22]:
                context=f'{region}_zt{zt}_{contrast}'
                page.locator(f'[data-context="{context}"]').click()
                page.wait_for_function(f'window.__explorer.context.id === "{context}"')
    page.locator('#reset').click();page.wait_for_function('window.__explorer.state.gene === null && window.__explorer.context.id === "SCN_zt16_resilient_vs_control"')
    assert page.locator('#expression .empty').count()==1
    page.locator('[data-context="SCN_zt10_resilient_vs_control"]').click()
    page.wait_for_function('window.__explorer.context.id === "SCN_zt10_resilient_vs_control"')
    assert '0 genes clearly changed' in page.locator('#volcano-sub').inner_text()
    assert 'Annotation only' in page.locator('#network-sub').inner_text()
    assert 'No genes pass' in page.locator('#network-note').inner_text()
    page.locator('#reset').click();page.wait_for_function('window.__explorer.context.id === "SCN_zt16_resilient_vs_control"')
    # The all-zero raw gene remains searchable and displays zero expression, without invented p-values.
    import pandas as pd
    raw=pd.read_csv(ROOT/'analysis/input/counts.csv',index_col=0)
    zero=raw.index[(raw.sum(axis=1)==0)][0]
    page.locator('#gene-search').fill(zero);page.locator('#gene-search').press('Enter')
    page.wait_for_function('window.__explorer.state.gene !== null')
    page.wait_for_selector('.sample-point')
    assert 'filtered out' in page.locator('#expression-sub').inner_text()
    assert 'no plottable' in page.locator('#volcano-note').inner_text()
    # Explicit search miss; keyboard activation of a context; CSV export.
    page.locator('#gene-search').fill('NOT_A_REAL_GENE_123');assert 'No matching' in page.locator('#suggestions').inner_text()
    page.locator('#reset').click();page.wait_for_function('window.__explorer.state.gene === null')
    page.locator('[data-context="Hb_zt4_resilient_vs_control"]').focus();page.keyboard.press('Enter')
    page.wait_for_function('window.__explorer.context.id === "Hb_zt4_resilient_vs_control"')
    with page.expect_download() as info: page.locator('#download').click()
    download=info.value;assert download.suggested_filename.startswith('Hb_zt4')
    page.locator('#reset').click();page.wait_for_function('window.__explorer.context.id === "SCN_zt16_resilient_vs_control"')
    # Laptop and mobile layouts must fit horizontally.
    for width,height in [(1366,900),(390,844)]:
        page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(400)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.screenshot(path=str(ROOT/f'docs/dashboard-{width}.png'),full_page=True)
    page.goto('http://127.0.0.1:8000/methods.html');assert page.locator('h1').inner_text()=='What the views mean.'
    assert not errors,errors
    bad=[x for x in responses if x[1]>=400];assert not bad,bad
    # Explicit no-GO fixture is restricted to this test browser; exported science is untouched.
    fixture=browser.new_page()
    fixture.route('**/data/networks/*.json',lambda route:route.fulfill(json={'mode':'annotation','terms':[],'total_enriched':0,'tested_terms':0}))
    fixture.goto('http://127.0.0.1:8000');fixture.wait_for_function('window.__explorer?.rows > 0')
    assert 'No eligible GO' in fixture.locator('#network').inner_text()
    fixture.close()
    result={'passed':True,'browser':'Chromium via Playwright','contexts_loaded':24,'linked_transitions':['context->volcano/network/profile','gene->profile/network','network gene->profile','process->volcano','clear process','contrast->views','reset'],'plain_language':['glossary hover','three-step guided story','example-gene shortcut','3D brain locator click','sideways volcano','zoomed linear profile','edge evidence widths','takeaway facts'],'edge_states':['no selection','filtered all-zero gene','search miss','NA statistics','real zero-DEG context','annotation-only network','no-GO mocked response (test only)'],'responsive_widths':[1440,1366,390],'console_errors':errors,'http_errors':bad}
    (ROOT/'audit/browser_validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));browser.close()
