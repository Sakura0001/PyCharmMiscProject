# PG16 Factor Catalog Mapping Status

Updated: 2026-06-26

## Summary

The factor integration model is in its first implementation slice. The global catalog exists, the mapping template exists, and the database object domain has end-to-end mappings for `CREATE DATABASE`, `ALTER DATABASE`, and `DROP DATABASE`.

Current audit result for the database mappings: `mapped=40`, `excluded=14`.

## Object Domain Status

| Object domain | Catalog status | Statement mapping status | Notes |
| --- | --- | --- | --- |
| database | Detailed | CREATE / ALTER / DROP mapped | First end-to-end example |
| domain | Seeded | Not mapped | Next first-batch target |
| schema | Seeded | Not mapped | Next first-batch target |
| role_user_group | Seeded | Not mapped | Next first-batch target |
| tablespace | Seeded | Not mapped | Next first-batch target |
| extension | Seeded | Not mapped | Next first-batch target |
| sequence | Seeded | Not mapped | Next first-batch target |

## DATABASE Mapping Results

| Statement | Mapping result | Main policy |
| --- | --- | --- |
| `create_database` | Uses database naming, owner, template, encoding, locale, strategy, privilege, environment, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |
| `alter_database` | Uses database naming, WITH options, owner target, tablespace, config parameter, environment, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |
| `drop_database` | Uses database naming, IF EXISTS, FORCE, privilege, connection state, active connection, boundary, and validation factors | Existing main axes stay `statement_branch`, `object_state`, `expected_status` |

## Current Audit Command

```bash
python3 tools/audit_factor_catalog_mapping.py --root .
```

## Next Migration Targets

1. Expand `domain` catalog values from `1.txt`.
2. Map `create_domain`, `alter_domain`, and `drop_domain`.
3. Expand and map `schema`.
4. Expand and map `role_user_group`.
5. Expand and map `tablespace`, `extension`, and `sequence`.
