-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR FAMILY privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATORFAMILY00836
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_family/drop_operator_family.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_family/drop_operator_family.yaml
-- primary_obligation_id: DROPOPERATORFAMILY-EXT|00836|drop_operator_family|error_assertion|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropoperatorfamily_00836_t CASCADE;
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_00836_opf USING btree CASCADE;
DROP OWNED BY dropoperatorfamily_00836_actor;
DROP ROLE IF EXISTS dropoperatorfamily_00836_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地操作符族和因子专用夹具。
CREATE ROLE dropoperatorfamily_00836_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_operator_family_intentionally_absent;
CREATE OPERATOR CLASS dropoperatorfamily_00836_opc FOR integer USING btree FAMILY dropoperatorfamily_00836_opf AS STORAGE integer;
CREATE TABLE dropoperatorfamily_00836_t (c integer);
CREATE INDEX dropoperatorfamily_00836_idx ON dropoperatorfamily_00836_t USING btree (c dropoperatorfamily_00836_opc);
SET ROLE dropoperatorfamily_00836_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR FAMILY。
-- primary-target-begin
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_00836_opf USING btree CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS family_absent FROM pg_catalog.pg_opfamily WHERE opfname = 'dropoperatorfamily_00836_opf' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OPERATOR FAMILY IF EXISTS dropoperatorfamily_00836_opf USING btree CASCADE;
DROP OWNED BY dropoperatorfamily_00836_actor;
DROP ROLE IF EXISTS dropoperatorfamily_00836_actor;
DROP TABLE IF EXISTS dropoperatorfamily_00836_t CASCADE;
