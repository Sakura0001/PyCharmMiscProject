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
-- factor expected_status=success
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_13778_grantee;
DROP ROLE IF EXISTS dcl_13778_grantor;
DROP ROLE IF EXISTS dcl_13778_member;
CREATE ROLE dcl_13778_grantee;
CREATE ROLE dcl_13778_grantor;
CREATE ROLE dcl_13778_member;
GRANT SET ON PARAMETER work_mem TO dcl_13778_grantee;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
DROP OWNED BY dcl_13778_grantee;
DROP OWNED BY dcl_13778_member;
DROP OWNED BY dcl_13778_grantor;
DROP ROLE IF EXISTS dcl_13778_member;
DROP ROLE IF EXISTS dcl_13778_grantor;
DROP ROLE IF EXISTS dcl_13778_grantee;
