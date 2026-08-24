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
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_13762_table;
DROP ROLE IF EXISTS dcl_13762_grantee;
DROP ROLE IF EXISTS dcl_13762_grantor;
DROP ROLE IF EXISTS dcl_13762_member;
CREATE ROLE dcl_13762_grantee;
CREATE ROLE dcl_13762_grantor;
CREATE ROLE dcl_13762_member;
CREATE TABLE dcl_13762_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_13762_table TO dcl_13762_grantee GRANTED BY CURRENT_USER;
SELECT count(*) AS table_count FROM dcl_13762_table;
DROP OWNED BY dcl_13762_grantee;
DROP OWNED BY dcl_13762_member;
DROP OWNED BY dcl_13762_grantor;
DROP ROLE IF EXISTS dcl_13762_member;
DROP ROLE IF EXISTS dcl_13762_grantor;
DROP ROLE IF EXISTS dcl_13762_grantee;
DROP TABLE IF EXISTS dcl_13762_table;
