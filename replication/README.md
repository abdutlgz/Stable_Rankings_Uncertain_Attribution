# Portable headline replication

This package computes the selected measurement audit, season-specific rates and joint models, external credits, persistence, corrected inference, all reported turnover subtypes, and the Appendix D expanding-window screening pilot from checksum-pinned raw inputs. It exports aggregate results only.

## Run

Tested target: Python 3.9.10. Install the pinned dependencies into a new virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Retrieve the exact public source versions and run the checks from this directory:

```bash
.venv/bin/python fetch_data.py
.venv/bin/python run.py --check-only
.venv/bin/python run.py
```

The downloader verifies each archive and named CSV member. It refuses to replace an existing file whose checksum differs. Public availability is not redistribution clearance.

Alternatively, import verified copies from an existing local research-data tree:

```bash
.venv/bin/python run.py --import-data /absolute/path/to/data-tree --check-only
.venv/bin/python run.py
```

The expected aggregate files are read only for post-computation comparison and for selecting displayed reconciliation keys. The pilot uses season scores freshly reconstructed in the same run; it does not refit first-stage scores within each downstream training window. Its design is described in manuscript Appendix D; aggregate references are in `pilot/expected_results.json`. No stored player estimate supplies a new estimate. The default run stops on a missing/changed input, failed fit or numerical mismatch. Successful aggregate results appear in `results/verification.json`. Computation may take several minutes.

## Scope and release boundary

The source contains only the dependency closure of functions needed for this computation. It reuses the original implementation rather than providing an independent estimator. It does not rerun dynamic smoothing, all supplementary falsifications, finite-prior scenarios or full fitting-uncertainty calculations. No independent video sample, label, event assignment table, outreach or coordinator report is included.

The data manifest pins exact bytes from the upstream archive at commit
`e829d4678be1e075f99e5d41a1c5f97089be446b`. See `upstream_manifest.json` for
all immutable download URLs and `../DATA_ACCESS.md` for the access arrangement.
Original records are retrieved from that archive, not redistributed here.
Third-party terms remain separate; see `THIRD_PARTY_NOTICES.md`.
