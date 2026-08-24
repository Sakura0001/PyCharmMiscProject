-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_01409_Grantee";
DROP ROLE IF EXISTS dcl_01409_grantor;
DROP ROLE IF EXISTS dcl_01409_member;
CREATE ROLE "dcl_01409_Grantee";
CREATE ROLE dcl_01409_grantor;
CREATE ROLE dcl_01409_member;
GRANT CONNECT ON DATABASE dcl_01409_database TO dcl_01409_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_01409_grantor;
GRANT CONNECT ON DATABASE dcl_01409_database TO SESSION_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY "dcl_01409_Grantee";
DROP OWNED BY dcl_01409_member;
DROP OWNED BY dcl_01409_grantor;
DROP ROLE IF EXISTS dcl_01409_member;
DROP ROLE IF EXISTS dcl_01409_grantor;
DROP ROLE IF EXISTS "dcl_01409_Grantee";
