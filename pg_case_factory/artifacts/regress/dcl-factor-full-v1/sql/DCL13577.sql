-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on serial
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=serial
DROP TABLE IF EXISTS dcl_13577_table;
DROP ROLE IF EXISTS dcl_13577_grantee;
CREATE ROLE dcl_13577_grantee;
CREATE TABLE dcl_13577_table (id integer, payload serial);
GRANT SELECT (payload) ON TABLE dcl_13577_table TO dcl_13577_grantee;
SELECT has_column_privilege('dcl_13577_grantee', 'dcl_13577_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13577_table;
DROP ROLE IF EXISTS dcl_13577_grantee;
DROP TABLE IF EXISTS dcl_13577_table;
