-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS "dcl_12603_Grantee";
DROP ROLE IF EXISTS dcl_12603_grantor;
DROP ROLE IF EXISTS dcl_12603_member;
CREATE ROLE "dcl_12603_Grantee";
CREATE ROLE dcl_12603_grantor;
CREATE ROLE dcl_12603_member;
GRANT CREATE ON TABLESPACE dcl_12603_missing_object TO SESSION_USER;
SET ROLE "dcl_12603_Grantee";
REVOKE ADMIN OPTION FOR CREATE ON TABLESPACE dcl_12603_missing_object FROM SESSION_USER GRANTED BY dcl_12603_grantor RESTRICT;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_12603_tablespace', 'CREATE');
DROP OWNED BY "dcl_12603_Grantee";
DROP OWNED BY dcl_12603_member;
DROP OWNED BY dcl_12603_grantor;
DROP ROLE IF EXISTS dcl_12603_member;
DROP ROLE IF EXISTS dcl_12603_grantor;
DROP ROLE IF EXISTS "dcl_12603_Grantee";
