-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP VIEW object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPVIEW02925
-- source_md: skills/pg-sql-generation/references/statements/ddl/view/drop_view.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/view/drop_view.yaml
-- primary_obligation_id: DROPVIEW-EXT|02925|drop_view|effect_query|cascade_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropview_02925_vbt CASCADE;
DROP VIEW IF EXISTS public.dropview_02925_v CASCADE;
DROP POLICY IF EXISTS dropview_02925_pol ON public.dropview_02925_v;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE dropview_02925_vbt (c integer);
CREATE VIEW public.dropview_02925_v AS SELECT * FROM dropview_02925_vbt;
ALTER TABLE public.dropview_02925_v ENABLE ROW LEVEL SECURITY;
CREATE POLICY dropview_02925_pol ON public.dropview_02925_v USING (true);
-- 3. 执行唯一获得覆盖信用的 DROP VIEW。
-- primary-target-begin
DROP VIEW public.dropview_02925_v RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS view_absent FROM pg_catalog.pg_class WHERE relname = 'dropview_02925_v' AND relkind = 'v' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS public.dropview_02925_v CASCADE;
DROP POLICY IF EXISTS dropview_02925_pol ON public.dropview_02925_v;
DROP TABLE IF EXISTS dropview_02925_vbt CASCADE;
