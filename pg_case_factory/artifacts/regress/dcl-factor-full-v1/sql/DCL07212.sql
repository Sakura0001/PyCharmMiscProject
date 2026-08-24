-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_07212_table;
DROP ROLE IF EXISTS "dcl_07212_Grantee";
DROP ROLE IF EXISTS dcl_07212_grantor;
DROP ROLE IF EXISTS dcl_07212_member;
CREATE ROLE "dcl_07212_Grantee";
CREATE ROLE dcl_07212_grantor;
CREATE ROLE dcl_07212_member;
CREATE TABLE dcl_07212_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_07212_missing_object TO "dcl_07212_Grantee";
SET ROLE "dcl_07212_Grantee";
REVOKE GRANT OPTION FOR MAINTAIN ON TABLE dcl_07212_missing_object FROM "dcl_07212_Grantee" GRANTED BY dcl_07212_grantor RESTRICT;
RESET ROLE;
SET ROLE "dcl_07212_Grantee";
SELECT count(*) AS privilege_effect_rows FROM dcl_07212_table;
RESET ROLE;
DROP OWNED BY "dcl_07212_Grantee";
DROP OWNED BY dcl_07212_member;
DROP OWNED BY dcl_07212_grantor;
DROP ROLE IF EXISTS dcl_07212_member;
DROP ROLE IF EXISTS dcl_07212_grantor;
DROP ROLE IF EXISTS "dcl_07212_Grantee";
DROP TABLE IF EXISTS dcl_07212_table;
