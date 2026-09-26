# Data access and reproducibility

Statistical source: NBA.com. The underlying files are publicly available in the
[shufinskiy/nba_data archive at the exact version used](https://github.com/shufinskiy/nba_data/tree/e829d4678be1e075f99e5d41a1c5f97089be446b).

## Retrieve the exact inputs

From the repository root, after installing `replication/requirements.txt` in a
virtual environment as described in README:

```bash
.venv/bin/python replication/fetch_data.py
.venv/bin/python replication/run.py --check-only
.venv/bin/python replication/run.py
```

The downloader retrieves 20 upstream archives and verifies archive hashes and the
22 resulting input-file hashes. It uses pinned commit URLs rather than a mutable
branch. The analysis reads eight matchup CSVs and fourteen source archives.

- [Exact source URLs, archive members and checksums](replication/upstream_manifest.json)
- [Required input paths, sizes and checksums](replication/data_manifest.json)
- [Portable computation instructions](replication/README.md)

The repository supplies code, aggregate results and retrieval instructions; it does
not re-host the underlying NBA records. No new rights in third-party data are granted.
The upstream Apache 2.0 notice is retained in `replication/licenses/`.

## What can be reproduced

`paper/aggregate_claims.json` records the displayed paper quantities, including
supplementary values not recomputed by this pipeline. `replication/expected_aggregates.json` provides reference outputs for
the portable headline computation. The README distinguishes this computation from
supplementary analyses and full model-fitting uncertainty. No private video-review
samples, coding returns or coordinator materials are distributed.
