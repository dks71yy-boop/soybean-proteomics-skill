---
name: soybean-proteomics
description: "监督并自动交付固定物种为 Glycine max 的质谱蛋白质组下游分析，覆盖只读输入审计、QC、差异丰度、ID 映射、GO/KEGG ORA 与 GSEA、PPI、植物生物学解释、XLSX/图件/中文报告和运行时审计。用于大豆 MaxQuant、DIA-NN、FragPipe、Spectronaut、Proteome Discoverer 或整理矩阵；坚持零本地安装，不用于其他物种，也不在 ANALYSIS PLAN 获确认前开始正式分析。"
---

# Soybean Proteomics

本 Skill 是固定物种为大豆的蛋白质组下游分析调度、执行与交付层。默认用户不编程：收到数据和 metadata 后，先做只读输入审计并提交 `ANALYSIS PLAN`；计划获明确确认后，自动完成当前环境可可靠执行的全流程，并交付表格、图件、中文报告、provenance 和运行时审计。准确性、可重复性和物种正确性优先于速度或结果数量。

## 不可变物种锁

<!-- HUMAN_DEFAULT_DENYLIST_START -->
NEVER assume Homo sapiens defaults.
<!-- HUMAN_DEFAULT_DENYLIST_END -->

```yaml
Organism:
  scientific_name: Glycine max
  common_name: soybean / 大豆
  ncbi_taxid: 3847
  kegg_code: gmx
```

每次 GO、KEGG、PPI、通路、功能注释或 ID mapping 前，显式记录工具、数据库、查询物种、版本或访问日期，并验证返回对象仍属于 `Glycine max`。KEGG 原生大豆分析必须使用 `gmx`；物种 Taxonomy ID 必须为 `3847`。

<!-- HUMAN_DEFAULT_DENYLIST_START -->
严禁无明确、经批准的同源分析理由而使用：`Homo sapiens`、`human`、`taxid 9606`、`hsa`、`org.Hs.eg.db`、`org.Mm.eg.db`、人类 Reactome 默认库、人类 STRING 默认参数或人类蛋白 accession 映射。
<!-- HUMAN_DEFAULT_DENYLIST_END -->

数据库不支持大豆时，停止该分支并报告覆盖限制；不得静默换物种或错误映射。只有用户明确确认后才可运行同源推断，结果写入 `ortholog_based_analysis/`，与大豆原生结果分开，并醒目标注“这是基于同源蛋白推断，不是 Glycine max 原生证据”。

## 零本地安装执行契约

不得要求用户在其 Windows 主机手工安装 Python、R、RStudio、Bioconductor、分析包或命令行工具，也不得为了本任务静默修改主机环境。按以下顺序选择执行环境：

1. 当前 Codex 已有执行能力、工具、MCP、已安装 Skill 或现成依赖。
2. 当前产品实际支持且用户授权的托管/云端执行或委派任务。
3. Codex 可控的沙箱、容器、临时或隔离环境；依赖只安装在该隔离环境，并记录版本。
4. 经验证、统计和生物学语义等价的实现；必须记录替代原因和验证证据。

若没有可执行环境，明确说明“当前任务缺少可用计算环境”，提出托管运行、上传或仅转移必要文件的方案；不得假装执行成功，也不得把本地安装教程转嫁给用户。云端任务不能直接读取本机 `D:\...` 等路径时，必须如实说明并请用户授权上传/传输必要文件。详细规则见 [references/execution-environments.md](references/execution-environments.md)。

## 范围与阶段门禁

本 Skill 的主范围是搜索与定量完成后的下游分析。若输入主要是 `.raw`、`.wiff`、`.d`、mzML 或尚未完成搜索的谱图，先说明这是上游流程，确认搜索引擎、参数、数据库、计算成本和输出后再做；不得自动发起大型搜索。

1. **检查阶段，可直接进行**：只读盘点输入、metadata、表头/数据字典、样本名、组别与重复、定量列、ID 类型、污染/decoy 标记、缺失编码；核验文件存在、可读、绝对路径或上传来源、大小及可行时的 SHA-256。可完成描述性 QC，不删样本、不改原件。
2. **计划阶段**：提交标题明确的 `ANALYSIS PLAN`，至少总结格式、样本数、设计、分组、生物学/技术重复、蛋白数量、缺失、对照方向、推荐模型、归一化、插补策略、ID 类型、数据库和预期交付物，并列出不确定项。
3. **正式分析阶段，必须等待确认**：只有计划获用户明确确认后，才运行归一化、插补、差异、映射、富集、PPI 和解释。若计划含推断出的样本桥接、组名、对照方向或批次关系，笼统的“继续”不构成确认；须逐项确认。
4. **自动交付阶段**：确认后不再要求用户逐条运行脚本；自动完成所有可行步骤，记录失败与替代路径，并生成最终 XLSX、图件、中文报告、完整 provenance 和 `RUNTIME ANALYSIS AUDIT REPORT`。

当前调用若仅要求建/升级 Skill、审计环境或检查输入，停在相应阶段；不得自行分析真实实验数据。

## 启动检查与数据诚信

先检查项目目录中的既有结果、脚本、notebook、metadata、提交表、样品交接表和 run manifest。既有结果仅作为证据来源，不自动视为权威；核对输入、物种、方法、版本和样本来源后再决定复用或重跑。不得把下游图名、脚本内标签或派生 `sample_group` 文件当作样本身份的独立证据。

原始数据始终只读，不复制覆盖、不移动、不改名。正式分析前记录 SHA-256；交付前在原路径仍可访问时重新计算并比较，输出 `INPUT INTEGRITY CHECK: PASS` 或 `FAILED`。若文件在云端不可访问，标记 `NOT_RUN` 并说明原因，不能伪装为通过。详细输入、QC、统计、映射、富集和解释规范见 [references/analysis-workflow.md](references/analysis-workflow.md)，正式分析前必须读取。

## 自动化工作流

计划确认后依次执行：输入审计、数据清洗、原始与归一化 QC、缺失机制评估、PCA/相关性/聚类、匹配设计的差异模型、火山图与热图、大豆 ID 映射、GO/KEGG ORA、基于全部可检验蛋白排序的 GSEA、可支持时的 PPI、候选蛋白、植物生物学解释和最终交付。任一分支失败不应抹去其他可靠结果；例如 GO 成功而 KEGG 失败时，仍交付 GO 与其余结果，并把 KEGG 标为失败或未运行。

不得捏造缺失结果、版本、映射率、富集条目、网络或图。每项结论区分观察、关联、富集、数据库注释、计算预测、假设和因果。最终目录、工作簿 sheet、图件和报告章节契约见 [references/deliverables.md](references/deliverables.md)。

## 工具、联网与隐私

每次项目重新盘点可用工具和版本，不假定上次环境仍存在。依赖和工具路由见 [references/tool-routing.md](references/tool-routing.md)，仅在实际选择执行路径时读取。

联网可用于经核实的官方数据库或可靠服务。只需 ID 时只提交 ID，不上传私有完整定量矩阵；任何向第三方提交大体量或敏感数据的操作必须先告知用户并遵守当前授权边界。数据库不可用时保留待查询 ID、参数、时间和失败日志，继续可独立完成的部分。

## 结果与可重复性

正式项目使用 `scripts/init_project.py` 新建结果树，默认拒绝覆盖已有目录。所有关键中间矩阵分开保存，包括清洗后、归一化后和仅在确有必要时的插补后矩阵。每次正式运行至少维护：

- `00_input_manifest/analysis_manifest.json`：输入、前置校验和、物种、执行环境、软件/包、数据库与注释版本、参数、阈值、随机种子、过滤、归一化、插补、统计、ID mapping、富集背景和交付能力。
- `logs/session_info.txt`：系统、运行时和包版本。
- `logs/run_log.jsonl`：时间、阶段、命令/函数、输入、输出、状态、警告和错误。
- `00_input_manifest/input_integrity_check.json`：交付前复核的输入大小、前后 SHA-256 和状态。

所有表保留明确列名、单位、变换状态和 provenance；ID 强制按文本处理，P 值和 FDR 保留有效精度。所有图导出高分辨率 PNG 与 PDF 或 SVG，带轴名、组名、样本标签、图例和可追溯绘图数据。

## 完成前审计

先运行静态 Skill 审计：

```powershell
python scripts/audit_skill.py .
```

正式结果交付前再运行实际结果审计：

```powershell
python scripts/runtime_audit.py <soybean_proteomics_results>
```

并按 [references/audit-checklist.md](references/audit-checklist.md) 核对证据。物种锁、样本映射、输入只读与校验和、未映射 ID 保留、统计方法、富集背景、版本 provenance 或必需交付物失败时，不得宣称完整成功；应交付可验证的部分并明确标为部分完成。
