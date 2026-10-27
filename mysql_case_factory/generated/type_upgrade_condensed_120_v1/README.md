# Type-upgrade condensed 120 SQL batch

This batch contains exactly 120 individual SQL files. Each file contains both
`INPLACE` and `INSTANT` candidates and compares each candidate with a directly
created target-type reference table.

- **BATCH_ID:** `2026-10-27-type-upgrade-condensed-120-v1`
- **BATCH_KIND:** `type_upgrade_condensed_sql`
- **CASE_PREFIX:** `TUCR`
- **Database:** `qa_type_upgrade_condensed_120`
- **SQL files:** 120
- **Expected output lines:** 240
- **Algorithms per file:** `INPLACE`, `INSTANT`

## Execution

Create the database:

```bash
mysql --login-path=internal_qa \
  -e "DROP DATABASE IF EXISTS qa_type_upgrade_condensed_120; CREATE DATABASE qa_type_upgrade_condensed_120 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
```

Run one file:

```bash
mysql --login-path=internal_qa \
  --batch --raw --skip-column-names --binary-mode --force \
  qa_type_upgrade_condensed_120 \
  < generated/type_upgrade_condensed_120_v1/sql/TUCR-000001.sql
```

Run all files:

```bash
for file in generated/type_upgrade_condensed_120_v1/sql/*.sql; do
  mysql --login-path=internal_qa \
    --batch --raw --skip-column-names --binary-mode --force \
    qa_type_upgrade_condensed_120 \
    < "$file"
done > generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Compare:

```bash
diff -u generated/type_upgrade_condensed_120_v1/expected_output.tsv \
  generated/type_upgrade_condensed_120_v1/actual_output.tsv
```

Use `--force` because each file intentionally executes both algorithms. A
natural algorithm rejection must not prevent the other algorithm and the data
comparison from running.
