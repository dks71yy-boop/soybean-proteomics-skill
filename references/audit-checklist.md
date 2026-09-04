# SOYBEAN-PROTEOMICS 运行时项目审计

正式交付前运行 `python scripts/runtime_audit.py <results_root>`。审计必须扫描实际分析脚本、R/Python 代码、manifest、日志、ID mapping、GO/KEGG/STRING 查询记录、统计结果和最终工件，而不只检查 Skill 文案。每项输出 `PASS`、`FAIL` 或 `NOT_RUN` 以及证据路径；`NOT_RUN` 不能包装成完成。

## A-N 强制检查

- **A — Glycine max**：原生分析的 scientific name、注释和查询物种均为 `Glycine max`。

<!-- HUMAN_DEFAULT_DENYLIST_START -->
- **B — 9606/人类默认泄漏**：活动代码、配置、查询和日志不得把 `Homo sapiens`、`human` 或 `9606` 用作原生分析参数。
- **C — hsa**：KEGG 查询或 pathway 前缀不得使用 `hsa`。
- **D — org.Hs/org.Mm**：不得加载 `org.Hs.eg.db`、`org.Mm.eg.db` 或等价的错误物种注释默认。
<!-- HUMAN_DEFAULT_DENYLIST_END -->

- **E — gmx**：KEGG 原生查询、结果与 pathway ID 使用 `gmx`，并保留查询记录。
- **F — 3847**：PPI、STRING、映射或分类学查询使用 Taxonomy ID `3847`。
- **G — 未映射保留**：ID mapping 输出含 `original_id`、`mapping_status`、多重性，保留并计数未映射、一对多和多对一记录。
- **H — 输入完整性**：分析前后可访问输入的大小和 SHA-256 一致，原件未覆盖；输出 `00_input_manifest/input_integrity_check.json` 和明确的 `INPUT INTEGRITY CHECK` 状态。
- **I — provenance**：记录 assembly、annotation release、reference proteome、FASTA 来源/校验和、GFF/GTF 版本、UniProt/GO/KEGG/STRING 版本或访问日期；不静默混用 Glyma release。
- **J — 统计模型**：模型匹配实验设计，避免把普通 Student's t-test 当作小样本默认；batch、配对、重复测量和技术重复按设计处理。
- **K — 缺失处理**：先评估 MCAR/MAR/MNAR；避免无依据的全局最小值、半最小值或下移高斯插补。未插补是允许的，但须记录理由；敏感性结果不能按显著性挑选。
- **L — 多重校正**：完整检验集合使用 BH/FDR 或有理由的其他方法，记录方法和检验数。
- **M — 富集背景**：ORA 的 universe/background 有文件和定义，优先使用实验实际可靠检测/定量且同命名空间的集合；GO/KEGG 前景与背景使用一致的去重单位和 protein-group 规则。
- **N — 版本记录**：运行时、包、数据库、注释、基因集和外部服务版本或访问日期完整；等价实现记录来源与验证。

## 其他必检

- 样本与组别来自独立 metadata/manifest 或用户逐项确认，不来自列位置、脚本标签或下游派生文件。
- protein group 原值、代表蛋白与选择规则并存；所有下游 ID 可回溯到 `original_id`。
- 归一化前后 QC 齐全；异常样本未经批准未删除。
- GSEA 使用全部可检验蛋白，优先按 moderated/model statistic 排序；若使用有符号 `-log10(P)` 备选，已记录原因、方向和 ties。
- GO/KEGG ORA 与 GSEA 分目录；PPI 失败不被解释为没有互作。
- 必需工作簿、sheet、图件、中文 DOCX、可支持时 PDF、manifest、日志和审计报告齐全。
- 图件有高分辨率 PNG、PDF/SVG、绘图数据、标题、轴名、图例和图注。
- 报告区分观察、关联、富集、预测、假设与因果；失败分支在 README、报告和审计中一致标注。

## 状态判定

- 任一 A-N 硬性项 `FAIL`：总体 `FAILED`，不得宣称完整完成。
- 无 `FAIL` 但存在应运行而未运行的分支：总体 `PARTIAL_NOT_RUN`，交付可靠部分并解释。
- A-N、必需交付物与输入完整性均 `PASS`：总体 `PASS`。
