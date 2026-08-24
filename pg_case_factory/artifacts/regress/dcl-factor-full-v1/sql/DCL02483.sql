-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_02483_grantee;
DROP ROLE IF EXISTS dcl_02483_grantor;
DROP ROLE IF EXISTS dcl_02483_member;
CREATE ROLE dcl_02483_grantee;
CREATE ROLE dcl_02483_grantor;
CREATE ROLE dcl_02483_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02483_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02483_fdw;
BEGIN;
SET ROLE dcl_02483_grantee;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02483_missing_object TO SESSION_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02483_fdw CASCADE;
DROP OWNED BY dcl_02483_grantee;
DROP OWNED BY dcl_02483_member;
DROP OWNED BY dcl_02483_grantor;
DROP ROLE IF EXISTS dcl_02483_member;
DROP ROLE IF EXISTS dcl_02483_grantor;
DROP ROLE IF EXISTS dcl_02483_grantee;
