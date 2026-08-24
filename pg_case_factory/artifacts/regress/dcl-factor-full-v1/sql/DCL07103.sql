-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=public
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
DROP TABLE IF EXISTS dcl_07103_schema.dcl_07103_table;
DROP ROLE IF EXISTS dcl_07103_grantee;
DROP ROLE IF EXISTS dcl_07103_grantor;
DROP ROLE IF EXISTS dcl_07103_member;
CREATE ROLE dcl_07103_grantee;
CREATE ROLE dcl_07103_grantor;
CREATE ROLE dcl_07103_member;
DROP SCHEMA IF EXISTS dcl_07103_schema CASCADE;
CREATE SCHEMA dcl_07103_schema;
CREATE TABLE dcl_07103_schema.dcl_07103_table (id integer, payload text);
GRANT SELECT ON ALL TABLES IN SCHEMA dcl_07103_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_07103_grantee;
REVOKE GRANT OPTION FOR SELECT ON ALL TABLES IN SCHEMA dcl_07103_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07103_schema.dcl_07103_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07103_schema CASCADE;
DROP OWNED BY dcl_07103_grantee;
DROP OWNED BY dcl_07103_member;
DROP OWNED BY dcl_07103_grantor;
DROP ROLE IF EXISTS dcl_07103_member;
DROP ROLE IF EXISTS dcl_07103_grantor;
DROP ROLE IF EXISTS dcl_07103_grantee;
DROP TABLE IF EXISTS dcl_07103_schema.dcl_07103_table;
