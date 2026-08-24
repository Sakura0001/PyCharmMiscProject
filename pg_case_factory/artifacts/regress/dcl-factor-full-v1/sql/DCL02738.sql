-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_02738_grantee;
DROP ROLE IF EXISTS dcl_02738_grantor;
DROP ROLE IF EXISTS dcl_02738_member;
CREATE ROLE dcl_02738_grantee;
CREATE ROLE dcl_02738_grantor;
CREATE ROLE dcl_02738_member;
DROP SERVER IF EXISTS dcl_02738_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02738_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02738_fdw;
CREATE SERVER dcl_02738_server FOREIGN DATA WRAPPER dcl_02738_fdw;
BEGIN;
GRANT USAGE ON FOREIGN SERVER dcl_02738_server TO PUBLIC GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_02738_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02738_fdw CASCADE;
DROP OWNED BY dcl_02738_grantee;
DROP OWNED BY dcl_02738_member;
DROP OWNED BY dcl_02738_grantor;
DROP ROLE IF EXISTS dcl_02738_member;
DROP ROLE IF EXISTS dcl_02738_grantor;
DROP ROLE IF EXISTS dcl_02738_grantee;
