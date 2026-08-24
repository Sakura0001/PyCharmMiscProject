-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_maintain
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_00055_table;
DROP ROLE IF EXISTS "dcl_00055_Grantee";
DROP ROLE IF EXISTS dcl_00055_grantor;
DROP ROLE IF EXISTS dcl_00055_member;
CREATE ROLE "dcl_00055_Grantee";
CREATE ROLE dcl_00055_grantor;
CREATE ROLE dcl_00055_member;
CREATE TABLE dcl_00055_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_00055_table TO dcl_00055_grantor WITH GRANT OPTION;
SET ROLE dcl_00055_grantor;
GRANT MAINTAIN ON TABLE dcl_00055_table TO SESSION_USER;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00055_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_00055_Grantee";
DROP OWNED BY dcl_00055_member;
DROP OWNED BY dcl_00055_grantor;
DROP ROLE IF EXISTS dcl_00055_member;
DROP ROLE IF EXISTS dcl_00055_grantor;
DROP ROLE IF EXISTS "dcl_00055_Grantee";
DROP TABLE IF EXISTS dcl_00055_table;
