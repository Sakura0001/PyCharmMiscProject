# MySQL 8.0.22 Factor Catalog

Global factor catalog for MySQL statement references. Statement files map local
factors to this catalog through `factor_catalog_mapping`.

```yaml
structured_config:
  kind: factor_catalog
  skill_name: mysql80_factor_catalog
  version: "8.0.22"
  object_domains:
    database:
      key: database
      label: Database
      applies_to:
        - create_database
        - alter_database
        - drop_database
      factor_groups:
        naming:
          key: naming
          label: Naming
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: Database identifier shape
              values:
                - key: unquoted_lower
                  label: unquoted lower-case identifier
                  expected_status: success
                - key: quoted_reserved
                  label: quoted reserved word identifier
                  expected_status: success
        options:
          key: options
          label: Database options
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            charset:
              key: charset
              label: CHARACTER SET option
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: utf8mb4
                  label: CHARACTER SET utf8mb4
                  expected_status: success
            collation:
              key: collation
              label: COLLATE option
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: utf8mb4_0900_ai_ci
                  label: COLLATE utf8mb4_0900_ai_ci
                  expected_status: success
    table:
      key: table
      label: Table
      applies_to:
        - create_table
        - alter_table
        - drop_table
        - insert
        - update
        - delete
      factor_groups:
        naming:
          key: naming
          label: Naming
          default_tier: T3
          default_coverage_role: rotate_attach
          factors:
            name_shape:
              key: name_shape
              label: Table identifier shape
              values:
                - key: unquoted_lower
                  label: unquoted lower-case identifier
                  expected_status: success
                - key: quoted_reserved
                  label: quoted reserved word identifier
                  expected_status: success
        definition:
          key: definition
          label: Definition
          default_tier: T1
          default_coverage_role: main_axis
          factors:
            temporary:
              key: temporary
              label: TEMPORARY table option
              values:
                - key: permanent
                  label: permanent table
                  expected_status: success
                - key: temporary
                  label: temporary table
                  expected_status: success
            if_not_exists:
              key: if_not_exists
              label: IF NOT EXISTS clause
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: present
                  label: present
                  expected_status: success
            storage_engine:
              key: storage_engine
              label: ENGINE table option
              values:
                - key: innodb
                  label: ENGINE=InnoDB
                  expected_status: success
                - key: memory
                  label: ENGINE=MEMORY
                  expected_status: success
        boundary:
          key: boundary
          label: Boundary
          default_tier: T5
          default_coverage_role: rotate_attach
          factors:
            duplicate_name:
              key: duplicate_name
              label: duplicate object name
              values:
                - key: no_conflict
                  label: no duplicate
                  expected_status: success
                - key: name_already_exists
                  label: object already exists
                  expected_status: failure
    index:
      key: index
      label: Index
      applies_to:
        - create_index
        - drop_index
      factor_groups:
        definition:
          key: definition
          label: Index definition
          default_tier: T1
          default_coverage_role: main_axis
          factors:
            index_kind:
              key: index_kind
              label: Index kind
              values:
                - key: normal
                  label: nonunique index
                  expected_status: success
                - key: unique
                  label: unique index
                  expected_status: success
                - key: fulltext
                  label: fulltext index
                  expected_status: success
                - key: spatial
                  label: spatial index
                  expected_status: success
            index_type:
              key: index_type
              label: USING index_type
              values:
                - key: omitted
                  label: default index type
                  expected_status: success
                - key: btree
                  label: USING BTREE
                  expected_status: success
                - key: hash
                  label: USING HASH
                  expected_status: success
        options:
          key: options
          label: Index options
          default_tier: T2
          default_coverage_role: representative_or_main
          factors:
            visibility:
              key: visibility
              label: VISIBLE or INVISIBLE
              values:
                - key: visible
                  label: VISIBLE
                  expected_status: success
                - key: invisible
                  label: INVISIBLE
                  expected_status: success
            algorithm_lock:
              key: algorithm_lock
              label: online DDL ALGORITHM/LOCK options
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: inplace_none
                  label: ALGORITHM=INPLACE LOCK=NONE
                  expected_status: success
    transaction:
      key: transaction
      label: Transaction
      applies_to:
        - start_transaction
        - commit
        - rollback
      factor_groups:
        control:
          key: control
          label: Transaction control
          default_tier: T1
          default_coverage_role: main_axis
          factors:
            chain_mode:
              key: chain_mode
              label: AND CHAIN / AND NO CHAIN
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: and_chain
                  label: AND CHAIN
                  expected_status: success
                - key: and_no_chain
                  label: AND NO CHAIN
                  expected_status: success
            release_mode:
              key: release_mode
              label: RELEASE / NO RELEASE
              values:
                - key: omitted
                  label: omitted
                  expected_status: success
                - key: release
                  label: RELEASE
                  expected_status: success
                - key: no_release
                  label: NO RELEASE
                  expected_status: success
```
