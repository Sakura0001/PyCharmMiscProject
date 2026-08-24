-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=absolute, hold_scroll_shape=no_scroll, cursor_name_shape=all_cursors, query_shape=non_scrollable_query, transaction_context=outside_transaction, dependency_state=missing_dependency, invalid_combination=syntax_valid_semantic_error, position_boundary=negative_or_zero_count, verification_mode=catalog_query, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=absolute
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=all_cursors
-- factor query_shape=non_scrollable_query
-- factor transaction_context=outside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=negative_or_zero_count
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00231_table;
CREATE TABLE cur_00231_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00231_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE cur_00231_cursor NO SCROLL CURSOR FOR SELECT missing_column FROM cur_00231_table ORDER BY missing_column;
CLOSE ALL;
FETCH NEXT FROM cur_00231_cursor;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors ORDER BY name;
COMMIT;
DROP TABLE IF EXISTS cur_00231_table;
