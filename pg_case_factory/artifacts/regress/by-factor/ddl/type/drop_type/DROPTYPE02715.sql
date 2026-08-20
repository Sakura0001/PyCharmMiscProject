-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TYPE dependency_state=used_in_table_columns
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTYPE02715
-- source_md: skills/pg-sql-generation/references/statements/ddl/type/drop_type.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/type/drop_type.yaml
-- primary_obligation_id: DROPTYPE-EXT|02715|drop_type|information_schema_user_defined_types|manual_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptype_02715_deptbl CASCADE;
DROP TYPE IF EXISTS droptype_02715_type CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TYPE droptype_02715_type AS ENUM ('a', 'b');
CREATE TABLE droptype_02715_deptbl (c droptype_02715_type);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TYPE。
-- primary-target-begin
DROP TYPE droptype_02715_type;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS type_present FROM pg_catalog.pg_type WHERE typname = 'droptype_02715_type' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TYPE IF EXISTS droptype_02715_type CASCADE;
DROP TABLE IF EXISTS droptype_02715_deptbl CASCADE;
