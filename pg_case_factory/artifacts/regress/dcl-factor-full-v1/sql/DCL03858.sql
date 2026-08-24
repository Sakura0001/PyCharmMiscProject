-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_03858_Grantee";
DROP ROLE IF EXISTS dcl_03858_grantor;
DROP ROLE IF EXISTS dcl_03858_member;
CREATE ROLE "dcl_03858_Grantee";
CREATE ROLE dcl_03858_grantor;
CREATE ROLE dcl_03858_member;
SET ROLE "dcl_03858_Grantee";
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC WITH GRANT OPTION GRANTED BY dcl_03858_grantor;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP OWNED BY "dcl_03858_Grantee";
DROP OWNED BY dcl_03858_member;
DROP OWNED BY dcl_03858_grantor;
DROP ROLE IF EXISTS dcl_03858_member;
DROP ROLE IF EXISTS dcl_03858_grantor;
DROP ROLE IF EXISTS "dcl_03858_Grantee";
