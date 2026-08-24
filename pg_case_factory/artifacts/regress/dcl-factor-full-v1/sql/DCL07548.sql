-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
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
DROP TABLE IF EXISTS dcl_07548_table;
DROP ROLE IF EXISTS "dcl_07548_Grantee";
DROP ROLE IF EXISTS dcl_07548_grantor;
DROP ROLE IF EXISTS dcl_07548_member;
CREATE ROLE "dcl_07548_Grantee";
CREATE ROLE dcl_07548_grantor;
CREATE ROLE dcl_07548_member;
CREATE TABLE dcl_07548_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07548_missing_object TO "dcl_07548_Grantee";
SET ROLE "dcl_07548_Grantee";
REVOKE INHERIT OPTION FOR EXECUTE (payload) ON TABLE dcl_07548_missing_object FROM "dcl_07548_Grantee" GRANTED BY dcl_07548_grantor RESTRICT;
RESET ROLE;
SET ROLE "dcl_07548_Grantee";
SELECT count(*) AS privilege_effect_rows FROM dcl_07548_table;
RESET ROLE;
DROP OWNED BY "dcl_07548_Grantee";
DROP OWNED BY dcl_07548_member;
DROP OWNED BY dcl_07548_grantor;
DROP ROLE IF EXISTS dcl_07548_member;
DROP ROLE IF EXISTS dcl_07548_grantor;
DROP ROLE IF EXISTS "dcl_07548_Grantee";
DROP TABLE IF EXISTS dcl_07548_table;
