-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP OPERATOR CLASS target_object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPOPERATORCLASS00883
-- source_md: skills/pg-sql-generation/references/statements/ddl/operator_class/drop_operator_class.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/operator_class/drop_operator_class.yaml
-- primary_obligation_id: DROPOPERATORCLASS-EXT|00883|drop_operator_class|effect_query|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS dropoperatorclass_00883_opclass USING btree CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地运算符类和因子专用夹具。
CREATE OPERATOR CLASS dropoperatorclass_00883_opclass FOR TYPE int USING btree AS (OPERATOR 1 <);
-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR CLASS。
-- primary-target-begin
DROP OPERATOR CLASS dropoperatorclass_00883_opclass USING btree RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS opclass_absent FROM pg_catalog.pg_opclass WHERE opcname = 'dropoperatorclass_00883_opclass' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OPERATOR CLASS IF EXISTS dropoperatorclass_00883_opclass USING btree CASCADE;
