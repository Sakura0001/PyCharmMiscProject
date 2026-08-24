-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07144_table;
DROP ROLE IF EXISTS dcl_07144_grantor;
DROP ROLE IF EXISTS dcl_07144_member;
CREATE ROLE dcl_07144_grantor;
CREATE ROLE dcl_07144_member;
CREATE TABLE dcl_07144_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07144_missing_object TO SESSION_USER;
GRANT EXECUTE ON TABLE dcl_07144_missing_object TO dcl_07144_grantor WITH GRANT OPTION;
GRANT dcl_07144_grantor TO dcl_07144_member WITH SET TRUE;
SET ROLE dcl_07144_member;
SET ROLE dcl_07144_grantor;
REVOKE INHERIT OPTION FOR EXECUTE ON TABLE dcl_07144_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_07144_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_07144_member;
DROP OWNED BY dcl_07144_grantor;
DROP ROLE IF EXISTS dcl_07144_member;
DROP ROLE IF EXISTS dcl_07144_grantor;
DROP TABLE IF EXISTS dcl_07144_table;
