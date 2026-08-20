-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : INSERT privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: INSERT01805
-- source_md: skills/pg-sql-generation/references/statements/dml/table/insert.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/insert.yaml
-- primary_obligation_id: INSERT-EXT|01805|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS insert_01805_tbl, insert_01805_src, insert_01805_ref CASCADE;
RESET ROLE;
DROP OWNED BY insert_01805_actor CASCADE;
DROP ROLE IF EXISTS insert_01805_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE insert_01805_actor LOGIN NOSUPERUSER;
CREATE TABLE insert_01805_tbl (id int PRIMARY KEY, val int);
CREATE TABLE insert_01805_src (val int);
INSERT INTO insert_01805_src VALUES (1);
GRANT SELECT ON insert_01805_tbl TO insert_01805_actor;
SET ROLE insert_01805_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 INSERT。
-- primary-target-begin
INSERT INTO "insert_01805_tbl" (id, val) VALUES (1, (SELECT val FROM insert_01805_src LIMIT 1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'insert_01805_tbl' AND relkind = 'r' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY insert_01805_actor CASCADE;
DROP ROLE IF EXISTS insert_01805_actor;
DROP TABLE IF EXISTS insert_01805_tbl, insert_01805_src, insert_01805_ref CASCADE;
