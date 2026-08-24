-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on time_with_time_zone
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=time_with_time_zone
DROP TABLE IF EXISTS dcl_13594_table;
DROP ROLE IF EXISTS dcl_13594_grantee;
CREATE ROLE dcl_13594_grantee;
CREATE TABLE dcl_13594_table (id integer, payload time with time zone);
GRANT SELECT (payload) ON TABLE dcl_13594_table TO dcl_13594_grantee;
SELECT has_column_privilege('dcl_13594_grantee', 'dcl_13594_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13594_table;
DROP ROLE IF EXISTS dcl_13594_grantee;
DROP TABLE IF EXISTS dcl_13594_table;
