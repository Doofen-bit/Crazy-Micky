'use strict';
/* Stress Atlas: D3 v7 coordinates four linked views from one shared state object.
   All statistics (DESeq2, GO enrichment) are computed offline; the browser only filters and draws. */
const $ = s => document.querySelector(s);
const DEFAULT = {region: 'SCN', zt: 16, contrast: 'resilient_vs_control', alpha: .05, lfc: .5, gene: null, term: null};
let state = {...DEFAULT}, genes = [], samples = [], overview = [], manifest = {}, rows = [], network = null, version = 0;
const cache = new Map(), colors = {control: '#596b85', resilient: '#007f79', susceptible: '#8e5bb0'};
const UP = '#d62f2f', DOWN = '#2b6cb0', REGION_COLOR = {SCN: '#e69f00', Hb: '#2fa36b'};
const names = {control: 'Control', resilient: 'Resilient', susceptible: 'Susceptible'};
const groupWord = {control: 'control (never-stressed)', resilient: 'resilient', susceptible: 'susceptible'};
const regionFull = {SCN: 'SCN (master clock)', Hb: 'Hb (habenula)'};
const regionSub = {SCN: 'master clock', Hb: 'habenula'};
const ztWord = {4: 'lights on, mice resting', 10: 'lights on, mice resting', 16: 'lights off, mice active', 22: 'lights off, mice active'};
const phases = [4, 10, 16, 22], regions = ['SCN', 'Hb'], night = new Set([16, 22]);
let rowById = new Map(), plotted = [], nearest = null, loadedId = null, topGene = null;

/* Plain-language glossary: one source for the hover definitions and the glossary section. */
const GLOSSARY = {
  gene: ['Gene', 'A stretch of DNA that holds the instructions for one molecule, usually a protein. Every cell carries the same genes but switches them on and off differently.'],
  expression: ['Gene activity (expression)', 'How much a gene is being used right now, measured by how many RNA copies of it are in the tissue.'],
  rnaseq: ['RNA-seq', 'RNA sequencing reads millions of short RNA fragments from a tissue sample and counts how many came from each gene. More reads means a more active gene.'],
  normcount: ['Normalized count', 'Read counts adjusted so samples with more or fewer total reads can be compared fairly (DESeq2 median-of-ratios). View 3 plots these counts on a plain (linear) axis zoomed to the data.'],
  csds: ['Chronic social defeat stress', 'A standard lab model of social stress. Each day a test mouse briefly meets a larger, aggressive mouse, then lives next to it behind a see-through divider.'],
  groups: ['Control / resilient / susceptible', 'Control mice were never stressed. After stress, a social test sorts mice: resilient mice still approach a new mouse; susceptible mice avoid it (a depression-like behaviour).'],
  scn: ['SCN (suprachiasmatic nucleus)', 'A tiny brain region that acts as the body’s master clock, keeping daily rhythms in step with light and dark.'],
  hb: ['Hb (habenula)', 'A small brain region that responds to disappointment and bad experiences; its over-activity is linked to depression. Source files call it LHb (lateral habenula).'],
  zt: ['ZT (zeitgeber time)', 'Hours after the lights turn on. ZT0 = lights on, ZT12 = lights off. Mice are night-active, so ZT4 and ZT10 are rest time and ZT16 and ZT22 are active time.'],
  lfc: ['Log₂ fold change', 'How much more (positive) or less (negative) active a gene is in the first group. +1 = twice as active, −1 = half as active, 0 = no change.'],
  padj: ['Adjusted p-value', 'How surprising the difference would be if there were really no difference, corrected because ~16,000 genes are tested at once. Smaller = more confident; .05 is the usual cutoff.'],
  deg: ['Changed gene (DEG)', 'A “differentially expressed gene” passes both cutoffs: confident enough (adjusted p) and big enough (fold change). View 1 counts these.'],
  volcano: ['Volcano plot', 'A scatter plot of every gene. Ours is turned on its side for easier reading: up-regulated genes at the top, down-regulated at the bottom, more confident further right.'],
  updown: ['Up- / down-regulated', 'Up-regulated (red): the gene is more active in the first group named. Down-regulated (blue): less active.'],
  evidence: ['Line thickness in View 4', 'Thick: a mouse experiment directly showed the gene takes part in the process. Medium: directly linked but inferred (e.g. from the same gene in rats or humans). Thin: indirect, the gene is annotated to a more specific sub-process.'],
  go: ['Gene Ontology (GO) process', 'A public database that labels genes with the biological processes they take part in, such as “regulation of membrane potential”.'],
  enrichment: ['Enriched process', 'A process is enriched when more of its genes are among the changed genes than random chance would predict (hypergeometric test, corrected for testing many processes).']
};

const cid = () => `${state.region}_zt${state.zt}_${state.contrast}`;
const label = i => genes[i]?.[1] || genes[i]?.[0] || 'Unknown gene';
const pair = () => state.contrast.split('_vs_');
const significant = r => r.padj !== null && r.padj < state.alpha && Math.abs(r.lfc) > state.lfc;
const pointColor = r => significant(r) ? r.lfc > 0 ? UP : DOWN : '#afbdc9';
const fmt = v => v === null || v === undefined ? 'NA' : Math.abs(v) > 0 && Math.abs(v) < .001 ? d3.format('.2e')(v) : d3.format(',.3~f')(v);
const fold = lfc => `${d3.format('.1f')(2 ** Math.abs(lfc))}× ${lfc > 0 ? 'more' : 'less'} active`;

function place(text, x, y) {
  const t = $('#tooltip'); t.textContent = text; t.hidden = false;
  const w = t.offsetWidth, h = t.offsetHeight;
  t.style.left = `${Math.max(5, Math.min(x + 15, innerWidth - w - 10))}px`;
  t.style.top = `${Math.max(5, Math.min(y + 15, innerHeight - h - 10))}px`;
}
const tip = (event, text) => place(text, event.clientX, event.clientY);
function hideTip() { $('#tooltip').hidden = true; }
async function load(url) {
  if (!cache.has(url)) cache.set(url, fetch(url).then(r => { if (!r.ok) throw Error(`${url}: ${r.status}`); return r.json(); }).catch(e => { cache.delete(url); throw e; }));
  return cache.get(url);
}
function status(text) { $('#status').textContent = text; }
function story(text) { const el = $('#story'); el.textContent = text || ''; el.hidden = !text; }
function empty(selector, text, action) {
  const el = $(selector); el.replaceChildren();
  const d = document.createElement('div'); d.className = 'empty';
  const p = document.createElement('p'); p.textContent = text; d.append(p);
  if (action) { const b = document.createElement('button'); b.className = 'example'; b.textContent = action.text; b.onclick = action.run; d.append(b); }
  el.append(d);
}
function activate(sel, fn) {
  sel.attr('tabindex', 0).attr('role', 'button').on('click', fn)
    .on('keydown', (e, d) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(e, d); } });
}
function svgFrame(selector, height) {
  const node = $(selector); node.replaceChildren();
  const w = Math.max(280, node.clientWidth);
  return {svg: d3.select(node).append('svg').attr('viewBox', `0 0 ${w} ${height}`).attr('width', '100%').attr('height', height), w, h: height};
}
function wrap(text, chars, maxLines = 2) {
  const words = text.split(' '), lines = [''];
  for (const word of words) {
    const cur = lines[lines.length - 1];
    if ((cur + ' ' + word).trim().length <= chars) lines[lines.length - 1] = (cur + ' ' + word).trim();
    else lines.push(word);
  }
  if (lines.length > maxLines) { lines.length = maxLines; lines[maxLines - 1] = lines[maxLines - 1].slice(0, chars - 1) + '…'; }
  return lines;
}

/* VIEW 1: region × time grid of changed-gene counts (heatmap with printed numbers). */
function overviewDraw() {
  const {svg, w} = svgFrame('#overview', 262), left = 96, right = 8, top = 46, h = 70;
  const data = overview.filter(d => d.contrast === state.contrast);
  const key = `${state.alpha}:${state.lfc}`;
  const count = d => { const t = d.thresholds[key]; return t.up + t.down; };
  const max = d3.max(data, count) || 1, scale = d3.scaleSequential(d3.interpolateGnBu).domain([0, max]);
  const x = d3.scaleBand().domain(phases).range([left, w - right]).paddingInner(.07);
  const y = d3.scaleBand().domain(regions).range([top, top + h * 2 + 16]).paddingInner(.13);
  const gap = x.step() - x.bandwidth();
  // Night band: encodes lights-off with a background, not colour of the data marks.
  svg.append('rect').attr('x', x(16) - gap / 2).attr('y', 0).attr('width', w - right - x(16) + gap / 2).attr('height', top + h * 2 + 22).attr('rx', 6).attr('fill', '#e4eaf1');
  const head = svg.selectAll('.zt').data(phases).join('g').attr('transform', d => `translate(${x(d) + x.bandwidth() / 2},0)`);
  head.append('text').attr('y', 18).attr('text-anchor', 'middle').style('font-weight', 700).style('fill', '#142c40').text(d => `ZT${d}`);
  head.append('text').attr('y', 34).attr('text-anchor', 'middle').style('font-size', '11px').text(d => night.has(d) ? '☾ night' : '☀ day');
  const rl = svg.selectAll('.region').data(regions).join('g').attr('transform', d => `translate(0,${y(d) + y.bandwidth() / 2})`);
  rl.append('circle').attr('cx', 5).attr('cy', -6).attr('r', 5).attr('fill', d => REGION_COLOR[d]);
  rl.append('text').attr('x', 14).attr('y', -2).style('font-weight', 700).style('fill', '#142c40').text(d => d);
  rl.append('text').attr('x', 14).attr('y', 14).style('font-size', '11px').text(d => regionSub[d]);
  const cell = svg.selectAll('.overview-cell').data(data).join('g').attr('class', 'overview-cell').attr('data-context', d => d.id)
    .attr('aria-label', d => `${regionFull[d.region]}, ZT${d.zt}: ${count(d)} changed genes; ${d.n_group1} versus ${d.n_group2} mice`)
    .attr('transform', d => `translate(${x(d.zt)},${y(d.region)})`);
  cell.append('rect').attr('width', x.bandwidth()).attr('height', y.bandwidth()).attr('rx', 4)
    .attr('fill', d => count(d) ? scale(count(d)) : '#f7f9fb')
    .attr('stroke', d => d.region === state.region && d.zt === state.zt ? '#142c40' : '#d5dee6')
    .attr('stroke-width', d => d.region === state.region && d.zt === state.zt ? 3 : 1);
  cell.append('text').attr('x', x.bandwidth() / 2).attr('y', 30).attr('text-anchor', 'middle').style('fill', d => count(d) > max * .6 ? 'white' : '#142c40').style('font-size', '24px').style('font-weight', 650).text(d => d3.format(',')(count(d)));
  cell.append('text').attr('x', x.bandwidth() / 2).attr('y', 51).attr('text-anchor', 'middle').style('fill', d => count(d) > max * .6 ? 'white' : '#536b7c').style('font-size', '11px').text(d => x.bandwidth() < 80 ? `n ${d.n_group1}/${d.n_group2}` : `${d.n_group1} vs ${d.n_group2} mice`);
  activate(cell, (_, d) => change({region: d.region, zt: d.zt, term: null}));
  const [a, b] = pair();
  cell.on('mousemove', (e, d) => tip(e, `${regionFull[d.region]} · ZT${d.zt} (${ztWord[d.zt]})\n${count(d)} changed genes: ${d.thresholds[key].up} more active and ${d.thresholds[key].down} less active in ${groupWord[a]} mice\n${d.n_group1} ${names[a].toLowerCase()} vs ${d.n_group2} ${names[b].toLowerCase()} mice\n${d3.format(',')(d.tested_genes)} genes had enough data to test\nClick to inspect this comparison`)).on('mouseleave', () => { hideTip(); brain.highlight(null); });
  cell.on('mouseenter', (_, d) => brain.highlight(d.region));
  svg.append('text').attr('x', left).attr('y', 250).text(w < 500 ? 'LIGHTS ON' : 'LIGHTS ON · MICE REST').style('font-size', '11px').style('letter-spacing', '.5px');
  svg.append('text').attr('x', x(16)).attr('y', 250).text(w < 500 ? 'LIGHTS OFF' : 'LIGHTS OFF · MICE ACTIVE').style('font-size', '11px').style('letter-spacing', '.5px');
  const lg = $('#overview-legend'); lg.className = 'note scale-legend'; lg.replaceChildren();
  const bar = document.createElement('span'); bar.className = 'ramp'; bar.style.background = `linear-gradient(90deg,${d3.range(0, 1.01, .25).map(t => scale(t * max)).join(',')})`;
  lg.append('0 ', bar, ` ${d3.format(',')(max)} changed genes. Darker = more. The scale is shared by all eight boxes.`);
}

/* VIEW 2: volcano plot turned sideways for lay readers: up-regulated genes at the top, confidence to the right
   (Canvas for ~16k points + SVG axes). */
function volcanoDraw() {
  const wrapEl = $('.volcano-wrap'), w = wrapEl.clientWidth, h = wrapEl.clientHeight, m = {l: 58, r: 15, t: 26, b: 42};
  const canvas = $('#volcano-canvas'), ctx = canvas.getContext('2d'), ratio = devicePixelRatio || 1;
  canvas.width = w * ratio; canvas.height = h * ratio; ctx.scale(ratio, ratio); ctx.clearRect(0, 0, w, h);
  const [a] = pair(), A = groupWord[a];
  const conf = r => Math.min(300, -Math.log10(Math.max(Number.MIN_VALUE, r.padj)));
  const valid = rows.filter(r => r.padj !== null && Number.isFinite(r.lfc));
  const ymax = Math.max(2, d3.max(valid, d => Math.abs(d.lfc)) || 2) * 1.08;
  const xmax = Math.max(3, d3.max(valid, conf) || 3) * 1.05;
  const x = d3.scaleLinear().domain([0, xmax]).range([m.l, w - m.r]);
  const y = d3.scaleLinear().domain([-ymax, ymax]).range([h - m.b, m.t]);
  const svg = d3.select('#volcano-axis').attr('viewBox', `0 0 ${w} ${h}`); svg.selectAll('*').remove();
  svg.append('g').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(6));
  svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(7).tickSize(-(w - m.l - m.r))).call(g => g.select('.domain').remove());
  svg.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(0)).attr('y2', y(0)).attr('stroke', '#8aa0b2');
  svg.append('text').attr('x', (w + m.l - m.r) / 2).attr('y', h - 4).attr('text-anchor', 'middle').attr('class', 'axis-label').text(w < 500 ? 'more confident → (−log₁₀ adj. p)' : 'more confident →  (−log₁₀ adjusted p-value)');
  svg.append('text').attr('transform', `translate(13,${(h - m.b + m.t) / 2}) rotate(-90)`).attr('text-anchor', 'middle').attr('class', 'axis-label').text('change · log₂ fold change');
  svg.append('text').attr('x', m.l + 4).attr('y', 15).attr('class', 'side-label').style('fill', UP).text(w < 500 ? '▲ UP-REGULATED' : `▲ UP-REGULATED · more active in ${A} mice`);
  svg.append('text').attr('x', m.l + 6).attr('y', h - m.b - 8).attr('class', 'side-label halo').style('fill', DOWN).text(w < 500 ? '▼ DOWN-REGULATED' : `▼ DOWN-REGULATED · less active in ${A} mice`);
  // Tinted zones where genes pass both cutoffs; dashed lines mark the cutoffs.
  const xa = x(-Math.log10(state.alpha));
  ctx.fillStyle = 'rgba(214,47,47,.06)'; ctx.fillRect(xa, m.t, w - m.r - xa, y(state.lfc) - m.t);
  ctx.fillStyle = 'rgba(43,108,176,.06)'; ctx.fillRect(xa, y(-state.lfc), w - m.r - xa, h - m.b - y(-state.lfc));
  ctx.strokeStyle = '#738897'; ctx.setLineDash([4, 4]); ctx.lineWidth = .8;
  for (const v of [-state.lfc, state.lfc]) { ctx.beginPath(); ctx.moveTo(m.l, y(v)); ctx.lineTo(w - m.r, y(v)); ctx.stroke(); }
  ctx.beginPath(); ctx.moveTo(xa, m.t); ctx.lineTo(xa, h - m.b); ctx.stroke(); ctx.setLineDash([]);
  const term = network?.terms.find(t => t.id === state.term), memberSet = new Set(term?.members || []);
  plotted = valid.map(r => ({...r, x: x(conf(r)), y: y(r.lfc)}));
  plotted.sort((p, q) => Number(significant(p)) - Number(significant(q)));
  for (const r of plotted) {
    ctx.globalAlpha = state.term && !memberSet.has(r.i) ? .1 : significant(r) ? .85 : .28;
    ctx.fillStyle = pointColor(r); ctx.beginPath(); ctx.arc(r.x, r.y, significant(r) ? 2.5 : 1.4, 0, Math.PI * 2); ctx.fill();
    if (state.term && memberSet.has(r.i)) { ctx.strokeStyle = '#123d48'; ctx.lineWidth = .7; ctx.stroke(); }
  }
  ctx.globalAlpha = 1; const selected = plotted.find(r => r.i === state.gene);
  if (selected) {
    ctx.beginPath(); ctx.arc(selected.x, selected.y, 6, 0, Math.PI * 2); ctx.strokeStyle = '#142c40'; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.font = 'bold 13px Segoe UI'; ctx.fillStyle = '#142c40'; const tw = ctx.measureText(label(selected.i)).width;
    ctx.fillText(label(selected.i), Math.min(w - tw - 4, selected.x + 9), Math.max(m.t + 12, selected.y - 9));
  }
  const delaunay = d3.Delaunay.from(plotted, d => d.x, d => d.y);
  canvas.onmousemove = e => {
    const rect = canvas.getBoundingClientRect(); const px = e.clientX - rect.left, pyy = e.clientY - rect.top;
    const r = plotted[delaunay.find(px, pyy)]; nearest = r && Math.hypot(r.x - px, r.y - pyy) < 14 ? r : null;
    canvas.style.cursor = nearest ? 'pointer' : 'default';
    if (nearest) tip(e, `${label(r.i)} · ${genes[r.i][0]}\n${fold(r.lfc)} in ${A} mice (${r.lfc > 0 ? 'up' : 'down'}-regulated)\nlog₂ fold change ${fmt(r.lfc)} · adjusted p ${fmt(r.padj)}\n${significant(r) ? 'Passes both cutoffs (changed gene)' : 'Does not pass both cutoffs'}\nClick to follow it through the day`);
    else hideTip();
  };
  canvas.onmouseleave = () => { nearest = null; hideTip(); };
  canvas.onclick = () => { if (nearest) change({gene: nearest.i}); };
  const pass = rows.filter(significant), nUp = pass.filter(r => r.lfc > 0).length;
  $('#volcano-sub').textContent = `${d3.format(',')(pass.length)} genes clearly changed out of ${d3.format(',')(valid.length)} tested: ${d3.format(',')(nUp)} up (red, top) and ${d3.format(',')(pass.length - nUp)} down (blue, bottom). Each dot is one gene; further right = more confident.`;
  $('#leg-up').textContent = `Up-regulated: more active in ${A}`; $('#leg-down').textContent = `Down-regulated: less active in ${A}`;
  const nNA = rows.length - valid.length;
  $('#volcano-note').textContent = `${d3.format(',')(nNA)} genes had too little data for a reliable test and are not plotted (still searchable). ${state.term ? `Outlined: genes in “${term?.name || state.term}”. ` : ''}${state.gene !== null && !selected ? 'The selected gene has no plottable adjusted p-value in this comparison. ' : ''}Dashed lines mark the two cutoffs; tinted corners hold the changed genes.`;
  const best = [...valid].sort((p, q) => p.padj - q.padj || Math.abs(q.lfc) - Math.abs(p.lfc)).slice(0, 6);
  topGene = best[0]?.i ?? null;
  d3.select('#candidates').selectAll('button').data(best, d => d.i).join('button').classed('active', d => d.i === state.gene)
    .style('border-left', d => `4px solid ${pointColor(d)}`)
    .text(d => `${label(d.i)} ${d.lfc > 0 ? '▲' : '▼'}`).attr('aria-label', d => `Inspect ${label(d.i)}`).on('click', (_, d) => change({gene: d.i}));
}

/* VIEW 3: one gene across four times; every mouse as a point, group means as lines.
   Linear normalized counts on a y-axis zoomed to the data range (break mark when it does not start at 0). */
async function expressionDraw(token) {
  const selected = state.gene, region = state.region, zt = state.zt;
  if (selected === null) {
    $('#expression-title').textContent = 'One gene, through the day';
    $('#expression-sub').textContent = 'Pick a gene in View 2, View 4 or the search box to see every individual mouse.';
    empty('#expression', 'One gene · four times of day · every mouse.', topGene === null ? null : {text: `Show an example: ${label(topGene)}`, run: () => change({gene: topGene})});
    return;
  }
  const [a, b] = pair();
  $('#expression-title').textContent = `${label(selected)}, through the day`;
  const r = rowById.get(selected);
  $('#expression-sub').textContent = `${regionFull[region]} · ${r ? `at ZT${zt}: ${r.padj === null ? 'not testable' : fold(r.lfc)} in ${groupWord[a]} vs ${groupWord[b]} mice (log₂ fold change ${fmt(r.lfc)}, adjusted p ${fmt(r.padj)})` : 'filtered out of this comparison (too few reads to test); its activity is still shown'}`;
  const chunk = await load(`data/expression/${genes[selected][2]}.json`); if (token !== version) return;
  const values = chunk[String(selected)]; if (!values) { empty('#expression', 'Expression unavailable for this gene.'); return; }
  const data = samples.map((s, i) => ({...s, count: values[i], value: values[i]})).filter(s => s.region === region);
  const means = Object.fromEntries(Object.keys(colors).map(ph => [ph, phases.map(t => { const g = data.filter(d => d.zt === t && d.phenotype === ph); return {zt: t, value: g.length ? d3.mean(g, d => d.count) : null, n: g.length}; })]));
  const all = [...data.map(d => d.value), ...Object.values(means).flat().map(d => d.value).filter(v => v !== null)];
  const lo = d3.min(all), hi = d3.max(all), pad = (hi - lo) * .12 || Math.max(1, hi * .1);
  const y0 = lo - pad <= .1 * (hi + pad) ? 0 : lo - pad;  // zoom unless the data already reach near zero
  const {svg, w, h} = svgFrame('#expression', 300), m = {l: 62, r: 15, t: 22, b: 40};
  const x = d3.scalePoint().domain(phases).range([m.l + 25, w - m.r - 25]);
  const y = d3.scaleLinear().domain([y0, hi + pad]).nice().range([h - m.b, m.t]);
  const broken = y.domain()[0] > 0;
  const step = x.step(), band = Math.min(step * .8, 70);
  svg.append('rect').attr('x', x(16) - step / 2).attr('y', m.t - 18).attr('width', w - m.r - x(16) + step / 2).attr('height', h - m.b - m.t + 18).attr('fill', '#e4eaf1');
  svg.append('text').attr('x', w - m.r - 6).attr('y', m.t - 6).attr('text-anchor', 'end').style('font-size', '11px').text('☾ lights off');
  svg.append('text').attr('x', m.l + 6).attr('y', m.t - 6).style('font-size', '11px').text('☀ lights on');
  svg.append('rect').attr('x', x(zt) - band / 2).attr('y', m.t).attr('width', band).attr('height', h - m.b - m.t).attr('fill', 'none').attr('stroke', '#007f79').attr('stroke-dasharray', '4 3').attr('rx', 4);
  svg.append('g').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).tickFormat(t => `ZT${t}${t === zt && w >= 500 ? ' (selected)' : ''}`));
  svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d3.format(',~r')).tickSize(-(w - m.l - m.r))).call(g => g.select('.domain').remove());
  if (broken) {
    // Axis-break mark: the scale is zoomed and does not start at zero.
    svg.append('rect').attr('x', m.l).attr('y', h - m.b - 13).attr('width', 15).attr('height', 12).attr('fill', 'white');
    svg.append('path').attr('class', 'axis-break').attr('d', `M${m.l + 1},${h - m.b - 3}l12,-7M${m.l + 1},${h - m.b + 2}l12,-7`).attr('stroke', '#142c40').attr('stroke-width', 1.6);
  }
  svg.append('text').attr('transform', `translate(13,${(h - m.b) / 2}) rotate(-90)`).attr('text-anchor', 'middle').attr('class', 'axis-label').text(broken ? 'gene activity · normalized count (zoomed)' : 'gene activity · normalized count');
  const shapes = {control: d3.symbolCircle, resilient: d3.symbolTriangle, susceptible: d3.symbolSquare};
  const offsets = {control: -12, resilient: 0, susceptible: 12};
  for (const [ph, co] of Object.entries(colors)) {
    const ms = means[ph].filter(d => d.value !== null);
    svg.append('path').datum(ms).attr('d', d3.line().x(d => x(d.zt) + offsets[ph]).y(d => y(d.value))).attr('fill', 'none').attr('stroke', co).attr('stroke-width', 2).attr('stroke-dasharray', ph === 'resilient' ? '6 3' : ph === 'susceptible' ? '2 3' : null);
    svg.selectAll(`.mean-${ph}`).data(ms).join('line').attr('x1', d => x(d.zt) + offsets[ph] - 7).attr('x2', d => x(d.zt) + offsets[ph] + 7).attr('y1', d => y(d.value)).attr('y2', d => y(d.value)).attr('stroke', co).attr('stroke-width', 3);
  }
  const jitter = s => { let v = 0; for (const c of s.sample_id_analysis) v = (v * 31 + c.charCodeAt(0)) >>> 0; return (v % 100) / 100 * 9 - 4.5; };
  const pts = svg.selectAll('.sample-point').data(data).join('path').attr('class', 'sample-point').attr('d', d => d3.symbol().type(shapes[d.phenotype]).size(40)())
    .attr('transform', d => `translate(${x(d.zt) + offsets[d.phenotype] + jitter(d)},${y(d.value)})`).attr('fill', d => colors[d.phenotype]).attr('fill-opacity', .78).attr('stroke', 'white').attr('stroke-width', .7);
  pts.on('mousemove', (e, d) => tip(e, `One ${names[d.phenotype].toLowerCase()} mouse (${d.animal_id})\nZT${d.zt} · ${ztWord[d.zt]}\nNormalized count ${fmt(d.count)}\nSample ${d.sample_id_analysis} (source file ${d.sample_id_source})`)).on('mouseleave', hideTip);
  svg.append('text').attr('x', w - m.r).attr('y', h - 6).attr('text-anchor', 'end').style('font-size', '11px').text(broken ? `axis starts at ${d3.format(',~r')(y.domain()[0])}, not 0` : 'lines: group averages');
}

/* VIEW 4: bipartite gene–process node-link diagram (deterministic two-column layout).
   Edge colour = gene direction (red up / blue down); edge width = how directly the GO annotation links them. */
const STRENGTH = {3: ['shown directly in mouse experiments', 3.2], 2: ['directly linked, inferred evidence', 1.8], 1: ['indirect, via a more specific sub-process', .7]};
function networkDraw() {
  if (!network) { empty('#network', 'GO data unavailable.'); return; }
  const terms = network.terms;
  $('#network-sub').textContent = network.mode === 'enrichment'
    ? 'Left: changed genes (red = up, blue = down). Right: biological processes that contain more changed genes than chance predicts (computed at the standard cutoffs). Click a process to light up its genes in View 2.'
    : 'Annotation only: no process was over-represented among changed genes at the standard cutoffs, so these are reference memberships of top-ranked genes.';
  if (!terms.length) { empty('#network', 'No eligible GO processes are available in this context.'); $('#term-buttons').replaceChildren(); $('#network-note').textContent = 'No network edges were invented.'; return; }
  const membership = new Set(terms.flatMap(t => t.members));
  let candidates = rows.filter(r => membership.has(r.i) && r.padj !== null).sort((p, q) => p.padj - q.padj || p.i - q.i);
  if (state.term) { const t = terms.find(t => t.id === state.term); const ms = new Set(t?.members); candidates.sort((p, q) => Number(ms.has(q.i)) - Number(ms.has(p.i)) || p.padj - q.padj); }
  const visible = candidates.slice(0, 30).map(r => r.i);
  if (state.gene !== null && !visible.includes(state.gene)) { if (visible.length >= 30) visible.pop(); visible.push(state.gene); }
  const {svg, w, h} = svgFrame('#network', 320), gx = Math.max(70, w * .17), tx = Math.max(gx + 95, w * .48);
  const chars = Math.max(14, Math.floor((w - tx - 22) / 6.3));
  const gy = d3.scalePoint().domain(visible).range([12, h - 12]); const ty = d3.scalePoint().domain(terms.map(t => t.id)).range([30, h - 30]).padding(.3);
  const links = [];
  for (const t of terms) { const k = new Map(t.members.map((i, j) => [i, t.strength?.[j] ?? 1])); for (const i of visible) if (k.has(i)) links.push({i, term: t.id, s: k.get(i)}); }
  links.sort((p, q) => p.s - q.s);
  const dirColor = i => { const r = rowById.get(i); return r && significant(r) ? (r.lfc > 0 ? UP : DOWN) : '#9fb3c2'; };
  const focus = d => (state.term ? d.term === state.term : true) && (state.gene !== null && !state.term ? d.i === state.gene : true);
  svg.selectAll('.edge').data(links).join('path').attr('class', 'edge').attr('d', d => `M${gx},${gy(d.i)} C${gx + 60},${gy(d.i)} ${tx - 75},${ty(d.term)} ${tx - 10},${ty(d.term)}`)
    .attr('fill', 'none').attr('stroke', d => dirColor(d.i)).attr('stroke-width', d => STRENGTH[d.s][1])
    .attr('stroke-opacity', d => focus(d) ? (d.s === 1 ? .35 : .75) : .07)
    .on('mousemove', (e, d) => tip(e, `${label(d.i)} → ${terms.find(t => t.id === d.term).name}\n${STRENGTH[d.s][0]}`)).on('mouseleave', hideTip);
  const nodes = svg.selectAll('.network-gene').data(visible).join('g').attr('class', 'network-gene').attr('transform', i => `translate(${gx},${gy(i)})`).attr('aria-label', i => `Inspect ${label(i)}`);
  nodes.append('circle').attr('r', i => i === state.gene ? 6.5 : 4.5).attr('fill', dirColor).attr('stroke', i => i === state.gene ? '#142c40' : 'white').attr('stroke-width', 1.5);
  // Sparse labels preserve legibility; all nodes have tooltips and keyboard activation.
  nodes.filter((i, n) => n % 3 === 0 || i === state.gene).append('text').attr('x', -10).attr('y', 4).attr('text-anchor', 'end').style('font-size', '11px').style('font-weight', i => i === state.gene ? 700 : 400).text(i => label(i).slice(0, 17));
  activate(nodes, (_, i) => change({gene: i}));
  nodes.on('mousemove', (e, i) => { const r = rowById.get(i); tip(e, `${label(i)} (${genes[i][0]})\n${r && r.padj !== null ? `${fold(r.lfc)} in ${groupWord[pair()[0]]} mice` : 'not testable here'}\nIn ${links.filter(d => d.i === i).length} of the processes shown\nClick to follow it through the day`); }).on('mouseleave', hideTip);
  const tnodes = svg.selectAll('.network-term').data(terms).join('g').attr('class', 'network-term').attr('transform', t => `translate(${tx},${ty(t.id)})`).attr('aria-label', t => `Highlight ${t.name}`);
  tnodes.append('rect').attr('x', -10).attr('y', -11).attr('width', 20).attr('height', 22).attr('rx', 3).attr('fill', t => state.term === t.id ? '#142c40' : '#e9eef4').attr('stroke', '#142c40');
  tnodes.each(function (t) {
    const g = d3.select(this), lines = wrap(t.name, chars);
    lines.forEach((line, k) => g.append('text').attr('x', 16).attr('y', -3 + k * 13).style('font-size', '11.5px').style('fill', '#142c40').style('font-weight', state.term === t.id ? 700 : 500).text(line));
    g.append('text').attr('x', 16).attr('y', -3 + lines.length * 13).style('font-size', '10px')
      .text(network.mode === 'enrichment' ? (w < 500 ? `${t.overlap_count} genes · p ${fmt(t.padj)}` : `${t.overlap_count} changed genes · adj. p ${fmt(t.padj)}`) : `${t.members.length} member genes`);
  });
  activate(tnodes, (_, t) => change({term: state.term === t.id ? null : t.id}));
  tnodes.on('mousemove', (e, t) => tip(e, `${t.name}\n${t.id}\n${network.mode === 'enrichment' ? `${t.overlap_count} of the changed genes / ${t.term_background} genes tested in this process\nEnrichment adjusted p ${fmt(t.padj)}` : 'Reference annotation (not enriched)'}\nClick to outline its genes in View 2`)).on('mouseleave', hideTip);
  d3.select('#term-buttons').selectAll('button').data(terms, t => t.id).join('button').classed('active', t => t.id === state.term).attr('aria-pressed', t => String(t.id === state.term))
    .html(t => `${t.name} <small>${t.id}</small>`).on('click', (_, t) => change({term: state.term === t.id ? null : t.id}));
  const selectedNoEdges = state.gene !== null && !links.some(d => d.i === state.gene);
  const counts = d3.rollup(links, v => v.length, d => d.s);
  $('#network-note').textContent = `Showing ${visible.length} of ${candidates.length} annotated genes (most confident first) and ${terms.length} processes${network.mode === 'enrichment' ? ` (${network.total_enriched} of ${network.tested_terms} tested processes were enriched)` : ''}. Lines shown: ${counts.get(3) || 0} experimental, ${counts.get(2) || 0} inferred, ${counts.get(1) || 0} indirect. ${selectedNoEdges ? 'The selected gene belongs to none of the processes shown. ' : ''}${rows.filter(significant).length === 0 ? 'No genes pass the current cutoffs; these are reference annotations.' : ''}`;
}

/* VIEW 1 companion: a see-through 3D sketch of a mouse brain (point cloud on Canvas 2D, no extra library).
   Shape = union of ellipsoids; SCN and Hb positions approximate the Allen Mouse Brain Atlas (schematic). */
const brain = (() => {
  const canvas = $('#brain3d'); if (!canvas) return {draw() {}};
  const ctx = canvas.getContext('2d');
  // x = front(+)/back, y = top(+)/bottom, z = left/right; units ≈ mm
  const parts = [[[.4, .9, 1.9], [4.3, 2.5, 2.2]], [[.4, .9, -1.9], [4.3, 2.5, 2.2]], [[5.4, .5, .75], [1.4, 1, .8]], [[5.4, .5, -.75], [1.4, 1, .8]],
    [[-4.4, .5, 0], [1.6, 1.9, 3.1]], [[-2.4, -.9, 0], [2.8, 1.6, 2]], [[-5.6, -1.4, 0], [1.9, 1, 1.1]], [[1, -1.3, 0], [2.2, 1.2, 1.5]]];
  const inside = (p, skip) => parts.some(([c, r], k) => k !== skip && ((p[0] - c[0]) / r[0]) ** 2 + ((p[1] - c[1]) / r[1]) ** 2 + ((p[2] - c[2]) / r[2]) ** 2 < .97);
  const pts = [];
  parts.forEach(([c, r], k) => {
    const n = Math.round(260 * Math.cbrt(r[0] * r[1] * r[2]) ** 1.4);
    for (let j = 0; j < n; j++) {
      const yy = 1 - 2 * (j + .5) / n, rad = Math.sqrt(1 - yy * yy), th = j * 2.399963;
      const p = [c[0] + r[0] * Math.cos(th) * rad, c[1] + r[1] * yy, c[2] + r[2] * Math.sin(th) * rad];
      if (!inside(p, k)) pts.push(p);
    }
  });
  const REG = {SCN: [[1.1, -2.15, .32], [1.1, -2.15, -.32]], Hb: [[-.2, .65, .3], [-.2, .65, -.3]]};
  const chiasm = [[1.3, -2.55, 0], [3.8, -2.1, 1.1], [3.8, -2.1, -1.1]];
  let yaw = -.75, pitch = .32, dragging = null, userUntil = 0, running = false, hover = null, W = 0, H = 0, proj = {};
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function project(p) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = p[0] * cy + p[2] * sy, z1 = -p[0] * sy + p[2] * cy;
    const y2 = p[1] * cp - z1 * sp, z2 = p[1] * sp + z1 * cp;
    const s = Math.min(W / 18, H / 10) * 18 / (18 - z2);
    return [W / 2 + x1 * s, H / 2 + 8 - y2 * s, z2, s];
  }
  function draw() {
    const ratio = devicePixelRatio || 1; W = canvas.clientWidth; H = canvas.clientHeight;
    if (canvas.width !== Math.round(W * ratio)) { canvas.width = W * ratio; canvas.height = H * ratio; }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, W, H);
    for (const p of pts) { const [x, y, z] = project(p); ctx.globalAlpha = Math.max(.08, Math.min(.6, .3 + z * .07)); ctx.fillStyle = '#6f8aa3'; ctx.fillRect(x - .8, y - .8, 1.6, 1.6); }
    ctx.globalAlpha = .8; ctx.strokeStyle = '#e69f00'; ctx.lineWidth = 1.2; ctx.setLineDash([3, 2]);
    const c0 = project(chiasm[0]); for (const q of chiasm.slice(1)) { const c1 = project(q); ctx.beginPath(); ctx.moveTo(c0[0], c0[1]); ctx.lineTo(c1[0], c1[1]); ctx.stroke(); }
    ctx.setLineDash([]); ctx.globalAlpha = 1;
    for (const [reg, centres] of Object.entries(REG)) {
      const col = REGION_COLOR[reg], on = state.region === reg || hover === reg;
      const ps = centres.map(project); proj[reg] = ps;
      for (const [x, y, , s] of ps) {
        const rr = s * (on ? .55 : .42), g = ctx.createRadialGradient(x, y, 0, x, y, rr * 2.2);
        g.addColorStop(0, col); g.addColorStop(.45, col + 'aa'); g.addColorStop(1, col + '00');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, rr * 2.2, 0, 7); ctx.fill();
      }
      const cx = d3.mean(ps, p => p[0]), cyy = d3.mean(ps, p => p[1]), up = reg === 'Hb';
      const lx = cx + (up ? -34 : 30), ly = cyy + (up ? -34 : 34);
      ctx.strokeStyle = col; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(cx, cyy); ctx.lineTo(lx, ly); ctx.stroke();
      ctx.font = `${on ? 700 : 600} 13px Segoe UI`; ctx.fillStyle = reg === 'SCN' ? '#9a6a00' : '#1f7a4d';
      ctx.textAlign = up ? 'right' : 'left'; ctx.fillText(reg === 'SCN' ? 'SCN · clock' : 'Hb · habenula', lx + (up ? -3 : 3), ly + (up ? -2 : 10));
    }
    ctx.textAlign = 'center'; ctx.font = '11px Segoe UI'; ctx.fillStyle = '#536b7c';
    const nose = project([7.1, .4, 0]), back = project([-6.6, .3, 0]);
    ctx.fillText('front', nose[0], nose[1] - 6); ctx.fillText('back', back[0], back[1] - 6); ctx.textAlign = 'left';
  }
  function loop(t) {
    if (!running) return;
    if (!dragging && !reduce && t > userUntil) yaw = -.75 + .55 * Math.sin(t / 2600);
    draw(); requestAnimationFrame(loop);
  }
  const hit = e => { const r = canvas.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    for (const [reg, ps] of Object.entries(proj)) if (ps.some(p => Math.hypot(p[0] - x, p[1] - y) < 16)) return reg; return null; };
  canvas.addEventListener('pointerdown', e => { dragging = {x: e.clientX, y: e.clientY, yaw, pitch, moved: false}; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', e => {
    if (dragging) { const dx = e.clientX - dragging.x, dy = e.clientY - dragging.y; if (Math.abs(dx) + Math.abs(dy) > 3) dragging.moved = true;
      yaw = dragging.yaw + dx * .01; pitch = Math.max(-1.2, Math.min(1.2, dragging.pitch + dy * .01)); if (reduce) draw(); return; }
    const h = hit(e); if (h !== hover) { hover = h; canvas.style.cursor = h ? 'pointer' : 'grab'; if (reduce) draw(); }
    if (h) tip(e, h === 'SCN' ? 'SCN, the master clock: a pair of tiny nuclei at the bottom of the brain, just above where the optic nerves (dashed) cross.\nClick to show SCN comparisons.' : 'Habenula: a pair of small structures deep in the top middle of the brain, involved in disappointment and depression.\nClick to show Hb comparisons.'); else hideTip();
  });
  canvas.addEventListener('pointerup', e => { const d = dragging; dragging = null; userUntil = performance.now() + 4000; if (d && !d.moved) { const h = hit(e); if (h) change({region: h, term: null}); } });
  canvas.addEventListener('pointerleave', () => { hover = null; hideTip(); });
  new IntersectionObserver(es => { const vis = es[0].isIntersecting; if (vis && !running) { running = true; requestAnimationFrame(loop); } if (!vis) running = false; }).observe(canvas);
  document.querySelectorAll('.brain-key').forEach(b => {
    b.addEventListener('click', () => change({region: b.dataset.region, term: null}));
    b.addEventListener('mouseenter', () => { hover = b.dataset.region; if (reduce) draw(); });
    b.addEventListener('mouseleave', () => { hover = null; if (reduce) draw(); });
  });
  return {draw, highlight: r => { hover = r; if (reduce) draw(); }};
})();

/* Closing takeaway: numbers are computed from the exported results (default cutoffs .05 / 0.5). */
async function takeaway() {
  const key = '0.05:0.5', cnt = d => d.thresholds[key].up + d.thresholds[key].down;
  const rc = overview.filter(d => d.contrast === 'resilient_vs_control'), sc = overview.filter(d => d.contrast === 'susceptible_vs_control');
  const tot = d3.sum(rc, cnt), atNight = d3.sum(rc.filter(d => d.zt === 16), cnt), sus = d3.sum(sc, cnt);
  $('#fact-night').textContent = `${Math.round(atNight / tot * 100)}%`;
  $('#fact-night-text').textContent = `of the ${d3.format(',')(tot)} gene changes in resilient mice appear at one moment: early night (ZT16), when mice are active.`;
  $('#fact-ratio').textContent = `${Math.round(tot / Math.max(1, sus))}×`;
  $('#fact-ratio-text').textContent = `more changed genes in resilient mice (${d3.format(',')(tot)}) than in susceptible mice (${sus}), each compared with never-stressed mice.`;
  const n = await load('data/networks/SCN_zt16_resilient_vs_control.json'), t = n.terms[0];
  $('#fact-go').textContent = t.overlap_count;
  $('#fact-go-text').textContent = `changed genes in the brain’s clock at night share one job, “${t.name}”: how easily neurons fire. Chance alone predicts about ${Math.round(t.foreground_size * t.term_background / t.background_size)}.`;
}

/* Shared state update: every interaction goes through change(), which redraws all four views. */
async function change(patch) {
  state = {...state, ...patch}; const token = ++version;
  $('#contrast').value = state.contrast; $('#alpha').value = state.alpha === .01 ? '.01' : state.alpha === .05 ? '.05' : '.1'; $('#lfc').value = String(state.lfc);
  if (patch.gene !== undefined) $('#gene-search').value = state.gene === null ? '' : label(state.gene);
  $('#suggestions').hidden = true; hideTip();
  try {
    if (loadedId !== cid() || !rows.length) {
      status('Loading selected comparison…'); $('.grid').classList.add('processing');
      const requested = cid();
      const [c, n] = await Promise.all([load(`data/contrasts/${requested}.json`), load(`data/networks/${requested}.json`)]);
      if (token !== version) return;
      rows = c.rows.map(d => ({i: d[0], lfc: d[1], padj: d[2], baseMean: d[3], pvalue: d[4], lfcSE: d[5]}));
      network = n; loadedId = requested; rowById = new Map(rows.map(d => [d.i, d]));
      if (!network.terms.some(t => t.id === state.term)) state.term = null;
    }
    $('.grid').classList.remove('processing');
    const [a, b] = pair(), context = overview.find(d => d.id === cid());
    $('#context-title').textContent = `Now showing: ${regionFull[state.region]} · ZT${state.zt} (${ztWord[state.zt]}) · ${names[a]} vs ${names[b]} · ${context.n_group1} vs ${context.n_group2} mice`;
    overviewDraw(); volcanoDraw(); networkDraw(); await expressionDraw(token); if (token !== version) return;
    status(`${context.retained_genes.toLocaleString()} genes analysed in this comparison · ${state.gene === null ? 'choose a gene to follow it through the day' : `${label(state.gene)} selected`}${state.term ? ' · process highlight on' : ''}.`);
    window.__explorer = {state: {...state}, context, rows: rows.length, selected: state.gene === null ? null : rowById.get(state.gene), networkMode: network.mode};
  } catch (e) {
    $('.grid').classList.remove('processing');
    status(`Unable to load data: ${e.message}. Retry by reloading. Serve this folder over HTTP; do not open index.html directly.`); console.error(e);
  }
}

function search() {
  const q = $('#gene-search').value.trim().toLowerCase(); const el = $('#suggestions'); el.replaceChildren();
  if (!q) { el.hidden = true; return; }
  const hits = genes.map((g, i) => ({g, i})).filter(({g}) => g[0].toLowerCase().includes(q) || (g[1] || '').toLowerCase().includes(q))
    .sort((p, q2) => Number((q2.g[1] || '').toLowerCase() === q) - Number((p.g[1] || '').toLowerCase() === q)).slice(0, 10);
  el.hidden = false;
  if (!hits.length) { el.textContent = 'No matching gene. Try another name or an Ensembl ID.'; el.style.color = '#142c40'; return; }
  for (const {g, i} of hits) { const b = document.createElement('button'); b.textContent = `${g[1] || 'Unnamed gene'} · ${g[0]}`; b.onclick = () => change({gene: i}); el.append(b); }
}

/* Guided story: three steps that set the state and explain what to look at. */
async function tour(step) {
  if (step === 'context') {
    await change({...DEFAULT});
    const key = `${state.alpha}:${state.lfc}`, cnt = d => d.thresholds[key].up + d.thresholds[key].down;
    const all = overview.filter(d => d.contrast === state.contrast), total = d3.sum(all, cnt), atNight = d3.sum(all.filter(d => d.zt === 16), cnt);
    const sus = d3.sum(overview.filter(d => d.contrast === 'susceptible_vs_control'), cnt);
    story(`Step 1 · View 1 counts changed genes in each brain region at each time. For resilient vs never-stressed mice, ${d3.format(',')(atNight)} of the ${d3.format(',')(total)} changes (${Math.round(atNight / total * 100)}%) happen at ZT16, early in the night when mice are active, and in both regions. Now switch “Which groups to compare” to Susceptible vs control: the whole grid adds up to only ${sus} changed genes. Resilience, not just stress, leaves the bigger night-time trace.`);
    $('#overview').scrollIntoView({block: 'center'});
  }
  if (step === 'gene') {
    const r = [...rows].filter(r => r.padj !== null).sort((p, q) => p.padj - q.padj)[0];
    if (r) await change({gene: r.i});
    const [a, b] = pair();
    if (r) story(`Step 2 · ${label(r.i)} is the most confident changed gene in ${regionFull[state.region]} at ZT${state.zt}: ${fold(r.lfc)} in ${groupWord[a]} than ${groupWord[b]} mice. View 3 shows every mouse. Compare the ${a === 'resilient' ? 'triangles' : 'marks'} with the ${b === 'control' ? 'circles' : 'other group'} in the selected column, then look at the other times. Click another box in View 1 and the same gene stays selected.`);
    $('#expression').scrollIntoView({block: 'center'});
  }
  if (step === 'process') {
    if (network?.terms.length) await change({term: network.terms[0].id});
    const t = network?.terms.find(t => t.id === state.term);
    if (t) story(network.mode === 'enrichment'
      ? `Step 3 · Changed genes are not random. “${t.name}” contains ${t.overlap_count} of them, far more than chance predicts (adjusted p ${fmt(t.padj)}). Its genes are now outlined in View 2. In View 4, red genes are up-regulated and blue down-regulated; thicker lines mean more direct evidence. Lines mean “belongs to this process”, not cause and effect.`
      : `Step 3 · In this comparison no process is over-represented, so View 4 shows reference memberships only. Its genes are outlined in View 2.`);
    $('#network').scrollIntoView({block: 'center'});
  }
}

/* Glossary: hover/focus definitions on .gloss terms, plus the full list near the bottom. */
function glossary() {
  const dl = $('#glossary-list');
  for (const [key, [term, def]] of Object.entries(GLOSSARY)) {
    const div = document.createElement('div'); div.id = `g-${key}`;
    const dt = document.createElement('dt'); dt.textContent = term; const dd = document.createElement('dd'); dd.textContent = def;
    div.append(dt, dd); dl.append(div);
  }
  document.querySelectorAll('.gloss').forEach(el => {
    const entry = GLOSSARY[el.dataset.gloss]; if (!entry) return;
    el.setAttribute('aria-label', `${el.textContent}: ${entry[1]}`);
    const show = () => { const r = el.getBoundingClientRect(); place(`${entry[0]}\n${entry[1]}`, r.left, r.bottom); };
    el.addEventListener('mouseenter', show); el.addEventListener('focus', show);
    el.addEventListener('mouseleave', hideTip); el.addEventListener('blur', hideTip);
  });
}

$('#contrast').onchange = e => change({contrast: e.target.value, term: null});
$('#alpha').onchange = e => change({alpha: +e.target.value});
$('#lfc').onchange = e => change({lfc: +e.target.value});
$('#reset').onclick = () => { story(''); change({...DEFAULT}); };
$('#clear-gene').onclick = () => change({gene: null});
$('#clear-term').onclick = () => change({term: null});
$('#gene-search').oninput = search; $('#search-go').onclick = search;
$('#gene-search').onkeydown = e => { if (e.key === 'Enter') { search(); $('#suggestions button')?.click(); } if (e.key === 'Escape') $('#suggestions').hidden = true; };
document.addEventListener('click', e => { if (!e.target.closest('.search')) $('#suggestions').hidden = true; });
$('#download').onclick = () => {
  const cols = ['ensembl_id', 'symbol', 'log2FoldChange', 'padj', 'baseMean', 'pvalue', 'lfcSE'];
  const csv = d3.csvFormat(rows.map(r => ({ensembl_id: genes[r.i][0], symbol: genes[r.i][1] || '', log2FoldChange: r.lfc, padj: r.padj, baseMean: r.baseMean, pvalue: r.pvalue, lfcSE: r.lfcSE})), cols);
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'})); a.download = `${cid()}_reanalysis.csv`; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
};
document.querySelectorAll('[data-tour]').forEach(b => b.onclick = () => tour(b.dataset.tour));
let resizeTimer; window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { if (rows.length) change({}); }, 160); });
(async () => {
  glossary();
  try {
    [genes, samples, overview, manifest] = await Promise.all(['genes', 'samples', 'overview', 'manifest'].map(n => load(`data/${n}.json`)));
    await change({});
    takeaway();
  } catch (e) { status(`Initialization failed: ${e.message}`); console.error(e); }
})();
