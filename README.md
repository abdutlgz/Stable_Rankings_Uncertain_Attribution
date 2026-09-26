# Stable Rankings, Uncertain Attribution

Research materials for **Stable Rankings, Uncertain Attribution: Validating NBA Matchup Turnover Metrics**.

- [Paper](paper/manuscript.md) and [abstract](paper/abstract.md)
- [Reported numerical values](paper/aggregate_claims.json), including supplementary results
- [Data sources and access](DATA_ACCESS.md)

## Run the analysis

Tested with Python 3.9.10 on macOS. From this repository's root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r replication/requirements.txt
.venv/bin/python replication/fetch_data.py
.venv/bin/python replication/run.py --check-only
.venv/bin/python replication/run.py
```

The downloader retrieves the exact public input versions and verifies their checksums. The analysis reconstructs the attribution audit, eight season models, external-credit correlations, persistence, corrected bootstrap inference, turnover subtypes and Appendix D screening pilot. It compares the outputs with reference values and writes `replication/results/verification.json`. These checked results were reproduced locally from checksum-verified inputs.

## Scope

The pipeline reuses the original implementation. It does not rerun every supplementary analysis, the finite-prior sensitivity grid, dynamic smoothing or full model-refitting uncertainty. `paper/aggregate_claims.json` records reported numerical values; it is not a replacement for recomputation. The figures are supplied as finished images; document-formatting tools are omitted. Independent human video validation is not available. See the paper for interpretation limits and [replication details](replication/README.md).

## License

Original software is provided under the [MIT License](LICENSE). NBA records are retrieved directly from the pinned upstream archive and are not included. See [third-party notices](replication/THIRD_PARTY_NOTICES.md).
