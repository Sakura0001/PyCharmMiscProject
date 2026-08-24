-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_00952_grantee;
DROP ROLE IF EXISTS dcl_00952_grantor;
DROP ROLE IF EXISTS dcl_00952_member;
CREATE ROLE dcl_00952_grantee;
CREATE ROLE dcl_00952_grantor;
CREATE ROLE dcl_00952_member;
DROP SEQUENCE IF EXISTS dcl_00952_sequence;
CREATE SEQUENCE dcl_00952_sequence;
GRANT USAGE ON SEQUENCE dcl_00952_sequence TO CURRENT_USER WITH GRANT OPTION;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_00952_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_00952_sequence;
DROP OWNED BY dcl_00952_grantee;
DROP OWNED BY dcl_00952_member;
DROP OWNED BY dcl_00952_grantor;
DROP ROLE IF EXISTS dcl_00952_member;
DROP ROLE IF EXISTS dcl_00952_grantor;
DROP ROLE IF EXISTS dcl_00952_grantee;
