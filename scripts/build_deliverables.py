"""Create bounded report/proposal PDFs, editable Word files, slides and figures."""
from pathlib import Path
import json, textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from docx import Document
from docx.shared import Inches,Pt
from pptx import Presentation
from pptx.util import Inches as PI,Pt as PP
from pptx.dml.color import RGBColor
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon
from PIL import Image as PILImage

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';F=D/'figures';F.mkdir(exist_ok=True)
URL='https://doofen-bit.github.io/Crazy-Micky/'
REPO='https://github.com/Doofen-bit/Crazy-Micky'
overview=pd.read_csv(ROOT/'results/overview.csv');overview['DEGs']=overview.up+overview.down
samples=pd.read_csv(ROOT/'results/samples.csv')
df=pd.read_csv(ROOT/'results/contrasts/SCN_zt16_resilient_vs_control.csv')
gene=df.loc[df.symbol=='Kcnk2'].iloc[0]
norm=pd.read_csv(ROOT/'results/normalized_counts.csv',index_col=0)
net=json.loads((ROOT/'site/data/networks/SCN_zt16_resilient_vs_control.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#142c40','text.color':'#142c40'})
fig,ax=plt.subplots(figsize=(8,3.2),layout='constrained')
matrix=overview[overview.contrast=='resilient_vs_control'].pivot(index='region',columns='zt',values='DEGs').loc[['SCN','Hb'],[4,10,16,22]]
im=ax.imshow(matrix.values,cmap='GnBu',vmin=0,vmax=matrix.values.max(),aspect='auto')
for i in range(2):
 for j in range(4):ax.text(j,i,str(matrix.iloc[i,j]),ha='center',va='center',fontsize=21,weight='bold',color='white' if matrix.iloc[i,j]>500 else '#142c40')
ax.set_xticks(range(4),['ZT4','ZT10','ZT16','ZT22']);ax.set_yticks(range(2),['SCN','Hb']);ax.set_title('Resilient vs control: passing genes at common cutoffs',loc='left',pad=15)
fig.colorbar(im,ax=ax,label='DEG count',shrink=.8);fig.savefig(F/'context-summary.png',dpi=220);fig.savefig(F/'context-summary.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,3.7),layout='constrained')
for ph,co,marker,offset in [('control','#596b85','o',-.18),('resilient','#007f79','^',0),('susceptible','#c25532','s',.18)]:
 means=[]
 for j,t in enumerate([4,10,16,22]):
  ss=samples[(samples.region=='SCN')&(samples.zt==t)&(samples.phenotype==ph)]
  vals=norm.loc[gene.ensembl_id,ss.sample_id_analysis].to_numpy()
  ax.scatter(j+offset+np.linspace(-.045,.045,len(vals)),np.log2(vals+1),s=28,c=co,marker=marker,alpha=.75)
  means.append(np.log2(vals.mean()+1))
 ax.plot(np.arange(4)+offset,means,c=co,ls={'control':'-','resilient':'--','susceptible':':'}[ph],label=ph.title())
ax.set_xticks(range(4),['ZT4','ZT10','ZT16','ZT22']);ax.set_ylabel('log2(normalized count + 1)');ax.set_ylim(0,None);ax.legend(ncol=3,frameon=False,loc='lower center');ax.set_title('Kcnk2 in SCN: individual samples and group means',loc='left')
fig.savefig(F/'kcnk2-profile.png',dpi=220);fig.savefig(F/'kcnk2-profile.pdf');plt.close(fig)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=10.1,leading=14.3,textColor=colors.HexColor('#233c4d'),spaceAfter=8))
styles.add(ParagraphStyle(name='HeadX',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=colors.HexColor('#103f59'),spaceAfter=12))
styles.add(ParagraphStyle(name='SubX',fontName='Helvetica-Bold',fontSize=11.5,leading=15,textColor=colors.HexColor('#007f79'),spaceBefore=10,spaceAfter=5))
styles.add(ParagraphStyle(name='SmallX',fontName='Helvetica',fontSize=8.3,leading=11.5,textColor=colors.HexColor('#536b7c'),spaceAfter=6))
styles.add(ParagraphStyle(name='TitleX',fontName='Times-Roman',fontSize=29,leading=32,textColor=colors.HexColor('#142c40'),spaceAfter=14))
def p(text,style='BodyX'):return Paragraph(text,styles[style])
def img(path,width=475,maxheight=300):
 w,h=PILImage.open(path).size;scale=min(width/w,maxheight/h);return Image(str(path),width=w*scale,height=h*scale)
def table(data,widths=None):
 t=Table([[p(str(x),'SmallX') for x in row] for row in data],colWidths=widths,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#dce4eb')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#dce4eb'));c.line(48,42,A4[0]-48,42);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#536b7c'));c.drawString(48,28,'STRESS ATLAS | Information Visualization | Fall 2026');c.drawRightString(A4[0]-48,28,str(doc.page))
def diagram():
 d=Drawing(495,183)
 for x,y,title,lines in [(0,96,'CONTEXT OVERVIEW',['region x time / printed DEG counts','Click cell: set region and time']), (260,96,'VOLCANO',['log2FC x -log10 adjusted p','Click point: select gene']), (0,0,'TIME PROFILE',['Individual dots + phenotype means','Selected gene / all four times']), (260,0,'GENE-GO NETWORK',['Gene circles - process rectangles','Click process: highlight members'])]:
  d.add(Rect(x,y,235,79,rx=5,fillColor=colors.HexColor('#eef5f7'),strokeColor=colors.HexColor('#ccdce3')))
  d.add(String(x+12,y+58,title,fontName='Helvetica-Bold',fontSize=10,fillColor=colors.HexColor('#007f79')))
  for j,line in enumerate(lines):d.add(String(x+12,y+36-j*16,line,fontName='Helvetica',fontSize=9,fillColor=colors.HexColor('#233c4d')))
 for x1,y1,x2,y2 in [(235,136,258,136),(117,96,117,81),(377,96,377,81)]:
  d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor('#007f79'),strokeWidth=1.5))
 d.add(String(170,85,'shared selections',fontName='Helvetica',fontSize=8,fillColor=colors.HexColor('#536b7c')))
 return d
def write_pdf(name,pages):
 flow=[]
 for i,page in enumerate(pages):
  if i:flow.append(PageBreak())
  flow.extend(page)
 SimpleDocTemplate(str(D/name),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=55).build(flow,onFirstPage=footer,onLaterPages=footer)
def docx_from_sections(name,sections):
 doc=Document();normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10.5)
 for i,(title,paras,figure) in enumerate(sections):
  if i:doc.add_page_break()
  doc.add_heading(title,0 if i==0 else 1)
  for text in paras:doc.add_paragraph(text)
  if figure:doc.add_picture(str(figure),width=Inches(6.1))
 doc.save(D/name)

team='Yixuan Du (yd2927) · Yi Yao (yy5075) · Jinyu Zheng (jz6539)'
links=f'Repository: <link href="{REPO}" color="#007f79">{REPO}</link><br/>GitHub Pages: <link href="{URL}" color="#007f79">{URL}</link>'
status='Implementation snapshot: 23 November 2026. Team review, instructor discussion, and personal reflection revision remain required before submission.'
tasks=[['Task / audience','Successful use'],['Compare contexts','A biology student locates region/time strata with more passing genes, while checking n and tested-gene counts.'],['Inspect a candidate','Select a gene; inspect direction, adjusted p-value and every individual sample across four times.'],['Explore relationships','Select a GO process to see its annotated genes highlighted in the volcano; distinguish membership from enrichment.']]
design=[['View','Encoding and linked behavior'],['Context overview','Region rows × time columns; lightness plus printed counts; shared scale. Cell click changes contrast context and network, retaining the gene.'],['Volcano','Position encodes log2FC and -log10(p-adj); thresholds and a selection ring add noncolor cues. Click or search selects a gene. Canvas handles ~17k genes; D3 provides scales and picking.'],['Time profile','Individual animals use color + shape; group means use distinct line styles. A selected time is shaded. No animal trajectories or inferred rhythm.'],['Gene–GO network','Deterministic bipartite node-link layout; circles are genes and rectangles are processes. A process click highlights all matching genes in the volcano. Bounded to 5 terms and 30 genes.']]
report=[]
report.append([p('Stress, across time.','TitleX'),p('An interactive RNA-seq explorer','HeadX'),p(team),p(links,'SmallX'),p(status,'SmallX'),p('1. Problem, data and audience','SubX'),p('Stress-associated expression can vary with brain region and sampling time. We built a static D3 application for biology undergraduates and new lab students to compare contexts, inspect individual variability, and explore functional annotations. The interface supports investigation rather than making mechanistic or clinical claims.'),p('The public Narain et al. (2024) mouse dataset covers SCN and habenula (Hb), ZT4/10/16/22, and control/resilient/susceptible phenotypes. The supplied 180.4 MB archive contains 96 count files × 46,603 Ensembl genes. There are 11,159 genes with zero counts across all raw samples. After three documented exclusions, 93 tissues from 47 animals remain; all 24 region/time/phenotype cells are represented.'),p('Relevant fields: Ensembl ID (key), count (integer), region and phenotype (categorical), ZT (ordered sampling time), animal ID (pairing), source and corrected sample IDs (provenance), log2FC and adjusted p-value (model outputs). Group sizes are 3–5. Data are released under CC BY 4.0.'),p('2. Three user tasks','SubX'),table(tasks,[112,385]),p('3. Preparation that changes interpretation','SubX'),p('C01_E1 keeps the corrected raw ZT4 label, ignoring a stale processed ZT10 header. A15_A requires one analysis-only region swap: author-normalized columns match the opposite raw file across 35,364 genes with relative reconstruction error below 5 × 10<super>-15</super>. Source files remain immutable. Exclusions: L1R-E05_5, S1R-E05_5 and L2S-E05_1. Complete suffixes identify animals; different sampling times are different animals.')])
report.append([p('4. Four distinct, linked views','HeadX'),table(design,[95,402]),Spacer(1,12),img(D/'view-overview.png',width=245,maxheight=225),p('Actual final overview, default resilient/control comparison. All view screenshots and the responsive dashboard are included as separate PNG files. Numeric counts make the heatmap readable without relying on color alone.','SmallX'),p('Why this design','SubX'),p('A dashboard keeps context, gene evidence and annotations simultaneously available. A volcano alone conceals sample variability; a ranked bar chart alone conceals the joint distribution of effect and statistical evidence. The profile uses individual points instead of smooth curves or animal trajectories. A deterministic two-column network avoids unstable force-layout motion and has explicit membership semantics. Sparse network labels are supplemented by tooltips, keyboard focus and full process buttons.'),p('Interaction trace','SubX'),p('SCN/ZT16 cell → load its prepared contrast/network → click Kcnk2 → update all 47 SCN expression points and selection marks → select a process → highlight its annotated volcano points → switch Hb context while preserving the gene → reset to SCN/ZT16, resilient/control, .05/.5, no gene or process selected.'),p('Accessibility and empty states','SubX'),p('HTML controls, keyboard-activatable cells/nodes, visible focus, group shapes/line patterns, printed values, tooltips, and responsive layouts support exploration. Null adjusted p-values are omitted from the y-axis with a count. A filtered-out gene can still show expression. No-DEG and annotation-only states are explicit; a no-GO response is tested separately. A human accessibility/usability study has not been conducted.')])
report.append([p('5. Implementation and statistical contract','HeadX'),p('Read-only data audit → R/DESeq2 models → Python annotation/enrichment/export → relative JSON assets → D3 scales, Canvas volcano and SVG views → shared state and coordinated updates. Source modules: prepare_inputs.py, verify_label_provenance.py, run_analysis.R, export_site.py, app.js, styles.css and index.html. A rendered R Markdown workbench explains and displays the actual results.'),p('Eight models, 24 contrasts','SubX'),p('Classroom filtering is retained: any phenotype median raw count ≥10 within a region/time stratum. DESeq2 median-ratio factors are estimated across all included times within each region, then reused in each ~phenotype stratum model and expression profile. Each fit contains three phenotypes and yields three explicit contrasts. Effects are unshrunken; positive log2FC favors the first named group. Independent filtering uses α=.05 and retains NA values. Default exploration uses p-adj&lt;.05 and |log2FC|&gt;.5, unlike the classroom .1/1 defaults. Changing website cutoffs does not rerun independent filtering or model fitting.'),p('GO Biological Process','SubX'),p('org.Mm.eg.db 3.23.0 and GO.db 3.23.1 supply Ensembl and inherited GOALL BP membership. Python/SciPy implements one-sided hypergeometric tests with BH correction across all eligible terms per contrast, including zero overlaps. Background = GO-mapped genes with finite p-adj; foreground = those passing .05/.5. Eligible term sizes are 10–500 background genes. Enrichment remains fixed when exploration cutoffs change. Terms absent at q&lt;.05 trigger an annotation-only fallback, never invented enrichment.'),p('Verification and performance','SubX'),table([['Check','Observed result'],['Scientific invariants','96 raw files aligned; 93 included samples; unique IDs; full-rank models; all reverse contrasts negate log2FC and preserve p-values; normalized-mean signs agree.'],['Export validation','All normalized values reconstructed from raw counts/size factors; all 24 filters independently reconstructed; every exported contrast value and NA checked; GO p-values and BH verified.'],['Browser QA','Chromium: 24 contexts, linked selection, process clear, gene search, reset, CSV download, no-DEG/NA/no-selection/no-GO states. No JS errors or failed requests.'],['Delivery','Initial assets: 3.66 MB uncompressed; complete static site: ~88.5 MB. Expression chunks contain 256 genes and load on demand. 1440, 1366 and 390 px layouts verified.']],[110,387]),p('Limits of the checks: automated QA is not human user testing; no new biological experiment was performed. The code uses no browser-side statistical fitting.','SmallX')])
report.append([p('6. Demonstration findings and boundaries','HeadX'),img(F/'context-summary.png',maxheight=200),p('At common .05/.5 cutoffs, resilient/control yields SCN counts 9, 0, 779, 0 and Hb counts 24, 0, 225, 1 across ZT4/10/16/22. This is a property of our declared reanalysis, not an exact replication of the paper. The table of finite adjusted p-values is essential: available test counts differ across contexts.'),img(F/'kcnk2-profile.png',maxheight=205),p(f'Kcnk2 is a demonstration candidate in SCN/ZT16: log2FC={gene.log2FoldChange:.3f}, p-adj={gene.padj:.3g}. Inspecting the points shows how the group means relate to individual samples. In this context, {net["total_enriched"]} BP terms pass q&lt;.05; regulation of membrane potential has 63 foreground members and q={net["terms"][0]["padj"]:.3g}. GO terms overlap hierarchically and are not independent mechanisms.'),p('Interpretation limits','SubX'),p('Significance at one time but not another is not a formal time-by-phenotype interaction. Four time points do not prove rhythmicity. Small unequal n, male-only animals, bulk tissue composition, possible unmodeled batch effects and a single dataset limit generalization. Two brain regions from one animal are paired; no cross-region inferential model is fit. Normalization is within region, so between-region profiles should not be treated as absolute abundance comparisons.')])
report.append([p('7. Changes, responsibilities and reflection','HeadX'),p('Changes from the proposal','SubX'),p('The four-view D3 plan and full eligible coverage were retained. Metadata uncertainty was replaced by reproducible content matching. A15_A is corrected once and C01_E1 uses raw ZT4. Three-group stratum models and region-wide factors make analysis/export semantics explicit. Public GO BP replaced dependence on commercial pathway software. A bounded deterministic bipartite network and annotation fallback prevent empty enrichment from being represented as a discovery. Chunked assets meet the planned initial-load target.'),p('AI and team responsibilities','SubX'),table([['Component','AI assistance / human responsibility'],['Data and statistics','Codex drafted audit/model/export/check scripts. Du and Zheng should review label evidence, normalization, contrasts, denominators and biological interpretation.'],['D3 and interaction','Codex implemented and tested the interface. Yao and the team should review encodings, accessibility, interactions and deployment.'],['Writing and presentation','Codex drafted the report, proposal, slides and demo script. All members must revise wording, add their own reflection, rehearse and understand the code. These are responsibilities, not claims of completed member work.']],[111,386]),p('Reflection: implementation observations; personal revision required','SubX'),p('The largest challenge was preserving meaning across data layers: filenames were insufficient evidence for sample identity, and missing adjusted p-values could not be treated as zeros. Content-level checks resolved the region swap. Linked visualization also required separating exploratory thresholds from precomputed enrichment. Inspecting individual samples made the volcano less easy to overinterpret. With more time, we would run a task-based study with biology students, review color/keyboard accessibility with users, add batch sensitivity analysis, and consider a preregistered interaction model. This paragraph summarizes implementation experience; each team member should replace or extend it with their own learning before submission.'),p('Submission schedule','SubX'),p('Nov 24: planned instructor discussion (not claimed completed). Nov 25: proposal. Dec 6: public visualization deadline. Dec 7 or 9: all members present. Dec 11: final report, source and public link. Public URL and repository are on page 1; publication is independently checked in audit/deployment.json.'),p('References and credits','SubX'),p('[1] Narain et al. (2024). Translational Psychiatry 14, 407. doi:10.1038/s41398-024-03100-w. [2] GIN data, doi:10.12751/g-node.jj57l9 (CC BY 4.0). [3] Love, Huber & Anders (2014), DESeq2. doi:10.1186/s13059-014-0550-8. [4] Bioconductor org.Mm.eg.db / GO.db, versions and source metadata archived. [5] D3.js 7.9.0, d3js.org (ISC). [6] Local gb_RNAseq_student.Rmd, Genomics and Bioinformatics classroom code. [7] OpenAI ChatGPT/Codex, https://chatgpt.com/; assisted implementation, verification and drafting. No article figures reused.','SmallX')])
write_pdf('Final_Report.pdf',report)

proposal=[
[p('Stress, across time.','TitleX'),p('Information Visualization proposal','HeadX'),p('4.1 Basic information and overview','SubX'),p(team),p(links,'SmallX'),p('A D3 visual analysis application for biology students to investigate stress-associated gene expression across brain regions and sampling times. The four-view prototype is implemented; this updated proposal records the plan and current evidence for instructor discussion, not instructor approval.'),p('4.2 Data and preparation','SubX'),p('Narain et al. (2024), doi:10.1038/s41398-024-03100-w; public CC BY 4.0 data at doi.gin.g-node.org/10.12751/g-node.jj57l9/. The 180.4 MB supplied archive includes 96 gene-count files with 46,603 Ensembl rows each. Main fields are integer counts, sample/animal ID, categorical region/phenotype, ordered ZT, and model statistics. All counts are nonnegative integers and gene order is identical; 11,159 genes are globally zero.'),p('The complete scope is SCN/Hb × ZT4/10/16/22 × control/resilient/susceptible. Three author exclusions leave 93 tissues, 47 animals and n=3–5 per cell. C01_E1 uses corrected ZT4. A15_A is mapped once to opposite analysis regions based on full-gene content matching. Raw and classroom files remain unchanged. Prepared DESeq2 contrasts and region-normalized gene chunks are used by the browser; NA remains missing.'),p('Known limitations: small male-mouse bulk-tissue dataset; tissue composition and possible batch effects; paired brain regions; different animals across times; changing tested universes. Annotation is not regulation, and a time profile is not proof of rhythmicity.'),p('4.3 Usage scenario and tasks','SubX'),p('A new lab student prepares for a journal club. They compare contexts, choose an expression candidate, and inspect its individual samples and shared biological processes. Successful use includes stating the selected contrast, n, thresholds and the limits of the result.'),table(tasks,[112,385])],
[p('4.4 Visualization design and sketches','HeadX'),table(design,[95,402]),Spacer(1,10),diagram(),p('Annotated layout sketch: boxes show view roles and selection flow; no plotted marks or biological values are invented. Actual final-view screenshots are included in docs/. Core features: four views, context/gene/process linkage, search/reset, source/threshold labels, individual samples, keyboard controls and honest empty states. Optional extensions: formal user testing, batch sensitivity and interaction models.','SmallX'),p('Encoding and alternative','SubX'),p('Position supports effect/significance comparison; hue plus shape and line style identifies phenotypes; lightness plus counts compares contexts. A node-link diagram meets the complex-layout requirement. A standalone volcano or static heatmap would lose the connection to sample variation and process membership. A deterministic bipartite layout is easier to explain than a moving force layout. The network is bounded to five terms and 30 genes, with displayed truncation and annotation-only fallback.'),p('Linked interaction','SubX'),p('Select SCN/ZT16 → volcano and process network update. Select Kcnk2 → profile and marks update. Select a process → annotated volcano points highlight. Change context → preserve gene, update selected-time marker. Reset → clear selections and restore documented default context.')],
[p('4.5 Implementation design','HeadX'),p('<b>Raw counts + label evidence</b><br/>↓ prepare_inputs.py / verify_label_provenance.py<br/><b>R: DESeq2 + mouse annotation</b><br/>↓ run_analysis.R<br/><b>Python: GO hypergeometric/BH + chunked exports</b><br/>↓ export_site.py<br/><b>D3 application: shared state → overview / volcano / profile / network</b><br/>↓ GitHub Actions → public static GitHub Pages'),p('The browser consumes relative JSON assets. It does not fit models. Eight region/time three-group fits provide 24 contrasts. First load is ~3.66 MB; 256-gene expression chunks are cached on demand. app.js owns state and render functions; index.html/styles.css own layout and accessible controls. Model and browser checks are stored in audit/.'),p('4.6 AI and team responsibilities','SubX'),table([['Component','AI assistance','Team review'],['Audit / R / export','Draft parsing, statistical calls and checks','Du / Zheng: verify counts, labels, contrast directions, NA and annotation background'],['D3 / state / UI','Draft render/event code and test transitions','Yao / team: justify encodings; inspect values and accessibility'],['Documents / demo','Draft report, proposal, slides and notes','All: revise in own voice, understand code, contribute personal reflection']],[95,175,227]),p('4.7 Team responsibilities and schedule','SubX'),p('Proposed ownership: Du — questions, metadata, overview and integration; Zheng — classroom analysis adaptation and expression view; Yao — frontend architecture, volcano/network and deployment. These assignments do not imply already-completed individual contributions.'),table([['Milestone','Plan / status'],['Nov 23–25','Implementation snapshot prepared; discuss with Gu Nov 24 and revise proposal before Nov 25. Discussion is not claimed completed.'],['By Dec 6','Review scientific choices, conduct team acceptance testing, publish and verify public GitHub Pages.'],['Dec 7 / 9','All members demonstrate tasks and justify design; rehearse failure/empty states.'],['By Dec 11','Revise reflection and final report (≤5 pages); submit report, source code and public URL.']],[105,392]),p('AI disclosure: OpenAI Codex assisted auditing, implementation, checks and drafts; https://chatgpt.com/. External resources: Narain/GIN data, DESeq2, Bioconductor mouse GO annotations, D3.js 7.9.0 and local classroom code.','SmallX')]
]
write_pdf('Proposal_Updated.pdf',proposal)

# Editable counterparts contain the exact text extracted from the same flowables.
def flow_text(pages):
 import re,html
 sections=[]
 for i,page in enumerate(pages):
  texts=[]
  for f in page:
   if isinstance(f,Paragraph):texts.append(html.unescape(re.sub('<[^>]+>',' ',f.text)))
   elif isinstance(f,Table):
    for row in f._cellvalues:texts.append(' | '.join(html.unescape(re.sub('<[^>]+>',' ',getattr(x,'text',str(x)))) for x in row))
  sections.append((texts[0],texts[1:],None))
 return sections
docx_from_sections('Final_Report_Editable.docx',flow_text(report))
docx_from_sections('Proposal_Updated_Editable.docx',flow_text(proposal))

slides=[
('Stress, across time.','A linked RNA-seq explorer', ['Two brain regions. Four sampling times. Three phenotypes.','Yixuan Du · Yi Yao · Jinyu Zheng',URL],None,'Du：开场说明目标是探索数据而非证明机制。介绍三个问题，约40秒。'),
('Start with three questions','Audience: biology undergraduates and new lab students',['Where are differences concentrated?','How variable is one candidate gene?','Which biological processes connect selected genes?'],None,'Du：用journal club场景串联三个任务，避免先讲软件细节。'),
('Know what one point means','93 tissues from 47 animals',['96 raw files × 46,603 genes; three author exclusions.','Both regions and all four times / three phenotypes remain covered.','Paired brain regions; different animals at different times.'],F/'context-summary.png','Du：数值图是已计算结果，不是示意。说明n=3–5，脑区配对但没有跨脑区检验。'),
('Labels needed evidence','A15_A is corrected once; C01_E1 remains ZT4',['A15_A author columns match opposite raw files across 35,364 genes.','Keep source IDs, analysis IDs and complete animal IDs separately.','Raw data and classroom code are unchanged.'],None,'Zheng：解释不能仅靠文件名交换；展示metadata-content-matching.json的重建误差。'),
('Four views, one context','Select a context, then inspect its evidence',['Heatmap: compare all region/time contexts.','Volcano: effect and statistical evidence together.','Profile: every sample, not only the mean.','Network: shared GO membership, never causality.'],D/'view-overview.png','Yao：解释四视图不同作用与联动；准备切换浏览器演示。'),
('A context worth inspecting','Resilient vs control, common .05/.5 cutoffs',['SCN ZT16: 779 passing genes. Hb ZT16: 225.','Counts also depend on n and tested-gene availability.','A difference in significance is not an interaction test.'],F/'context-summary.png','Du：只陈述本重分析结果；不声称完整复现论文或时间效应得到证明。'),
('Select Kcnk2','Move from a statistical point to individual samples',[f'SCN ZT16: log2FC {gene.log2FoldChange:.3f}; adjusted p {gene.padj:.3g}.','Symbols and line styles distinguish phenotypes.','Lines connect means, not repeated animals.'],F/'kcnk2-profile.png','Zheng：现场点击Kcnk2，看47个SCN样本，切Hb保留基因。强调共享region normalization。'),
('Processes connect annotations','A bounded bipartite node-link diagram',['At most five terms and 30 ranked genes.','Selecting a process highlights annotated volcano genes.','Fixed default enrichment; annotation fallback when none pass.'],D/'view-network.png','Yao：点击regulation of membrane potential。说明q值不随探索阈值重算，边只是membership。'),
('Live demo','A short path with an honest empty state',['Reset → SCN / ZT16 → select Kcnk2.','Select a process → inspect cross-highlights.','Switch Hb, then SCN / ZT10: zero DEGs is a valid result.','Change cutoffs → search a gene → reset.'],None,'三人各负责一段约40–60秒；网络失败时打开本地start_explorer.cmd或使用截图。'),
('Prepared data, reproducible views','Inference stays offline',['Eight DESeq2 fits; 24 explicit contrasts; preserved NA.','Mouse GO annotations; declared enrichment background and BH family.','Chunked static assets; first load ~3.66 MB; GitHub Pages.'],None,'Zheng解释模型，Yao解释D3 scales/Canvas/SVG和共享state。不要展开全部代码。'),
('What we checked—and what remains','Automated validation is not a user study',['Raw alignment, exclusions, reverse contrasts, normalization and GO math pass.','All 24 contexts and linked/empty states tested in Chromium.','Desktop and mobile layouts checked; no console or HTTP errors.','Small male-mouse dataset; batch effects, tissue composition, no causal claims.'],None,'Du：可说明还需要真实用户任务测试、团队复核和个人反思。'),
('Explore it. Question it.','Sources and next steps',[URL,REPO,'Narain et al. 2024 · GIN CC BY 4.0 · DESeq2 · mouse GO · D3','AI-assisted code and documents; team review and understanding required.'],None,'全体：结束后Q&A。准备解释为什么NA不能当0、GO背景、阈值与富集固定、A15交换证据。')]
prs=Presentation();prs.slide_width=PI(13.333);prs.slide_height=PI(7.5)
pdf=canvas.Canvas(str(D/'Presentation.pdf'),pagesize=(960,540))
def tb(slide,x,y,w,h,text,size,color='#142c40',bold=False):
 shape=slide.shapes.add_textbox(PI(x),PI(y),PI(w),PI(h));tf=shape.text_frame;tf.word_wrap=True
 for j,line in enumerate(text.split('\n')):
  para=tf.paragraphs[0] if j==0 else tf.add_paragraph();para.text=line;para.font.size=PP(size);para.font.name='Aptos';para.font.bold=bold;para.font.color.rgb=RGBColor.from_string(color.lstrip('#'));para.space_after=PP(10)
 return shape
for i,(title,sub,bullets,figure,notes) in enumerate(slides):
 slide=prs.slides.add_slide(prs.slide_layouts[6]);slide.background.fill.solid();slide.background.fill.fore_color.rgb=RGBColor.from_string('F4F7FA')
 tb(slide,.6,.35,12,.4,'STRESS ATLAS / INFORMATION VISUALIZATION',12,'#007f79',True)
 tb(slide,.6,1,12,1,title,32,bold=True);tb(slide,.6,1.85,12,.65,sub,19,'#536b7c')
 text='\n'.join('• '+t for t in bullets)
 tb(slide,.6,2.65,5.5 if figure else 12,3.6,text,20 if figure else 23)
 if figure:
  iw,ih=PILImage.open(figure).size;s=min(6.4/iw,4.1/ih);slide.shapes.add_picture(str(figure),PI(6.5),PI(2.6),width=PI(iw*s),height=PI(ih*s))
 tb(slide,.6,7,11,.3,'Narain et al. (2024) public data · Reanalysis v1.0.0 · AI assistance disclosed',10,'#536b7c');tb(slide,12.1,7,.6,.3,f'{i+1:02}',10,'#536b7c')
 slide.notes_slide.notes_text_frame.text=notes
 pdf.setFillColor(colors.HexColor('#f4f7fa'));pdf.rect(0,0,960,540,fill=1,stroke=0)
 pdf.setFillColor(colors.HexColor('#007f79'));pdf.setFont('Helvetica-Bold',10);pdf.drawString(44,507,'STRESS ATLAS / INFORMATION VISUALIZATION')
 pdf.setFillColor(colors.HexColor('#142c40'));pdf.setFont('Helvetica-Bold',26);pdf.drawString(44,445,title.replace('—','-'))
 pdf.setFillColor(colors.HexColor('#536b7c'));pdf.setFont('Helvetica',15);pdf.drawString(44,406,sub)
 y=343;pdf.setFillColor(colors.HexColor('#142c40'));pdf.setFont('Helvetica',16)
 for bullet in bullets:
  for j,line in enumerate(textwrap.wrap(bullet,width=43 if figure else 92)):
   pdf.drawString(44,y,('• ' if j==0 else '  ')+line);y-=23
  y-=17
 if figure:
  iw,ih=PILImage.open(figure).size;s=min(455/iw,290/ih);pdf.drawImage(str(figure),470,350-ih*s,width=iw*s,height=ih*s,mask='auto')
 pdf.setFillColor(colors.HexColor('#536b7c'));pdf.setFont('Helvetica',8);pdf.drawString(44,22,'Reanalysis v1.0.0 | Sources and AI assistance disclosed in report');pdf.drawRightString(917,22,str(i+1));pdf.showPage()
prs.save(D/'Presentation.pptx');pdf.save()
notes='Stress Atlas 演示与答辩脚本\n建议总时长 8–10 分钟，按教师实际要求调整；三人均需发言。\n\n'
for i,(title,_,_,_,note) in enumerate(slides):notes+=f'{i+1}. {title}\n{note}\n\n'
notes+='提交前：成员修改个人反思、确认分工；不要声称已完成用户访谈或教师批准。\n演示备份：运行 start_explorer.cmd；Presentation.pdf 无需联网。\n'
(D/'Demo_Script_CN.txt').write_text(notes,encoding='utf-8')
print('Created report, proposal, editable Word files, 12-slide PPTX/PDF, figures and Chinese demo script.')
