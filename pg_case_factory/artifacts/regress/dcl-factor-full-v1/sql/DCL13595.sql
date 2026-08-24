-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on interval
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=interval
DROP TABLE IF EXISTS dcl_13595_table;
DROP ROLE IF EXISTS dcl_13595_grantee;
CREATE ROLE dcl_13595_grantee;
CREATE TABLE dcl_13595_table (id integer, payload interval);
GRANT SELECT (payload) ON TABLE dcl_13595_table TO dcl_13595_grantee;
SELECT has_column_privilege('dcl_13595_grantee', 'dcl_13595_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13595_table;
DROP ROLE IF EXISTS dcl_13595_grantee;
DROP TABLE IF EXISTS dcl_13595_table;
