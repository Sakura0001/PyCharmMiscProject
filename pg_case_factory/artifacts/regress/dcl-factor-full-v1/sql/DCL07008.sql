-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07008_table;
DROP ROLE IF EXISTS "dcl_07008_Grantee";
DROP ROLE IF EXISTS dcl_07008_grantor;
DROP ROLE IF EXISTS dcl_07008_member;
CREATE ROLE "dcl_07008_Grantee";
CREATE ROLE dcl_07008_grantor;
CREATE ROLE dcl_07008_member;
CREATE TABLE dcl_07008_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_07008_missing_object TO CURRENT_USER;
SET ROLE "dcl_07008_Grantee";
REVOKE GRANT OPTION FOR SELECT ON TABLE dcl_07008_missing_object FROM CURRENT_USER GRANTED BY dcl_07008_grantor RESTRICT;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_07008_table;
DROP OWNED BY "dcl_07008_Grantee";
DROP OWNED BY dcl_07008_member;
DROP OWNED BY dcl_07008_grantor;
DROP ROLE IF EXISTS dcl_07008_member;
DROP ROLE IF EXISTS dcl_07008_grantor;
DROP ROLE IF EXISTS "dcl_07008_Grantee";
DROP TABLE IF EXISTS dcl_07008_table;
