-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_03644_grantee;
DROP ROLE IF EXISTS dcl_03644_grantor;
DROP ROLE IF EXISTS dcl_03644_member;
CREATE ROLE dcl_03644_grantee;
CREATE ROLE dcl_03644_grantor;
CREATE ROLE dcl_03644_member;
BEGIN;
GRANT USAGE ON LANGUAGE plpgsql TO CURRENT_ROLE GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_03644_grantee;
DROP OWNED BY dcl_03644_member;
DROP OWNED BY dcl_03644_grantor;
DROP ROLE IF EXISTS dcl_03644_member;
DROP ROLE IF EXISTS dcl_03644_grantor;
DROP ROLE IF EXISTS dcl_03644_grantee;
