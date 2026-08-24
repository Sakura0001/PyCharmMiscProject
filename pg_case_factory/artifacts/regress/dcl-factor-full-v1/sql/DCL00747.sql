-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_00747_schema.dcl_00747_table;
DROP ROLE IF EXISTS "dcl_00747_Grantee";
DROP ROLE IF EXISTS dcl_00747_grantor;
DROP ROLE IF EXISTS dcl_00747_member;
CREATE ROLE "dcl_00747_Grantee";
CREATE ROLE dcl_00747_grantor;
CREATE ROLE dcl_00747_member;
DROP SCHEMA IF EXISTS dcl_00747_schema CASCADE;
CREATE SCHEMA dcl_00747_schema;
CREATE TABLE dcl_00747_schema.dcl_00747_table (id integer, payload text);
SET ROLE "dcl_00747_Grantee";
GRANT EXECUTE (payload) ON TABLE dcl_00747_missing_object.dcl_00747_table TO SESSION_USER WITH ADMIN OPTION GRANTED BY dcl_00747_grantor;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00747_schema.dcl_00747_table;
DROP SCHEMA IF EXISTS dcl_00747_schema CASCADE;
DROP OWNED BY "dcl_00747_Grantee";
DROP OWNED BY dcl_00747_member;
DROP OWNED BY dcl_00747_grantor;
DROP ROLE IF EXISTS dcl_00747_member;
DROP ROLE IF EXISTS dcl_00747_grantor;
DROP ROLE IF EXISTS "dcl_00747_Grantee";
DROP TABLE IF EXISTS dcl_00747_schema.dcl_00747_table;
