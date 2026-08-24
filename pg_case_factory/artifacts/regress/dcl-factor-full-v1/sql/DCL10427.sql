-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
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
DROP ROLE IF EXISTS "dcl_10427_Grantee";
DROP ROLE IF EXISTS dcl_10427_grantor;
DROP ROLE IF EXISTS dcl_10427_member;
CREATE ROLE "dcl_10427_Grantee";
CREATE ROLE dcl_10427_grantor;
CREATE ROLE dcl_10427_member;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_10427_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_10427_grantor;
REVOKE GRANT OPTION FOR USAGE ON LANGUAGE plpgsql FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY "dcl_10427_Grantee";
DROP OWNED BY dcl_10427_member;
DROP OWNED BY dcl_10427_grantor;
DROP ROLE IF EXISTS dcl_10427_member;
DROP ROLE IF EXISTS dcl_10427_grantor;
DROP ROLE IF EXISTS "dcl_10427_Grantee";
