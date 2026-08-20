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
-- case_id: DROPOPERATORFAMILY02147
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/drop_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/drop_operator_family.yaml
-- primary_obligation_id: DROPOPERATORFAMILY-EXT|02147|drop_operator_family|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropoperatorfamily_02147_t CASCADE;
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_02147_opf USING btree CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地操作符族和因子专用夹具。
CREATE OPERATOR FAMILY dropoperatorfamily_02147_opf USING btree;
CREATE OPERATOR CLASS dropoperatorfamily_02147_opc FOR integer USING btree FAMILY dropoperatorfamily_02147_opf AS STORAGE integer;
CREATE TABLE dropoperatorfamily_02147_t (c integer);
CREATE INDEX dropoperatorfamily_02147_idx ON dropoperatorfamily_02147_t USING btree (c dropoperatorfamily_02147_opc);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR FAMILY。
-- primary-target-begin
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_02147_opf USING btree RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS family_present FROM pg_catalog.pg_opfamily WHERE opfname = 'dropoperatorfamily_02147_opf' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_02147_opf USING btree CASCADE;
DROP TABLE IF EXISTS dropoperatorfamily_02147_t CASCADE;
