-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 FETCH with statement_branch=branch_1, expected_status=success, cursor_state=with_hold_after_commit, direction_shape=prior, hold_scroll_shape=with_hold, cursor_name_shape=quoted_identifier, query_shape=empty_result, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=after_last, verification_mode=catalog_query, cleanup_mode=reset_state
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=prior
-- factor hold_scroll_shape=with_hold
-- factor cursor_name_shape=quoted_identifier
-- factor query_shape=empty_result
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=after_last
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS cur_00370_table;
CREATE TABLE cur_00370_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00370_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE "cur_00370_Cursor" CURSOR WITH HOLD FOR SELECT id, payload FROM cur_00370_table WHERE false ORDER BY id;
COMMIT;
BEGIN;
FETCH ABSOLUTE 999 FROM "cur_00370_Cursor";
SELECT count(*) AS source_rows FROM cur_00370_table;
SELECT name, is_holdable, is_scrollable FROM pg_catalog.pg_cursors ORDER BY name;
ROLLBACK;
RESET ALL;
DROP TABLE IF EXISTS cur_00370_table;
