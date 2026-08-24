-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS dcl_09008_grantee;
DROP ROLE IF EXISTS dcl_09008_grantor;
DROP ROLE IF EXISTS dcl_09008_member;
CREATE ROLE dcl_09008_grantee;
CREATE ROLE dcl_09008_grantor;
CREATE ROLE dcl_09008_member;
DROP DOMAIN IF EXISTS dcl_09008_domain;
CREATE DOMAIN dcl_09008_domain AS text;
GRANT USAGE ON DOMAIN dcl_09008_missing_object TO dcl_09008_grantee;
BEGIN;
SET ROLE dcl_09008_grantee;
REVOKE USAGE ON DOMAIN dcl_09008_missing_object FROM dcl_09008_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_09008_domain;
DROP OWNED BY dcl_09008_grantee;
DROP OWNED BY dcl_09008_member;
DROP OWNED BY dcl_09008_grantor;
DROP ROLE IF EXISTS dcl_09008_member;
DROP ROLE IF EXISTS dcl_09008_grantor;
DROP ROLE IF EXISTS dcl_09008_grantee;
