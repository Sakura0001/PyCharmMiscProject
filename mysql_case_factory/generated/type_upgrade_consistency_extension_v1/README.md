# Type-upgrade consistency extension v1

BATCH_ID: 2026-10-13-type-upgrade-consistency-extension-v1
BATCH_KIND: EXTENSION
PARENT_BATCH_ID: 2026-10-13-type-upgrade-consistency
CASE_COUNT: 13721
CASE_PREFIX: TUCX

This is an independent extension batch. Do not mix it with the verified `TUC` baseline.
`TUC` is the 8,270-case baseline; `TUCX` is this extension batch.

## Internal AI execution instructions

1. Verify `manifest.json` first. The parent batch, extension batch, case count, profile
   counts, and artifact hashes must match.
2. Execute only `TUCX-` cases carrying this extension batch ID. Do not execute or merge
   results with `TUC-` baseline cases.
3. Run `COPY` locally only as the MySQL 8.0.45 oracle. Internal PASS must come from
   separate `INPLACE` and `INSTANT` executions.
4. Negative cases may intentionally return SQL errors. Use `mysql --force`, preserve stderr,
   and continue through planned rejects.
5. A server crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`; never classify it as
   an expected negative result.
6. On failure, stop, preserve stdout/stderr and the nearest `-- CASE_ID`, and report batch
   ID, profile, case ID, gap ID, SQL, error, and terminal state.

Example:

```bash
gunzip -c inplace_suite.sql.gz > inplace_suite.sql
gunzip -c instant_suite.sql.gz > instant_suite.sql

mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade_extension \
  < inplace_suite.sql > inplace.results.tsv 2> inplace.errors.log

mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade_extension \
  < instant_suite.sql > instant.results.tsv 2> instant.errors.log

grep -n $'\tFAIL\t\|^FAIL\b' inplace.results.tsv instant.results.tsv || true
```
