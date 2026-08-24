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
DROP TABLE IF EXISTS dcl_00007_table;
DROP ROLE IF EXISTS "dcl_00007_Grantee";
DROP ROLE IF EXISTS dcl_00007_grantor;
DROP ROLE IF EXISTS dcl_00007_member;
CREATE ROLE "dcl_00007_Grantee";
CREATE ROLE dcl_00007_grantor;
CREATE ROLE dcl_00007_member;
CREATE TABLE dcl_00007_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_00007_table TO dcl_00007_grantor WITH GRANT OPTION;
SET ROLE dcl_00007_grantor;
GRANT SELECT ON TABLE dcl_00007_table TO PUBLIC;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00007_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_00007_Grantee";
DROP OWNED BY dcl_00007_member;
DROP OWNED BY dcl_00007_grantor;
DROP ROLE IF EXISTS dcl_00007_member;
DROP ROLE IF EXISTS dcl_00007_grantor;
DROP ROLE IF EXISTS "dcl_00007_Grantee";
DROP TABLE IF EXISTS dcl_00007_table;
