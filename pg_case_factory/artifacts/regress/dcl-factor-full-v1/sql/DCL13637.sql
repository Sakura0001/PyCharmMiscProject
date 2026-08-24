-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT column privilege on composite_type
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=grant
-- factor column_type=composite_type
DROP TABLE IF EXISTS dcl_13637_table;
DROP ROLE IF EXISTS dcl_13637_grantee;
CREATE ROLE dcl_13637_grantee;
CREATE TYPE dcl_13637_composite AS (value integer);
CREATE TABLE dcl_13637_table (id integer, payload dcl_13637_composite);
GRANT SELECT (payload) ON TABLE dcl_13637_table TO dcl_13637_grantee;
SELECT has_column_privilege('dcl_13637_grantee', 'dcl_13637_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13637_table;
DROP TYPE IF EXISTS dcl_13637_composite;
DROP ROLE IF EXISTS dcl_13637_grantee;
DROP TABLE IF EXISTS dcl_13637_table;
