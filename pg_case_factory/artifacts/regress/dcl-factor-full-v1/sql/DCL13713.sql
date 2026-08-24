-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on tstzrange
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=tstzrange
DROP TABLE IF EXISTS dcl_13713_table;
DROP ROLE IF EXISTS dcl_13713_grantee;
CREATE ROLE dcl_13713_grantee;
CREATE TABLE dcl_13713_table (id integer, payload tstzrange);
GRANT SELECT (payload) ON TABLE dcl_13713_table TO dcl_13713_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13713_table FROM dcl_13713_grantee;
SELECT has_column_privilege('dcl_13713_grantee', 'dcl_13713_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13713_table;
DROP ROLE IF EXISTS dcl_13713_grantee;
DROP TABLE IF EXISTS dcl_13713_table;
