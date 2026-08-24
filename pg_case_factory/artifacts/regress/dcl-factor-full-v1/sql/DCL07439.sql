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
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_07439_schema.dcl_07439_table;
DROP ROLE IF EXISTS dcl_07439_grantee;
DROP ROLE IF EXISTS dcl_07439_grantor;
DROP ROLE IF EXISTS dcl_07439_member;
CREATE ROLE dcl_07439_grantee;
CREATE ROLE dcl_07439_grantor;
CREATE ROLE dcl_07439_member;
DROP SCHEMA IF EXISTS dcl_07439_schema CASCADE;
CREATE SCHEMA dcl_07439_schema;
CREATE TABLE dcl_07439_schema.dcl_07439_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07439_missing_object.dcl_07439_table TO PUBLIC;
BEGIN;
SET ROLE dcl_07439_grantee;
REVOKE INHERIT OPTION FOR EXECUTE (payload) ON TABLE dcl_07439_missing_object.dcl_07439_table FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07439_schema.dcl_07439_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07439_schema CASCADE;
DROP OWNED BY dcl_07439_grantee;
DROP OWNED BY dcl_07439_member;
DROP OWNED BY dcl_07439_grantor;
DROP ROLE IF EXISTS dcl_07439_member;
DROP ROLE IF EXISTS dcl_07439_grantor;
DROP ROLE IF EXISTS dcl_07439_grantee;
DROP TABLE IF EXISTS dcl_07439_schema.dcl_07439_table;
