-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR CLASS expected_status=failure
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATORCLASS00015
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/drop_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/drop_operator_class.yaml
-- primary_obligation_id: DROPOPERATORCLASS-SFV|sfv-0ce4b96889a7b276ab6d7ef9|drop_operator_class
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS dropoperatorclass_00015_opclass USING btree CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地运算符类和因子专用夹具。
SELECT 1 AS target_operator_class_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR CLASS。
-- primary-target-begin
DROP OPERATOR CLASS dropoperatorclass_00015_opclass USING btree;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opclass_absent FROM pg_catalog.pg_opclass WHERE opcname = 'dropoperatorclass_00015_opclass' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS dropoperatorclass_00015_opclass USING btree CASCADE;
