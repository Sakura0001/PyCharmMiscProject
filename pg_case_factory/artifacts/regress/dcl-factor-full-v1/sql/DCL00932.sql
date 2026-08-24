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
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_00932_grantee;
DROP ROLE IF EXISTS dcl_00932_grantor;
DROP ROLE IF EXISTS dcl_00932_member;
CREATE ROLE dcl_00932_grantee;
CREATE ROLE dcl_00932_grantor;
CREATE ROLE dcl_00932_member;
DROP SEQUENCE IF EXISTS dcl_00932_sequence;
CREATE SEQUENCE dcl_00932_sequence;
BEGIN;
GRANT USAGE ON SEQUENCE dcl_00932_sequence TO dcl_00932_grantee GRANTED BY CURRENT_USER;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_00932_sequence;
DROP OWNED BY dcl_00932_grantee;
DROP OWNED BY dcl_00932_member;
DROP OWNED BY dcl_00932_grantor;
DROP ROLE IF EXISTS dcl_00932_member;
DROP ROLE IF EXISTS dcl_00932_grantor;
DROP ROLE IF EXISTS dcl_00932_grantee;
