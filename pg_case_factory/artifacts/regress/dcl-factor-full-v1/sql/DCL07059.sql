-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07059_schema.dcl_07059_table;
DROP ROLE IF EXISTS "dcl_07059_Grantee";
DROP ROLE IF EXISTS dcl_07059_grantor;
DROP ROLE IF EXISTS dcl_07059_member;
CREATE ROLE "dcl_07059_Grantee";
CREATE ROLE dcl_07059_grantor;
CREATE ROLE dcl_07059_member;
DROP SCHEMA IF EXISTS dcl_07059_schema CASCADE;
CREATE SCHEMA dcl_07059_schema;
CREATE TABLE dcl_07059_schema.dcl_07059_table (id integer, payload text);
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_07059_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_07059_Grantee";
REVOKE ADMIN OPTION FOR SELECT ON ALL TABLES IN SCHEMA dcl_07059_missing_object FROM CURRENT_ROLE GRANTED BY dcl_07059_grantor RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07059_schema.dcl_07059_table;
DROP SCHEMA IF EXISTS dcl_07059_schema CASCADE;
DROP OWNED BY "dcl_07059_Grantee";
DROP OWNED BY dcl_07059_member;
DROP OWNED BY dcl_07059_grantor;
DROP ROLE IF EXISTS dcl_07059_member;
DROP ROLE IF EXISTS dcl_07059_grantor;
DROP ROLE IF EXISTS "dcl_07059_Grantee";
DROP TABLE IF EXISTS dcl_07059_schema.dcl_07059_table;
