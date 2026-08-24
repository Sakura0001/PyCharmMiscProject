-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on numeric
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=numeric
DROP TABLE IF EXISTS dcl_13579_table;
DROP ROLE IF EXISTS dcl_13579_grantee;
CREATE ROLE dcl_13579_grantee;
CREATE TABLE dcl_13579_table (id integer, payload numeric);
GRANT SELECT (payload) ON TABLE dcl_13579_table TO dcl_13579_grantee;
SELECT has_column_privilege('dcl_13579_grantee', 'dcl_13579_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13579_table;
DROP ROLE IF EXISTS dcl_13579_grantee;
DROP TABLE IF EXISTS dcl_13579_table;
