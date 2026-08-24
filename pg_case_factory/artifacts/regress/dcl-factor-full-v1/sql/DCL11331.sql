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
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11331_Grantee";
DROP ROLE IF EXISTS dcl_11331_grantor;
DROP ROLE IF EXISTS dcl_11331_member;
CREATE ROLE "dcl_11331_Grantee";
CREATE ROLE dcl_11331_grantor;
CREATE ROLE dcl_11331_member;
GRANT SET ON PARAMETER work_mem TO CURRENT_ROLE;
GRANT SET ON PARAMETER work_mem TO dcl_11331_grantor WITH GRANT OPTION;
SET ROLE dcl_11331_grantor;
REVOKE SET ON PARAMETER work_mem FROM CURRENT_ROLE GRANTED BY dcl_11331_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP OWNED BY "dcl_11331_Grantee";
DROP OWNED BY dcl_11331_member;
DROP OWNED BY dcl_11331_grantor;
DROP ROLE IF EXISTS dcl_11331_member;
DROP ROLE IF EXISTS dcl_11331_grantor;
DROP ROLE IF EXISTS "dcl_11331_Grantee";
