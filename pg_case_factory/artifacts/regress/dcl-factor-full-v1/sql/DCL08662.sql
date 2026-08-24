-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_08662_grantor;
DROP ROLE IF EXISTS dcl_08662_member;
CREATE ROLE dcl_08662_grantor;
CREATE ROLE dcl_08662_member;
DROP DOMAIN IF EXISTS dcl_08662_domain;
CREATE DOMAIN dcl_08662_domain AS text;
GRANT USAGE ON DOMAIN dcl_08662_missing_object TO PUBLIC;
GRANT USAGE ON DOMAIN dcl_08662_missing_object TO dcl_08662_grantor WITH GRANT OPTION;
GRANT dcl_08662_grantor TO dcl_08662_member WITH SET TRUE;
SET ROLE dcl_08662_member;
SET ROLE dcl_08662_grantor;
REVOKE GRANT OPTION FOR USAGE ON DOMAIN dcl_08662_missing_object FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_08662_domain;
DROP OWNED BY dcl_08662_member;
DROP OWNED BY dcl_08662_grantor;
DROP ROLE IF EXISTS dcl_08662_member;
DROP ROLE IF EXISTS dcl_08662_grantor;
