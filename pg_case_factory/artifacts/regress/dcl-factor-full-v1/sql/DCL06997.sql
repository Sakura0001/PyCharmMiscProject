-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_06997_table;
DROP ROLE IF EXISTS dcl_06997_grantor;
DROP ROLE IF EXISTS dcl_06997_member;
CREATE ROLE dcl_06997_grantor;
CREATE ROLE dcl_06997_member;
CREATE TABLE dcl_06997_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_06997_missing_object TO CURRENT_ROLE;
GRANT EXECUTE ON TABLE dcl_06997_missing_object TO dcl_06997_grantor WITH GRANT OPTION;
GRANT dcl_06997_grantor TO dcl_06997_member WITH SET TRUE;
SET ROLE dcl_06997_member;
SET ROLE dcl_06997_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON TABLE dcl_06997_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06997_member;
DROP OWNED BY dcl_06997_grantor;
DROP ROLE IF EXISTS dcl_06997_member;
DROP ROLE IF EXISTS dcl_06997_grantor;
DROP TABLE IF EXISTS dcl_06997_table;
