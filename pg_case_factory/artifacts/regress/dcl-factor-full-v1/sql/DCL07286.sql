-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_07286_schema.dcl_07286_table;
DROP ROLE IF EXISTS dcl_07286_grantee;
DROP ROLE IF EXISTS dcl_07286_grantor;
DROP ROLE IF EXISTS dcl_07286_member;
CREATE ROLE dcl_07286_grantee;
CREATE ROLE dcl_07286_grantor;
CREATE ROLE dcl_07286_member;
DROP SCHEMA IF EXISTS dcl_07286_schema CASCADE;
CREATE SCHEMA dcl_07286_schema;
CREATE TABLE dcl_07286_schema.dcl_07286_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07286_schema.dcl_07286_table TO CURRENT_USER;
BEGIN;
REVOKE SELECT (payload) ON TABLE dcl_07286_schema.dcl_07286_table FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
SELECT count(*) AS privilege_effect_rows FROM dcl_07286_schema.dcl_07286_table;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07286_schema CASCADE;
DROP OWNED BY dcl_07286_grantee;
DROP OWNED BY dcl_07286_member;
DROP OWNED BY dcl_07286_grantor;
DROP ROLE IF EXISTS dcl_07286_member;
DROP ROLE IF EXISTS dcl_07286_grantor;
DROP ROLE IF EXISTS dcl_07286_grantee;
DROP TABLE IF EXISTS dcl_07286_schema.dcl_07286_table;
