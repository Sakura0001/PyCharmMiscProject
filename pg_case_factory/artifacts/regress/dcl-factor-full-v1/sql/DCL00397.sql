-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_00397_table;
DROP ROLE IF EXISTS dcl_00397_grantor;
DROP ROLE IF EXISTS dcl_00397_member;
CREATE ROLE dcl_00397_grantor;
CREATE ROLE dcl_00397_member;
CREATE TABLE dcl_00397_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_00397_missing_object TO dcl_00397_grantor WITH GRANT OPTION;
GRANT dcl_00397_grantor TO dcl_00397_member WITH SET TRUE;
SET ROLE dcl_00397_member;
SET ROLE dcl_00397_grantor;
GRANT EXECUTE ON TABLE dcl_00397_missing_object TO CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_00397_member;
DROP OWNED BY dcl_00397_grantor;
DROP ROLE IF EXISTS dcl_00397_member;
DROP ROLE IF EXISTS dcl_00397_grantor;
DROP TABLE IF EXISTS dcl_00397_table;
