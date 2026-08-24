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
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_04535_Grantee";
DROP ROLE IF EXISTS dcl_04535_grantor;
DROP ROLE IF EXISTS dcl_04535_member;
CREATE ROLE "dcl_04535_Grantee";
CREATE ROLE dcl_04535_grantor;
CREATE ROLE dcl_04535_member;
GRANT SET ON PARAMETER work_mem TO dcl_04535_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_04535_grantor;
GRANT SET ON PARAMETER work_mem TO "dcl_04535_Grantee" WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY "dcl_04535_Grantee";
DROP OWNED BY dcl_04535_member;
DROP OWNED BY dcl_04535_grantor;
DROP ROLE IF EXISTS dcl_04535_member;
DROP ROLE IF EXISTS dcl_04535_grantor;
DROP ROLE IF EXISTS "dcl_04535_Grantee";
