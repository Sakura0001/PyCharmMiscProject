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
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_07285_table;
DROP ROLE IF EXISTS "dcl_07285_Grantee";
DROP ROLE IF EXISTS dcl_07285_grantor;
DROP ROLE IF EXISTS dcl_07285_member;
CREATE ROLE "dcl_07285_Grantee";
CREATE ROLE dcl_07285_grantor;
CREATE ROLE dcl_07285_member;
CREATE TABLE dcl_07285_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07285_table TO CURRENT_USER;
GRANT SELECT (payload) ON TABLE dcl_07285_table TO dcl_07285_grantor WITH GRANT OPTION;
SET ROLE dcl_07285_grantor;
REVOKE SELECT (payload) ON TABLE dcl_07285_table FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07285_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_07285_Grantee";
DROP OWNED BY dcl_07285_member;
DROP OWNED BY dcl_07285_grantor;
DROP ROLE IF EXISTS dcl_07285_member;
DROP ROLE IF EXISTS dcl_07285_grantor;
DROP ROLE IF EXISTS "dcl_07285_Grantee";
DROP TABLE IF EXISTS dcl_07285_table;
