# Skill: PG18.4 Type Catalog

## Purpose

Defines a finite, executable PostgreSQL 18.4 **core column-test profile** inventory. It is deliberately not presented as every row in `pg_type`: the exact source-derived built-in and automatic-array inventories are recorded separately below. The executable profiles use stable `snake_case` keys, declaration SQL, boundary values, setup prerequisites, and conservative index capability metadata.

## Usage

- Statement references can select column data types from `structured_config.types`.
- `type_sets.canonical_executable_column_profiles` is the canonical finite **executable-profile** selector and resolves to `structured_config.types`; it is only one dimension of a complete column scope.
- `concrete_builtin_types` and `auto_array_types` are exact source-derived inventories from PostgreSQL 18.4 `pg_type.dat`; they are evidence inventories, not a claim that every internal type accepts a portable literal.
- `type_sets.all_pg18_column_types` is a deprecated compatibility name for the core profile selector; it does **not** mean all concrete `pg_type` rows.
- Entries for user-defined enum, domain, and composite types include `requires_setup` SQL that must run before table creation.
- Serial entries are declaration syntax that expands to integer columns with sequence-backed defaults; they are not ordinary storage types.
- A feature plan that marks `column_type` complete must enumerate all seven complementary dimensions: `types`, `concrete_builtin_types`, `auto_array_types`, `pseudo_types`, `declaration_aliases`, `typmod_declarations`, and `user_defined_archetypes`. Unsupported or environment-bound entries remain explicit expected-failure or justified-N/A obligations.
- The PG16.4-to-PG18.4 review found one documented numeric alias addition (`FLOAT`), interval infinity support, UUIDv4/UUIDv7 generators, a changed malformed-array diagnostic, and MERGE composite expansion. These deltas are recorded below.

## Structured Config

```yaml
structured_config:
  kind: type_catalog
  skill_name: pg18_type_catalog
  version: pg18.4
  source_docs:
    - https://www.postgresql.org/docs/18/datatype.html
    - https://www.postgresql.org/docs/18/datatype-numeric.html
    - https://www.postgresql.org/docs/18/datatype-pseudo.html
    - https://www.postgresql.org/docs/18/rangetypes.html
    - https://www.postgresql.org/docs/18/datatype-oid.html
    - https://www.postgresql.org/docs/18/datatype-json.html
    - https://www.postgresql.org/docs/18/datatype-geometric.html
    - https://www.postgresql.org/docs/18/datatype-net-types.html
    - https://www.postgresql.org/docs/18/textsearch-intro.html
    - https://www.postgresql.org/docs/18/arrays.html
    - https://www.postgresql.org/docs/18/rowtypes.html
  source_audit:
    baseline_release: "16.4"
    target_release: "18.4"
    baseline_archive_sha256: 971766d645aa73e93b9ef4e3be44201b4f45b5477095b049125403f9f3386d6f
    target_archive_sha256: 81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094
    review_status: semantic_reviewed
    readiness: ready
    catalog_sources:
      pg_type_dat:
        path: src/include/catalog/pg_type.dat
        sha256: 5f5887b75677cba2d4a1a0cfeb355df5ed91f85d385fac88bd8d7c605b3578f9
        derivation: Parse pg_type.dat records in declaration order; explicit typtype p records are pseudo-types, and array_type_oid marks an automatically generated array type.
    documents:
      datatype.sgml:
        baseline_sha256: fc56c84616a08e0fdbe2fa36a4610f6660b3f6d00ccf8411a6f13e7e5993c3b0
        target_sha256: 86328daa77e20d81d222376ec0306d9841a17104e436c08d138eb763aefb3700
        disposition: adapted
      rangetypes.sgml:
        baseline_sha256: cfeffb134d2acc2ec45141726583b041410665c4a2f8ecf66cd3f9484a7f0014
        target_sha256: cfeffb134d2acc2ec45141726583b041410665c4a2f8ecf66cd3f9484a7f0014
        disposition: inherited_unchanged
      array.sgml:
        baseline_sha256: 4d9bd538c411a19089721d24b3f884ea9ebf97e36c856945f863e886fdc9e09c
        target_sha256: a432afb453ba3e4fc99b3b8055794fbd1f1d2980a85b14933ea8bae285dc6ab4
        disposition: diagnostic_changed
      rowtypes.sgml:
        baseline_sha256: a7349bd0b30cb136c1047609ec4c5e0873c7a688c6d54f89058ee25327bebe63
        target_sha256: a11d32279ca040d7bfdc4947178ea2cf2038d8536600f70881e794bec51f0c41
        disposition: merge_returning_adapted
    required_delta_tests:
      - pg18_float_alias_and_precision_boundaries
      - pg18_interval_infinity
      - pg18_uuid_v4_v7_generation
      - pg18_multidimensional_array_error_parity
      - pg18_merge_composite_expansion
  type_sets:
    canonical_executable_column_profiles:
      selector: structured_config.types
      description: Every finite, portable core profile maintained in this catalog. This is not every concrete pg_type row.
      include_pseudo_types: false
      completeness_scope: core_executable_profiles
      inventory_count: 85
      inventory_sha256: 1dc7ad6615d45c4191b5f00cd1b3a54fcfc1bb9cfa4eaa79f7b9a6377970ee7d
      review_status: semantic_reviewed
      readiness: ready
    all_pg18_column_types:
      description: Deprecated compatibility alias for canonical_executable_column_profiles; not all concrete PostgreSQL types.
      canonical: false
      replacement: canonical_executable_column_profiles
      include_pseudo_types: false
      review_status: semantic_reviewed
      readiness: ready
  concrete_builtin_types:
    source_member: source_audit.catalog_sources.pg_type_dat
    derivation: Every explicit pg_type.dat record whose typtype is not p, in source order.
    semantics: Exact PostgreSQL catalog inventory; internal/input-restricted entries may require catalog-derived values or expected-failure cases.
    count: 85
    inventory_sha256: 86ab59230c92253e56d467dd54cd3fe841c1af091595344a2cc33907b948d12e
    values:
      - bool
      - bytea
      - char
      - name
      - int8
      - int2
      - int2vector
      - int4
      - regproc
      - text
      - oid
      - tid
      - xid
      - cid
      - oidvector
      - pg_type
      - pg_attribute
      - pg_proc
      - pg_class
      - json
      - xml
      - pg_node_tree
      - pg_ndistinct
      - pg_dependencies
      - pg_mcv_list
      - xid8
      - point
      - lseg
      - path
      - box
      - polygon
      - float4
      - float8
      - circle
      - money
      - macaddr
      - inet
      - cidr
      - macaddr8
      - aclitem
      - bpchar
      - varchar
      - date
      - time
      - timestamp
      - timestamptz
      - interval
      - timetz
      - bit
      - varbit
      - numeric
      - refcursor
      - regprocedure
      - regoper
      - regoperator
      - regclass
      - regcollation
      - regtype
      - regrole
      - regnamespace
      - uuid
      - pg_lsn
      - tsvector
      - gtsvector
      - tsquery
      - regconfig
      - regdictionary
      - jsonb
      - jsonpath
      - txid_snapshot
      - pg_snapshot
      - int4range
      - numrange
      - tsrange
      - tstzrange
      - daterange
      - int8range
      - int4multirange
      - nummultirange
      - tsmultirange
      - tstzmultirange
      - datemultirange
      - int8multirange
      - pg_brin_bloom_summary
      - pg_brin_minmax_multi_summary
  auto_array_types:
    source_member: source_audit.catalog_sources.pg_type_dat
    derivation: Non-pseudo pg_type.dat records that declare array_type_oid; each element type has an automatically generated array type.
    declaration_rule: <element_type>[]
    count: 79
    inventory_sha256: 97a0c54b16e1020dc13e540fabe97fd59dff5c296c279aaebe398b06ed34c39b
    element_types:
      - bool
      - bytea
      - char
      - name
      - int8
      - int2
      - int2vector
      - int4
      - regproc
      - text
      - oid
      - tid
      - xid
      - cid
      - oidvector
      - pg_type
      - pg_attribute
      - pg_proc
      - pg_class
      - json
      - xml
      - xid8
      - point
      - lseg
      - path
      - box
      - polygon
      - float4
      - float8
      - circle
      - money
      - macaddr
      - inet
      - cidr
      - macaddr8
      - aclitem
      - bpchar
      - varchar
      - date
      - time
      - timestamp
      - timestamptz
      - interval
      - timetz
      - bit
      - varbit
      - numeric
      - refcursor
      - regprocedure
      - regoper
      - regoperator
      - regclass
      - regcollation
      - regtype
      - regrole
      - regnamespace
      - uuid
      - pg_lsn
      - tsvector
      - gtsvector
      - tsquery
      - regconfig
      - regdictionary
      - jsonb
      - jsonpath
      - txid_snapshot
      - pg_snapshot
      - int4range
      - numrange
      - tsrange
      - tstzrange
      - daterange
      - int8range
      - int4multirange
      - nummultirange
      - tsmultirange
      - tstzmultirange
      - datemultirange
      - int8multirange
  declaration_aliases:
    scope: SQL spellings or shorthands mapped to concrete pg_type identities
    count: 16
    inventory_sha256: 6a98d14a560cfa6758796766ac3d9014eace86eebe3154d4e4185a0cfa9a9329
    mappings:
      smallint: int2
      integer: int4
      bigint: int8
      smallserial: int2_with_sequence_default
      serial: int4_with_sequence_default
      bigserial: int8_with_sequence_default
      decimal: numeric
      real: float4
      double_precision: float8
      float: float4_or_float8_by_typmod
      character: bpchar
      character_varying: varchar
      boolean: bool
      timestamp_with_time_zone: timestamptz
      time_with_time_zone: timetz
      bit_varying: varbit
  typmod_profiles:
    completeness_basis: semantic declaration classes and valid/invalid boundaries, not every integer typmod value
    numeric:
      success: [NUMERIC, NUMERIC(1), NUMERIC(1000), "NUMERIC(10,0)", "NUMERIC(10,2)", "NUMERIC(10,-2)", "NUMERIC(1,1000)"]
      failure: [NUMERIC(0), NUMERIC(1001), "NUMERIC(10,-1001)", "NUMERIC(10,1001)"]
    character:
      success: [VARCHAR, VARCHAR(1), VARCHAR(10485760), CHARACTER, CHARACTER(1), CHARACTER(10485760)]
      failure: [VARCHAR(0), VARCHAR(10485761), CHARACTER(0), CHARACTER(10485761)]
    bit_string:
      success: [BIT, BIT(1), BIT(83886080), BIT VARYING, BIT VARYING(1), BIT VARYING(83886080)]
      failure: [BIT(0), BIT(83886081), BIT VARYING(0), BIT VARYING(83886081)]
    float:
      success: [FLOAT, FLOAT(1), FLOAT(24), FLOAT(25), FLOAT(53)]
      failure: [FLOAT(0), FLOAT(54)]
    datetime_precision:
      success: [TIME(0), TIME(6), TIMESTAMP(0), TIMESTAMP(6), INTERVAL(0), INTERVAL(6)]
      failure: [TIME(7), TIMESTAMP(7), INTERVAL(7)]
    interval_fields:
      success: [INTERVAL YEAR, INTERVAL MONTH, INTERVAL DAY, INTERVAL HOUR, INTERVAL MINUTE, INTERVAL SECOND, INTERVAL YEAR TO MONTH, INTERVAL DAY TO HOUR, INTERVAL DAY TO MINUTE, INTERVAL DAY TO SECOND, INTERVAL HOUR TO MINUTE, INTERVAL HOUR TO SECOND, INTERVAL MINUTE TO SECOND]
  typmod_declarations:
    completeness_scope: Every success and failure declaration in typmod_profiles, in family/status order.
    count: 60
    inventory_sha256: 80d2b6ded0f70c983e554c30ec0cd9473a1988981f309f96db6e52bf06a08d34
    values:
      - NUMERIC
      - NUMERIC(1)
      - NUMERIC(1000)
      - NUMERIC(10,0)
      - NUMERIC(10,2)
      - NUMERIC(10,-2)
      - NUMERIC(1,1000)
      - NUMERIC(0)
      - NUMERIC(1001)
      - NUMERIC(10,-1001)
      - NUMERIC(10,1001)
      - VARCHAR
      - VARCHAR(1)
      - VARCHAR(10485760)
      - CHARACTER
      - CHARACTER(1)
      - CHARACTER(10485760)
      - VARCHAR(0)
      - VARCHAR(10485761)
      - CHARACTER(0)
      - CHARACTER(10485761)
      - BIT
      - BIT(1)
      - BIT(83886080)
      - BIT VARYING
      - BIT VARYING(1)
      - BIT VARYING(83886080)
      - BIT(0)
      - BIT(83886081)
      - BIT VARYING(0)
      - BIT VARYING(83886081)
      - FLOAT
      - FLOAT(1)
      - FLOAT(24)
      - FLOAT(25)
      - FLOAT(53)
      - FLOAT(0)
      - FLOAT(54)
      - TIME(0)
      - TIME(6)
      - TIMESTAMP(0)
      - TIMESTAMP(6)
      - INTERVAL(0)
      - INTERVAL(6)
      - TIME(7)
      - TIMESTAMP(7)
      - INTERVAL(7)
      - INTERVAL YEAR
      - INTERVAL MONTH
      - INTERVAL DAY
      - INTERVAL HOUR
      - INTERVAL MINUTE
      - INTERVAL SECOND
      - INTERVAL YEAR TO MONTH
      - INTERVAL DAY TO HOUR
      - INTERVAL DAY TO MINUTE
      - INTERVAL DAY TO SECOND
      - INTERVAL HOUR TO MINUTE
      - INTERVAL HOUR TO SECOND
      - INTERVAL MINUTE TO SECOND
    expected_failure_values:
      - NUMERIC(0)
      - NUMERIC(1001)
      - NUMERIC(10,-1001)
      - NUMERIC(10,1001)
      - VARCHAR(0)
      - VARCHAR(10485761)
      - CHARACTER(0)
      - CHARACTER(10485761)
      - BIT(0)
      - BIT(83886081)
      - BIT VARYING(0)
      - BIT VARYING(83886081)
      - FLOAT(0)
      - FLOAT(54)
      - TIME(7)
      - TIMESTAMP(7)
      - INTERVAL(7)
  user_defined_archetypes:
    completeness_scope: PostgreSQL type-construction families, not every environment-specific type name
    count: 8
    inventory_sha256: d07ccce0cc897da904a968438d7887d7bc3ef40c47ce81d7dbd605c0ae5f08ba
    values:
      - enum
      - domain
      - composite
      - table_row_type
      - base_type
      - range
      - multirange
      - array_of_user_defined_type
    portable_without_external_binary_code:
      - enum
      - domain
      - composite
      - table_row_type
      - range
      - multirange
      - array_of_user_defined_type
    environment_required:
      - base_type
  type_categories:
    numeric: {}
    monetary: {}
    character: {}
    binary: {}
    datetime: {}
    boolean: {}
    enum: {}
    geometric: {}
    network: {}
    bit_string: {}
    text_search: {}
    uuid: {}
    xml: {}
    json: {}
    array: {}
    range: {}
    domain: {}
    composite: {}
    object_identifier: {}
    transaction_snapshot: {}
    pg_lsn: {}
    name: {}
  types:
    smallint:
      type_key: smallint
      type_category: numeric
      declaration_sql: SMALLINT
      sample_values:
        success:
          - "1"
        boundary:
          - "-32768"
          - "32767"
        failure:
          - "32768"
      requires_setup: &no_setup []
      index_capabilities: &ordered_scalar_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: true
        collation: false
        predicate_expression: true
      notes: &no_notes []
    integer:
      type_key: integer
      type_category: numeric
      declaration_sql: INTEGER
      sample_values:
        success:
          - "1"
        boundary:
          - "-2147483648"
          - "2147483647"
        failure:
          - "2147483648"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    bigint:
      type_key: bigint
      type_category: numeric
      declaration_sql: BIGINT
      sample_values:
        success:
          - "1"
        boundary:
          - "-9223372036854775808"
          - "9223372036854775807"
        failure:
          - "9223372036854775808"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    smallserial:
      type_key: smallserial
      type_category: numeric
      declaration_sql: SMALLSERIAL
      sample_values:
        success:
          - "DEFAULT"
          - "1"
        boundary:
          - "32767"
        failure:
          - "32768"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - SMALLSERIAL is declaration shorthand that creates a smallint column with a sequence-backed default.
        - It is not a standalone storage type after table creation.
    serial:
      type_key: serial
      type_category: numeric
      declaration_sql: SERIAL
      sample_values:
        success:
          - "DEFAULT"
          - "1"
        boundary:
          - "2147483647"
        failure:
          - "2147483648"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - SERIAL is declaration shorthand that creates an integer column with a sequence-backed default.
        - It is not a standalone storage type after table creation.
    bigserial:
      type_key: bigserial
      type_category: numeric
      declaration_sql: BIGSERIAL
      sample_values:
        success:
          - "DEFAULT"
          - "1"
        boundary:
          - "9223372036854775807"
        failure:
          - "9223372036854775808"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - BIGSERIAL is declaration shorthand that creates a bigint column with a sequence-backed default.
        - It is not a standalone storage type after table creation.
    numeric:
      type_key: numeric
      type_category: numeric
      declaration_sql: NUMERIC
      sample_values:
        success:
          - "123.45"
          - "'NaN'"
        boundary: []
        failure:
          - "'not_numeric'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - NUMERIC stores exact values with selectable precision and scale.
    decimal:
      type_key: decimal
      type_category: numeric
      declaration_sql: DECIMAL
      sample_values:
        success:
          - "123.45"
        boundary: []
        failure:
          - "'not_decimal'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - DECIMAL is equivalent to NUMERIC in PostgreSQL.
    real:
      type_key: real
      type_category: numeric
      declaration_sql: REAL
      sample_values:
        success:
          - "1.25"
          - "'NaN'"
        boundary: []
        failure:
          - "'not_real'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - REAL is inexact single precision floating point.
    double_precision:
      type_key: double_precision
      type_category: numeric
      declaration_sql: DOUBLE PRECISION
      sample_values:
        success:
          - "1.25"
          - "'Infinity'"
        boundary: []
        failure:
          - "'not_double'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - DOUBLE PRECISION is inexact double precision floating point.
    float:
      type_key: float
      type_category: numeric
      declaration_sql: FLOAT
      declaration_variants:
        success:
          - FLOAT
          - FLOAT(1)
          - FLOAT(24)
          - FLOAT(25)
          - FLOAT(53)
        failure:
          - FLOAT(0)
          - FLOAT(54)
      sample_values:
        success:
          - "1.25"
          - "'Infinity'"
          - "'NaN'"
        boundary: []
        failure:
          - "'not_float'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - FLOAT without precision is an alias for DOUBLE PRECISION in PostgreSQL 18.4.
        - FLOAT precision 1 through 24 selects REAL; precision 25 through 53 selects DOUBLE PRECISION.
    money:
      type_key: money
      type_category: monetary
      declaration_sql: MONEY
      sample_values:
        success:
          - "12.34"
        boundary: []
        failure:
          - "'not_money'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - MONEY input and output are locale-sensitive.
    character_varying:
      type_key: character_varying
      type_category: character
      declaration_sql: CHARACTER VARYING(32)
      sample_values:
        success:
          - "'alpha'"
        boundary:
          - "''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: &collatable_scalar_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: true
        collation: true
        predicate_expression: true
      notes:
        - Collation-sensitive comparisons depend on the column collation.
    character:
      type_key: character
      type_category: character
      declaration_sql: CHARACTER(8)
      sample_values:
        success:
          - "'alpha'"
        boundary:
          - "''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *collatable_scalar_index
      notes:
        - CHARACTER pads values to the declared length.
    bpchar:
      type_key: bpchar
      type_category: character
      declaration_sql: BPCHAR
      sample_values:
        success:
          - "'alpha'"
        boundary:
          - "''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *collatable_scalar_index
      notes:
        - BPCHAR is PostgreSQL's internal alias for blank-padded char.
    text:
      type_key: text
      type_category: character
      declaration_sql: TEXT
      sample_values:
        success:
          - "'alpha'"
        boundary:
          - "''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *collatable_scalar_index
      notes:
        - Collation-sensitive comparisons depend on the column collation.
    bytea:
      type_key: bytea
      type_category: binary
      declaration_sql: BYTEA
      sample_values:
        success:
          - "decode('DEADBEEF', 'hex')"
        boundary:
          - "decode('', 'hex')"
        failure:
          - "'not_hex'"
      requires_setup: *no_setup
      index_capabilities: &bytea_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - BYTEA has binary comparison support; keep BRIN false in this catalog unless a specific opclass is selected.
    timestamp:
      type_key: timestamp
      type_category: datetime
      declaration_sql: TIMESTAMP
      sample_values:
        success:
          - "'2024-01-01 12:34:56'"
        boundary: []
        failure:
          - "'not_timestamp'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    timestamp_with_time_zone:
      type_key: timestamp_with_time_zone
      type_category: datetime
      declaration_sql: TIMESTAMP WITH TIME ZONE
      sample_values:
        success:
          - "'2024-01-01 12:34:56+00'"
        boundary: []
        failure:
          - "'not_timestamptz'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - TIMESTAMP WITH TIME ZONE is stored in UTC and displayed according to TimeZone.
    date:
      type_key: date
      type_category: datetime
      declaration_sql: DATE
      sample_values:
        success:
          - "'2024-01-01'"
        boundary: []
        failure:
          - "'not_date'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    time:
      type_key: time
      type_category: datetime
      declaration_sql: TIME
      sample_values:
        success:
          - "'12:34:56'"
        boundary: []
        failure:
          - "'not_time'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    time_with_time_zone:
      type_key: time_with_time_zone
      type_category: datetime
      declaration_sql: TIME WITH TIME ZONE
      sample_values:
        success:
          - "'12:34:56+00'"
        boundary: []
        failure:
          - "'not_timetz'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    interval:
      type_key: interval
      type_category: datetime
      declaration_sql: INTERVAL
      sample_values:
        success:
          - "'1 day'"
        boundary:
          - "'infinity'"
          - "'-infinity'"
        failure:
          - "'not_interval'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - PostgreSQL 18 supports positive and negative infinity interval values; compare their text and ordering with the reference server.
    boolean:
      type_key: boolean
      type_category: boolean
      declaration_sql: BOOLEAN
      sample_values:
        success:
          - "TRUE"
          - "FALSE"
        boundary: []
        failure:
          - "'not_boolean'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes: *no_notes
    enum_type:
      type_key: enum_type
      type_category: enum
      declaration_sql: pgcf_mood
      sample_values:
        success:
          - "'ok'"
        boundary: []
        failure:
          - "'missing_label'"
      requires_setup:
        - "CREATE TYPE pgcf_mood AS ENUM ('sad', 'ok', 'happy');"
      index_capabilities: &enum_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - Enumerated types require CREATE TYPE before table creation.
        - Ordering follows the label order declared by CREATE TYPE.
    point:
      type_key: point
      type_category: geometric
      declaration_sql: POINT
      sample_values:
        success:
          - "'(1,2)'"
        boundary: []
        failure:
          - "'not_point'"
      requires_setup: *no_setup
      index_capabilities: &geometric_gist_index
        btree: false
        btree_unique: false
        hash: false
        gist: true
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - Geometric indexing uses spatial operator classes; this catalog does not mark generic btree or hash support.
    line:
      type_key: line
      type_category: geometric
      declaration_sql: LINE
      sample_values:
        success:
          - "'{1,-1,0}'"
        boundary: []
        failure:
          - "'not_line'"
      requires_setup: *no_setup
      index_capabilities: &no_index
        btree: false
        btree_unique: false
        hash: false
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - Conservative catalog entry; verify a concrete operator class before generating index cases.
    lseg:
      type_key: lseg
      type_category: geometric
      declaration_sql: LSEG
      sample_values:
        success:
          - "'[(0,0),(1,1)]'"
        boundary: []
        failure:
          - "'not_lseg'"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - Conservative catalog entry; verify a concrete operator class before generating index cases.
    box:
      type_key: box
      type_category: geometric
      declaration_sql: BOX
      sample_values:
        success:
          - "'((0,0),(1,1))'"
        boundary: []
        failure:
          - "'not_box'"
      requires_setup: *no_setup
      index_capabilities: *geometric_gist_index
      notes:
        - Geometric indexing uses spatial operator classes; this catalog does not mark generic btree or hash support.
    path:
      type_key: path
      type_category: geometric
      declaration_sql: PATH
      sample_values:
        success:
          - "'[(0,0),(1,1),(2,0)]'"
        boundary: []
        failure:
          - "'not_path'"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - Conservative catalog entry; verify a concrete operator class before generating index cases.
    polygon:
      type_key: polygon
      type_category: geometric
      declaration_sql: POLYGON
      sample_values:
        success:
          - "'((0,0),(1,1),(2,0))'"
        boundary: []
        failure:
          - "'not_polygon'"
      requires_setup: *no_setup
      index_capabilities: *geometric_gist_index
      notes:
        - Geometric indexing uses spatial operator classes; this catalog does not mark generic btree or hash support.
    circle:
      type_key: circle
      type_category: geometric
      declaration_sql: CIRCLE
      sample_values:
        success:
          - "'<(0,0),1>'"
        boundary: []
        failure:
          - "'not_circle'"
      requires_setup: *no_setup
      index_capabilities: *geometric_gist_index
      notes:
        - Geometric indexing uses spatial operator classes; this catalog does not mark generic btree or hash support.
    cidr:
      type_key: cidr
      type_category: network
      declaration_sql: CIDR
      sample_values:
        success:
          - "'192.168.0.0/24'"
        boundary: []
        failure:
          - "'192.168.0.1/24'"
      requires_setup: *no_setup
      index_capabilities: &network_index
        btree: true
        btree_unique: true
        hash: true
        gist: true
        spgist: true
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - CIDR requires network bits to be zero to the right of the mask.
    inet:
      type_key: inet
      type_category: network
      declaration_sql: INET
      sample_values:
        success:
          - "'192.168.0.1/24'"
        boundary: []
        failure:
          - "'not_inet'"
      requires_setup: *no_setup
      index_capabilities: *network_index
      notes:
        - INET stores host addresses with an optional subnet mask.
    macaddr:
      type_key: macaddr
      type_category: network
      declaration_sql: MACADDR
      sample_values:
        success:
          - "'08:00:2b:01:02:03'"
        boundary: []
        failure:
          - "'not_macaddr'"
      requires_setup: *no_setup
      index_capabilities: &mac_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes: *no_notes
    macaddr8:
      type_key: macaddr8
      type_category: network
      declaration_sql: MACADDR8
      sample_values:
        success:
          - "'08:00:2b:01:02:03:04:05'"
        boundary: []
        failure:
          - "'not_macaddr8'"
      requires_setup: *no_setup
      index_capabilities: *mac_index
      notes: *no_notes
    bit:
      type_key: bit
      type_category: bit_string
      declaration_sql: BIT(8)
      sample_values:
        success:
          - "B'10101010'"
        boundary: []
        failure:
          - "B'101'"
      requires_setup: *no_setup
      index_capabilities: &bit_string_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - BIT enforces the declared bit length.
    bit_varying:
      type_key: bit_varying
      type_category: bit_string
      declaration_sql: BIT VARYING(16)
      sample_values:
        success:
          - "B'1010'"
        boundary:
          - "B''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *bit_string_index
      notes:
        - BIT VARYING allows variable-length bit strings up to the declared maximum.
    tsvector:
      type_key: tsvector
      type_category: text_search
      declaration_sql: TSVECTOR
      sample_values:
        success:
          - "'a fat cat sat'::tsvector"
        boundary: []
        failure:
          - "'unterminated:1A'::tsvector"
      requires_setup: *no_setup
      index_capabilities: &text_search_doc_index
        btree: false
        btree_unique: false
        hash: false
        gist: true
        spgist: false
        gin: true
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - Full text search documents are commonly indexed with GIN or GiST for match operations.
    tsquery:
      type_key: tsquery
      type_category: text_search
      declaration_sql: TSQUERY
      sample_values:
        success:
          - "'cat & rat'::tsquery"
        boundary: []
        failure:
          - "'cat &'::tsquery"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - TSQUERY represents search queries; index support is normally on TSVECTOR columns, not TSQUERY columns.
    uuid:
      type_key: uuid
      type_category: uuid
      declaration_sql: UUID
      sample_values:
        success:
          - "'9c36adc1-7fb5-4d5b-83b4-90356a46061a'"
          - "uuidv4()"
          - "uuidv7()"
        boundary: []
        failure:
          - "'not_uuid'"
      requires_setup: *no_setup
      index_capabilities: *ordered_scalar_index
      notes:
        - PostgreSQL 18 follows RFC 9562 and provides native UUIDv4 and UUIDv7 generation.
        - Validate version bits, uniqueness, ordering behavior, and exact reference parity without assuming generated values are deterministic.
    xml:
      type_key: xml
      type_category: xml
      declaration_sql: XML
      sample_values:
        success:
          - "XMLPARSE(CONTENT '<a>1</a>')"
        boundary: []
        failure:
          - "XMLPARSE(DOCUMENT '<a>')"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - XML lacks generic equality ordering in this conservative catalog.
    json:
      type_key: json
      type_category: json
      declaration_sql: JSON
      sample_values:
        success:
          - "'{\"a\": 1}'"
        boundary:
          - "'null'"
        failure:
          - "'{bad json}'"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - JSON stores textual JSON and does not have the jsonb indexing operator classes.
    jsonb:
      type_key: jsonb
      type_category: json
      declaration_sql: JSONB
      sample_values:
        success:
          - "'{\"a\": 1}'::jsonb"
        boundary:
          - "'null'::jsonb"
        failure:
          - "'{bad json}'::jsonb"
      requires_setup: *no_setup
      index_capabilities: &jsonb_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: true
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - JSONB supports GIN indexing for containment and jsonpath match operators.
        - B-tree and hash support are primarily useful for equality and ordering semantics, not document search.
    jsonpath:
      type_key: jsonpath
      type_category: json
      declaration_sql: JSONPATH
      sample_values:
        success:
          - "'$.a'"
        boundary: []
        failure:
          - "'$ ? ('"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - JSONPATH values define path expressions; JSONB columns are the usual indexed search target.
    integer_array:
      type_key: integer_array
      type_category: array
      declaration_sql: INTEGER[]
      sample_values:
        success:
          - "ARRAY[1, 2]"
        boundary:
          - "ARRAY[]::INTEGER[]"
        failure:
          - "ARRAY['not_int']"
      requires_setup: *no_setup
      index_capabilities: &array_index
        btree: true
        btree_unique: true
        hash: false
        gist: false
        spgist: false
        gin: true
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    text_array:
      type_key: text_array
      type_category: array
      declaration_sql: TEXT[]
      sample_values:
        success:
          - "ARRAY['a', 'b']"
        boundary:
          - "ARRAY[]::TEXT[]"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *array_index
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    varchar_array:
      type_key: varchar_array
      type_category: array
      declaration_sql: VARCHAR(32)[]
      sample_values:
        success:
          - "ARRAY['a', 'b']::VARCHAR(32)[]"
        boundary:
          - "ARRAY[]::VARCHAR(32)[]"
        failure: []
      requires_setup: *no_setup
      index_capabilities: *array_index
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    numeric_array:
      type_key: numeric_array
      type_category: array
      declaration_sql: NUMERIC[]
      sample_values:
        success:
          - "ARRAY[1.1, 2.2]::NUMERIC[]"
        boundary:
          - "ARRAY[]::NUMERIC[]"
        failure:
          - "ARRAY['not_numeric']"
      requires_setup: *no_setup
      index_capabilities: *array_index
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    timestamp_array:
      type_key: timestamp_array
      type_category: array
      declaration_sql: TIMESTAMP[]
      sample_values:
        success:
          - "ARRAY['2024-01-01 00:00:00'::timestamp]"
        boundary:
          - "ARRAY[]::TIMESTAMP[]"
        failure:
          - "ARRAY['not_timestamp']"
      requires_setup: *no_setup
      index_capabilities: *array_index
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    jsonb_array:
      type_key: jsonb_array
      type_category: array
      declaration_sql: JSONB[]
      sample_values:
        success:
          - "ARRAY['{\"a\": 1}'::jsonb]"
        boundary:
          - "ARRAY[]::JSONB[]"
        failure:
          - "ARRAY['{bad json}'::jsonb]"
      requires_setup: *no_setup
      index_capabilities: *array_index
      notes:
        - Arrays support GIN indexing for containment-style operators.
        - B-tree ordering depends on the element type's comparison support.
    int4range:
      type_key: int4range
      type_category: range
      declaration_sql: INT4RANGE
      sample_values:
        success:
          - "'[1,10)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: &range_index
        btree: true
        btree_unique: true
        hash: true
        gist: true
        spgist: true
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    int8range:
      type_key: int8range
      type_category: range
      declaration_sql: INT8RANGE
      sample_values:
        success:
          - "'[1,10)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: *range_index
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    numrange:
      type_key: numrange
      type_category: range
      declaration_sql: NUMRANGE
      sample_values:
        success:
          - "'[1.1,10.5)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: *range_index
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    tsrange:
      type_key: tsrange
      type_category: range
      declaration_sql: TSRANGE
      sample_values:
        success:
          - "'[2024-01-01 00:00,2024-01-02 00:00)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: *range_index
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    tstzrange:
      type_key: tstzrange
      type_category: range
      declaration_sql: TSTZRANGE
      sample_values:
        success:
          - "'[2024-01-01 00:00+00,2024-01-02 00:00+00)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: *range_index
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    daterange:
      type_key: daterange
      type_category: range
      declaration_sql: DATERANGE
      sample_values:
        success:
          - "'[2024-01-01,2024-02-01)'"
        boundary:
          - "'empty'"
        failure:
          - "'not_range'"
      requires_setup: *no_setup
      index_capabilities: *range_index
      notes:
        - PostgreSQL documents GiST and SP-GiST support for range columns.
        - B-tree and hash support are mainly useful for equality or internal ordering, not general range search.
    int4multirange:
      type_key: int4multirange
      type_category: range
      declaration_sql: INT4MULTIRANGE
      sample_values:
        success:
          - "'{[1,3),[5,8)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: &multirange_index
        btree: false
        btree_unique: false
        hash: false
        gist: true
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    int8multirange:
      type_key: int8multirange
      type_category: range
      declaration_sql: INT8MULTIRANGE
      sample_values:
        success:
          - "'{[1,3),[5,8)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: *multirange_index
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    nummultirange:
      type_key: nummultirange
      type_category: range
      declaration_sql: NUMMULTIRANGE
      sample_values:
        success:
          - "'{[1.1,3.3),[5.5,8.8)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: *multirange_index
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    tsmultirange:
      type_key: tsmultirange
      type_category: range
      declaration_sql: TSMULTIRANGE
      sample_values:
        success:
          - "'{[2024-01-01 00:00,2024-01-02 00:00)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: *multirange_index
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    tstzmultirange:
      type_key: tstzmultirange
      type_category: range
      declaration_sql: TSTZMULTIRANGE
      sample_values:
        success:
          - "'{[2024-01-01 00:00+00,2024-01-02 00:00+00)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: *multirange_index
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    datemultirange:
      type_key: datemultirange
      type_category: range
      declaration_sql: DATEMULTIRANGE
      sample_values:
        success:
          - "'{[2024-01-01,2024-02-01)}'"
        boundary:
          - "'{}'"
        failure:
          - "'not_multirange'"
      requires_setup: *no_setup
      index_capabilities: *multirange_index
      notes:
        - PostgreSQL documents GiST support for multirange columns.
        - This catalog keeps B-tree and hash false for multiranges unless a specific opclass is selected.
    domain_type:
      type_key: domain_type
      type_category: domain
      declaration_sql: pgcf_positive_integer
      sample_values:
        success:
          - "1"
        boundary: []
        failure:
          - "0"
      requires_setup:
        - "CREATE DOMAIN pgcf_positive_integer AS INTEGER CHECK (VALUE > 0);"
      index_capabilities: *ordered_scalar_index
      notes:
        - Domain types require CREATE DOMAIN before table creation.
        - Index capabilities follow the domain's base type when the selected operator class supports it.
    composite_type:
      type_key: composite_type
      type_category: composite
      declaration_sql: pgcf_address
      sample_values:
        success:
          - "ROW('Paris', 75001)::pgcf_address"
        boundary: []
        failure:
          - "ROW('Paris')::pgcf_address"
      requires_setup:
        - "CREATE TYPE pgcf_address AS (city TEXT, zip INTEGER);"
      index_capabilities: *no_index
      notes:
        - Composite types require CREATE TYPE before table creation.
        - This catalog keeps generic indexes false; prefer expression indexes on composite fields.
    oid:
      type_key: oid
      type_category: object_identifier
      declaration_sql: OID
      sample_values:
        success:
          - "1"
        boundary: []
        failure:
          - "'not_oid'"
      requires_setup: *no_setup
      index_capabilities: &object_identifier_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - OID is an unsigned four-byte object identifier used by PostgreSQL system catalogs.
    regclass:
      type_key: regclass
      type_category: object_identifier
      declaration_sql: REGCLASS
      sample_values:
        success:
          - "'pg_type'::regclass"
        boundary: []
        failure:
          - "'missing_relation'::regclass"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGCLASS is an OID alias type with specialized relation-name input and output.
    regcollation:
      type_key: regcollation
      type_category: object_identifier
      declaration_sql: REGCOLLATION
      sample_values:
        success:
          - "'\"POSIX\"'::regcollation"
        boundary: []
        failure:
          - "'missing_collation'::regcollation"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGCOLLATION is an OID alias type with specialized collation-name input and output.
    regconfig:
      type_key: regconfig
      type_category: object_identifier
      declaration_sql: REGCONFIG
      sample_values:
        success:
          - "'english'::regconfig"
        boundary: []
        failure:
          - "'missing_config'::regconfig"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGCONFIG is an OID alias type with specialized text search configuration input and output.
    regdictionary:
      type_key: regdictionary
      type_category: object_identifier
      declaration_sql: REGDICTIONARY
      sample_values:
        success:
          - "'simple'::regdictionary"
        boundary: []
        failure:
          - "'missing_dictionary'::regdictionary"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGDICTIONARY is an OID alias type with specialized text search dictionary input and output.
    regnamespace:
      type_key: regnamespace
      type_category: object_identifier
      declaration_sql: REGNAMESPACE
      sample_values:
        success:
          - "'pg_catalog'::regnamespace"
        boundary: []
        failure:
          - "'missing_schema'::regnamespace"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGNAMESPACE is an OID alias type with specialized namespace input and output.
    regoper:
      type_key: regoper
      type_category: object_identifier
      declaration_sql: REGOPER
      sample_values:
        success:
          - "'+'::regoper"
        boundary: []
        failure:
          - "'missing_operator'::regoper"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGOPER is an OID alias type for operator names.
        - PostgreSQL documents that overloaded operators are better represented with REGOPERATOR.
    regoperator:
      type_key: regoperator
      type_category: object_identifier
      declaration_sql: REGOPERATOR
      sample_values:
        success:
          - "'+(integer,integer)'::regoperator"
        boundary: []
        failure:
          - "'missing_operator(integer,integer)'::regoperator"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGOPERATOR is an OID alias type for operators with argument types.
    regproc:
      type_key: regproc
      type_category: object_identifier
      declaration_sql: REGPROC
      sample_values:
        success:
          - "'now'::regproc"
        boundary: []
        failure:
          - "'missing_function'::regproc"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGPROC is an OID alias type for function names.
        - PostgreSQL documents that overloaded functions are better represented with REGPROCEDURE.
    regprocedure:
      type_key: regprocedure
      type_category: object_identifier
      declaration_sql: REGPROCEDURE
      sample_values:
        success:
          - "'sum(integer)'::regprocedure"
        boundary: []
        failure:
          - "'missing_function(integer)'::regprocedure"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGPROCEDURE is an OID alias type for functions with argument types.
    regrole:
      type_key: regrole
      type_category: object_identifier
      declaration_sql: REGROLE
      sample_values:
        success:
          - "'pg_monitor'::regrole"
        boundary: []
        failure:
          - "'missing_role'::regrole"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGROLE is an OID alias type for role names.
        - PostgreSQL documents that REGROLE constants are not allowed in stored expressions that create dependencies.
    regtype:
      type_key: regtype
      type_category: object_identifier
      declaration_sql: REGTYPE
      sample_values:
        success:
          - "'integer'::regtype"
        boundary: []
        failure:
          - "'missing_type'::regtype"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - REGTYPE is an OID alias type for data type names.
    xid:
      type_key: xid
      type_category: object_identifier
      declaration_sql: XID
      sample_values:
        success:
          - "'1'::xid"
        boundary: []
        failure:
          - "'not_xid'::xid"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - XID is a 32-bit transaction identifier used by system columns such as xmin and xmax.
    xid8:
      type_key: xid8
      type_category: object_identifier
      declaration_sql: XID8
      sample_values:
        success:
          - "'1'::xid8"
        boundary: []
        failure:
          - "'not_xid8'::xid8"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - XID8 is the 64-bit transaction identifier variant documented by PostgreSQL.
    cid:
      type_key: cid
      type_category: object_identifier
      declaration_sql: CID
      sample_values:
        success:
          - "'0'::cid"
        boundary: []
        failure:
          - "'not_cid'::cid"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - CID is a 32-bit command identifier used by cmin and cmax system columns.
    tid:
      type_key: tid
      type_category: object_identifier
      declaration_sql: TID
      sample_values:
        success:
          - "'(0,1)'"
        boundary: []
        failure:
          - "'not_tid'"
      requires_setup: *no_setup
      index_capabilities: *object_identifier_index
      notes:
        - TID is the tuple identifier type used by the ctid system column.
    pg_lsn:
      type_key: pg_lsn
      type_category: pg_lsn
      declaration_sql: PG_LSN
      sample_values:
        success:
          - "'0/16B6C50'"
        boundary: []
        failure:
          - "'not_lsn'"
      requires_setup: *no_setup
      index_capabilities: &pg_lsn_index
        btree: true
        btree_unique: true
        hash: false
        gist: false
        spgist: false
        gin: false
        brin: true
        collation: false
        predicate_expression: true
      notes:
        - PG_LSN stores PostgreSQL Log Sequence Numbers.
    pg_snapshot:
      type_key: pg_snapshot
      type_category: transaction_snapshot
      declaration_sql: PG_SNAPSHOT
      sample_values:
        success:
          - "pg_current_snapshot()"
        boundary: []
        failure:
          - "'not_snapshot'::pg_snapshot"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - PG_SNAPSHOT stores user-level transaction ID snapshots.
        - This catalog keeps generic indexes false for transaction snapshot values.
    txid_snapshot:
      type_key: txid_snapshot
      type_category: transaction_snapshot
      declaration_sql: TXID_SNAPSHOT
      sample_values:
        success:
          - "'1:2:'::txid_snapshot"
        boundary: []
        failure:
          - "'not_snapshot'::txid_snapshot"
      requires_setup: *no_setup
      index_capabilities: *no_index
      notes:
        - TXID_SNAPSHOT is deprecated in PostgreSQL 18.4; prefer PG_SNAPSHOT.
    name:
      type_key: name
      type_category: name
      declaration_sql: NAME
      sample_values:
        success:
          - "'pg_type'"
        boundary:
          - "''"
        failure: []
      requires_setup: *no_setup
      index_capabilities: &name_index
        btree: true
        btree_unique: true
        hash: true
        gist: false
        spgist: false
        gin: false
        brin: false
        collation: false
        predicate_expression: true
      notes:
        - NAME is PostgreSQL's internal identifier-name type with fixed maximum length.
  pseudo_types:
    source_member: source_audit.catalog_sources.pg_type_dat
    derivation: Every explicit pg_type.dat record whose typtype is p, in source order.
    count: 26
    inventory_sha256: e12bc3225ac03af3718b1a15b2af18c14d946ea9e79ab2ef2aabb2b9b265d0ea
    allowed_as_table_columns: false
    values:
      - pg_ddl_command
      - unknown
      - record
      - _record
      - cstring
      - any
      - anyarray
      - void
      - trigger
      - event_trigger
      - language_handler
      - internal
      - anyelement
      - anynonarray
      - anyenum
      - fdw_handler
      - index_am_handler
      - tsm_handler
      - table_am_handler
      - anyrange
      - anycompatible
      - anycompatiblearray
      - anycompatiblenonarray
      - anycompatiblerange
      - anymultirange
      - anycompatiblemultirange
    notes:
      - PostgreSQL 18.4 documents pseudo-types as function argument or result markers, not table column data types.
```
