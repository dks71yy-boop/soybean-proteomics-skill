# Contributing

Contributions, forks, modifications, and derivative development are welcome.

## Before contributing

This repository is intentionally species-locked to **soybean (*Glycine max*)**:

- NCBI Taxonomy ID: `3847`
- KEGG organism code: `gmx`

Changes to the soybean workflow should preserve this species lock and must not silently introduce human, mouse, or other-organism defaults.

If you want to support another plant species, the preferred approach is to fork this repository or create a clearly separated species profile/skill so that organism-specific databases, identifiers, enrichment resources, and provenance remain explicit.

## Suggested workflow

1. Fork the repository.
2. Create a feature branch.
3. Make focused changes.
4. Run the static checks:

```bash
python -m py_compile scripts/*.py
python scripts/audit_skill.py .
```

5. Document behavior changes in `CHANGELOG.md` when appropriate.
6. Open a pull request describing the motivation, implementation, and validation performed.

## Pull-request expectations

Please keep the following principles intact unless the pull request explicitly proposes and justifies a design change:

- read-only handling of original experimental inputs;
- explicit analysis-plan gate before formal downstream analysis;
- experiment-aware enrichment background;
- clear separation of native soybean evidence from orthology-based inference;
- reproducible provenance and runtime auditing;
- no fabricated database versions, mapping rates, pathways, PPI results, or statistical outputs.

## License

By contributing, you agree that your contributions will be licensed under the repository's MIT License.
