-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_maintain
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
DROP TABLE IF EXISTS dcl_06827_table;
DROP ROLE IF EXISTS "dcl_06827_Grantee";
DROP ROLE IF EXISTS dcl_06827_grantor;
DROP ROLE IF EXISTS dcl_06827_member;
CREATE ROLE "dcl_06827_Grantee";
CREATE ROLE dcl_06827_grantor;
CREATE ROLE dcl_06827_member;
CREATE TABLE dcl_06827_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_06827_table TO PUBLIC;
GRANT MAINTAIN ON TABLE dcl_06827_table TO dcl_06827_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_06827_grantor;
REVOKE GRANT OPTION FOR MAINTAIN ON TABLE dcl_06827_table FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_06827_table;
ROLLBACK;
DROP OWNED BY "dcl_06827_Grantee";
DROP OWNED BY dcl_06827_member;
DROP OWNED BY dcl_06827_grantor;
DROP ROLE IF EXISTS dcl_06827_member;
DROP ROLE IF EXISTS dcl_06827_grantor;
DROP ROLE IF EXISTS "dcl_06827_Grantee";
DROP TABLE IF EXISTS dcl_06827_table;
