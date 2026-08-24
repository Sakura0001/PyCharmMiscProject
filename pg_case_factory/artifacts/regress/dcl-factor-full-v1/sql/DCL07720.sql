-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_07720_grantee;
DROP ROLE IF EXISTS dcl_07720_grantor;
DROP ROLE IF EXISTS dcl_07720_member;
CREATE ROLE dcl_07720_grantee;
CREATE ROLE dcl_07720_grantor;
CREATE ROLE dcl_07720_member;
DROP SEQUENCE IF EXISTS dcl_07720_sequence;
CREATE SEQUENCE dcl_07720_sequence;
GRANT USAGE ON SEQUENCE dcl_07720_sequence TO dcl_07720_grantee;
REVOKE GRANT OPTION FOR USAGE ON SEQUENCE dcl_07720_sequence FROM dcl_07720_grantee RESTRICT;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07720_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_07720_sequence;
DROP OWNED BY dcl_07720_grantee;
DROP OWNED BY dcl_07720_member;
DROP OWNED BY dcl_07720_grantor;
DROP ROLE IF EXISTS dcl_07720_member;
DROP ROLE IF EXISTS dcl_07720_grantor;
DROP ROLE IF EXISTS dcl_07720_grantee;
