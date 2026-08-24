-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on uuid
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=uuid
DROP TABLE IF EXISTS dcl_13698_table;
DROP ROLE IF EXISTS dcl_13698_grantee;
CREATE ROLE dcl_13698_grantee;
CREATE TABLE dcl_13698_table (id integer, payload uuid);
GRANT SELECT (payload) ON TABLE dcl_13698_table TO dcl_13698_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13698_table FROM dcl_13698_grantee;
SELECT has_column_privilege('dcl_13698_grantee', 'dcl_13698_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13698_table;
DROP ROLE IF EXISTS dcl_13698_grantee;
DROP TABLE IF EXISTS dcl_13698_table;
