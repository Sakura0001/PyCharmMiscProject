-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP TABLE IF EXISTS dcl_06947_schema.dcl_06947_table;
DROP ROLE IF EXISTS dcl_06947_grantee;
DROP ROLE IF EXISTS dcl_06947_grantor;
DROP ROLE IF EXISTS dcl_06947_member;
CREATE ROLE dcl_06947_grantee;
CREATE ROLE dcl_06947_grantor;
CREATE ROLE dcl_06947_member;
DROP SCHEMA IF EXISTS dcl_06947_schema CASCADE;
CREATE SCHEMA dcl_06947_schema;
CREATE TABLE dcl_06947_schema.dcl_06947_table (id integer, payload text);
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_06947_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_06947_grantee;
REVOKE GRANT OPTION FOR SELECT ON ALL TABLES IN SCHEMA dcl_06947_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_06947_schema.dcl_06947_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_06947_schema CASCADE;
DROP OWNED BY dcl_06947_grantee;
DROP OWNED BY dcl_06947_member;
DROP OWNED BY dcl_06947_grantor;
DROP ROLE IF EXISTS dcl_06947_member;
DROP ROLE IF EXISTS dcl_06947_grantor;
DROP ROLE IF EXISTS dcl_06947_grantee;
DROP TABLE IF EXISTS dcl_06947_schema.dcl_06947_table;
