-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE COLLATION target_form=define_with_params
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATECOLLATION00905
-- source_md: skills/pg-sql-generation/references/statements/ddl/collation/create_collation.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/collation/create_collation.yaml
-- primary_obligation_id: CCOL-EXT|00905|actual_collation_usage|DROP_COLLATION
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP COLLATION IF EXISTS public.createcollation_00905_col CASCADE;
DROP COLLATION IF EXISTS createcollation_00905_src CASCADE;
DROP COLLATION IF EXISTS createcollation_00905_nosuch CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE COLLATION。
-- primary-target-begin
CREATE COLLATION IF NOT EXISTS public.createcollation_00905_col (LOCALE = 'C', PROVIDER = icu);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 'a' COLLATE public.createcollation_00905_col AS usage_check;
-- 5. 清理全部本编号对象。
DROP COLLATION public.createcollation_00905_col;
