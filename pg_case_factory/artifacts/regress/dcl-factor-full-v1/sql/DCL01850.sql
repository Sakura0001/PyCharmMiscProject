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
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_01850_grantee;
DROP ROLE IF EXISTS dcl_01850_grantor;
DROP ROLE IF EXISTS dcl_01850_member;
CREATE ROLE dcl_01850_grantee;
CREATE ROLE dcl_01850_grantor;
CREATE ROLE dcl_01850_member;
DROP DOMAIN IF EXISTS dcl_01850_domain;
CREATE DOMAIN dcl_01850_domain AS text;
BEGIN;
GRANT USAGE ON DOMAIN dcl_01850_domain TO CURRENT_USER GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_01850_domain;
DROP OWNED BY dcl_01850_grantee;
DROP OWNED BY dcl_01850_member;
DROP OWNED BY dcl_01850_grantor;
DROP ROLE IF EXISTS dcl_01850_member;
DROP ROLE IF EXISTS dcl_01850_grantor;
DROP ROLE IF EXISTS dcl_01850_grantee;
