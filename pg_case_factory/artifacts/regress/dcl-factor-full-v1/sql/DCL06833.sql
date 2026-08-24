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
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_06833_table;
DROP ROLE IF EXISTS "dcl_06833_Grantee";
DROP ROLE IF EXISTS dcl_06833_grantor;
DROP ROLE IF EXISTS dcl_06833_member;
CREATE ROLE "dcl_06833_Grantee";
CREATE ROLE dcl_06833_grantor;
CREATE ROLE dcl_06833_member;
CREATE TABLE dcl_06833_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_06833_table TO CURRENT_ROLE;
GRANT MAINTAIN ON TABLE dcl_06833_table TO dcl_06833_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_06833_grantor;
REVOKE GRANT OPTION FOR MAINTAIN ON TABLE dcl_06833_table FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_06833_table;
ROLLBACK;
DROP OWNED BY "dcl_06833_Grantee";
DROP OWNED BY dcl_06833_member;
DROP OWNED BY dcl_06833_grantor;
DROP ROLE IF EXISTS dcl_06833_member;
DROP ROLE IF EXISTS dcl_06833_grantor;
DROP ROLE IF EXISTS "dcl_06833_Grantee";
DROP TABLE IF EXISTS dcl_06833_table;
