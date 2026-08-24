-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11496_Grantee";
DROP ROLE IF EXISTS dcl_11496_grantor;
DROP ROLE IF EXISTS dcl_11496_member;
CREATE ROLE "dcl_11496_Grantee";
CREATE ROLE dcl_11496_grantor;
CREATE ROLE dcl_11496_member;
GRANT SELECT ON PARAMETER work_mem TO CURRENT_ROLE;
SET ROLE "dcl_11496_Grantee";
REVOKE GRANT OPTION FOR SELECT ON PARAMETER work_mem FROM CURRENT_ROLE GRANTED BY dcl_11496_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP OWNED BY "dcl_11496_Grantee";
DROP OWNED BY dcl_11496_member;
DROP OWNED BY dcl_11496_grantor;
DROP ROLE IF EXISTS dcl_11496_member;
DROP ROLE IF EXISTS dcl_11496_grantor;
DROP ROLE IF EXISTS "dcl_11496_Grantee";
