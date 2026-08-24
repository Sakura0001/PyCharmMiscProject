-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DEFAULT PRIVILEGES conditional product: action_mode=revoke_option_restrict, actor=superuser, for_scope=omitted, object_class=LARGE_OBJECTS, operation=revoke, privilege_binding=single_privilege, privilege_sql=SELECT, recipient=simple, schema_scope=multiple
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDEFAULTPRIVILEGES03824
-- source_md: skills/pg-sql-generation/references/statements/ddl/default_privileges/alter_default_privileges.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/default_privileges/alter_default_privileges.yaml
-- factor_values: operation_type=revoke, revoke_grant_option_for=grant_option_for, revoke_cascade_restrict=restrict, object_class=LARGE_OBJECTS, privilege_set=single_privilege, for_role_clause=omitted_current_role, nonexistent_target_role=role_exists, in_schema_clause=not_allowed_for_schemas_class, schema_name_shape=simple_id, schema_existence=schema_exists, nonexistent_schema=schema_exists, in_schema_on_schemas=in_schema_with_schemas_class, recipient_role_name_shape=simple_id, group_keyword=omitted, role_existence=role_exists, privilege_level=superuser, privilege_denied=authorized_success, role_not_member_of_target_role=is_member, expected_status=failure, verification_mode=error_assertion, cleanup_mode=drop_role_owned_by
-- derived_axes: action_mode=revoke_option_restrict, actor=superuser, expected_sqlstate=0LP01, for_scope=omitted, object_class=LARGE_OBJECTS, operation=revoke, privilege_binding=single_privilege, privilege_sql=SELECT, recipient=simple, schema_scope=multiple
-- combination_strategy: action modifier(8) × forbidden class(2) × schema cardinality(2)
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 0LP01; pg_default_acl, future-object, and cleanup oracles

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session profile is applied after table-first pre-cleanup.

-- 3. Idempotent pre-cleanup.
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS prior_large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900003824::oid, 910003824::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_scope_schema CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_target_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_target_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_03824_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_intruder;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_target_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_target_role;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_group_role;

-- 4. Roles, schemas, membership, and complete fixture structures.
SET client_min_messages TO warning;
SET search_path TO pg_catalog, public;
CREATE ROLE alterdefaultprivileges_03824_member_actor;
CREATE ROLE alterdefaultprivileges_03824_intruder;
CREATE ROLE alterdefaultprivileges_03824_recipient_role;
CREATE SCHEMA alterdefaultprivileges_03824_scope_schema;
CREATE SCHEMA alterdefaultprivileges_03824_scope_schema_two;
CREATE SCHEMA alterdefaultprivileges_03824_other_schema;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_03824_other_schema TO alterdefaultprivileges_03824_member_actor;

-- 5. Revoke fixtures establish a real privilege to remove.

-- 6. Capture the exact pg_default_acl state before the primary target.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = CURRENT_USER)
      AND d.defaclnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alterdefaultprivileges_03824_scope_schema')
      AND d.defaclobjtype = 'L'
    ORDER BY d.oid
    LIMIT 1
), '<NONE>') AS before_default_acl
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_default_acl;
\gset

-- 7. Select the authorized or deliberately unauthorized executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER DEFAULT PRIVILEGES IN SCHEMA alterdefaultprivileges_03824_scope_schema, alterdefaultprivileges_03824_scope_schema_two REVOKE GRANT OPTION FOR SELECT ON LARGE OBJECTS FROM alterdefaultprivileges_03824_recipient_role RESTRICT;
\set adp_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'adp_sqlstate' = '0LP01' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog and future-object semantic verification.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = CURRENT_USER)
      AND d.defaclnamespace = (SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = 'alterdefaultprivileges_03824_scope_schema')
      AND d.defaclobjtype = 'L'
    ORDER BY d.oid
    LIMIT 1
), '<NONE>') AS after_default_acl
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY after_default_acl;
\gset
SELECT :'after_default_acl' = :'before_default_acl' AS default_acl_unchanged_after_failure_or_rollback;
SELECT
    pg_catalog.pg_get_userbyid(d.defaclrole)::text AS default_acl_role,
    COALESCE(n.nspname, '<GLOBAL>')::text AS default_acl_schema,
    d.defaclobjtype::text AS default_acl_object_type,
    pg_catalog.array_to_string(d.defaclacl, ',')::text AS default_acl_text
FROM pg_catalog.pg_default_acl AS d
LEFT JOIN pg_catalog.pg_namespace AS n ON n.oid = d.defaclnamespace
WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = CURRENT_USER)
ORDER BY default_acl_role, default_acl_schema, default_acl_object_type, default_acl_text;

-- 11. Reverse default ACL changes and remove created objects/roles.
RESET ROLE;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900003824::oid, 910003824::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_03824_scope_schema.alterdefaultprivileges_03824_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_03824_scope_schema CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_target_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_target_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_03824_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_03824_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_intruder;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_target_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_target_role;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_03824_group_role;

-- 12. Cleanup oracle; table cases end with an idempotent table DROP.
SELECT
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_roles AS r
        WHERE r.rolname IN ('alterdefaultprivileges_03824_member_actor', 'alterdefaultprivileges_03824_intruder', 'alterdefaultprivileges_03824_target_role_two', 'alterdefaultprivileges_03824_target_role', 'alterdefaultprivileges_03824_recipient_role_two', 'alterdefaultprivileges_03824_recipient_role', 'alterdefaultprivileges_03824_group_role')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace AS n
        WHERE n.nspname IN ('alterdefaultprivileges_03824_scope_schema', 'alterdefaultprivileges_03824_scope_schema_two', 'alterdefaultprivileges_03824_other_schema', 'alterdefaultprivileges_03824_future_schema')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_default_acl AS d
        WHERE pg_catalog.array_to_string(d.defaclacl, ',') LIKE '%alterdefaultprivileges_03824_%'
    ) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;
