-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on enum_type
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=enum_type
DROP TABLE IF EXISTS dcl_13682_table;
DROP ROLE IF EXISTS dcl_13682_grantee;
CREATE ROLE dcl_13682_grantee;
CREATE TYPE dcl_13682_enum AS ENUM ('alpha', 'beta');
CREATE TABLE dcl_13682_table (id integer, payload dcl_13682_enum);
GRANT SELECT (payload) ON TABLE dcl_13682_table TO dcl_13682_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13682_table FROM dcl_13682_grantee;
SELECT has_column_privilege('dcl_13682_grantee', 'dcl_13682_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13682_table;
DROP TYPE IF EXISTS dcl_13682_enum;
DROP ROLE IF EXISTS dcl_13682_grantee;
DROP TABLE IF EXISTS dcl_13682_table;
