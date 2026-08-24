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
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11647_grantor;
DROP ROLE IF EXISTS dcl_11647_member;
CREATE ROLE dcl_11647_grantor;
CREATE ROLE dcl_11647_member;
GRANT SET ON PARAMETER work_mem TO dcl_11647_missing_role;
GRANT SET ON PARAMETER work_mem TO dcl_11647_grantor WITH GRANT OPTION;
GRANT dcl_11647_grantor TO dcl_11647_member WITH SET TRUE;
SET ROLE dcl_11647_member;
SET ROLE dcl_11647_grantor;
REVOKE SET ON PARAMETER work_mem FROM dcl_11647_missing_role RESTRICT;
RESET ROLE;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11647_member;
DROP OWNED BY dcl_11647_grantor;
DROP ROLE IF EXISTS dcl_11647_member;
DROP ROLE IF EXISTS dcl_11647_grantor;
