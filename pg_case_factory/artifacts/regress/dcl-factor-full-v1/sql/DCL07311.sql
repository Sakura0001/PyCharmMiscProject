-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07311_schema.dcl_07311_table;
DROP ROLE IF EXISTS "dcl_07311_Grantee";
DROP ROLE IF EXISTS dcl_07311_grantor;
DROP ROLE IF EXISTS dcl_07311_member;
CREATE ROLE "dcl_07311_Grantee";
CREATE ROLE dcl_07311_grantor;
CREATE ROLE dcl_07311_member;
DROP SCHEMA IF EXISTS dcl_07311_schema CASCADE;
CREATE SCHEMA dcl_07311_schema;
CREATE TABLE dcl_07311_schema.dcl_07311_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07311_missing_object.dcl_07311_table TO PUBLIC;
SET ROLE "dcl_07311_Grantee";
REVOKE EXECUTE (payload) ON TABLE dcl_07311_missing_object.dcl_07311_table FROM PUBLIC GRANTED BY dcl_07311_grantor RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07311_schema.dcl_07311_table;
DROP SCHEMA IF EXISTS dcl_07311_schema CASCADE;
DROP OWNED BY "dcl_07311_Grantee";
DROP OWNED BY dcl_07311_member;
DROP OWNED BY dcl_07311_grantor;
DROP ROLE IF EXISTS dcl_07311_member;
DROP ROLE IF EXISTS dcl_07311_grantor;
DROP ROLE IF EXISTS "dcl_07311_Grantee";
DROP TABLE IF EXISTS dcl_07311_schema.dcl_07311_table;
