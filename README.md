# Soybean Proteomics Skill

> A species-locked agent skill for downstream **soybean (*Glycine max*) proteomics** analysis, quality control, statistical planning, annotation/enrichment routing, biological interpretation, reproducible delivery, and runtime auditing.

中文：这是一个面向 **大豆（*Glycine max*）蛋白质组下游分析** 的 Agent Skill。它强调物种锁定、只读输入审计、分析计划确认、可重复性、ID 映射/GO/KEGG/PPI 的物种核验，以及最终结果与运行时审计。

## Scope

This repository is intentionally **soybean-specific**, not a generic plant-proteomics workflow.

Species lock:

- Scientific name: `Glycine max`
- NCBI Taxonomy ID: `3847`
- KEGG organism code: `gmx`

The skill is designed for downstream analysis after protein identification/quantification from workflows such as MaxQuant, DIA-NN, FragPipe, Spectronaut, Proteome Discoverer, or a curated protein abundance matrix.

It does **not** silently switch to human/mouse defaults and does not automatically run large raw-MS search workflows without a separate plan.

## What this repository contains

```text
soybean-proteomics-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── analysis-workflow.md
│   ├── audit-checklist.md
│   ├── deliverables.md
│   ├── execution-environments.md
│   └── tool-routing.md
├── scripts/
│   ├── audit_skill.py
│   ├── init_project.py
│   └── runtime_audit.py
├── .github/
│   └── workflows/
│       └── skill-audit.yml
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Important design principles

1. **Species correctness first** — soybean remains the native analysis target.
2. **Input files are read-only** — the workflow records file size and SHA-256 where possible.
3. **Plan gate before formal analysis** — input audit and `ANALYSIS PLAN` come before normalization, imputation, differential analysis, enrichment, PPI, and interpretation.
4. **No naive statistics by default** — the skill explicitly avoids blindly defaulting to Student's t-test or minimum-value imputation.
5. **Enrichment background is experiment-aware** — GO/KEGG background should reflect proteins reliably detected/quantified in the experiment.
6. **Zero-local-install preference** — use existing, managed, sandboxed, or isolated compute before asking the user to modify their host environment.
7. **Partial failure is explicit** — one failed branch (for example KEGG or PPI) must not be disguised as full success.
8. **Reproducible delivery** — manifests, logs, versions, database provenance, figures, tables, and runtime audit are part of the deliverable contract.

## Skill format

The repository follows the current Agent Skills structure used by ChatGPT/Codex:

- `SKILL.md` — required instructions and metadata
- `scripts/` — optional deterministic helper scripts
- `references/` — supporting workflow documentation
- `agents/openai.yaml` — optional UI/invocation metadata

Official documentation: <https://learn.chatgpt.com/docs/build-skills>

## Install for local Codex use

### User-scoped installation

Clone or copy the skill directory into your user skills folder:

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/dks71yy-boop/soybean-proteomics-skill.git ~/.agents/skills/soybean-proteomics
```

### Repository-scoped installation

For a project that should carry the skill with it:

```text
YOUR_PROJECT/
└── .agents/
    └── skills/
        └── soybean-proteomics/
            ├── SKILL.md
            ├── agents/
            ├── references/
            └── scripts/
```

Codex scans `.agents/skills` locations in the repository hierarchy. Restart Codex if a newly installed or updated skill does not appear.

## Basic validation

Static skill audit:

```bash
python scripts/audit_skill.py .
```

Create a new results tree without overwriting an existing project:

```bash
python scripts/init_project.py --help
```

Audit an actual analysis result directory:

```bash
python scripts/runtime_audit.py <soybean_proteomics_results>
```

## Recommended invocation

```text
Use $soybean-proteomics to read-only audit my soybean proteomics input and metadata.
First return INPUT AUDIT and ANALYSIS PLAN. After I explicitly confirm the plan,
complete the reliable downstream analysis and deliver tables, figures, a Chinese report,
provenance, and runtime audit without requiring local host installation.
```

## Repository status

This repository provides the **agent workflow specification, project initializer, static audit, and runtime audit layer**. It is not a single standalone Python package that independently implements every statistical, enrichment, and PPI method. The agent routes analysis to suitable available tools/environments while following the rules in this skill.

## Contributing and derivative development

Forks, pull requests, modifications, and derivative development are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

If you extend the workflow to rice, maize, Arabidopsis, or another organism, keep organism-specific identifiers, annotation databases, enrichment resources, and provenance explicit rather than silently replacing the soybean species lock.

## License

Released under the **MIT License**. You may use, copy, modify, merge, publish, distribute, sublicense, and create derivative works from this repository, including for commercial use, provided that the copyright and license notice are retained. See [`LICENSE`](LICENSE).

## Acknowledgment

If you publish or extend this workflow, keep organism/database provenance and the distinction between native soybean evidence and any orthology-based inference explicit.
