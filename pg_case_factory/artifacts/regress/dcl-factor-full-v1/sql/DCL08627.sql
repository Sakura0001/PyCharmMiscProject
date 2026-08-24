-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_08627_Grantee";
DROP ROLE IF EXISTS dcl_08627_grantor;
DROP ROLE IF EXISTS dcl_08627_member;
CREATE ROLE "dcl_08627_Grantee";
CREATE ROLE dcl_08627_grantor;
CREATE ROLE dcl_08627_member;
DROP DOMAIN IF EXISTS dcl_08627_domain;
CREATE DOMAIN dcl_08627_domain AS text;
GRANT USAGE ON DOMAIN dcl_08627_domain TO PUBLIC;
GRANT USAGE ON DOMAIN dcl_08627_domain TO dcl_08627_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_08627_grantor;
REVOKE GRANT OPTION FOR USAGE ON DOMAIN dcl_08627_domain FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08627_domain;
DROP OWNED BY "dcl_08627_Grantee";
DROP OWNED BY dcl_08627_member;
DROP OWNED BY dcl_08627_grantor;
DROP ROLE IF EXISTS dcl_08627_member;
DROP ROLE IF EXISTS dcl_08627_grantor;
DROP ROLE IF EXISTS "dcl_08627_Grantee";
