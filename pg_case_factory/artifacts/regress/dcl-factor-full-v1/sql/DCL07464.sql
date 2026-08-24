-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07464_table;
DROP ROLE IF EXISTS "dcl_07464_Grantee";
DROP ROLE IF EXISTS dcl_07464_grantor;
DROP ROLE IF EXISTS dcl_07464_member;
CREATE ROLE "dcl_07464_Grantee";
CREATE ROLE dcl_07464_grantor;
CREATE ROLE dcl_07464_member;
CREATE TABLE dcl_07464_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07464_missing_object TO CURRENT_USER;
SET ROLE "dcl_07464_Grantee";
REVOKE INHERIT OPTION FOR EXECUTE (payload) ON TABLE dcl_07464_missing_object FROM CURRENT_USER GRANTED BY dcl_07464_grantor RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_07464_table;
DROP OWNED BY "dcl_07464_Grantee";
DROP OWNED BY dcl_07464_member;
DROP OWNED BY dcl_07464_grantor;
DROP ROLE IF EXISTS dcl_07464_member;
DROP ROLE IF EXISTS dcl_07464_grantor;
DROP ROLE IF EXISTS "dcl_07464_Grantee";
DROP TABLE IF EXISTS dcl_07464_table;
