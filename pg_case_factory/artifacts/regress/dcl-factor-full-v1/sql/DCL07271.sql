-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
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
DROP TABLE IF EXISTS dcl_07271_table;
DROP ROLE IF EXISTS "dcl_07271_Grantee";
DROP ROLE IF EXISTS dcl_07271_grantor;
DROP ROLE IF EXISTS dcl_07271_member;
CREATE ROLE "dcl_07271_Grantee";
CREATE ROLE dcl_07271_grantor;
CREATE ROLE dcl_07271_member;
CREATE TABLE dcl_07271_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07271_table TO "dcl_07271_Grantee";
GRANT SELECT (payload) ON TABLE dcl_07271_table TO dcl_07271_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_07271_grantor;
REVOKE GRANT OPTION FOR SELECT (payload) ON TABLE dcl_07271_table FROM "dcl_07271_Grantee" GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SET ROLE "dcl_07271_Grantee";
SELECT count(*) AS privilege_effect_rows FROM dcl_07271_table;
RESET ROLE;
ROLLBACK;
DROP OWNED BY "dcl_07271_Grantee";
DROP OWNED BY dcl_07271_member;
DROP OWNED BY dcl_07271_grantor;
DROP ROLE IF EXISTS dcl_07271_member;
DROP ROLE IF EXISTS dcl_07271_grantor;
DROP ROLE IF EXISTS "dcl_07271_Grantee";
DROP TABLE IF EXISTS dcl_07271_table;
