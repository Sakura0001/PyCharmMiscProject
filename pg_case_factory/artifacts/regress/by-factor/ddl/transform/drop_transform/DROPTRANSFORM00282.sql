-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRANSFORM type_name_shape=nonexistent_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRANSFORM00282
-- source_md: skills/pg-sql-generation/references/statements/ddl/transform/drop_transform.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/transform/drop_transform.yaml
-- primary_obligation_id: DROPTRANSFORM-EXT|00282|drop_transform|notice_assertion|cascade_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS droptransform_00282_schema CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA droptransform_00282_schema;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 DROP TRANSFORM。
-- primary-target-begin
DROP TRANSFORM IF EXISTS FOR droptransform_00282_schema.droptransform_00282_notype LANGUAGE plpgsql;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS droptransform_00282_schema CASCADE;
