-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on varchar_array
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=varchar_array
DROP TABLE IF EXISTS dcl_13620_table;
DROP ROLE IF EXISTS dcl_13620_grantee;
CREATE ROLE dcl_13620_grantee;
CREATE TABLE dcl_13620_table (id integer, payload varchar[]);
GRANT SELECT (payload) ON TABLE dcl_13620_table TO dcl_13620_grantee;
SELECT has_column_privilege('dcl_13620_grantee', 'dcl_13620_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13620_table;
DROP ROLE IF EXISTS dcl_13620_grantee;
DROP TABLE IF EXISTS dcl_13620_table;
