-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_00155_schema.dcl_00155_table;
DROP ROLE IF EXISTS dcl_00155_grantee;
DROP ROLE IF EXISTS dcl_00155_grantor;
DROP ROLE IF EXISTS dcl_00155_member;
CREATE ROLE dcl_00155_grantee;
CREATE ROLE dcl_00155_grantor;
CREATE ROLE dcl_00155_member;
DROP SCHEMA IF EXISTS dcl_00155_schema CASCADE;
CREATE SCHEMA dcl_00155_schema;
CREATE TABLE dcl_00155_schema.dcl_00155_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00155_grantee;
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_00155_missing_object TO CURRENT_ROLE WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00155_schema.dcl_00155_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00155_schema CASCADE;
DROP OWNED BY dcl_00155_grantee;
DROP OWNED BY dcl_00155_member;
DROP OWNED BY dcl_00155_grantor;
DROP ROLE IF EXISTS dcl_00155_member;
DROP ROLE IF EXISTS dcl_00155_grantor;
DROP ROLE IF EXISTS dcl_00155_grantee;
DROP TABLE IF EXISTS dcl_00155_schema.dcl_00155_table;
