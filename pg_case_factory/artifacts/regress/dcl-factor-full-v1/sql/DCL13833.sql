-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_13833_table;
DROP ROLE IF EXISTS dcl_13833_grantee;
DROP ROLE IF EXISTS dcl_13833_grantor;
DROP ROLE IF EXISTS dcl_13833_member;
CREATE ROLE dcl_13833_grantee;
CREATE ROLE dcl_13833_grantor;
CREATE ROLE dcl_13833_member;
CREATE TABLE dcl_13833_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_13833_missing_object TO dcl_13833_grantee;
SET ROLE dcl_13833_grantee;
REVOKE SELECT ON TABLE dcl_13833_missing_object FROM dcl_13833_grantee RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_13833_table;
DROP OWNED BY dcl_13833_grantee;
DROP OWNED BY dcl_13833_member;
DROP OWNED BY dcl_13833_grantor;
DROP ROLE IF EXISTS dcl_13833_member;
DROP ROLE IF EXISTS dcl_13833_grantor;
DROP ROLE IF EXISTS dcl_13833_grantee;
DROP TABLE IF EXISTS dcl_13833_table;
