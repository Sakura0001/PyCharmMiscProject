-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE column privilege on domain_type
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor dcl_statement=revoke
-- factor column_type=domain_type
DROP TABLE IF EXISTS dcl_13721_table;
DROP ROLE IF EXISTS dcl_13721_grantee;
CREATE ROLE dcl_13721_grantee;
CREATE DOMAIN dcl_13721_domain AS text;
CREATE TABLE dcl_13721_table (id integer, payload dcl_13721_domain);
GRANT SELECT (payload) ON TABLE dcl_13721_table TO dcl_13721_grantee;
REVOKE SELECT (payload) ON TABLE dcl_13721_table FROM dcl_13721_grantee;
SELECT has_column_privilege('dcl_13721_grantee', 'dcl_13721_table', 'payload', 'SELECT');
DROP TABLE IF EXISTS dcl_13721_table;
DROP DOMAIN IF EXISTS dcl_13721_domain;
DROP ROLE IF EXISTS dcl_13721_grantee;
DROP TABLE IF EXISTS dcl_13721_table;
