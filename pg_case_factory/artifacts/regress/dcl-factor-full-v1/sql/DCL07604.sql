-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_07604_table;
DROP ROLE IF EXISTS dcl_07604_grantee;
DROP ROLE IF EXISTS dcl_07604_grantor;
DROP ROLE IF EXISTS dcl_07604_member;
CREATE ROLE dcl_07604_grantee;
CREATE ROLE dcl_07604_grantor;
CREATE ROLE dcl_07604_member;
CREATE TABLE dcl_07604_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07604_missing_object TO dcl_07604_grantee;
BEGIN;
SET ROLE dcl_07604_grantee;
REVOKE ADMIN OPTION FOR EXECUTE (payload) ON TABLE dcl_07604_missing_object FROM dcl_07604_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SET ROLE dcl_07604_grantee;
SELECT count(*) AS privilege_effect_rows FROM dcl_07604_table;
RESET ROLE;
ROLLBACK;
DROP OWNED BY dcl_07604_grantee;
DROP OWNED BY dcl_07604_member;
DROP OWNED BY dcl_07604_grantor;
DROP ROLE IF EXISTS dcl_07604_member;
DROP ROLE IF EXISTS dcl_07604_grantor;
DROP ROLE IF EXISTS dcl_07604_grantee;
DROP TABLE IF EXISTS dcl_07604_table;
