-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_01812_Grantee";
DROP ROLE IF EXISTS dcl_01812_grantor;
DROP ROLE IF EXISTS dcl_01812_member;
CREATE ROLE "dcl_01812_Grantee";
CREATE ROLE dcl_01812_grantor;
CREATE ROLE dcl_01812_member;
SET ROLE "dcl_01812_Grantee";
GRANT CONNECT ON DATABASE dcl_01812_missing_object TO CURRENT_USER WITH GRANT OPTION GRANTED BY dcl_01812_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP OWNED BY "dcl_01812_Grantee";
DROP OWNED BY dcl_01812_member;
DROP OWNED BY dcl_01812_grantor;
DROP ROLE IF EXISTS dcl_01812_member;
DROP ROLE IF EXISTS dcl_01812_grantor;
DROP ROLE IF EXISTS "dcl_01812_Grantee";
