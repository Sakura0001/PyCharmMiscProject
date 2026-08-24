-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_01652_grantee;
DROP ROLE IF EXISTS dcl_01652_grantor;
DROP ROLE IF EXISTS dcl_01652_member;
CREATE ROLE dcl_01652_grantee;
CREATE ROLE dcl_01652_grantor;
CREATE ROLE dcl_01652_member;
BEGIN;
SET ROLE dcl_01652_grantee;
GRANT CONNECT ON DATABASE dcl_01652_missing_object TO dcl_01652_grantee GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_01652_grantee;
DROP OWNED BY dcl_01652_member;
DROP OWNED BY dcl_01652_grantor;
DROP ROLE IF EXISTS dcl_01652_member;
DROP ROLE IF EXISTS dcl_01652_grantor;
DROP ROLE IF EXISTS dcl_01652_grantee;
