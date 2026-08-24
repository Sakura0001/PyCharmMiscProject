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
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11947_grantor;
DROP ROLE IF EXISTS dcl_11947_member;
CREATE ROLE dcl_11947_grantor;
CREATE ROLE dcl_11947_member;
DROP SCHEMA IF EXISTS dcl_11947_schema CASCADE;
CREATE SCHEMA dcl_11947_schema;
GRANT USAGE ON SCHEMA dcl_11947_missing_object TO CURRENT_ROLE;
GRANT USAGE ON SCHEMA dcl_11947_missing_object TO dcl_11947_grantor WITH GRANT OPTION;
GRANT dcl_11947_grantor TO dcl_11947_member WITH SET TRUE;
SET ROLE dcl_11947_member;
SET ROLE dcl_11947_grantor;
REVOKE ADMIN OPTION FOR USAGE ON SCHEMA dcl_11947_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_11947_schema', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_11947_schema CASCADE;
DROP OWNED BY dcl_11947_member;
DROP OWNED BY dcl_11947_grantor;
DROP ROLE IF EXISTS dcl_11947_member;
DROP ROLE IF EXISTS dcl_11947_grantor;
