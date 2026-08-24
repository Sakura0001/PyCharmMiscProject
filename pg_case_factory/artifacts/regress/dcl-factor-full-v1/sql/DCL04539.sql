-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=success
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_04539_Grantee";
DROP ROLE IF EXISTS dcl_04539_grantor;
DROP ROLE IF EXISTS dcl_04539_member;
CREATE ROLE "dcl_04539_Grantee";
CREATE ROLE dcl_04539_grantor;
CREATE ROLE dcl_04539_member;
GRANT SET ON PARAMETER work_mem TO dcl_04539_grantor WITH GRANT OPTION;
SET ROLE dcl_04539_grantor;
GRANT SET ON PARAMETER work_mem TO PUBLIC GRANTED BY dcl_04539_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP OWNED BY "dcl_04539_Grantee";
DROP OWNED BY dcl_04539_member;
DROP OWNED BY dcl_04539_grantor;
DROP ROLE IF EXISTS dcl_04539_member;
DROP ROLE IF EXISTS dcl_04539_grantor;
DROP ROLE IF EXISTS "dcl_04539_Grantee";
