#!/usr/bin/env python3
"""Audit immutable species, zero-install and delivery rules in this skill."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DENYLIST_START = "<!-- HUMAN_DEFAULT_DENYLIST_START -->"
DENYLIST_END = "<!-- HUMAN_DEFAULT_DENYLIST_END -->"
FORBIDDEN = [
    re.compile(r"Homo sapiens", re.I),
    re.compile(r"\bhuman\b", re.I),
    re.compile(r"\b9606\b"),
    re.compile(r"\bhsa\b", re.I),
    re.compile(r"org\.Hs\.eg\.db", re.I),
    re.compile(r"org\.Mm\.eg\.db", re.I),
]


def remove_denylist_blocks(text: str) -> str:
    pattern = re.compile(
        re.escape(DENYLIST_START) + r".*?" + re.escape(DENYLIST_END), re.S
    )
    return pattern.sub("", text)


def has_all(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    root = args.skill_dir.resolve()
    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        print(f"FAIL: missing {skill_path}")
        return 2

    files = [skill_path, *sorted((root / "references").glob("*.md"))]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    scrubbed = remove_denylist_blocks(combined)
    leaked = sorted({pattern.pattern for pattern in FORBIDDEN if pattern.search(scrubbed)})

    checks = {
        "A_species_locked": has_all(
            combined, ["scientific_name: Glycine max", "common_name: soybean / 大豆"]
        ),
        "B_D_no_forbidden_default_leak": not leaked,
        "E_kegg_gmx": "kegg_code: gmx" in combined,
        "F_taxid_3847": "ncbi_taxid: 3847" in combined,
        "G_unmapped_retained": has_all(
            combined, ["未映射", "一对多", "多对一", "original_id", "mapping_status"]
        ),
        "H_input_read_only_and_rehash": has_all(
            combined, ["原始数据始终只读", "SHA-256", "input_integrity_check.json"]
        ),
        "I_annotation_provenance": has_all(
            combined,
            ["assembly", "annotation release", "reference proteome", "FASTA", "GFF/GTF"],
        ),
        "J_no_naive_ttest": has_all(
            combined, ["Student's t-test 不是默认方法", "limma", "DEqMS", "MSstats"]
        ),
        "K_missingness_guard": has_all(
            combined, ["MCAR", "MAR", "MNAR", "不要默认“所有缺失填最小值”"]
        ),
        "L_multiple_testing": has_all(combined, ["Benjamini-Hochberg", "FDR"]),
        "M_enrichment_background": has_all(
            combined, ["background_definition", "实际可靠检测/定量"]
        ),
        "N_versions_recorded": has_all(combined, ["版本或访问日期", "session_info.txt"]),
        "plan_gate": has_all(combined, ["ANALYSIS PLAN", "必须等待确认"]),
        "zero_local_install": has_all(
            combined, ["零本地安装", "不得要求用户", "Windows 主机", "隔离环境"]
        ),
        "cloud_path_truthfulness": has_all(
            combined, ["不能直接读取本机", "授权上传/传输"]
        ),
        "full_delivery": has_all(
            combined,
            ["soybean_proteomics_results.xlsx", "soybean_proteomics_report_zh.docx", "RUNTIME ANALYSIS AUDIT REPORT"],
        ),
        "gsea_full_rank": has_all(
            combined, ["全部可检验蛋白", "moderated/model statistic", "ORA", "GSEA"]
        ),
        "runtime_audit_present": (root / "scripts" / "runtime_audit.py").is_file(),
    }
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}\t{name}")
    if leaked:
        print("Leaked forbidden patterns outside denylist blocks: " + ", ".join(leaked))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
