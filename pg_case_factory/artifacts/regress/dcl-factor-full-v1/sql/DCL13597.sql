-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on enum_type
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=enum_type
DROP TABLE IF EXISTS dcl_13597_table;
DROP ROLE IF EXISTS dcl_13597_grantee;
CREATE ROLE dcl_13597_grantee;
CREATE TYPE dcl_13597_enum AS ENUM ('alpha', 'beta');
CREATE TABLE dcl_13597_table (id integer, payload dcl_13597_enum);
GRANT SELECT (payload) ON TABLE dcl_13597_table TO dcl_13597_grantee;
SELECT has_column_privilege('dcl_13597_grantee', 'dcl_13597_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13597_table;
DROP TYPE IF EXISTS dcl_13597_enum;
DROP ROLE IF EXISTS dcl_13597_grantee;
DROP TABLE IF EXISTS dcl_13597_table;
