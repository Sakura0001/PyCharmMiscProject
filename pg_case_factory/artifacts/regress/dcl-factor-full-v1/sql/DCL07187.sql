-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP TABLE IF EXISTS dcl_07187_schema.dcl_07187_table;
DROP ROLE IF EXISTS dcl_07187_grantee;
DROP ROLE IF EXISTS dcl_07187_grantor;
DROP ROLE IF EXISTS dcl_07187_member;
CREATE ROLE dcl_07187_grantee;
CREATE ROLE dcl_07187_grantor;
CREATE ROLE dcl_07187_member;
DROP SCHEMA IF EXISTS dcl_07187_schema CASCADE;
CREATE SCHEMA dcl_07187_schema;
CREATE TABLE dcl_07187_schema.dcl_07187_table (id integer, payload text);
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_07187_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_07187_grantee;
REVOKE GRANT OPTION FOR SELECT ON ALL TABLES IN SCHEMA dcl_07187_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07187_schema.dcl_07187_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07187_schema CASCADE;
DROP OWNED BY dcl_07187_grantee;
DROP OWNED BY dcl_07187_member;
DROP OWNED BY dcl_07187_grantor;
DROP ROLE IF EXISTS dcl_07187_member;
DROP ROLE IF EXISTS dcl_07187_grantor;
DROP ROLE IF EXISTS dcl_07187_grantee;
DROP TABLE IF EXISTS dcl_07187_schema.dcl_07187_table;
