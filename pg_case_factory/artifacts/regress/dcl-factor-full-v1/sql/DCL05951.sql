-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_05951_grantee;
DROP ROLE IF EXISTS dcl_05951_grantor;
DROP ROLE IF EXISTS dcl_05951_member;
CREATE ROLE dcl_05951_grantee;
CREATE ROLE dcl_05951_grantor;
CREATE ROLE dcl_05951_member;
DROP TYPE IF EXISTS dcl_05951_type;
CREATE TYPE dcl_05951_type AS ENUM ('alpha', 'beta');
BEGIN;
SET ROLE dcl_05951_grantee;
GRANT USAGE ON TYPE dcl_05951_missing_object TO CURRENT_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_05951_type', 'USAGE');
ROLLBACK;
DROP TYPE IF EXISTS dcl_05951_type;
DROP OWNED BY dcl_05951_grantee;
DROP OWNED BY dcl_05951_member;
DROP OWNED BY dcl_05951_grantor;
DROP ROLE IF EXISTS dcl_05951_member;
DROP ROLE IF EXISTS dcl_05951_grantor;
DROP ROLE IF EXISTS dcl_05951_grantee;
