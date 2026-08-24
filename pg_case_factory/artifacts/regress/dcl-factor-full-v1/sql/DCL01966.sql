-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01966_grantor;
DROP ROLE IF EXISTS dcl_01966_member;
CREATE ROLE dcl_01966_grantor;
CREATE ROLE dcl_01966_member;
DROP DOMAIN IF EXISTS dcl_01966_domain;
CREATE DOMAIN dcl_01966_domain AS text;
GRANT USAGE ON DOMAIN dcl_01966_missing_object TO dcl_01966_grantor WITH GRANT OPTION;
GRANT dcl_01966_grantor TO dcl_01966_member WITH SET TRUE;
SET ROLE dcl_01966_member;
SET ROLE dcl_01966_grantor;
GRANT USAGE ON DOMAIN dcl_01966_missing_object TO CURRENT_USER WITH INHERIT TRUE;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_01966_domain;
DROP OWNED BY dcl_01966_member;
DROP OWNED BY dcl_01966_grantor;
DROP ROLE IF EXISTS dcl_01966_member;
DROP ROLE IF EXISTS dcl_01966_grantor;
