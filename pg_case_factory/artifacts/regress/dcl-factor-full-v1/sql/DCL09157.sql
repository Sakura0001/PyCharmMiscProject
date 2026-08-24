-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS dcl_09157_grantor;
DROP ROLE IF EXISTS dcl_09157_member;
CREATE ROLE dcl_09157_grantor;
CREATE ROLE dcl_09157_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09157_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09157_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09157_missing_object TO dcl_09157_missing_role;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09157_missing_object TO dcl_09157_grantor WITH GRANT OPTION;
GRANT dcl_09157_grantor TO dcl_09157_member WITH SET TRUE;
SET ROLE dcl_09157_member;
SET ROLE dcl_09157_grantor;
REVOKE USAGE ON FOREIGN DATA WRAPPER dcl_09157_missing_object FROM dcl_09157_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09157_fdw CASCADE;
DROP OWNED BY dcl_09157_member;
DROP OWNED BY dcl_09157_grantor;
DROP ROLE IF EXISTS dcl_09157_member;
DROP ROLE IF EXISTS dcl_09157_grantor;
