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
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11685_Grantee";
DROP ROLE IF EXISTS dcl_11685_grantor;
DROP ROLE IF EXISTS dcl_11685_member;
CREATE ROLE "dcl_11685_Grantee";
CREATE ROLE dcl_11685_grantor;
CREATE ROLE dcl_11685_member;
GRANT SET ON PARAMETER work_mem TO CURRENT_USER;
SET ROLE "dcl_11685_Grantee";
REVOKE SET ON PARAMETER work_mem FROM CURRENT_USER GRANTED BY dcl_11685_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP OWNED BY "dcl_11685_Grantee";
DROP OWNED BY dcl_11685_member;
DROP OWNED BY dcl_11685_grantor;
DROP ROLE IF EXISTS dcl_11685_member;
DROP ROLE IF EXISTS dcl_11685_grantor;
DROP ROLE IF EXISTS "dcl_11685_Grantee";
