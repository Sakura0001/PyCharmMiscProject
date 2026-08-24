-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07235_schema.dcl_07235_table;
DROP ROLE IF EXISTS dcl_07235_grantee;
DROP ROLE IF EXISTS dcl_07235_grantor;
DROP ROLE IF EXISTS dcl_07235_member;
CREATE ROLE dcl_07235_grantee;
CREATE ROLE dcl_07235_grantor;
CREATE ROLE dcl_07235_member;
DROP SCHEMA IF EXISTS dcl_07235_schema CASCADE;
CREATE SCHEMA dcl_07235_schema;
CREATE TABLE dcl_07235_schema.dcl_07235_table (id integer, payload text);
GRANT MAINTAIN ON ALL TABLES IN SCHEMA dcl_07235_missing_object TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_07235_grantee;
REVOKE GRANT OPTION FOR MAINTAIN ON ALL TABLES IN SCHEMA dcl_07235_missing_object FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07235_schema.dcl_07235_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07235_schema CASCADE;
DROP OWNED BY dcl_07235_grantee;
DROP OWNED BY dcl_07235_member;
DROP OWNED BY dcl_07235_grantor;
DROP ROLE IF EXISTS dcl_07235_member;
DROP ROLE IF EXISTS dcl_07235_grantor;
DROP ROLE IF EXISTS dcl_07235_grantee;
DROP TABLE IF EXISTS dcl_07235_schema.dcl_07235_table;
