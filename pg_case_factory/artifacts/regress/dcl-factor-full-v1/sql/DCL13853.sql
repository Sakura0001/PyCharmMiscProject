-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
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
DROP ROLE IF EXISTS dcl_13853_grantee;
DROP ROLE IF EXISTS dcl_13853_grantor;
DROP ROLE IF EXISTS dcl_13853_member;
CREATE ROLE dcl_13853_grantee;
CREATE ROLE dcl_13853_grantor;
CREATE ROLE dcl_13853_member;
DROP TYPE IF EXISTS dcl_13853_type;
CREATE TYPE dcl_13853_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_13853_type TO dcl_13853_grantee;
REVOKE USAGE ON TYPE dcl_13853_type FROM dcl_13853_grantee RESTRICT;
SELECT has_type_privilege(CURRENT_USER, 'dcl_13853_type', 'USAGE');
DROP TYPE IF EXISTS dcl_13853_type;
DROP OWNED BY dcl_13853_grantee;
DROP OWNED BY dcl_13853_member;
DROP OWNED BY dcl_13853_grantor;
DROP ROLE IF EXISTS dcl_13853_member;
DROP ROLE IF EXISTS dcl_13853_grantor;
DROP ROLE IF EXISTS dcl_13853_grantee;
