-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_01455_Grantee";
DROP ROLE IF EXISTS dcl_01455_grantor;
DROP ROLE IF EXISTS dcl_01455_member;
CREATE ROLE "dcl_01455_Grantee";
CREATE ROLE dcl_01455_grantor;
CREATE ROLE dcl_01455_member;
SET ROLE "dcl_01455_Grantee";
GRANT CONNECT ON DATABASE dcl_01455_missing_object TO CURRENT_USER WITH ADMIN OPTION GRANTED BY dcl_01455_grantor;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_01455_database', 'CONNECT');
DROP OWNED BY "dcl_01455_Grantee";
DROP OWNED BY dcl_01455_member;
DROP OWNED BY dcl_01455_grantor;
DROP ROLE IF EXISTS dcl_01455_member;
DROP ROLE IF EXISTS dcl_01455_grantor;
DROP ROLE IF EXISTS "dcl_01455_Grantee";
