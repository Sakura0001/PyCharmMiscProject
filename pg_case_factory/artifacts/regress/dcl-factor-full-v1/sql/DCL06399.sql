-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_06399_Grantee";
DROP ROLE IF EXISTS dcl_06399_grantor;
DROP ROLE IF EXISTS dcl_06399_member;
CREATE ROLE "dcl_06399_Grantee";
CREATE ROLE dcl_06399_grantor;
CREATE ROLE dcl_06399_member;
SET ROLE "dcl_06399_Grantee";
GRANT dcl_06399_missing_member TO CURRENT_ROLE WITH ADMIN OPTION GRANTED BY dcl_06399_grantor;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
DROP OWNED BY "dcl_06399_Grantee";
DROP OWNED BY dcl_06399_member;
DROP OWNED BY dcl_06399_grantor;
DROP ROLE IF EXISTS dcl_06399_member;
DROP ROLE IF EXISTS dcl_06399_grantor;
DROP ROLE IF EXISTS "dcl_06399_Grantee";
