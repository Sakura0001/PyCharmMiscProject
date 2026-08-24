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
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07273_table;
DROP ROLE IF EXISTS "dcl_07273_Grantee";
DROP ROLE IF EXISTS dcl_07273_grantor;
DROP ROLE IF EXISTS dcl_07273_member;
CREATE ROLE "dcl_07273_Grantee";
CREATE ROLE dcl_07273_grantor;
CREATE ROLE dcl_07273_member;
CREATE TABLE dcl_07273_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07273_table TO PUBLIC;
GRANT SELECT (payload) ON TABLE dcl_07273_table TO dcl_07273_grantor WITH GRANT OPTION;
SET ROLE dcl_07273_grantor;
REVOKE SELECT (payload) ON TABLE dcl_07273_table FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07273_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_07273_Grantee";
DROP OWNED BY dcl_07273_member;
DROP OWNED BY dcl_07273_grantor;
DROP ROLE IF EXISTS dcl_07273_member;
DROP ROLE IF EXISTS dcl_07273_grantor;
DROP ROLE IF EXISTS "dcl_07273_Grantee";
DROP TABLE IF EXISTS dcl_07273_table;
