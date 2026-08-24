-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on time_with_time_zone
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=time_with_time_zone
DROP TABLE IF EXISTS dcl_13679_table;
DROP ROLE IF EXISTS dcl_13679_grantee;
CREATE ROLE dcl_13679_grantee;
CREATE TABLE dcl_13679_table (id integer, payload time with time zone);
GRANT SELECT (payload) ON TABLE dcl_13679_table TO dcl_13679_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13679_table FROM dcl_13679_grantee;
SELECT has_column_privilege('dcl_13679_grantee', 'dcl_13679_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13679_table;
DROP ROLE IF EXISTS dcl_13679_grantee;
DROP TABLE IF EXISTS dcl_13679_table;
