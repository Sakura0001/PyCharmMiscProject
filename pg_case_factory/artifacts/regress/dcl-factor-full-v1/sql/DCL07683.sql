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
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07683_schema.dcl_07683_table;
DROP ROLE IF EXISTS "dcl_07683_Grantee";
DROP ROLE IF EXISTS dcl_07683_grantor;
DROP ROLE IF EXISTS dcl_07683_member;
CREATE ROLE "dcl_07683_Grantee";
CREATE ROLE dcl_07683_grantor;
CREATE ROLE dcl_07683_member;
DROP SCHEMA IF EXISTS dcl_07683_schema CASCADE;
CREATE SCHEMA dcl_07683_schema;
CREATE TABLE dcl_07683_schema.dcl_07683_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07683_missing_object.dcl_07683_table TO CURRENT_ROLE;
SET ROLE "dcl_07683_Grantee";
REVOKE EXECUTE (payload) ON TABLE dcl_07683_missing_object.dcl_07683_table FROM CURRENT_ROLE GRANTED BY dcl_07683_grantor RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07683_schema.dcl_07683_table;
DROP SCHEMA IF EXISTS dcl_07683_schema CASCADE;
DROP OWNED BY "dcl_07683_Grantee";
DROP OWNED BY dcl_07683_member;
DROP OWNED BY dcl_07683_grantor;
DROP ROLE IF EXISTS dcl_07683_member;
DROP ROLE IF EXISTS dcl_07683_grantor;
DROP ROLE IF EXISTS "dcl_07683_Grantee";
DROP TABLE IF EXISTS dcl_07683_schema.dcl_07683_table;
