# Type-upgrade consistency batch

BATCH_ID: 2026-10-13-type-upgrade-consistency
BATCH_KIND: NEW_MERGE
CASE_COUNT: 8270
CASE_PREFIX: TUC

This batch is separate from previous DDL verification cases.
It was merged into `codex/ddl-verify-20260919` as a new type-upgrade consistency suite.

## Internal AI execution instructions

Execute only this batch. Do not mix it with previous DDL verification cases.

1. Treat `cases.jsonl.gz` as the authoritative case list. Every selected case must have
   `batch_id=2026-10-13-type-upgrade-consistency`, `batch_kind=new_merge`, and a case ID beginning with
   `TUC-`. Do not execute older cases or cases from previous workbooks.
2. Verify `manifest.json` before running: the batch identity, 8,270 case count, profile case
   counts, and artifact SHA-256 values must all match.
3. Create an isolated internal QA schema. Run `INPLACE` and `INSTANT` separately using
   `inplace_suite.sql.gz` and `instant_suite.sql.gz`. The local COPY result is evidence from
   the local MySQL 8.0.45 oracle and must not be reported as internal PASS.
4. Negative cases intentionally return SQL errors. Execute the SQL files with `mysql --force`,
   preserve stderr, and continue through the planned rejects.
5. A run passes only when the result output contains no `FAIL` and the expected 8,270 case
   markers are present for the profile. Planned negative DDL errors may appear in stderr.
6. A server crash, assertion, signal, or lost connection such as MySQL error 2013 is
   `FAIL_CRASH`; never classify it as an expected negative result.
7. On any failure, stop the batch, preserve stdout/stderr and the nearest `-- CASE_ID`,
   and report the batch ID, profile, case ID, SQL, error, and terminal state. Do not retry
   silently or rewrite the expected outcome.

Example execution:

```bash
gunzip -c inplace_suite.sql.gz > inplace_suite.sql
gunzip -c instant_suite.sql.gz > instant_suite.sql

mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade \
  < inplace_suite.sql > inplace.results.tsv 2> inplace.errors.log

mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade \
  < instant_suite.sql > instant.results.tsv 2> instant.errors.log

grep -n $'\tFAIL\t\|^FAIL\b' inplace.results.tsv instant.results.tsv || true
```
