# 大豆蛋白质组分析规范

只在需要检查真实输入或执行正式分析时读取。所有步骤受 `SKILL.md` 的物种锁、零本地安装契约和阶段门禁约束。

## 1. 输入契约与实验设计

支持识别但不凭文件名独断：

- MaxQuant：`proteinGroups.txt`，必要时连同 `peptides.txt`、`evidence.txt` 和实验设计表。
- DIA-NN：`report.tsv`、`report.parquet`、protein/PG matrix；先确认版本、q-value 语境和定量字段。
- FragPipe：`combined_protein.tsv`、`protein.tsv` 及相关 peptide/PSM 表。
- Spectronaut、Proteome Discoverer 的 protein/peptide 导出表。
- 已整理的 CSV、TSV、XLSX。

最少建立以下数据字典：文件与 sheet、行列数、字段名、ID 层级、定量值语义与单位、缺失编码、零值语义、是否已 log/归一化/插补、污染/反向/decoy/site-only 标记、软件与版本。记录绝对路径或上传来源、可读性、大小和分析前 SHA-256；输入只读。

metadata 至少明确：`sample_id`、原始 run 名、实验组、对照方向、生物学重复、技术重复、batch、pair/subject（若有）、时间点/因子（若有）。样本列与 metadata 必须一一核对，并输出 unmatched、duplicate 和 many-to-one 清单。样本别名必须有独立的提交表、交接表、管号-run manifest 或用户逐项确认作为桥梁；无法证明时保持未决，不重命名输出。

若表头不足以区分定量列、样本身份、组别或重复，停止并询问用户。技术重复如何汇总必须写入计划；不得当作独立生物学重复提高样本量。

## 2. 清洗与 protein group

对 MaxQuant 等结果识别并记录 contaminants、reverse hits、decoys 和 only-identified-by-site。输出过滤前后计数、命中规则、被排除行的完整审计表。不要在原文件上删除。

将 `A;B;C` 等 protein group 作为原始分析单位保存在 `protein_group_original`。如映射或富集需要代表蛋白，另建 `representative_protein` 和 `representative_rule`；规则可基于 leading/majority/razor、unique peptide 支持、数据库注释或预先声明的确定性顺序，但不得无说明只取第一个。对歧义 group 可进行 group-preserving 或多映射敏感性分析。

零值是否代表缺失必须由来源软件/字段语义确认；确认后才转换为 NA。永远在 log 变换前检查非正值、单位和变换状态。

## 3. 正式差异前 QC

至少输出并解释：

1. 每个样本鉴定蛋白数和定量蛋白数。
2. 总缺失比例、每样本缺失率、每蛋白缺失模式和组别特异缺失。
3. 原始与 log2 强度分布、总信号与中位数。
4. 样本相关矩阵和组内重复相关；注明相关系数与 pairwise complete 规则。
5. PCA 和层次聚类，注明使用矩阵、缩放、距离与 linkage。
6. batch 与实验条件是否混杂。
7. potential outliers 的多证据摘要。
8. 每组 CV/重复变异；CV 在线性尺度计算，若从 log 值推导须说明公式。

先看未归一化数据，再看归一化后数据。异常样本只能标记为 `review_required`；不得自动删除。删除需要用户确认、预先定义的规则和带/不带该样本的敏感性分析。固定相关系数或缺失率只能作警报线，不能单独决定剔除。

## 4. 归一化与缺失值

归一化由数据层级、采集/标记方式、软件已执行步骤、总信号偏差、强度依赖和实验设计决定。评估 no additional normalization、median、quantile、VSN、robust/feature-level normalization 等候选；TMT、LFQ、DIA 和已归一化导出表不得套用同一默认方案。记录选法理由并分别保留 `filtered_matrix`、`normalized_matrix` 和仅在实际插补时的 `imputed_matrix`。

先结合采集方式、强度-缺失关系、组别模式和技术原因评估 MCAR、MAR、MNAR；采集方式是证据但不是自动判决。不要默认“所有缺失填最小值”。候选包括不插补、MinProb、QRILC、KNN、left-censored 或模型化分析。以显著性检验为目的时优先选择不会由人工压低组内方差制造显著性的模型；广泛或强度相关缺失优先评估 proDA、msqrob2 或 MSstats 的删失/feature-level 模型。若合理策略改变主要结论，报告 sensitivity analysis，不挑最显著的一种。

## 5. 差异丰度统计

先定义 contrast、实验单位、协变量、batch、配对/重复测量和交互项，再选模型：

- 小样本蛋白级矩阵：优先评估 `limma` 的 mean-variance trend 与 robust empirical Bayes。
- 有可靠 PSM/peptide count：评估 `DEqMS`，并明确计数列为何代表定量精度。
- peptide/feature-level、技术重复、嵌套或重复测量：评估 `MSstats` 或 `msqrob2`。
- 大量强度依赖缺失：评估 `proDA`、`msqrob2` 或适合的删失模型，不先插补再检验。
- 普通 Student's t-test 不是默认方法。只有设计简单、样本量足够、假设经检查且更合适模型不可用时，才可在计划中说明使用 Welch 检验及其局限。

batch 应进入模型；仅用于可视化的 batch-corrected 矩阵不得不加说明地输入显著性检验。多重检验默认 Benjamini-Hochberg FDR。未经用户决定，不擅自设置 fold-change cutoff；先返回完整统计结果并提出阈值选项。若要检验最小生物学效应，优先把效应阈值纳入统计假设，而不是事后双重筛选。

每个 contrast 至少输出：`protein_group_original`、`representative_protein`（若用）、`log2FC`、`FC`、`p_value`、`adjusted_p_value`/`FDR`、组均值或模型估计、缺失情况、观测数、所用方法、contrast、`significance_status`。保留未达到可检验条件的蛋白并给出状态和原因，不静默删除。

## 6. Glycine max ID mapping

先判断输入 ID 命名空间和参考蛋白组/基因组版本：UniProt accession、Glyma gene/protein ID、NCBI Protein/Gene、Ensembl Plants、gene symbol 或 protein group。Glyma 版本或组装版本之间不得静默互换。

映射表至少含：`original_id`、`protein_group_original`、`mapped_id`、`target_namespace`、`mapping_database`、`mapping_version_or_access_date`、`query_species`、`mapping_status`、`mapping_multiplicity`、`evidence`、`notes`。

报告总 ID、成功、未映射、一对多和多对一数量。未映射与歧义记录必须保留。所有下游表都能回溯到 `original_id`。映射数据库每次查询都限制并验证大豆物种；不得借用其他物种 accession 填空。

## 7. GO/KEGG ORA、GSEA 与 PPI

GO ORA 分别对 all differential、up、down 分析 BP、MF、CC。KEGG ORA 分别分析 all、up、down，原生分析 organism 固定为 `gmx`。默认背景为本实验实际可靠检测/定量且成功映射到同一命名空间的蛋白集合；若改用全基因组，写明理由并做敏感性分析。前景与背景去重单位、protein group 代表规则和 universe 必须一致。

GO 表至少含：`GO_ID`、`term`、`ontology`、`foreground_count`、`background_count`、`p_value`、`adjusted_p_value`、`proteins`、`background_definition`。KEGG 表至少含：`pathway_id`、`pathway_name`、`protein_count`、`p_value`、`FDR`、`associated_proteins`、`background_definition`。

GSEA 使用该 contrast 中**全部可检验蛋白**，而不是只用显著蛋白。排序指标优先为与差异模型一致的 moderated/model statistic；只有该统计量无法获得且已定义方向时，才可使用 `sign(log2FC) × -log10(p_value)`，并记录零值截断、ties 和不可检验蛋白。不得用 FDR 构造排序分数。记录基因集来源/版本、ID 空间、去重/多映射规则、集合大小上下限、置换策略、随机种子、NES、nominal P 和 FDR。GO 与 KEGG 的 ORA、GSEA 分目录保存，不能混为同一种证据。

PPI 请求前确认服务当前支持 `Glycine max` 和 taxonomy `3847`，记录版本/访问日期、输入数、映射数、网络覆盖率和置信度阈值。覆盖不足时报告 limitation，不把无网络解释为无生物学互作。同源 PPI 必须经过阶段门禁并写入独立目录。

## 8. 注释 provenance

在 ID mapping 或功能分析前锁定并记录：基因组 assembly、annotation release、reference proteome、FASTA 来源和 SHA-256、GFF/GTF 版本、UniProt release/访问日期、GO 来源/版本/访问日期、KEGG 访问日期，以及运行 PPI 时的 STRING 版本/访问日期。若输入 ID 与选定 release 不一致，先建立显式版本转换表并报告覆盖率；不得静默混用不同 Glyma release。

## 9. 植物生物学解释

只根据差异结果、效应方向、富集统计、定位/功能证据和已核实文献解释。可考虑光合作用、叶绿体、碳氮与氨基酸代谢、脂质、次生代谢、苯丙烷/黄酮/异黄酮、激素、ROS/氧化胁迫、植物-病原互作、非生物胁迫、核糖体、蛋白酶体、蛋白加工和转运，但不得因为常见就强行套用。

区分大豆直接实验/数据库证据、其他植物同源证据、计算注释和作者推断。若结论依赖同源证据，明确物种、ortholog 映射、同源类型、覆盖率和不确定性。关联或富集不等于机制或因果；把后续验证写成可检验假设。

## 10. 结果、图形与部分失败

完整结果目录、XLSX sheet、图件和 25 节中文报告按 [deliverables.md](deliverables.md) 执行。每图保存高分辨率 PNG 与 PDF 或 SVG，并保留绘图数据与脚本。图注说明数据层级、变换/归一化、样本数、统计口径、缺失处理和阈值。

某个外部分支失败时，记录错误、尝试可靠替代；仍失败则标为 `FAILED` 或 `NOT_RUN`，继续不依赖该分支的分析。不得根据期望补写富集条目、网络或候选蛋白。交付前重新计算可访问输入的 SHA-256，并运行 `scripts/runtime_audit.py`。
