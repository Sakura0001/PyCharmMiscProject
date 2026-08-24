-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_privilege
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
DROP TABLE IF EXISTS dcl_00029_table;
DROP ROLE IF EXISTS "dcl_00029_Grantee";
DROP ROLE IF EXISTS dcl_00029_grantor;
DROP ROLE IF EXISTS dcl_00029_member;
CREATE ROLE "dcl_00029_Grantee";
CREATE ROLE dcl_00029_grantor;
CREATE ROLE dcl_00029_member;
CREATE TABLE dcl_00029_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_00029_table TO dcl_00029_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_00029_grantor;
GRANT SELECT ON TABLE dcl_00029_table TO SESSION_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_00029_table;
ROLLBACK;
DROP OWNED BY "dcl_00029_Grantee";
DROP OWNED BY dcl_00029_member;
DROP OWNED BY dcl_00029_grantor;
DROP ROLE IF EXISTS dcl_00029_member;
DROP ROLE IF EXISTS dcl_00029_grantor;
DROP ROLE IF EXISTS "dcl_00029_Grantee";
DROP TABLE IF EXISTS dcl_00029_table;
