-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=closed_cursor, direction_shape=all, hold_scroll_shape=without_hold, cursor_name_shape=all_cursors, query_shape=non_scrollable_query, transaction_context=after_rollback, dependency_state=missing_dependency, invalid_combination=none, position_boundary=negative_or_zero_count, verification_mode=catalog_query, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=closed_cursor
-- factor direction_shape=all
-- factor hold_scroll_shape=without_hold
-- factor cursor_name_shape=all_cursors
-- factor query_shape=non_scrollable_query
-- factor transaction_context=after_rollback
-- factor dependency_state=missing_dependency
-- factor invalid_combination=none
-- factor position_boundary=negative_or_zero_count
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00635_table;
CREATE TABLE cur_00635_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00635_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
ROLLBACK;
DECLARE cur_00635_cursor CURSOR WITHOUT HOLD FOR SELECT id FROM cur_00635_missing_table ORDER BY id;
CLOSE cur_00635_cursor;
MOVE RELATIVE -1 IN ALL;
SELECT 1 AS failure_boundary;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors ORDER BY name;
ROLLBACK;
DROP TABLE IF EXISTS cur_00635_table;
