-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=success
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_11338_grantee;
DROP ROLE IF EXISTS dcl_11338_grantor;
DROP ROLE IF EXISTS dcl_11338_member;
CREATE ROLE dcl_11338_grantee;
CREATE ROLE dcl_11338_grantor;
CREATE ROLE dcl_11338_member;
GRANT SET ON PARAMETER work_mem TO CURRENT_USER;
REVOKE GRANT OPTION FOR SET ON PARAMETER work_mem FROM CURRENT_USER RESTRICT;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11338_grantee;
DROP OWNED BY dcl_11338_member;
DROP OWNED BY dcl_11338_grantor;
DROP ROLE IF EXISTS dcl_11338_member;
DROP ROLE IF EXISTS dcl_11338_grantor;
DROP ROLE IF EXISTS dcl_11338_grantee;
