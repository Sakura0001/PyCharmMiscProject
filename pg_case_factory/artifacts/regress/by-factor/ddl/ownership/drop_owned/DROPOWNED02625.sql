-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OWNED dependent_objects=has_dependent_objects_restrict_fails
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOWNED02625
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/drop_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/drop_owned.yaml
-- primary_obligation_id: DROPOWNED-EXT|02625|drop_owned|error_assertion|drop_owned_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropowned_02625_t CASCADE;
DROP VIEW IF EXISTS dropowned_02625_v;
DROP OWNED BY dropowned_02625_actor;
DROP ROLE IF EXISTS dropowned_02625_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE dropowned_02625_actor LOGIN;
CREATE TABLE dropowned_02625_t (c integer);
ALTER TABLE dropowned_02625_t OWNER TO dropowned_02625_actor;
CREATE VIEW dropowned_02625_v AS SELECT * FROM dropowned_02625_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OWNED。
-- primary-target-begin
DROP OWNED BY dropowned_02625_actor;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_oracle;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS dropowned_02625_v;
DROP OWNED BY dropowned_02625_actor;
DROP ROLE IF EXISTS dropowned_02625_actor;
DROP TABLE IF EXISTS dropowned_02625_t CASCADE;
