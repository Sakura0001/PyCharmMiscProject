-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11943_Grantee";
DROP ROLE IF EXISTS dcl_11943_grantor;
DROP ROLE IF EXISTS dcl_11943_member;
CREATE ROLE "dcl_11943_Grantee";
CREATE ROLE dcl_11943_grantor;
CREATE ROLE dcl_11943_member;
DROP SCHEMA IF EXISTS dcl_11943_schema CASCADE;
CREATE SCHEMA dcl_11943_schema;
GRANT USAGE ON SCHEMA dcl_11943_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_11943_Grantee";
REVOKE USAGE ON SCHEMA dcl_11943_missing_object FROM CURRENT_ROLE GRANTED BY dcl_11943_grantor RESTRICT;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_11943_schema', 'USAGE');
DROP SCHEMA IF EXISTS dcl_11943_schema CASCADE;
DROP OWNED BY "dcl_11943_Grantee";
DROP OWNED BY dcl_11943_member;
DROP OWNED BY dcl_11943_grantor;
DROP ROLE IF EXISTS dcl_11943_member;
DROP ROLE IF EXISTS dcl_11943_grantor;
DROP ROLE IF EXISTS "dcl_11943_Grantee";
