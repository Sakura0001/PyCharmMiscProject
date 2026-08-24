# PostgreSQL 18.4 stable regress cases

This snapshot contains only regress SQL files whose two executions produced byte-identical raw `stdout` and raw `stderr` under PostgreSQL 18.4. Success and error outcomes are both retained when their complete outputs are stable.

## Snapshot

- Stable SQL files: 837,755
- Excluded unstable SQL files: 18,158
- Original executions: 1,711,826
- PostgreSQL version: 18.4 (`server_version_num = 180004`)
- Source manifest SHA-256: `60ea761fdcc12238d6adbb53b1aad19ea603e9914dfd27b155ae13c3322756e0`

## Files

- `stable-manifest.jsonl.gz`: stable case metadata and SQL SHA-256 values.
- `stable-cases.tsv.gz`: stable case IDs, paths, exit codes, and raw output hashes.
- `unstable-cases.tsv`: exclusion ledger for cases that were not copied into this snapshot.
- `final-summary.json`: full-run integrity and stability counts.
- `statement-summary.json`: execution classifications grouped by statement factor.
- `stability-analysis.md`: human-readable result and cause analysis.

The large runtime batch logs are intentionally not included. The stable manifest and indexes preserve the per-case identity, SQL digest, and two-run raw transcript digests needed to audit this snapshot.

## Verify the stable manifest row count

```bash
gzip -dc stable-manifest.jsonl.gz | wc -l
```

Expected result: `837755`.
