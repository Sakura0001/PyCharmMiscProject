-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_10472_grantee;
DROP ROLE IF EXISTS dcl_10472_grantor;
DROP ROLE IF EXISTS dcl_10472_member;
CREATE ROLE dcl_10472_grantee;
CREATE ROLE dcl_10472_grantor;
CREATE ROLE dcl_10472_member;
GRANT USAGE ON LANGUAGE plpgsql TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_10472_grantee;
REVOKE USAGE ON LANGUAGE plpgsql FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_10472_grantee;
DROP OWNED BY dcl_10472_member;
DROP OWNED BY dcl_10472_grantor;
DROP ROLE IF EXISTS dcl_10472_member;
DROP ROLE IF EXISTS dcl_10472_grantor;
DROP ROLE IF EXISTS dcl_10472_grantee;
