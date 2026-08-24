-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_00482_schema.dcl_00482_table;
DROP ROLE IF EXISTS dcl_00482_grantee;
DROP ROLE IF EXISTS dcl_00482_grantor;
DROP ROLE IF EXISTS dcl_00482_member;
CREATE ROLE dcl_00482_grantee;
CREATE ROLE dcl_00482_grantor;
CREATE ROLE dcl_00482_member;
DROP SCHEMA IF EXISTS dcl_00482_schema CASCADE;
CREATE SCHEMA dcl_00482_schema;
CREATE TABLE dcl_00482_schema.dcl_00482_table (id integer, payload text);
BEGIN;
GRANT SELECT (payload) ON TABLE dcl_00482_schema.dcl_00482_table TO dcl_00482_grantee GRANTED BY CURRENT_USER;
SET ROLE dcl_00482_grantee;
SELECT count(*) AS privilege_effect_rows FROM dcl_00482_schema.dcl_00482_table;
RESET ROLE;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00482_schema CASCADE;
DROP OWNED BY dcl_00482_grantee;
DROP OWNED BY dcl_00482_member;
DROP OWNED BY dcl_00482_grantor;
DROP ROLE IF EXISTS dcl_00482_member;
DROP ROLE IF EXISTS dcl_00482_grantor;
DROP ROLE IF EXISTS dcl_00482_grantee;
DROP TABLE IF EXISTS dcl_00482_schema.dcl_00482_table;
