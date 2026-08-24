-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER LANGUAGE new_owner_shape=session_user
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERLANGUAGE00514
-- source_md: skills/pg-sql-generation/references/statements/ddl/language/alter_language.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/language/alter_language.yaml
-- primary_obligation_id: AL-EXT|00514|owner_change|effect_query|reset_state
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP LANGUAGE IF EXISTS alterlanguage_00514_lang;
DROP FUNCTION IF EXISTS alterlanguage_00514_handler() CASCADE;
DROP ROLE IF EXISTS alterlanguage_00514_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地语言和因子专用夹具。
CREATE ROLE alterlanguage_00514_actor LOGIN;
CREATE FUNCTION alterlanguage_00514_handler() RETURNS language_handler AS '$libdir/plpgsql', 'plpgsql_call_handler' LANGUAGE C;
CREATE LANGUAGE alterlanguage_00514_lang HANDLER alterlanguage_00514_handler;
SET ROLE alterlanguage_00514_actor;
-- 3. 执行唯一获得覆盖信用的 ALTER LANGUAGE。
-- primary-target-begin
ALTER LANGUAGE alterlanguage_00514_lang OWNER TO SESSION_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS owner_is_target FROM pg_catalog.pg_language AS l JOIN pg_catalog.pg_roles AS r ON l.lanowner = r.oid WHERE l.lanname = 'alterlanguage_00514_lang' AND r.rolname = session_user ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP LANGUAGE IF EXISTS alterlanguage_00514_lang;
DROP FUNCTION IF EXISTS alterlanguage_00514_handler() CASCADE;
DROP OWNED BY alterlanguage_00514_actor;
DROP ROLE IF EXISTS alterlanguage_00514_actor;
