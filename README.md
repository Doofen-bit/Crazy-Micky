# Stress Atlas — Stress, across time

Information Visualization 期末项目。四个真实数据驱动的 D3 联动视图：context overview、volcano、temporal expression、gene–GO network。

- 网站：https://doofen-bit.github.io/Crazy-Micky/
- 仓库：https://github.com/Doofen-bit/Crazy-Micky
- 团队：Yixuan Du / yd2927；Yi Yao / yy5075；Jinyu Zheng / jz6539。
- 数据：[Narain et al. 2024](https://doi.org/10.1038/s41398-024-03100-w)，[GIN](https://doi.gin.g-node.org/10.12751/g-node.jj57l9/)，CC BY 4.0。
- 当前代码与文档为 AI-assisted implementation；成员需要理解、复核并修改个人反思后提交。没有代替团队完成教师讨论、真实用户访谈或课堂演讲。

## 直接查看

Windows 双击 `start_explorer.cmd`，打开 `http://localhost:8000`。需要 Python。也可以运行：

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

不要直接双击 `site/index.html`，浏览器会阻止 `file://` 下的 JSON 加载。D3 已放在本地，不依赖 CDN。网站不需要后端。

## 交付文件

| 路径 | 用途 |
|---|---|
| `docs/Final_Report.pdf` | 最多5页的英文项目报告；Reflection 包含待成员自行改写的明确标记 |
| `docs/Final_Report_Editable.docx` | 可编辑报告文本版 |
| `docs/Proposal_Updated.pdf` | 最多3页，按4.1–4.7顺序，含仓库与网站地址 |
| `docs/Proposal_Updated_Editable.docx` | 可编辑 proposal 文本版 |
| `docs/Presentation.pptx` / `.pdf` | 12页演示，PPTX 含中文 speaker notes |
| `docs/Demo_Script_CN.txt` | 三人演示路径、分工建议和答辩提醒 |
| `analysis/Stress_RNAseq_Workbench.Rmd` / `.html` | 可解释、可重运行的统计 workbench |
| `docs/source-code-review.md` | 实际课堂代码逐步对应与元数据证据 |
| `docs/figures/` | 由本项目结果生成的 PNG/PDF 图 |
| `docs/dashboard-*.png`, `docs/view-*.png` | 实际网页截图 |
| `audit/` | 输入、模型、导出、浏览器、部署验证记录 |
| `results/contrasts/` | 完整24个 DESeq2 比较 CSV |
| `site/` | GitHub Pages 静态网站，含全部按需数据 |

## 分析约定

96份原始 counts → 93份纳入组织样本、47只动物。排除作者列出的 L1R-E05_5、S1R-E05_5、L2S-E05_1。A15_A 仅在 analysis ID/region 映射交换一次；全基因比例验证见 `docs/metadata-content-matching.json`。C01_E1 使用原始已纠正 ZT4。原始数据、ZIP 和 Genomics 课堂文件没有被修改。

每个 region×ZT 内任一 phenotype median count≥10 的基因保留。DESeq2 median-ratio size factors 在每个脑区全部纳入样本上估计并固定用于四个时间模型；8个 `~phenotype` 三组模型，24个显式 contrasts。正 LFC 表示第一个组更高，未经 shrinkage。独立过滤固定 alpha=.05，保留 NA。默认展示 p-adj<.05、|log2FC|>.5，阈值可调整，但不会重新拟合模型。

GO 使用实际 org.Mm.eg.db 3.23.0、GO.db 3.23.1 的 GOALL BP。Python 实现 hypergeometric / BH（并非声称调用 clusterProfiler）。背景为该对比 finite-padj 且有BP注释的基因，前景为默认阈值DEG，term背景大小10–500，所有合格term进入BH。GO富集固定默认阈值；没有显著富集时显示 annotation-only。边表示 membership，非因果。组均值的时间连线不代表同一动物。

这是 Information Visualization 交付，参考课堂方法；不声称已完成另一门 GB 作业的所有要求，亦非论文方法的精确复现。

## 重现

Python 3.11+（本机3.14），R 4.6.1 / Bioconductor 3.23（本次实际环境）。依赖版本见 `requirements.txt`、`results/session_info.txt`。

原始数据放在项目同级路径：
`../narain_et_al-2024-translational_psychiatry/narain_et_al-2024-translational_psychiatry/`。
原ZIP放在同级 `../narain_et_al-2024-translational_psychiatry-master.zip`。
ZIP SHA256：`edefea6fc5042d0eb377a05c32585d665fd0b9001a014901d795b48f9df75495`。

```powershell
python -m pip install -r requirements.txt
& 'D:\R-4.6.1\bin\Rscript.exe' scripts/setup.R
python scripts/verify_label_provenance.py
python scripts/prepare_inputs.py
& 'D:\R-4.6.1\bin\Rscript.exe' analysis/run_analysis.R
python scripts/export_site.py
python scripts/validate_results.py
& 'D:\R-4.6.1\bin\Rscript.exe' scripts/render_workbench.R
```

Windows 启动 R 时本机 locale 有非致命警告；完整统计运行见 session 与输出校验。`scripts/setup.R` 只补缺包，不自动更新已有包。若Rscript在PATH上可替换绝对路径。大体积 raw/count/GO 中间文件未提交 Git；可按以上步骤重建，静态网页不需要它们。

浏览器测试及报告生成（先在另一终端启动上面的 HTTP 服务）：

```powershell
python -m playwright install chromium
python scripts/browser_qa.py
python scripts/build_deliverables.py
```

报告PDF由 ReportLab生成，可编辑Word为同源文本版。演示PPTX为可编辑文本/图像，PDF作为离线备份。

## 发布

`.github/workflows/pages.yml` 将 `site/` 部署到 GitHub Pages。仓库 Settings → Pages → Build and deployment 选择 GitHub Actions。推送 main 后自动部署。以 `audit/deployment.json` 和 Actions 返回值为实际部署证据，不能把配置文件本身当成发布成功。

## 评估与待团队完成

自动检查覆盖原始ID、排除、模型rank、反向contrast、全部标准化值、24个过滤/NA/export、GO p-value/BH、24个页面context和联动/空状态；1366/1440/390px响应式检查。未进行真人用户研究，也不代替科学同行复核。

提交前：团队讨论并修订模型解释；各成员改写个人反思和实际分工；按课程要求完成教师讨论与课堂演示；再次检查网站可公开访问。参见 `AI_USAGE.md` 和 `DECISIONS.md`。

## 外部代码与署名

D3.js 7.9.0 (ISC)，本地vendor文件保留版权说明，完整license在 `site/vendor/D3-LICENSE.txt`。没有使用第三方网页模板或论文图片。数据CC BY4.0，模型引用Love/Huber/Anders (2014)。Codex帮助审计、编码、测试与起草，记录于AI_USAGE.md。
