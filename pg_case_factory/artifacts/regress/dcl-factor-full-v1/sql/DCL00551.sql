-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_00551_schema.dcl_00551_table;
DROP ROLE IF EXISTS dcl_00551_grantee;
DROP ROLE IF EXISTS dcl_00551_grantor;
DROP ROLE IF EXISTS dcl_00551_member;
CREATE ROLE dcl_00551_grantee;
CREATE ROLE dcl_00551_grantor;
CREATE ROLE dcl_00551_member;
DROP SCHEMA IF EXISTS dcl_00551_schema CASCADE;
CREATE SCHEMA dcl_00551_schema;
CREATE TABLE dcl_00551_schema.dcl_00551_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00551_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00551_missing_object.dcl_00551_table TO CURRENT_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00551_schema.dcl_00551_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00551_schema CASCADE;
DROP OWNED BY dcl_00551_grantee;
DROP OWNED BY dcl_00551_member;
DROP OWNED BY dcl_00551_grantor;
DROP ROLE IF EXISTS dcl_00551_member;
DROP ROLE IF EXISTS dcl_00551_grantor;
DROP ROLE IF EXISTS dcl_00551_grantee;
DROP TABLE IF EXISTS dcl_00551_schema.dcl_00551_table;
