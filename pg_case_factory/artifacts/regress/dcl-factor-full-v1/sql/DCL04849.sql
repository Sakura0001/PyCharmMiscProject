-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_04849_grantor;
DROP ROLE IF EXISTS dcl_04849_member;
CREATE ROLE dcl_04849_grantor;
CREATE ROLE dcl_04849_member;
GRANT SELECT ON PARAMETER work_mem TO dcl_04849_grantor WITH GRANT OPTION;
GRANT dcl_04849_grantor TO dcl_04849_member WITH SET TRUE;
SET ROLE dcl_04849_member;
SET ROLE dcl_04849_grantor;
GRANT SELECT ON PARAMETER work_mem TO SESSION_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_04849_member;
DROP OWNED BY dcl_04849_grantor;
DROP ROLE IF EXISTS dcl_04849_member;
DROP ROLE IF EXISTS dcl_04849_grantor;
