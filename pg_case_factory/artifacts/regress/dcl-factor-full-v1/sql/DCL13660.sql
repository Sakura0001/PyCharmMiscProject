-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on bigint
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=bigint
DROP TABLE IF EXISTS dcl_13660_table;
DROP ROLE IF EXISTS dcl_13660_grantee;
CREATE ROLE dcl_13660_grantee;
CREATE TABLE dcl_13660_table (id integer, payload bigint);
GRANT SELECT (payload) ON TABLE dcl_13660_table TO dcl_13660_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13660_table FROM dcl_13660_grantee;
SELECT has_column_privilege('dcl_13660_grantee', 'dcl_13660_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13660_table;
DROP ROLE IF EXISTS dcl_13660_grantee;
DROP TABLE IF EXISTS dcl_13660_table;
