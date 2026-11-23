# 课堂代码与样本标签审阅

审阅日期：2026-11-23。此文档记录本地文件的实际检查结果；没有运行差异表达模型，也不把结构审计解释为生物学发现。原始数据及 Genomics 课堂文件保持不变。

## 课堂工作流

实际读取了 `Genomics/gb_RNAseq_student.Rmd` 全文、`run_rnaseq.R`、`README_RNAseq.md`，并检查 `GB_Assignment6_Mousegenes_Student.Rmd`。后者是基因长度和 GC 含量的描述统计作业，不能代替 RNA-seq 分析。目录中还包括 penguin、coronavirus 与 ChIP-seq 作业，它们不是本项目的 DEG 模型来源。

|步骤|课堂代码与定位（gb_RNAseq_student.Rmd 行号）|迁移到小鼠 stress RNA-seq|
|---|---|---|
|输入与样本对齐|73–95 行：实验设计、条件因子与 BAM 次序；142 行断言 count 列顺序|直接从真实整数 count 文件开始，不重做缺失 FASTQ/BAM 步骤；明确对齐 source sample、analysis sample、animal ID|
|reads 计数|135–145 行：summarizeOverlaps，Union、single-end、ignore.strand=TRUE；仅删除终端 transcript 后缀再 rowsum|已有 Ensembl 基因计数无需重复计数或按 symbol 合并|
|低表达过滤|154–159 行：逐组求 median count；任一组 median >=10 保留|对每个 region × ZT 的三 phenotype 分组应用同一规则，预先固定规则|
|模型|175–178 行：DESeqDataSetFromMatrix，design=~condition，DESeq 默认 size factors 与 dispersions|每个 region × ZT 单独拟合 ~phenotype，三个显式 pairwise contrasts；全覆盖为8个拟合、24个 contrast|
|效应方向|186 行：contrast=c('condition','treated','untreated')|contrast 第一个 phenotype 相对第二个 phenotype；正值=第一个组更高|
|阈值|186、200–201 行：alpha=.1；padj<.1 且 abs(log2FC)>1|课堂阈值与 handoff/paper 建议 .05/.5 不同；如默认采用后者，需明确记录是展示/研究阈值调整，不声称与课堂完全相同|
|结果|189、194–196 行：normalized counts、padj 排序，NA 最后|保留 NA；导出 JSON null；effect estimates 是原始未 shrink 的 DESeq2 LFC|
|QC/绘图|220–235 行 EnhancedVolcano，以 padj 作 y；243–262 行 VST、PCA、逐行标准化 heatmap|PCA 作为离线 QC；D3 图需与结果同源，不能用 raw p-value 图轴冒充 padj|
|ID 注释|274–282 行：ID 匹配 descriptions，去重后 match|使用 Ensembl 主键；小鼠符号和 GO 的版本、映射丢失率需记录，不能沿用拟南芥 org.At.tair.db|
|GO ORA|292–295 行：clusterProfiler::enrichGO，BP、BH、universe=filtered genes、p/q=.05|使用真实小鼠 BP annotations；保留实际可映射的背景；网络边只表示 membership|
|GSEA|315–329 行：全部 finite LFC 排序，gseGO、BH、固定随机种子|如实施则单独标注；InfoVis 核心 network 不应伪称 GSEA|

`run_rnaseq.R` 解析并执行同一 Rmd 的代码 chunks，`--render` 通过 rmarkdown 生成 HTML，`--check` 仅校验 setup/inputs。可借鉴此单一代码来源结构。课堂 README 指定本机 Rscript：`D:/R-4.6.1/bin/Rscript.exe`；该文件本次确认存在。课堂目录的 `.r-library` 可供读取已有包，但不向该目录写新分析结果。

横跨时间的表达图应独立在同一脑区全体纳入样本上估计共同 normalization，避免把每个 region-time 模型的任意尺度拼成折线。该图是 descriptive profile，不是 rhythmicity 或 time×phenotype interaction 检验。两个脑区属于同一动物；本项目分脑区模型不把这两个组织当两只动物，且不做未经配对处理的跨脑区检验。

## 标签证据与具体决定

下文数据路径以 `Visualization/narain_et_al-2024-translational_psychiatry/narain_et_al-2024-translational_psychiatry/` 为根目录。

标签定义来自 `01_data_raw/04_labelling_legend.json`。`01_data_raw/07_README_raw_data.md` 第7行称 `05_label_changes` 记录修正，但并未证明每个原始文件内容已改变。没有找到可执行作者 .R/.Rmd/.py/.sh 脚本；`00_counts_processed` 的 normalized、rlog 和 dds 文件均是63字节 pointer，不能用作模型对象。

### C01_E1：采用 ZT4，拒绝旧表头覆盖修正

`01_data_raw/05_label_changes.xlsx` sheet1 第2–3行明确记录 L2C→L1C、S2C→S1C，理由为 sacrifice timepoint 早于原标签。现存 count 文件确实为 `L1C-C01_E1.txt` 与 `S1C-C01_E1.txt`。因此源 ID 和分析 ID 此处相同，时间统一 ZT4。

两个作者 `timeseries_*_control.csv` 的第1行却仍用 `ZT10_C01-E1_1`。对完整35,364个基因比较，Hb 列按单一 scalar 可重建原始 L1C（最大相对误差4.97e-15，0个零模式差异）；SCN 列可重建 S1C（最大误差4.75e-7，0个零模式差异，CSV 精度较低）。即确为同一动物的数据，但旧表头时间未修正。不能直接把作者 timeseries header 用作重分析 metadata；也不能声称新结果必然复现作者具体时间分层结果。

### A15_A：原始内容没有交换，分析映射应交换一次

sheet1 第4–6行以临时名记录两脑区互换，原因为 PCA。仅凭文件名原本无法判定状态，本次用作者 normalized 列和原始整数 count 做全基因内容指纹比较解决该问题。对每一候选匹配，计算所有双方正值基因的 `median(raw / processed)`；以其重建 count，再检查全部35,364基因的相对误差及零值模式。

|作者目标列|实际匹配原始文件|raw/normalized scalar|最大相对重建误差|零模式差异|
|---|---|---:|---:|---:|
|timeseries_lhb_susceptible.csv: ZT4_A15-A_4|S1S-A15_A.txt|1.2065283928691595|4.81e-15|0|
|timeseries_scn_susceptible.csv: ZT4_A15-A_1|L1S-A15_A.txt|1.1061142632850955|4.85e-15|0|

反过来不交换的匹配，各有4,468个零值模式差异，median relative error 约0.21。这个证据远强于仅看 PCA 靠近哪一组，支持在导入时**仅对 analysis metadata 交换一次**：source `L1S-A15_A` → analysis `S1S-A15_A`（SCN）；source `S1S-A15_A` → analysis `L1S-A15_A`（Hb）。保持文件内容和 source ID 不变，animal ID 均为完整 `A15_A`。这复制作者已记录的纠正，并不自行认定新的样本交换。

复现命令（项目根目录）：`python scripts/verify_label_provenance.py`。完整8组匹配结果存于 `docs/metadata-content-matching.json`，脚本断言正确匹配误差<1e-6 且零模式一致，错误匹配不能通过。

### 排除样本与最终分组

sheet1 第7–9行明确排除 `L1R-E05_5`、`S1R-E05_5`、`L2S-E05_1`，理由为缺失对应脑区或很差的 clustering。作者 timeseries 确实没有这三个样本；SCN susceptible 列仍有 `ZT10_E05-1_1`。因此纳入 S2S-E05_1 是有出处的，不能机械删除单侧剩余样本。默认遵循这三个作者 exclusions；其他 outlier 不应仅因视觉分离而自动剔除。

排除后93个组织样本：Hb46、SCN47；47只 filename-derived 动物（46只双脑区、E05_1 仅 SCN）。E05_5 双侧均排除，故比原始48只少1只。动物 ID 取首个连字符后的完整后缀，不能丢掉下划线后段。

|ZT|Hb control/resilient/susceptible|SCN control/resilient/susceptible|
|---|---|---|
|4|5 / 3 / 4|5 / 3 / 4|
|10|3 / 4 / 3|3 / 4 / 4|
|16|4 / 4 / 4|4 / 4 / 4|
|22|4 / 4 / 4|4 / 4 / 4|

所有24个 region×time×phenotype cell 至少3个样本，支持完整24个 phenotype contrasts。样本 provenance 仍只证明与作者公开表和修正记录一致；没有实验室 mouse registry 可供独立确认动物身份，不能把命名推断升级为实验核验。

## 对实施脚本的只读复核

本次进一步读取 `scripts/prepare_inputs.py` 和 `analysis/run_analysis.R`。导入脚本按纠正 analysis ID 标记 count 列，source ID 单独保留；A15_A 两列互换 metadata 没有重复交换内容。R 在排除后按 metadata 次序取矩阵列，检查 within-stratum animal 唯一性与设计矩阵满秩。拟合模型使用8个 region×ZT 三组模型与24个显式 contrasts，且通过反向 contrast 检查 LFC 变号和 p-value 不变。没有发现明显的样本错配或 contrast 方向错误。

与课堂流程不同的已声明决定：

1. **Normalization scope**：课堂在过滤后的两组数据估计 size factors；本项目在每个脑区的全部时间点、全部纳入原始基因上用 DESeq2 median-ratio 方法估计，再固定供该脑区4个时间层模型及表达图共用。估计方法相同，scope 不同；不跨脑区比较绝对 normalized 水平。
2. **Three-group model**：每层三个 phenotype 同时估计 dispersion，再取两两 contrasts；不同于课堂两组实验。条件内动物独立，不做跨区域 pooled 检验。
3. **QC transform**：实施脚本 PCA 使用 log2(normalized count+1) 的500个高变基因，明确不是课堂 VST；仅用于描述性 QC，不能把 PCA 分离当成有效 DEG 检验。
4. **Display/DEG thresholds**：使用 paper/handoff 的 padj<.05 且 abs(LFC)>.5，替代课堂 .1/1。`results(alpha=.05)` 的 independent filtering 固定；浏览器更改可视阈值只重算已导出的统计摘要，不重新拟合，也不能恢复固定过滤产生的 NA。
5. **GO implementation**：主项目计划使用 Python hypergeometric ORA + BH，真实 org.Mm.eg.db 的 GOALL Biological Process annotations；这是课堂 ORA 思路的显式实现迁移，不声称运行 clusterProfiler。背景使用该 contrast finite-padj 且具有 BP mapping 的基因，而不是课堂全部 filtered genes，以使入选和背景具有相同被选机会。需同时导出这些背景大小、可测试 terms 范围及 mapped DEG 数；GOALL 含祖先 membership，应在注释源说明。
6. **Scope**：此次交付针对 Information Visualization；GSEA 不在四视图核心范围。不能声称完整覆盖了另外一门 GB 作业的所有实施步骤。

若网页允许阈值调整，预计算默认阈值的 GO 富集必须仍显示其原来的 .05/.5 条件；没有重算时不得暗示富集响应了新的阈值。annotation-only 的联动高亮不构成 enrichment 重新检验。

## 分析前后的必要校验

- 原始96文件、每文件46,603唯一基因、整数非负、共同顺序；排除后93样本；source→analysis 一一对应且只交换 A15_A。
- C01_E1 两个脑区均 ZT4；作者3个排除项确实不进入模型；完整 animal suffix 保留。
- 八个 region-time 模型设计矩阵满秩；三 phenotype 均有重复；24个 contrast 的 positive direction 明确。
- raw、normalized、model result 按 Ensembl join；随机基因逐组复核；NA 不转换为零；每个 contrast 有独立过滤/有效 padj 计数。
- GO 记录 annotation version、universe、eligible terms、BH 校正；无显著 enrichment 时明确 annotation-only，不能改称富集。
- QC 与保守 exclusions 先记录再拟合；本审阅没有声称任何基因具有真实应激效应。
