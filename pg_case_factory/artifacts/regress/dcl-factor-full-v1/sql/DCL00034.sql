-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_00034_schema.dcl_00034_table;
DROP ROLE IF EXISTS dcl_00034_grantee;
DROP ROLE IF EXISTS dcl_00034_grantor;
DROP ROLE IF EXISTS dcl_00034_member;
CREATE ROLE dcl_00034_grantee;
CREATE ROLE dcl_00034_grantor;
CREATE ROLE dcl_00034_member;
DROP SCHEMA IF EXISTS dcl_00034_schema CASCADE;
CREATE SCHEMA dcl_00034_schema;
CREATE TABLE dcl_00034_schema.dcl_00034_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_00034_schema.dcl_00034_table TO dcl_00034_grantee WITH GRANT OPTION;
SELECT count(*) AS table_count FROM dcl_00034_schema.dcl_00034_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_00034_schema CASCADE;
DROP OWNED BY dcl_00034_grantee;
DROP OWNED BY dcl_00034_member;
DROP OWNED BY dcl_00034_grantor;
DROP ROLE IF EXISTS dcl_00034_member;
DROP ROLE IF EXISTS dcl_00034_grantor;
DROP ROLE IF EXISTS dcl_00034_grantee;
DROP TABLE IF EXISTS dcl_00034_schema.dcl_00034_table;
