#!/usr/bin/env python3
"""Create a non-overwriting, zero-host-install soybean proteomics project."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


DIRECTORIES = [
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_record(path: Path, skip_checksum: bool, origin: str) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"Input is not a file: {resolved}")
    checksum = None if skip_checksum else sha256(resolved)
    return {
        "source_path": str(resolved),
        "source_origin": origin,
        "exists_at_initial_audit": True,
        "readable_at_initial_audit": True,
        "size_bytes_before": resolved.stat().st_size,
        "sha256_before": checksum,
        "sha256_after": None,
        "integrity_status": "SKIPPED" if skip_checksum else "PENDING_FINAL_CHECK",
        "source_mutated": False,
    }


def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def write_input_table(path: Path, inputs: list[dict[str, object]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    fields = [
        "source_path",
        "source_origin",
        "exists_at_initial_audit",
        "readable_at_initial_audit",
        "size_bytes_before",
        "sha256_before",
        "integrity_status",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", delimiter="\t")
        writer.writeheader()
        writer.writerows(inputs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="New result directory")
    parser.add_argument("--input", action="append", default=[], type=Path)
    parser.add_argument(
        "--input-origin",
        choices=["local-path", "uploaded", "managed-cloud", "transferred"],
        default="local-path",
    )
    parser.add_argument("--skip-checksum", action="store_true")
    parser.add_argument(
        "--execution-environment",
        choices=[
            "current-codex",
            "managed-cloud",
            "sandbox-container",
            "ephemeral-isolated",
            "equivalent-implementation",
        ],
        default="current-codex",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Create only missing directories; still refuse to overwrite files",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if root.exists() and not args.resume:
        raise FileExistsError(
            f"Result directory already exists: {root}. Use a new path or --resume."
        )
    root.mkdir(parents=True, exist_ok=args.resume)
    for name in DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True)

    inputs = [
        input_record(path, args.skip_checksum, args.input_origin) for path in args.input
    ]
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "skill": "soybean-proteomics",
        "created_utc": now,
        "analysis_status": "PLANNING",
        "organism": {
            "scientific_name": "Glycine max",
            "common_name": "soybean / 大豆",
            "ncbi_taxid": 3847,
            "kegg_code": "gmx",
        },
        "gate": {
            "status": "ANALYSIS_PLAN_REQUIRED",
            "confirmed_by_user": False,
            "confirmation_evidence": None,
        },
        "execution_environment": {
            "selected": args.execution_environment,
            "zero_local_install": True,
            "windows_host_environment_modified": False,
            "equivalent_implementation_validation": None,
        },
        "input_files": inputs,
        "sample_metadata": {
            "path": None,
            "mapping_evidence": None,
            "unresolved_aliases": [],
        },
        "annotation_provenance": {
            "genome_assembly": None,
            "annotation_release": None,
            "reference_proteome": None,
            "fasta_source": None,
            "fasta_sha256": None,
            "gff_gtf_version": None,
            "uniprot_release_or_access_date": None,
            "go_source_version_or_access_date": None,
            "kegg_access_date": None,
            "string_version_or_access_date": None,
        },
        "software": {},
        "databases": {},
        "parameters": {},
        "thresholds": {},
        "random_seed": None,
        "filtering_rules": [],
        "normalization": None,
        "missingness_assessment": None,
        "imputation": None,
        "statistical_method": None,
        "multiple_testing": None,
        "id_mapping": None,
        "enrichment": {
            "background_definition": None,
            "go_ora": "NOT_RUN",
            "kegg_ora": "NOT_RUN",
            "gsea_ranking_metric": None,
            "gsea": "NOT_RUN",
        },
        "analysis_branches": {
            "qc": "NOT_RUN",
            "differential": "NOT_RUN",
            "id_mapping": "NOT_RUN",
            "go": "NOT_RUN",
            "kegg": "NOT_RUN",
            "gsea": "NOT_RUN",
            "ppi": "NOT_RUN",
        },
        "deliverables": {
            "workbook": "14_final_tables/soybean_proteomics_results.xlsx",
            "required_sheets": REQUIRED_SHEETS,
            "chinese_docx": "16_final_report/soybean_proteomics_report_zh.docx",
            "chinese_pdf": "16_final_report/soybean_proteomics_report_zh.pdf",
            "pdf_supported": None,
            "status": "NOT_RUN",
        },
    }
    manifest_dir = root / "00_input_manifest"
    write_new(
        manifest_dir / "analysis_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    write_input_table(manifest_dir / "input_manifest.tsv", inputs)
    session = (
        f"created_utc: {now}\n"
        f"platform: {platform.platform()}\n"
        f"python: {sys.version.replace(chr(10), ' ')}\n"
        f"execution_environment: {args.execution_environment}\n"
        "zero_local_install: true\n"
    )
    write_new(root / "logs" / "session_info.txt", session)
    write_new(root / "logs" / "run_log.jsonl", "")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
