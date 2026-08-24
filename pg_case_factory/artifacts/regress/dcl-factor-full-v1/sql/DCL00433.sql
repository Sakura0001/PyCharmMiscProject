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
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_00433_table;
DROP ROLE IF EXISTS dcl_00433_grantor;
DROP ROLE IF EXISTS dcl_00433_member;
CREATE ROLE dcl_00433_grantor;
CREATE ROLE dcl_00433_member;
CREATE TABLE dcl_00433_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_00433_missing_object TO dcl_00433_grantor WITH GRANT OPTION;
GRANT dcl_00433_grantor TO dcl_00433_member WITH SET TRUE;
SET ROLE dcl_00433_member;
SET ROLE dcl_00433_grantor;
GRANT EXECUTE ON TABLE dcl_00433_missing_object TO PUBLIC;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_maintain' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_00433_member;
DROP OWNED BY dcl_00433_grantor;
DROP ROLE IF EXISTS dcl_00433_member;
DROP ROLE IF EXISTS dcl_00433_grantor;
DROP TABLE IF EXISTS dcl_00433_table;
