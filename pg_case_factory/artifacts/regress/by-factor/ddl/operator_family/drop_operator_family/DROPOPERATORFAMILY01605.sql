-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR FAMILY contained_opclass_state=has_contained_opclass
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATORFAMILY01605
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/drop_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/drop_operator_family.yaml
-- primary_obligation_id: DROPOPERATORFAMILY-EXT|01605|drop_operator_family|error_assertion|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropoperatorfamily_01605_t CASCADE;
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01605_opf USING btree CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地操作符族和因子专用夹具。
SELECT 1 AS target_operator_family_intentionally_absent;
CREATE OPERATOR CLASS dropoperatorfamily_01605_opc FOR integer USING btree FAMILY dropoperatorfamily_01605_opf AS STORAGE integer;
CREATE TABLE dropoperatorfamily_01605_t (c integer);
CREATE INDEX dropoperatorfamily_01605_idx ON dropoperatorfamily_01605_t USING btree (c dropoperatorfamily_01605_opc);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR FAMILY。
-- primary-target-begin
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01605_opf USING btree;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS family_absent FROM pg_catalog.pg_opfamily WHERE opfname = 'dropoperatorfamily_01605_opf' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01605_opf USING btree CASCADE;
DROP TABLE IF EXISTS dropoperatorfamily_01605_t CASCADE;
