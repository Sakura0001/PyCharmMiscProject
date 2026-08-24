-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : ALTER DEFAULT PRIVILEGES conditional product: action_mode=grant_with_option, actor=superuser, for_scope=role_multiple, object_class=TABLES, operation=grant, privilege_binding=all_privileges, privilege_sql=ALL PRIVILEGES, recipient=group_role, schema_scope=omitted, schema_shape=not_applicable, target_shape=quoted_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERDEFAULTPRIVILEGES00370
-- source_md: skills/pg-sql-generation/references/statements/ddl/default_privileges/alter_default_privileges.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/default_privileges/alter_default_privileges.yaml
-- factor_values: operation_type=grant, grant_option=with_grant_option, object_class=TABLES, privilege_set=all_privileges, for_role_clause=multiple_target_roles, target_role_name_shape=quoted_id, nonexistent_target_role=role_exists, in_schema_clause=omitted_global, schema_existence=schema_exists, nonexistent_schema=schema_exists, in_schema_on_schemas=no_conflict, recipient_role_name_shape=group_role_name, group_keyword=omitted, role_existence=role_exists, privilege_level=superuser, privilege_denied=authorized_success, role_not_member_of_target_role=is_member, additive_vs_overriding=global_only, cannot_revoke_global_from_per_schema=valid_revoke, expected_status=success, verification_mode=catalog_query_pg_default_acl, cleanup_mode=revoke_default_privileges
-- derived_axes: action_mode=grant_with_option, actor=superuser, expected_sqlstate=00000, for_scope=role_multiple, object_class=TABLES, operation=grant, privilege_binding=all_privileges, privilege_sql=ALL PRIVILEGES, recipient=group_role, schema_scope=omitted, schema_shape=not_applicable, target_shape=quoted_id
-- combination_strategy: full conditional product: class/privilege × action modifiers × FOR scope × applicable schema scope
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000; pg_default_acl, future-object, and cleanup oracles

-- 1. Header and immutable trace metadata are complete above.

-- 2. Session profile is applied after table-first pre-cleanup.

-- 3. Idempotent pre-cleanup.
DROP TABLE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_table, alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_table CASCADE;
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS prior_large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900000370::oid, 910000370::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_scope_schema CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role Two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS prior_owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_00370_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_intruder;
DROP ROLE IF EXISTS "alterdefaultprivileges_00370_Target Role Two";
DROP ROLE IF EXISTS "alterdefaultprivileges_00370_Target Role";
DROP ROLE IF EXISTS alterdefaultprivileges_00370_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_group_role;

-- 4. Roles, schemas, membership, and complete fixture structures.
SET client_min_messages TO warning;
SET search_path TO pg_catalog, public;
CREATE ROLE alterdefaultprivileges_00370_member_actor;
CREATE ROLE alterdefaultprivileges_00370_intruder;
CREATE ROLE "alterdefaultprivileges_00370_Target Role";
CREATE ROLE "alterdefaultprivileges_00370_Target Role Two";
CREATE ROLE alterdefaultprivileges_00370_recipient_role;
CREATE ROLE alterdefaultprivileges_00370_group_role;
CREATE SCHEMA alterdefaultprivileges_00370_other_schema;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_00370_other_schema TO alterdefaultprivileges_00370_member_actor;
GRANT USAGE, CREATE ON SCHEMA alterdefaultprivileges_00370_other_schema TO "alterdefaultprivileges_00370_Target Role";

-- 5. Revoke fixtures establish a real privilege to remove.

-- 6. Capture the exact pg_default_acl state before the primary target.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role')
      AND d.defaclnamespace = 0::oid
      AND d.defaclobjtype = 'r'
    ORDER BY d.oid
    LIMIT 1
), '<NONE>') AS before_default_acl
FROM (VALUES (true)) AS capture_anchor(dummy)
ORDER BY before_default_acl;
\gset

-- 7. Select the authorized or deliberately unauthorized executor.

-- 8. Primary target statement (exactly one coverage-credit operation).
\set ON_ERROR_STOP off
ALTER DEFAULT PRIVILEGES FOR ROLE "alterdefaultprivileges_00370_Target Role", "alterdefaultprivileges_00370_Target Role Two" GRANT ALL PRIVILEGES ON TABLES TO alterdefaultprivileges_00370_group_role WITH GRANT OPTION;
\set adp_sqlstate :SQLSTATE
\set ON_ERROR_STOP on

-- 9. SQLSTATE and primary-result oracle.
SELECT :'adp_sqlstate' = '00000' AS expected_SQLSTATE;
RESET ROLE;

-- 10. Catalog and future-object semantic verification.
SELECT COALESCE((
    SELECT pg_catalog.array_to_string(d.defaclacl, ',')
    FROM pg_catalog.pg_default_acl AS d
    WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role')
      AND d.defaclnamespace = 0::oid
      AND d.defaclobjtype = 'r'
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
WHERE d.defaclrole = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role')
ORDER BY default_acl_role, default_acl_schema, default_acl_object_type, default_acl_text;
SET ROLE "alterdefaultprivileges_00370_Target Role";
CREATE TABLE alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_table (
    id bigint NOT NULL,
    tenant_id bigint NOT NULL,
    payload text NOT NULL,
    amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
    status smallint NOT NULL DEFAULT 0 CHECK (status BETWEEN 0 AND 9),
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT alterdefaultprivileges_00370_future_table_pk PRIMARY KEY (id),
    CONSTRAINT alterdefaultprivileges_00370_future_table_tenant_uk UNIQUE (tenant_id, id)
);
INSERT INTO alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_table(id, tenant_id, payload, amount, status) VALUES
    (1, 10, 'alpha', 12.50, 1),
    (2, 10, 'beta', 7.25, 2);
RESET ROLE;
SELECT
    COALESCE(pg_catalog.bool_or(
        acl.grantee = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_group_role')
        AND acl.privilege_type = 'SELECT'
    ), false) = true AS direct_acl_privilege_matches,
    COALESCE(pg_catalog.bool_or(
        acl.grantee = (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_group_role')
        AND acl.privilege_type = 'SELECT'
        AND acl.is_grantable
    ), false) = true AS direct_acl_grant_option_matches
FROM pg_catalog.pg_class AS c
JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
CROSS JOIN LATERAL pg_catalog.aclexplode(
    COALESCE(
        c.relacl,
        pg_catalog.acldefault('r'::"char", c.relowner)
    )
) AS acl
WHERE n.nspname = 'alterdefaultprivileges_00370_other_schema'
  AND c.relname = 'alterdefaultprivileges_00370_future_table'
  AND c.relkind = 'r'
ORDER BY direct_acl_privilege_matches, direct_acl_grant_option_matches;

-- 11. Reverse default ACL changes and remove created objects/roles.
ALTER DEFAULT PRIVILEGES FOR ROLE "alterdefaultprivileges_00370_Target Role", "alterdefaultprivileges_00370_Target Role Two" REVOKE ALL PRIVILEGES ON TABLES FROM alterdefaultprivileges_00370_group_role CASCADE;
RESET ROLE;
SELECT pg_catalog.lo_unlink(oid) >= 0 AS large_object_removed FROM pg_catalog.pg_largeobject_metadata WHERE oid IN (900000370::oid, 910000370::oid) ORDER BY oid;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_procedure(integer) CASCADE;
DROP PROCEDURE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_procedure(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_function(integer) CASCADE;
DROP FUNCTION IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_function(integer) CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_sequence CASCADE;
DROP SEQUENCE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_sequence CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_type CASCADE;
DROP TYPE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_type CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_future_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_other_schema CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_scope_schema_two CASCADE;
DROP SCHEMA IF EXISTS alterdefaultprivileges_00370_scope_schema CASCADE;
DROP TABLE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_table, alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_table CASCADE;
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_member_actor' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_intruder' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role Two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_Target Role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_recipient_role_two' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_recipient_role' ORDER BY rolname;
\gexec
SELECT format('DROP OWNED BY %I CASCADE', rolname) AS owned_cleanup FROM pg_catalog.pg_roles WHERE rolname = 'alterdefaultprivileges_00370_group_role' ORDER BY rolname;
\gexec
DROP ROLE IF EXISTS alterdefaultprivileges_00370_member_actor;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_intruder;
DROP ROLE IF EXISTS "alterdefaultprivileges_00370_Target Role Two";
DROP ROLE IF EXISTS "alterdefaultprivileges_00370_Target Role";
DROP ROLE IF EXISTS alterdefaultprivileges_00370_recipient_role_two;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_recipient_role;
DROP ROLE IF EXISTS alterdefaultprivileges_00370_group_role;

-- 12. Cleanup oracle; table cases end with an idempotent table DROP.
SELECT
    NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_roles AS r
        WHERE r.rolname IN ('alterdefaultprivileges_00370_member_actor', 'alterdefaultprivileges_00370_intruder', 'alterdefaultprivileges_00370_Target Role Two', 'alterdefaultprivileges_00370_Target Role', 'alterdefaultprivileges_00370_recipient_role_two', 'alterdefaultprivileges_00370_recipient_role', 'alterdefaultprivileges_00370_group_role')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_namespace AS n
        WHERE n.nspname IN ('alterdefaultprivileges_00370_scope_schema', 'alterdefaultprivileges_00370_scope_schema_two', 'alterdefaultprivileges_00370_other_schema', 'alterdefaultprivileges_00370_future_schema')
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_default_acl AS d
        WHERE pg_catalog.array_to_string(d.defaclacl, ',') LIKE '%alterdefaultprivileges_00370_%'
    ) AS cleanup_complete
FROM (VALUES (true)) AS cleanup_anchor(dummy)
ORDER BY cleanup_complete;
DROP TABLE IF EXISTS alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_future_table, alterdefaultprivileges_00370_other_schema.alterdefaultprivileges_00370_existing_table CASCADE;
