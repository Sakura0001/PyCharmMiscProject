-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on varchar_array
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=varchar_array
DROP TABLE IF EXISTS dcl_13705_table;
DROP ROLE IF EXISTS dcl_13705_grantee;
CREATE ROLE dcl_13705_grantee;
CREATE TABLE dcl_13705_table (id integer, payload varchar[]);
GRANT SELECT (payload) ON TABLE dcl_13705_table TO dcl_13705_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13705_table FROM dcl_13705_grantee;
SELECT has_column_privilege('dcl_13705_grantee', 'dcl_13705_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13705_table;
DROP ROLE IF EXISTS dcl_13705_grantee;
DROP TABLE IF EXISTS dcl_13705_table;
