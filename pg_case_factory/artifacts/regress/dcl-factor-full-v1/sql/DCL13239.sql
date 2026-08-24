-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_13239_Grantee";
DROP ROLE IF EXISTS dcl_13239_grantor;
DROP ROLE IF EXISTS dcl_13239_member;
CREATE ROLE "dcl_13239_Grantee";
CREATE ROLE dcl_13239_grantor;
CREATE ROLE dcl_13239_member;
SET ROLE "dcl_13239_Grantee";
REVOKE dcl_13239_missing_member FROM CURRENT_ROLE GRANTED BY dcl_13239_grantor RESTRICT;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
DROP OWNED BY "dcl_13239_Grantee";
DROP OWNED BY dcl_13239_member;
DROP OWNED BY dcl_13239_grantor;
DROP ROLE IF EXISTS dcl_13239_member;
DROP ROLE IF EXISTS dcl_13239_grantor;
DROP ROLE IF EXISTS "dcl_13239_Grantee";
