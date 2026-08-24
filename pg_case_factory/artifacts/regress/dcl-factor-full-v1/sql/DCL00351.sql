-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_00351_schema.dcl_00351_table;
DROP ROLE IF EXISTS "dcl_00351_Grantee";
DROP ROLE IF EXISTS dcl_00351_grantor;
DROP ROLE IF EXISTS dcl_00351_member;
CREATE ROLE "dcl_00351_Grantee";
CREATE ROLE dcl_00351_grantor;
CREATE ROLE dcl_00351_member;
DROP SCHEMA IF EXISTS dcl_00351_schema CASCADE;
CREATE SCHEMA dcl_00351_schema;
CREATE TABLE dcl_00351_schema.dcl_00351_table (id integer, payload text);
SET ROLE "dcl_00351_Grantee";
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_00351_missing_object TO SESSION_USER GRANTED BY dcl_00351_grantor;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00351_schema.dcl_00351_table;
DROP SCHEMA IF EXISTS dcl_00351_schema CASCADE;
DROP OWNED BY "dcl_00351_Grantee";
DROP OWNED BY dcl_00351_member;
DROP OWNED BY dcl_00351_grantor;
DROP ROLE IF EXISTS dcl_00351_member;
DROP ROLE IF EXISTS dcl_00351_grantor;
DROP ROLE IF EXISTS "dcl_00351_Grantee";
DROP TABLE IF EXISTS dcl_00351_schema.dcl_00351_table;
