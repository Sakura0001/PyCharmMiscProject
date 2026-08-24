-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP CAST source_type=bigint
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPCAST00019
-- source_md: skills/pg-sql-generation/references/statements/ddl/cast/drop_cast.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/cast/drop_cast.yaml
-- primary_obligation_id: DCAST-SFV|sfv-7b5dcd057a2cbe4617b2852d|drop_cast
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CAST IF EXISTS (bigint AS dropcast_00019_targettype);
DROP FUNCTION IF EXISTS dropcast_00019_castfn;
DROP TYPE IF EXISTS dropcast_00019_targettype;
\set ON_ERROR_STOP on
-- 2. 创建完整本地类型和因子专用夹具。
CREATE TYPE dropcast_00019_targettype AS ENUM ('a', 'b');
CREATE FUNCTION dropcast_00019_castfn(bigint) RETURNS dropcast_00019_targettype LANGUAGE SQL IMMUTABLE AS $$ SELECT NULL::dropcast_00019_targettype $$;
CREATE CAST (bigint AS dropcast_00019_targettype) WITH FUNCTION dropcast_00019_castfn;
-- 3. 执行唯一获得覆盖信用的 DROP CAST。
-- primary-target-begin
DROP CAST (bigint AS dropcast_00019_targettype);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS cast_absent FROM pg_catalog.pg_cast WHERE castsource = 'bigint'::regtype AND casttarget = 'dropcast_00019_targettype'::regtype ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP CAST IF EXISTS (bigint AS dropcast_00019_targettype);
DROP FUNCTION IF EXISTS dropcast_00019_castfn;
DROP TYPE IF EXISTS dropcast_00019_targettype;
