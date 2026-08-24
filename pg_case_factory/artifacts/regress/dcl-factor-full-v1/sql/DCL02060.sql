-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_02060_grantee;
DROP ROLE IF EXISTS dcl_02060_grantor;
DROP ROLE IF EXISTS dcl_02060_member;
CREATE ROLE dcl_02060_grantee;
CREATE ROLE dcl_02060_grantor;
CREATE ROLE dcl_02060_member;
DROP DOMAIN IF EXISTS dcl_02060_domain;
CREATE DOMAIN dcl_02060_domain AS text;
BEGIN;
SET ROLE dcl_02060_grantee;
GRANT USAGE ON DOMAIN dcl_02060_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_02060_domain;
DROP OWNED BY dcl_02060_grantee;
DROP OWNED BY dcl_02060_member;
DROP OWNED BY dcl_02060_grantor;
DROP ROLE IF EXISTS dcl_02060_member;
DROP ROLE IF EXISTS dcl_02060_grantor;
DROP ROLE IF EXISTS dcl_02060_grantee;
