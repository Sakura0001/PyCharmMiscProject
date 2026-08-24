-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS dcl_08713_grantor;
DROP ROLE IF EXISTS dcl_08713_member;
CREATE ROLE dcl_08713_grantor;
CREATE ROLE dcl_08713_member;
DROP DOMAIN IF EXISTS dcl_08713_domain;
CREATE DOMAIN dcl_08713_domain AS text;
GRANT USAGE ON DOMAIN dcl_08713_missing_object TO dcl_08713_missing_role;
GRANT USAGE ON DOMAIN dcl_08713_missing_object TO dcl_08713_grantor WITH GRANT OPTION;
GRANT dcl_08713_grantor TO dcl_08713_member WITH SET TRUE;
SET ROLE dcl_08713_member;
SET ROLE dcl_08713_grantor;
REVOKE ADMIN OPTION FOR USAGE ON DOMAIN dcl_08713_missing_object FROM dcl_08713_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_08713_domain;
DROP OWNED BY dcl_08713_member;
DROP OWNED BY dcl_08713_grantor;
DROP ROLE IF EXISTS dcl_08713_member;
DROP ROLE IF EXISTS dcl_08713_grantor;
