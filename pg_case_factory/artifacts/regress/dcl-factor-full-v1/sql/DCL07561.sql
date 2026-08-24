-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07561_table;
DROP ROLE IF EXISTS dcl_07561_grantor;
DROP ROLE IF EXISTS dcl_07561_member;
CREATE ROLE dcl_07561_grantor;
CREATE ROLE dcl_07561_member;
CREATE TABLE dcl_07561_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07561_missing_object TO CURRENT_ROLE;
GRANT EXECUTE ON TABLE dcl_07561_missing_object TO dcl_07561_grantor WITH GRANT OPTION;
GRANT dcl_07561_grantor TO dcl_07561_member WITH SET TRUE;
SET ROLE dcl_07561_member;
SET ROLE dcl_07561_grantor;
REVOKE EXECUTE ON TABLE dcl_07561_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_07561_member;
DROP OWNED BY dcl_07561_grantor;
DROP ROLE IF EXISTS dcl_07561_member;
DROP ROLE IF EXISTS dcl_07561_grantor;
DROP TABLE IF EXISTS dcl_07561_table;
