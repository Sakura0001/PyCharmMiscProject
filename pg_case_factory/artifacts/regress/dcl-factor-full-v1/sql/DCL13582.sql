-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on double_precision
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=double_precision
DROP TABLE IF EXISTS dcl_13582_table;
DROP ROLE IF EXISTS dcl_13582_grantee;
CREATE ROLE dcl_13582_grantee;
CREATE TABLE dcl_13582_table (id integer, payload double precision);
GRANT SELECT (payload) ON TABLE dcl_13582_table TO dcl_13582_grantee;
SELECT has_column_privilege('dcl_13582_grantee', 'dcl_13582_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13582_table;
DROP ROLE IF EXISTS dcl_13582_grantee;
DROP TABLE IF EXISTS dcl_13582_table;
