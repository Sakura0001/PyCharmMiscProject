-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_02878_grantor;
DROP ROLE IF EXISTS dcl_02878_member;
CREATE ROLE dcl_02878_grantor;
CREATE ROLE dcl_02878_member;
DROP SERVER IF EXISTS dcl_02878_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02878_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02878_fdw;
CREATE SERVER dcl_02878_server FOREIGN DATA WRAPPER dcl_02878_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_02878_missing_object TO dcl_02878_grantor WITH GRANT OPTION;
GRANT dcl_02878_grantor TO dcl_02878_member WITH SET TRUE;
SET ROLE dcl_02878_member;
SET ROLE dcl_02878_grantor;
GRANT USAGE ON FOREIGN SERVER dcl_02878_missing_object TO SESSION_USER WITH INHERIT TRUE;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_02878_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02878_fdw CASCADE;
DROP OWNED BY dcl_02878_member;
DROP OWNED BY dcl_02878_grantor;
DROP ROLE IF EXISTS dcl_02878_member;
DROP ROLE IF EXISTS dcl_02878_grantor;
