# RunbookDrift Gate

RunbookDrift Gate is a narrow GenLayer Intelligent Contract for detecting safety regressions between authenticated versions of an operations runbook.

Every validator independently fetches a baseline and candidate from commit-pinned Raw GitHub locations, recomputes both SHA-256 digests from the fetched bytes and evaluates whether rollback, verification and escalation safeguards remain effective. Deterministic contract logic derives the verdict. Only a `SAFE_REVISION` can become the next baseline generation.

## Why GenLayer

Textual diffs cannot reliably determine whether differently worded procedures preserve the same operational safeguard. GenLayer validators can independently judge semantic equivalence while the contract enforces source integrity, bounded output, verdict precedence, authority, lifecycle and replay resistance.

## Public methods

- `open_lineage`: create generation zero from a commit-pinned baseline.
- `propose_revision`: bind one candidate to the current generation.
- `assess_revision`: fetch, hash and semantically compare both documents.
- `promote_revision`: advance the lineage only after `SAFE_REVISION`.
- `dismiss_revision`: close a finalized non-promoted candidate.
- `cancel_pending`: cancel before assessment.
- `get_lineage`, `get_revision`, `get_counts`: authoritative readback.

## Test

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Current status: contract implementation and 11 direct/static tests pass, including exact fetched-byte hashing, proof that digest mismatch blocks the semantic prompt, and a regression test for the GenLayer web response field `status`. Public fixture URLs and SHA-256 commitments computed from their Raw GitHub bytes are recorded in [verification/RAW_FIXTURES.json](verification/RAW_FIXTURES.json).

An initial StudioNet deployment at `0x0A1c0bE98F74fe09FDe3B8a3Afd07Ee2cAdD412C` matched the earlier repository source but exposed an API integration defect: the contract read `response.status_code` while the pinned GenLayer runtime exposes `response.status`. Its assessment safely returned `ASSESSMENT_RETRYABLE` without state mutation. That deployment is superseded and must not be submitted as the production address. The corrected source requires a new deployment before live verification resumes.

See [SPEC.md](SPEC.md), [fixtures/README.md](fixtures/README.md) and [verification/AUDIT.md](verification/AUDIT.md).
