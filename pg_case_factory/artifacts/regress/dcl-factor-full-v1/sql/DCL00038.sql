-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_00038_schema.dcl_00038_table;
DROP ROLE IF EXISTS dcl_00038_grantee;
DROP ROLE IF EXISTS dcl_00038_grantor;
DROP ROLE IF EXISTS dcl_00038_member;
CREATE ROLE dcl_00038_grantee;
CREATE ROLE dcl_00038_grantor;
CREATE ROLE dcl_00038_member;
DROP SCHEMA IF EXISTS dcl_00038_schema CASCADE;
CREATE SCHEMA dcl_00038_schema;
CREATE TABLE dcl_00038_schema.dcl_00038_table (id integer, payload text);
BEGIN;
GRANT MAINTAIN ON TABLE dcl_00038_schema.dcl_00038_table TO PUBLIC GRANTED BY CURRENT_USER;
SELECT count(*) AS privilege_effect_rows FROM dcl_00038_schema.dcl_00038_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00038_schema CASCADE;
DROP OWNED BY dcl_00038_grantee;
DROP OWNED BY dcl_00038_member;
DROP OWNED BY dcl_00038_grantor;
DROP ROLE IF EXISTS dcl_00038_member;
DROP ROLE IF EXISTS dcl_00038_grantor;
DROP ROLE IF EXISTS dcl_00038_grantee;
DROP TABLE IF EXISTS dcl_00038_schema.dcl_00038_table;
