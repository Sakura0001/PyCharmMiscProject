-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_10 (large_object) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_04474_grantor;
DROP ROLE IF EXISTS dcl_04474_member;
CREATE ROLE dcl_04474_grantor;
CREATE ROLE dcl_04474_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_04474_grantor WITH GRANT OPTION;
GRANT dcl_04474_grantor TO dcl_04474_member WITH SET TRUE;
SET ROLE dcl_04474_member;
SET ROLE dcl_04474_grantor;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_04474_missing_role WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_04474_member;
DROP OWNED BY dcl_04474_grantor;
DROP ROLE IF EXISTS dcl_04474_member;
DROP ROLE IF EXISTS dcl_04474_grantor;
