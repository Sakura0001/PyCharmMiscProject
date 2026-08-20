-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COPY target_action=copy_from
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COPY04614
-- source_md: skills/pg-sql-generation/references/statements/utility/data_transfer/copy.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/data_transfer/copy.yaml
-- primary_obligation_id: COPY-EXT|04614|catalog_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS copy_04614_t;
DROP ROLE IF EXISTS copy_04614_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE copy_04614_actor LOGIN NOSUPERUSER;
CREATE TABLE copy_04614_t (copy_04614_c int);
GRANT SELECT, INSERT ON copy_04614_t TO copy_04614_actor;
SET ROLE copy_04614_actor;
-- 3. 执行唯一获得覆盖信用的 COPY。
-- primary-target-begin
COPY copy_04614_t FROM 'copy_04614_src.csv';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS table_present FROM pg_catalog.pg_class WHERE relname = 'copy_04614_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
RESET search_path;
DROP ROLE IF EXISTS copy_04614_actor;
DROP TABLE IF EXISTS copy_04614_t;
