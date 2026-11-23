'use strict';
/* D3 v7 coordinates the four views; all inference is computed offline. */
const $ = s => document.querySelector(s);
const DEFAULT = {region:'SCN',zt:16,contrast:'resilient_vs_control',alpha:.05,lfc:.5,gene:null,term:null};
let state={...DEFAULT}, genes=[],samples=[],overview=[],manifest={},rows=[],network=null,version=0;
const cache=new Map(), colors={control:'#596b85',resilient:'#007f79',susceptible:'#c25532'};
const names={control:'Control',resilient:'Resilient',susceptible:'Susceptible'};
const phases=[4,10,16,22], regions=['SCN','Hb'];
let rowById=new Map(), plotted=[], nearest=null, loadedId=null;
const cid=()=>`${state.region}_zt${state.zt}_${state.contrast}`;
const label=i=>genes[i]?.[1] || genes[i]?.[0] || 'Unknown gene';
const significant=r=>r.padj!==null&&r.padj<state.alpha&&Math.abs(r.lfc)>state.lfc;
const pointColor=r=>significant(r)?r.lfc>0?'#c25532':'#356ab4':'#afbdc9';
const fmt=v=>v===null||v===undefined?'NA':Math.abs(v)>0&&Math.abs(v)<.001?d3.format('.2e')(v):d3.format(',.3~f')(v);
function tip(event,text){const t=$('#tooltip');t.textContent=text;t.hidden=false;const w=t.offsetWidth,h=t.offsetHeight;t.style.left=`${Math.min(event.clientX+15,innerWidth-w-10)}px`;t.style.top=`${Math.max(5,Math.min(event.clientY+15,innerHeight-h-10))}px`}
function hideTip(){$('#tooltip').hidden=true}
async function load(url){if(!cache.has(url)) cache.set(url,fetch(url).then(r=>{if(!r.ok)throw Error(`${url}: ${r.status}`);return r.json()}).catch(e=>{cache.delete(url);throw e}));return cache.get(url)}
function status(text){$('#status').textContent=text}
function empty(selector,text){const el=$(selector);el.replaceChildren();const d=document.createElement('div');d.className='empty';d.textContent=text;el.append(d)}
function activate(sel,fn){sel.attr('tabindex',0).attr('role','button').on('click',fn).on('keydown',(e,d)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn(e,d)}})}
function svgFrame(selector,height){const node=$(selector);node.replaceChildren();const w=Math.max(280,node.clientWidth);return {svg:d3.select(node).append('svg').attr('viewBox',`0 0 ${w} ${height}`).attr('width','100%').attr('height',height),w,h:height}}
function overviewDraw(){
 const {svg,w}=svgFrame('#overview',248),left=48,right=8,top=42,h=70;
 const data=overview.filter(d=>d.contrast===state.contrast);
 const key=`${state.alpha}:${state.lfc}`;
 const count=d=>{const t=d.thresholds[key];return t.up+t.down};
 const max=d3.max(data,count)||1,scale=d3.scaleSequential(d3.interpolateGnBu).domain([0,max]);
 const x=d3.scaleBand().domain(phases).range([left,w-right]).paddingInner(.07),y=d3.scaleBand().domain(regions).range([top,top+h*2+16]).paddingInner(.13);
 svg.selectAll('.zt').data(phases).join('text').attr('x',d=>x(d)+x.bandwidth()/2).attr('y',20).attr('text-anchor','middle').style('font-weight',650).text(d=>`ZT${d}`);
 svg.selectAll('.region').data(regions).join('text').attr('x',0).attr('y',d=>y(d)+y.bandwidth()/2+5).style('font-weight',650).text(d=>d);
 const cell=svg.selectAll('.overview-cell').data(data).join('g').attr('class','overview-cell').attr('data-context',d=>d.id).attr('aria-label',d=>`${d.region}, ZT${d.zt}: ${count(d)} genes; n=${d.n_group1} versus ${d.n_group2}`).attr('transform',d=>`translate(${x(d.zt)},${y(d.region)})`);
 cell.append('rect').attr('width',x.bandwidth()).attr('height',y.bandwidth()).attr('rx',4).attr('fill',d=>count(d)?scale(count(d)):'#f0f4f7').attr('stroke',d=>d.region===state.region&&d.zt===state.zt?'#142c40':'none').attr('stroke-width',3);
 cell.append('text').attr('x',x.bandwidth()/2).attr('y',30).attr('text-anchor','middle').style('fill',d=>count(d)>max*.6?'white':'#142c40').style('font-size','24px').style('font-weight',650).text(d=>d3.format(',')(count(d)));
 cell.append('text').attr('x',x.bandwidth()/2).attr('y',51).attr('text-anchor','middle').style('fill',d=>count(d)>max*.6?'white':'#536b7c').style('font-size','11px').text(d=>`n = ${d.n_group1} / ${d.n_group2}`);
 activate(cell,(_,d)=>change({region:d.region,zt:d.zt,term:null}));
 cell.on('mousemove',(e,d)=>tip(e,`${d.region} · ZT${d.zt}\n${count(d)} genes (${d.thresholds[key].up} higher / ${d.thresholds[key].down} lower)\n${d3.format(',')(d.tested_genes)} finite adjusted p-values\n${d.unavailable_padj} unavailable adjusted p-values\nn = ${d.n_group1} vs ${d.n_group2}`)).on('mouseleave',hideTip);
 svg.append('text').attr('x',left).attr('y',221).text('DAY / LIGHT PHASE').style('font-size','11px');
 svg.append('text').attr('x',x(16)).attr('y',221).text('NIGHT / DARK PHASE').style('font-size','11px');
 $('#overview-legend').textContent=`Color scale: 0–${d3.format(',')(max)} passing genes, shared across these eight cells.`;$('#overview-legend').className='note';
}
function volcanoDraw(){
 const wrap=$('.volcano-wrap'),w=wrap.clientWidth,h=wrap.clientHeight,m={l:55,r:15,t:12,b:43};
 const canvas=$('#volcano-canvas'),ctx=canvas.getContext('2d'),ratio=devicePixelRatio||1;
 canvas.width=w*ratio;canvas.height=h*ratio;ctx.scale(ratio,ratio);ctx.clearRect(0,0,w,h);
 const valid=rows.filter(r=>r.padj!==null&&Number.isFinite(r.lfc));
 const xmax=Math.max(2,d3.max(valid,d=>Math.abs(d.lfc))||2)*1.06;
 const ymax=Math.max(3,d3.max(valid,d=>Math.min(300,-Math.log10(Math.max(Number.MIN_VALUE,d.padj))))||3)*1.05;
 const x=d3.scaleLinear().domain([-xmax,xmax]).range([m.l,w-m.r]);
 const y=d3.scaleLinear().domain([0,ymax]).range([h-m.b,m.t]);
 const svg=d3.select('#volcano-axis').attr('viewBox',`0 0 ${w} ${h}`);svg.selectAll('*').remove();
 svg.append('g').attr('transform',`translate(0,${h-m.b})`).call(d3.axisBottom(x).ticks(7));
 svg.append('g').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(w-m.l-m.r))).call(g=>g.select('.domain').remove());
 svg.append('text').attr('x',(w+m.l-m.r)/2).attr('y',h-3).attr('text-anchor','middle').attr('class','axis-label').text('log₂ fold change (first / second group)');
 svg.append('text').attr('transform',`translate(13,${(h-m.b)/2}) rotate(-90)`).attr('text-anchor','middle').attr('class','axis-label').text('−log₁₀ adjusted p-value');
 ctx.strokeStyle='#738897';ctx.setLineDash([4,4]);ctx.lineWidth=.8;
 for(const v of [-state.lfc,state.lfc]){ctx.beginPath();ctx.moveTo(x(v),m.t);ctx.lineTo(x(v),h-m.b);ctx.stroke()}
 const py=y(-Math.log10(state.alpha));ctx.beginPath();ctx.moveTo(m.l,py);ctx.lineTo(w-m.r,py);ctx.stroke();ctx.setLineDash([]);
 const term=network?.terms.find(t=>t.id===state.term),memberSet=new Set(term?.members||[]);
 plotted=valid.map(r=>({...r,x:x(r.lfc),y:y(Math.min(300,-Math.log10(Math.max(Number.MIN_VALUE,r.padj))))}));
 plotted.sort((a,b)=>Number(significant(a))-Number(significant(b)));
 for(const r of plotted){ctx.globalAlpha=state.term&&!memberSet.has(r.i)?.1:significant(r)?.8:.28;ctx.fillStyle=pointColor(r);ctx.beginPath();ctx.arc(r.x,r.y,significant(r)?2.4:1.4,0,Math.PI*2);ctx.fill();if(state.term&&memberSet.has(r.i)){ctx.strokeStyle='#123d48';ctx.lineWidth=.7;ctx.stroke()}}
 ctx.globalAlpha=1;const selected=plotted.find(r=>r.i===state.gene);
 if(selected){ctx.beginPath();ctx.arc(selected.x,selected.y,6,0,Math.PI*2);ctx.strokeStyle='#142c40';ctx.lineWidth=2.5;ctx.stroke();ctx.font='bold 13px Segoe UI';ctx.fillStyle='#142c40';const tw=ctx.measureText(label(selected.i)).width;ctx.fillText(label(selected.i),Math.min(w-tw-4,selected.x+9),Math.max(17,selected.y-9))}
 const delaunay=d3.Delaunay.from(plotted,d=>d.x,d=>d.y);
 canvas.onmousemove=e=>{const rect=canvas.getBoundingClientRect();const px=e.clientX-rect.left,py=e.clientY-rect.top;const idx=delaunay.find(px,py);const r=plotted[idx];nearest=r&&Math.hypot(r.x-px,r.y-py)<14?r:null;canvas.style.cursor=nearest?'pointer':'default';if(nearest)tip(e,`${label(r.i)} · ${genes[r.i][0]}\nlog₂FC ${fmt(r.lfc)} · p-adj ${fmt(r.padj)}\nClick to inspect all sampling times`);else hideTip()};
 canvas.onmouseleave=()=>{nearest=null;hideTip()};canvas.onclick=()=>{if(nearest)change({gene:nearest.i})};
 const pass=rows.filter(significant);$('#volcano-sub').textContent=`${d3.format(',')(pass.length)} passing genes · ${d3.format(',')(valid.length)} plotted · positive effects favor ${names[state.contrast.split('_vs_')[0]].toLowerCase()}.`;
 const nNA=rows.length-valid.length;
 $('#volcano-note').textContent=`${nNA} genes with unavailable statistics omitted from the plot. ${state.term?`${term?.name||state.term}: annotated genes highlighted. `:''}${state.gene!==null&&!selected?'Selected gene has no plottable adjusted p-value in this context. ':''}Zero p-values, if present, are displayed at a −log₁₀ cap of 300.`;
 const best=[...valid].sort((a,b)=>a.padj-b.padj||Math.abs(b.lfc)-Math.abs(a.lfc)).slice(0,6);
 d3.select('#candidates').selectAll('button').data(best,d=>d.i).join('button').classed('active',d=>d.i===state.gene).text(d=>label(d.i)).attr('aria-label',d=>`Inspect ${label(d.i)}`).on('click',(_,d)=>change({gene:d.i}));
}
async function expressionDraw(token){
 const selected=state.gene,region=state.region,zt=state.zt;
 if(selected===null){$('#expression-title').textContent='A gene, across the day';$('#expression-sub').textContent='Select a gene in the volcano, network, or search to reveal individual samples.';empty('#expression','One gene. Four sampling times. Every individual sample.');return}
 $('#expression-title').textContent=`${label(selected)}, across the day`;
 const r=rowById.get(selected);
 $('#expression-sub').textContent=`${genes[selected][0]} · ${region} · ${r?`selected contrast: log₂FC ${fmt(r.lfc)}, p-adj ${fmt(r.padj)}`:'filtered out of the selected contrast; expression remains available'}`;
 const chunk=await load(`data/expression/${genes[selected][2]}.json`);if(token!==version)return;
 const values=chunk[String(selected)];if(!values){empty('#expression','Expression unavailable for this gene.');return}
 const data=samples.map((s,i)=>({...s,count:values[i],value:Math.log2(values[i]+1)})).filter(s=>s.region===region);
 const {svg,w,h}=svgFrame('#expression',300),m={l:56,r:15,t:15,b:40};
 const x=d3.scalePoint().domain(phases).range([m.l+25,w-m.r-25]),y=d3.scaleLinear().domain([0,Math.max(1,d3.max(data,d=>d.value)*1.1)]).nice().range([h-m.b,m.t]);
 const step=x.step(),band=Math.min(step*.8,70);
 svg.append('rect').attr('x',x(zt)-band/2).attr('y',m.t).attr('width',band).attr('height',h-m.b-m.t).attr('fill','#edf4f7');
 svg.append('g').attr('transform',`translate(0,${h-m.b})`).call(d3.axisBottom(x).tickFormat(t=>`ZT${t}`));
 svg.append('g').attr('transform',`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(w-m.l-m.r))).call(g=>g.select('.domain').remove());
 svg.append('text').attr('transform',`translate(13,${(h-m.b)/2}) rotate(-90)`).attr('text-anchor','middle').attr('class','axis-label').text('log₂(normalized count + 1)');
 const shapes={control:d3.symbolCircle,resilient:d3.symbolTriangle,susceptible:d3.symbolSquare};
 const offsets={control:-12,resilient:0,susceptible:12};
 for(const [ph,co] of Object.entries(colors)){
  // Transform the arithmetic mean of normalized counts; do not average logged values.
  const means=phases.map(t=>{const g=data.filter(d=>d.zt===t&&d.phenotype===ph);return {zt:t,value:Math.log2(d3.mean(g,d=>d.count)+1),n:g.length}});
  svg.append('path').datum(means).attr('d',d3.line().x(d=>x(d.zt)+offsets[ph]).y(d=>y(d.value))).attr('fill','none').attr('stroke',co).attr('stroke-width',2).attr('stroke-dasharray',ph==='resilient'?'6 3':ph==='susceptible'?'2 3':null);
  svg.selectAll(`.mean-${ph}`).data(means).join('line').attr('x1',d=>x(d.zt)+offsets[ph]-7).attr('x2',d=>x(d.zt)+offsets[ph]+7).attr('y1',d=>y(d.value)).attr('y2',d=>y(d.value)).attr('stroke',co).attr('stroke-width',3);
 }
 const jitter=s=>{let v=0;for(const c of s.sample_id_analysis)v=(v*31+c.charCodeAt(0))>>>0;return (v%100)/100*9-4.5};
 const pts=svg.selectAll('.sample-point').data(data).join('path').attr('class','sample-point').attr('d',d=>d3.symbol().type(shapes[d.phenotype]).size(36)()).attr('transform',d=>`translate(${x(d.zt)+offsets[d.phenotype]+jitter(d)},${y(d.value)})`).attr('fill',d=>colors[d.phenotype]).attr('fill-opacity',.7).attr('stroke','white').attr('stroke-width',.7);
 pts.on('mousemove',(e,d)=>tip(e,`${d.sample_id_analysis}\nAnimal: ${d.animal_id} · ${names[d.phenotype]}\nZT${d.zt} · normalized count ${fmt(d.count)}\nSource: ${d.sample_id_source}`)).on('mouseleave',hideTip);
 svg.append('text').attr('x',w-m.r).attr('y',h-6).attr('text-anchor','end').style('font-size','11px').text('Lines: log₂(group mean count + 1)');
}
function networkDraw(){
 if(!network){empty('#network','GO data unavailable.');return}
 const terms=network.terms;
 const mode=network.mode==='enrichment'?'Enrichment at fixed default cutoffs':'Annotation only · no enriched terms at default cutoffs';
 $('#network-sub').textContent=`${mode}. Select a process to highlight its genes in the volcano.`;
 if(!terms.length){empty('#network','No eligible GO processes are available in this context.');$('#term-buttons').replaceChildren();$('#network-note').textContent='No network edges were invented.';return}
 const membership=new Set(terms.flatMap(t=>t.members));
 let candidates=rows.filter(r=>membership.has(r.i)&&r.padj!==null).sort((a,b)=>a.padj-b.padj||a.i-b.i);
 if(state.term){const t=terms.find(t=>t.id===state.term);const ms=new Set(t?.members);candidates.sort((a,b)=>Number(ms.has(b.i))-Number(ms.has(a.i))||a.padj-b.padj)}
 const visible=candidates.slice(0,30).map(r=>r.i);
 if(state.gene!==null&&!visible.includes(state.gene)){if(visible.length>=30)visible.pop();visible.push(state.gene)}
 const {svg,w,h}=svgFrame('#network',300),gx=Math.max(75,w*.28),tx=Math.max(185,w*.73);
 const gy=d3.scalePoint().domain(visible).range([12,h-12]);const ty=d3.scalePoint().domain(terms.map(t=>t.id)).range([35,h-35]).padding(.3);
 const links=[];for(const t of terms){const ms=new Set(t.members);for(const i of visible)if(ms.has(i))links.push({i,term:t.id})}
 svg.selectAll('.edge').data(links).join('path').attr('class','edge').attr('d',d=>`M${gx},${gy(d.i)} C${gx+60},${gy(d.i)} ${tx-75},${ty(d.term)} ${tx-10},${ty(d.term)}`).attr('fill','none').attr('stroke',d=>d.i===state.gene||d.term===state.term?'#007f79':'#b7cbd5').attr('stroke-opacity',d=>state.term&&d.term!==state.term?.15:.65).attr('stroke-width',d=>d.i===state.gene||d.term===state.term?1.7:.7);
 const nodes=svg.selectAll('.network-gene').data(visible).join('g').attr('class','network-gene').attr('transform',i=>`translate(${gx},${gy(i)})`).attr('aria-label',i=>`Inspect ${label(i)}`);
 nodes.append('circle').attr('r',i=>i===state.gene?5:3.3).attr('fill',i=>rowById.has(i)?pointColor(rowById.get(i)):'#aabac6').attr('stroke',i=>i===state.gene?'#142c40':'white').attr('stroke-width',1.5);
 // Sparse labels preserve legibility; all nodes have tooltips and keyboard activation.
 nodes.filter((i,n)=>n%3===0||i===state.gene).append('text').attr('x',-9).attr('y',4).attr('text-anchor','end').style('font-size','11px').style('font-weight',i=>i===state.gene?700:400).text(i=>label(i).slice(0,17));
 activate(nodes,(_,i)=>change({gene:i}));nodes.on('mousemove',(e,i)=>tip(e,`${label(i)}\n${genes[i][0]}\n${links.filter(d=>d.i===i).length} visible process memberships`)).on('mouseleave',hideTip);
 const tnodes=svg.selectAll('.network-term').data(terms).join('g').attr('class','network-term').attr('transform',t=>`translate(${tx},${ty(t.id)})`).attr('aria-label',t=>`Highlight ${t.name}`);
 tnodes.append('rect').attr('x',-10).attr('y',-11).attr('width',20).attr('height',22).attr('rx',3).attr('fill',t=>state.term===t.id?'#007f79':'#e0eeed').attr('stroke','#007f79');
 tnodes.append('text').attr('x',16).attr('y',-2).style('font-size','11px').text(t=>t.id);
 tnodes.append('text').attr('x',16).attr('y',12).style('font-size','10px').text(t=>network.mode==='enrichment'?`q ${fmt(t.padj)}`:`${t.members.length} members`);
 activate(tnodes,(_,t)=>change({term:state.term===t.id?null:t.id}));tnodes.on('mousemove',(e,t)=>tip(e,`${t.name}\n${t.id}\nBH p-adj ${fmt(t.padj)} (default cutoffs)\n${t.overlap_count} foreground / ${t.term_background} background genes`)).on('mouseleave',hideTip);
 d3.select('#term-buttons').selectAll('button').data(terms,t=>t.id).join('button').classed('active',t=>t.id===state.term).attr('aria-pressed',t=>String(t.id===state.term)).text(t=>`${t.id} · ${t.name}`).on('click',(_,t)=>change({term:state.term===t.id?null:t.id}));
 const selectedNoEdges=state.gene!==null&&!links.some(d=>d.i===state.gene);
 $('#network-note').textContent=`Showing ${visible.length} of ${candidates.length} ranked annotated genes; ${terms.length} processes (${network.total_enriched} enriched across ${network.tested_terms} tested terms). Gene order follows p-adj; process selection prioritizes members. ${selectedNoEdges?'Selected gene has no edge to the displayed processes. ':''}${rows.filter(significant).length===0?'No genes pass the current exploration cutoffs; these are reference annotations.':''}`;
}
async function change(patch){
 const old=cid();state={...state,...patch};const token=++version;
 $('#contrast').value=state.contrast;$('#alpha').value=state.alpha===.01?'.01':state.alpha===.05?'.05':'.1';$('#lfc').value=String(state.lfc);
 if(patch.gene!==undefined)$('#gene-search').value=state.gene===null?'':label(state.gene);
 $('#suggestions').hidden=true;hideTip();
 try{
  if(loadedId!==cid()||!rows.length){status('Loading selected comparison…');$('.grid').classList.add('processing');const requested=cid();const [c,n]=await Promise.all([load(`data/contrasts/${requested}.json`),load(`data/networks/${requested}.json`)]);if(token!==version)return;rows=c.rows.map(d=>({i:d[0],lfc:d[1],padj:d[2],baseMean:d[3],pvalue:d[4],lfcSE:d[5]}));network=n;loadedId=requested;rowById=new Map(rows.map(d=>[d.i,d]));if(!network.terms.some(t=>t.id===state.term))state.term=null}
  $('.grid').classList.remove('processing');
  const [a,b]=state.contrast.split('_vs_'),context=overview.find(d=>d.id===cid());
  $('#context-title').textContent=`${state.region} / ZT${state.zt} / ${names[a]} vs ${names[b]} · n = ${context.n_group1} vs ${context.n_group2}`;
  overviewDraw();volcanoDraw();networkDraw();await expressionDraw(token);if(token!==version)return;
  status(`Prepared DESeq2 results · ${context.retained_genes.toLocaleString()} retained genes · ${state.gene===null?'choose a gene to inspect its profile':`${label(state.gene)} selected`}${state.term?' · process highlight active':''}.`);
  window.__explorer={state:{...state},context,rows:rows.length,selected:state.gene===null?null:rowById.get(state.gene),networkMode:network.mode};
 }catch(e){$('.grid').classList.remove('processing');status(`Unable to load data: ${e.message}. Retry by reloading. Serve this folder over HTTP; do not open index.html directly.`);console.error(e)}
}
function search(){const q=$('#gene-search').value.trim().toLowerCase();const el=$('#suggestions');el.replaceChildren();if(!q){el.hidden=true;return}const hits=genes.map((g,i)=>({g,i})).filter(({g})=>g[0].toLowerCase().includes(q)||(g[1]||'').toLowerCase().includes(q)).sort((a,b)=>Number((b.g[1]||'').toLowerCase()===q)-Number((a.g[1]||'').toLowerCase()===q)).slice(0,10);el.hidden=false;if(!hits.length){el.textContent='No matching gene. Try an Ensembl ID.';el.style.color='#142c40';return}for(const {g,i} of hits){const b=document.createElement('button');b.textContent=`${g[1]||'Unmapped symbol'} · ${g[0]}`;b.onclick=()=>change({gene:i});el.append(b)}}
$('#contrast').onchange=e=>change({contrast:e.target.value,term:null});$('#alpha').onchange=e=>change({alpha:+e.target.value});$('#lfc').onchange=e=>change({lfc:+e.target.value});$('#reset').onclick=()=>change({...DEFAULT});$('#clear-gene').onclick=()=>change({gene:null});$('#clear-term').onclick=()=>change({term:null});$('#gene-search').oninput=search;$('#search-go').onclick=search;$('#gene-search').onkeydown=e=>{if(e.key==='Enter'){search();$('#suggestions button')?.click()}if(e.key==='Escape')$('#suggestions').hidden=true};
document.addEventListener('click',e=>{if(!e.target.closest('.search'))$('#suggestions').hidden=true});
$('#download').onclick=()=>{const cols=['ensembl_id','symbol','log2FoldChange','padj','baseMean','pvalue','lfcSE'];const csv=d3.csvFormat(rows.map(r=>({ensembl_id:genes[r.i][0],symbol:genes[r.i][1]||'',log2FoldChange:r.lfc,padj:r.padj,baseMean:r.baseMean,pvalue:r.pvalue,lfcSE:r.lfcSE})),cols);const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download=`${cid()}_reanalysis.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
document.querySelectorAll('[data-tour]').forEach(b=>b.onclick=async()=>{if(b.dataset.tour==='context'){await change({...DEFAULT});status('Task 1: compare the eight context cells, noting sample sizes and available tests. Select a cell to inspect its volcano.');$('#overview').scrollIntoView({block:'center'})}if(b.dataset.tour==='gene'){const r=[...rows].filter(r=>r.padj!==null).sort((a,b)=>a.padj-b.padj)[0];if(r)await change({gene:r.i});$('#expression').scrollIntoView({block:'center'})}if(b.dataset.tour==='process'){if(network?.terms.length)await change({term:network.terms[0].id});$('#network').scrollIntoView({block:'center'})}});
let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(rows.length)change({})},160)});
(async()=>{try{[genes,samples,overview,manifest]=await Promise.all(['genes','samples','overview','manifest'].map(n=>load(`data/${n}.json`)));await change({})}catch(e){status(`Initialization failed: ${e.message}`);console.error(e)}})();
