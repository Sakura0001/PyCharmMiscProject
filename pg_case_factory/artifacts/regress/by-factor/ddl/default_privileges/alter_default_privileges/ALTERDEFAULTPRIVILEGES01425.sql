-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DEFAULT PRIVILEGES conditional product: action_mode=revoke_plain_cascade, actor=superuser, for_scope=user_single, object_class=SEQUENCES, operation=revoke, privilege_binding=public, privilege_sql=USAGE, recipient=public, schema_scope=multiple, schema_shape=simple_id, target_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDEFAULTPRIVILEGES01425
-- source_md: skills/pg-sql-generation/references/statements/ddl/default_privileges/alter_default_privileges.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/default_privileges/alter_default_privileges.yaml
-- factor_values: operation_type=revoke, revoke_grant_option_for=omitted, revoke_cascade_restrict=cascade, object_class=SEQUENCES, privilege_set=public, for_role_clause=for_user_keyword, target_role_name_shape=simple_id, nonexistent_target_role=role_exists, in_schema_clause=multiple_schemas, schema_name_shape=simple_id, schema_existence=schema_exists, nonexistent_schema=schema_exists, in_schema_on_schemas=no_conflict, recipient_role_name_shape=public, group_keyword=omitted, role_existence=role_exists, privilege_level=superuser, privilege_denied=authorized_success, role_not_member_of_target_role=is_member, additive_vs_overriding=per_schema_additive, cannot_revoke_global_from_per_schema=valid_revoke, expected_status=success, verification_mode=catalog_query_pg_default_acl, cleanup_mode=drop_schema
-- derived_axes: action_mode=revoke_plain_cascade, actor=superuser, expected_sqlstate=00000, for_scope=user_single, object_class=SEQUENCES, operation=revoke, privilege_binding=public, privilege_sql=USAGE, recipient=public, schema_scope=multiple, schema_shape=simple_id, target_shape=simple_id
-- combination_strategy: full conditional product: class/privilege × action modifiers × FOR scope × applicable schema scope
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000; pg_default_acl, future-object, and cleanup oracles

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session profile is applied after table-first pre-cleanup.

-- 3. Idempotent pre-cleanup.
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS prior_large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900001425::oid, 910001425::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_scope_schema CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_01425_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_intruder;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_target_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_target_role;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_group_role;

-- 4. Roles, schemas, membership, and complete fixture structures.
SET client_min_messages TO warning;
SET search_path TO pg_catalog, public;
CREATE ROLE alterdefaultprivileges_01425_member_actor;
CREATE ROLE alterdefaultprivileges_01425_intruder;
CREATE ROLE alterdefaultprivileges_01425_target_role;
CREATE SCHEMA alterdefaultprivileges_01425_scope_schema;
CREATE SCHEMA alterdefaultprivileges_01425_scope_schema_two;
CREATE SCHEMA alterdefaultprivileges_01425_other_schema;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_01425_other_schema TO alterdefaultprivileges_01425_member_actor;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_01425_other_schema TO alterdefaultprivileges_01425_target_role;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_01425_scope_schema TO alterdefaultprivileges_01425_target_role;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_01425_scope_schema_two TO alterdefaultprivileges_01425_target_role;

-- 5. Revoke fixtures establish a real privilege to remove.
-- setup-only ALTER DEFAULT PRIVILEGES; coverage_credit=false
ALTER DEFAULT PRIVILEGES FOR USER alterdefaultprivileges_01425_target_role IN SCHEMA alterdefaultprivileges_01425_scope_schema, alterdefaultprivileges_01425_scope_schema_two GRANT USAGE ON SEQUENCES TO PUBLIC;

-- 6. Capture the exact pg_default_acl state before the primary target.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role')
      AND d.defaclnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alterdefaultprivileges_01425_scope_schema')
      AND d.defaclobjtype = 'S'
    ORDER BY d.oid
    LIMIT 1
), '<NONE>') AS before_default_acl
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_default_acl;
\gset

-- 7. Select the authorized or deliberately unauthorized executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER DEFAULT PRIVILEGES FOR USER alterdefaultprivileges_01425_target_role IN SCHEMA alterdefaultprivileges_01425_scope_schema, alterdefaultprivileges_01425_scope_schema_two REVOKE USAGE ON SEQUENCES FROM PUBLIC CASCADE;
\set adp_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'adp_sqlstate' = '00000' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog and future-object semantic verification.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role')
      AND d.defaclnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alterdefaultprivileges_01425_scope_schema')
      AND d.defaclobjtype = 'S'
    ORDER BY d.oid
    LIMIT 1
), '<NONE>') AS after_default_acl
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY after_default_acl;
\gset
SELECT :'after_default_acl' IS NOT NULL AS default_acl_catalog_observed;
SELECT
    pg_catalog.pg_get_userbyid(d.defaclrole)::text AS default_acl_role,
    COALESCE(n.nspname, '<GLOBAL>')::text AS default_acl_schema,
    d.defaclobjtype::text AS default_acl_object_type,
    pg_catalog.array_to_string(d.defaclacl, ',')::text AS default_acl_text
FROM pg_catalog.pg_default_acl AS d
LEFT JOIN pg_catalog.pg_namespace AS n ON n.oid = d.defaclnamespace
WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role')
ORDER BY default_acl_role, default_acl_schema, default_acl_object_type, default_acl_text;
SET ROLE alterdefaultprivileges_01425_target_role;
CREATE SEQUENCE alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_sequence START WITH 101 INCREMENT BY 7 MINVALUE 1 CACHE 5;
RESET ROLE;
SELECT
    COALESCE(pg_catalog.bool_or(
        acl.grantee = 0::oid
        AND acl.privilege_type = 'USAGE'
    ), false) = false AS direct_acl_privilege_matches,
    COALESCE(pg_catalog.bool_or(
        acl.grantee = 0::oid
        AND acl.privilege_type = 'USAGE'
        AND acl.is_grantable
    ), false) = false AS direct_acl_grant_option_matches
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(
        c.relacl,
        pg_catalog.acldefault('S'::"char", c.relowner)
    )
) AS acl
WHERE n.nspname = 'alterdefaultprivileges_01425_scope_schema'
  AND c.relname = 'alterdefaultprivileges_01425_future_sequence'
  AND c.relkind = 'S'
ORDER BY direct_acl_privilege_matches, direct_acl_grant_option_matches;

-- 11. Reverse default ACL changes and remove created objects/roles.
RESET ROLE;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900001425::oid, 910001425::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_01425_scope_schema.alterdefaultprivileges_01425_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_01425_scope_schema CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_target_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_01425_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_01425_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_intruder;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_target_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_target_role;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_01425_group_role;

-- 12. Cleanup oracle; table cases end with an idempotent table DROP.
SELECT
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_roles AS r
        WHERE r.rolname IN ('alterdefaultprivileges_01425_member_actor', 'alterdefaultprivileges_01425_intruder', 'alterdefaultprivileges_01425_target_role_two', 'alterdefaultprivileges_01425_target_role', 'alterdefaultprivileges_01425_recipient_role_two', 'alterdefaultprivileges_01425_recipient_role', 'alterdefaultprivileges_01425_group_role')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace AS n
        WHERE n.nspname IN ('alterdefaultprivileges_01425_scope_schema', 'alterdefaultprivileges_01425_scope_schema_two', 'alterdefaultprivileges_01425_other_schema', 'alterdefaultprivileges_01425_future_schema')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_default_acl AS d
        WHERE pg_catalog.array_to_string(d.defaclacl, ',') LIKE '%alterdefaultprivileges_01425_%'
    ) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;
