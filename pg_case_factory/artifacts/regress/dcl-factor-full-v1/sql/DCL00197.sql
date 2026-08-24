-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_00197_table;
DROP ROLE IF EXISTS dcl_00197_grantee;
DROP ROLE IF EXISTS dcl_00197_grantor;
DROP ROLE IF EXISTS dcl_00197_member;
CREATE ROLE dcl_00197_grantee;
CREATE ROLE dcl_00197_grantor;
CREATE ROLE dcl_00197_member;
CREATE TABLE dcl_00197_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00197_grantee;
GRANT SELECT ON TABLE dcl_00197_missing_object TO PUBLIC WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_00197_grantee;
DROP OWNED BY dcl_00197_member;
DROP OWNED BY dcl_00197_grantor;
DROP ROLE IF EXISTS dcl_00197_member;
DROP ROLE IF EXISTS dcl_00197_grantor;
DROP ROLE IF EXISTS dcl_00197_grantee;
DROP TABLE IF EXISTS dcl_00197_table;
