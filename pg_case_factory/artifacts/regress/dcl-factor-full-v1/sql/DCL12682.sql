-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_12682_grantee;
DROP ROLE IF EXISTS dcl_12682_grantor;
DROP ROLE IF EXISTS dcl_12682_member;
CREATE ROLE dcl_12682_grantee;
CREATE ROLE dcl_12682_grantor;
CREATE ROLE dcl_12682_member;
DROP TYPE IF EXISTS dcl_12682_type;
CREATE TYPE dcl_12682_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12682_type TO CURRENT_ROLE;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12682_type FROM CURRENT_ROLE RESTRICT;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12682_type', 'USAGE');
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_12682_type;
DROP OWNED BY dcl_12682_grantee;
DROP OWNED BY dcl_12682_member;
DROP OWNED BY dcl_12682_grantor;
DROP ROLE IF EXISTS dcl_12682_member;
DROP ROLE IF EXISTS dcl_12682_grantor;
DROP ROLE IF EXISTS dcl_12682_grantee;
