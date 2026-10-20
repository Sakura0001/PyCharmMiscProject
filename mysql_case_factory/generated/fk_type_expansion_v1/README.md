# FK type-expansion consistency batch

This independent `TUCFK` batch verifies parent/child consistency after child
foreign-key column expansion.

- **BATCH_ID:** `2026-10-20-fk-type-expansion-consistency-v1`
- **BATCH_KIND:** `fk_type_expansion_consistency`
- **CASE_PREFIX:** `TUCFK`
- **Database:** `qa_fk_type_expansion`
- **Cases:** 568
- **Transitions:** 71
- **Profiles:** `inplace`, `instant`
- **FK actions:** `RESTRICT`, `NO ACTION`, `CASCADE`, `SET NULL`

## Execution

```bash
gunzip -c inplace_suite.sql.gz > inplace.sql
mysql --login-path=internal_qa --batch --raw --skip-column-names --binary-mode --force \
  qa_fk_type_expansion < inplace.sql > inplace.actual.tsv 2> inplace.errors.log

diff -u expected_output_inplace.tsv inplace.actual.tsv
```

Repeat for `instant_suite.sql.gz` and `expected_output_instant.tsv`.

A run passes only when:

1. stdout matches the expected TSV exactly;
2. no result row is `FAIL`;
3. orphan count is always zero;
4. the FK still exists;
5. there is no signal, assertion, timeout, MySQL 2013/2006, or lost connection.
