-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_07667_schema.dcl_07667_table;
DROP ROLE IF EXISTS dcl_07667_grantee;
DROP ROLE IF EXISTS dcl_07667_grantor;
DROP ROLE IF EXISTS dcl_07667_member;
CREATE ROLE dcl_07667_grantee;
CREATE ROLE dcl_07667_grantor;
CREATE ROLE dcl_07667_member;
DROP SCHEMA IF EXISTS dcl_07667_schema CASCADE;
CREATE SCHEMA dcl_07667_schema;
CREATE TABLE dcl_07667_schema.dcl_07667_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07667_missing_object.dcl_07667_table TO dcl_07667_grantee;
BEGIN;
SET ROLE dcl_07667_grantee;
REVOKE INHERIT OPTION FOR EXECUTE (payload) ON TABLE dcl_07667_missing_object.dcl_07667_table FROM dcl_07667_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07667_schema.dcl_07667_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07667_schema CASCADE;
DROP OWNED BY dcl_07667_grantee;
DROP OWNED BY dcl_07667_member;
DROP OWNED BY dcl_07667_grantor;
DROP ROLE IF EXISTS dcl_07667_member;
DROP ROLE IF EXISTS dcl_07667_grantor;
DROP ROLE IF EXISTS dcl_07667_grantee;
DROP TABLE IF EXISTS dcl_07667_schema.dcl_07667_table;
