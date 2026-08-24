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
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_07213_table;
DROP ROLE IF EXISTS dcl_07213_grantor;
DROP ROLE IF EXISTS dcl_07213_member;
CREATE ROLE dcl_07213_grantor;
CREATE ROLE dcl_07213_member;
CREATE TABLE dcl_07213_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07213_missing_object TO dcl_07213_missing_role;
GRANT EXECUTE ON TABLE dcl_07213_missing_object TO dcl_07213_grantor WITH GRANT OPTION;
GRANT dcl_07213_grantor TO dcl_07213_member WITH SET TRUE;
SET ROLE dcl_07213_member;
SET ROLE dcl_07213_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON TABLE dcl_07213_missing_object FROM dcl_07213_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_07213_member;
DROP OWNED BY dcl_07213_grantor;
DROP ROLE IF EXISTS dcl_07213_member;
DROP ROLE IF EXISTS dcl_07213_grantor;
DROP TABLE IF EXISTS dcl_07213_table;
