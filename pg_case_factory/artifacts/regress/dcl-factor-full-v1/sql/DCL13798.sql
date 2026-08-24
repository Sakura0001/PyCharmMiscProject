-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=success
-- factor privilege_scope=table_privilege
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
DROP ROLE IF EXISTS dcl_13798_grantee;
DROP ROLE IF EXISTS dcl_13798_grantor;
DROP ROLE IF EXISTS dcl_13798_member;
CREATE ROLE dcl_13798_grantee;
CREATE ROLE dcl_13798_grantor;
CREATE ROLE dcl_13798_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_13798_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_13798_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_13798_fdw TO dcl_13798_grantee;
SELECT true AS fdw_privilege_statement_completed;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_13798_fdw CASCADE;
DROP OWNED BY dcl_13798_grantee;
DROP OWNED BY dcl_13798_member;
DROP OWNED BY dcl_13798_grantor;
DROP ROLE IF EXISTS dcl_13798_member;
DROP ROLE IF EXISTS dcl_13798_grantor;
DROP ROLE IF EXISTS dcl_13798_grantee;
