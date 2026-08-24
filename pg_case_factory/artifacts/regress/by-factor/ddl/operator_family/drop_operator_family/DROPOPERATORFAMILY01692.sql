-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR FAMILY dependency_state=has_dependents
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATORFAMILY01692
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/drop_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/drop_operator_family.yaml
-- primary_obligation_id: DROPOPERATORFAMILY-EXT|01692|drop_operator_family|effect_query|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropoperatorfamily_01692_t CASCADE;
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01692_opf USING btree CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地操作符族和因子专用夹具。
CREATE OPERATOR FAMILY dropoperatorfamily_01692_opf USING btree;
CREATE OPERATOR CLASS dropoperatorfamily_01692_opc FOR integer USING btree FAMILY dropoperatorfamily_01692_opf AS STORAGE integer;
CREATE TABLE dropoperatorfamily_01692_t (c integer);
CREATE INDEX dropoperatorfamily_01692_idx ON dropoperatorfamily_01692_t USING btree (c dropoperatorfamily_01692_opc);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR FAMILY。
-- primary-target-begin
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01692_opf USING btree;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS family_present FROM pg_catalog.pg_opfamily WHERE opfname = 'dropoperatorfamily_01692_opf' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_01692_opf USING btree CASCADE;
DROP TABLE IF EXISTS dropoperatorfamily_01692_t CASCADE;
