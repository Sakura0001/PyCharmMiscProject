-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_12457_grantor;
DROP ROLE IF EXISTS dcl_12457_member;
CREATE ROLE dcl_12457_grantor;
CREATE ROLE dcl_12457_member;
GRANT CREATE ON TABLESPACE dcl_12457_missing_object TO CURRENT_ROLE;
GRANT CREATE ON TABLESPACE dcl_12457_missing_object TO dcl_12457_grantor WITH GRANT OPTION;
GRANT dcl_12457_grantor TO dcl_12457_member WITH SET TRUE;
SET ROLE dcl_12457_member;
SET ROLE dcl_12457_grantor;
REVOKE ADMIN OPTION FOR CREATE ON TABLESPACE dcl_12457_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_12457_member;
DROP OWNED BY dcl_12457_grantor;
DROP ROLE IF EXISTS dcl_12457_member;
DROP ROLE IF EXISTS dcl_12457_grantor;
