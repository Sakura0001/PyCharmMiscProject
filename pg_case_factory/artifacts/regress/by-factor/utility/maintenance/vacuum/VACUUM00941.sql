-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : VACUUM target_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: VACUUM00941
-- source_md: skills/pg-sql-generation/references/statements/utility/maintenance/vacuum.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/maintenance/vacuum.yaml
-- primary_obligation_id: VACUUM-EXT|00941|effect_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS vacuum_00941_t CASCADE;
DROP VIEW IF EXISTS vacuum_00941_v CASCADE;
DROP SCHEMA IF EXISTS vacuum_00941_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA vacuum_00941_sch;
CREATE TABLE vacuum_00941_t (id integer);
CREATE VIEW vacuum_00941_v AS SELECT id FROM vacuum_00941_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 VACUUM。
-- primary-target-begin
VACUUM FULL vacuum_00941_v;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) AS vacuum_stat_rows FROM pg_catalog.pg_class c WHERE c.relname = 'vacuum_00941_t' AND c.relpages >= 0 ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS vacuum_00941_v CASCADE;
DROP SCHEMA IF EXISTS vacuum_00941_sch CASCADE;
ROLLBACK;
DROP TABLE IF EXISTS vacuum_00941_t CASCADE;
