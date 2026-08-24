-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_13153_grantor;
DROP ROLE IF EXISTS dcl_13153_member;
CREATE ROLE dcl_13153_grantor;
CREATE ROLE dcl_13153_member;
GRANT dcl_13153_missing_member TO dcl_13153_grantor WITH GRANT OPTION;
GRANT dcl_13153_grantor TO dcl_13153_member WITH SET TRUE;
SET ROLE dcl_13153_member;
SET ROLE dcl_13153_grantor;
REVOKE dcl_13153_missing_member FROM dcl_13153_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_13153_member;
DROP OWNED BY dcl_13153_grantor;
DROP ROLE IF EXISTS dcl_13153_member;
DROP ROLE IF EXISTS dcl_13153_grantor;
