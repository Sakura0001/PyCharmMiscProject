-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_07597_table;
DROP ROLE IF EXISTS dcl_07597_grantor;
DROP ROLE IF EXISTS dcl_07597_member;
CREATE ROLE dcl_07597_grantor;
CREATE ROLE dcl_07597_member;
CREATE TABLE dcl_07597_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07597_missing_object TO dcl_07597_missing_role;
GRANT EXECUTE ON TABLE dcl_07597_missing_object TO dcl_07597_grantor WITH GRANT OPTION;
GRANT dcl_07597_grantor TO dcl_07597_member WITH SET TRUE;
SET ROLE dcl_07597_member;
SET ROLE dcl_07597_grantor;
REVOKE EXECUTE ON TABLE dcl_07597_missing_object FROM dcl_07597_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_07597_member;
DROP OWNED BY dcl_07597_grantor;
DROP ROLE IF EXISTS dcl_07597_member;
DROP ROLE IF EXISTS dcl_07597_grantor;
DROP TABLE IF EXISTS dcl_07597_table;
