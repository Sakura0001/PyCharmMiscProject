-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on bit_varying
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=bit_varying
DROP TABLE IF EXISTS dcl_13610_table;
DROP ROLE IF EXISTS dcl_13610_grantee;
CREATE ROLE dcl_13610_grantee;
CREATE TABLE dcl_13610_table (id integer, payload bit varying);
GRANT SELECT (payload) ON TABLE dcl_13610_table TO dcl_13610_grantee;
SELECT has_column_privilege('dcl_13610_grantee', 'dcl_13610_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13610_table;
DROP ROLE IF EXISTS dcl_13610_grantee;
DROP TABLE IF EXISTS dcl_13610_table;
