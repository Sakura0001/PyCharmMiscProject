-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP CAST nonexistent_cast=without_if_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCAST00012
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/drop_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/drop_cast.yaml
-- primary_obligation_id: DCAST-SFV|sfv-4275456df37958aebf282cfc|drop_cast
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (dropcast_00012_sourcetype AS dropcast_00012_targettype);
DROP FUNCTION IF EXISTS dropcast_00012_castfn;
DROP TYPE IF EXISTS dropcast_00012_sourcetype;
DROP TYPE IF EXISTS dropcast_00012_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
CREATE TYPE dropcast_00012_sourcetype AS ENUM ('a', 'b');
CREATE TYPE dropcast_00012_targettype AS ENUM ('a', 'b');
SELECT 1 AS target_cast_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP CAST。
-- primary-target-begin
DROP CAST (dropcast_00012_sourcetype AS dropcast_00012_targettype);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_absent FROM pg_catalog.pg_cast WHERE castsource = 'dropcast_00012_sourcetype'::regtype AND casttarget = 'dropcast_00012_targettype'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (dropcast_00012_sourcetype AS dropcast_00012_targettype);
DROP FUNCTION IF EXISTS dropcast_00012_castfn;
DROP TYPE IF EXISTS dropcast_00012_sourcetype;
DROP TYPE IF EXISTS dropcast_00012_targettype;
