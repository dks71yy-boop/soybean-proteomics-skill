# 最终交付契约

只在计划编制、正式执行和交付审计时读取。目录名和必需工件用于机器审计；不要随意改名。

## 1. 结果目录

```text
soybean_proteomics_results/
├── 00_input_manifest/
├── 01_data_audit/
├── 02_data_cleaning/
├── 03_qc/
│   ├── protein_counts/
│   ├── missingness/
│   ├── intensity_distribution/
│   └── replicate_qc/
├── 04_normalization/
├── 05_pca_correlation/
│   ├── PCA/
│   ├── correlation_heatmap/
│   └── clustering/
├── 06_differential_proteins/
│   ├── all_results/
│   ├── significant_results/
│   ├── upregulated/
│   └── downregulated/
├── 07_volcano_heatmap/
├── 08_id_mapping/
├── 09_go_enrichment/
│   ├── ORA/
│   └── GSEA/
├── 10_kegg_enrichment/
│   ├── ORA/
│   └── GSEA/
├── 11_ppi/
├── 12_candidate_proteins/
├── 13_biological_interpretation/
├── 14_final_tables/
├── 15_final_figures/
├── 16_final_report/
└── logs/
```

## 2. 最终工作簿

生成 `14_final_tables/soybean_proteomics_results.xlsx`，至少包含以下 sheet，名称保持一致：

`README`、`Sample_Metadata`、`QC_Summary`、`All_Proteins`、`Differential_All`、`Differential_Significant`、`Upregulated`、`Downregulated`、`ID_Mapping`、`GO_BP`、`GO_CC`、`GO_MF`、`GO_Up`、`GO_Down`、`KEGG_All`、`KEGG_Up`、`KEGG_Down`、`GSEA`、`Candidate_Proteins`、`Analysis_Parameters`。

规则：

- accession、Glyma、GO、KEGG 和原始 ID 按文本写入，防止科学计数法、截断或日期转换。
- P 值、FDR、效应量与强度写为真实数值，保留足够有效位；显示格式不能替代底层精度。
- 每个统计表明确 contrast、分子方向、检验方法、样本/观测数、缺失状态、显著性定义与不可检验原因。
- 无结果的已运行分支保留带状态与原因的 sheet；失败或未运行不得伪造空的“成功”表。
- README 汇总输入、物种、对照方向、阶段状态、部分失败、关键文件和使用说明；Analysis_Parameters 汇总全部参数与版本。

## 3. 图件

至少生成：PCA、样本相关性热图、层次聚类、缺失概览、强度分布、火山图、差异蛋白热图、GO BP/CC/MF、KEGG、适用时 GSEA、适用且数据库支持时 PPI。

每图在对应分析目录保留绘图数据与脚本，并把定稿复制/汇总到 `15_final_figures/`。导出高分辨率 PNG（投稿级；默认不低于 300 dpi，像素尺寸与版面匹配）以及 PDF 或 SVG。图名、轴、图例、样本数、变换/归一化、统计口径和阈值须可理解；无数据不画占位图。

## 4. 中文报告

生成 `16_final_report/soybean_proteomics_report_zh.docx`；环境支持可靠渲染时同时生成 PDF。报告至少按以下 25 个编号章节组织：

1. 项目概览
2. 研究问题与比较方向
3. 输入文件与完整性
4. 样本 metadata 与实验设计
5. 数据格式和定量层级
6. 数据清洗规则
7. 蛋白/蛋白组推断规则
8. 缺失值概况与机制评估
9. 归一化方法与依据
10. 样本蛋白计数 QC
11. 强度分布 QC
12. 重复一致性与 CV
13. 样本相关性
14. PCA 与聚类
15. 异常样本与敏感性分析
16. 差异丰度模型与多重校正
17. 差异蛋白总体结果
18. 上调与下调结果
19. Glycine max ID 映射与覆盖率
20. GO ORA 结果
21. KEGG ORA 结果
22. GSEA 结果
23. PPI 与候选蛋白
24. 植物生物学解释、局限与可检验假设
25. 结论、交付清单、provenance 与运行时审计

图按出现顺序编号，含中文标题、图注和一段面向研究者的解释。措辞必须严格区分：数据观察、统计关联、过度代表/富集、数据库注释、网络预测、工作假设和因果结论。没有干预或因果设计时，不使用“导致”“驱动”“证明机制”等因果措辞。

## 5. 注释与数据库 provenance

`analysis_manifest.json` 与报告须记录：基因组 assembly、annotation release、reference proteome、FASTA 来源与 SHA-256、GFF/GTF 版本、UniProt release/访问日期、KEGG 访问日期、GO 来源/版本/访问日期、STRING 版本/访问日期（若运行）。不得把不同 Glyma release 的 ID、FASTA 和注释静默混用；转换必须有版本化映射表和覆盖统计。

## 6. 完成状态

完整成功必须同时具备：最终 XLSX、必需图件、中文 DOCX（及环境支持时 PDF）、输入完整性检查、注释/数据库 provenance、运行日志和 `RUNTIME ANALYSIS AUDIT REPORT`。某个外部数据库分支失败时可以部分交付，但 README、报告和审计必须一致标为部分完成，并列出已完成和未完成项。
