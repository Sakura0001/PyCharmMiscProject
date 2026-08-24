-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on tsmultirange
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=tsmultirange
DROP TABLE IF EXISTS dcl_13633_table;
DROP ROLE IF EXISTS dcl_13633_grantee;
CREATE ROLE dcl_13633_grantee;
CREATE TABLE dcl_13633_table (id integer, payload tsmultirange);
GRANT SELECT (payload) ON TABLE dcl_13633_table TO dcl_13633_grantee;
SELECT has_column_privilege('dcl_13633_grantee', 'dcl_13633_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13633_table;
DROP ROLE IF EXISTS dcl_13633_grantee;
DROP TABLE IF EXISTS dcl_13633_table;
