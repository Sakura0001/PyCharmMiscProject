# Sub-Agent Factor Review Template

Each review covers a bounded group of PostgreSQL statement references and maps
them to MySQL Community Server 8.0.22.

## Required Output

```yaml
review:
  reviewer: "<agent nickname>"
  scope:
    pg_paths:
      - "skills/pg-sql-generation/references/statements/..."
  official_sources:
    - url: "https://dev.mysql.com/doc/refman/8.0/en/..."
      used_for:
        - "CREATE TABLE syntax"
  statements:
    - pg_statement_key: "create_index"
      mysql_statement_key: "create_index"
      decision: "rewrite_for_mysql"
      reason: "MySQL has CREATE INDEX but the method/operator-class factors are PostgreSQL-specific."
      factor_decisions:
        - pg_factor: "method"
          decision: "rewrite_for_mysql"
          mysql_factor: "index_type"
          mysql_values:
            - "btree"
            - "hash"
          evidence_url: "https://dev.mysql.com/doc/refman/8.0/en/create-index.html"
      mysql_missing_factors:
        - factor: "index_algorithm_lock"
          reason: "MySQL CREATE INDEX is mapped to ALTER TABLE and supports ALGORITHM/LOCK behavior."
          evidence_url: "https://dev.mysql.com/doc/refman/8.0/en/create-index.html"
  mysql_missing_statements:
    - statement_key: "create_user"
      reason: "MySQL account management statement not represented by PostgreSQL role/user mapping."
      evidence_url: "https://dev.mysql.com/doc/refman/8.0/en/create-user.html"
```

## Decision Values

- `keep_as_mysql`: the statement or factor maps directly to MySQL 8.0.22.
- `rewrite_for_mysql`: MySQL covers the concept but syntax, values, or behavior
  must change.
- `drop_pg_only`: PostgreSQL-only feature with no MySQL 8.0.22 counterpart.
- `add_mysql_missing`: MySQL 8.0.22 feature missing from the PostgreSQL-derived
  library.
- `excluded_after_8_0_22`: appears in current docs but is not proven for 8.0.22.
