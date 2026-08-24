-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_06808_schema.dcl_06808_table;
DROP ROLE IF EXISTS dcl_06808_grantee;
DROP ROLE IF EXISTS dcl_06808_grantor;
DROP ROLE IF EXISTS dcl_06808_member;
CREATE ROLE dcl_06808_grantee;
CREATE ROLE dcl_06808_grantor;
CREATE ROLE dcl_06808_member;
DROP SCHEMA IF EXISTS dcl_06808_schema CASCADE;
CREATE SCHEMA dcl_06808_schema;
CREATE TABLE dcl_06808_schema.dcl_06808_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_06808_schema.dcl_06808_table TO CURRENT_USER;
REVOKE GRANT OPTION FOR SELECT ON TABLE dcl_06808_schema.dcl_06808_table FROM CURRENT_USER RESTRICT;
SELECT count(*) AS table_count FROM dcl_06808_schema.dcl_06808_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_06808_schema CASCADE;
DROP OWNED BY dcl_06808_grantee;
DROP OWNED BY dcl_06808_member;
DROP OWNED BY dcl_06808_grantor;
DROP ROLE IF EXISTS dcl_06808_member;
DROP ROLE IF EXISTS dcl_06808_grantor;
DROP ROLE IF EXISTS dcl_06808_grantee;
DROP TABLE IF EXISTS dcl_06808_schema.dcl_06808_table;
