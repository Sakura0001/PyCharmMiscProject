-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_04883_grantee;
DROP ROLE IF EXISTS dcl_04883_grantor;
DROP ROLE IF EXISTS dcl_04883_member;
CREATE ROLE dcl_04883_grantee;
CREATE ROLE dcl_04883_grantor;
CREATE ROLE dcl_04883_member;
BEGIN;
SET ROLE dcl_04883_grantee;
GRANT SET ON PARAMETER work_mem TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
ROLLBACK;
DROP OWNED BY dcl_04883_grantee;
DROP OWNED BY dcl_04883_member;
DROP OWNED BY dcl_04883_grantor;
DROP ROLE IF EXISTS dcl_04883_member;
DROP ROLE IF EXISTS dcl_04883_grantor;
DROP ROLE IF EXISTS dcl_04883_grantee;
