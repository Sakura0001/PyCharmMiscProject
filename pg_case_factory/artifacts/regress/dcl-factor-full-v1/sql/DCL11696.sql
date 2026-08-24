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
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_11696_grantee;
DROP ROLE IF EXISTS dcl_11696_grantor;
DROP ROLE IF EXISTS dcl_11696_member;
CREATE ROLE dcl_11696_grantee;
CREATE ROLE dcl_11696_grantor;
CREATE ROLE dcl_11696_member;
GRANT SET ON PARAMETER work_mem TO SESSION_USER;
BEGIN;
SET ROLE dcl_11696_grantee;
REVOKE SET ON PARAMETER work_mem FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_11696_grantee;
DROP OWNED BY dcl_11696_member;
DROP OWNED BY dcl_11696_grantor;
DROP ROLE IF EXISTS dcl_11696_member;
DROP ROLE IF EXISTS dcl_11696_grantor;
DROP ROLE IF EXISTS dcl_11696_grantee;
