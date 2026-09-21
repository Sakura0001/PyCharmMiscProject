-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功 (BINARY/VARBINARY/DECIMAL 已确认支持))
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 20: DECIMAL INSTANT (预期成功)

-- Test Case: TC-I0001
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0001, t2_i0001;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0001 (target) VALUES (-99999999.99);
INSERT INTO t1_i0001 (target) VALUES (99999999.99);
INSERT INTO t1_i0001 (target) VALUES (0.00);
INSERT INTO t1_i0001 (target) VALUES (1.11);
INSERT INTO t1_i0001 (target) VALUES (-1.11);
INSERT INTO t1_i0001 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0001 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0001 (target) VALUES (-1.99);
INSERT INTO t1_i0001 (target) VALUES (0.00);
INSERT INTO t1_i0001 (target) VALUES (1.00);
INSERT INTO t1_i0001 (target) VALUES (99999999.99);
INSERT INTO t1_i0001 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0001 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0001 (target) VALUES (-99999999.99);
INSERT INTO t2_i0001 (target) VALUES (99999999.99);
INSERT INTO t2_i0001 (target) VALUES (0.00);
INSERT INTO t2_i0001 (target) VALUES (1.11);
INSERT INTO t2_i0001 (target) VALUES (-1.11);
INSERT INTO t2_i0001 (target) VALUES (NULL);
INSERT INTO t2_i0001 (target) VALUES (9999999999.99);
INSERT INTO t2_i0001 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0001 (target) VALUES (1.99);
INSERT INTO t2_i0001 (target) VALUES (-1.99);
INSERT INTO t2_i0001 (target) VALUES (0.00);
INSERT INTO t2_i0001 (target) VALUES (1.00);
INSERT INTO t2_i0001 (target) VALUES (99999999.99);
INSERT INTO t2_i0001 (target) VALUES (NULL);
SELECT 'TC-I0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0001
   WHERE id NOT IN (SELECT id FROM t2_i0001)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0001
   WHERE id NOT IN (SELECT id FROM t1_i0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0001 a JOIN t2_i0001 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0002
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0002, t2_i0002;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0002 (target) VALUES (-99999999.99);
INSERT INTO t1_i0002 (target) VALUES (99999999.99);
INSERT INTO t1_i0002 (target) VALUES (0.00);
INSERT INTO t1_i0002 (target) VALUES (1.11);
INSERT INTO t1_i0002 (target) VALUES (-1.11);
INSERT INTO t1_i0002 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0002 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0002 (target) VALUES (-1.99);
INSERT INTO t1_i0002 (target) VALUES (0.00);
INSERT INTO t1_i0002 (target) VALUES (1.00);
INSERT INTO t1_i0002 (target) VALUES (99999999.99);
INSERT INTO t1_i0002 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0002 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0002 (target) VALUES (-99999999.99);
INSERT INTO t2_i0002 (target) VALUES (99999999.99);
INSERT INTO t2_i0002 (target) VALUES (0.00);
INSERT INTO t2_i0002 (target) VALUES (1.11);
INSERT INTO t2_i0002 (target) VALUES (-1.11);
INSERT INTO t2_i0002 (target) VALUES (NULL);
INSERT INTO t2_i0002 (target) VALUES (9999999999.99);
INSERT INTO t2_i0002 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0002 (target) VALUES (1.99);
INSERT INTO t2_i0002 (target) VALUES (-1.99);
INSERT INTO t2_i0002 (target) VALUES (0.00);
INSERT INTO t2_i0002 (target) VALUES (1.00);
INSERT INTO t2_i0002 (target) VALUES (99999999.99);
INSERT INTO t2_i0002 (target) VALUES (NULL);
SELECT 'TC-I0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0002
   WHERE id NOT IN (SELECT id FROM t2_i0002)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0002
   WHERE id NOT IN (SELECT id FROM t1_i0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0002 a JOIN t2_i0002 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0003
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0003, t2_i0003;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0003 (target) VALUES (-99999999.99);
INSERT INTO t1_i0003 (target) VALUES (99999999.99);
INSERT INTO t1_i0003 (target) VALUES (0.00);
INSERT INTO t1_i0003 (target) VALUES (1.11);
INSERT INTO t1_i0003 (target) VALUES (-1.11);
INSERT INTO t1_i0003 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0003 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0003 (target) VALUES (-1.99);
INSERT INTO t1_i0003 (target) VALUES (0.00);
INSERT INTO t1_i0003 (target) VALUES (1.00);
INSERT INTO t1_i0003 (target) VALUES (99999999.99);
INSERT INTO t1_i0003 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0003 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0003 (target) VALUES (-99999999.99);
INSERT INTO t2_i0003 (target) VALUES (99999999.99);
INSERT INTO t2_i0003 (target) VALUES (0.00);
INSERT INTO t2_i0003 (target) VALUES (1.11);
INSERT INTO t2_i0003 (target) VALUES (-1.11);
INSERT INTO t2_i0003 (target) VALUES (NULL);
INSERT INTO t2_i0003 (target) VALUES (9999999999.99);
INSERT INTO t2_i0003 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0003 (target) VALUES (1.99);
INSERT INTO t2_i0003 (target) VALUES (-1.99);
INSERT INTO t2_i0003 (target) VALUES (0.00);
INSERT INTO t2_i0003 (target) VALUES (1.00);
INSERT INTO t2_i0003 (target) VALUES (99999999.99);
INSERT INTO t2_i0003 (target) VALUES (NULL);
SELECT 'TC-I0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0003
   WHERE id NOT IN (SELECT id FROM t2_i0003)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0003
   WHERE id NOT IN (SELECT id FROM t1_i0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0003 a JOIN t2_i0003 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0004
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0004, t2_i0004;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0004 (target) VALUES (-99999999.99);
INSERT INTO t1_i0004 (target) VALUES (99999999.99);
INSERT INTO t1_i0004 (target) VALUES (0.00);
INSERT INTO t1_i0004 (target) VALUES (1.11);
INSERT INTO t1_i0004 (target) VALUES (-1.11);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0004 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0004 (target) VALUES (-1.99);
INSERT INTO t1_i0004 (target) VALUES (0.00);
INSERT INTO t1_i0004 (target) VALUES (1.00);
INSERT INTO t1_i0004 (target) VALUES (99999999.99);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0004 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_i0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0004 (target) VALUES (-99999999.99);
INSERT INTO t2_i0004 (target) VALUES (99999999.99);
INSERT INTO t2_i0004 (target) VALUES (0.00);
INSERT INTO t2_i0004 (target) VALUES (1.11);
INSERT INTO t2_i0004 (target) VALUES (-1.11);
INSERT INTO t2_i0004 (target) VALUES (9999999999.99);
INSERT INTO t2_i0004 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0004 (target) VALUES (1.99);
INSERT INTO t2_i0004 (target) VALUES (-1.99);
INSERT INTO t2_i0004 (target) VALUES (0.00);
INSERT INTO t2_i0004 (target) VALUES (1.00);
INSERT INTO t2_i0004 (target) VALUES (99999999.99);
SELECT 'TC-I0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0004
   WHERE id NOT IN (SELECT id FROM t2_i0004)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0004
   WHERE id NOT IN (SELECT id FROM t1_i0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0004 a JOIN t2_i0004 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0005
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0005, t2_i0005;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0005 (target) VALUES (-99999999.99);
INSERT INTO t1_i0005 (target) VALUES (99999999.99);
INSERT INTO t1_i0005 (target) VALUES (0.00);
INSERT INTO t1_i0005 (target) VALUES (1.11);
INSERT INTO t1_i0005 (target) VALUES (-1.11);
INSERT INTO t1_i0005 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0005 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0005 (target) VALUES (-1.99);
INSERT INTO t1_i0005 (target) VALUES (0.00);
INSERT INTO t1_i0005 (target) VALUES (1.00);
INSERT INTO t1_i0005 (target) VALUES (99999999.99);
INSERT INTO t1_i0005 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0005 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0005 (target) VALUES (-99999999.99);
INSERT INTO t2_i0005 (target) VALUES (99999999.99);
INSERT INTO t2_i0005 (target) VALUES (0.00);
INSERT INTO t2_i0005 (target) VALUES (1.11);
INSERT INTO t2_i0005 (target) VALUES (-1.11);
INSERT INTO t2_i0005 (target) VALUES (NULL);
INSERT INTO t2_i0005 (target) VALUES (9999999999.99);
INSERT INTO t2_i0005 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0005 (target) VALUES (1.99);
INSERT INTO t2_i0005 (target) VALUES (-1.99);
INSERT INTO t2_i0005 (target) VALUES (0.00);
INSERT INTO t2_i0005 (target) VALUES (1.00);
INSERT INTO t2_i0005 (target) VALUES (99999999.99);
INSERT INTO t2_i0005 (target) VALUES (NULL);
SELECT 'TC-I0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0005
   WHERE id NOT IN (SELECT id FROM t2_i0005)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0005
   WHERE id NOT IN (SELECT id FROM t1_i0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0005 a JOIN t2_i0005 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0006
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0006, t2_i0006;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0006 (target) VALUES (-99999999.99);
INSERT INTO t1_i0006 (target) VALUES (99999999.99);
INSERT INTO t1_i0006 (target) VALUES (0.00);
INSERT INTO t1_i0006 (target) VALUES (1.11);
INSERT INTO t1_i0006 (target) VALUES (-1.11);
INSERT INTO t1_i0006 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0006 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0006 (target) VALUES (-1.99);
INSERT INTO t1_i0006 (target) VALUES (0.00);
INSERT INTO t1_i0006 (target) VALUES (1.00);
INSERT INTO t1_i0006 (target) VALUES (99999999.99);
INSERT INTO t1_i0006 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0006 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0006 (target) VALUES (-99999999.99);
INSERT INTO t2_i0006 (target) VALUES (99999999.99);
INSERT INTO t2_i0006 (target) VALUES (0.00);
INSERT INTO t2_i0006 (target) VALUES (1.11);
INSERT INTO t2_i0006 (target) VALUES (-1.11);
INSERT INTO t2_i0006 (target) VALUES (NULL);
INSERT INTO t2_i0006 (target) VALUES (9999999999.99);
INSERT INTO t2_i0006 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0006 (target) VALUES (1.99);
INSERT INTO t2_i0006 (target) VALUES (-1.99);
INSERT INTO t2_i0006 (target) VALUES (0.00);
INSERT INTO t2_i0006 (target) VALUES (1.00);
INSERT INTO t2_i0006 (target) VALUES (99999999.99);
INSERT INTO t2_i0006 (target) VALUES (NULL);
SELECT 'TC-I0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0006
   WHERE id NOT IN (SELECT id FROM t2_i0006)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0006
   WHERE id NOT IN (SELECT id FROM t1_i0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0006 a JOIN t2_i0006 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0007
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0007, t2_i0007;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0007 (target) VALUES (-99999999.99);
INSERT INTO t1_i0007 (target) VALUES (99999999.99);
INSERT INTO t1_i0007 (target) VALUES (0.00);
INSERT INTO t1_i0007 (target) VALUES (1.11);
INSERT INTO t1_i0007 (target) VALUES (-1.11);
INSERT INTO t1_i0007 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0007 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0007 (target) VALUES (-1.99);
INSERT INTO t1_i0007 (target) VALUES (0.00);
INSERT INTO t1_i0007 (target) VALUES (1.00);
INSERT INTO t1_i0007 (target) VALUES (99999999.99);
INSERT INTO t1_i0007 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0007 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0007 (target) VALUES (-99999999.99);
INSERT INTO t2_i0007 (target) VALUES (99999999.99);
INSERT INTO t2_i0007 (target) VALUES (0.00);
INSERT INTO t2_i0007 (target) VALUES (1.11);
INSERT INTO t2_i0007 (target) VALUES (-1.11);
INSERT INTO t2_i0007 (target) VALUES (NULL);
INSERT INTO t2_i0007 (target) VALUES (9999999999.99);
INSERT INTO t2_i0007 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0007 (target) VALUES (1.99);
INSERT INTO t2_i0007 (target) VALUES (-1.99);
INSERT INTO t2_i0007 (target) VALUES (0.00);
INSERT INTO t2_i0007 (target) VALUES (1.00);
INSERT INTO t2_i0007 (target) VALUES (99999999.99);
INSERT INTO t2_i0007 (target) VALUES (NULL);
SELECT 'TC-I0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0007
   WHERE id NOT IN (SELECT id FROM t2_i0007)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0007
   WHERE id NOT IN (SELECT id FROM t1_i0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0007 a JOIN t2_i0007 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0008
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0008, t2_i0008;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0008 (target) VALUES (-99999999.99);
INSERT INTO t1_i0008 (target) VALUES (99999999.99);
INSERT INTO t1_i0008 (target) VALUES (0.00);
INSERT INTO t1_i0008 (target) VALUES (1.11);
INSERT INTO t1_i0008 (target) VALUES (-1.11);
INSERT INTO t1_i0008 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0008 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0008 (target) VALUES (-1.99);
INSERT INTO t1_i0008 (target) VALUES (0.00);
INSERT INTO t1_i0008 (target) VALUES (1.00);
INSERT INTO t1_i0008 (target) VALUES (99999999.99);
INSERT INTO t1_i0008 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0008 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0008 (target) VALUES (-99999999.99);
INSERT INTO t2_i0008 (target) VALUES (99999999.99);
INSERT INTO t2_i0008 (target) VALUES (0.00);
INSERT INTO t2_i0008 (target) VALUES (1.11);
INSERT INTO t2_i0008 (target) VALUES (-1.11);
INSERT INTO t2_i0008 (target) VALUES (NULL);
INSERT INTO t2_i0008 (target) VALUES (9999999999.99);
INSERT INTO t2_i0008 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0008 (target) VALUES (1.99);
INSERT INTO t2_i0008 (target) VALUES (-1.99);
INSERT INTO t2_i0008 (target) VALUES (0.00);
INSERT INTO t2_i0008 (target) VALUES (1.00);
INSERT INTO t2_i0008 (target) VALUES (99999999.99);
INSERT INTO t2_i0008 (target) VALUES (NULL);
SELECT 'TC-I0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0008
   WHERE id NOT IN (SELECT id FROM t2_i0008)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0008
   WHERE id NOT IN (SELECT id FROM t1_i0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0008 a JOIN t2_i0008 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0009
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0009, t2_i0009;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0009 (target) VALUES (-99999999.99);
INSERT INTO t1_i0009 (target) VALUES (99999999.99);
INSERT INTO t1_i0009 (target) VALUES (0.00);
INSERT INTO t1_i0009 (target) VALUES (1.11);
INSERT INTO t1_i0009 (target) VALUES (-1.11);
INSERT INTO t1_i0009 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0009 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0009 (target) VALUES (-1.99);
INSERT INTO t1_i0009 (target) VALUES (0.00);
INSERT INTO t1_i0009 (target) VALUES (1.00);
INSERT INTO t1_i0009 (target) VALUES (99999999.99);
INSERT INTO t1_i0009 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0009 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0009 (target) VALUES (-99999999.99);
INSERT INTO t2_i0009 (target) VALUES (99999999.99);
INSERT INTO t2_i0009 (target) VALUES (0.00);
INSERT INTO t2_i0009 (target) VALUES (1.11);
INSERT INTO t2_i0009 (target) VALUES (-1.11);
INSERT INTO t2_i0009 (target) VALUES (NULL);
INSERT INTO t2_i0009 (target) VALUES (9999999999.99);
INSERT INTO t2_i0009 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0009 (target) VALUES (1.99);
INSERT INTO t2_i0009 (target) VALUES (-1.99);
INSERT INTO t2_i0009 (target) VALUES (0.00);
INSERT INTO t2_i0009 (target) VALUES (1.00);
INSERT INTO t2_i0009 (target) VALUES (99999999.99);
INSERT INTO t2_i0009 (target) VALUES (NULL);
SELECT 'TC-I0009' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0009
   WHERE id NOT IN (SELECT id FROM t2_i0009)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0009
   WHERE id NOT IN (SELECT id FROM t1_i0009)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0009 a JOIN t2_i0009 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0010
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0010, t2_i0010;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0010 (
  target DECIMAL(10,2),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0010 (target) VALUES (-99999999.99);
INSERT INTO t1_i0010 (target) VALUES (99999999.99);
INSERT INTO t1_i0010 (target) VALUES (0.00);
INSERT INTO t1_i0010 (target) VALUES (1.11);
INSERT INTO t1_i0010 (target) VALUES (-1.11);
INSERT INTO t1_i0010 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0010 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0010 (target) VALUES (-1.99);
INSERT INTO t1_i0010 (target) VALUES (0.00);
INSERT INTO t1_i0010 (target) VALUES (1.00);
INSERT INTO t1_i0010 (target) VALUES (99999999.99);
INSERT INTO t1_i0010 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0010 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0010 (
  target DECIMAL(12,2),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0010 (target) VALUES (-99999999.99);
INSERT INTO t2_i0010 (target) VALUES (99999999.99);
INSERT INTO t2_i0010 (target) VALUES (0.00);
INSERT INTO t2_i0010 (target) VALUES (1.11);
INSERT INTO t2_i0010 (target) VALUES (-1.11);
INSERT INTO t2_i0010 (target) VALUES (NULL);
INSERT INTO t2_i0010 (target) VALUES (9999999999.99);
INSERT INTO t2_i0010 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0010 (target) VALUES (1.99);
INSERT INTO t2_i0010 (target) VALUES (-1.99);
INSERT INTO t2_i0010 (target) VALUES (0.00);
INSERT INTO t2_i0010 (target) VALUES (1.00);
INSERT INTO t2_i0010 (target) VALUES (99999999.99);
INSERT INTO t2_i0010 (target) VALUES (NULL);
SELECT 'TC-I0010' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0010
   WHERE id NOT IN (SELECT id FROM t2_i0010)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0010
   WHERE id NOT IN (SELECT id FROM t1_i0010)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0010 a JOIN t2_i0010 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0011
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0011, t2_i0011;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(10,2), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0011 (target) VALUES (-99999999.99);
INSERT INTO t1_i0011 (target) VALUES (99999999.99);
INSERT INTO t1_i0011 (target) VALUES (0.00);
INSERT INTO t1_i0011 (target) VALUES (1.11);
INSERT INTO t1_i0011 (target) VALUES (-1.11);
INSERT INTO t1_i0011 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0011 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0011 (target) VALUES (-1.99);
INSERT INTO t1_i0011 (target) VALUES (0.00);
INSERT INTO t1_i0011 (target) VALUES (1.00);
INSERT INTO t1_i0011 (target) VALUES (99999999.99);
INSERT INTO t1_i0011 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0011 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(12,2), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0011 (target) VALUES (-99999999.99);
INSERT INTO t2_i0011 (target) VALUES (99999999.99);
INSERT INTO t2_i0011 (target) VALUES (0.00);
INSERT INTO t2_i0011 (target) VALUES (1.11);
INSERT INTO t2_i0011 (target) VALUES (-1.11);
INSERT INTO t2_i0011 (target) VALUES (NULL);
INSERT INTO t2_i0011 (target) VALUES (9999999999.99);
INSERT INTO t2_i0011 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0011 (target) VALUES (1.99);
INSERT INTO t2_i0011 (target) VALUES (-1.99);
INSERT INTO t2_i0011 (target) VALUES (0.00);
INSERT INTO t2_i0011 (target) VALUES (1.00);
INSERT INTO t2_i0011 (target) VALUES (99999999.99);
INSERT INTO t2_i0011 (target) VALUES (NULL);
SELECT 'TC-I0011' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0011
   WHERE id NOT IN (SELECT id FROM t2_i0011)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0011
   WHERE id NOT IN (SELECT id FROM t1_i0011)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0011 a JOIN t2_i0011 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0012
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0012, t2_i0012;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0012 (target) VALUES (-99999999.99);
INSERT INTO t1_i0012 (target) VALUES (99999999.99);
INSERT INTO t1_i0012 (target) VALUES (0.00);
INSERT INTO t1_i0012 (target) VALUES (1.11);
INSERT INTO t1_i0012 (target) VALUES (-1.11);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0012 MODIFY target DECIMAL(12,2) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0012 (target) VALUES (-1.99);
INSERT INTO t1_i0012 (target) VALUES (0.00);
INSERT INTO t1_i0012 (target) VALUES (1.00);
INSERT INTO t1_i0012 (target) VALUES (99999999.99);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0012 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0012 (target) VALUES (-99999999.99);
INSERT INTO t2_i0012 (target) VALUES (99999999.99);
INSERT INTO t2_i0012 (target) VALUES (0.00);
INSERT INTO t2_i0012 (target) VALUES (1.11);
INSERT INTO t2_i0012 (target) VALUES (-1.11);
INSERT INTO t2_i0012 (target) VALUES (9999999999.99);
INSERT INTO t2_i0012 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0012 (target) VALUES (1.99);
INSERT INTO t2_i0012 (target) VALUES (-1.99);
INSERT INTO t2_i0012 (target) VALUES (0.00);
INSERT INTO t2_i0012 (target) VALUES (1.00);
INSERT INTO t2_i0012 (target) VALUES (99999999.99);
SELECT 'TC-I0012' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0012
   WHERE id NOT IN (SELECT id FROM t2_i0012)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0012
   WHERE id NOT IN (SELECT id FROM t1_i0012)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0012 a JOIN t2_i0012 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0013
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0013, t2_i0013;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0013 (target) VALUES (-99999999.99);
INSERT INTO t1_i0013 (target) VALUES (99999999.99);
INSERT INTO t1_i0013 (target) VALUES (0.00);
INSERT INTO t1_i0013 (target) VALUES (1.11);
INSERT INTO t1_i0013 (target) VALUES (-1.11);
INSERT INTO t1_i0013 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0013 MODIFY target DECIMAL(12,2) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0013 (target) VALUES (-1.99);
INSERT INTO t1_i0013 (target) VALUES (0.00);
INSERT INTO t1_i0013 (target) VALUES (1.00);
INSERT INTO t1_i0013 (target) VALUES (99999999.99);
INSERT INTO t1_i0013 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0013 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0013 (target) VALUES (-99999999.99);
INSERT INTO t2_i0013 (target) VALUES (99999999.99);
INSERT INTO t2_i0013 (target) VALUES (0.00);
INSERT INTO t2_i0013 (target) VALUES (1.11);
INSERT INTO t2_i0013 (target) VALUES (-1.11);
INSERT INTO t2_i0013 (target) VALUES (NULL);
INSERT INTO t2_i0013 (target) VALUES (9999999999.99);
INSERT INTO t2_i0013 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0013 (target) VALUES (1.99);
INSERT INTO t2_i0013 (target) VALUES (-1.99);
INSERT INTO t2_i0013 (target) VALUES (0.00);
INSERT INTO t2_i0013 (target) VALUES (1.00);
INSERT INTO t2_i0013 (target) VALUES (99999999.99);
INSERT INTO t2_i0013 (target) VALUES (NULL);
SELECT 'TC-I0013' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0013
   WHERE id NOT IN (SELECT id FROM t2_i0013)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0013
   WHERE id NOT IN (SELECT id FROM t1_i0013)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0013 a JOIN t2_i0013 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0014
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0014, t2_i0014;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0014 (target) VALUES (-99999999.99);
INSERT INTO t1_i0014 (target) VALUES (99999999.99);
INSERT INTO t1_i0014 (target) VALUES (0.00);
INSERT INTO t1_i0014 (target) VALUES (1.11);
INSERT INTO t1_i0014 (target) VALUES (-1.11);
INSERT INTO t1_i0014 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0014 MODIFY target DECIMAL(12,2) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0014 (target) VALUES (-1.99);
INSERT INTO t1_i0014 (target) VALUES (0.00);
INSERT INTO t1_i0014 (target) VALUES (1.00);
INSERT INTO t1_i0014 (target) VALUES (99999999.99);
INSERT INTO t1_i0014 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0014 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0014 (target) VALUES (-99999999.99);
INSERT INTO t2_i0014 (target) VALUES (99999999.99);
INSERT INTO t2_i0014 (target) VALUES (0.00);
INSERT INTO t2_i0014 (target) VALUES (1.11);
INSERT INTO t2_i0014 (target) VALUES (-1.11);
INSERT INTO t2_i0014 (target) VALUES (NULL);
INSERT INTO t2_i0014 (target) VALUES (9999999999.99);
INSERT INTO t2_i0014 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0014 (target) VALUES (1.99);
INSERT INTO t2_i0014 (target) VALUES (-1.99);
INSERT INTO t2_i0014 (target) VALUES (0.00);
INSERT INTO t2_i0014 (target) VALUES (1.00);
INSERT INTO t2_i0014 (target) VALUES (99999999.99);
INSERT INTO t2_i0014 (target) VALUES (NULL);
SELECT 'TC-I0014' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0014
   WHERE id NOT IN (SELECT id FROM t2_i0014)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0014
   WHERE id NOT IN (SELECT id FROM t1_i0014)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0014 a JOIN t2_i0014 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0015
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0015, t2_i0015;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0015 (target) VALUES (-99999999.99);
INSERT INTO t1_i0015 (target) VALUES (99999999.99);
INSERT INTO t1_i0015 (target) VALUES (0.00);
INSERT INTO t1_i0015 (target) VALUES (1.11);
INSERT INTO t1_i0015 (target) VALUES (-1.11);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0015 MODIFY target DECIMAL(12,2) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0015 (target) VALUES (-1.99);
INSERT INTO t1_i0015 (target) VALUES (0.00);
INSERT INTO t1_i0015 (target) VALUES (1.00);
INSERT INTO t1_i0015 (target) VALUES (99999999.99);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0015 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0015 (target) VALUES (-99999999.99);
INSERT INTO t2_i0015 (target) VALUES (99999999.99);
INSERT INTO t2_i0015 (target) VALUES (0.00);
INSERT INTO t2_i0015 (target) VALUES (1.11);
INSERT INTO t2_i0015 (target) VALUES (-1.11);
INSERT INTO t2_i0015 (target) VALUES (9999999999.99);
INSERT INTO t2_i0015 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0015 (target) VALUES (1.99);
INSERT INTO t2_i0015 (target) VALUES (-1.99);
INSERT INTO t2_i0015 (target) VALUES (0.00);
INSERT INTO t2_i0015 (target) VALUES (1.00);
INSERT INTO t2_i0015 (target) VALUES (99999999.99);
SELECT 'TC-I0015' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0015
   WHERE id NOT IN (SELECT id FROM t2_i0015)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0015
   WHERE id NOT IN (SELECT id FROM t1_i0015)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0015 a JOIN t2_i0015 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0016
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0016, t2_i0016;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0016 (target) VALUES (-99999999.99);
INSERT INTO t1_i0016 (target) VALUES (99999999.99);
INSERT INTO t1_i0016 (target) VALUES (0.00);
INSERT INTO t1_i0016 (target) VALUES (1.11);
INSERT INTO t1_i0016 (target) VALUES (-1.11);
INSERT INTO t1_i0016 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0016 MODIFY target DECIMAL(12,2) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0016 (target) VALUES (-1.99);
INSERT INTO t1_i0016 (target) VALUES (0.00);
INSERT INTO t1_i0016 (target) VALUES (1.00);
INSERT INTO t1_i0016 (target) VALUES (99999999.99);
INSERT INTO t1_i0016 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0016 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0016 (target) VALUES (-99999999.99);
INSERT INTO t2_i0016 (target) VALUES (99999999.99);
INSERT INTO t2_i0016 (target) VALUES (0.00);
INSERT INTO t2_i0016 (target) VALUES (1.11);
INSERT INTO t2_i0016 (target) VALUES (-1.11);
INSERT INTO t2_i0016 (target) VALUES (NULL);
INSERT INTO t2_i0016 (target) VALUES (9999999999.99);
INSERT INTO t2_i0016 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0016 (target) VALUES (1.99);
INSERT INTO t2_i0016 (target) VALUES (-1.99);
INSERT INTO t2_i0016 (target) VALUES (0.00);
INSERT INTO t2_i0016 (target) VALUES (1.00);
INSERT INTO t2_i0016 (target) VALUES (99999999.99);
INSERT INTO t2_i0016 (target) VALUES (NULL);
SELECT 'TC-I0016' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0016
   WHERE id NOT IN (SELECT id FROM t2_i0016)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0016
   WHERE id NOT IN (SELECT id FROM t1_i0016)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0016 a JOIN t2_i0016 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0017
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0017, t2_i0017;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0017 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0017 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0017' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0017
   WHERE id NOT IN (SELECT id FROM t2_i0017)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0017
   WHERE id NOT IN (SELECT id FROM t1_i0017)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0017 a JOIN t2_i0017 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0018
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0018, t2_i0018;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0018 (target) VALUES (-99999999.99);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0018 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0018 (target) VALUES (-1.99);
INSERT INTO t1_i0018 (target) VALUES (0.00);
INSERT INTO t1_i0018 (target) VALUES (1.00);
INSERT INTO t1_i0018 (target) VALUES (99999999.99);
INSERT INTO t1_i0018 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0018 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0018 (target) VALUES (-99999999.99);
INSERT INTO t2_i0018 (target) VALUES (9999999999.99);
INSERT INTO t2_i0018 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0018 (target) VALUES (1.99);
INSERT INTO t2_i0018 (target) VALUES (-1.99);
INSERT INTO t2_i0018 (target) VALUES (0.00);
INSERT INTO t2_i0018 (target) VALUES (1.00);
INSERT INTO t2_i0018 (target) VALUES (99999999.99);
INSERT INTO t2_i0018 (target) VALUES (NULL);
SELECT 'TC-I0018' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0018
   WHERE id NOT IN (SELECT id FROM t2_i0018)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0018
   WHERE id NOT IN (SELECT id FROM t1_i0018)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0018 a JOIN t2_i0018 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0019
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0019, t2_i0019;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0019 (target) VALUES (-99999999.99);
INSERT INTO t1_i0019 (target) VALUES (99999999.99);
INSERT INTO t1_i0019 (target) VALUES (0.00);
INSERT INTO t1_i0019 (target) VALUES (1.11);
INSERT INTO t1_i0019 (target) VALUES (-1.11);
INSERT INTO t1_i0019 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0019 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0019 (target) VALUES (-1.99);
INSERT INTO t1_i0019 (target) VALUES (0.00);
INSERT INTO t1_i0019 (target) VALUES (1.00);
INSERT INTO t1_i0019 (target) VALUES (99999999.99);
INSERT INTO t1_i0019 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0019 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0019 (target) VALUES (-99999999.99);
INSERT INTO t2_i0019 (target) VALUES (99999999.99);
INSERT INTO t2_i0019 (target) VALUES (0.00);
INSERT INTO t2_i0019 (target) VALUES (1.11);
INSERT INTO t2_i0019 (target) VALUES (-1.11);
INSERT INTO t2_i0019 (target) VALUES (NULL);
INSERT INTO t2_i0019 (target) VALUES (9999999999.99);
INSERT INTO t2_i0019 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0019 (target) VALUES (1.99);
INSERT INTO t2_i0019 (target) VALUES (-1.99);
INSERT INTO t2_i0019 (target) VALUES (0.00);
INSERT INTO t2_i0019 (target) VALUES (1.00);
INSERT INTO t2_i0019 (target) VALUES (99999999.99);
INSERT INTO t2_i0019 (target) VALUES (NULL);
SELECT 'TC-I0019' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0019
   WHERE id NOT IN (SELECT id FROM t2_i0019)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0019
   WHERE id NOT IN (SELECT id FROM t1_i0019)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0019 a JOIN t2_i0019 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0020
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0020, t2_i0020;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0020 (target) VALUES (-99999999.99);
INSERT INTO t1_i0020 (target) VALUES (99999999.99);
INSERT INTO t1_i0020 (target) VALUES (0.00);
INSERT INTO t1_i0020 (target) VALUES (1.11);
INSERT INTO t1_i0020 (target) VALUES (-1.11);
INSERT INTO t1_i0020 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0020 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0020 (target) VALUES (-1.99);
INSERT INTO t1_i0020 (target) VALUES (0.00);
INSERT INTO t1_i0020 (target) VALUES (1.00);
INSERT INTO t1_i0020 (target) VALUES (99999999.99);
INSERT INTO t1_i0020 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0020 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0020 (target) VALUES (-99999999.99);
INSERT INTO t2_i0020 (target) VALUES (99999999.99);
INSERT INTO t2_i0020 (target) VALUES (0.00);
INSERT INTO t2_i0020 (target) VALUES (1.11);
INSERT INTO t2_i0020 (target) VALUES (-1.11);
INSERT INTO t2_i0020 (target) VALUES (NULL);
INSERT INTO t2_i0020 (target) VALUES (9999999999.99);
INSERT INTO t2_i0020 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0020 (target) VALUES (1.99);
INSERT INTO t2_i0020 (target) VALUES (-1.99);
INSERT INTO t2_i0020 (target) VALUES (0.00);
INSERT INTO t2_i0020 (target) VALUES (1.00);
INSERT INTO t2_i0020 (target) VALUES (99999999.99);
INSERT INTO t2_i0020 (target) VALUES (NULL);
SELECT 'TC-I0020' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0020
   WHERE id NOT IN (SELECT id FROM t2_i0020)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0020
   WHERE id NOT IN (SELECT id FROM t1_i0020)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0020 a JOIN t2_i0020 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0021
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0021, t2_i0021;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0021 (target) VALUES (-99999999.99);
INSERT INTO t1_i0021 (target) VALUES (99999999.99);
INSERT INTO t1_i0021 (target) VALUES (0.00);
INSERT INTO t1_i0021 (target) VALUES (1.11);
INSERT INTO t1_i0021 (target) VALUES (-1.11);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0021 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0021 (target) VALUES (-1.99);
INSERT INTO t1_i0021 (target) VALUES (0.00);
INSERT INTO t1_i0021 (target) VALUES (1.00);
INSERT INTO t1_i0021 (target) VALUES (99999999.99);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0021 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0021 (target) VALUES (-99999999.99);
INSERT INTO t2_i0021 (target) VALUES (99999999.99);
INSERT INTO t2_i0021 (target) VALUES (0.00);
INSERT INTO t2_i0021 (target) VALUES (1.11);
INSERT INTO t2_i0021 (target) VALUES (-1.11);
INSERT INTO t2_i0021 (target) VALUES (9999999999.99);
INSERT INTO t2_i0021 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0021 (target) VALUES (1.99);
INSERT INTO t2_i0021 (target) VALUES (-1.99);
INSERT INTO t2_i0021 (target) VALUES (0.00);
INSERT INTO t2_i0021 (target) VALUES (1.00);
INSERT INTO t2_i0021 (target) VALUES (99999999.99);
SELECT 'TC-I0021' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0021
   WHERE id NOT IN (SELECT id FROM t2_i0021)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0021
   WHERE id NOT IN (SELECT id FROM t1_i0021)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0021 a JOIN t2_i0021 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0022
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0022, t2_i0022;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0022 (target) VALUES (-99999999.99);
INSERT INTO t1_i0022 (target) VALUES (99999999.99);
INSERT INTO t1_i0022 (target) VALUES (0.00);
INSERT INTO t1_i0022 (target) VALUES (1.11);
INSERT INTO t1_i0022 (target) VALUES (-1.11);
INSERT INTO t1_i0022 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0022 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0022 (target) VALUES (-1.99);
INSERT INTO t1_i0022 (target) VALUES (0.00);
INSERT INTO t1_i0022 (target) VALUES (1.00);
INSERT INTO t1_i0022 (target) VALUES (99999999.99);
INSERT INTO t1_i0022 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0022 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0022 (target) VALUES (-99999999.99);
INSERT INTO t2_i0022 (target) VALUES (99999999.99);
INSERT INTO t2_i0022 (target) VALUES (0.00);
INSERT INTO t2_i0022 (target) VALUES (1.11);
INSERT INTO t2_i0022 (target) VALUES (-1.11);
INSERT INTO t2_i0022 (target) VALUES (NULL);
INSERT INTO t2_i0022 (target) VALUES (9999999999.99);
INSERT INTO t2_i0022 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0022 (target) VALUES (1.99);
INSERT INTO t2_i0022 (target) VALUES (-1.99);
INSERT INTO t2_i0022 (target) VALUES (0.00);
INSERT INTO t2_i0022 (target) VALUES (1.00);
INSERT INTO t2_i0022 (target) VALUES (99999999.99);
INSERT INTO t2_i0022 (target) VALUES (NULL);
SELECT 'TC-I0022' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0022
   WHERE id NOT IN (SELECT id FROM t2_i0022)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0022
   WHERE id NOT IN (SELECT id FROM t1_i0022)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0022 a JOIN t2_i0022 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0023
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0023, t2_i0023;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0023 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0023 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0023 (target) VALUES (-1.99);
INSERT INTO t1_i0023 (target) VALUES (0.00);
INSERT INTO t1_i0023 (target) VALUES (1.00);
INSERT INTO t1_i0023 (target) VALUES (99999999.99);
INSERT INTO t1_i0023 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0023 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0023 (target) VALUES (NULL);
INSERT INTO t2_i0023 (target) VALUES (9999999999.99);
INSERT INTO t2_i0023 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0023 (target) VALUES (1.99);
INSERT INTO t2_i0023 (target) VALUES (-1.99);
INSERT INTO t2_i0023 (target) VALUES (0.00);
INSERT INTO t2_i0023 (target) VALUES (1.00);
INSERT INTO t2_i0023 (target) VALUES (99999999.99);
INSERT INTO t2_i0023 (target) VALUES (NULL);
SELECT 'TC-I0023' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0023
   WHERE id NOT IN (SELECT id FROM t2_i0023)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0023
   WHERE id NOT IN (SELECT id FROM t1_i0023)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0023 a JOIN t2_i0023 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0024
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0024, t2_i0024;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0024 (target) VALUES (-99999999.99);
INSERT INTO t1_i0024 (target) VALUES (99999999.99);
INSERT INTO t1_i0024 (target) VALUES (0.00);
INSERT INTO t1_i0024 (target) VALUES (1.11);
INSERT INTO t1_i0024 (target) VALUES (-1.11);
INSERT INTO t1_i0024 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0024 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0024 (target) VALUES (-1.99);
INSERT INTO t1_i0024 (target) VALUES (0.00);
INSERT INTO t1_i0024 (target) VALUES (1.00);
INSERT INTO t1_i0024 (target) VALUES (99999999.99);
INSERT INTO t1_i0024 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0024 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0024 (target) VALUES (-99999999.99);
INSERT INTO t2_i0024 (target) VALUES (99999999.99);
INSERT INTO t2_i0024 (target) VALUES (0.00);
INSERT INTO t2_i0024 (target) VALUES (1.11);
INSERT INTO t2_i0024 (target) VALUES (-1.11);
INSERT INTO t2_i0024 (target) VALUES (NULL);
INSERT INTO t2_i0024 (target) VALUES (9999999999.99);
INSERT INTO t2_i0024 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0024 (target) VALUES (1.99);
INSERT INTO t2_i0024 (target) VALUES (-1.99);
INSERT INTO t2_i0024 (target) VALUES (0.00);
INSERT INTO t2_i0024 (target) VALUES (1.00);
INSERT INTO t2_i0024 (target) VALUES (99999999.99);
INSERT INTO t2_i0024 (target) VALUES (NULL);
SELECT 'TC-I0024' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0024
   WHERE id NOT IN (SELECT id FROM t2_i0024)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0024
   WHERE id NOT IN (SELECT id FROM t1_i0024)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0024 a JOIN t2_i0024 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0025
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0025, t2_i0025;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0025 MODIFY target DECIMAL(12,2) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0025 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0025' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0025
   WHERE id NOT IN (SELECT id FROM t2_i0025)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0025
   WHERE id NOT IN (SELECT id FROM t1_i0025)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0025 a JOIN t2_i0025 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0026
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0026, t2_i0026;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0026 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0026 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0026' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0026
   WHERE id NOT IN (SELECT id FROM t2_i0026)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0026
   WHERE id NOT IN (SELECT id FROM t1_i0026)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0026 a JOIN t2_i0026 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0027
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0027, t2_i0027;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(10,2) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0027 MODIFY target DECIMAL(12,2) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0027 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_i0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(12,2) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0027' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0027
   WHERE id NOT IN (SELECT id FROM t2_i0027)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0027
   WHERE id NOT IN (SELECT id FROM t1_i0027)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0027 a JOIN t2_i0027 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0028
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0028, t2_i0028;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0028 (
  target DECIMAL(10,2),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0028 (target) VALUES (-99999999.99);
INSERT INTO t1_i0028 (target) VALUES (99999999.99);
INSERT INTO t1_i0028 (target) VALUES (0.00);
INSERT INTO t1_i0028 (target) VALUES (1.11);
INSERT INTO t1_i0028 (target) VALUES (-1.11);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0028 MODIFY target DECIMAL(12,2), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (-9999999999.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (1.99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0028 (target) VALUES (-1.99);
INSERT INTO t1_i0028 (target) VALUES (0.00);
INSERT INTO t1_i0028 (target) VALUES (1.00);
INSERT INTO t1_i0028 (target) VALUES (99999999.99);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0028 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_i0028 (
  target DECIMAL(10,2),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0028 (target) VALUES (-99999999.99);
INSERT INTO t2_i0028 (target) VALUES (99999999.99);
INSERT INTO t2_i0028 (target) VALUES (0.00);
INSERT INTO t2_i0028 (target) VALUES (1.11);
INSERT INTO t2_i0028 (target) VALUES (-1.11);
INSERT INTO t2_i0028 (target) VALUES (9999999999.99);
INSERT INTO t2_i0028 (target) VALUES (-9999999999.99);
INSERT INTO t2_i0028 (target) VALUES (1.99);
INSERT INTO t2_i0028 (target) VALUES (-1.99);
INSERT INTO t2_i0028 (target) VALUES (0.00);
INSERT INTO t2_i0028 (target) VALUES (1.00);
INSERT INTO t2_i0028 (target) VALUES (99999999.99);
SELECT 'TC-I0028' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0028
   WHERE id NOT IN (SELECT id FROM t2_i0028)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0028
   WHERE id NOT IN (SELECT id FROM t1_i0028)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0028 a JOIN t2_i0028 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0029
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0029, t2_tc_ia0029;
CREATE TABLE t1_tc_ia0029 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(10,2) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0029 (target) VALUES (-99999999.99);
INSERT INTO t1_tc_ia0029 (target) VALUES (99999999.99);
INSERT INTO t1_tc_ia0029 (target) VALUES (0.00);
INSERT INTO t1_tc_ia0029 (target) VALUES (1.11);
INSERT INTO t1_tc_ia0029 (target) VALUES (-1.11);
ALTER TABLE t1_tc_ia0029 MODIFY target DECIMAL(12,2) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0029 (target) VALUES (9999999999.99);
INSERT INTO t1_tc_ia0029 (target) VALUES (-9999999999.99);
INSERT INTO t1_tc_ia0029 (target) VALUES (1.99);
SELECT 'TC-IA0029' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0029' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0030
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0030, t2_i0030;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0030 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0030 (target) VALUES (-9);
INSERT INTO t1_i0030 (target) VALUES (9);
INSERT INTO t1_i0030 (target) VALUES (0);
INSERT INTO t1_i0030 (target) VALUES (1);
INSERT INTO t1_i0030 (target) VALUES (-1);
INSERT INTO t1_i0030 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0030 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0030 (target) VALUES (-999999999);
INSERT INTO t1_i0030 (target) VALUES (0);
INSERT INTO t1_i0030 (target) VALUES (1);
INSERT INTO t1_i0030 (target) VALUES (9);
INSERT INTO t1_i0030 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0030 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0030 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0030 (target) VALUES (-9);
INSERT INTO t2_i0030 (target) VALUES (9);
INSERT INTO t2_i0030 (target) VALUES (0);
INSERT INTO t2_i0030 (target) VALUES (1);
INSERT INTO t2_i0030 (target) VALUES (-1);
INSERT INTO t2_i0030 (target) VALUES (NULL);
INSERT INTO t2_i0030 (target) VALUES (99);
INSERT INTO t2_i0030 (target) VALUES (-99);
INSERT INTO t2_i0030 (target) VALUES (999999999);
INSERT INTO t2_i0030 (target) VALUES (-999999999);
INSERT INTO t2_i0030 (target) VALUES (0);
INSERT INTO t2_i0030 (target) VALUES (1);
INSERT INTO t2_i0030 (target) VALUES (9);
INSERT INTO t2_i0030 (target) VALUES (NULL);
SELECT 'TC-I0030' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0030
   WHERE id NOT IN (SELECT id FROM t2_i0030)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0030
   WHERE id NOT IN (SELECT id FROM t1_i0030)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0030 a JOIN t2_i0030 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0031
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0031, t2_i0031;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0031 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0031 (target) VALUES (-9);
INSERT INTO t1_i0031 (target) VALUES (9);
INSERT INTO t1_i0031 (target) VALUES (0);
INSERT INTO t1_i0031 (target) VALUES (1);
INSERT INTO t1_i0031 (target) VALUES (-1);
INSERT INTO t1_i0031 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0031 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0031 (target) VALUES (-999999999);
INSERT INTO t1_i0031 (target) VALUES (0);
INSERT INTO t1_i0031 (target) VALUES (1);
INSERT INTO t1_i0031 (target) VALUES (9);
INSERT INTO t1_i0031 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0031 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0031 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0031 (target) VALUES (-9);
INSERT INTO t2_i0031 (target) VALUES (9);
INSERT INTO t2_i0031 (target) VALUES (0);
INSERT INTO t2_i0031 (target) VALUES (1);
INSERT INTO t2_i0031 (target) VALUES (-1);
INSERT INTO t2_i0031 (target) VALUES (NULL);
INSERT INTO t2_i0031 (target) VALUES (99);
INSERT INTO t2_i0031 (target) VALUES (-99);
INSERT INTO t2_i0031 (target) VALUES (999999999);
INSERT INTO t2_i0031 (target) VALUES (-999999999);
INSERT INTO t2_i0031 (target) VALUES (0);
INSERT INTO t2_i0031 (target) VALUES (1);
INSERT INTO t2_i0031 (target) VALUES (9);
INSERT INTO t2_i0031 (target) VALUES (NULL);
SELECT 'TC-I0031' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0031
   WHERE id NOT IN (SELECT id FROM t2_i0031)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0031
   WHERE id NOT IN (SELECT id FROM t1_i0031)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0031 a JOIN t2_i0031 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0032
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0032, t2_i0032;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0032 (target) VALUES (-9);
INSERT INTO t1_i0032 (target) VALUES (9);
INSERT INTO t1_i0032 (target) VALUES (0);
INSERT INTO t1_i0032 (target) VALUES (1);
INSERT INTO t1_i0032 (target) VALUES (-1);
INSERT INTO t1_i0032 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0032 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0032 (target) VALUES (-999999999);
INSERT INTO t1_i0032 (target) VALUES (0);
INSERT INTO t1_i0032 (target) VALUES (1);
INSERT INTO t1_i0032 (target) VALUES (9);
INSERT INTO t1_i0032 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0032 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0032 (target) VALUES (-9);
INSERT INTO t2_i0032 (target) VALUES (9);
INSERT INTO t2_i0032 (target) VALUES (0);
INSERT INTO t2_i0032 (target) VALUES (1);
INSERT INTO t2_i0032 (target) VALUES (-1);
INSERT INTO t2_i0032 (target) VALUES (NULL);
INSERT INTO t2_i0032 (target) VALUES (99);
INSERT INTO t2_i0032 (target) VALUES (-99);
INSERT INTO t2_i0032 (target) VALUES (999999999);
INSERT INTO t2_i0032 (target) VALUES (-999999999);
INSERT INTO t2_i0032 (target) VALUES (0);
INSERT INTO t2_i0032 (target) VALUES (1);
INSERT INTO t2_i0032 (target) VALUES (9);
INSERT INTO t2_i0032 (target) VALUES (NULL);
SELECT 'TC-I0032' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0032
   WHERE id NOT IN (SELECT id FROM t2_i0032)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0032
   WHERE id NOT IN (SELECT id FROM t1_i0032)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0032 a JOIN t2_i0032 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0033
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0033, t2_i0033;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0033 (target) VALUES (-9);
INSERT INTO t1_i0033 (target) VALUES (9);
INSERT INTO t1_i0033 (target) VALUES (0);
INSERT INTO t1_i0033 (target) VALUES (1);
INSERT INTO t1_i0033 (target) VALUES (-1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0033 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0033 (target) VALUES (-999999999);
INSERT INTO t1_i0033 (target) VALUES (0);
INSERT INTO t1_i0033 (target) VALUES (1);
INSERT INTO t1_i0033 (target) VALUES (9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0033 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(1,0)
CREATE TABLE t2_i0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0033 (target) VALUES (-9);
INSERT INTO t2_i0033 (target) VALUES (9);
INSERT INTO t2_i0033 (target) VALUES (0);
INSERT INTO t2_i0033 (target) VALUES (1);
INSERT INTO t2_i0033 (target) VALUES (-1);
INSERT INTO t2_i0033 (target) VALUES (99);
INSERT INTO t2_i0033 (target) VALUES (-99);
INSERT INTO t2_i0033 (target) VALUES (999999999);
INSERT INTO t2_i0033 (target) VALUES (-999999999);
INSERT INTO t2_i0033 (target) VALUES (0);
INSERT INTO t2_i0033 (target) VALUES (1);
INSERT INTO t2_i0033 (target) VALUES (9);
SELECT 'TC-I0033' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0033
   WHERE id NOT IN (SELECT id FROM t2_i0033)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0033
   WHERE id NOT IN (SELECT id FROM t1_i0033)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0033 a JOIN t2_i0033 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0034
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0034, t2_i0034;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0034 (target) VALUES (-9);
INSERT INTO t1_i0034 (target) VALUES (9);
INSERT INTO t1_i0034 (target) VALUES (0);
INSERT INTO t1_i0034 (target) VALUES (1);
INSERT INTO t1_i0034 (target) VALUES (-1);
INSERT INTO t1_i0034 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0034 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0034 (target) VALUES (-999999999);
INSERT INTO t1_i0034 (target) VALUES (0);
INSERT INTO t1_i0034 (target) VALUES (1);
INSERT INTO t1_i0034 (target) VALUES (9);
INSERT INTO t1_i0034 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0034 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0034 (target) VALUES (-9);
INSERT INTO t2_i0034 (target) VALUES (9);
INSERT INTO t2_i0034 (target) VALUES (0);
INSERT INTO t2_i0034 (target) VALUES (1);
INSERT INTO t2_i0034 (target) VALUES (-1);
INSERT INTO t2_i0034 (target) VALUES (NULL);
INSERT INTO t2_i0034 (target) VALUES (99);
INSERT INTO t2_i0034 (target) VALUES (-99);
INSERT INTO t2_i0034 (target) VALUES (999999999);
INSERT INTO t2_i0034 (target) VALUES (-999999999);
INSERT INTO t2_i0034 (target) VALUES (0);
INSERT INTO t2_i0034 (target) VALUES (1);
INSERT INTO t2_i0034 (target) VALUES (9);
INSERT INTO t2_i0034 (target) VALUES (NULL);
SELECT 'TC-I0034' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0034
   WHERE id NOT IN (SELECT id FROM t2_i0034)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0034
   WHERE id NOT IN (SELECT id FROM t1_i0034)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0034 a JOIN t2_i0034 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0035
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0035, t2_i0035;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0035 (target) VALUES (-9);
INSERT INTO t1_i0035 (target) VALUES (9);
INSERT INTO t1_i0035 (target) VALUES (0);
INSERT INTO t1_i0035 (target) VALUES (1);
INSERT INTO t1_i0035 (target) VALUES (-1);
INSERT INTO t1_i0035 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0035 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0035 (target) VALUES (-999999999);
INSERT INTO t1_i0035 (target) VALUES (0);
INSERT INTO t1_i0035 (target) VALUES (1);
INSERT INTO t1_i0035 (target) VALUES (9);
INSERT INTO t1_i0035 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0035 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0035 (target) VALUES (-9);
INSERT INTO t2_i0035 (target) VALUES (9);
INSERT INTO t2_i0035 (target) VALUES (0);
INSERT INTO t2_i0035 (target) VALUES (1);
INSERT INTO t2_i0035 (target) VALUES (-1);
INSERT INTO t2_i0035 (target) VALUES (NULL);
INSERT INTO t2_i0035 (target) VALUES (99);
INSERT INTO t2_i0035 (target) VALUES (-99);
INSERT INTO t2_i0035 (target) VALUES (999999999);
INSERT INTO t2_i0035 (target) VALUES (-999999999);
INSERT INTO t2_i0035 (target) VALUES (0);
INSERT INTO t2_i0035 (target) VALUES (1);
INSERT INTO t2_i0035 (target) VALUES (9);
INSERT INTO t2_i0035 (target) VALUES (NULL);
SELECT 'TC-I0035' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0035
   WHERE id NOT IN (SELECT id FROM t2_i0035)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0035
   WHERE id NOT IN (SELECT id FROM t1_i0035)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0035 a JOIN t2_i0035 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0036
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0036, t2_i0036;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0036 (target) VALUES (-9);
INSERT INTO t1_i0036 (target) VALUES (9);
INSERT INTO t1_i0036 (target) VALUES (0);
INSERT INTO t1_i0036 (target) VALUES (1);
INSERT INTO t1_i0036 (target) VALUES (-1);
INSERT INTO t1_i0036 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0036 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0036 (target) VALUES (-999999999);
INSERT INTO t1_i0036 (target) VALUES (0);
INSERT INTO t1_i0036 (target) VALUES (1);
INSERT INTO t1_i0036 (target) VALUES (9);
INSERT INTO t1_i0036 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0036 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0036 (target) VALUES (-9);
INSERT INTO t2_i0036 (target) VALUES (9);
INSERT INTO t2_i0036 (target) VALUES (0);
INSERT INTO t2_i0036 (target) VALUES (1);
INSERT INTO t2_i0036 (target) VALUES (-1);
INSERT INTO t2_i0036 (target) VALUES (NULL);
INSERT INTO t2_i0036 (target) VALUES (99);
INSERT INTO t2_i0036 (target) VALUES (-99);
INSERT INTO t2_i0036 (target) VALUES (999999999);
INSERT INTO t2_i0036 (target) VALUES (-999999999);
INSERT INTO t2_i0036 (target) VALUES (0);
INSERT INTO t2_i0036 (target) VALUES (1);
INSERT INTO t2_i0036 (target) VALUES (9);
INSERT INTO t2_i0036 (target) VALUES (NULL);
SELECT 'TC-I0036' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0036
   WHERE id NOT IN (SELECT id FROM t2_i0036)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0036
   WHERE id NOT IN (SELECT id FROM t1_i0036)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0036 a JOIN t2_i0036 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0037
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0037, t2_i0037;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0037 (target) VALUES (-9);
INSERT INTO t1_i0037 (target) VALUES (9);
INSERT INTO t1_i0037 (target) VALUES (0);
INSERT INTO t1_i0037 (target) VALUES (1);
INSERT INTO t1_i0037 (target) VALUES (-1);
INSERT INTO t1_i0037 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0037 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0037 (target) VALUES (-999999999);
INSERT INTO t1_i0037 (target) VALUES (0);
INSERT INTO t1_i0037 (target) VALUES (1);
INSERT INTO t1_i0037 (target) VALUES (9);
INSERT INTO t1_i0037 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0037 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0037 (target) VALUES (-9);
INSERT INTO t2_i0037 (target) VALUES (9);
INSERT INTO t2_i0037 (target) VALUES (0);
INSERT INTO t2_i0037 (target) VALUES (1);
INSERT INTO t2_i0037 (target) VALUES (-1);
INSERT INTO t2_i0037 (target) VALUES (NULL);
INSERT INTO t2_i0037 (target) VALUES (99);
INSERT INTO t2_i0037 (target) VALUES (-99);
INSERT INTO t2_i0037 (target) VALUES (999999999);
INSERT INTO t2_i0037 (target) VALUES (-999999999);
INSERT INTO t2_i0037 (target) VALUES (0);
INSERT INTO t2_i0037 (target) VALUES (1);
INSERT INTO t2_i0037 (target) VALUES (9);
INSERT INTO t2_i0037 (target) VALUES (NULL);
SELECT 'TC-I0037' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0037
   WHERE id NOT IN (SELECT id FROM t2_i0037)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0037
   WHERE id NOT IN (SELECT id FROM t1_i0037)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0037 a JOIN t2_i0037 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0038
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0038, t2_i0038;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0038 (target) VALUES (-9);
INSERT INTO t1_i0038 (target) VALUES (9);
INSERT INTO t1_i0038 (target) VALUES (0);
INSERT INTO t1_i0038 (target) VALUES (1);
INSERT INTO t1_i0038 (target) VALUES (-1);
INSERT INTO t1_i0038 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0038 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0038 (target) VALUES (-999999999);
INSERT INTO t1_i0038 (target) VALUES (0);
INSERT INTO t1_i0038 (target) VALUES (1);
INSERT INTO t1_i0038 (target) VALUES (9);
INSERT INTO t1_i0038 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0038 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0038 (target) VALUES (-9);
INSERT INTO t2_i0038 (target) VALUES (9);
INSERT INTO t2_i0038 (target) VALUES (0);
INSERT INTO t2_i0038 (target) VALUES (1);
INSERT INTO t2_i0038 (target) VALUES (-1);
INSERT INTO t2_i0038 (target) VALUES (NULL);
INSERT INTO t2_i0038 (target) VALUES (99);
INSERT INTO t2_i0038 (target) VALUES (-99);
INSERT INTO t2_i0038 (target) VALUES (999999999);
INSERT INTO t2_i0038 (target) VALUES (-999999999);
INSERT INTO t2_i0038 (target) VALUES (0);
INSERT INTO t2_i0038 (target) VALUES (1);
INSERT INTO t2_i0038 (target) VALUES (9);
INSERT INTO t2_i0038 (target) VALUES (NULL);
SELECT 'TC-I0038' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0038
   WHERE id NOT IN (SELECT id FROM t2_i0038)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0038
   WHERE id NOT IN (SELECT id FROM t1_i0038)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0038 a JOIN t2_i0038 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0039
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0039, t2_i0039;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0039 (
  target DECIMAL(1,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0039 (target) VALUES (-9);
INSERT INTO t1_i0039 (target) VALUES (9);
INSERT INTO t1_i0039 (target) VALUES (0);
INSERT INTO t1_i0039 (target) VALUES (1);
INSERT INTO t1_i0039 (target) VALUES (-1);
INSERT INTO t1_i0039 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0039 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0039 (target) VALUES (-999999999);
INSERT INTO t1_i0039 (target) VALUES (0);
INSERT INTO t1_i0039 (target) VALUES (1);
INSERT INTO t1_i0039 (target) VALUES (9);
INSERT INTO t1_i0039 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0039 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0039 (
  target DECIMAL(2,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0039 (target) VALUES (-9);
INSERT INTO t2_i0039 (target) VALUES (9);
INSERT INTO t2_i0039 (target) VALUES (0);
INSERT INTO t2_i0039 (target) VALUES (1);
INSERT INTO t2_i0039 (target) VALUES (-1);
INSERT INTO t2_i0039 (target) VALUES (NULL);
INSERT INTO t2_i0039 (target) VALUES (99);
INSERT INTO t2_i0039 (target) VALUES (-99);
INSERT INTO t2_i0039 (target) VALUES (999999999);
INSERT INTO t2_i0039 (target) VALUES (-999999999);
INSERT INTO t2_i0039 (target) VALUES (0);
INSERT INTO t2_i0039 (target) VALUES (1);
INSERT INTO t2_i0039 (target) VALUES (9);
INSERT INTO t2_i0039 (target) VALUES (NULL);
SELECT 'TC-I0039' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0039
   WHERE id NOT IN (SELECT id FROM t2_i0039)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0039
   WHERE id NOT IN (SELECT id FROM t1_i0039)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0039 a JOIN t2_i0039 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0040
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0040, t2_i0040;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(1,0), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0040 (target) VALUES (-9);
INSERT INTO t1_i0040 (target) VALUES (9);
INSERT INTO t1_i0040 (target) VALUES (0);
INSERT INTO t1_i0040 (target) VALUES (1);
INSERT INTO t1_i0040 (target) VALUES (-1);
INSERT INTO t1_i0040 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0040 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0040 (target) VALUES (-999999999);
INSERT INTO t1_i0040 (target) VALUES (0);
INSERT INTO t1_i0040 (target) VALUES (1);
INSERT INTO t1_i0040 (target) VALUES (9);
INSERT INTO t1_i0040 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0040 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(2,0), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0040 (target) VALUES (-9);
INSERT INTO t2_i0040 (target) VALUES (9);
INSERT INTO t2_i0040 (target) VALUES (0);
INSERT INTO t2_i0040 (target) VALUES (1);
INSERT INTO t2_i0040 (target) VALUES (-1);
INSERT INTO t2_i0040 (target) VALUES (NULL);
INSERT INTO t2_i0040 (target) VALUES (99);
INSERT INTO t2_i0040 (target) VALUES (-99);
INSERT INTO t2_i0040 (target) VALUES (999999999);
INSERT INTO t2_i0040 (target) VALUES (-999999999);
INSERT INTO t2_i0040 (target) VALUES (0);
INSERT INTO t2_i0040 (target) VALUES (1);
INSERT INTO t2_i0040 (target) VALUES (9);
INSERT INTO t2_i0040 (target) VALUES (NULL);
SELECT 'TC-I0040' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0040
   WHERE id NOT IN (SELECT id FROM t2_i0040)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0040
   WHERE id NOT IN (SELECT id FROM t1_i0040)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0040 a JOIN t2_i0040 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0041
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0041, t2_i0041;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0041 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0041 (target) VALUES (-9);
INSERT INTO t1_i0041 (target) VALUES (9);
INSERT INTO t1_i0041 (target) VALUES (0);
INSERT INTO t1_i0041 (target) VALUES (1);
INSERT INTO t1_i0041 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0041 MODIFY target DECIMAL(2,0) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0041 (target) VALUES (-999999999);
INSERT INTO t1_i0041 (target) VALUES (0);
INSERT INTO t1_i0041 (target) VALUES (1);
INSERT INTO t1_i0041 (target) VALUES (9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0041 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0041 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0041 (target) VALUES (-9);
INSERT INTO t2_i0041 (target) VALUES (9);
INSERT INTO t2_i0041 (target) VALUES (0);
INSERT INTO t2_i0041 (target) VALUES (1);
INSERT INTO t2_i0041 (target) VALUES (-1);
INSERT INTO t2_i0041 (target) VALUES (99);
INSERT INTO t2_i0041 (target) VALUES (-99);
INSERT INTO t2_i0041 (target) VALUES (999999999);
INSERT INTO t2_i0041 (target) VALUES (-999999999);
INSERT INTO t2_i0041 (target) VALUES (0);
INSERT INTO t2_i0041 (target) VALUES (1);
INSERT INTO t2_i0041 (target) VALUES (9);
SELECT 'TC-I0041' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0041
   WHERE id NOT IN (SELECT id FROM t2_i0041)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0041
   WHERE id NOT IN (SELECT id FROM t1_i0041)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0041 a JOIN t2_i0041 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0042
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0042, t2_i0042;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0042 (target) VALUES (-9);
INSERT INTO t1_i0042 (target) VALUES (9);
INSERT INTO t1_i0042 (target) VALUES (0);
INSERT INTO t1_i0042 (target) VALUES (1);
INSERT INTO t1_i0042 (target) VALUES (-1);
INSERT INTO t1_i0042 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0042 MODIFY target DECIMAL(2,0) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0042 (target) VALUES (-999999999);
INSERT INTO t1_i0042 (target) VALUES (0);
INSERT INTO t1_i0042 (target) VALUES (1);
INSERT INTO t1_i0042 (target) VALUES (9);
INSERT INTO t1_i0042 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0042 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0042 (target) VALUES (-9);
INSERT INTO t2_i0042 (target) VALUES (9);
INSERT INTO t2_i0042 (target) VALUES (0);
INSERT INTO t2_i0042 (target) VALUES (1);
INSERT INTO t2_i0042 (target) VALUES (-1);
INSERT INTO t2_i0042 (target) VALUES (NULL);
INSERT INTO t2_i0042 (target) VALUES (99);
INSERT INTO t2_i0042 (target) VALUES (-99);
INSERT INTO t2_i0042 (target) VALUES (999999999);
INSERT INTO t2_i0042 (target) VALUES (-999999999);
INSERT INTO t2_i0042 (target) VALUES (0);
INSERT INTO t2_i0042 (target) VALUES (1);
INSERT INTO t2_i0042 (target) VALUES (9);
INSERT INTO t2_i0042 (target) VALUES (NULL);
SELECT 'TC-I0042' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0042
   WHERE id NOT IN (SELECT id FROM t2_i0042)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0042
   WHERE id NOT IN (SELECT id FROM t1_i0042)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0042 a JOIN t2_i0042 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0043
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0043, t2_i0043;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0043 (target) VALUES (-9);
INSERT INTO t1_i0043 (target) VALUES (9);
INSERT INTO t1_i0043 (target) VALUES (0);
INSERT INTO t1_i0043 (target) VALUES (1);
INSERT INTO t1_i0043 (target) VALUES (-1);
INSERT INTO t1_i0043 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0043 MODIFY target DECIMAL(2,0) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0043 (target) VALUES (-999999999);
INSERT INTO t1_i0043 (target) VALUES (0);
INSERT INTO t1_i0043 (target) VALUES (1);
INSERT INTO t1_i0043 (target) VALUES (9);
INSERT INTO t1_i0043 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0043 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0043 (target) VALUES (-9);
INSERT INTO t2_i0043 (target) VALUES (9);
INSERT INTO t2_i0043 (target) VALUES (0);
INSERT INTO t2_i0043 (target) VALUES (1);
INSERT INTO t2_i0043 (target) VALUES (-1);
INSERT INTO t2_i0043 (target) VALUES (NULL);
INSERT INTO t2_i0043 (target) VALUES (99);
INSERT INTO t2_i0043 (target) VALUES (-99);
INSERT INTO t2_i0043 (target) VALUES (999999999);
INSERT INTO t2_i0043 (target) VALUES (-999999999);
INSERT INTO t2_i0043 (target) VALUES (0);
INSERT INTO t2_i0043 (target) VALUES (1);
INSERT INTO t2_i0043 (target) VALUES (9);
INSERT INTO t2_i0043 (target) VALUES (NULL);
SELECT 'TC-I0043' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0043
   WHERE id NOT IN (SELECT id FROM t2_i0043)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0043
   WHERE id NOT IN (SELECT id FROM t1_i0043)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0043 a JOIN t2_i0043 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0044
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0044, t2_i0044;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0044 (target) VALUES (-9);
INSERT INTO t1_i0044 (target) VALUES (9);
INSERT INTO t1_i0044 (target) VALUES (0);
INSERT INTO t1_i0044 (target) VALUES (1);
INSERT INTO t1_i0044 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0044 MODIFY target DECIMAL(2,0) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0044 (target) VALUES (-999999999);
INSERT INTO t1_i0044 (target) VALUES (0);
INSERT INTO t1_i0044 (target) VALUES (1);
INSERT INTO t1_i0044 (target) VALUES (9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0044 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0044 (target) VALUES (-9);
INSERT INTO t2_i0044 (target) VALUES (9);
INSERT INTO t2_i0044 (target) VALUES (0);
INSERT INTO t2_i0044 (target) VALUES (1);
INSERT INTO t2_i0044 (target) VALUES (-1);
INSERT INTO t2_i0044 (target) VALUES (99);
INSERT INTO t2_i0044 (target) VALUES (-99);
INSERT INTO t2_i0044 (target) VALUES (999999999);
INSERT INTO t2_i0044 (target) VALUES (-999999999);
INSERT INTO t2_i0044 (target) VALUES (0);
INSERT INTO t2_i0044 (target) VALUES (1);
INSERT INTO t2_i0044 (target) VALUES (9);
SELECT 'TC-I0044' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0044
   WHERE id NOT IN (SELECT id FROM t2_i0044)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0044
   WHERE id NOT IN (SELECT id FROM t1_i0044)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0044 a JOIN t2_i0044 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0045
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0045, t2_i0045;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0045 (target) VALUES (-9);
INSERT INTO t1_i0045 (target) VALUES (9);
INSERT INTO t1_i0045 (target) VALUES (0);
INSERT INTO t1_i0045 (target) VALUES (1);
INSERT INTO t1_i0045 (target) VALUES (-1);
INSERT INTO t1_i0045 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0045 MODIFY target DECIMAL(2,0) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0045 (target) VALUES (-999999999);
INSERT INTO t1_i0045 (target) VALUES (0);
INSERT INTO t1_i0045 (target) VALUES (1);
INSERT INTO t1_i0045 (target) VALUES (9);
INSERT INTO t1_i0045 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0045 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0045 (target) VALUES (-9);
INSERT INTO t2_i0045 (target) VALUES (9);
INSERT INTO t2_i0045 (target) VALUES (0);
INSERT INTO t2_i0045 (target) VALUES (1);
INSERT INTO t2_i0045 (target) VALUES (-1);
INSERT INTO t2_i0045 (target) VALUES (NULL);
INSERT INTO t2_i0045 (target) VALUES (99);
INSERT INTO t2_i0045 (target) VALUES (-99);
INSERT INTO t2_i0045 (target) VALUES (999999999);
INSERT INTO t2_i0045 (target) VALUES (-999999999);
INSERT INTO t2_i0045 (target) VALUES (0);
INSERT INTO t2_i0045 (target) VALUES (1);
INSERT INTO t2_i0045 (target) VALUES (9);
INSERT INTO t2_i0045 (target) VALUES (NULL);
SELECT 'TC-I0045' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0045
   WHERE id NOT IN (SELECT id FROM t2_i0045)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0045
   WHERE id NOT IN (SELECT id FROM t1_i0045)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0045 a JOIN t2_i0045 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0046
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0046, t2_i0046;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0046 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0046 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0046' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0046
   WHERE id NOT IN (SELECT id FROM t2_i0046)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0046
   WHERE id NOT IN (SELECT id FROM t1_i0046)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0046 a JOIN t2_i0046 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0047
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0047, t2_i0047;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0047 (target) VALUES (-9);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0047 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0047 (target) VALUES (-999999999);
INSERT INTO t1_i0047 (target) VALUES (0);
INSERT INTO t1_i0047 (target) VALUES (1);
INSERT INTO t1_i0047 (target) VALUES (9);
INSERT INTO t1_i0047 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0047 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0047 (target) VALUES (-9);
INSERT INTO t2_i0047 (target) VALUES (99);
INSERT INTO t2_i0047 (target) VALUES (-99);
INSERT INTO t2_i0047 (target) VALUES (999999999);
INSERT INTO t2_i0047 (target) VALUES (-999999999);
INSERT INTO t2_i0047 (target) VALUES (0);
INSERT INTO t2_i0047 (target) VALUES (1);
INSERT INTO t2_i0047 (target) VALUES (9);
INSERT INTO t2_i0047 (target) VALUES (NULL);
SELECT 'TC-I0047' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0047
   WHERE id NOT IN (SELECT id FROM t2_i0047)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0047
   WHERE id NOT IN (SELECT id FROM t1_i0047)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0047 a JOIN t2_i0047 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0048
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0048, t2_i0048;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0048 (target) VALUES (-9);
INSERT INTO t1_i0048 (target) VALUES (9);
INSERT INTO t1_i0048 (target) VALUES (0);
INSERT INTO t1_i0048 (target) VALUES (1);
INSERT INTO t1_i0048 (target) VALUES (-1);
INSERT INTO t1_i0048 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0048 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0048 (target) VALUES (-999999999);
INSERT INTO t1_i0048 (target) VALUES (0);
INSERT INTO t1_i0048 (target) VALUES (1);
INSERT INTO t1_i0048 (target) VALUES (9);
INSERT INTO t1_i0048 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0048 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0048 (target) VALUES (-9);
INSERT INTO t2_i0048 (target) VALUES (9);
INSERT INTO t2_i0048 (target) VALUES (0);
INSERT INTO t2_i0048 (target) VALUES (1);
INSERT INTO t2_i0048 (target) VALUES (-1);
INSERT INTO t2_i0048 (target) VALUES (NULL);
INSERT INTO t2_i0048 (target) VALUES (99);
INSERT INTO t2_i0048 (target) VALUES (-99);
INSERT INTO t2_i0048 (target) VALUES (999999999);
INSERT INTO t2_i0048 (target) VALUES (-999999999);
INSERT INTO t2_i0048 (target) VALUES (0);
INSERT INTO t2_i0048 (target) VALUES (1);
INSERT INTO t2_i0048 (target) VALUES (9);
INSERT INTO t2_i0048 (target) VALUES (NULL);
SELECT 'TC-I0048' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0048
   WHERE id NOT IN (SELECT id FROM t2_i0048)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0048
   WHERE id NOT IN (SELECT id FROM t1_i0048)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0048 a JOIN t2_i0048 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0049
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0049, t2_i0049;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0049 (target) VALUES (-9);
INSERT INTO t1_i0049 (target) VALUES (9);
INSERT INTO t1_i0049 (target) VALUES (0);
INSERT INTO t1_i0049 (target) VALUES (1);
INSERT INTO t1_i0049 (target) VALUES (-1);
INSERT INTO t1_i0049 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0049 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0049 (target) VALUES (-999999999);
INSERT INTO t1_i0049 (target) VALUES (0);
INSERT INTO t1_i0049 (target) VALUES (1);
INSERT INTO t1_i0049 (target) VALUES (9);
INSERT INTO t1_i0049 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0049 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0049 (target) VALUES (-9);
INSERT INTO t2_i0049 (target) VALUES (9);
INSERT INTO t2_i0049 (target) VALUES (0);
INSERT INTO t2_i0049 (target) VALUES (1);
INSERT INTO t2_i0049 (target) VALUES (-1);
INSERT INTO t2_i0049 (target) VALUES (NULL);
INSERT INTO t2_i0049 (target) VALUES (99);
INSERT INTO t2_i0049 (target) VALUES (-99);
INSERT INTO t2_i0049 (target) VALUES (999999999);
INSERT INTO t2_i0049 (target) VALUES (-999999999);
INSERT INTO t2_i0049 (target) VALUES (0);
INSERT INTO t2_i0049 (target) VALUES (1);
INSERT INTO t2_i0049 (target) VALUES (9);
INSERT INTO t2_i0049 (target) VALUES (NULL);
SELECT 'TC-I0049' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0049
   WHERE id NOT IN (SELECT id FROM t2_i0049)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0049
   WHERE id NOT IN (SELECT id FROM t1_i0049)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0049 a JOIN t2_i0049 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0050
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0050, t2_i0050;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0050 (target) VALUES (-9);
INSERT INTO t1_i0050 (target) VALUES (9);
INSERT INTO t1_i0050 (target) VALUES (0);
INSERT INTO t1_i0050 (target) VALUES (1);
INSERT INTO t1_i0050 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0050 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0050 (target) VALUES (-999999999);
INSERT INTO t1_i0050 (target) VALUES (0);
INSERT INTO t1_i0050 (target) VALUES (1);
INSERT INTO t1_i0050 (target) VALUES (9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0050 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0050 (target) VALUES (-9);
INSERT INTO t2_i0050 (target) VALUES (9);
INSERT INTO t2_i0050 (target) VALUES (0);
INSERT INTO t2_i0050 (target) VALUES (1);
INSERT INTO t2_i0050 (target) VALUES (-1);
INSERT INTO t2_i0050 (target) VALUES (99);
INSERT INTO t2_i0050 (target) VALUES (-99);
INSERT INTO t2_i0050 (target) VALUES (999999999);
INSERT INTO t2_i0050 (target) VALUES (-999999999);
INSERT INTO t2_i0050 (target) VALUES (0);
INSERT INTO t2_i0050 (target) VALUES (1);
INSERT INTO t2_i0050 (target) VALUES (9);
SELECT 'TC-I0050' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0050
   WHERE id NOT IN (SELECT id FROM t2_i0050)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0050
   WHERE id NOT IN (SELECT id FROM t1_i0050)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0050 a JOIN t2_i0050 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0051
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0051, t2_i0051;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0051 (target) VALUES (-9);
INSERT INTO t1_i0051 (target) VALUES (9);
INSERT INTO t1_i0051 (target) VALUES (0);
INSERT INTO t1_i0051 (target) VALUES (1);
INSERT INTO t1_i0051 (target) VALUES (-1);
INSERT INTO t1_i0051 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0051 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0051 (target) VALUES (-999999999);
INSERT INTO t1_i0051 (target) VALUES (0);
INSERT INTO t1_i0051 (target) VALUES (1);
INSERT INTO t1_i0051 (target) VALUES (9);
INSERT INTO t1_i0051 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0051 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0051 (target) VALUES (-9);
INSERT INTO t2_i0051 (target) VALUES (9);
INSERT INTO t2_i0051 (target) VALUES (0);
INSERT INTO t2_i0051 (target) VALUES (1);
INSERT INTO t2_i0051 (target) VALUES (-1);
INSERT INTO t2_i0051 (target) VALUES (NULL);
INSERT INTO t2_i0051 (target) VALUES (99);
INSERT INTO t2_i0051 (target) VALUES (-99);
INSERT INTO t2_i0051 (target) VALUES (999999999);
INSERT INTO t2_i0051 (target) VALUES (-999999999);
INSERT INTO t2_i0051 (target) VALUES (0);
INSERT INTO t2_i0051 (target) VALUES (1);
INSERT INTO t2_i0051 (target) VALUES (9);
INSERT INTO t2_i0051 (target) VALUES (NULL);
SELECT 'TC-I0051' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0051
   WHERE id NOT IN (SELECT id FROM t2_i0051)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0051
   WHERE id NOT IN (SELECT id FROM t1_i0051)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0051 a JOIN t2_i0051 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0052
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0052, t2_i0052;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0052 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0052 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0052 (target) VALUES (-999999999);
INSERT INTO t1_i0052 (target) VALUES (0);
INSERT INTO t1_i0052 (target) VALUES (1);
INSERT INTO t1_i0052 (target) VALUES (9);
INSERT INTO t1_i0052 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0052 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0052 (target) VALUES (NULL);
INSERT INTO t2_i0052 (target) VALUES (99);
INSERT INTO t2_i0052 (target) VALUES (-99);
INSERT INTO t2_i0052 (target) VALUES (999999999);
INSERT INTO t2_i0052 (target) VALUES (-999999999);
INSERT INTO t2_i0052 (target) VALUES (0);
INSERT INTO t2_i0052 (target) VALUES (1);
INSERT INTO t2_i0052 (target) VALUES (9);
INSERT INTO t2_i0052 (target) VALUES (NULL);
SELECT 'TC-I0052' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0052
   WHERE id NOT IN (SELECT id FROM t2_i0052)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0052
   WHERE id NOT IN (SELECT id FROM t1_i0052)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0052 a JOIN t2_i0052 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0053
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0053, t2_i0053;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0053 (target) VALUES (-9);
INSERT INTO t1_i0053 (target) VALUES (9);
INSERT INTO t1_i0053 (target) VALUES (0);
INSERT INTO t1_i0053 (target) VALUES (1);
INSERT INTO t1_i0053 (target) VALUES (-1);
INSERT INTO t1_i0053 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0053 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0053 (target) VALUES (-999999999);
INSERT INTO t1_i0053 (target) VALUES (0);
INSERT INTO t1_i0053 (target) VALUES (1);
INSERT INTO t1_i0053 (target) VALUES (9);
INSERT INTO t1_i0053 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0053 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0053 (target) VALUES (-9);
INSERT INTO t2_i0053 (target) VALUES (9);
INSERT INTO t2_i0053 (target) VALUES (0);
INSERT INTO t2_i0053 (target) VALUES (1);
INSERT INTO t2_i0053 (target) VALUES (-1);
INSERT INTO t2_i0053 (target) VALUES (NULL);
INSERT INTO t2_i0053 (target) VALUES (99);
INSERT INTO t2_i0053 (target) VALUES (-99);
INSERT INTO t2_i0053 (target) VALUES (999999999);
INSERT INTO t2_i0053 (target) VALUES (-999999999);
INSERT INTO t2_i0053 (target) VALUES (0);
INSERT INTO t2_i0053 (target) VALUES (1);
INSERT INTO t2_i0053 (target) VALUES (9);
INSERT INTO t2_i0053 (target) VALUES (NULL);
SELECT 'TC-I0053' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0053
   WHERE id NOT IN (SELECT id FROM t2_i0053)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0053
   WHERE id NOT IN (SELECT id FROM t1_i0053)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0053 a JOIN t2_i0053 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0054
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0054, t2_i0054;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0054 MODIFY target DECIMAL(2,0) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0054 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0054' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0054
   WHERE id NOT IN (SELECT id FROM t2_i0054)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0054
   WHERE id NOT IN (SELECT id FROM t1_i0054)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0054 a JOIN t2_i0054 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0055
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0055, t2_i0055;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0055 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0055 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0055' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0055
   WHERE id NOT IN (SELECT id FROM t2_i0055)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0055
   WHERE id NOT IN (SELECT id FROM t1_i0055)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0055 a JOIN t2_i0055 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0056
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0056, t2_i0056;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0056 MODIFY target DECIMAL(2,0) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0056 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(2,0)
CREATE TABLE t2_i0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0056' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0056
   WHERE id NOT IN (SELECT id FROM t2_i0056)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0056
   WHERE id NOT IN (SELECT id FROM t1_i0056)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0056 a JOIN t2_i0056 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0057
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0057, t2_i0057;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0057 (
  target DECIMAL(1,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0057 (target) VALUES (-9);
INSERT INTO t1_i0057 (target) VALUES (9);
INSERT INTO t1_i0057 (target) VALUES (0);
INSERT INTO t1_i0057 (target) VALUES (1);
INSERT INTO t1_i0057 (target) VALUES (-1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0057 MODIFY target DECIMAL(2,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (-99);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0057 (target) VALUES (-999999999);
INSERT INTO t1_i0057 (target) VALUES (0);
INSERT INTO t1_i0057 (target) VALUES (1);
INSERT INTO t1_i0057 (target) VALUES (9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0057 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(1,0)
CREATE TABLE t2_i0057 (
  target DECIMAL(1,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0057 (target) VALUES (-9);
INSERT INTO t2_i0057 (target) VALUES (9);
INSERT INTO t2_i0057 (target) VALUES (0);
INSERT INTO t2_i0057 (target) VALUES (1);
INSERT INTO t2_i0057 (target) VALUES (-1);
INSERT INTO t2_i0057 (target) VALUES (99);
INSERT INTO t2_i0057 (target) VALUES (-99);
INSERT INTO t2_i0057 (target) VALUES (999999999);
INSERT INTO t2_i0057 (target) VALUES (-999999999);
INSERT INTO t2_i0057 (target) VALUES (0);
INSERT INTO t2_i0057 (target) VALUES (1);
INSERT INTO t2_i0057 (target) VALUES (9);
SELECT 'TC-I0057' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0057
   WHERE id NOT IN (SELECT id FROM t2_i0057)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0057
   WHERE id NOT IN (SELECT id FROM t1_i0057)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0057 a JOIN t2_i0057 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0058
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(1,0) -> DECIMAL(2,0), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0058, t2_tc_ia0058;
CREATE TABLE t1_tc_ia0058 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(1,0) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0058 (target) VALUES (-9);
INSERT INTO t1_tc_ia0058 (target) VALUES (9);
INSERT INTO t1_tc_ia0058 (target) VALUES (0);
INSERT INTO t1_tc_ia0058 (target) VALUES (1);
INSERT INTO t1_tc_ia0058 (target) VALUES (-1);
ALTER TABLE t1_tc_ia0058 MODIFY target DECIMAL(2,0) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0058 (target) VALUES (99);
INSERT INTO t1_tc_ia0058 (target) VALUES (-99);
INSERT INTO t1_tc_ia0058 (target) VALUES (999999999);
SELECT 'TC-IA0058' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0058' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0059
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0059, t2_i0059;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0059 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0059 (target) VALUES (-.9);
INSERT INTO t1_i0059 (target) VALUES (.9);
INSERT INTO t1_i0059 (target) VALUES (0.0);
INSERT INTO t1_i0059 (target) VALUES (1.1);
INSERT INTO t1_i0059 (target) VALUES (-1.1);
INSERT INTO t1_i0059 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0059 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0059 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0059 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0059 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0059 (target) VALUES (-1.9);
INSERT INTO t1_i0059 (target) VALUES (0.0);
INSERT INTO t1_i0059 (target) VALUES (1.0);
INSERT INTO t1_i0059 (target) VALUES (.9);
INSERT INTO t1_i0059 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0059 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0059 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0059 (target) VALUES (-.9);
INSERT INTO t2_i0059 (target) VALUES (.9);
INSERT INTO t2_i0059 (target) VALUES (0.0);
INSERT INTO t2_i0059 (target) VALUES (1.1);
INSERT INTO t2_i0059 (target) VALUES (-1.1);
INSERT INTO t2_i0059 (target) VALUES (NULL);
INSERT INTO t2_i0059 (target) VALUES (9.9);
INSERT INTO t2_i0059 (target) VALUES (-9.9);
INSERT INTO t2_i0059 (target) VALUES (1.9);
INSERT INTO t2_i0059 (target) VALUES (-1.9);
INSERT INTO t2_i0059 (target) VALUES (0.0);
INSERT INTO t2_i0059 (target) VALUES (1.0);
INSERT INTO t2_i0059 (target) VALUES (.9);
INSERT INTO t2_i0059 (target) VALUES (NULL);
SELECT 'TC-I0059' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0059
   WHERE id NOT IN (SELECT id FROM t2_i0059)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0059
   WHERE id NOT IN (SELECT id FROM t1_i0059)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0059 a JOIN t2_i0059 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0060
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0060, t2_i0060;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0060 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0060 (target) VALUES (-.9);
INSERT INTO t1_i0060 (target) VALUES (.9);
INSERT INTO t1_i0060 (target) VALUES (0.0);
INSERT INTO t1_i0060 (target) VALUES (1.1);
INSERT INTO t1_i0060 (target) VALUES (-1.1);
INSERT INTO t1_i0060 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0060 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0060 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0060 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0060 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0060 (target) VALUES (-1.9);
INSERT INTO t1_i0060 (target) VALUES (0.0);
INSERT INTO t1_i0060 (target) VALUES (1.0);
INSERT INTO t1_i0060 (target) VALUES (.9);
INSERT INTO t1_i0060 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0060 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0060 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0060 (target) VALUES (-.9);
INSERT INTO t2_i0060 (target) VALUES (.9);
INSERT INTO t2_i0060 (target) VALUES (0.0);
INSERT INTO t2_i0060 (target) VALUES (1.1);
INSERT INTO t2_i0060 (target) VALUES (-1.1);
INSERT INTO t2_i0060 (target) VALUES (NULL);
INSERT INTO t2_i0060 (target) VALUES (9.9);
INSERT INTO t2_i0060 (target) VALUES (-9.9);
INSERT INTO t2_i0060 (target) VALUES (1.9);
INSERT INTO t2_i0060 (target) VALUES (-1.9);
INSERT INTO t2_i0060 (target) VALUES (0.0);
INSERT INTO t2_i0060 (target) VALUES (1.0);
INSERT INTO t2_i0060 (target) VALUES (.9);
INSERT INTO t2_i0060 (target) VALUES (NULL);
SELECT 'TC-I0060' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0060
   WHERE id NOT IN (SELECT id FROM t2_i0060)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0060
   WHERE id NOT IN (SELECT id FROM t1_i0060)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0060 a JOIN t2_i0060 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0061
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0061, t2_i0061;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0061 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0061 (target) VALUES (-.9);
INSERT INTO t1_i0061 (target) VALUES (.9);
INSERT INTO t1_i0061 (target) VALUES (0.0);
INSERT INTO t1_i0061 (target) VALUES (1.1);
INSERT INTO t1_i0061 (target) VALUES (-1.1);
INSERT INTO t1_i0061 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0061 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0061 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0061 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0061 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0061 (target) VALUES (-1.9);
INSERT INTO t1_i0061 (target) VALUES (0.0);
INSERT INTO t1_i0061 (target) VALUES (1.0);
INSERT INTO t1_i0061 (target) VALUES (.9);
INSERT INTO t1_i0061 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0061 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0061 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0061 (target) VALUES (-.9);
INSERT INTO t2_i0061 (target) VALUES (.9);
INSERT INTO t2_i0061 (target) VALUES (0.0);
INSERT INTO t2_i0061 (target) VALUES (1.1);
INSERT INTO t2_i0061 (target) VALUES (-1.1);
INSERT INTO t2_i0061 (target) VALUES (NULL);
INSERT INTO t2_i0061 (target) VALUES (9.9);
INSERT INTO t2_i0061 (target) VALUES (-9.9);
INSERT INTO t2_i0061 (target) VALUES (1.9);
INSERT INTO t2_i0061 (target) VALUES (-1.9);
INSERT INTO t2_i0061 (target) VALUES (0.0);
INSERT INTO t2_i0061 (target) VALUES (1.0);
INSERT INTO t2_i0061 (target) VALUES (.9);
INSERT INTO t2_i0061 (target) VALUES (NULL);
SELECT 'TC-I0061' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0061
   WHERE id NOT IN (SELECT id FROM t2_i0061)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0061
   WHERE id NOT IN (SELECT id FROM t1_i0061)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0061 a JOIN t2_i0061 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0062
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0062, t2_i0062;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0062 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0062 (target) VALUES (-.9);
INSERT INTO t1_i0062 (target) VALUES (.9);
INSERT INTO t1_i0062 (target) VALUES (0.0);
INSERT INTO t1_i0062 (target) VALUES (1.1);
INSERT INTO t1_i0062 (target) VALUES (-1.1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0062 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0062 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0062 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0062 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0062 (target) VALUES (-1.9);
INSERT INTO t1_i0062 (target) VALUES (0.0);
INSERT INTO t1_i0062 (target) VALUES (1.0);
INSERT INTO t1_i0062 (target) VALUES (.9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0062 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(1,1)
CREATE TABLE t2_i0062 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0062 (target) VALUES (-.9);
INSERT INTO t2_i0062 (target) VALUES (.9);
INSERT INTO t2_i0062 (target) VALUES (0.0);
INSERT INTO t2_i0062 (target) VALUES (1.1);
INSERT INTO t2_i0062 (target) VALUES (-1.1);
INSERT INTO t2_i0062 (target) VALUES (9.9);
INSERT INTO t2_i0062 (target) VALUES (-9.9);
INSERT INTO t2_i0062 (target) VALUES (1.9);
INSERT INTO t2_i0062 (target) VALUES (-1.9);
INSERT INTO t2_i0062 (target) VALUES (0.0);
INSERT INTO t2_i0062 (target) VALUES (1.0);
INSERT INTO t2_i0062 (target) VALUES (.9);
SELECT 'TC-I0062' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0062
   WHERE id NOT IN (SELECT id FROM t2_i0062)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0062
   WHERE id NOT IN (SELECT id FROM t1_i0062)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0062 a JOIN t2_i0062 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0063
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0063, t2_i0063;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0063 (target) VALUES (-.9);
INSERT INTO t1_i0063 (target) VALUES (.9);
INSERT INTO t1_i0063 (target) VALUES (0.0);
INSERT INTO t1_i0063 (target) VALUES (1.1);
INSERT INTO t1_i0063 (target) VALUES (-1.1);
INSERT INTO t1_i0063 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0063 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0063 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0063 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0063 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0063 (target) VALUES (-1.9);
INSERT INTO t1_i0063 (target) VALUES (0.0);
INSERT INTO t1_i0063 (target) VALUES (1.0);
INSERT INTO t1_i0063 (target) VALUES (.9);
INSERT INTO t1_i0063 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0063 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0063 (target) VALUES (-.9);
INSERT INTO t2_i0063 (target) VALUES (.9);
INSERT INTO t2_i0063 (target) VALUES (0.0);
INSERT INTO t2_i0063 (target) VALUES (1.1);
INSERT INTO t2_i0063 (target) VALUES (-1.1);
INSERT INTO t2_i0063 (target) VALUES (NULL);
INSERT INTO t2_i0063 (target) VALUES (9.9);
INSERT INTO t2_i0063 (target) VALUES (-9.9);
INSERT INTO t2_i0063 (target) VALUES (1.9);
INSERT INTO t2_i0063 (target) VALUES (-1.9);
INSERT INTO t2_i0063 (target) VALUES (0.0);
INSERT INTO t2_i0063 (target) VALUES (1.0);
INSERT INTO t2_i0063 (target) VALUES (.9);
INSERT INTO t2_i0063 (target) VALUES (NULL);
SELECT 'TC-I0063' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0063
   WHERE id NOT IN (SELECT id FROM t2_i0063)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0063
   WHERE id NOT IN (SELECT id FROM t1_i0063)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0063 a JOIN t2_i0063 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0064
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0064, t2_i0064;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0064 (target) VALUES (-.9);
INSERT INTO t1_i0064 (target) VALUES (.9);
INSERT INTO t1_i0064 (target) VALUES (0.0);
INSERT INTO t1_i0064 (target) VALUES (1.1);
INSERT INTO t1_i0064 (target) VALUES (-1.1);
INSERT INTO t1_i0064 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0064 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0064 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0064 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0064 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0064 (target) VALUES (-1.9);
INSERT INTO t1_i0064 (target) VALUES (0.0);
INSERT INTO t1_i0064 (target) VALUES (1.0);
INSERT INTO t1_i0064 (target) VALUES (.9);
INSERT INTO t1_i0064 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0064 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0064 (target) VALUES (-.9);
INSERT INTO t2_i0064 (target) VALUES (.9);
INSERT INTO t2_i0064 (target) VALUES (0.0);
INSERT INTO t2_i0064 (target) VALUES (1.1);
INSERT INTO t2_i0064 (target) VALUES (-1.1);
INSERT INTO t2_i0064 (target) VALUES (NULL);
INSERT INTO t2_i0064 (target) VALUES (9.9);
INSERT INTO t2_i0064 (target) VALUES (-9.9);
INSERT INTO t2_i0064 (target) VALUES (1.9);
INSERT INTO t2_i0064 (target) VALUES (-1.9);
INSERT INTO t2_i0064 (target) VALUES (0.0);
INSERT INTO t2_i0064 (target) VALUES (1.0);
INSERT INTO t2_i0064 (target) VALUES (.9);
INSERT INTO t2_i0064 (target) VALUES (NULL);
SELECT 'TC-I0064' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0064
   WHERE id NOT IN (SELECT id FROM t2_i0064)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0064
   WHERE id NOT IN (SELECT id FROM t1_i0064)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0064 a JOIN t2_i0064 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0065
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0065, t2_i0065;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0065 (target) VALUES (-.9);
INSERT INTO t1_i0065 (target) VALUES (.9);
INSERT INTO t1_i0065 (target) VALUES (0.0);
INSERT INTO t1_i0065 (target) VALUES (1.1);
INSERT INTO t1_i0065 (target) VALUES (-1.1);
INSERT INTO t1_i0065 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0065 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0065 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0065 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0065 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0065 (target) VALUES (-1.9);
INSERT INTO t1_i0065 (target) VALUES (0.0);
INSERT INTO t1_i0065 (target) VALUES (1.0);
INSERT INTO t1_i0065 (target) VALUES (.9);
INSERT INTO t1_i0065 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0065 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0065 (target) VALUES (-.9);
INSERT INTO t2_i0065 (target) VALUES (.9);
INSERT INTO t2_i0065 (target) VALUES (0.0);
INSERT INTO t2_i0065 (target) VALUES (1.1);
INSERT INTO t2_i0065 (target) VALUES (-1.1);
INSERT INTO t2_i0065 (target) VALUES (NULL);
INSERT INTO t2_i0065 (target) VALUES (9.9);
INSERT INTO t2_i0065 (target) VALUES (-9.9);
INSERT INTO t2_i0065 (target) VALUES (1.9);
INSERT INTO t2_i0065 (target) VALUES (-1.9);
INSERT INTO t2_i0065 (target) VALUES (0.0);
INSERT INTO t2_i0065 (target) VALUES (1.0);
INSERT INTO t2_i0065 (target) VALUES (.9);
INSERT INTO t2_i0065 (target) VALUES (NULL);
SELECT 'TC-I0065' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0065
   WHERE id NOT IN (SELECT id FROM t2_i0065)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0065
   WHERE id NOT IN (SELECT id FROM t1_i0065)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0065 a JOIN t2_i0065 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0066
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0066, t2_i0066;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0066 (target) VALUES (-.9);
INSERT INTO t1_i0066 (target) VALUES (.9);
INSERT INTO t1_i0066 (target) VALUES (0.0);
INSERT INTO t1_i0066 (target) VALUES (1.1);
INSERT INTO t1_i0066 (target) VALUES (-1.1);
INSERT INTO t1_i0066 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0066 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0066 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0066 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0066 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0066 (target) VALUES (-1.9);
INSERT INTO t1_i0066 (target) VALUES (0.0);
INSERT INTO t1_i0066 (target) VALUES (1.0);
INSERT INTO t1_i0066 (target) VALUES (.9);
INSERT INTO t1_i0066 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0066 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0066 (target) VALUES (-.9);
INSERT INTO t2_i0066 (target) VALUES (.9);
INSERT INTO t2_i0066 (target) VALUES (0.0);
INSERT INTO t2_i0066 (target) VALUES (1.1);
INSERT INTO t2_i0066 (target) VALUES (-1.1);
INSERT INTO t2_i0066 (target) VALUES (NULL);
INSERT INTO t2_i0066 (target) VALUES (9.9);
INSERT INTO t2_i0066 (target) VALUES (-9.9);
INSERT INTO t2_i0066 (target) VALUES (1.9);
INSERT INTO t2_i0066 (target) VALUES (-1.9);
INSERT INTO t2_i0066 (target) VALUES (0.0);
INSERT INTO t2_i0066 (target) VALUES (1.0);
INSERT INTO t2_i0066 (target) VALUES (.9);
INSERT INTO t2_i0066 (target) VALUES (NULL);
SELECT 'TC-I0066' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0066
   WHERE id NOT IN (SELECT id FROM t2_i0066)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0066
   WHERE id NOT IN (SELECT id FROM t1_i0066)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0066 a JOIN t2_i0066 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0067
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0067, t2_i0067;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0067 (target) VALUES (-.9);
INSERT INTO t1_i0067 (target) VALUES (.9);
INSERT INTO t1_i0067 (target) VALUES (0.0);
INSERT INTO t1_i0067 (target) VALUES (1.1);
INSERT INTO t1_i0067 (target) VALUES (-1.1);
INSERT INTO t1_i0067 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0067 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0067 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0067 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0067 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0067 (target) VALUES (-1.9);
INSERT INTO t1_i0067 (target) VALUES (0.0);
INSERT INTO t1_i0067 (target) VALUES (1.0);
INSERT INTO t1_i0067 (target) VALUES (.9);
INSERT INTO t1_i0067 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0067 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0067 (target) VALUES (-.9);
INSERT INTO t2_i0067 (target) VALUES (.9);
INSERT INTO t2_i0067 (target) VALUES (0.0);
INSERT INTO t2_i0067 (target) VALUES (1.1);
INSERT INTO t2_i0067 (target) VALUES (-1.1);
INSERT INTO t2_i0067 (target) VALUES (NULL);
INSERT INTO t2_i0067 (target) VALUES (9.9);
INSERT INTO t2_i0067 (target) VALUES (-9.9);
INSERT INTO t2_i0067 (target) VALUES (1.9);
INSERT INTO t2_i0067 (target) VALUES (-1.9);
INSERT INTO t2_i0067 (target) VALUES (0.0);
INSERT INTO t2_i0067 (target) VALUES (1.0);
INSERT INTO t2_i0067 (target) VALUES (.9);
INSERT INTO t2_i0067 (target) VALUES (NULL);
SELECT 'TC-I0067' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0067
   WHERE id NOT IN (SELECT id FROM t2_i0067)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0067
   WHERE id NOT IN (SELECT id FROM t1_i0067)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0067 a JOIN t2_i0067 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0068
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0068, t2_i0068;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0068 (
  target DECIMAL(1,1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0068 (target) VALUES (-.9);
INSERT INTO t1_i0068 (target) VALUES (.9);
INSERT INTO t1_i0068 (target) VALUES (0.0);
INSERT INTO t1_i0068 (target) VALUES (1.1);
INSERT INTO t1_i0068 (target) VALUES (-1.1);
INSERT INTO t1_i0068 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0068 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0068 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0068 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0068 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0068 (target) VALUES (-1.9);
INSERT INTO t1_i0068 (target) VALUES (0.0);
INSERT INTO t1_i0068 (target) VALUES (1.0);
INSERT INTO t1_i0068 (target) VALUES (.9);
INSERT INTO t1_i0068 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0068 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0068 (
  target DECIMAL(2,1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0068 (target) VALUES (-.9);
INSERT INTO t2_i0068 (target) VALUES (.9);
INSERT INTO t2_i0068 (target) VALUES (0.0);
INSERT INTO t2_i0068 (target) VALUES (1.1);
INSERT INTO t2_i0068 (target) VALUES (-1.1);
INSERT INTO t2_i0068 (target) VALUES (NULL);
INSERT INTO t2_i0068 (target) VALUES (9.9);
INSERT INTO t2_i0068 (target) VALUES (-9.9);
INSERT INTO t2_i0068 (target) VALUES (1.9);
INSERT INTO t2_i0068 (target) VALUES (-1.9);
INSERT INTO t2_i0068 (target) VALUES (0.0);
INSERT INTO t2_i0068 (target) VALUES (1.0);
INSERT INTO t2_i0068 (target) VALUES (.9);
INSERT INTO t2_i0068 (target) VALUES (NULL);
SELECT 'TC-I0068' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0068
   WHERE id NOT IN (SELECT id FROM t2_i0068)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0068
   WHERE id NOT IN (SELECT id FROM t1_i0068)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0068 a JOIN t2_i0068 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0069
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0069, t2_i0069;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(1,1), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0069 (target) VALUES (-.9);
INSERT INTO t1_i0069 (target) VALUES (.9);
INSERT INTO t1_i0069 (target) VALUES (0.0);
INSERT INTO t1_i0069 (target) VALUES (1.1);
INSERT INTO t1_i0069 (target) VALUES (-1.1);
INSERT INTO t1_i0069 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0069 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0069 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0069 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0069 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0069 (target) VALUES (-1.9);
INSERT INTO t1_i0069 (target) VALUES (0.0);
INSERT INTO t1_i0069 (target) VALUES (1.0);
INSERT INTO t1_i0069 (target) VALUES (.9);
INSERT INTO t1_i0069 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0069 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(2,1), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0069 (target) VALUES (-.9);
INSERT INTO t2_i0069 (target) VALUES (.9);
INSERT INTO t2_i0069 (target) VALUES (0.0);
INSERT INTO t2_i0069 (target) VALUES (1.1);
INSERT INTO t2_i0069 (target) VALUES (-1.1);
INSERT INTO t2_i0069 (target) VALUES (NULL);
INSERT INTO t2_i0069 (target) VALUES (9.9);
INSERT INTO t2_i0069 (target) VALUES (-9.9);
INSERT INTO t2_i0069 (target) VALUES (1.9);
INSERT INTO t2_i0069 (target) VALUES (-1.9);
INSERT INTO t2_i0069 (target) VALUES (0.0);
INSERT INTO t2_i0069 (target) VALUES (1.0);
INSERT INTO t2_i0069 (target) VALUES (.9);
INSERT INTO t2_i0069 (target) VALUES (NULL);
SELECT 'TC-I0069' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0069
   WHERE id NOT IN (SELECT id FROM t2_i0069)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0069
   WHERE id NOT IN (SELECT id FROM t1_i0069)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0069 a JOIN t2_i0069 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0070
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0070, t2_i0070;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0070 (target) VALUES (-.9);
INSERT INTO t1_i0070 (target) VALUES (.9);
INSERT INTO t1_i0070 (target) VALUES (0.0);
INSERT INTO t1_i0070 (target) VALUES (1.1);
INSERT INTO t1_i0070 (target) VALUES (-1.1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0070 MODIFY target DECIMAL(2,1) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0070 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0070 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0070 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0070 (target) VALUES (-1.9);
INSERT INTO t1_i0070 (target) VALUES (0.0);
INSERT INTO t1_i0070 (target) VALUES (1.0);
INSERT INTO t1_i0070 (target) VALUES (.9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0070 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0070 (target) VALUES (-.9);
INSERT INTO t2_i0070 (target) VALUES (.9);
INSERT INTO t2_i0070 (target) VALUES (0.0);
INSERT INTO t2_i0070 (target) VALUES (1.1);
INSERT INTO t2_i0070 (target) VALUES (-1.1);
INSERT INTO t2_i0070 (target) VALUES (9.9);
INSERT INTO t2_i0070 (target) VALUES (-9.9);
INSERT INTO t2_i0070 (target) VALUES (1.9);
INSERT INTO t2_i0070 (target) VALUES (-1.9);
INSERT INTO t2_i0070 (target) VALUES (0.0);
INSERT INTO t2_i0070 (target) VALUES (1.0);
INSERT INTO t2_i0070 (target) VALUES (.9);
SELECT 'TC-I0070' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0070
   WHERE id NOT IN (SELECT id FROM t2_i0070)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0070
   WHERE id NOT IN (SELECT id FROM t1_i0070)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0070 a JOIN t2_i0070 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0071
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0071, t2_i0071;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0071 (target) VALUES (-.9);
INSERT INTO t1_i0071 (target) VALUES (.9);
INSERT INTO t1_i0071 (target) VALUES (0.0);
INSERT INTO t1_i0071 (target) VALUES (1.1);
INSERT INTO t1_i0071 (target) VALUES (-1.1);
INSERT INTO t1_i0071 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0071 MODIFY target DECIMAL(2,1) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0071 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0071 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0071 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0071 (target) VALUES (-1.9);
INSERT INTO t1_i0071 (target) VALUES (0.0);
INSERT INTO t1_i0071 (target) VALUES (1.0);
INSERT INTO t1_i0071 (target) VALUES (.9);
INSERT INTO t1_i0071 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0071 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0071 (target) VALUES (-.9);
INSERT INTO t2_i0071 (target) VALUES (.9);
INSERT INTO t2_i0071 (target) VALUES (0.0);
INSERT INTO t2_i0071 (target) VALUES (1.1);
INSERT INTO t2_i0071 (target) VALUES (-1.1);
INSERT INTO t2_i0071 (target) VALUES (NULL);
INSERT INTO t2_i0071 (target) VALUES (9.9);
INSERT INTO t2_i0071 (target) VALUES (-9.9);
INSERT INTO t2_i0071 (target) VALUES (1.9);
INSERT INTO t2_i0071 (target) VALUES (-1.9);
INSERT INTO t2_i0071 (target) VALUES (0.0);
INSERT INTO t2_i0071 (target) VALUES (1.0);
INSERT INTO t2_i0071 (target) VALUES (.9);
INSERT INTO t2_i0071 (target) VALUES (NULL);
SELECT 'TC-I0071' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0071
   WHERE id NOT IN (SELECT id FROM t2_i0071)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0071
   WHERE id NOT IN (SELECT id FROM t1_i0071)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0071 a JOIN t2_i0071 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0072
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0072, t2_i0072;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0072 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0072 (target) VALUES (-.9);
INSERT INTO t1_i0072 (target) VALUES (.9);
INSERT INTO t1_i0072 (target) VALUES (0.0);
INSERT INTO t1_i0072 (target) VALUES (1.1);
INSERT INTO t1_i0072 (target) VALUES (-1.1);
INSERT INTO t1_i0072 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0072 MODIFY target DECIMAL(2,1) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0072 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0072 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0072 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0072 (target) VALUES (-1.9);
INSERT INTO t1_i0072 (target) VALUES (0.0);
INSERT INTO t1_i0072 (target) VALUES (1.0);
INSERT INTO t1_i0072 (target) VALUES (.9);
INSERT INTO t1_i0072 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0072 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0072 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0072 (target) VALUES (-.9);
INSERT INTO t2_i0072 (target) VALUES (.9);
INSERT INTO t2_i0072 (target) VALUES (0.0);
INSERT INTO t2_i0072 (target) VALUES (1.1);
INSERT INTO t2_i0072 (target) VALUES (-1.1);
INSERT INTO t2_i0072 (target) VALUES (NULL);
INSERT INTO t2_i0072 (target) VALUES (9.9);
INSERT INTO t2_i0072 (target) VALUES (-9.9);
INSERT INTO t2_i0072 (target) VALUES (1.9);
INSERT INTO t2_i0072 (target) VALUES (-1.9);
INSERT INTO t2_i0072 (target) VALUES (0.0);
INSERT INTO t2_i0072 (target) VALUES (1.0);
INSERT INTO t2_i0072 (target) VALUES (.9);
INSERT INTO t2_i0072 (target) VALUES (NULL);
SELECT 'TC-I0072' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0072
   WHERE id NOT IN (SELECT id FROM t2_i0072)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0072
   WHERE id NOT IN (SELECT id FROM t1_i0072)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0072 a JOIN t2_i0072 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0073
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0073, t2_i0073;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0073 (target) VALUES (-.9);
INSERT INTO t1_i0073 (target) VALUES (.9);
INSERT INTO t1_i0073 (target) VALUES (0.0);
INSERT INTO t1_i0073 (target) VALUES (1.1);
INSERT INTO t1_i0073 (target) VALUES (-1.1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0073 MODIFY target DECIMAL(2,1) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0073 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0073 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0073 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0073 (target) VALUES (-1.9);
INSERT INTO t1_i0073 (target) VALUES (0.0);
INSERT INTO t1_i0073 (target) VALUES (1.0);
INSERT INTO t1_i0073 (target) VALUES (.9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0073 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0073 (target) VALUES (-.9);
INSERT INTO t2_i0073 (target) VALUES (.9);
INSERT INTO t2_i0073 (target) VALUES (0.0);
INSERT INTO t2_i0073 (target) VALUES (1.1);
INSERT INTO t2_i0073 (target) VALUES (-1.1);
INSERT INTO t2_i0073 (target) VALUES (9.9);
INSERT INTO t2_i0073 (target) VALUES (-9.9);
INSERT INTO t2_i0073 (target) VALUES (1.9);
INSERT INTO t2_i0073 (target) VALUES (-1.9);
INSERT INTO t2_i0073 (target) VALUES (0.0);
INSERT INTO t2_i0073 (target) VALUES (1.0);
INSERT INTO t2_i0073 (target) VALUES (.9);
SELECT 'TC-I0073' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0073
   WHERE id NOT IN (SELECT id FROM t2_i0073)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0073
   WHERE id NOT IN (SELECT id FROM t1_i0073)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0073 a JOIN t2_i0073 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0074
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0074, t2_i0074;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0074 (target) VALUES (-.9);
INSERT INTO t1_i0074 (target) VALUES (.9);
INSERT INTO t1_i0074 (target) VALUES (0.0);
INSERT INTO t1_i0074 (target) VALUES (1.1);
INSERT INTO t1_i0074 (target) VALUES (-1.1);
INSERT INTO t1_i0074 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0074 MODIFY target DECIMAL(2,1) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0074 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0074 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0074 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0074 (target) VALUES (-1.9);
INSERT INTO t1_i0074 (target) VALUES (0.0);
INSERT INTO t1_i0074 (target) VALUES (1.0);
INSERT INTO t1_i0074 (target) VALUES (.9);
INSERT INTO t1_i0074 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0074 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0074 (target) VALUES (-.9);
INSERT INTO t2_i0074 (target) VALUES (.9);
INSERT INTO t2_i0074 (target) VALUES (0.0);
INSERT INTO t2_i0074 (target) VALUES (1.1);
INSERT INTO t2_i0074 (target) VALUES (-1.1);
INSERT INTO t2_i0074 (target) VALUES (NULL);
INSERT INTO t2_i0074 (target) VALUES (9.9);
INSERT INTO t2_i0074 (target) VALUES (-9.9);
INSERT INTO t2_i0074 (target) VALUES (1.9);
INSERT INTO t2_i0074 (target) VALUES (-1.9);
INSERT INTO t2_i0074 (target) VALUES (0.0);
INSERT INTO t2_i0074 (target) VALUES (1.0);
INSERT INTO t2_i0074 (target) VALUES (.9);
INSERT INTO t2_i0074 (target) VALUES (NULL);
SELECT 'TC-I0074' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0074
   WHERE id NOT IN (SELECT id FROM t2_i0074)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0074
   WHERE id NOT IN (SELECT id FROM t1_i0074)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0074 a JOIN t2_i0074 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0075
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0075, t2_i0075;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0075 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0075 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0075' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0075
   WHERE id NOT IN (SELECT id FROM t2_i0075)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0075
   WHERE id NOT IN (SELECT id FROM t1_i0075)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0075 a JOIN t2_i0075 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0076
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0076, t2_i0076;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0076 (target) VALUES (-.9);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0076 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0076 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0076 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0076 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0076 (target) VALUES (-1.9);
INSERT INTO t1_i0076 (target) VALUES (0.0);
INSERT INTO t1_i0076 (target) VALUES (1.0);
INSERT INTO t1_i0076 (target) VALUES (.9);
INSERT INTO t1_i0076 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0076 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0076 (target) VALUES (-.9);
INSERT INTO t2_i0076 (target) VALUES (9.9);
INSERT INTO t2_i0076 (target) VALUES (-9.9);
INSERT INTO t2_i0076 (target) VALUES (1.9);
INSERT INTO t2_i0076 (target) VALUES (-1.9);
INSERT INTO t2_i0076 (target) VALUES (0.0);
INSERT INTO t2_i0076 (target) VALUES (1.0);
INSERT INTO t2_i0076 (target) VALUES (.9);
INSERT INTO t2_i0076 (target) VALUES (NULL);
SELECT 'TC-I0076' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0076
   WHERE id NOT IN (SELECT id FROM t2_i0076)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0076
   WHERE id NOT IN (SELECT id FROM t1_i0076)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0076 a JOIN t2_i0076 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0077
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0077, t2_i0077;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0077 (target) VALUES (-.9);
INSERT INTO t1_i0077 (target) VALUES (.9);
INSERT INTO t1_i0077 (target) VALUES (0.0);
INSERT INTO t1_i0077 (target) VALUES (1.1);
INSERT INTO t1_i0077 (target) VALUES (-1.1);
INSERT INTO t1_i0077 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0077 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0077 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0077 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0077 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0077 (target) VALUES (-1.9);
INSERT INTO t1_i0077 (target) VALUES (0.0);
INSERT INTO t1_i0077 (target) VALUES (1.0);
INSERT INTO t1_i0077 (target) VALUES (.9);
INSERT INTO t1_i0077 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0077 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0077 (target) VALUES (-.9);
INSERT INTO t2_i0077 (target) VALUES (.9);
INSERT INTO t2_i0077 (target) VALUES (0.0);
INSERT INTO t2_i0077 (target) VALUES (1.1);
INSERT INTO t2_i0077 (target) VALUES (-1.1);
INSERT INTO t2_i0077 (target) VALUES (NULL);
INSERT INTO t2_i0077 (target) VALUES (9.9);
INSERT INTO t2_i0077 (target) VALUES (-9.9);
INSERT INTO t2_i0077 (target) VALUES (1.9);
INSERT INTO t2_i0077 (target) VALUES (-1.9);
INSERT INTO t2_i0077 (target) VALUES (0.0);
INSERT INTO t2_i0077 (target) VALUES (1.0);
INSERT INTO t2_i0077 (target) VALUES (.9);
INSERT INTO t2_i0077 (target) VALUES (NULL);
SELECT 'TC-I0077' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0077
   WHERE id NOT IN (SELECT id FROM t2_i0077)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0077
   WHERE id NOT IN (SELECT id FROM t1_i0077)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0077 a JOIN t2_i0077 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0078
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0078, t2_i0078;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0078 (target) VALUES (-.9);
INSERT INTO t1_i0078 (target) VALUES (.9);
INSERT INTO t1_i0078 (target) VALUES (0.0);
INSERT INTO t1_i0078 (target) VALUES (1.1);
INSERT INTO t1_i0078 (target) VALUES (-1.1);
INSERT INTO t1_i0078 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0078 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0078 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0078 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0078 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0078 (target) VALUES (-1.9);
INSERT INTO t1_i0078 (target) VALUES (0.0);
INSERT INTO t1_i0078 (target) VALUES (1.0);
INSERT INTO t1_i0078 (target) VALUES (.9);
INSERT INTO t1_i0078 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0078 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0078 (target) VALUES (-.9);
INSERT INTO t2_i0078 (target) VALUES (.9);
INSERT INTO t2_i0078 (target) VALUES (0.0);
INSERT INTO t2_i0078 (target) VALUES (1.1);
INSERT INTO t2_i0078 (target) VALUES (-1.1);
INSERT INTO t2_i0078 (target) VALUES (NULL);
INSERT INTO t2_i0078 (target) VALUES (9.9);
INSERT INTO t2_i0078 (target) VALUES (-9.9);
INSERT INTO t2_i0078 (target) VALUES (1.9);
INSERT INTO t2_i0078 (target) VALUES (-1.9);
INSERT INTO t2_i0078 (target) VALUES (0.0);
INSERT INTO t2_i0078 (target) VALUES (1.0);
INSERT INTO t2_i0078 (target) VALUES (.9);
INSERT INTO t2_i0078 (target) VALUES (NULL);
SELECT 'TC-I0078' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0078
   WHERE id NOT IN (SELECT id FROM t2_i0078)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0078
   WHERE id NOT IN (SELECT id FROM t1_i0078)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0078 a JOIN t2_i0078 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0079
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0079, t2_i0079;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0079 (target) VALUES (-.9);
INSERT INTO t1_i0079 (target) VALUES (.9);
INSERT INTO t1_i0079 (target) VALUES (0.0);
INSERT INTO t1_i0079 (target) VALUES (1.1);
INSERT INTO t1_i0079 (target) VALUES (-1.1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0079 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0079 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0079 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0079 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0079 (target) VALUES (-1.9);
INSERT INTO t1_i0079 (target) VALUES (0.0);
INSERT INTO t1_i0079 (target) VALUES (1.0);
INSERT INTO t1_i0079 (target) VALUES (.9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0079 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0079 (target) VALUES (-.9);
INSERT INTO t2_i0079 (target) VALUES (.9);
INSERT INTO t2_i0079 (target) VALUES (0.0);
INSERT INTO t2_i0079 (target) VALUES (1.1);
INSERT INTO t2_i0079 (target) VALUES (-1.1);
INSERT INTO t2_i0079 (target) VALUES (9.9);
INSERT INTO t2_i0079 (target) VALUES (-9.9);
INSERT INTO t2_i0079 (target) VALUES (1.9);
INSERT INTO t2_i0079 (target) VALUES (-1.9);
INSERT INTO t2_i0079 (target) VALUES (0.0);
INSERT INTO t2_i0079 (target) VALUES (1.0);
INSERT INTO t2_i0079 (target) VALUES (.9);
SELECT 'TC-I0079' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0079
   WHERE id NOT IN (SELECT id FROM t2_i0079)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0079
   WHERE id NOT IN (SELECT id FROM t1_i0079)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0079 a JOIN t2_i0079 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0080
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0080, t2_i0080;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0080 (target) VALUES (-.9);
INSERT INTO t1_i0080 (target) VALUES (.9);
INSERT INTO t1_i0080 (target) VALUES (0.0);
INSERT INTO t1_i0080 (target) VALUES (1.1);
INSERT INTO t1_i0080 (target) VALUES (-1.1);
INSERT INTO t1_i0080 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0080 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0080 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0080 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0080 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0080 (target) VALUES (-1.9);
INSERT INTO t1_i0080 (target) VALUES (0.0);
INSERT INTO t1_i0080 (target) VALUES (1.0);
INSERT INTO t1_i0080 (target) VALUES (.9);
INSERT INTO t1_i0080 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0080 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0080 (target) VALUES (-.9);
INSERT INTO t2_i0080 (target) VALUES (.9);
INSERT INTO t2_i0080 (target) VALUES (0.0);
INSERT INTO t2_i0080 (target) VALUES (1.1);
INSERT INTO t2_i0080 (target) VALUES (-1.1);
INSERT INTO t2_i0080 (target) VALUES (NULL);
INSERT INTO t2_i0080 (target) VALUES (9.9);
INSERT INTO t2_i0080 (target) VALUES (-9.9);
INSERT INTO t2_i0080 (target) VALUES (1.9);
INSERT INTO t2_i0080 (target) VALUES (-1.9);
INSERT INTO t2_i0080 (target) VALUES (0.0);
INSERT INTO t2_i0080 (target) VALUES (1.0);
INSERT INTO t2_i0080 (target) VALUES (.9);
INSERT INTO t2_i0080 (target) VALUES (NULL);
SELECT 'TC-I0080' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0080
   WHERE id NOT IN (SELECT id FROM t2_i0080)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0080
   WHERE id NOT IN (SELECT id FROM t1_i0080)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0080 a JOIN t2_i0080 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0081
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0081, t2_i0081;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0081 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0081 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0081 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0081 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0081 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0081 (target) VALUES (-1.9);
INSERT INTO t1_i0081 (target) VALUES (0.0);
INSERT INTO t1_i0081 (target) VALUES (1.0);
INSERT INTO t1_i0081 (target) VALUES (.9);
INSERT INTO t1_i0081 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0081 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0081 (target) VALUES (NULL);
INSERT INTO t2_i0081 (target) VALUES (9.9);
INSERT INTO t2_i0081 (target) VALUES (-9.9);
INSERT INTO t2_i0081 (target) VALUES (1.9);
INSERT INTO t2_i0081 (target) VALUES (-1.9);
INSERT INTO t2_i0081 (target) VALUES (0.0);
INSERT INTO t2_i0081 (target) VALUES (1.0);
INSERT INTO t2_i0081 (target) VALUES (.9);
INSERT INTO t2_i0081 (target) VALUES (NULL);
SELECT 'TC-I0081' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0081
   WHERE id NOT IN (SELECT id FROM t2_i0081)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0081
   WHERE id NOT IN (SELECT id FROM t1_i0081)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0081 a JOIN t2_i0081 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0082
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0082, t2_i0082;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0082 (target) VALUES (-.9);
INSERT INTO t1_i0082 (target) VALUES (.9);
INSERT INTO t1_i0082 (target) VALUES (0.0);
INSERT INTO t1_i0082 (target) VALUES (1.1);
INSERT INTO t1_i0082 (target) VALUES (-1.1);
INSERT INTO t1_i0082 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0082 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0082 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0082 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0082 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0082 (target) VALUES (-1.9);
INSERT INTO t1_i0082 (target) VALUES (0.0);
INSERT INTO t1_i0082 (target) VALUES (1.0);
INSERT INTO t1_i0082 (target) VALUES (.9);
INSERT INTO t1_i0082 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0082 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0082 (target) VALUES (-.9);
INSERT INTO t2_i0082 (target) VALUES (.9);
INSERT INTO t2_i0082 (target) VALUES (0.0);
INSERT INTO t2_i0082 (target) VALUES (1.1);
INSERT INTO t2_i0082 (target) VALUES (-1.1);
INSERT INTO t2_i0082 (target) VALUES (NULL);
INSERT INTO t2_i0082 (target) VALUES (9.9);
INSERT INTO t2_i0082 (target) VALUES (-9.9);
INSERT INTO t2_i0082 (target) VALUES (1.9);
INSERT INTO t2_i0082 (target) VALUES (-1.9);
INSERT INTO t2_i0082 (target) VALUES (0.0);
INSERT INTO t2_i0082 (target) VALUES (1.0);
INSERT INTO t2_i0082 (target) VALUES (.9);
INSERT INTO t2_i0082 (target) VALUES (NULL);
SELECT 'TC-I0082' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0082
   WHERE id NOT IN (SELECT id FROM t2_i0082)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0082
   WHERE id NOT IN (SELECT id FROM t1_i0082)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0082 a JOIN t2_i0082 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0083
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0083, t2_i0083;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0083 MODIFY target DECIMAL(2,1) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0083 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0083' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0083
   WHERE id NOT IN (SELECT id FROM t2_i0083)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0083
   WHERE id NOT IN (SELECT id FROM t1_i0083)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0083 a JOIN t2_i0083 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0084
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0084, t2_i0084;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0084 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0084 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0084' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0084
   WHERE id NOT IN (SELECT id FROM t2_i0084)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0084
   WHERE id NOT IN (SELECT id FROM t1_i0084)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0084 a JOIN t2_i0084 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0085
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0085, t2_i0085;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(1,1) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0085 MODIFY target DECIMAL(2,1) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0085 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(2,1)
CREATE TABLE t2_i0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(2,1) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0085' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0085
   WHERE id NOT IN (SELECT id FROM t2_i0085)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0085
   WHERE id NOT IN (SELECT id FROM t1_i0085)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0085 a JOIN t2_i0085 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0086
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0086, t2_i0086;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0086 (
  target DECIMAL(1,1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0086 (target) VALUES (-.9);
INSERT INTO t1_i0086 (target) VALUES (.9);
INSERT INTO t1_i0086 (target) VALUES (0.0);
INSERT INTO t1_i0086 (target) VALUES (1.1);
INSERT INTO t1_i0086 (target) VALUES (-1.1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0086 MODIFY target DECIMAL(2,1), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0086 (target) VALUES (9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0086 (target) VALUES (-9.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0086 (target) VALUES (1.9);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0086 (target) VALUES (-1.9);
INSERT INTO t1_i0086 (target) VALUES (0.0);
INSERT INTO t1_i0086 (target) VALUES (1.0);
INSERT INTO t1_i0086 (target) VALUES (.9);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0086 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(1,1)
CREATE TABLE t2_i0086 (
  target DECIMAL(1,1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0086 (target) VALUES (-.9);
INSERT INTO t2_i0086 (target) VALUES (.9);
INSERT INTO t2_i0086 (target) VALUES (0.0);
INSERT INTO t2_i0086 (target) VALUES (1.1);
INSERT INTO t2_i0086 (target) VALUES (-1.1);
INSERT INTO t2_i0086 (target) VALUES (9.9);
INSERT INTO t2_i0086 (target) VALUES (-9.9);
INSERT INTO t2_i0086 (target) VALUES (1.9);
INSERT INTO t2_i0086 (target) VALUES (-1.9);
INSERT INTO t2_i0086 (target) VALUES (0.0);
INSERT INTO t2_i0086 (target) VALUES (1.0);
INSERT INTO t2_i0086 (target) VALUES (.9);
SELECT 'TC-I0086' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0086
   WHERE id NOT IN (SELECT id FROM t2_i0086)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0086
   WHERE id NOT IN (SELECT id FROM t1_i0086)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0086 a JOIN t2_i0086 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0087
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(1,1) -> DECIMAL(2,1), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0087, t2_tc_ia0087;
CREATE TABLE t1_tc_ia0087 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(1,1) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0087 (target) VALUES (-.9);
INSERT INTO t1_tc_ia0087 (target) VALUES (.9);
INSERT INTO t1_tc_ia0087 (target) VALUES (0.0);
INSERT INTO t1_tc_ia0087 (target) VALUES (1.1);
INSERT INTO t1_tc_ia0087 (target) VALUES (-1.1);
ALTER TABLE t1_tc_ia0087 MODIFY target DECIMAL(2,1) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0087 (target) VALUES (9.9);
INSERT INTO t1_tc_ia0087 (target) VALUES (-9.9);
INSERT INTO t1_tc_ia0087 (target) VALUES (1.9);
SELECT 'TC-IA0087' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0087' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0088
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0088, t2_i0088;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0088 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0088 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0088 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0088 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0088 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0088 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0088 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0088 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0088 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0088 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0088 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0088 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0088 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0088 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0088 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0088 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0088 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0088 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0088 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0088 (target) VALUES (NULL);
INSERT INTO t2_i0088 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0088 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0088 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0088 (target) VALUES (NULL);
SELECT 'TC-I0088' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0088
   WHERE id NOT IN (SELECT id FROM t2_i0088)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0088
   WHERE id NOT IN (SELECT id FROM t1_i0088)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0088 a JOIN t2_i0088 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0089
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0089, t2_i0089;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0089 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0089 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0089 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0089 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0089 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0089 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0089 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0089 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0089 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0089 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0089 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0089 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0089 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0089 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0089 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0089 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0089 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0089 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0089 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0089 (target) VALUES (NULL);
INSERT INTO t2_i0089 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0089 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0089 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0089 (target) VALUES (NULL);
SELECT 'TC-I0089' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0089
   WHERE id NOT IN (SELECT id FROM t2_i0089)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0089
   WHERE id NOT IN (SELECT id FROM t1_i0089)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0089 a JOIN t2_i0089 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0090
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0090, t2_i0090;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0090 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0090 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0090 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0090 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0090 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0090 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0090 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0090 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0090 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0090 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0090 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0090 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0090 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0090 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0090 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0090 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0090 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0090 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0090 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0090 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0090 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0090 (target) VALUES (NULL);
INSERT INTO t2_i0090 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0090 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0090 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0090 (target) VALUES (NULL);
SELECT 'TC-I0090' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0090
   WHERE id NOT IN (SELECT id FROM t2_i0090)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0090
   WHERE id NOT IN (SELECT id FROM t1_i0090)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0090 a JOIN t2_i0090 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0091
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0091, t2_i0091;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0091 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0091 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0091 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0091 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0091 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0091 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0091 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0091 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0091 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0091 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0091 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0091 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0091 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0091 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0091 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(64,30)
CREATE TABLE t2_i0091 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0091 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0091 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0091 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0091 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0091 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0091 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0091 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
SELECT 'TC-I0091' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0091
   WHERE id NOT IN (SELECT id FROM t2_i0091)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0091
   WHERE id NOT IN (SELECT id FROM t1_i0091)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0091 a JOIN t2_i0091 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0092
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0092, t2_i0092;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0092 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0092 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0092 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0092 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0092 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0092 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0092 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0092 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0092 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0092 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0092 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0092 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0092 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0092 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0092 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0092 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0092 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0092 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0092 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0092 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0092 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0092 (target) VALUES (NULL);
INSERT INTO t2_i0092 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0092 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0092 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0092 (target) VALUES (NULL);
SELECT 'TC-I0092' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0092
   WHERE id NOT IN (SELECT id FROM t2_i0092)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0092
   WHERE id NOT IN (SELECT id FROM t1_i0092)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0092 a JOIN t2_i0092 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0093
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0093, t2_i0093;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0093 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0093 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0093 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0093 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0093 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0093 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0093 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0093 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0093 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0093 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0093 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0093 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0093 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0093 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0093 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0093 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0093 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0093 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0093 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0093 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0093 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0093 (target) VALUES (NULL);
INSERT INTO t2_i0093 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0093 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0093 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0093 (target) VALUES (NULL);
SELECT 'TC-I0093' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0093
   WHERE id NOT IN (SELECT id FROM t2_i0093)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0093
   WHERE id NOT IN (SELECT id FROM t1_i0093)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0093 a JOIN t2_i0093 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0094
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0094, t2_i0094;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0094 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0094 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0094 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0094 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0094 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0094 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0094 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0094 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0094 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0094 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0094 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0094 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0094 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0094 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0094 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0094 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0094 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0094 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0094 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0094 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0094 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0094 (target) VALUES (NULL);
INSERT INTO t2_i0094 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0094 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0094 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0094 (target) VALUES (NULL);
SELECT 'TC-I0094' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0094
   WHERE id NOT IN (SELECT id FROM t2_i0094)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0094
   WHERE id NOT IN (SELECT id FROM t1_i0094)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0094 a JOIN t2_i0094 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0095
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0095, t2_i0095;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0095 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0095 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0095 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0095 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0095 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0095 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0095 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0095 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0095 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0095 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0095 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0095 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0095 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0095 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0095 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0095 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0095 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0095 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0095 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0095 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0095 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0095 (target) VALUES (NULL);
INSERT INTO t2_i0095 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0095 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0095 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0095 (target) VALUES (NULL);
SELECT 'TC-I0095' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0095
   WHERE id NOT IN (SELECT id FROM t2_i0095)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0095
   WHERE id NOT IN (SELECT id FROM t1_i0095)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0095 a JOIN t2_i0095 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0096
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0096, t2_i0096;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0096 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0096 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0096 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0096 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0096 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0096 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0096 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0096 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0096 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0096 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0096 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0096 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0096 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0096 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0096 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0096 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0096 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0096 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0096 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0096 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0096 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0096 (target) VALUES (NULL);
INSERT INTO t2_i0096 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0096 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0096 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0096 (target) VALUES (NULL);
SELECT 'TC-I0096' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0096
   WHERE id NOT IN (SELECT id FROM t2_i0096)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0096
   WHERE id NOT IN (SELECT id FROM t1_i0096)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0096 a JOIN t2_i0096 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0097
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0097, t2_i0097;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0097 (
  target DECIMAL(64,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0097 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0097 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0097 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0097 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0097 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0097 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0097 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0097 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0097 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0097 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0097 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0097 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0097 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0097 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0097 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0097 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0097 (
  target DECIMAL(65,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0097 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0097 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0097 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0097 (target) VALUES (NULL);
INSERT INTO t2_i0097 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0097 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0097 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0097 (target) VALUES (NULL);
SELECT 'TC-I0097' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0097
   WHERE id NOT IN (SELECT id FROM t2_i0097)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0097
   WHERE id NOT IN (SELECT id FROM t1_i0097)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0097 a JOIN t2_i0097 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0098
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0098, t2_i0098;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0098 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(64,30), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0098 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0098 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0098 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0098 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0098 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0098 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0098 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0098 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0098 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0098 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0098 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0098 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0098 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0098 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0098 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0098 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0098 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(65,30), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0098 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0098 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0098 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0098 (target) VALUES (NULL);
INSERT INTO t2_i0098 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0098 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0098 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0098 (target) VALUES (NULL);
SELECT 'TC-I0098' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0098
   WHERE id NOT IN (SELECT id FROM t2_i0098)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0098
   WHERE id NOT IN (SELECT id FROM t1_i0098)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0098 a JOIN t2_i0098 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0099
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0099, t2_i0099;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0099 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0099 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0099 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0099 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0099 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0099 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0099 MODIFY target DECIMAL(65,30) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0099 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0099 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0099 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0099 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0099 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0099 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0099 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0099 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0099 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0099 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0099 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0099 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0099 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0099 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0099 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0099 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
SELECT 'TC-I0099' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0099
   WHERE id NOT IN (SELECT id FROM t2_i0099)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0099
   WHERE id NOT IN (SELECT id FROM t1_i0099)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0099 a JOIN t2_i0099 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0100
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0100, t2_i0100;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0100 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0100 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0100 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0100 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0100 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0100 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0100 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0100 MODIFY target DECIMAL(65,30) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0100 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0100 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0100 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0100 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0100 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0100 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0100 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0100 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0100 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0100 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0100 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0100 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0100 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0100 (target) VALUES (NULL);
INSERT INTO t2_i0100 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0100 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0100 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0100 (target) VALUES (NULL);
SELECT 'TC-I0100' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0100
   WHERE id NOT IN (SELECT id FROM t2_i0100)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0100
   WHERE id NOT IN (SELECT id FROM t1_i0100)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0100 a JOIN t2_i0100 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0101
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0101, t2_i0101;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0101 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0101 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0101 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0101 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0101 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0101 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0101 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0101 MODIFY target DECIMAL(65,30) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0101 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0101 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0101 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0101 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0101 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0101 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0101 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0101 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0101 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0101 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0101 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0101 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0101 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0101 (target) VALUES (NULL);
INSERT INTO t2_i0101 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0101 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0101 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0101 (target) VALUES (NULL);
SELECT 'TC-I0101' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0101
   WHERE id NOT IN (SELECT id FROM t2_i0101)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0101
   WHERE id NOT IN (SELECT id FROM t1_i0101)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0101 a JOIN t2_i0101 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0102
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0102, t2_i0102;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0102 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0102 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0102 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0102 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0102 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0102 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0102 MODIFY target DECIMAL(65,30) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0102 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0102 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0102 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0102 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0102 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0102 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0102 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0102 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0102 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0102 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0102 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0102 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0102 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0102 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0102 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0102 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
SELECT 'TC-I0102' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0102
   WHERE id NOT IN (SELECT id FROM t2_i0102)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0102
   WHERE id NOT IN (SELECT id FROM t1_i0102)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0102 a JOIN t2_i0102 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0103
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0103, t2_i0103;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0103 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0103 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0103 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0103 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0103 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0103 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0103 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0103 MODIFY target DECIMAL(65,30) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0103 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0103 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0103 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0103 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0103 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0103 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0103 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0103 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0103 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0103 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0103 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0103 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0103 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0103 (target) VALUES (NULL);
INSERT INTO t2_i0103 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0103 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0103 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0103 (target) VALUES (NULL);
SELECT 'TC-I0103' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0103
   WHERE id NOT IN (SELECT id FROM t2_i0103)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0103
   WHERE id NOT IN (SELECT id FROM t1_i0103)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0103 a JOIN t2_i0103 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0104
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0104, t2_i0104;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0104 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0104 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0104 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0104 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0104' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0104
   WHERE id NOT IN (SELECT id FROM t2_i0104)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0104
   WHERE id NOT IN (SELECT id FROM t1_i0104)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0104 a JOIN t2_i0104 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0105
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0105, t2_i0105;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0105 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0105 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0105 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0105 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0105 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0105 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0105 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0105 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0105 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0105 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0105 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0105 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0105 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0105 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0105 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0105 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0105 (target) VALUES (NULL);
SELECT 'TC-I0105' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0105
   WHERE id NOT IN (SELECT id FROM t2_i0105)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0105
   WHERE id NOT IN (SELECT id FROM t1_i0105)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0105 a JOIN t2_i0105 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0106
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0106, t2_i0106;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0106 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0106 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0106 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0106 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0106 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0106 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0106 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0106 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0106 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0106 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0106 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0106 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0106 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0106 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0106 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0106 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0106 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0106 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0106 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0106 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0106 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0106 (target) VALUES (NULL);
INSERT INTO t2_i0106 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0106 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0106 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0106 (target) VALUES (NULL);
SELECT 'TC-I0106' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0106
   WHERE id NOT IN (SELECT id FROM t2_i0106)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0106
   WHERE id NOT IN (SELECT id FROM t1_i0106)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0106 a JOIN t2_i0106 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0107
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0107, t2_i0107;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0107 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0107 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0107 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0107 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0107 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0107 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0107 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0107 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0107 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0107 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0107 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0107 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0107 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0107 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0107 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0107 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0107 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0107 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0107 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0107 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0107 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0107 (target) VALUES (NULL);
INSERT INTO t2_i0107 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0107 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0107 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0107 (target) VALUES (NULL);
SELECT 'TC-I0107' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0107
   WHERE id NOT IN (SELECT id FROM t2_i0107)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0107
   WHERE id NOT IN (SELECT id FROM t1_i0107)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0107 a JOIN t2_i0107 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0108
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0108, t2_i0108;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0108 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0108 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0108 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0108 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0108 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0108 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0108 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0108 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0108 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0108 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0108 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0108 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0108 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0108 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0108 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0108 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0108 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0108 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0108 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0108 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0108 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0108 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0108 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
SELECT 'TC-I0108' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0108
   WHERE id NOT IN (SELECT id FROM t2_i0108)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0108
   WHERE id NOT IN (SELECT id FROM t1_i0108)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0108 a JOIN t2_i0108 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0109
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0109, t2_i0109;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0109 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0109 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0109 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0109 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0109 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0109 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0109 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0109 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0109 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0109 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0109 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0109 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0109 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0109 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0109 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0109 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0109 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0109 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0109 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0109 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0109 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0109 (target) VALUES (NULL);
INSERT INTO t2_i0109 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0109 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0109 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0109 (target) VALUES (NULL);
SELECT 'TC-I0109' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0109
   WHERE id NOT IN (SELECT id FROM t2_i0109)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0109
   WHERE id NOT IN (SELECT id FROM t1_i0109)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0109 a JOIN t2_i0109 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0110
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0110, t2_i0110;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0110 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0110 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0110 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0110 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0110 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0110 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0110 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0110 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0110 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0110 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0110 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0110 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0110 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0110 (target) VALUES (NULL);
INSERT INTO t2_i0110 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0110 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0110 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0110 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0110 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0110 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0110 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0110 (target) VALUES (NULL);
SELECT 'TC-I0110' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0110
   WHERE id NOT IN (SELECT id FROM t2_i0110)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0110
   WHERE id NOT IN (SELECT id FROM t1_i0110)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0110 a JOIN t2_i0110 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0111
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0111, t2_i0111;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0111 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0111 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0111 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0111 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0111 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0111 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0111 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0111 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0111 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0111 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0111 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0111 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0111 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0111 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0111 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0111 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0111 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0111 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0111 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0111 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0111 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0111 (target) VALUES (NULL);
INSERT INTO t2_i0111 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0111 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0111 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0111 (target) VALUES (NULL);
SELECT 'TC-I0111' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0111
   WHERE id NOT IN (SELECT id FROM t2_i0111)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0111
   WHERE id NOT IN (SELECT id FROM t1_i0111)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0111 a JOIN t2_i0111 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0112
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0112, t2_i0112;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0112 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0112 MODIFY target DECIMAL(65,30) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0112 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0112 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0112' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0112
   WHERE id NOT IN (SELECT id FROM t2_i0112)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0112
   WHERE id NOT IN (SELECT id FROM t1_i0112)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0112 a JOIN t2_i0112 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0113
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0113, t2_i0113;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0113 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0113 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0113 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0113 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0113' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0113
   WHERE id NOT IN (SELECT id FROM t2_i0113)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0113
   WHERE id NOT IN (SELECT id FROM t1_i0113)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0113 a JOIN t2_i0113 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0114
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0114, t2_i0114;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0114 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(64,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0114 MODIFY target DECIMAL(65,30) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0114 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(65,30)
CREATE TABLE t2_i0114 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(65,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0114' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0114
   WHERE id NOT IN (SELECT id FROM t2_i0114)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0114
   WHERE id NOT IN (SELECT id FROM t1_i0114)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0114 a JOIN t2_i0114 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0115
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0115, t2_i0115;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0115 (
  target DECIMAL(64,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0115 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0115 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_i0115 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0115 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0115 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0115 MODIFY target DECIMAL(65,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0115 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0115 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0115 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0115 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0115 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0115 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0115 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0115 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(64,30)
CREATE TABLE t2_i0115 (
  target DECIMAL(64,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0115 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0115 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0115 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0115 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0115 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0115 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0115 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
SELECT 'TC-I0115' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0115
   WHERE id NOT IN (SELECT id FROM t2_i0115)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0115
   WHERE id NOT IN (SELECT id FROM t1_i0115)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0115 a JOIN t2_i0115 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0116
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(64,30) -> DECIMAL(65,30), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0116, t2_tc_ia0116;
CREATE TABLE t1_tc_ia0116 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(64,30) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0116 (target) VALUES (-9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0116 (target) VALUES (9999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0116 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_tc_ia0116 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_tc_ia0116 (target) VALUES (-1.111111111111111111111111111111);
ALTER TABLE t1_tc_ia0116 MODIFY target DECIMAL(65,30) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0116 (target) VALUES (99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0116 (target) VALUES (-99999999999999999999999999999999999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0116 (target) VALUES (1.999999999999999999999999999999);
SELECT 'TC-IA0116' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0116' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0117
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0117, t2_i0117;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0117 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0117 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0117 (target) VALUES (999999999999999999);
INSERT INTO t1_i0117 (target) VALUES (0);
INSERT INTO t1_i0117 (target) VALUES (1);
INSERT INTO t1_i0117 (target) VALUES (-1);
INSERT INTO t1_i0117 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0117 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0117 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0117 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0117 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0117 (target) VALUES (-999999999);
INSERT INTO t1_i0117 (target) VALUES (0);
INSERT INTO t1_i0117 (target) VALUES (1);
INSERT INTO t1_i0117 (target) VALUES (999999999999999999);
INSERT INTO t1_i0117 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0117 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0117 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0117 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0117 (target) VALUES (999999999999999999);
INSERT INTO t2_i0117 (target) VALUES (0);
INSERT INTO t2_i0117 (target) VALUES (1);
INSERT INTO t2_i0117 (target) VALUES (-1);
INSERT INTO t2_i0117 (target) VALUES (NULL);
INSERT INTO t2_i0117 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0117 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0117 (target) VALUES (999999999);
INSERT INTO t2_i0117 (target) VALUES (-999999999);
INSERT INTO t2_i0117 (target) VALUES (0);
INSERT INTO t2_i0117 (target) VALUES (1);
INSERT INTO t2_i0117 (target) VALUES (999999999999999999);
INSERT INTO t2_i0117 (target) VALUES (NULL);
SELECT 'TC-I0117' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0117
   WHERE id NOT IN (SELECT id FROM t2_i0117)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0117
   WHERE id NOT IN (SELECT id FROM t1_i0117)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0117 a JOIN t2_i0117 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0118
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0118, t2_i0118;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0118 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0118 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0118 (target) VALUES (999999999999999999);
INSERT INTO t1_i0118 (target) VALUES (0);
INSERT INTO t1_i0118 (target) VALUES (1);
INSERT INTO t1_i0118 (target) VALUES (-1);
INSERT INTO t1_i0118 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0118 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0118 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0118 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0118 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0118 (target) VALUES (-999999999);
INSERT INTO t1_i0118 (target) VALUES (0);
INSERT INTO t1_i0118 (target) VALUES (1);
INSERT INTO t1_i0118 (target) VALUES (999999999999999999);
INSERT INTO t1_i0118 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0118 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0118 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0118 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0118 (target) VALUES (999999999999999999);
INSERT INTO t2_i0118 (target) VALUES (0);
INSERT INTO t2_i0118 (target) VALUES (1);
INSERT INTO t2_i0118 (target) VALUES (-1);
INSERT INTO t2_i0118 (target) VALUES (NULL);
INSERT INTO t2_i0118 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0118 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0118 (target) VALUES (999999999);
INSERT INTO t2_i0118 (target) VALUES (-999999999);
INSERT INTO t2_i0118 (target) VALUES (0);
INSERT INTO t2_i0118 (target) VALUES (1);
INSERT INTO t2_i0118 (target) VALUES (999999999999999999);
INSERT INTO t2_i0118 (target) VALUES (NULL);
SELECT 'TC-I0118' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0118
   WHERE id NOT IN (SELECT id FROM t2_i0118)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0118
   WHERE id NOT IN (SELECT id FROM t1_i0118)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0118 a JOIN t2_i0118 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0119
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0119, t2_i0119;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0119 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0119 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0119 (target) VALUES (999999999999999999);
INSERT INTO t1_i0119 (target) VALUES (0);
INSERT INTO t1_i0119 (target) VALUES (1);
INSERT INTO t1_i0119 (target) VALUES (-1);
INSERT INTO t1_i0119 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0119 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0119 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0119 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0119 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0119 (target) VALUES (-999999999);
INSERT INTO t1_i0119 (target) VALUES (0);
INSERT INTO t1_i0119 (target) VALUES (1);
INSERT INTO t1_i0119 (target) VALUES (999999999999999999);
INSERT INTO t1_i0119 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0119 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0119 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0119 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0119 (target) VALUES (999999999999999999);
INSERT INTO t2_i0119 (target) VALUES (0);
INSERT INTO t2_i0119 (target) VALUES (1);
INSERT INTO t2_i0119 (target) VALUES (-1);
INSERT INTO t2_i0119 (target) VALUES (NULL);
INSERT INTO t2_i0119 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0119 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0119 (target) VALUES (999999999);
INSERT INTO t2_i0119 (target) VALUES (-999999999);
INSERT INTO t2_i0119 (target) VALUES (0);
INSERT INTO t2_i0119 (target) VALUES (1);
INSERT INTO t2_i0119 (target) VALUES (999999999999999999);
INSERT INTO t2_i0119 (target) VALUES (NULL);
SELECT 'TC-I0119' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0119
   WHERE id NOT IN (SELECT id FROM t2_i0119)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0119
   WHERE id NOT IN (SELECT id FROM t1_i0119)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0119 a JOIN t2_i0119 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0120
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0120, t2_i0120;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0120 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0120 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0120 (target) VALUES (999999999999999999);
INSERT INTO t1_i0120 (target) VALUES (0);
INSERT INTO t1_i0120 (target) VALUES (1);
INSERT INTO t1_i0120 (target) VALUES (-1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0120 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0120 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0120 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0120 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0120 (target) VALUES (-999999999);
INSERT INTO t1_i0120 (target) VALUES (0);
INSERT INTO t1_i0120 (target) VALUES (1);
INSERT INTO t1_i0120 (target) VALUES (999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0120 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(18,0)
CREATE TABLE t2_i0120 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0120 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0120 (target) VALUES (999999999999999999);
INSERT INTO t2_i0120 (target) VALUES (0);
INSERT INTO t2_i0120 (target) VALUES (1);
INSERT INTO t2_i0120 (target) VALUES (-1);
INSERT INTO t2_i0120 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0120 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0120 (target) VALUES (999999999);
INSERT INTO t2_i0120 (target) VALUES (-999999999);
INSERT INTO t2_i0120 (target) VALUES (0);
INSERT INTO t2_i0120 (target) VALUES (1);
INSERT INTO t2_i0120 (target) VALUES (999999999999999999);
SELECT 'TC-I0120' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0120
   WHERE id NOT IN (SELECT id FROM t2_i0120)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0120
   WHERE id NOT IN (SELECT id FROM t1_i0120)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0120 a JOIN t2_i0120 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0121
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0121, t2_i0121;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0121 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0121 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0121 (target) VALUES (999999999999999999);
INSERT INTO t1_i0121 (target) VALUES (0);
INSERT INTO t1_i0121 (target) VALUES (1);
INSERT INTO t1_i0121 (target) VALUES (-1);
INSERT INTO t1_i0121 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0121 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0121 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0121 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0121 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0121 (target) VALUES (-999999999);
INSERT INTO t1_i0121 (target) VALUES (0);
INSERT INTO t1_i0121 (target) VALUES (1);
INSERT INTO t1_i0121 (target) VALUES (999999999999999999);
INSERT INTO t1_i0121 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0121 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0121 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0121 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0121 (target) VALUES (999999999999999999);
INSERT INTO t2_i0121 (target) VALUES (0);
INSERT INTO t2_i0121 (target) VALUES (1);
INSERT INTO t2_i0121 (target) VALUES (-1);
INSERT INTO t2_i0121 (target) VALUES (NULL);
INSERT INTO t2_i0121 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0121 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0121 (target) VALUES (999999999);
INSERT INTO t2_i0121 (target) VALUES (-999999999);
INSERT INTO t2_i0121 (target) VALUES (0);
INSERT INTO t2_i0121 (target) VALUES (1);
INSERT INTO t2_i0121 (target) VALUES (999999999999999999);
INSERT INTO t2_i0121 (target) VALUES (NULL);
SELECT 'TC-I0121' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0121
   WHERE id NOT IN (SELECT id FROM t2_i0121)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0121
   WHERE id NOT IN (SELECT id FROM t1_i0121)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0121 a JOIN t2_i0121 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0122
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0122, t2_i0122;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0122 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0122 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0122 (target) VALUES (999999999999999999);
INSERT INTO t1_i0122 (target) VALUES (0);
INSERT INTO t1_i0122 (target) VALUES (1);
INSERT INTO t1_i0122 (target) VALUES (-1);
INSERT INTO t1_i0122 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0122 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0122 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0122 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0122 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0122 (target) VALUES (-999999999);
INSERT INTO t1_i0122 (target) VALUES (0);
INSERT INTO t1_i0122 (target) VALUES (1);
INSERT INTO t1_i0122 (target) VALUES (999999999999999999);
INSERT INTO t1_i0122 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0122 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0122 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0122 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0122 (target) VALUES (999999999999999999);
INSERT INTO t2_i0122 (target) VALUES (0);
INSERT INTO t2_i0122 (target) VALUES (1);
INSERT INTO t2_i0122 (target) VALUES (-1);
INSERT INTO t2_i0122 (target) VALUES (NULL);
INSERT INTO t2_i0122 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0122 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0122 (target) VALUES (999999999);
INSERT INTO t2_i0122 (target) VALUES (-999999999);
INSERT INTO t2_i0122 (target) VALUES (0);
INSERT INTO t2_i0122 (target) VALUES (1);
INSERT INTO t2_i0122 (target) VALUES (999999999999999999);
INSERT INTO t2_i0122 (target) VALUES (NULL);
SELECT 'TC-I0122' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0122
   WHERE id NOT IN (SELECT id FROM t2_i0122)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0122
   WHERE id NOT IN (SELECT id FROM t1_i0122)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0122 a JOIN t2_i0122 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0123
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0123, t2_i0123;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0123 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0123 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0123 (target) VALUES (999999999999999999);
INSERT INTO t1_i0123 (target) VALUES (0);
INSERT INTO t1_i0123 (target) VALUES (1);
INSERT INTO t1_i0123 (target) VALUES (-1);
INSERT INTO t1_i0123 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0123 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0123 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0123 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0123 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0123 (target) VALUES (-999999999);
INSERT INTO t1_i0123 (target) VALUES (0);
INSERT INTO t1_i0123 (target) VALUES (1);
INSERT INTO t1_i0123 (target) VALUES (999999999999999999);
INSERT INTO t1_i0123 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0123 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0123 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0123 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0123 (target) VALUES (999999999999999999);
INSERT INTO t2_i0123 (target) VALUES (0);
INSERT INTO t2_i0123 (target) VALUES (1);
INSERT INTO t2_i0123 (target) VALUES (-1);
INSERT INTO t2_i0123 (target) VALUES (NULL);
INSERT INTO t2_i0123 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0123 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0123 (target) VALUES (999999999);
INSERT INTO t2_i0123 (target) VALUES (-999999999);
INSERT INTO t2_i0123 (target) VALUES (0);
INSERT INTO t2_i0123 (target) VALUES (1);
INSERT INTO t2_i0123 (target) VALUES (999999999999999999);
INSERT INTO t2_i0123 (target) VALUES (NULL);
SELECT 'TC-I0123' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0123
   WHERE id NOT IN (SELECT id FROM t2_i0123)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0123
   WHERE id NOT IN (SELECT id FROM t1_i0123)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0123 a JOIN t2_i0123 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0124
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0124, t2_i0124;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0124 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0124 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0124 (target) VALUES (999999999999999999);
INSERT INTO t1_i0124 (target) VALUES (0);
INSERT INTO t1_i0124 (target) VALUES (1);
INSERT INTO t1_i0124 (target) VALUES (-1);
INSERT INTO t1_i0124 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0124 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0124 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0124 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0124 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0124 (target) VALUES (-999999999);
INSERT INTO t1_i0124 (target) VALUES (0);
INSERT INTO t1_i0124 (target) VALUES (1);
INSERT INTO t1_i0124 (target) VALUES (999999999999999999);
INSERT INTO t1_i0124 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0124 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0124 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0124 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0124 (target) VALUES (999999999999999999);
INSERT INTO t2_i0124 (target) VALUES (0);
INSERT INTO t2_i0124 (target) VALUES (1);
INSERT INTO t2_i0124 (target) VALUES (-1);
INSERT INTO t2_i0124 (target) VALUES (NULL);
INSERT INTO t2_i0124 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0124 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0124 (target) VALUES (999999999);
INSERT INTO t2_i0124 (target) VALUES (-999999999);
INSERT INTO t2_i0124 (target) VALUES (0);
INSERT INTO t2_i0124 (target) VALUES (1);
INSERT INTO t2_i0124 (target) VALUES (999999999999999999);
INSERT INTO t2_i0124 (target) VALUES (NULL);
SELECT 'TC-I0124' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0124
   WHERE id NOT IN (SELECT id FROM t2_i0124)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0124
   WHERE id NOT IN (SELECT id FROM t1_i0124)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0124 a JOIN t2_i0124 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0125
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0125, t2_i0125;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0125 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0125 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0125 (target) VALUES (999999999999999999);
INSERT INTO t1_i0125 (target) VALUES (0);
INSERT INTO t1_i0125 (target) VALUES (1);
INSERT INTO t1_i0125 (target) VALUES (-1);
INSERT INTO t1_i0125 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0125 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0125 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0125 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0125 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0125 (target) VALUES (-999999999);
INSERT INTO t1_i0125 (target) VALUES (0);
INSERT INTO t1_i0125 (target) VALUES (1);
INSERT INTO t1_i0125 (target) VALUES (999999999999999999);
INSERT INTO t1_i0125 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0125 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0125 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0125 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0125 (target) VALUES (999999999999999999);
INSERT INTO t2_i0125 (target) VALUES (0);
INSERT INTO t2_i0125 (target) VALUES (1);
INSERT INTO t2_i0125 (target) VALUES (-1);
INSERT INTO t2_i0125 (target) VALUES (NULL);
INSERT INTO t2_i0125 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0125 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0125 (target) VALUES (999999999);
INSERT INTO t2_i0125 (target) VALUES (-999999999);
INSERT INTO t2_i0125 (target) VALUES (0);
INSERT INTO t2_i0125 (target) VALUES (1);
INSERT INTO t2_i0125 (target) VALUES (999999999999999999);
INSERT INTO t2_i0125 (target) VALUES (NULL);
SELECT 'TC-I0125' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0125
   WHERE id NOT IN (SELECT id FROM t2_i0125)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0125
   WHERE id NOT IN (SELECT id FROM t1_i0125)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0125 a JOIN t2_i0125 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0126
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0126, t2_i0126;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0126 (
  target DECIMAL(18,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0126 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0126 (target) VALUES (999999999999999999);
INSERT INTO t1_i0126 (target) VALUES (0);
INSERT INTO t1_i0126 (target) VALUES (1);
INSERT INTO t1_i0126 (target) VALUES (-1);
INSERT INTO t1_i0126 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0126 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0126 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0126 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0126 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0126 (target) VALUES (-999999999);
INSERT INTO t1_i0126 (target) VALUES (0);
INSERT INTO t1_i0126 (target) VALUES (1);
INSERT INTO t1_i0126 (target) VALUES (999999999999999999);
INSERT INTO t1_i0126 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0126 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0126 (
  target DECIMAL(20,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0126 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0126 (target) VALUES (999999999999999999);
INSERT INTO t2_i0126 (target) VALUES (0);
INSERT INTO t2_i0126 (target) VALUES (1);
INSERT INTO t2_i0126 (target) VALUES (-1);
INSERT INTO t2_i0126 (target) VALUES (NULL);
INSERT INTO t2_i0126 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0126 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0126 (target) VALUES (999999999);
INSERT INTO t2_i0126 (target) VALUES (-999999999);
INSERT INTO t2_i0126 (target) VALUES (0);
INSERT INTO t2_i0126 (target) VALUES (1);
INSERT INTO t2_i0126 (target) VALUES (999999999999999999);
INSERT INTO t2_i0126 (target) VALUES (NULL);
SELECT 'TC-I0126' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0126
   WHERE id NOT IN (SELECT id FROM t2_i0126)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0126
   WHERE id NOT IN (SELECT id FROM t1_i0126)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0126 a JOIN t2_i0126 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0127
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0127, t2_i0127;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0127 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(18,0), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0127 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0127 (target) VALUES (999999999999999999);
INSERT INTO t1_i0127 (target) VALUES (0);
INSERT INTO t1_i0127 (target) VALUES (1);
INSERT INTO t1_i0127 (target) VALUES (-1);
INSERT INTO t1_i0127 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0127 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0127 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0127 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0127 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0127 (target) VALUES (-999999999);
INSERT INTO t1_i0127 (target) VALUES (0);
INSERT INTO t1_i0127 (target) VALUES (1);
INSERT INTO t1_i0127 (target) VALUES (999999999999999999);
INSERT INTO t1_i0127 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0127 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0127 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(20,0), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0127 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0127 (target) VALUES (999999999999999999);
INSERT INTO t2_i0127 (target) VALUES (0);
INSERT INTO t2_i0127 (target) VALUES (1);
INSERT INTO t2_i0127 (target) VALUES (-1);
INSERT INTO t2_i0127 (target) VALUES (NULL);
INSERT INTO t2_i0127 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0127 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0127 (target) VALUES (999999999);
INSERT INTO t2_i0127 (target) VALUES (-999999999);
INSERT INTO t2_i0127 (target) VALUES (0);
INSERT INTO t2_i0127 (target) VALUES (1);
INSERT INTO t2_i0127 (target) VALUES (999999999999999999);
INSERT INTO t2_i0127 (target) VALUES (NULL);
SELECT 'TC-I0127' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0127
   WHERE id NOT IN (SELECT id FROM t2_i0127)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0127
   WHERE id NOT IN (SELECT id FROM t1_i0127)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0127 a JOIN t2_i0127 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0128
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0128, t2_i0128;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0128 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0128 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0128 (target) VALUES (999999999999999999);
INSERT INTO t1_i0128 (target) VALUES (0);
INSERT INTO t1_i0128 (target) VALUES (1);
INSERT INTO t1_i0128 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0128 MODIFY target DECIMAL(20,0) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0128 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0128 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0128 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0128 (target) VALUES (-999999999);
INSERT INTO t1_i0128 (target) VALUES (0);
INSERT INTO t1_i0128 (target) VALUES (1);
INSERT INTO t1_i0128 (target) VALUES (999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0128 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0128 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0128 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0128 (target) VALUES (999999999999999999);
INSERT INTO t2_i0128 (target) VALUES (0);
INSERT INTO t2_i0128 (target) VALUES (1);
INSERT INTO t2_i0128 (target) VALUES (-1);
INSERT INTO t2_i0128 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0128 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0128 (target) VALUES (999999999);
INSERT INTO t2_i0128 (target) VALUES (-999999999);
INSERT INTO t2_i0128 (target) VALUES (0);
INSERT INTO t2_i0128 (target) VALUES (1);
INSERT INTO t2_i0128 (target) VALUES (999999999999999999);
SELECT 'TC-I0128' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0128
   WHERE id NOT IN (SELECT id FROM t2_i0128)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0128
   WHERE id NOT IN (SELECT id FROM t1_i0128)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0128 a JOIN t2_i0128 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0129
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0129, t2_i0129;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0129 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0129 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0129 (target) VALUES (999999999999999999);
INSERT INTO t1_i0129 (target) VALUES (0);
INSERT INTO t1_i0129 (target) VALUES (1);
INSERT INTO t1_i0129 (target) VALUES (-1);
INSERT INTO t1_i0129 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0129 MODIFY target DECIMAL(20,0) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0129 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0129 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0129 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0129 (target) VALUES (-999999999);
INSERT INTO t1_i0129 (target) VALUES (0);
INSERT INTO t1_i0129 (target) VALUES (1);
INSERT INTO t1_i0129 (target) VALUES (999999999999999999);
INSERT INTO t1_i0129 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0129 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0129 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0129 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0129 (target) VALUES (999999999999999999);
INSERT INTO t2_i0129 (target) VALUES (0);
INSERT INTO t2_i0129 (target) VALUES (1);
INSERT INTO t2_i0129 (target) VALUES (-1);
INSERT INTO t2_i0129 (target) VALUES (NULL);
INSERT INTO t2_i0129 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0129 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0129 (target) VALUES (999999999);
INSERT INTO t2_i0129 (target) VALUES (-999999999);
INSERT INTO t2_i0129 (target) VALUES (0);
INSERT INTO t2_i0129 (target) VALUES (1);
INSERT INTO t2_i0129 (target) VALUES (999999999999999999);
INSERT INTO t2_i0129 (target) VALUES (NULL);
SELECT 'TC-I0129' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0129
   WHERE id NOT IN (SELECT id FROM t2_i0129)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0129
   WHERE id NOT IN (SELECT id FROM t1_i0129)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0129 a JOIN t2_i0129 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0130
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0130, t2_i0130;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0130 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0130 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0130 (target) VALUES (999999999999999999);
INSERT INTO t1_i0130 (target) VALUES (0);
INSERT INTO t1_i0130 (target) VALUES (1);
INSERT INTO t1_i0130 (target) VALUES (-1);
INSERT INTO t1_i0130 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0130 MODIFY target DECIMAL(20,0) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0130 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0130 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0130 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0130 (target) VALUES (-999999999);
INSERT INTO t1_i0130 (target) VALUES (0);
INSERT INTO t1_i0130 (target) VALUES (1);
INSERT INTO t1_i0130 (target) VALUES (999999999999999999);
INSERT INTO t1_i0130 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0130 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0130 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0130 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0130 (target) VALUES (999999999999999999);
INSERT INTO t2_i0130 (target) VALUES (0);
INSERT INTO t2_i0130 (target) VALUES (1);
INSERT INTO t2_i0130 (target) VALUES (-1);
INSERT INTO t2_i0130 (target) VALUES (NULL);
INSERT INTO t2_i0130 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0130 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0130 (target) VALUES (999999999);
INSERT INTO t2_i0130 (target) VALUES (-999999999);
INSERT INTO t2_i0130 (target) VALUES (0);
INSERT INTO t2_i0130 (target) VALUES (1);
INSERT INTO t2_i0130 (target) VALUES (999999999999999999);
INSERT INTO t2_i0130 (target) VALUES (NULL);
SELECT 'TC-I0130' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0130
   WHERE id NOT IN (SELECT id FROM t2_i0130)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0130
   WHERE id NOT IN (SELECT id FROM t1_i0130)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0130 a JOIN t2_i0130 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0131
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0131, t2_i0131;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0131 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0131 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0131 (target) VALUES (999999999999999999);
INSERT INTO t1_i0131 (target) VALUES (0);
INSERT INTO t1_i0131 (target) VALUES (1);
INSERT INTO t1_i0131 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0131 MODIFY target DECIMAL(20,0) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0131 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0131 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0131 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0131 (target) VALUES (-999999999);
INSERT INTO t1_i0131 (target) VALUES (0);
INSERT INTO t1_i0131 (target) VALUES (1);
INSERT INTO t1_i0131 (target) VALUES (999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0131 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0131 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0131 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0131 (target) VALUES (999999999999999999);
INSERT INTO t2_i0131 (target) VALUES (0);
INSERT INTO t2_i0131 (target) VALUES (1);
INSERT INTO t2_i0131 (target) VALUES (-1);
INSERT INTO t2_i0131 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0131 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0131 (target) VALUES (999999999);
INSERT INTO t2_i0131 (target) VALUES (-999999999);
INSERT INTO t2_i0131 (target) VALUES (0);
INSERT INTO t2_i0131 (target) VALUES (1);
INSERT INTO t2_i0131 (target) VALUES (999999999999999999);
SELECT 'TC-I0131' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0131
   WHERE id NOT IN (SELECT id FROM t2_i0131)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0131
   WHERE id NOT IN (SELECT id FROM t1_i0131)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0131 a JOIN t2_i0131 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0132
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0132, t2_i0132;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0132 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0132 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0132 (target) VALUES (999999999999999999);
INSERT INTO t1_i0132 (target) VALUES (0);
INSERT INTO t1_i0132 (target) VALUES (1);
INSERT INTO t1_i0132 (target) VALUES (-1);
INSERT INTO t1_i0132 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0132 MODIFY target DECIMAL(20,0) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0132 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0132 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0132 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0132 (target) VALUES (-999999999);
INSERT INTO t1_i0132 (target) VALUES (0);
INSERT INTO t1_i0132 (target) VALUES (1);
INSERT INTO t1_i0132 (target) VALUES (999999999999999999);
INSERT INTO t1_i0132 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0132 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0132 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0132 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0132 (target) VALUES (999999999999999999);
INSERT INTO t2_i0132 (target) VALUES (0);
INSERT INTO t2_i0132 (target) VALUES (1);
INSERT INTO t2_i0132 (target) VALUES (-1);
INSERT INTO t2_i0132 (target) VALUES (NULL);
INSERT INTO t2_i0132 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0132 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0132 (target) VALUES (999999999);
INSERT INTO t2_i0132 (target) VALUES (-999999999);
INSERT INTO t2_i0132 (target) VALUES (0);
INSERT INTO t2_i0132 (target) VALUES (1);
INSERT INTO t2_i0132 (target) VALUES (999999999999999999);
INSERT INTO t2_i0132 (target) VALUES (NULL);
SELECT 'TC-I0132' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0132
   WHERE id NOT IN (SELECT id FROM t2_i0132)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0132
   WHERE id NOT IN (SELECT id FROM t1_i0132)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0132 a JOIN t2_i0132 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0133
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0133, t2_i0133;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0133 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0133 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0133 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0133 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0133' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0133
   WHERE id NOT IN (SELECT id FROM t2_i0133)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0133
   WHERE id NOT IN (SELECT id FROM t1_i0133)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0133 a JOIN t2_i0133 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0134
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0134, t2_i0134;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0134 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0134 (target) VALUES (-999999999999999999);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0134 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0134 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0134 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0134 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0134 (target) VALUES (-999999999);
INSERT INTO t1_i0134 (target) VALUES (0);
INSERT INTO t1_i0134 (target) VALUES (1);
INSERT INTO t1_i0134 (target) VALUES (999999999999999999);
INSERT INTO t1_i0134 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0134 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0134 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0134 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0134 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0134 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0134 (target) VALUES (999999999);
INSERT INTO t2_i0134 (target) VALUES (-999999999);
INSERT INTO t2_i0134 (target) VALUES (0);
INSERT INTO t2_i0134 (target) VALUES (1);
INSERT INTO t2_i0134 (target) VALUES (999999999999999999);
INSERT INTO t2_i0134 (target) VALUES (NULL);
SELECT 'TC-I0134' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0134
   WHERE id NOT IN (SELECT id FROM t2_i0134)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0134
   WHERE id NOT IN (SELECT id FROM t1_i0134)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0134 a JOIN t2_i0134 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0135
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0135, t2_i0135;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0135 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0135 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0135 (target) VALUES (999999999999999999);
INSERT INTO t1_i0135 (target) VALUES (0);
INSERT INTO t1_i0135 (target) VALUES (1);
INSERT INTO t1_i0135 (target) VALUES (-1);
INSERT INTO t1_i0135 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0135 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0135 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0135 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0135 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0135 (target) VALUES (-999999999);
INSERT INTO t1_i0135 (target) VALUES (0);
INSERT INTO t1_i0135 (target) VALUES (1);
INSERT INTO t1_i0135 (target) VALUES (999999999999999999);
INSERT INTO t1_i0135 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0135 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0135 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0135 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0135 (target) VALUES (999999999999999999);
INSERT INTO t2_i0135 (target) VALUES (0);
INSERT INTO t2_i0135 (target) VALUES (1);
INSERT INTO t2_i0135 (target) VALUES (-1);
INSERT INTO t2_i0135 (target) VALUES (NULL);
INSERT INTO t2_i0135 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0135 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0135 (target) VALUES (999999999);
INSERT INTO t2_i0135 (target) VALUES (-999999999);
INSERT INTO t2_i0135 (target) VALUES (0);
INSERT INTO t2_i0135 (target) VALUES (1);
INSERT INTO t2_i0135 (target) VALUES (999999999999999999);
INSERT INTO t2_i0135 (target) VALUES (NULL);
SELECT 'TC-I0135' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0135
   WHERE id NOT IN (SELECT id FROM t2_i0135)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0135
   WHERE id NOT IN (SELECT id FROM t1_i0135)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0135 a JOIN t2_i0135 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0136
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0136, t2_i0136;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0136 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0136 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0136 (target) VALUES (999999999999999999);
INSERT INTO t1_i0136 (target) VALUES (0);
INSERT INTO t1_i0136 (target) VALUES (1);
INSERT INTO t1_i0136 (target) VALUES (-1);
INSERT INTO t1_i0136 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0136 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0136 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0136 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0136 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0136 (target) VALUES (-999999999);
INSERT INTO t1_i0136 (target) VALUES (0);
INSERT INTO t1_i0136 (target) VALUES (1);
INSERT INTO t1_i0136 (target) VALUES (999999999999999999);
INSERT INTO t1_i0136 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0136 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0136 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0136 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0136 (target) VALUES (999999999999999999);
INSERT INTO t2_i0136 (target) VALUES (0);
INSERT INTO t2_i0136 (target) VALUES (1);
INSERT INTO t2_i0136 (target) VALUES (-1);
INSERT INTO t2_i0136 (target) VALUES (NULL);
INSERT INTO t2_i0136 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0136 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0136 (target) VALUES (999999999);
INSERT INTO t2_i0136 (target) VALUES (-999999999);
INSERT INTO t2_i0136 (target) VALUES (0);
INSERT INTO t2_i0136 (target) VALUES (1);
INSERT INTO t2_i0136 (target) VALUES (999999999999999999);
INSERT INTO t2_i0136 (target) VALUES (NULL);
SELECT 'TC-I0136' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0136
   WHERE id NOT IN (SELECT id FROM t2_i0136)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0136
   WHERE id NOT IN (SELECT id FROM t1_i0136)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0136 a JOIN t2_i0136 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0137
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0137, t2_i0137;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0137 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0137 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0137 (target) VALUES (999999999999999999);
INSERT INTO t1_i0137 (target) VALUES (0);
INSERT INTO t1_i0137 (target) VALUES (1);
INSERT INTO t1_i0137 (target) VALUES (-1);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0137 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0137 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0137 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0137 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0137 (target) VALUES (-999999999);
INSERT INTO t1_i0137 (target) VALUES (0);
INSERT INTO t1_i0137 (target) VALUES (1);
INSERT INTO t1_i0137 (target) VALUES (999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0137 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0137 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0137 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0137 (target) VALUES (999999999999999999);
INSERT INTO t2_i0137 (target) VALUES (0);
INSERT INTO t2_i0137 (target) VALUES (1);
INSERT INTO t2_i0137 (target) VALUES (-1);
INSERT INTO t2_i0137 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0137 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0137 (target) VALUES (999999999);
INSERT INTO t2_i0137 (target) VALUES (-999999999);
INSERT INTO t2_i0137 (target) VALUES (0);
INSERT INTO t2_i0137 (target) VALUES (1);
INSERT INTO t2_i0137 (target) VALUES (999999999999999999);
SELECT 'TC-I0137' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0137
   WHERE id NOT IN (SELECT id FROM t2_i0137)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0137
   WHERE id NOT IN (SELECT id FROM t1_i0137)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0137 a JOIN t2_i0137 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0138
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0138, t2_i0138;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0138 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0138 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0138 (target) VALUES (999999999999999999);
INSERT INTO t1_i0138 (target) VALUES (0);
INSERT INTO t1_i0138 (target) VALUES (1);
INSERT INTO t1_i0138 (target) VALUES (-1);
INSERT INTO t1_i0138 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0138 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0138 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0138 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0138 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0138 (target) VALUES (-999999999);
INSERT INTO t1_i0138 (target) VALUES (0);
INSERT INTO t1_i0138 (target) VALUES (1);
INSERT INTO t1_i0138 (target) VALUES (999999999999999999);
INSERT INTO t1_i0138 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0138 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0138 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0138 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0138 (target) VALUES (999999999999999999);
INSERT INTO t2_i0138 (target) VALUES (0);
INSERT INTO t2_i0138 (target) VALUES (1);
INSERT INTO t2_i0138 (target) VALUES (-1);
INSERT INTO t2_i0138 (target) VALUES (NULL);
INSERT INTO t2_i0138 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0138 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0138 (target) VALUES (999999999);
INSERT INTO t2_i0138 (target) VALUES (-999999999);
INSERT INTO t2_i0138 (target) VALUES (0);
INSERT INTO t2_i0138 (target) VALUES (1);
INSERT INTO t2_i0138 (target) VALUES (999999999999999999);
INSERT INTO t2_i0138 (target) VALUES (NULL);
SELECT 'TC-I0138' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0138
   WHERE id NOT IN (SELECT id FROM t2_i0138)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0138
   WHERE id NOT IN (SELECT id FROM t1_i0138)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0138 a JOIN t2_i0138 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0139
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0139, t2_i0139;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0139 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0139 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0139 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0139 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0139 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0139 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0139 (target) VALUES (-999999999);
INSERT INTO t1_i0139 (target) VALUES (0);
INSERT INTO t1_i0139 (target) VALUES (1);
INSERT INTO t1_i0139 (target) VALUES (999999999999999999);
INSERT INTO t1_i0139 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0139 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0139 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0139 (target) VALUES (NULL);
INSERT INTO t2_i0139 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0139 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0139 (target) VALUES (999999999);
INSERT INTO t2_i0139 (target) VALUES (-999999999);
INSERT INTO t2_i0139 (target) VALUES (0);
INSERT INTO t2_i0139 (target) VALUES (1);
INSERT INTO t2_i0139 (target) VALUES (999999999999999999);
INSERT INTO t2_i0139 (target) VALUES (NULL);
SELECT 'TC-I0139' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0139
   WHERE id NOT IN (SELECT id FROM t2_i0139)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0139
   WHERE id NOT IN (SELECT id FROM t1_i0139)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0139 a JOIN t2_i0139 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0140
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0140, t2_i0140;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0140 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0140 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0140 (target) VALUES (999999999999999999);
INSERT INTO t1_i0140 (target) VALUES (0);
INSERT INTO t1_i0140 (target) VALUES (1);
INSERT INTO t1_i0140 (target) VALUES (-1);
INSERT INTO t1_i0140 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0140 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0140 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0140 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0140 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0140 (target) VALUES (-999999999);
INSERT INTO t1_i0140 (target) VALUES (0);
INSERT INTO t1_i0140 (target) VALUES (1);
INSERT INTO t1_i0140 (target) VALUES (999999999999999999);
INSERT INTO t1_i0140 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0140 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0140 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0140 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0140 (target) VALUES (999999999999999999);
INSERT INTO t2_i0140 (target) VALUES (0);
INSERT INTO t2_i0140 (target) VALUES (1);
INSERT INTO t2_i0140 (target) VALUES (-1);
INSERT INTO t2_i0140 (target) VALUES (NULL);
INSERT INTO t2_i0140 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0140 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0140 (target) VALUES (999999999);
INSERT INTO t2_i0140 (target) VALUES (-999999999);
INSERT INTO t2_i0140 (target) VALUES (0);
INSERT INTO t2_i0140 (target) VALUES (1);
INSERT INTO t2_i0140 (target) VALUES (999999999999999999);
INSERT INTO t2_i0140 (target) VALUES (NULL);
SELECT 'TC-I0140' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0140
   WHERE id NOT IN (SELECT id FROM t2_i0140)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0140
   WHERE id NOT IN (SELECT id FROM t1_i0140)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0140 a JOIN t2_i0140 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0141
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0141, t2_i0141;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0141 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0141 MODIFY target DECIMAL(20,0) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0141 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0141 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0141' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0141
   WHERE id NOT IN (SELECT id FROM t2_i0141)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0141
   WHERE id NOT IN (SELECT id FROM t1_i0141)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0141 a JOIN t2_i0141 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0142
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0142, t2_i0142;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0142 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0142 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0142 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0142 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0142' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0142
   WHERE id NOT IN (SELECT id FROM t2_i0142)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0142
   WHERE id NOT IN (SELECT id FROM t1_i0142)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0142 a JOIN t2_i0142 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0143
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0143, t2_i0143;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0143 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(18,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0143 MODIFY target DECIMAL(20,0) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0143 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(20,0)
CREATE TABLE t2_i0143 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(20,0) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0143' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0143
   WHERE id NOT IN (SELECT id FROM t2_i0143)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0143
   WHERE id NOT IN (SELECT id FROM t1_i0143)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0143 a JOIN t2_i0143 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0144
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0144, t2_i0144;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0144 (
  target DECIMAL(18,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0144 (target) VALUES (-999999999999999999);
INSERT INTO t1_i0144 (target) VALUES (999999999999999999);
INSERT INTO t1_i0144 (target) VALUES (0);
INSERT INTO t1_i0144 (target) VALUES (1);
INSERT INTO t1_i0144 (target) VALUES (-1);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0144 MODIFY target DECIMAL(20,0), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0144 (target) VALUES (99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0144 (target) VALUES (-99999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0144 (target) VALUES (999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0144 (target) VALUES (-999999999);
INSERT INTO t1_i0144 (target) VALUES (0);
INSERT INTO t1_i0144 (target) VALUES (1);
INSERT INTO t1_i0144 (target) VALUES (999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0144 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999);
-- Oracle table: DECIMAL(18,0)
CREATE TABLE t2_i0144 (
  target DECIMAL(18,0),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0144 (target) VALUES (-999999999999999999);
INSERT INTO t2_i0144 (target) VALUES (999999999999999999);
INSERT INTO t2_i0144 (target) VALUES (0);
INSERT INTO t2_i0144 (target) VALUES (1);
INSERT INTO t2_i0144 (target) VALUES (-1);
INSERT INTO t2_i0144 (target) VALUES (99999999999999999999);
INSERT INTO t2_i0144 (target) VALUES (-99999999999999999999);
INSERT INTO t2_i0144 (target) VALUES (999999999);
INSERT INTO t2_i0144 (target) VALUES (-999999999);
INSERT INTO t2_i0144 (target) VALUES (0);
INSERT INTO t2_i0144 (target) VALUES (1);
INSERT INTO t2_i0144 (target) VALUES (999999999999999999);
SELECT 'TC-I0144' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0144
   WHERE id NOT IN (SELECT id FROM t2_i0144)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0144
   WHERE id NOT IN (SELECT id FROM t1_i0144)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0144 a JOIN t2_i0144 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0145
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(18,0) -> DECIMAL(20,0), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0145, t2_tc_ia0145;
CREATE TABLE t1_tc_ia0145 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(18,0) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0145 (target) VALUES (-999999999999999999);
INSERT INTO t1_tc_ia0145 (target) VALUES (999999999999999999);
INSERT INTO t1_tc_ia0145 (target) VALUES (0);
INSERT INTO t1_tc_ia0145 (target) VALUES (1);
INSERT INTO t1_tc_ia0145 (target) VALUES (-1);
ALTER TABLE t1_tc_ia0145 MODIFY target DECIMAL(20,0) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0145 (target) VALUES (99999999999999999999);
INSERT INTO t1_tc_ia0145 (target) VALUES (-99999999999999999999);
INSERT INTO t1_tc_ia0145 (target) VALUES (999999999);
SELECT 'TC-IA0145' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0145' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-I0146
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0146, t2_i0146;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0146 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0146 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0146 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0146 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0146 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0146 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0146 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0146 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0146 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0146 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0146 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0146 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0146 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0146 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0146 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0146 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0146 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0146 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0146 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0146 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0146 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0146 (target) VALUES (NULL);
INSERT INTO t2_i0146 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0146 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0146 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0146 (target) VALUES (NULL);
SELECT 'TC-I0146' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0146
   WHERE id NOT IN (SELECT id FROM t2_i0146)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0146
   WHERE id NOT IN (SELECT id FROM t1_i0146)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0146 a JOIN t2_i0146 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0147
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0147, t2_i0147;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0147 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_i0147 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0147 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0147 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0147 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0147 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0147 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0147 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0147 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0147 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0147 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0147 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0147 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0147 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0147 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0147 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0147 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0147 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_i0147 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0147 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0147 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0147 (target) VALUES (NULL);
INSERT INTO t2_i0147 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0147 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0147 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0147 (target) VALUES (NULL);
SELECT 'TC-I0147' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0147
   WHERE id NOT IN (SELECT id FROM t2_i0147)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0147
   WHERE id NOT IN (SELECT id FROM t1_i0147)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0147 a JOIN t2_i0147 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0148
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0148, t2_i0148;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0148 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_i0148 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0148 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0148 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0148 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0148 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0148 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0148 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0148 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0148 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0148 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0148 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0148 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0148 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0148 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0148 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0148 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0148 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_i0148 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0148 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0148 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0148 (target) VALUES (NULL);
INSERT INTO t2_i0148 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0148 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0148 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0148 (target) VALUES (NULL);
SELECT 'TC-I0148' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0148
   WHERE id NOT IN (SELECT id FROM t2_i0148)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0148
   WHERE id NOT IN (SELECT id FROM t1_i0148)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0148 a JOIN t2_i0148 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0149
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0149, t2_i0149;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0149 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0149 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0149 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0149 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0149 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0149 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0149 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0149 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0149 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0149 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0149 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0149 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0149 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0149 (target) VALUES (9.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0149 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(31,30)
CREATE TABLE t2_i0149 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0149 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0149 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0149 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0149 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0149 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0149 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0149 (target) VALUES (9.999999999999999999999999999999);
SELECT 'TC-I0149' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0149
   WHERE id NOT IN (SELECT id FROM t2_i0149)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0149
   WHERE id NOT IN (SELECT id FROM t1_i0149)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0149 a JOIN t2_i0149 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0150
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0150, t2_i0150;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0150 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0150 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0150 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0150 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0150 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0150 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0150 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0150 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0150 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0150 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0150 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0150 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0150 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0150 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0150 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0150 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0150 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0150 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0150 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0150 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0150 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0150 (target) VALUES (NULL);
INSERT INTO t2_i0150 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0150 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0150 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0150 (target) VALUES (NULL);
SELECT 'TC-I0150' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0150
   WHERE id NOT IN (SELECT id FROM t2_i0150)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0150
   WHERE id NOT IN (SELECT id FROM t1_i0150)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0150 a JOIN t2_i0150 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0151
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0151, t2_i0151;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0151 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0151 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0151 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0151 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0151 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0151 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0151 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0151 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0151 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0151 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0151 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0151 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0151 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0151 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0151 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0151 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0151 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0151 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0151 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0151 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0151 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0151 (target) VALUES (NULL);
INSERT INTO t2_i0151 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0151 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0151 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0151 (target) VALUES (NULL);
SELECT 'TC-I0151' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0151
   WHERE id NOT IN (SELECT id FROM t2_i0151)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0151
   WHERE id NOT IN (SELECT id FROM t1_i0151)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0151 a JOIN t2_i0151 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0152
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0152, t2_i0152;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0152 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0152 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0152 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0152 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0152 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0152 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0152 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0152 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0152 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0152 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0152 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0152 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0152 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0152 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0152 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0152 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0152 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0152 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0152 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0152 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0152 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0152 (target) VALUES (NULL);
INSERT INTO t2_i0152 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0152 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0152 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0152 (target) VALUES (NULL);
SELECT 'TC-I0152' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0152
   WHERE id NOT IN (SELECT id FROM t2_i0152)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0152
   WHERE id NOT IN (SELECT id FROM t1_i0152)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0152 a JOIN t2_i0152 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0153
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0153, t2_i0153;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0153 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0153 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0153 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0153 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0153 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0153 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0153 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0153 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0153 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0153 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0153 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0153 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0153 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0153 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0153 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0153 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0153 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0153 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0153 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0153 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0153 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0153 (target) VALUES (NULL);
INSERT INTO t2_i0153 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0153 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0153 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0153 (target) VALUES (NULL);
SELECT 'TC-I0153' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0153
   WHERE id NOT IN (SELECT id FROM t2_i0153)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0153
   WHERE id NOT IN (SELECT id FROM t1_i0153)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0153 a JOIN t2_i0153 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0154
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0154, t2_i0154;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0154 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0154 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0154 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0154 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0154 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0154 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0154 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0154 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0154 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0154 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0154 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0154 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0154 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0154 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0154 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0154 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0154 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0154 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0154 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0154 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0154 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0154 (target) VALUES (NULL);
INSERT INTO t2_i0154 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0154 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0154 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0154 (target) VALUES (NULL);
SELECT 'TC-I0154' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0154
   WHERE id NOT IN (SELECT id FROM t2_i0154)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0154
   WHERE id NOT IN (SELECT id FROM t1_i0154)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0154 a JOIN t2_i0154 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0155
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0155, t2_i0155;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0155 (
  target DECIMAL(31,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0155 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0155 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0155 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0155 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0155 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0155 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0155 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0155 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0155 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0155 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0155 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0155 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0155 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0155 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0155 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0155 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0155 (
  target DECIMAL(33,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0155 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0155 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0155 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0155 (target) VALUES (NULL);
INSERT INTO t2_i0155 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0155 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0155 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0155 (target) VALUES (NULL);
SELECT 'TC-I0155' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0155
   WHERE id NOT IN (SELECT id FROM t2_i0155)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0155
   WHERE id NOT IN (SELECT id FROM t1_i0155)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0155 a JOIN t2_i0155 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0156
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_i0156, t2_i0156;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0156 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(31,30), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0156 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0156 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0156 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0156 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0156 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0156 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0156 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0156 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0156 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0156 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0156 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0156 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0156 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0156 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0156 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0156 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0156 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target DECIMAL(33,30), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0156 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0156 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0156 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0156 (target) VALUES (NULL);
INSERT INTO t2_i0156 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0156 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0156 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0156 (target) VALUES (NULL);
SELECT 'TC-I0156' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0156
   WHERE id NOT IN (SELECT id FROM t2_i0156)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0156
   WHERE id NOT IN (SELECT id FROM t1_i0156)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0156 a JOIN t2_i0156 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0157
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0157, t2_i0157;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0157 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0157 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0157 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0157 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0157 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0157 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0157 MODIFY target DECIMAL(33,30) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0157 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0157 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0157 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0157 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0157 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0157 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0157 (target) VALUES (9.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0157 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0157 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0157 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0157 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0157 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0157 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0157 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0157 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0157 (target) VALUES (9.999999999999999999999999999999);
SELECT 'TC-I0157' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0157
   WHERE id NOT IN (SELECT id FROM t2_i0157)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0157
   WHERE id NOT IN (SELECT id FROM t1_i0157)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0157 a JOIN t2_i0157 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0158
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0158, t2_i0158;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0158 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0158 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0158 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0158 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0158 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0158 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0158 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0158 MODIFY target DECIMAL(33,30) DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0158 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0158 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0158 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0158 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0158 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0158 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0158 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0158 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0158 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0158 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0158 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0158 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0158 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0158 (target) VALUES (NULL);
INSERT INTO t2_i0158 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0158 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0158 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0158 (target) VALUES (NULL);
SELECT 'TC-I0158' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0158
   WHERE id NOT IN (SELECT id FROM t2_i0158)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0158
   WHERE id NOT IN (SELECT id FROM t1_i0158)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0158 a JOIN t2_i0158 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0159
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0159, t2_i0159;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0159 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0159 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0159 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0159 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0159 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0159 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0159 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0159 MODIFY target DECIMAL(33,30) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0159 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0159 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0159 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0159 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0159 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0159 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0159 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0159 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0159 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0159 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0159 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0159 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0159 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0159 (target) VALUES (NULL);
INSERT INTO t2_i0159 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0159 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0159 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0159 (target) VALUES (NULL);
SELECT 'TC-I0159' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0159
   WHERE id NOT IN (SELECT id FROM t2_i0159)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0159
   WHERE id NOT IN (SELECT id FROM t1_i0159)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0159 a JOIN t2_i0159 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0160
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0160, t2_i0160;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0160 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0160 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0160 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0160 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0160 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0160 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0160 MODIFY target DECIMAL(33,30) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0160 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0160 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0160 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0160 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0160 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0160 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0160 (target) VALUES (9.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0160 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0160 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0160 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0160 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0160 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0160 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0160 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0160 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0160 (target) VALUES (9.999999999999999999999999999999);
SELECT 'TC-I0160' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0160
   WHERE id NOT IN (SELECT id FROM t2_i0160)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0160
   WHERE id NOT IN (SELECT id FROM t1_i0160)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0160 a JOIN t2_i0160 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0161
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0161, t2_i0161;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0161 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0161 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0161 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0161 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0161 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0161 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0161 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0161 MODIFY target DECIMAL(33,30) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0161 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0161 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0161 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0161 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0161 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0161 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0161 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0161 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0161 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0161 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0161 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0161 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0161 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0161 (target) VALUES (NULL);
INSERT INTO t2_i0161 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0161 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0161 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0161 (target) VALUES (NULL);
SELECT 'TC-I0161' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0161
   WHERE id NOT IN (SELECT id FROM t2_i0161)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0161
   WHERE id NOT IN (SELECT id FROM t1_i0161)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0161 a JOIN t2_i0161 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0162
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0162, t2_i0162;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0162 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0162 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0162 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0162 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0162' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0162
   WHERE id NOT IN (SELECT id FROM t2_i0162)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0162
   WHERE id NOT IN (SELECT id FROM t1_i0162)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0162 a JOIN t2_i0162 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0163
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0163, t2_i0163;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0163 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0163 (target) VALUES (-9.999999999999999999999999999999);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0163 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0163 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0163 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0163 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0163 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0163 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0163 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0163 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0163 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0163 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0163 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0163 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0163 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0163 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0163 (target) VALUES (NULL);
SELECT 'TC-I0163' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0163
   WHERE id NOT IN (SELECT id FROM t2_i0163)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0163
   WHERE id NOT IN (SELECT id FROM t1_i0163)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0163 a JOIN t2_i0163 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0164
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0164, t2_i0164;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0164 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0164 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0164 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0164 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0164 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0164 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0164 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0164 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0164 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0164 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0164 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0164 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0164 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0164 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0164 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0164 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0164 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0164 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0164 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0164 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0164 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0164 (target) VALUES (NULL);
INSERT INTO t2_i0164 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0164 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0164 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0164 (target) VALUES (NULL);
SELECT 'TC-I0164' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0164
   WHERE id NOT IN (SELECT id FROM t2_i0164)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0164
   WHERE id NOT IN (SELECT id FROM t1_i0164)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0164 a JOIN t2_i0164 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0165
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0165, t2_i0165;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0165 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0165 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0165 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0165 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0165 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0165 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0165 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0165 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0165 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0165 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0165 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0165 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0165 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0165 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0165 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0165 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0165 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0165 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0165 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0165 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0165 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0165 (target) VALUES (NULL);
INSERT INTO t2_i0165 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0165 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0165 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0165 (target) VALUES (NULL);
SELECT 'TC-I0165' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0165
   WHERE id NOT IN (SELECT id FROM t2_i0165)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0165
   WHERE id NOT IN (SELECT id FROM t1_i0165)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0165 a JOIN t2_i0165 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0166
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0166, t2_i0166;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0166 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0166 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0166 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0166 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0166 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0166 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0166 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0166 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0166 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0166 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0166 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0166 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0166 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0166 (target) VALUES (9.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0166 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0166 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0166 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0166 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0166 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0166 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0166 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0166 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0166 (target) VALUES (9.999999999999999999999999999999);
SELECT 'TC-I0166' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0166
   WHERE id NOT IN (SELECT id FROM t2_i0166)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0166
   WHERE id NOT IN (SELECT id FROM t1_i0166)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0166 a JOIN t2_i0166 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0167
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0167, t2_i0167;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0167 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0167 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0167 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0167 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0167 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0167 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0167 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0167 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0167 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0167 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0167 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0167 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0167 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0167 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0167 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0167 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0167 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0167 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0167 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0167 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0167 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0167 (target) VALUES (NULL);
INSERT INTO t2_i0167 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0167 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0167 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0167 (target) VALUES (NULL);
SELECT 'TC-I0167' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0167
   WHERE id NOT IN (SELECT id FROM t2_i0167)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0167
   WHERE id NOT IN (SELECT id FROM t1_i0167)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0167 a JOIN t2_i0167 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0168
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0168, t2_i0168;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0168 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0168 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0168 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0168 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0168 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0168 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0168 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0168 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0168 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0168 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0168 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0168 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0168 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0168 (target) VALUES (NULL);
INSERT INTO t2_i0168 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0168 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0168 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0168 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0168 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0168 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0168 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0168 (target) VALUES (NULL);
SELECT 'TC-I0168' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0168
   WHERE id NOT IN (SELECT id FROM t2_i0168)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0168
   WHERE id NOT IN (SELECT id FROM t1_i0168)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0168 a JOIN t2_i0168 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0169
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0169, t2_i0169;
SET SESSION sql_mode = '';
CREATE TABLE t1_i0169 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0169 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0169 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0169 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0169 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0169 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t1_i0169 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0169 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0169 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0169 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0169 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0169 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0169 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0169 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0169 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0169 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0169 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0169 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0169 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0169 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0169 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0169 (target) VALUES (NULL);
INSERT INTO t2_i0169 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0169 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0169 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0169 (target) VALUES (NULL);
SELECT 'TC-I0169' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0169
   WHERE id NOT IN (SELECT id FROM t2_i0169)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0169
   WHERE id NOT IN (SELECT id FROM t1_i0169)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0169 a JOIN t2_i0169 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0170
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0170, t2_i0170;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0170 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0170 MODIFY target DECIMAL(33,30) NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0170 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0170 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0170' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0170
   WHERE id NOT IN (SELECT id FROM t2_i0170)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0170
   WHERE id NOT IN (SELECT id FROM t1_i0170)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0170 a JOIN t2_i0170 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0171
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0171, t2_i0171;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0171 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0171 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0171 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0171 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0171' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0171
   WHERE id NOT IN (SELECT id FROM t2_i0171)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0171
   WHERE id NOT IN (SELECT id FROM t1_i0171)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0171 a JOIN t2_i0171 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0172
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_i0172, t2_i0172;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0172 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(31,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_i0172 MODIFY target DECIMAL(33,30) NOT NULL DEFAULT 0, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0172 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(33,30)
CREATE TABLE t2_i0172 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target DECIMAL(33,30) NOT NULL DEFAULT 0,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-I0172' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0172
   WHERE id NOT IN (SELECT id FROM t2_i0172)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0172
   WHERE id NOT IN (SELECT id FROM t1_i0172)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0172 a JOIN t2_i0172 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-I0173
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_i0173, t2_i0173;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_i0173 (
  target DECIMAL(31,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_i0173 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_i0173 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_i0173 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0173 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_i0173 (target) VALUES (-1.111111111111111111111111111111);
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_i0173 MODIFY target DECIMAL(33,30), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0173 (target) VALUES (999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0173 (target) VALUES (-999.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0173 (target) VALUES (1.999999999999999999999999999999);
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_i0173 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t1_i0173 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_i0173 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t1_i0173 (target) VALUES (9.999999999999999999999999999999);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_i0173 (target) VALUES (9999999999999999999999999999999999999999999999999999999999999999999999.99);
-- Oracle table: DECIMAL(31,30)
CREATE TABLE t2_i0173 (
  target DECIMAL(31,30),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_i0173 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0173 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t2_i0173 (target) VALUES (-1.111111111111111111111111111111);
INSERT INTO t2_i0173 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (1.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (-1.999999999999999999999999999999);
INSERT INTO t2_i0173 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t2_i0173 (target) VALUES (1.000000000000000000000000000000);
INSERT INTO t2_i0173 (target) VALUES (9.999999999999999999999999999999);
SELECT 'TC-I0173' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_i0173
   WHERE id NOT IN (SELECT id FROM t2_i0173)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_i0173
   WHERE id NOT IN (SELECT id FROM t1_i0173)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_i0173 a JOIN t2_i0173 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-IA0174
-- Column attribute preservation: COMMENT
-- Type: DECIMAL(31,30) -> DECIMAL(33,30), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_ia0174, t2_tc_ia0174;
CREATE TABLE t1_tc_ia0174 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target DECIMAL(31,30) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_ia0174 (target) VALUES (-9.999999999999999999999999999999);
INSERT INTO t1_tc_ia0174 (target) VALUES (9.999999999999999999999999999999);
INSERT INTO t1_tc_ia0174 (target) VALUES (0.000000000000000000000000000000);
INSERT INTO t1_tc_ia0174 (target) VALUES (1.111111111111111111111111111111);
INSERT INTO t1_tc_ia0174 (target) VALUES (-1.111111111111111111111111111111);
ALTER TABLE t1_tc_ia0174 MODIFY target DECIMAL(33,30) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_ia0174 (target) VALUES (999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0174 (target) VALUES (-999.999999999999999999999999999999);
INSERT INTO t1_tc_ia0174 (target) VALUES (1.999999999999999999999999999999);
SELECT 'TC-IA0174' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_ia0174' AND column_name='target' AND column_comment='test_comment';

