-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_02864_grantee;
DROP ROLE IF EXISTS dcl_02864_grantor;
DROP ROLE IF EXISTS dcl_02864_member;
CREATE ROLE dcl_02864_grantee;
CREATE ROLE dcl_02864_grantor;
CREATE ROLE dcl_02864_member;
DROP SERVER IF EXISTS dcl_02864_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02864_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02864_fdw;
CREATE SERVER dcl_02864_server FOREIGN DATA WRAPPER dcl_02864_fdw;
BEGIN;
SET ROLE dcl_02864_grantee;
GRANT USAGE ON FOREIGN SERVER dcl_02864_missing_object TO CURRENT_USER WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_02864_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02864_fdw CASCADE;
DROP OWNED BY dcl_02864_grantee;
DROP OWNED BY dcl_02864_member;
DROP OWNED BY dcl_02864_grantor;
DROP ROLE IF EXISTS dcl_02864_member;
DROP ROLE IF EXISTS dcl_02864_grantor;
DROP ROLE IF EXISTS dcl_02864_grantee;
