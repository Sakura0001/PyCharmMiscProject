-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_00908_table;
DROP ROLE IF EXISTS dcl_00908_grantee;
DROP ROLE IF EXISTS dcl_00908_grantor;
DROP ROLE IF EXISTS dcl_00908_member;
CREATE ROLE dcl_00908_grantee;
CREATE ROLE dcl_00908_grantor;
CREATE ROLE dcl_00908_member;
CREATE TABLE dcl_00908_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00908_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00908_missing_object TO CURRENT_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_00908_table;
ROLLBACK;
DROP OWNED BY dcl_00908_grantee;
DROP OWNED BY dcl_00908_member;
DROP OWNED BY dcl_00908_grantor;
DROP ROLE IF EXISTS dcl_00908_member;
DROP ROLE IF EXISTS dcl_00908_grantor;
DROP ROLE IF EXISTS dcl_00908_grantee;
DROP TABLE IF EXISTS dcl_00908_table;
