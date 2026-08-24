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
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_00659_schema.dcl_00659_table;
DROP ROLE IF EXISTS dcl_00659_grantee;
DROP ROLE IF EXISTS dcl_00659_grantor;
DROP ROLE IF EXISTS dcl_00659_member;
CREATE ROLE dcl_00659_grantee;
CREATE ROLE dcl_00659_grantor;
CREATE ROLE dcl_00659_member;
DROP SCHEMA IF EXISTS dcl_00659_schema CASCADE;
CREATE SCHEMA dcl_00659_schema;
CREATE TABLE dcl_00659_schema.dcl_00659_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00659_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00659_missing_object.dcl_00659_table TO CURRENT_ROLE WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00659_schema.dcl_00659_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00659_schema CASCADE;
DROP OWNED BY dcl_00659_grantee;
DROP OWNED BY dcl_00659_member;
DROP OWNED BY dcl_00659_grantor;
DROP ROLE IF EXISTS dcl_00659_member;
DROP ROLE IF EXISTS dcl_00659_grantor;
DROP ROLE IF EXISTS dcl_00659_grantee;
DROP TABLE IF EXISTS dcl_00659_schema.dcl_00659_table;
