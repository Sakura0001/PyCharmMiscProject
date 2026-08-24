-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on int4range
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=int4range
DROP TABLE IF EXISTS dcl_13624_table;
DROP ROLE IF EXISTS dcl_13624_grantee;
CREATE ROLE dcl_13624_grantee;
CREATE TABLE dcl_13624_table (id integer, payload int4range);
GRANT SELECT (payload) ON TABLE dcl_13624_table TO dcl_13624_grantee;
SELECT has_column_privilege('dcl_13624_grantee', 'dcl_13624_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13624_table;
DROP ROLE IF EXISTS dcl_13624_grantee;
DROP TABLE IF EXISTS dcl_13624_table;
