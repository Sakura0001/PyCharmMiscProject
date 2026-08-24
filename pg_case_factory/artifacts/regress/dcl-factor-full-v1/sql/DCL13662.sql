-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on serial
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=serial
DROP TABLE IF EXISTS dcl_13662_table;
DROP ROLE IF EXISTS dcl_13662_grantee;
CREATE ROLE dcl_13662_grantee;
CREATE TABLE dcl_13662_table (id integer, payload serial);
GRANT SELECT (payload) ON TABLE dcl_13662_table TO dcl_13662_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13662_table FROM dcl_13662_grantee;
SELECT has_column_privilege('dcl_13662_grantee', 'dcl_13662_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13662_table;
DROP ROLE IF EXISTS dcl_13662_grantee;
DROP TABLE IF EXISTS dcl_13662_table;
