# MySQL type-upgrade consistency suite

This suite verifies SQL-direct type upgrades for result correctness, data
correctness, and consistency between the local `COPY` oracle and internal
`INPLACE` / `INSTANT` profiles. It intentionally excludes temporal, floating
point, `ENUM`, `SET`, JSON, spatial, vector, FULLTEXT, and SPATIAL factors.

## Scope

Retained type families:

- Integer: `TINYINT`, `SMALLINT`, `MEDIUMINT`, `INT`, `BIGINT`, including
  signed/unsigned transitions.
- Exact decimal: `DECIMAL(p,s)` / `NUMERIC(p,s)`; positive cases increase
  precision while preserving scale.
- Character: `CHAR`, `VARCHAR`, and TEXT family upgrades across length-head
  boundaries and charsets/collations.
- Binary: `BINARY`, `VARBINARY`, and BLOB family upgrades.
- `BIT(M)` width upgrades from 1 through 64.

The suite also covers column attributes, indexes, foreign keys, generated
columns, functional indexes, views, triggers, stored functions, stored
procedures, prepared statements, table forms, partitioning, row formats,
INSTANT ALTER history, and relevant SQL modes.

## Artifacts

Generated artifacts are deterministic and stored compressed:

- `generated/type_upgrade_consistency/cases.jsonl.gz`
- `generated/type_upgrade_consistency/copy_suite.sql.gz`
- `generated/type_upgrade_consistency/inplace_suite.sql.gz`
- `generated/type_upgrade_consistency/instant_suite.sql.gz`
- `generated/type_upgrade_consistency/coverage.tsv`
- `generated/type_upgrade_consistency/manifest.json`
- `generated/type_upgrade_consistency/local_results.jsonl`
- `generated/type_upgrade_consistency/local_summary.json`
- `generated/type_upgrade_consistency/local_summary.md`

`manifest.json` records case counts, cluster/family coverage, forbidden-type
absence, and SHA-256 hashes for the generated artifacts.

Current generated size: **8,270 cases**. The three profiles (`COPY`,
`INPLACE`, and `INSTANT`) share the same ordered case IDs.

## Generate

```bash
cd mysql_case_factory
python3 -m venv .venv312
.venv312/bin/pip install -e '.[test,runner]'
.venv312/bin/python tools/generate_type_upgrade_cases.py \
  --output generated/type_upgrade_consistency
```

The generator is deterministic. Re-running it must produce byte-identical
compressed case and suite artifacts.

## Local COPY verification

The local runner starts an isolated MySQL 8.0.45 instance with a temporary
data directory, Unix socket, `--skip-networking`, and no credentials:

```bash
cd mysql_case_factory
.venv312/bin/python tools/run_type_upgrade_copy.py \
  --cases generated/type_upgrade_consistency/cases.jsonl.gz \
  --results generated/type_upgrade_consistency/local_results.jsonl \
  --summary generated/type_upgrade_consistency/local_summary.json
```

The runner stops on the first failure, preserves the result and error metadata,
and cleans up the server and temporary directory. A natural server crash is
classified as a failure and is never treated as an expected negative result.

Current local evidence is recorded in `local_summary.md` and ties the result to
the case manifest SHA-256.

## Internal INPLACE / INSTANT verification

The same case IDs are rendered for both internal profiles:

```bash
gunzip -c generated/type_upgrade_consistency/inplace_suite.sql.gz > inplace_suite.sql
gunzip -c generated/type_upgrade_consistency/instant_suite.sql.gz > instant_suite.sql
```

Run each suite in an isolated internal QA schema. For every expected-success
case, the final schema, existing data, post-DDL data, indexes, constraints,
and dependency behavior must match the reference expectation. For every
expected-reject case, the DDL must fail without partially changing the table.

A difference between `INPLACE` and `INSTANT` is an algorithm difference and
must be reported unless the product contract explicitly permits it.
