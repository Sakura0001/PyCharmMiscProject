-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP TABLE IF EXISTS dcl_00632_table;
DROP ROLE IF EXISTS dcl_00632_grantee;
DROP ROLE IF EXISTS dcl_00632_grantor;
DROP ROLE IF EXISTS dcl_00632_member;
CREATE ROLE dcl_00632_grantee;
CREATE ROLE dcl_00632_grantor;
CREATE ROLE dcl_00632_member;
CREATE TABLE dcl_00632_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00632_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00632_missing_object TO dcl_00632_grantee GRANTED BY CURRENT_USER;
RESET ROLE;
SET ROLE dcl_00632_grantee;
SELECT count(*) AS privilege_effect_rows FROM dcl_00632_table;
RESET ROLE;
ROLLBACK;
DROP OWNED BY dcl_00632_grantee;
DROP OWNED BY dcl_00632_member;
DROP OWNED BY dcl_00632_grantor;
DROP ROLE IF EXISTS dcl_00632_member;
DROP ROLE IF EXISTS dcl_00632_grantor;
DROP ROLE IF EXISTS dcl_00632_grantee;
DROP TABLE IF EXISTS dcl_00632_table;
