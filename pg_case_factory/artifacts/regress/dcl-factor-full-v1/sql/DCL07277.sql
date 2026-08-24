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
-- factor grantee_shape=public
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
DROP TABLE IF EXISTS dcl_07277_table;
DROP ROLE IF EXISTS "dcl_07277_Grantee";
DROP ROLE IF EXISTS dcl_07277_grantor;
DROP ROLE IF EXISTS dcl_07277_member;
CREATE ROLE "dcl_07277_Grantee";
CREATE ROLE dcl_07277_grantor;
CREATE ROLE dcl_07277_member;
CREATE TABLE dcl_07277_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07277_table TO PUBLIC;
GRANT SELECT (payload) ON TABLE dcl_07277_table TO dcl_07277_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_07277_grantor;
REVOKE GRANT OPTION FOR SELECT (payload) ON TABLE dcl_07277_table FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_07277_table;
ROLLBACK;
DROP OWNED BY "dcl_07277_Grantee";
DROP OWNED BY dcl_07277_member;
DROP OWNED BY dcl_07277_grantor;
DROP ROLE IF EXISTS dcl_07277_member;
DROP ROLE IF EXISTS dcl_07277_grantor;
DROP ROLE IF EXISTS "dcl_07277_Grantee";
DROP TABLE IF EXISTS dcl_07277_table;
