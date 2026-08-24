-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on int4range
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=int4range
DROP TABLE IF EXISTS dcl_13709_table;
DROP ROLE IF EXISTS dcl_13709_grantee;
CREATE ROLE dcl_13709_grantee;
CREATE TABLE dcl_13709_table (id integer, payload int4range);
GRANT SELECT (payload) ON TABLE dcl_13709_table TO dcl_13709_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13709_table FROM dcl_13709_grantee;
SELECT has_column_privilege('dcl_13709_grantee', 'dcl_13709_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13709_table;
DROP ROLE IF EXISTS dcl_13709_grantee;
DROP TABLE IF EXISTS dcl_13709_table;
