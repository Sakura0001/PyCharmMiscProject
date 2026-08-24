-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP TABLE IF EXISTS dcl_00704_table;
DROP ROLE IF EXISTS dcl_00704_grantee;
DROP ROLE IF EXISTS dcl_00704_grantor;
DROP ROLE IF EXISTS dcl_00704_member;
CREATE ROLE dcl_00704_grantee;
CREATE ROLE dcl_00704_grantor;
CREATE ROLE dcl_00704_member;
CREATE TABLE dcl_00704_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00704_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00704_missing_object TO PUBLIC GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_00704_table;
ROLLBACK;
DROP OWNED BY dcl_00704_grantee;
DROP OWNED BY dcl_00704_member;
DROP OWNED BY dcl_00704_grantor;
DROP ROLE IF EXISTS dcl_00704_member;
DROP ROLE IF EXISTS dcl_00704_grantor;
DROP ROLE IF EXISTS dcl_00704_grantee;
DROP TABLE IF EXISTS dcl_00704_table;
