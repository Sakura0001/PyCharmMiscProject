-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_13770_schema.dcl_13770_table;
DROP ROLE IF EXISTS dcl_13770_grantee;
DROP ROLE IF EXISTS dcl_13770_grantor;
DROP ROLE IF EXISTS dcl_13770_member;
CREATE ROLE dcl_13770_grantee;
CREATE ROLE dcl_13770_grantor;
CREATE ROLE dcl_13770_member;
DROP SCHEMA IF EXISTS dcl_13770_schema CASCADE;
CREATE SCHEMA dcl_13770_schema;
CREATE TABLE dcl_13770_schema.dcl_13770_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_13770_schema.dcl_13770_table TO dcl_13770_grantee;
SELECT count(*) AS table_count FROM dcl_13770_schema.dcl_13770_table;
DROP SCHEMA IF EXISTS dcl_13770_schema CASCADE;
DROP OWNED BY dcl_13770_grantee;
DROP OWNED BY dcl_13770_member;
DROP OWNED BY dcl_13770_grantor;
DROP ROLE IF EXISTS dcl_13770_member;
DROP ROLE IF EXISTS dcl_13770_grantor;
DROP ROLE IF EXISTS dcl_13770_grantee;
DROP TABLE IF EXISTS dcl_13770_schema.dcl_13770_table;
