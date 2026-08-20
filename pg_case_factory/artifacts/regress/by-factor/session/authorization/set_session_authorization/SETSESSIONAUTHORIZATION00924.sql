-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET SESSION AUTHORIZATION target_action=set_session_authorization
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SETSESSIONAUTHORIZATION00924
-- source_md: skills/pg-sql-generation/references/statements/session/authorization/set_session_authorization.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/authorization/set_session_authorization.yaml
-- primary_obligation_id: SETSESSIONAUTHORIZATION-EXT|00924|catalog_query|rollback|name_payload
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
SET SESSION AUTHORIZATION DEFAULT;
DROP ROLE IF EXISTS setsessionauthorization_00924_witness;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE setsessionauthorization_00924_witness LOGIN;
GRANT setsessionauthorization_00924_witness TO CURRENT_USER;
-- 3. 执行唯一获得覆盖信心的 SET SESSION AUTHORIZATION。
-- primary-target-begin
SET SESSION AUTHORIZATION setsessionauthorization_00924_witness;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS role_observed FROM pg_catalog.pg_roles WHERE rolname = 'setsessionauthorization_00924_witness' ORDER BY count(*);
-- 5. 清理全部本编号对象。
SET SESSION AUTHORIZATION DEFAULT;
DROP ROLE IF EXISTS setsessionauthorization_00924_witness;
