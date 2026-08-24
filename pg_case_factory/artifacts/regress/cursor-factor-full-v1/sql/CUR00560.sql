-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=prior, hold_scroll_shape=without_hold, cursor_name_shape=missing_name, query_shape=simple_select, transaction_context=after_rollback, dependency_state=ready, invalid_combination=none, position_boundary=before_first, verification_mode=effect_query, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=prior
-- factor hold_scroll_shape=without_hold
-- factor cursor_name_shape=missing_name
-- factor query_shape=simple_select
-- factor transaction_context=after_rollback
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=before_first
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00560_table;
CREATE TABLE cur_00560_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00560_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
ROLLBACK;
DECLARE cur_00560_cursor CURSOR WITHOUT HOLD FOR SELECT id, payload FROM cur_00560_table ORDER BY id;
MOVE ABSOLUTE 0 FROM cur_00560_missing_cursor;
SELECT 1 AS failure_boundary;
SELECT count(*) AS cursor_effect_rows FROM cur_00560_table;
ROLLBACK;
DROP TABLE IF EXISTS cur_00560_table;
