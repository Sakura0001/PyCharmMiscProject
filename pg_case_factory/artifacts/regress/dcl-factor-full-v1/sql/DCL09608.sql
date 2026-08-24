-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS dcl_09608_grantee;
DROP ROLE IF EXISTS dcl_09608_grantor;
DROP ROLE IF EXISTS dcl_09608_member;
CREATE ROLE dcl_09608_grantee;
CREATE ROLE dcl_09608_grantor;
CREATE ROLE dcl_09608_member;
DROP SERVER IF EXISTS dcl_09608_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09608_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09608_fdw;
CREATE SERVER dcl_09608_server FOREIGN DATA WRAPPER dcl_09608_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09608_missing_object TO dcl_09608_grantee;
BEGIN;
SET ROLE dcl_09608_grantee;
REVOKE USAGE ON FOREIGN SERVER dcl_09608_missing_object FROM dcl_09608_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_09608_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09608_fdw CASCADE;
DROP OWNED BY dcl_09608_grantee;
DROP OWNED BY dcl_09608_member;
DROP OWNED BY dcl_09608_grantor;
DROP ROLE IF EXISTS dcl_09608_member;
DROP ROLE IF EXISTS dcl_09608_grantor;
DROP ROLE IF EXISTS dcl_09608_grantee;
