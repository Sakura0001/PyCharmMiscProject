-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_07472_table;
DROP ROLE IF EXISTS dcl_07472_grantee;
DROP ROLE IF EXISTS dcl_07472_grantor;
DROP ROLE IF EXISTS dcl_07472_member;
CREATE ROLE dcl_07472_grantee;
CREATE ROLE dcl_07472_grantor;
CREATE ROLE dcl_07472_member;
CREATE TABLE dcl_07472_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07472_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_07472_grantee;
REVOKE ADMIN OPTION FOR EXECUTE (payload) ON TABLE dcl_07472_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_07472_table;
ROLLBACK;
DROP OWNED BY dcl_07472_grantee;
DROP OWNED BY dcl_07472_member;
DROP OWNED BY dcl_07472_grantor;
DROP ROLE IF EXISTS dcl_07472_member;
DROP ROLE IF EXISTS dcl_07472_grantor;
DROP ROLE IF EXISTS dcl_07472_grantee;
DROP TABLE IF EXISTS dcl_07472_table;
