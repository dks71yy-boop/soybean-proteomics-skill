#!/usr/bin/env python3
"""Audit actual soybean proteomics results and emit an evidence-backed report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


TEXT_SUFFIXES = {".py", ".r", ".json", ".jsonl", ".yaml", ".yml", ".txt", ".tsv", ".csv"}
MAX_SCAN_BYTES = 20 * 1024 * 1024
REQUIRED_DIRS = [
    "00_input_manifest",
    "01_data_audit",
    "02_data_cleaning",
    "03_qc/protein_counts",
    "03_qc/missingness",
    "03_qc/intensity_distribution",
    "03_qc/replicate_qc",
    "04_normalization",
    "05_pca_correlation/PCA",
    "05_pca_correlation/correlation_heatmap",
    "05_pca_correlation/clustering",
    "06_differential_proteins/all_results",
    "06_differential_proteins/significant_results",
    "06_differential_proteins/upregulated",
    "06_differential_proteins/downregulated",
    "07_volcano_heatmap",
    "08_id_mapping",
    "09_go_enrichment/ORA",
    "09_go_enrichment/GSEA",
    "10_kegg_enrichment/ORA",
    "10_kegg_enrichment/GSEA",
    "11_ppi",
    "12_candidate_proteins",
    "13_biological_interpretation",
    "14_final_tables",
    "15_final_figures",
    "16_final_report",
    "logs",
]
REQUIRED_SHEETS = [
    "README",
    "Sample_Metadata",
    "QC_Summary",
    "All_Proteins",
    "Differential_All",
    "Differential_Significant",
    "Upregulated",
    "Downregulated",
    "ID_Mapping",
    "GO_BP",
    "GO_CC",
    "GO_MF",
    "GO_Up",
    "GO_Down",
    "KEGG_All",
    "KEGG_Up",
    "KEGG_Down",
    "GSEA",
    "Candidate_Proteins",
    "Analysis_Parameters",
]
FORBIDDEN = {
    "B": [re.compile(r"Homo sapiens", re.I), re.compile(r"\bhuman\b", re.I), re.compile(r"\b9606\b")],
    "C": [re.compile(r"\bhsa\b", re.I)],
    "D": [re.compile(r"org\.Hs\.eg\.db", re.I), re.compile(r"org\.Mm\.eg\.db", re.I)],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(root: Path) -> tuple[dict[str, Any], Path | None]:
    candidates = [
        root / "00_input_manifest" / "analysis_manifest.json",
        root / "logs" / "analysis_manifest.json",
        root / "analysis_manifest.json",
    ]
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8-sig")), path
    return {}, None


def read_text(path: Path) -> str:
    if path.stat().st_size > MAX_SCAN_BYTES:
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def workbook_strings(path: Path) -> str:
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name == "xl/sharedStrings.xml" or name.startswith("xl/worksheets/sheet"):
                    data = archive.read(name)
                    if len(data) <= MAX_SCAN_BYTES:
                        chunks.append(data.decode("utf-8", errors="replace"))
    except (OSError, zipfile.BadZipFile):
        return ""
    return "\n".join(chunks)


def workbook_sheets(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("xl/workbook.xml")
        root = ElementTree.fromstring(xml)
        namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        return [node.attrib.get("name", "") for node in root.findall(".//m:sheet", namespace)]
    except (OSError, KeyError, zipfile.BadZipFile, ElementTree.ParseError):
        return []


def is_excluded(path: Path) -> bool:
    lower_parts = [part.lower() for part in path.parts]
    if "ortholog_based_analysis" in lower_parts:
        return True
    return path.name.lower() in {
        "runtime_analysis_audit_report.md",
        "runtime_audit.json",
        "input_integrity_check.json",
    }


def scan_artifacts(root: Path) -> tuple[list[tuple[Path, str]], list[str]]:
    texts: list[tuple[Path, str]] = []
    skipped: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or is_excluded(path):
            continue
        try:
            if path.suffix.lower() in TEXT_SUFFIXES:
                if path.stat().st_size > MAX_SCAN_BYTES:
                    skipped.append(str(path.relative_to(root)))
                    continue
                texts.append((path, read_text(path)))
            elif path.suffix.lower() == ".xlsx":
                texts.append((path, workbook_strings(path)))
        except OSError as exc:
            skipped.append(f"{path.relative_to(root)} ({exc})")
    return texts, skipped


def compact_hits(root: Path, texts: list[tuple[Path, str]], patterns: list[re.Pattern[str]]) -> list[str]:
    hits: list[str] = []
    for path, text in texts:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{path.relative_to(root)}:{line} [{pattern.pattern}]")
                break
    return hits[:30]


def branch_state(manifest: dict[str, Any], name: str) -> str:
    value = manifest.get("analysis_branches", {}).get(name, "UNKNOWN")
    return str(value).upper()


def branch_succeeded(manifest: dict[str, Any], name: str) -> bool:
    return branch_state(manifest, name) in {"PASS", "PASSED", "SUCCESS", "COMPLETE", "COMPLETED"}


def branch_not_run_or_failed(manifest: dict[str, Any], name: str) -> bool:
    return branch_state(manifest, name) in {"NOT_RUN", "FAILED", "SKIPPED", "UNAVAILABLE"}


def is_formal_delivery(manifest: dict[str, Any], root: Path) -> bool:
    states = {
        str(manifest.get("analysis_status", "")).upper(),
        str(manifest.get("gate", {}).get("status", "")).upper(),
        str(manifest.get("deliverables", {}).get("status", "")).upper(),
    }
    terminal = {"COMPLETE", "COMPLETED", "READY_FOR_DELIVERY", "DELIVERED", "PARTIAL_COMPLETE"}
    return bool(states & terminal) or (root / "14_final_tables" / "soybean_proteomics_results.xlsx").is_file()


def has_version_record(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        keys = " ".join(str(key).lower() for key in value)
        if any(token in keys for token in ("version", "release", "access_date", "accessed")):
            return any(has_version_record(item) for item in value.values())
        return all(has_version_record(item) for item in value.values()) if value else False
    if isinstance(value, list):
        return bool(value) and all(has_version_record(item) for item in value)
    return value is not None


def find_mapping_files(root: Path) -> list[Path]:
    base = root / "08_id_mapping"
    if not base.exists():
        return []
    return [path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in {".tsv", ".csv", ".txt", ".xlsx"}]


def mapping_has_required_fields(path: Path) -> bool:
    if path.suffix.lower() == ".xlsx":
        text = workbook_strings(path).lower()
    else:
        text = read_text(path).lower()
    return all(term in text for term in ("original_id", "mapping_status", "mapping_multiplicity"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_root", type=Path)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    root = args.results_root.resolve()
    if not root.is_dir():
        print(f"FAIL: result root not found: {root}")
        return 2
    manifest, manifest_path = load_manifest(root)
    formal = is_formal_delivery(manifest, root)
    results: list[dict[str, str]] = []

    def add(code: str, title: str, status: str, evidence: str) -> None:
        results.append({"code": code, "title": title, "status": status, "evidence": evidence})

    manifest_ref = str(manifest_path.relative_to(root)) if manifest_path else "未找到 analysis_manifest.json"
    organism = manifest.get("organism", {})
    if organism.get("scientific_name") == "Glycine max":
        add("A", "Glycine max 物种锁", "PASS", manifest_ref)
    else:
        add("A", "Glycine max 物种锁", "FAIL", f"{manifest_ref}; scientific_name={organism.get('scientific_name')!r}")

    texts, skipped = scan_artifacts(root)
    for code, title in (("B", "错误分类学默认泄漏"), ("C", "错误 KEGG 前缀泄漏"), ("D", "错误物种注释包泄漏")):
        hits = compact_hits(root, texts, FORBIDDEN[code])
        add(code, title, "FAIL" if hits else "PASS", "; ".join(hits) if hits else "活动代码、配置、日志、查询及可读结果未检出禁用参数")

    kegg_files = [
        (path, text)
        for path, text in texts
        if "kegg" in str(path.relative_to(root)).lower() or "kegg" in text.lower()
    ]
    kegg_ok = organism.get("kegg_code") == "gmx"
    if kegg_files and not any(re.search(r"\bgmx\b", text, re.I) for _, text in kegg_files):
        kegg_ok = False
    add("E", "KEGG gmx", "PASS" if kegg_ok else "FAIL", f"manifest kegg_code={organism.get('kegg_code')!r}; KEGG 工件数={len(kegg_files)}")

    tax_files = [
        (path, text)
        for path, text in texts
        if any(token in str(path.relative_to(root)).lower() for token in ("ppi", "string", "mapping", "query"))
        or any(token in text.lower() for token in ("taxonomy", "string", "ncbi_taxid"))
    ]
    tax_ok = organism.get("ncbi_taxid") == 3847
    if tax_files and branch_succeeded(manifest, "ppi") and not any(re.search(r"\b3847\b", text) for _, text in tax_files):
        tax_ok = False
    add("F", "Taxonomy 3847", "PASS" if tax_ok else "FAIL", f"manifest ncbi_taxid={organism.get('ncbi_taxid')!r}; 相关工件数={len(tax_files)}")

    mapping_files = find_mapping_files(root)
    if mapping_files:
        valid_mapping = [path for path in mapping_files if mapping_has_required_fields(path)]
        status = "PASS" if valid_mapping else "FAIL"
        evidence = ", ".join(str(path.relative_to(root)) for path in (valid_mapping or mapping_files)[:10])
    else:
        status = "FAIL" if formal and branch_succeeded(manifest, "id_mapping") else "NOT_RUN"
        evidence = "未找到可审计的 ID mapping 输出"
    add("G", "未映射与多重映射保留", status, evidence)

    integrity_records: list[dict[str, Any]] = []
    integrity_states: list[str] = []
    for record in manifest.get("input_files", []):
        source = Path(str(record.get("source_path", "")))
        item: dict[str, Any] = {
            "source_path": str(source),
            "size_bytes_before": record.get("size_bytes_before", record.get("size_bytes")),
            "sha256_before": record.get("sha256_before", record.get("sha256")),
            "checked_utc": datetime.now(timezone.utc).isoformat(),
        }
        before = item["sha256_before"]
        if not before:
            item["status"] = "NOT_RUN"
            item["reason"] = "分析前校验和缺失或被明确跳过"
        elif not source.is_file():
            item["status"] = "NOT_RUN"
            item["reason"] = "当前执行环境无法访问原输入路径"
        else:
            item["size_bytes_after"] = source.stat().st_size
            item["sha256_after"] = sha256(source)
            same_size = item["size_bytes_before"] in (None, item["size_bytes_after"])
            item["status"] = "PASS" if same_size and item["sha256_after"] == before else "FAILED"
        integrity_records.append(item)
        integrity_states.append(str(item["status"]))

    if not integrity_records:
        integrity_status = "NOT_RUN"
    elif "FAILED" in integrity_states:
        integrity_status = "FAILED"
    elif "NOT_RUN" in integrity_states:
        integrity_status = "NOT_RUN"
    else:
        integrity_status = "PASS"
    integrity_payload = {
        "title": "INPUT INTEGRITY CHECK",
        "status": integrity_status,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "files": integrity_records,
    }
    integrity_path = root / "00_input_manifest" / "input_integrity_check.json"
    integrity_path.parent.mkdir(parents=True, exist_ok=True)
    integrity_path.write_text(json.dumps(integrity_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    h_status = "FAIL" if integrity_status == "FAILED" else integrity_status
    add("H", "输入只读与前后校验", h_status, f"00_input_manifest/input_integrity_check.json; INPUT INTEGRITY CHECK: {integrity_status}")

    provenance = manifest.get("annotation_provenance", {})
    required_provenance = [
        "genome_assembly",
        "annotation_release",
        "reference_proteome",
        "fasta_source",
        "fasta_sha256",
        "gff_gtf_version",
        "uniprot_release_or_access_date",
        "go_source_version_or_access_date",
        "kegg_access_date",
    ]
    if branch_succeeded(manifest, "ppi"):
        required_provenance.append("string_version_or_access_date")
    missing_provenance = [key for key in required_provenance if not provenance.get(key)]
    if missing_provenance:
        status = "FAIL" if formal else "NOT_RUN"
        evidence = "缺失: " + ", ".join(missing_provenance)
    else:
        status, evidence = "PASS", manifest_ref
    add("I", "注释与数据库 provenance", status, evidence)

    statistical = manifest.get("statistical_method")
    if statistical is None:
        add("J", "设计匹配的差异模型", "FAIL" if formal and branch_succeeded(manifest, "differential") else "NOT_RUN", "statistical_method 未记录")
    else:
        stat_text = json.dumps(statistical, ensure_ascii=False).lower()
        naive = bool(re.search(r"student'?s?\s+t[- ]?test|equal[_ -]?var(?:iance)?\s*[:=]\s*true", stat_text))
        add("J", "设计匹配的差异模型", "FAIL" if naive else "PASS", stat_text[:500])

    imputation = manifest.get("imputation")
    if imputation is None:
        add("K", "缺失机制与插补保护", "FAIL" if formal and branch_succeeded(manifest, "differential") else "NOT_RUN", "imputation/不插补理由未记录")
    else:
        imp_text = json.dumps(imputation, ensure_ascii=False).lower()
        naive = bool(re.search(r"global[_ -]?min|half[_ -]?min|minimum[_ -]?value|downshifted gaussian", imp_text)) and "sensitivity" not in imp_text
        assessed = bool(manifest.get("missingness_assessment"))
        add("K", "缺失机制与插补保护", "FAIL" if naive or not assessed else "PASS", f"missingness_assessment={assessed}; {imp_text[:400]}")

    multiple = manifest.get("multiple_testing")
    if multiple is None:
        add("L", "多重检验校正", "FAIL" if formal and branch_succeeded(manifest, "differential") else "NOT_RUN", "multiple_testing 未记录")
    else:
        mt_text = json.dumps(multiple, ensure_ascii=False).lower()
        ok = any(token in mt_text for token in ("benjamini", "bh", "fdr", "q-value", "qvalue"))
        add("L", "多重检验校正", "PASS" if ok else "FAIL", mt_text[:400])

    enrichment = manifest.get("enrichment", {})
    enrichment_ran = any(branch_succeeded(manifest, name) for name in ("go", "kegg", "gsea"))
    background = enrichment.get("background_definition") if isinstance(enrichment, dict) else None
    if background:
        add("M", "富集背景", "PASS", json.dumps(background, ensure_ascii=False)[:500])
    else:
        add("M", "富集背景", "FAIL" if enrichment_ran else "NOT_RUN", "background_definition 未记录")

    software = manifest.get("software", {})
    databases = manifest.get("databases", {})
    versions_ok = bool(software) and bool(databases) and has_version_record(software) and has_version_record(databases)
    if versions_ok:
        add("N", "软件与数据库版本", "PASS", f"software={len(software)}; databases={len(databases)}")
    else:
        add("N", "软件与数据库版本", "FAIL" if formal else "NOT_RUN", f"software={len(software) if isinstance(software, dict) else 0}; databases={len(databases) if isinstance(databases, dict) else 0}")

    missing_dirs = [name for name in REQUIRED_DIRS if not (root / name).is_dir()]
    add("TREE", "标准结果目录", "FAIL" if missing_dirs else "PASS", "缺失: " + ", ".join(missing_dirs) if missing_dirs else "全部标准目录存在")

    workbook = root / "14_final_tables" / "soybean_proteomics_results.xlsx"
    if workbook.is_file():
        sheets = workbook_sheets(workbook)
        missing_sheets = [name for name in REQUIRED_SHEETS if name not in sheets]
        add("XLSX", "最终工作簿与 sheet", "FAIL" if missing_sheets else "PASS", "缺失 sheet: " + ", ".join(missing_sheets) if missing_sheets else str(workbook.relative_to(root)))
    else:
        add("XLSX", "最终工作簿与 sheet", "FAIL" if formal else "NOT_RUN", "未找到 14_final_tables/soybean_proteomics_results.xlsx")

    figure_files = [path for path in (root / "15_final_figures").glob("*") if path.is_file()] if (root / "15_final_figures").is_dir() else []
    figure_text = [str(path.relative_to(root)).lower() for path in figure_files]
    figure_specs = {
        "PCA": ("qc", [r"pca"]),
        "correlation": ("qc", [r"correlation|corr"]),
        "clustering": ("qc", [r"cluster"]),
        "missingness": ("qc", [r"missing"]),
        "intensity": ("qc", [r"intensity|distribution"]),
        "volcano": ("differential", [r"volcano"]),
        "differential_heatmap": ("differential", [r"differential.*heatmap|heatmap.*differential|dep.*heatmap|protein.*heatmap"]),
        "GO_BP": ("go", [r"go[_-]?bp"]),
        "GO_CC": ("go", [r"go[_-]?cc"]),
        "GO_MF": ("go", [r"go[_-]?mf"]),
        "KEGG": ("kegg", [r"kegg"]),
        "GSEA": ("gsea", [r"gsea"]),
        "PPI": ("ppi", [r"ppi|string|network"]),
    }
    figure_failures: list[str] = []
    figure_not_run: list[str] = []
    for label, (branch, patterns) in figure_specs.items():
        matched = [path for path, lower in zip(figure_files, figure_text) if any(re.search(pattern, lower) for pattern in patterns)]
        has_png = any(path.suffix.lower() == ".png" for path in matched)
        has_vector = any(path.suffix.lower() in {".pdf", ".svg"} for path in matched)
        if has_png and has_vector:
            continue
        if branch_not_run_or_failed(manifest, branch):
            figure_not_run.append(f"{label}({branch_state(manifest, branch)})")
        elif formal or branch_succeeded(manifest, branch):
            figure_failures.append(label)
    if figure_failures:
        add("FIG", "最终图件 PNG+矢量", "FAIL", "缺少或格式不全: " + ", ".join(figure_failures))
    elif figure_not_run:
        add("FIG", "最终图件 PNG+矢量", "NOT_RUN", "分支未完成: " + ", ".join(figure_not_run))
    else:
        add("FIG", "最终图件 PNG+矢量", "PASS", f"审计文件数={len(figure_files)}")

    report_docx = root / "16_final_report" / "soybean_proteomics_report_zh.docx"
    report_pdf = root / "16_final_report" / "soybean_proteomics_report_zh.pdf"
    if report_docx.is_file():
        pdf_supported = manifest.get("deliverables", {}).get("pdf_supported")
        report_status = "FAIL" if pdf_supported is True and not report_pdf.is_file() else "PASS"
        evidence = f"DOCX=present; PDF={'present' if report_pdf.is_file() else 'not produced'}; pdf_supported={pdf_supported!r}"
    else:
        report_status = "FAIL" if formal else "NOT_RUN"
        evidence = "未找到中文 DOCX"
    add("REPORT", "中文报告", report_status, evidence)

    if skipped:
        add("SCAN", "大文件/不可读扫描说明", "NOT_RUN", "; ".join(skipped[:20]))

    failed = [item for item in results if item["status"] == "FAIL"]
    not_run = [item for item in results if item["status"] == "NOT_RUN"]
    overall = "FAILED" if failed else ("PARTIAL_NOT_RUN" if not_run else "PASS")
    generated = datetime.now(timezone.utc).isoformat()

    report_lines = [
        "# RUNTIME ANALYSIS AUDIT REPORT",
        "",
        f"- 结果目录：`{root}`",
        f"- 生成时间（UTC）：`{generated}`",
        f"- 总体状态：**{overall}**",
        f"- 正式交付状态已触发：`{formal}`",
        f"- INPUT INTEGRITY CHECK：**{integrity_status}**",
        "",
        "| 编号 | 检查项 | 状态 | 证据 |",
        "|---|---|---|---|",
    ]
    for item in results:
        evidence = item["evidence"].replace("|", "\\|").replace("\n", " ")
        report_lines.append(f"| {item['code']} | {item['title']} | **{item['status']}** | {evidence} |")
    report_lines.extend(
        [
            "",
            "## 判定",
            "",
            "- `FAILED`：至少一个硬性检查失败，不得宣称完整成功。",
            "- `PARTIAL_NOT_RUN`：没有硬失败，但仍有未执行、不可访问或外部分支未完成；只能作为部分完成交付。",
            "- `PASS`：A-N、输入完整性和必需工件均通过。",
            "",
        ]
    )
    report_path = args.report.resolve() if args.report else root / "logs" / "RUNTIME_ANALYSIS_AUDIT_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8", newline="\n")
    json_path = root / "logs" / "runtime_audit.json"
    json_path.write_text(
        json.dumps({"overall_status": overall, "generated_utc": generated, "formal_delivery": formal, "results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"RUNTIME ANALYSIS AUDIT REPORT: {overall}")
    print(report_path)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
