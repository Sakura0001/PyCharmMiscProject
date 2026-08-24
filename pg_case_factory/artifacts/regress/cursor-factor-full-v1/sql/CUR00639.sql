-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=closed_cursor, direction_shape=forward_backward_count, hold_scroll_shape=with_hold, cursor_name_shape=all_cursors, query_shape=non_scrollable_query, transaction_context=outside_transaction, dependency_state=missing_dependency, invalid_combination=syntax_valid_semantic_error, position_boundary=negative_or_zero_count, verification_mode=catalog_query, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=closed_cursor
-- factor direction_shape=forward_backward_count
-- factor hold_scroll_shape=with_hold
-- factor cursor_name_shape=all_cursors
-- factor query_shape=non_scrollable_query
-- factor transaction_context=outside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=negative_or_zero_count
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00639_table;
CREATE TABLE cur_00639_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00639_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE cur_00639_cursor CURSOR WITH HOLD FOR SELECT id FROM cur_00639_missing_table ORDER BY id;
CLOSE cur_00639_cursor;
MOVE RELATIVE -1 FROM cur_00639_missing_cursor;
SELECT 1 AS failure_boundary;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors ORDER BY name;
COMMIT;
DROP TABLE IF EXISTS cur_00639_table;
