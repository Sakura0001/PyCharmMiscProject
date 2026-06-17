const fs = require('fs');
const path = require('path');

const outDir = path.resolve('artifacts/generated_sql');

const author = 'y00938623 yuzhengwen';
const version = '26.6.0';
const fe = 'FE2026031900337';
const createAt = '2026-05-07';
const targetRows = 120000;
const helperRows = 7168;

function header(description) {
  return `-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : ${author}
-- create at    : ${createAt}
-- version      : ${version}
-- description  : ${description}
-- FE           : ${fe}
-- ++
-- --------------------------------------------------------

-- read-ahead开关为GLOBAL级变量，本用例执行前保存原值，结束时恢复原值。
SET SESSION long_query_time = 0.01;
SET SESSION rds_log_slow_verbosity = 'io_info';
SET SESSION cte_max_recursion_depth = 10000;
SET SESSION sql_mode = CONCAT_WS(',', @@SESSION.sql_mode, 'NO_UNSIGNED_SUBTRACTION');
`;
}

function originTable(name) {
  return `
DROP TEMPORARY TABLE IF EXISTS ${name}_orig;
CREATE TEMPORARY TABLE ${name}_orig AS
SELECT
    @@GLOBAL.innodb_read_ahead_threshold AS orig_linear_threshold,
    @@GLOBAL.innodb_random_read_ahead AS orig_random_read_ahead;
`;
}

function restore(name) {
  return `
SELECT orig_linear_threshold, orig_random_read_ahead
INTO @orig_linear_threshold, @orig_random_read_ahead
FROM ${name}_orig;
SET GLOBAL innodb_read_ahead_threshold = @orig_linear_threshold;
SET GLOBAL innodb_random_read_ahead = @orig_random_read_ahead;
DROP TEMPORARY TABLE IF EXISTS ${name}_orig;
`;
}

function helper(table) {
  return `
CREATE TABLE ${table} (
    id BIGINT NOT NULL PRIMARY KEY,
    helper_col BIGINT NOT NULL,
    payload LONGBLOB NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

INSERT INTO ${table} (id, helper_col, payload)
WITH RECURSIVE seq(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < ${helperRows}
)
SELECT n, n % 2048, REPEAT('e', 1024 * 1024)
FROM seq;
`;
}

function evict(table) {
  return `
-- 扫描helper表，尽量驱逐目标对象页面，制造冷数据访问条件。
SELECT
    COUNT(*) AS eviction_rows,
    SUM(helper_col) AS eviction_checksum,
    SUM(OCTET_LENGTH(payload)) AS eviction_payload_bytes
FROM ${table};
`;
}

function metricBefore(name) {
  return `
DROP TEMPORARY TABLE IF EXISTS ${name}_before;
CREATE TEMPORARY TABLE ${name}_before AS
SELECT
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_read_ahead' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS linear_before,
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_read_ahead_rnd' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS random_before,
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_reads' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS sync_before
FROM performance_schema.global_status
WHERE variable_name IN ('Innodb_buffer_pool_read_ahead', 'Innodb_buffer_pool_read_ahead_rnd', 'Innodb_buffer_pool_reads');
`;
}

function metricAfter(name) {
  return `
DROP TEMPORARY TABLE IF EXISTS ${name}_after;
CREATE TEMPORARY TABLE ${name}_after AS
SELECT
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_read_ahead' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS linear_after,
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_read_ahead_rnd' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS random_after,
    SUM(CASE WHEN variable_name = 'Innodb_buffer_pool_reads' THEN CAST(variable_value AS UNSIGNED) ELSE 0 END) AS sync_after
FROM performance_schema.global_status
WHERE variable_name IN ('Innodb_buffer_pool_read_ahead', 'Innodb_buffer_pool_read_ahead_rnd', 'Innodb_buffer_pool_reads');
`;
}

function linearResult(label, name, targetBytesExpr) {
  return `
SELECT
    '${label}' AS check_point,
    b.linear_before,
    a.linear_after,
    CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS async_read_pages,
    @@innodb_page_size AS innodb_page_size,
    (CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED)) * @@innodb_page_size AS async_read_bytes,
    CAST(a.sync_after AS SIGNED) - CAST(b.sync_before AS SIGNED) AS sync_read_pages,
    (CAST(a.sync_after AS SIGNED) - CAST(b.sync_before AS SIGNED)) * @@innodb_page_size AS sync_read_bytes,
    ${targetBytesExpr} AS target_object_storage_bytes
FROM ${name}_before b
CROSS JOIN ${name}_after a;
`;
}

function randomResult(label, name, targetBytesExpr) {
  return `
SELECT
    '${label}' AS check_point,
    b.random_before,
    a.random_after,
    CAST(a.random_after AS SIGNED) - CAST(b.random_before AS SIGNED) AS async_read_pages,
    @@innodb_page_size AS innodb_page_size,
    (CAST(a.random_after AS SIGNED) - CAST(b.random_before AS SIGNED)) * @@innodb_page_size AS async_read_bytes,
    CAST(a.sync_after AS SIGNED) - CAST(b.sync_before AS SIGNED) AS sync_read_pages,
    (CAST(a.sync_after AS SIGNED) - CAST(b.sync_before AS SIGNED)) * @@innodb_page_size AS sync_read_bytes,
    ${targetBytesExpr} AS target_object_storage_bytes
FROM ${name}_before b
CROSS JOIN ${name}_after a;
`;
}

function objectBytes(table) {
  return `(SELECT COALESCE(data_length + index_length, 0) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = '${table}')`;
}

function intNormalTable(table) {
  return `
CREATE TABLE ${table} (
    id BIGINT NOT NULL,
    target_col INT NOT NULL,
    payload VARCHAR(256) NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_${table.slice(4)}_target ON ${table} (target_col);

INSERT INTO ${table} (id, target_col, payload)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT (a.n - 1) * 300 + b.n, (a.n - 1) * 300 + b.n, RPAD('p', 220, 'p')
FROM a JOIN b;
`;
}

function partitionDatetimeTable(table) {
  return `
CREATE TABLE ${table} (
    id BIGINT NOT NULL,
    target_col DATETIME NOT NULL,
    payload VARCHAR(256) NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4
PARTITION BY RANGE (id) (
    PARTITION p0 VALUES LESS THAN (30001),
    PARTITION p1 VALUES LESS THAN (60001),
    PARTITION p2 VALUES LESS THAN (90001),
    PARTITION p3 VALUES LESS THAN MAXVALUE
);

CREATE INDEX idx_${table.slice(4)}_target ON ${table} (target_col);

INSERT INTO ${table} (id, target_col, payload)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT
    (a.n - 1) * 300 + b.n,
    TIMESTAMP('2026-05-07 00:00:00') + INTERVAL (((a.n - 1) * 300 + b.n) MOD 86400) SECOND,
    RPAD('p', 220, 'p')
FROM a JOIN b;
`;
}

function viewVarchar(base, view) {
  return `
CREATE TABLE ${base} (
    id BIGINT NOT NULL,
    target_col VARCHAR(64) NOT NULL,
    payload VARCHAR(256) NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE VIEW ${view} AS
SELECT id, target_col, payload
FROM ${base};

CREATE INDEX idx_${base.slice(4)}_target ON ${base} (target_col);

INSERT INTO ${base} (id, target_col, payload)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT (a.n - 1) * 300 + b.n, CONCAT('v_', LPAD((a.n - 1) * 300 + b.n, 8, '0')), RPAD('p', 220, 'p')
FROM a JOIN b;
`;
}

function temporaryDoubleTable(table) {
  return `
CREATE TEMPORARY TABLE ${table} (
    id BIGINT NOT NULL,
    target_col DOUBLE NOT NULL,
    payload VARCHAR(256) NOT NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_${table.slice(4)}_target ON ${table} (target_col);

INSERT INTO ${table} (id, target_col, payload)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT (a.n - 1) * 300 + b.n, ((a.n - 1) * 300 + b.n) / 10, RPAD('p', 220, 'p')
FROM a JOIN b;
`;
}

function foreignJsonTable(parent, child) {
  return `
CREATE TABLE ${parent} (
    id BIGINT NOT NULL PRIMARY KEY,
    parent_marker VARCHAR(32) NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE ${child} (
    id BIGINT NOT NULL,
    target_col JSON NOT NULL,
    payload VARCHAR(256) NOT NULL,
    parent_id BIGINT NOT NULL,
    target_json_key BIGINT GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(target_col, '$.k')) AS UNSIGNED)) STORED,
    PRIMARY KEY (id),
    CONSTRAINT fk_${child.slice(4)}_parent FOREIGN KEY (parent_id) REFERENCES ${parent} (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE INDEX idx_${child.slice(4)}_json_key ON ${child} (target_json_key);
CREATE INDEX idx_${child.slice(4)}_parent ON ${child} (parent_id);

INSERT INTO ${parent} (id, parent_marker)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT (a.n - 1) * 300 + b.n, CONCAT('p_', LPAD((a.n - 1) * 300 + b.n, 8, '0'))
FROM a JOIN b;

INSERT INTO ${child} (id, target_col, payload, parent_id)
WITH RECURSIVE a(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM a WHERE n < 400
),
b(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM b WHERE n < 300
)
SELECT
    (a.n - 1) * 300 + b.n,
    JSON_OBJECT('k', (a.n - 1) * 300 + b.n, 'v', CONCAT('v_', LPAD((a.n - 1) * 300 + b.n, 8, '0'))),
    RPAD('p', 220, 'p'),
    (a.n - 1) * 300 + b.n
FROM a JOIN b;
`;
}

function randomDriver(table) {
  return `
CREATE TEMPORARY TABLE ${table} (
    seq BIGINT NOT NULL PRIMARY KEY,
    id BIGINT NOT NULL,
    KEY idx_${table.slice(4)}_id (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

INSERT INTO ${table} (seq, id)
WITH RECURSIVE seq(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM seq WHERE n < 4096
)
SELECT n, ((n * 7919) MOD ${targetRows}) + 1
FROM seq;
`;
}

const files = new Map();

files.set('bp_s04_linear_readahead_switch_normal_table_int.sql', `${header('场景4：线性预读开关对比，普通表，整型(int)，相同范围扫描下对比threshold=64抑制线性预读和threshold=1开启线性预读，验证异步读页面数和字节数。')}
${originTable('tab_ra_linear_switch_norm_int')}
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_switch_norm_int_off_before;
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_switch_norm_int_off_after;
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_switch_norm_int_on_before;
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_switch_norm_int_on_after;
DROP TABLE IF EXISTS tab_ra_linear_switch_norm_int;
DROP TABLE IF EXISTS tab_ra_linear_switch_norm_int_evict;
${intNormalTable('tab_ra_linear_switch_norm_int')}
${helper('tab_ra_linear_switch_norm_int_evict')}
ANALYZE TABLE tab_ra_linear_switch_norm_int;
ANALYZE TABLE tab_ra_linear_switch_norm_int_evict;
SET GLOBAL innodb_random_read_ahead = OFF;
SET GLOBAL innodb_read_ahead_threshold = 64;
${evict('tab_ra_linear_switch_norm_int_evict')}
${metricBefore('tab_ra_linear_switch_norm_int_off')}
SELECT 'linear_off_range_scan' AS query_label, COUNT(*) AS matched_rows, SUM(target_col) AS target_checksum, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_switch_norm_int
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_switch_norm_int_off')}
${linearResult('linear_off_threshold_64_check', 'tab_ra_linear_switch_norm_int_off', objectBytes('tab_ra_linear_switch_norm_int'))}
SET GLOBAL innodb_read_ahead_threshold = 1;
${evict('tab_ra_linear_switch_norm_int_evict')}
${metricBefore('tab_ra_linear_switch_norm_int_on')}
SELECT 'linear_on_range_scan' AS query_label, COUNT(*) AS matched_rows, SUM(target_col) AS target_checksum, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_switch_norm_int
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_switch_norm_int_on')}
${linearResult('linear_on_threshold_1_check', 'tab_ra_linear_switch_norm_int_on', objectBytes('tab_ra_linear_switch_norm_int'))}
SELECT 'linear_switch_expectation' AS check_point,
    on_r.async_read_pages AS on_async_read_pages,
    off_r.async_read_pages AS off_async_read_pages,
    CASE WHEN on_r.async_read_pages >= off_r.async_read_pages THEN 'OK' ELSE 'CHECK' END AS expectation_result
FROM (
    SELECT CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS async_read_pages
    FROM tab_ra_linear_switch_norm_int_on_before b CROSS JOIN tab_ra_linear_switch_norm_int_on_after a
) on_r
CROSS JOIN (
    SELECT CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS async_read_pages
    FROM tab_ra_linear_switch_norm_int_off_before b CROSS JOIN tab_ra_linear_switch_norm_int_off_after a
) off_r;
${restore('tab_ra_linear_switch_norm_int')}
DROP TABLE IF EXISTS tab_ra_linear_switch_norm_int;
DROP TABLE IF EXISTS tab_ra_linear_switch_norm_int_evict;
`);

files.set('bp_s04_linear_readahead_threshold_partition_table_datetime.sql', `${header('场景4：线性预读阈值验证，分区表，日期类型(datetime)，分别在innodb_read_ahead_threshold=1、56、64下执行冷数据连续范围扫描，验证异步读页面数和字节数。')}
${originTable('tab_ra_linear_threshold_part_dt')}
DROP TABLE IF EXISTS tab_ra_linear_threshold_part_dt;
DROP TABLE IF EXISTS tab_ra_linear_threshold_part_dt_evict;
${partitionDatetimeTable('tab_ra_linear_threshold_part_dt')}
${helper('tab_ra_linear_threshold_part_dt_evict')}
ANALYZE TABLE tab_ra_linear_threshold_part_dt;
ANALYZE TABLE tab_ra_linear_threshold_part_dt_evict;
SET GLOBAL innodb_random_read_ahead = OFF;
SET GLOBAL innodb_read_ahead_threshold = 1;
${evict('tab_ra_linear_threshold_part_dt_evict')}
${metricBefore('tab_ra_linear_threshold_part_dt_t1')}
SELECT 'linear_threshold_1_scan' AS query_label, COUNT(*) AS matched_rows, MIN(target_col) AS min_target_col, MAX(target_col) AS max_target_col, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_threshold_part_dt
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_threshold_part_dt_t1')}
${linearResult('linear_threshold_1_check', 'tab_ra_linear_threshold_part_dt_t1', objectBytes('tab_ra_linear_threshold_part_dt'))}
SET GLOBAL innodb_read_ahead_threshold = 56;
${evict('tab_ra_linear_threshold_part_dt_evict')}
${metricBefore('tab_ra_linear_threshold_part_dt_t56')}
SELECT 'linear_threshold_56_scan' AS query_label, COUNT(*) AS matched_rows, MIN(target_col) AS min_target_col, MAX(target_col) AS max_target_col, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_threshold_part_dt
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_threshold_part_dt_t56')}
${linearResult('linear_threshold_56_check', 'tab_ra_linear_threshold_part_dt_t56', objectBytes('tab_ra_linear_threshold_part_dt'))}
SET GLOBAL innodb_read_ahead_threshold = 64;
${evict('tab_ra_linear_threshold_part_dt_evict')}
${metricBefore('tab_ra_linear_threshold_part_dt_t64')}
SELECT 'linear_threshold_64_scan' AS query_label, COUNT(*) AS matched_rows, MIN(target_col) AS min_target_col, MAX(target_col) AS max_target_col, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_threshold_part_dt
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_threshold_part_dt_t64')}
${linearResult('linear_threshold_64_check', 'tab_ra_linear_threshold_part_dt_t64', objectBytes('tab_ra_linear_threshold_part_dt'))}
${restore('tab_ra_linear_threshold_part_dt')}
DROP TABLE IF EXISTS tab_ra_linear_threshold_part_dt;
DROP TABLE IF EXISTS tab_ra_linear_threshold_part_dt_evict;
`);

files.set('bp_s04_linear_readahead_scale_view_varchar.sql', `${header('场景4：线性预读扫描规模验证，视图，字符串类型(varchar)，冷数据连续扫描小范围和大范围，验证异步读统计随扫描规模增加。')}
${originTable('tab_ra_linear_scale_view_vc')}
DROP VIEW IF EXISTS tab_ra_linear_scale_view_vc;
DROP TABLE IF EXISTS tab_ra_linear_scale_view_vc_base;
DROP TABLE IF EXISTS tab_ra_linear_scale_view_vc_evict;
${viewVarchar('tab_ra_linear_scale_view_vc_base', 'tab_ra_linear_scale_view_vc')}
${helper('tab_ra_linear_scale_view_vc_evict')}
ANALYZE TABLE tab_ra_linear_scale_view_vc_base;
ANALYZE TABLE tab_ra_linear_scale_view_vc_evict;
SET GLOBAL innodb_random_read_ahead = OFF;
SET GLOBAL innodb_read_ahead_threshold = 1;
${evict('tab_ra_linear_scale_view_vc_evict')}
${metricBefore('tab_ra_linear_scale_view_vc_small')}
SELECT 'linear_scale_small_scan' AS query_label, COUNT(*) AS matched_rows, MIN(target_col) AS min_target_col, MAX(target_col) AS max_target_col, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_scale_view_vc
WHERE id BETWEEN 1 AND 10000;
${metricAfter('tab_ra_linear_scale_view_vc_small')}
${linearResult('linear_scale_small_check', 'tab_ra_linear_scale_view_vc_small', objectBytes('tab_ra_linear_scale_view_vc_base'))}
${evict('tab_ra_linear_scale_view_vc_evict')}
${metricBefore('tab_ra_linear_scale_view_vc_large')}
SELECT 'linear_scale_large_scan' AS query_label, COUNT(*) AS matched_rows, MIN(target_col) AS min_target_col, MAX(target_col) AS max_target_col, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM tab_ra_linear_scale_view_vc
WHERE id BETWEEN 1 AND ${targetRows};
${metricAfter('tab_ra_linear_scale_view_vc_large')}
${linearResult('linear_scale_large_check', 'tab_ra_linear_scale_view_vc_large', objectBytes('tab_ra_linear_scale_view_vc_base'))}
SELECT 'linear_scale_expectation' AS check_point,
    large_r.async_read_pages AS large_async_read_pages,
    small_r.async_read_pages AS small_async_read_pages,
    CASE WHEN large_r.async_read_pages >= small_r.async_read_pages THEN 'OK' ELSE 'CHECK' END AS expectation_result
FROM (
    SELECT CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS async_read_pages
    FROM tab_ra_linear_scale_view_vc_large_before b CROSS JOIN tab_ra_linear_scale_view_vc_large_after a
) large_r
CROSS JOIN (
    SELECT CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS async_read_pages
    FROM tab_ra_linear_scale_view_vc_small_before b CROSS JOIN tab_ra_linear_scale_view_vc_small_after a
) small_r;
${restore('tab_ra_linear_scale_view_vc')}
DROP VIEW IF EXISTS tab_ra_linear_scale_view_vc;
DROP TABLE IF EXISTS tab_ra_linear_scale_view_vc_base;
DROP TABLE IF EXISTS tab_ra_linear_scale_view_vc_evict;
`);

files.set('bp_s04_linear_readahead_limit_temporary_table_double.sql', `${header('场景4：线性预读LIMIT小范围扫描，临时表，浮点数类型(double)，开启线性预读后执行冷数据LIMIT小范围扫描，验证异步读页面数和字节数。')}
${originTable('tab_ra_linear_limit_tmp_dbl')}
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_limit_tmp_dbl;
DROP TABLE IF EXISTS tab_ra_linear_limit_tmp_dbl_evict;
${temporaryDoubleTable('tab_ra_linear_limit_tmp_dbl')}
${helper('tab_ra_linear_limit_tmp_dbl_evict')}
ANALYZE TABLE tab_ra_linear_limit_tmp_dbl;
ANALYZE TABLE tab_ra_linear_limit_tmp_dbl_evict;
SET GLOBAL innodb_random_read_ahead = OFF;
SET GLOBAL innodb_read_ahead_threshold = 1;
${evict('tab_ra_linear_limit_tmp_dbl_evict')}
${metricBefore('tab_ra_linear_limit_tmp_dbl_limit')}
SELECT 'linear_limit_small_scan' AS query_label, COUNT(*) AS matched_rows, SUM(target_col) AS target_checksum, SUM(OCTET_LENGTH(payload)) AS payload_bytes
FROM (
    SELECT id, target_col, payload
    FROM tab_ra_linear_limit_tmp_dbl
    WHERE id BETWEEN 1 AND ${targetRows}
    ORDER BY id
    LIMIT 32
) s;
${metricAfter('tab_ra_linear_limit_tmp_dbl_limit')}
${linearResult('linear_limit_small_check', 'tab_ra_linear_limit_tmp_dbl_limit', '120000 * 256')}
SELECT 'linear_limit_expectation' AS check_point,
    CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) AS limit_async_read_pages,
    CASE WHEN CAST(a.linear_after AS SIGNED) - CAST(b.linear_before AS SIGNED) <= 128 THEN 'OK' ELSE 'CHECK' END AS expectation_result
FROM tab_ra_linear_limit_tmp_dbl_limit_before b
CROSS JOIN tab_ra_linear_limit_tmp_dbl_limit_after a;
${restore('tab_ra_linear_limit_tmp_dbl')}
DROP TEMPORARY TABLE IF EXISTS tab_ra_linear_limit_tmp_dbl;
DROP TABLE IF EXISTS tab_ra_linear_limit_tmp_dbl_evict;
`);

files.set('bp_s04_random_readahead_mixed_table_types.sql', `${header('场景4：随机预读验证，开启innodb_random_read_ahead，覆盖普通表、分区表、外键表以及int/datetime/json列类型，观察随机预读异步读统计是否合理。')}
${originTable('tab_ra_random_mixed')}
DROP TEMPORARY TABLE IF EXISTS tab_ra_random_mixed_driver;
DROP TABLE IF EXISTS tab_ra_random_norm_int;
DROP TABLE IF EXISTS tab_ra_random_part_dt;
DROP TABLE IF EXISTS tab_ra_random_fk_js_child;
DROP TABLE IF EXISTS tab_ra_random_fk_js_parent;
DROP TABLE IF EXISTS tab_ra_random_mixed_evict;
${intNormalTable('tab_ra_random_norm_int')}
${partitionDatetimeTable('tab_ra_random_part_dt')}
${foreignJsonTable('tab_ra_random_fk_js_parent', 'tab_ra_random_fk_js_child')}
${randomDriver('tab_ra_random_mixed_driver')}
${helper('tab_ra_random_mixed_evict')}
ANALYZE TABLE tab_ra_random_norm_int;
ANALYZE TABLE tab_ra_random_part_dt;
ANALYZE TABLE tab_ra_random_fk_js_child;
ANALYZE TABLE tab_ra_random_mixed_evict;
SET GLOBAL innodb_read_ahead_threshold = 64;
SET GLOBAL innodb_random_read_ahead = ON;
${evict('tab_ra_random_mixed_evict')}
${metricBefore('tab_ra_random_norm_int')}
SELECT 'random_readahead_normal_int' AS query_label, COUNT(*) AS matched_rows, SUM(t.target_col) AS target_checksum, SUM(OCTET_LENGTH(t.payload)) AS payload_bytes
FROM tab_ra_random_mixed_driver d
STRAIGHT_JOIN tab_ra_random_norm_int t FORCE INDEX (PRIMARY) ON t.id = d.id;
${metricAfter('tab_ra_random_norm_int')}
${randomResult('random_readahead_normal_int_check', 'tab_ra_random_norm_int', objectBytes('tab_ra_random_norm_int'))}
${evict('tab_ra_random_mixed_evict')}
${metricBefore('tab_ra_random_part_dt')}
SELECT 'random_readahead_partition_datetime' AS query_label, COUNT(*) AS matched_rows, MIN(t.target_col) AS min_target_col, MAX(t.target_col) AS max_target_col, SUM(OCTET_LENGTH(t.payload)) AS payload_bytes
FROM tab_ra_random_mixed_driver d
STRAIGHT_JOIN tab_ra_random_part_dt t FORCE INDEX (PRIMARY) ON t.id = d.id;
${metricAfter('tab_ra_random_part_dt')}
${randomResult('random_readahead_partition_datetime_check', 'tab_ra_random_part_dt', objectBytes('tab_ra_random_part_dt'))}
${evict('tab_ra_random_mixed_evict')}
${metricBefore('tab_ra_random_fk_js')}
SELECT 'random_readahead_foreign_json' AS query_label, COUNT(*) AS matched_rows, SUM(t.target_json_key) AS json_key_checksum, SUM(OCTET_LENGTH(t.payload)) AS payload_bytes
FROM tab_ra_random_mixed_driver d
STRAIGHT_JOIN tab_ra_random_fk_js_child t FORCE INDEX (PRIMARY) ON t.id = d.id
JOIN tab_ra_random_fk_js_parent p ON p.id = t.parent_id;
${metricAfter('tab_ra_random_fk_js')}
${randomResult('random_readahead_foreign_json_check', 'tab_ra_random_fk_js', objectBytes('tab_ra_random_fk_js_child'))}
SELECT 'random_readahead_expectation' AS check_point, 'deltas_are_non_negative_and_used_for_reasonableness_observation' AS expectation;
${restore('tab_ra_random_mixed')}
DROP TEMPORARY TABLE IF EXISTS tab_ra_random_mixed_driver;
DROP TABLE IF EXISTS tab_ra_random_norm_int;
DROP TABLE IF EXISTS tab_ra_random_part_dt;
DROP TABLE IF EXISTS tab_ra_random_fk_js_child;
DROP TABLE IF EXISTS tab_ra_random_fk_js_parent;
DROP TABLE IF EXISTS tab_ra_random_mixed_evict;
`);

fs.mkdirSync(outDir, { recursive: true });
for (const [file, sql] of files) {
  fs.writeFileSync(path.join(outDir, file), sql.replace(/\n{3,}/g, '\n\n'));
}
console.log(`generated=${files.size}`);
