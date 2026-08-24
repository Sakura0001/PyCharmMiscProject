-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_03635_Grantee";
DROP ROLE IF EXISTS dcl_03635_grantor;
DROP ROLE IF EXISTS dcl_03635_member;
CREATE ROLE "dcl_03635_Grantee";
CREATE ROLE dcl_03635_grantor;
CREATE ROLE dcl_03635_member;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_03635_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_03635_grantor;
GRANT USAGE ON LANGUAGE plpgsql TO "dcl_03635_Grantee" WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY "dcl_03635_Grantee";
DROP OWNED BY dcl_03635_member;
DROP OWNED BY dcl_03635_grantor;
DROP ROLE IF EXISTS dcl_03635_member;
DROP ROLE IF EXISTS dcl_03635_grantor;
DROP ROLE IF EXISTS "dcl_03635_Grantee";
