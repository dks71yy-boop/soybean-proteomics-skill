# 工具路由与环境要求

只在环境审计、方法选择或调用外部工具时读取。包名是候选能力，不是用户安装清单；以当前输入、官方文档和实际版本为准。必须同时遵守 [execution-environments.md](execution-environments.md) 的零本地安装规则。

## 1. 环境盘点顺序

1. 列出已安装 Skills，精确搜索蛋白组、植物基因组、富集、PPI、ID mapping、文档、表格与科研作图能力，并读取实际调用的 `SKILL.md`。
2. 枚举当前可调用 MCP/tool；名称不存在就视为不可用，不因能力索引出现而声称已安装。
3. 检查当前任务可访问的 Python、Rscript、包管理器、CLI 和库的真实路径/版本。PowerShell 的 `r` 可能只是 history alias，不能据此认定 R 已安装；必须确认 `Rscript` 或 `R.exe`。
4. 检查数据库或 API 是否可访问、是否支持 `Glycine max`，记录版本或访问日期。
5. 按“现成能力 → 托管/云端 → 沙箱/容器/临时隔离环境 → 经验证等价实现”的顺序选择执行路径。

缺失依赖只能由 Codex 安装到可控隔离环境，且须核对官方 README、包仓库或 Bioconductor 页面；不得修改用户 Windows 主机环境，不运行来源不明的一键脚本，不让用户手工搭环境。若无可靠环境，报告缺口、保留计划和已完成审计，不静默降级为错误模型。

## 2. 可复用能力边界

- 已安装且经审阅的通用蛋白组能力可承担格式、QC 和流程参考；不采纳其物种示例、固定生物学阈值或普通检验默认。
- 植物基因组能力可用于发现资源和证据分级；仍须逐项核对大豆覆盖和 release。
- GPTomics/bioSkills 类模块可作 `data-import`、`proteomics-qc`、`differential-abundance`、`protein-inference` 方法参考；简化的“取第一个 accession”不能覆盖 protein-group 保留规则。
- 论文级图形、工作簿、DOCX/PDF 可调用当前已安装的专用 Skill，但必须遵守本 Skill 的物种、数据和 provenance 契约。
- 任何外部能力的成功声明都要有实际工具返回、输出文件或日志证据。

## 3. 建议能力层级

### 核心表格与 QC

- Python：`pandas`、`numpy`、`scipy`、`statsmodels`、`scikit-learn`、`matplotlib`、`seaborn`、`pyarrow`、`openpyxl`。
- R：base R、`limma`；按设计再选 `DEqMS`、`MSstats`、`proDA`、`msqrob2`、`QFeatures`、`Spectra`、`PTXQC`、`MSstatsTMT`、`vsn`、`imputeLCMD`、`pcaMethods`。

### 原始/搜索输出与平台

- `pyOpenMS`/OpenMS、`msconvert`、ThermoRawFileParser 只在确实处理 mzML/vendor RAW 或仪器级 QC 时需要。
- MaxQuant、DIA-NN、FragPipe/MSFragger、Spectronaut、Proteome Discoverer 只在确认需要重新搜索/导出时需要；已有 protein matrix 时不列为硬依赖。
- 原始谱图的大型搜索属于上游分析，须先确认数据库、参数、资源、预计数据传输与输出。

### 注释、富集和网络

- 采用可追踪的大豆资源：NCBI Taxonomy/Protein/Gene、UniProt、Ensembl Plants、KEGG `gmx`；其他资源按调用时覆盖验证。
- GO/富集可用 `clusterProfiler` 配合版本化 `TERM2GENE`，或经验证支持大豆的 API/包；不要假设某个物种注释包存在或适用。
- GSEA 优先使用差异模型的全量可检验蛋白 statistic；实现须能保存基因集、排序向量、参数、seed 和 leading edge。
- PPI 仅在服务物种列表/接口确认支持 Taxonomy `3847` 后使用。
- ID mapping 优先官方 API、发布版映射表或项目参考 FASTA/GFF；版本和 many-to-many 关系进入 mapping ledger。

## 4. Windows、本地路径与托管执行

- 路径始终使用能处理空格和中文的 API/引号，记录绝对路径；脚本使用 `pathlib`。
- 不把 Bash 示例直接当作 PowerShell 命令；在隔离环境中按真实 shell 运行。
- 当前本地任务能读取 Windows 盘符时只读访问；托管或云端环境若不可见该盘符，必须说明并请求授权上传/传输最小必要文件，不能声称已经读取。
- Excel 输入通过 `.xlsx` 只读读取器处理，保留 sheet 名、公式/值语义以及零与空白的区别。

## 5. 最小环境与降级原则

纯输入审计可仅依赖安全的文本/表格读取能力。描述性 QC 需要基本数值与绘图库。小样本正式差异若缺少方差收缩或缺失建模能力，应尝试托管/隔离环境或经验证等价实现；仍不可用则停止该分支并报告，不能静默改用普通检验。富集或 PPI 服务不可用时保留已映射列表、查询参数和失败日志，不伪造结果；其余独立分支继续执行并部分交付。
