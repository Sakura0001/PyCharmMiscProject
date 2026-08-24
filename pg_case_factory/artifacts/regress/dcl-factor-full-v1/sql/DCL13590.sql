-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on timestamp
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=timestamp
DROP TABLE IF EXISTS dcl_13590_table;
DROP ROLE IF EXISTS dcl_13590_grantee;
CREATE ROLE dcl_13590_grantee;
CREATE TABLE dcl_13590_table (id integer, payload timestamp);
GRANT SELECT (payload) ON TABLE dcl_13590_table TO dcl_13590_grantee;
SELECT has_column_privilege('dcl_13590_grantee', 'dcl_13590_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13590_table;
DROP ROLE IF EXISTS dcl_13590_grantee;
DROP TABLE IF EXISTS dcl_13590_table;
