-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_07148_table;
DROP ROLE IF EXISTS dcl_07148_grantee;
DROP ROLE IF EXISTS dcl_07148_grantor;
DROP ROLE IF EXISTS dcl_07148_member;
CREATE ROLE dcl_07148_grantee;
CREATE ROLE dcl_07148_grantor;
CREATE ROLE dcl_07148_member;
CREATE TABLE dcl_07148_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_07148_missing_object TO dcl_07148_grantee;
BEGIN;
SET ROLE dcl_07148_grantee;
REVOKE SELECT ON TABLE dcl_07148_missing_object FROM dcl_07148_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SET ROLE dcl_07148_grantee;
SELECT count(*) AS privilege_effect_rows FROM dcl_07148_table;
RESET ROLE;
ROLLBACK;
DROP OWNED BY dcl_07148_grantee;
DROP OWNED BY dcl_07148_member;
DROP OWNED BY dcl_07148_grantor;
DROP ROLE IF EXISTS dcl_07148_member;
DROP ROLE IF EXISTS dcl_07148_grantor;
DROP ROLE IF EXISTS dcl_07148_grantee;
DROP TABLE IF EXISTS dcl_07148_table;
