-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 07: VARCHAR INSTANT

-- Test Case: TC-A0001
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0001, t2_a0001;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0001 (target) VALUES ('');
INSERT INTO t1_a0001 (target) VALUES ('a');
INSERT INTO t1_a0001 (target) VALUES ('x');
INSERT INTO t1_a0001 (target) VALUES ('');
INSERT INTO t1_a0001 (target) VALUES ('a');
INSERT INTO t1_a0001 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0001 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0001 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0001 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0001 (target) VALUES ('ww');
INSERT INTO t1_a0001 (target) VALUES ('');
INSERT INTO t1_a0001 (target) VALUES ('a');
INSERT INTO t1_a0001 (target) VALUES ('x');
INSERT INTO t1_a0001 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0001 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0001 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0001 (target) VALUES ('');
INSERT INTO t2_a0001 (target) VALUES ('a');
INSERT INTO t2_a0001 (target) VALUES ('x');
INSERT INTO t2_a0001 (target) VALUES ('');
INSERT INTO t2_a0001 (target) VALUES ('a');
INSERT INTO t2_a0001 (target) VALUES (NULL);
INSERT INTO t2_a0001 (target) VALUES ('zz');
INSERT INTO t2_a0001 (target) VALUES ('z');
INSERT INTO t2_a0001 (target) VALUES ('ww');
INSERT INTO t2_a0001 (target) VALUES ('');
INSERT INTO t2_a0001 (target) VALUES ('a');
INSERT INTO t2_a0001 (target) VALUES ('x');
INSERT INTO t2_a0001 (target) VALUES (NULL);
SELECT 'TC-A0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0001
   WHERE id NOT IN (SELECT id FROM t2_a0001)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0001
   WHERE id NOT IN (SELECT id FROM t1_a0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0001 a JOIN t2_a0001 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0002
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0002, t2_a0002;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0002 (target) VALUES ('');
INSERT INTO t1_a0002 (target) VALUES ('a');
INSERT INTO t1_a0002 (target) VALUES ('x');
INSERT INTO t1_a0002 (target) VALUES ('');
INSERT INTO t1_a0002 (target) VALUES ('a');
INSERT INTO t1_a0002 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0002 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0002 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0002 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0002 (target) VALUES ('ww');
INSERT INTO t1_a0002 (target) VALUES ('');
INSERT INTO t1_a0002 (target) VALUES ('a');
INSERT INTO t1_a0002 (target) VALUES ('x');
INSERT INTO t1_a0002 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0002 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0002 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0002 (target) VALUES ('');
INSERT INTO t2_a0002 (target) VALUES ('a');
INSERT INTO t2_a0002 (target) VALUES ('x');
INSERT INTO t2_a0002 (target) VALUES ('');
INSERT INTO t2_a0002 (target) VALUES ('a');
INSERT INTO t2_a0002 (target) VALUES (NULL);
INSERT INTO t2_a0002 (target) VALUES ('zz');
INSERT INTO t2_a0002 (target) VALUES ('z');
INSERT INTO t2_a0002 (target) VALUES ('ww');
INSERT INTO t2_a0002 (target) VALUES ('');
INSERT INTO t2_a0002 (target) VALUES ('a');
INSERT INTO t2_a0002 (target) VALUES ('x');
INSERT INTO t2_a0002 (target) VALUES (NULL);
SELECT 'TC-A0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0002
   WHERE id NOT IN (SELECT id FROM t2_a0002)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0002
   WHERE id NOT IN (SELECT id FROM t1_a0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0002 a JOIN t2_a0002 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0003
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0003, t2_a0003;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0003 (target) VALUES ('');
INSERT INTO t1_a0003 (target) VALUES ('a');
INSERT INTO t1_a0003 (target) VALUES ('x');
INSERT INTO t1_a0003 (target) VALUES ('');
INSERT INTO t1_a0003 (target) VALUES ('a');
INSERT INTO t1_a0003 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0003 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0003 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0003 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0003 (target) VALUES ('ww');
INSERT INTO t1_a0003 (target) VALUES ('');
INSERT INTO t1_a0003 (target) VALUES ('a');
INSERT INTO t1_a0003 (target) VALUES ('x');
INSERT INTO t1_a0003 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0003 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0003 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0003 (target) VALUES ('');
INSERT INTO t2_a0003 (target) VALUES ('a');
INSERT INTO t2_a0003 (target) VALUES ('x');
INSERT INTO t2_a0003 (target) VALUES ('');
INSERT INTO t2_a0003 (target) VALUES ('a');
INSERT INTO t2_a0003 (target) VALUES (NULL);
INSERT INTO t2_a0003 (target) VALUES ('zz');
INSERT INTO t2_a0003 (target) VALUES ('z');
INSERT INTO t2_a0003 (target) VALUES ('ww');
INSERT INTO t2_a0003 (target) VALUES ('');
INSERT INTO t2_a0003 (target) VALUES ('a');
INSERT INTO t2_a0003 (target) VALUES ('x');
INSERT INTO t2_a0003 (target) VALUES (NULL);
SELECT 'TC-A0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0003
   WHERE id NOT IN (SELECT id FROM t2_a0003)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0003
   WHERE id NOT IN (SELECT id FROM t1_a0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0003 a JOIN t2_a0003 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0004
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0004, t2_a0004;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0004 (target) VALUES ('');
INSERT INTO t1_a0004 (target) VALUES ('a');
INSERT INTO t1_a0004 (target) VALUES ('x');
INSERT INTO t1_a0004 (target) VALUES ('');
INSERT INTO t1_a0004 (target) VALUES ('a');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0004 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0004 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0004 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0004 (target) VALUES ('ww');
INSERT INTO t1_a0004 (target) VALUES ('');
INSERT INTO t1_a0004 (target) VALUES ('a');
INSERT INTO t1_a0004 (target) VALUES ('x');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0004 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0004 (target) VALUES ('test');
-- Oracle table: VARCHAR(1)
CREATE TABLE t2_a0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0004 (target) VALUES ('');
INSERT INTO t2_a0004 (target) VALUES ('a');
INSERT INTO t2_a0004 (target) VALUES ('x');
INSERT INTO t2_a0004 (target) VALUES ('');
INSERT INTO t2_a0004 (target) VALUES ('a');
INSERT INTO t2_a0004 (target) VALUES ('zz');
INSERT INTO t2_a0004 (target) VALUES ('z');
INSERT INTO t2_a0004 (target) VALUES ('ww');
INSERT INTO t2_a0004 (target) VALUES ('');
INSERT INTO t2_a0004 (target) VALUES ('a');
INSERT INTO t2_a0004 (target) VALUES ('x');
SELECT 'TC-A0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0004
   WHERE id NOT IN (SELECT id FROM t2_a0004)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0004
   WHERE id NOT IN (SELECT id FROM t1_a0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0004 a JOIN t2_a0004 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0005
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0005, t2_a0005;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0005 (target) VALUES ('');
INSERT INTO t1_a0005 (target) VALUES ('a');
INSERT INTO t1_a0005 (target) VALUES ('x');
INSERT INTO t1_a0005 (target) VALUES ('');
INSERT INTO t1_a0005 (target) VALUES ('a');
INSERT INTO t1_a0005 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0005 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0005 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0005 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0005 (target) VALUES ('ww');
INSERT INTO t1_a0005 (target) VALUES ('');
INSERT INTO t1_a0005 (target) VALUES ('a');
INSERT INTO t1_a0005 (target) VALUES ('x');
INSERT INTO t1_a0005 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0005 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0005 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0005 (target) VALUES ('');
INSERT INTO t2_a0005 (target) VALUES ('a');
INSERT INTO t2_a0005 (target) VALUES ('x');
INSERT INTO t2_a0005 (target) VALUES ('');
INSERT INTO t2_a0005 (target) VALUES ('a');
INSERT INTO t2_a0005 (target) VALUES (NULL);
INSERT INTO t2_a0005 (target) VALUES ('zz');
INSERT INTO t2_a0005 (target) VALUES ('z');
INSERT INTO t2_a0005 (target) VALUES ('ww');
INSERT INTO t2_a0005 (target) VALUES ('');
INSERT INTO t2_a0005 (target) VALUES ('a');
INSERT INTO t2_a0005 (target) VALUES ('x');
INSERT INTO t2_a0005 (target) VALUES (NULL);
SELECT 'TC-A0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0005
   WHERE id NOT IN (SELECT id FROM t2_a0005)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0005
   WHERE id NOT IN (SELECT id FROM t1_a0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0005 a JOIN t2_a0005 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0006
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0006, t2_a0006;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0006 (target) VALUES ('');
INSERT INTO t1_a0006 (target) VALUES ('a');
INSERT INTO t1_a0006 (target) VALUES ('x');
INSERT INTO t1_a0006 (target) VALUES ('');
INSERT INTO t1_a0006 (target) VALUES ('a');
INSERT INTO t1_a0006 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0006 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0006 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0006 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0006 (target) VALUES ('ww');
INSERT INTO t1_a0006 (target) VALUES ('');
INSERT INTO t1_a0006 (target) VALUES ('a');
INSERT INTO t1_a0006 (target) VALUES ('x');
INSERT INTO t1_a0006 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0006 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0006 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0006 (target) VALUES ('');
INSERT INTO t2_a0006 (target) VALUES ('a');
INSERT INTO t2_a0006 (target) VALUES ('x');
INSERT INTO t2_a0006 (target) VALUES ('');
INSERT INTO t2_a0006 (target) VALUES ('a');
INSERT INTO t2_a0006 (target) VALUES (NULL);
INSERT INTO t2_a0006 (target) VALUES ('zz');
INSERT INTO t2_a0006 (target) VALUES ('z');
INSERT INTO t2_a0006 (target) VALUES ('ww');
INSERT INTO t2_a0006 (target) VALUES ('');
INSERT INTO t2_a0006 (target) VALUES ('a');
INSERT INTO t2_a0006 (target) VALUES ('x');
INSERT INTO t2_a0006 (target) VALUES (NULL);
SELECT 'TC-A0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0006
   WHERE id NOT IN (SELECT id FROM t2_a0006)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0006
   WHERE id NOT IN (SELECT id FROM t1_a0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0006 a JOIN t2_a0006 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0007
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0007, t2_a0007;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0007 (target) VALUES ('');
INSERT INTO t1_a0007 (target) VALUES ('a');
INSERT INTO t1_a0007 (target) VALUES ('x');
INSERT INTO t1_a0007 (target) VALUES ('');
INSERT INTO t1_a0007 (target) VALUES ('a');
INSERT INTO t1_a0007 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0007 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0007 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0007 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0007 (target) VALUES ('ww');
INSERT INTO t1_a0007 (target) VALUES ('');
INSERT INTO t1_a0007 (target) VALUES ('a');
INSERT INTO t1_a0007 (target) VALUES ('x');
INSERT INTO t1_a0007 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0007 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0007 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0007 (target) VALUES ('');
INSERT INTO t2_a0007 (target) VALUES ('a');
INSERT INTO t2_a0007 (target) VALUES ('x');
INSERT INTO t2_a0007 (target) VALUES ('');
INSERT INTO t2_a0007 (target) VALUES ('a');
INSERT INTO t2_a0007 (target) VALUES (NULL);
INSERT INTO t2_a0007 (target) VALUES ('zz');
INSERT INTO t2_a0007 (target) VALUES ('z');
INSERT INTO t2_a0007 (target) VALUES ('ww');
INSERT INTO t2_a0007 (target) VALUES ('');
INSERT INTO t2_a0007 (target) VALUES ('a');
INSERT INTO t2_a0007 (target) VALUES ('x');
INSERT INTO t2_a0007 (target) VALUES (NULL);
SELECT 'TC-A0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0007
   WHERE id NOT IN (SELECT id FROM t2_a0007)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0007
   WHERE id NOT IN (SELECT id FROM t1_a0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0007 a JOIN t2_a0007 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0008
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0008, t2_a0008;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0008 (target) VALUES ('');
INSERT INTO t1_a0008 (target) VALUES ('a');
INSERT INTO t1_a0008 (target) VALUES ('x');
INSERT INTO t1_a0008 (target) VALUES ('');
INSERT INTO t1_a0008 (target) VALUES ('a');
INSERT INTO t1_a0008 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0008 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0008 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0008 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0008 (target) VALUES ('ww');
INSERT INTO t1_a0008 (target) VALUES ('');
INSERT INTO t1_a0008 (target) VALUES ('a');
INSERT INTO t1_a0008 (target) VALUES ('x');
INSERT INTO t1_a0008 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0008 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0008 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0008 (target) VALUES ('');
INSERT INTO t2_a0008 (target) VALUES ('a');
INSERT INTO t2_a0008 (target) VALUES ('x');
INSERT INTO t2_a0008 (target) VALUES ('');
INSERT INTO t2_a0008 (target) VALUES ('a');
INSERT INTO t2_a0008 (target) VALUES (NULL);
INSERT INTO t2_a0008 (target) VALUES ('zz');
INSERT INTO t2_a0008 (target) VALUES ('z');
INSERT INTO t2_a0008 (target) VALUES ('ww');
INSERT INTO t2_a0008 (target) VALUES ('');
INSERT INTO t2_a0008 (target) VALUES ('a');
INSERT INTO t2_a0008 (target) VALUES ('x');
INSERT INTO t2_a0008 (target) VALUES (NULL);
SELECT 'TC-A0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0008
   WHERE id NOT IN (SELECT id FROM t2_a0008)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0008
   WHERE id NOT IN (SELECT id FROM t1_a0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0008 a JOIN t2_a0008 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0009
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0009, t2_a0009;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0009 (target) VALUES ('');
INSERT INTO t1_a0009 (target) VALUES ('a');
INSERT INTO t1_a0009 (target) VALUES ('x');
INSERT INTO t1_a0009 (target) VALUES ('');
INSERT INTO t1_a0009 (target) VALUES ('a');
INSERT INTO t1_a0009 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0009 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0009 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0009 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0009 (target) VALUES ('ww');
INSERT INTO t1_a0009 (target) VALUES ('');
INSERT INTO t1_a0009 (target) VALUES ('a');
INSERT INTO t1_a0009 (target) VALUES ('x');
INSERT INTO t1_a0009 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0009 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0009 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0009 (target) VALUES ('');
INSERT INTO t2_a0009 (target) VALUES ('a');
INSERT INTO t2_a0009 (target) VALUES ('x');
INSERT INTO t2_a0009 (target) VALUES ('');
INSERT INTO t2_a0009 (target) VALUES ('a');
INSERT INTO t2_a0009 (target) VALUES (NULL);
INSERT INTO t2_a0009 (target) VALUES ('zz');
INSERT INTO t2_a0009 (target) VALUES ('z');
INSERT INTO t2_a0009 (target) VALUES ('ww');
INSERT INTO t2_a0009 (target) VALUES ('');
INSERT INTO t2_a0009 (target) VALUES ('a');
INSERT INTO t2_a0009 (target) VALUES ('x');
INSERT INTO t2_a0009 (target) VALUES (NULL);
SELECT 'TC-A0009' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0009
   WHERE id NOT IN (SELECT id FROM t2_a0009)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0009
   WHERE id NOT IN (SELECT id FROM t1_a0009)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0009 a JOIN t2_a0009 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0010
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0010, t2_a0010;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0010 (
  target VARCHAR(1) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0010 (target) VALUES ('');
INSERT INTO t1_a0010 (target) VALUES ('a');
INSERT INTO t1_a0010 (target) VALUES ('x');
INSERT INTO t1_a0010 (target) VALUES ('');
INSERT INTO t1_a0010 (target) VALUES ('a');
INSERT INTO t1_a0010 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0010 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0010 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0010 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0010 (target) VALUES ('ww');
INSERT INTO t1_a0010 (target) VALUES ('');
INSERT INTO t1_a0010 (target) VALUES ('a');
INSERT INTO t1_a0010 (target) VALUES ('x');
INSERT INTO t1_a0010 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0010 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0010 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0010 (
  target VARCHAR(2) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0010 (target) VALUES ('');
INSERT INTO t2_a0010 (target) VALUES ('a');
INSERT INTO t2_a0010 (target) VALUES ('x');
INSERT INTO t2_a0010 (target) VALUES ('');
INSERT INTO t2_a0010 (target) VALUES ('a');
INSERT INTO t2_a0010 (target) VALUES (NULL);
INSERT INTO t2_a0010 (target) VALUES ('zz');
INSERT INTO t2_a0010 (target) VALUES ('z');
INSERT INTO t2_a0010 (target) VALUES ('ww');
INSERT INTO t2_a0010 (target) VALUES ('');
INSERT INTO t2_a0010 (target) VALUES ('a');
INSERT INTO t2_a0010 (target) VALUES ('x');
INSERT INTO t2_a0010 (target) VALUES (NULL);
SELECT 'TC-A0010' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0010
   WHERE id NOT IN (SELECT id FROM t2_a0010)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0010
   WHERE id NOT IN (SELECT id FROM t1_a0010)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0010 a JOIN t2_a0010 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0011
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0011, t2_a0011;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(1) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0011 (target) VALUES ('');
INSERT INTO t1_a0011 (target) VALUES ('a');
INSERT INTO t1_a0011 (target) VALUES ('x');
INSERT INTO t1_a0011 (target) VALUES ('');
INSERT INTO t1_a0011 (target) VALUES ('a');
INSERT INTO t1_a0011 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0011 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0011 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0011 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0011 (target) VALUES ('ww');
INSERT INTO t1_a0011 (target) VALUES ('');
INSERT INTO t1_a0011 (target) VALUES ('a');
INSERT INTO t1_a0011 (target) VALUES ('x');
INSERT INTO t1_a0011 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0011 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0011 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(2) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0011 (target) VALUES ('');
INSERT INTO t2_a0011 (target) VALUES ('a');
INSERT INTO t2_a0011 (target) VALUES ('x');
INSERT INTO t2_a0011 (target) VALUES ('');
INSERT INTO t2_a0011 (target) VALUES ('a');
INSERT INTO t2_a0011 (target) VALUES (NULL);
INSERT INTO t2_a0011 (target) VALUES ('zz');
INSERT INTO t2_a0011 (target) VALUES ('z');
INSERT INTO t2_a0011 (target) VALUES ('ww');
INSERT INTO t2_a0011 (target) VALUES ('');
INSERT INTO t2_a0011 (target) VALUES ('a');
INSERT INTO t2_a0011 (target) VALUES ('x');
INSERT INTO t2_a0011 (target) VALUES (NULL);
SELECT 'TC-A0011' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0011
   WHERE id NOT IN (SELECT id FROM t2_a0011)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0011
   WHERE id NOT IN (SELECT id FROM t1_a0011)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0011 a JOIN t2_a0011 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0012
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0012, t2_a0012;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0012 (target) VALUES ('');
INSERT INTO t1_a0012 (target) VALUES ('a');
INSERT INTO t1_a0012 (target) VALUES ('x');
INSERT INTO t1_a0012 (target) VALUES ('');
INSERT INTO t1_a0012 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0012 MODIFY target VARCHAR(2) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0012 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0012 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0012 (target) VALUES ('ww');
INSERT INTO t1_a0012 (target) VALUES ('');
INSERT INTO t1_a0012 (target) VALUES ('a');
INSERT INTO t1_a0012 (target) VALUES ('x');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0012 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0012 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0012 (target) VALUES ('');
INSERT INTO t2_a0012 (target) VALUES ('a');
INSERT INTO t2_a0012 (target) VALUES ('x');
INSERT INTO t2_a0012 (target) VALUES ('');
INSERT INTO t2_a0012 (target) VALUES ('a');
INSERT INTO t2_a0012 (target) VALUES ('zz');
INSERT INTO t2_a0012 (target) VALUES ('z');
INSERT INTO t2_a0012 (target) VALUES ('ww');
INSERT INTO t2_a0012 (target) VALUES ('');
INSERT INTO t2_a0012 (target) VALUES ('a');
INSERT INTO t2_a0012 (target) VALUES ('x');
SELECT 'TC-A0012' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0012
   WHERE id NOT IN (SELECT id FROM t2_a0012)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0012
   WHERE id NOT IN (SELECT id FROM t1_a0012)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0012 a JOIN t2_a0012 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0013
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0013, t2_a0013;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0013 (target) VALUES ('');
INSERT INTO t1_a0013 (target) VALUES ('a');
INSERT INTO t1_a0013 (target) VALUES ('x');
INSERT INTO t1_a0013 (target) VALUES ('');
INSERT INTO t1_a0013 (target) VALUES ('a');
INSERT INTO t1_a0013 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0013 MODIFY target VARCHAR(2) CHARACTER SET latin1 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0013 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0013 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0013 (target) VALUES ('ww');
INSERT INTO t1_a0013 (target) VALUES ('');
INSERT INTO t1_a0013 (target) VALUES ('a');
INSERT INTO t1_a0013 (target) VALUES ('x');
INSERT INTO t1_a0013 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0013 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0013 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0013 (target) VALUES ('');
INSERT INTO t2_a0013 (target) VALUES ('a');
INSERT INTO t2_a0013 (target) VALUES ('x');
INSERT INTO t2_a0013 (target) VALUES ('');
INSERT INTO t2_a0013 (target) VALUES ('a');
INSERT INTO t2_a0013 (target) VALUES (NULL);
INSERT INTO t2_a0013 (target) VALUES ('zz');
INSERT INTO t2_a0013 (target) VALUES ('z');
INSERT INTO t2_a0013 (target) VALUES ('ww');
INSERT INTO t2_a0013 (target) VALUES ('');
INSERT INTO t2_a0013 (target) VALUES ('a');
INSERT INTO t2_a0013 (target) VALUES ('x');
INSERT INTO t2_a0013 (target) VALUES (NULL);
SELECT 'TC-A0013' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0013
   WHERE id NOT IN (SELECT id FROM t2_a0013)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0013
   WHERE id NOT IN (SELECT id FROM t1_a0013)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0013 a JOIN t2_a0013 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0014
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0014, t2_a0014;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0014 (target) VALUES ('');
INSERT INTO t1_a0014 (target) VALUES ('a');
INSERT INTO t1_a0014 (target) VALUES ('x');
INSERT INTO t1_a0014 (target) VALUES ('');
INSERT INTO t1_a0014 (target) VALUES ('a');
INSERT INTO t1_a0014 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0014 MODIFY target VARCHAR(2) CHARACTER SET latin1 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0014 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0014 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0014 (target) VALUES ('ww');
INSERT INTO t1_a0014 (target) VALUES ('');
INSERT INTO t1_a0014 (target) VALUES ('a');
INSERT INTO t1_a0014 (target) VALUES ('x');
INSERT INTO t1_a0014 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0014 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0014 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0014 (target) VALUES ('');
INSERT INTO t2_a0014 (target) VALUES ('a');
INSERT INTO t2_a0014 (target) VALUES ('x');
INSERT INTO t2_a0014 (target) VALUES ('');
INSERT INTO t2_a0014 (target) VALUES ('a');
INSERT INTO t2_a0014 (target) VALUES (NULL);
INSERT INTO t2_a0014 (target) VALUES ('zz');
INSERT INTO t2_a0014 (target) VALUES ('z');
INSERT INTO t2_a0014 (target) VALUES ('ww');
INSERT INTO t2_a0014 (target) VALUES ('');
INSERT INTO t2_a0014 (target) VALUES ('a');
INSERT INTO t2_a0014 (target) VALUES ('x');
INSERT INTO t2_a0014 (target) VALUES (NULL);
SELECT 'TC-A0014' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0014
   WHERE id NOT IN (SELECT id FROM t2_a0014)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0014
   WHERE id NOT IN (SELECT id FROM t1_a0014)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0014 a JOIN t2_a0014 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0015
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0015, t2_a0015;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0015 (target) VALUES ('');
INSERT INTO t1_a0015 (target) VALUES ('a');
INSERT INTO t1_a0015 (target) VALUES ('x');
INSERT INTO t1_a0015 (target) VALUES ('');
INSERT INTO t1_a0015 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0015 MODIFY target VARCHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0015 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0015 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0015 (target) VALUES ('ww');
INSERT INTO t1_a0015 (target) VALUES ('');
INSERT INTO t1_a0015 (target) VALUES ('a');
INSERT INTO t1_a0015 (target) VALUES ('x');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0015 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0015 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0015 (target) VALUES ('');
INSERT INTO t2_a0015 (target) VALUES ('a');
INSERT INTO t2_a0015 (target) VALUES ('x');
INSERT INTO t2_a0015 (target) VALUES ('');
INSERT INTO t2_a0015 (target) VALUES ('a');
INSERT INTO t2_a0015 (target) VALUES ('zz');
INSERT INTO t2_a0015 (target) VALUES ('z');
INSERT INTO t2_a0015 (target) VALUES ('ww');
INSERT INTO t2_a0015 (target) VALUES ('');
INSERT INTO t2_a0015 (target) VALUES ('a');
INSERT INTO t2_a0015 (target) VALUES ('x');
SELECT 'TC-A0015' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0015
   WHERE id NOT IN (SELECT id FROM t2_a0015)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0015
   WHERE id NOT IN (SELECT id FROM t1_a0015)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0015 a JOIN t2_a0015 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0016
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0016, t2_a0016;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0016 (target) VALUES ('');
INSERT INTO t1_a0016 (target) VALUES ('a');
INSERT INTO t1_a0016 (target) VALUES ('x');
INSERT INTO t1_a0016 (target) VALUES ('');
INSERT INTO t1_a0016 (target) VALUES ('a');
INSERT INTO t1_a0016 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0016 MODIFY target VARCHAR(2) CHARACTER SET latin1 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0016 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0016 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0016 (target) VALUES ('ww');
INSERT INTO t1_a0016 (target) VALUES ('');
INSERT INTO t1_a0016 (target) VALUES ('a');
INSERT INTO t1_a0016 (target) VALUES ('x');
INSERT INTO t1_a0016 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0016 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0016 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0016 (target) VALUES ('');
INSERT INTO t2_a0016 (target) VALUES ('a');
INSERT INTO t2_a0016 (target) VALUES ('x');
INSERT INTO t2_a0016 (target) VALUES ('');
INSERT INTO t2_a0016 (target) VALUES ('a');
INSERT INTO t2_a0016 (target) VALUES (NULL);
INSERT INTO t2_a0016 (target) VALUES ('zz');
INSERT INTO t2_a0016 (target) VALUES ('z');
INSERT INTO t2_a0016 (target) VALUES ('ww');
INSERT INTO t2_a0016 (target) VALUES ('');
INSERT INTO t2_a0016 (target) VALUES ('a');
INSERT INTO t2_a0016 (target) VALUES ('x');
INSERT INTO t2_a0016 (target) VALUES (NULL);
SELECT 'TC-A0016' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0016
   WHERE id NOT IN (SELECT id FROM t2_a0016)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0016
   WHERE id NOT IN (SELECT id FROM t1_a0016)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0016 a JOIN t2_a0016 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0017
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0017, t2_a0017;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0017 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0017 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0017 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0017' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0017
   WHERE id NOT IN (SELECT id FROM t2_a0017)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0017
   WHERE id NOT IN (SELECT id FROM t1_a0017)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0017 a JOIN t2_a0017 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0018
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0018, t2_a0018;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0018 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0018 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0018 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0018 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0018 (target) VALUES ('ww');
INSERT INTO t1_a0018 (target) VALUES ('');
INSERT INTO t1_a0018 (target) VALUES ('a');
INSERT INTO t1_a0018 (target) VALUES ('x');
INSERT INTO t1_a0018 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0018 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0018 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0018 (target) VALUES ('');
INSERT INTO t2_a0018 (target) VALUES ('zz');
INSERT INTO t2_a0018 (target) VALUES ('z');
INSERT INTO t2_a0018 (target) VALUES ('ww');
INSERT INTO t2_a0018 (target) VALUES ('');
INSERT INTO t2_a0018 (target) VALUES ('a');
INSERT INTO t2_a0018 (target) VALUES ('x');
INSERT INTO t2_a0018 (target) VALUES (NULL);
SELECT 'TC-A0018' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0018
   WHERE id NOT IN (SELECT id FROM t2_a0018)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0018
   WHERE id NOT IN (SELECT id FROM t1_a0018)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0018 a JOIN t2_a0018 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0019
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0019, t2_a0019;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0019 (target) VALUES ('');
INSERT INTO t1_a0019 (target) VALUES ('a');
INSERT INTO t1_a0019 (target) VALUES ('x');
INSERT INTO t1_a0019 (target) VALUES ('');
INSERT INTO t1_a0019 (target) VALUES ('a');
INSERT INTO t1_a0019 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0019 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0019 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0019 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0019 (target) VALUES ('ww');
INSERT INTO t1_a0019 (target) VALUES ('');
INSERT INTO t1_a0019 (target) VALUES ('a');
INSERT INTO t1_a0019 (target) VALUES ('x');
INSERT INTO t1_a0019 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0019 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0019 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0019 (target) VALUES ('');
INSERT INTO t2_a0019 (target) VALUES ('a');
INSERT INTO t2_a0019 (target) VALUES ('x');
INSERT INTO t2_a0019 (target) VALUES ('');
INSERT INTO t2_a0019 (target) VALUES ('a');
INSERT INTO t2_a0019 (target) VALUES (NULL);
INSERT INTO t2_a0019 (target) VALUES ('zz');
INSERT INTO t2_a0019 (target) VALUES ('z');
INSERT INTO t2_a0019 (target) VALUES ('ww');
INSERT INTO t2_a0019 (target) VALUES ('');
INSERT INTO t2_a0019 (target) VALUES ('a');
INSERT INTO t2_a0019 (target) VALUES ('x');
INSERT INTO t2_a0019 (target) VALUES (NULL);
SELECT 'TC-A0019' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0019
   WHERE id NOT IN (SELECT id FROM t2_a0019)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0019
   WHERE id NOT IN (SELECT id FROM t1_a0019)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0019 a JOIN t2_a0019 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0020
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0020, t2_a0020;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0020 (target) VALUES ('');
INSERT INTO t1_a0020 (target) VALUES ('a');
INSERT INTO t1_a0020 (target) VALUES ('x');
INSERT INTO t1_a0020 (target) VALUES ('');
INSERT INTO t1_a0020 (target) VALUES ('a');
INSERT INTO t1_a0020 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0020 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0020 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0020 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0020 (target) VALUES ('ww');
INSERT INTO t1_a0020 (target) VALUES ('');
INSERT INTO t1_a0020 (target) VALUES ('a');
INSERT INTO t1_a0020 (target) VALUES ('x');
INSERT INTO t1_a0020 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0020 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0020 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0020 (target) VALUES ('');
INSERT INTO t2_a0020 (target) VALUES ('a');
INSERT INTO t2_a0020 (target) VALUES ('x');
INSERT INTO t2_a0020 (target) VALUES ('');
INSERT INTO t2_a0020 (target) VALUES ('a');
INSERT INTO t2_a0020 (target) VALUES (NULL);
INSERT INTO t2_a0020 (target) VALUES ('zz');
INSERT INTO t2_a0020 (target) VALUES ('z');
INSERT INTO t2_a0020 (target) VALUES ('ww');
INSERT INTO t2_a0020 (target) VALUES ('');
INSERT INTO t2_a0020 (target) VALUES ('a');
INSERT INTO t2_a0020 (target) VALUES ('x');
INSERT INTO t2_a0020 (target) VALUES (NULL);
SELECT 'TC-A0020' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0020
   WHERE id NOT IN (SELECT id FROM t2_a0020)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0020
   WHERE id NOT IN (SELECT id FROM t1_a0020)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0020 a JOIN t2_a0020 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0021
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0021, t2_a0021;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0021 (target) VALUES ('');
INSERT INTO t1_a0021 (target) VALUES ('a');
INSERT INTO t1_a0021 (target) VALUES ('x');
INSERT INTO t1_a0021 (target) VALUES ('');
INSERT INTO t1_a0021 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0021 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0021 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0021 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0021 (target) VALUES ('ww');
INSERT INTO t1_a0021 (target) VALUES ('');
INSERT INTO t1_a0021 (target) VALUES ('a');
INSERT INTO t1_a0021 (target) VALUES ('x');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0021 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0021 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0021 (target) VALUES ('');
INSERT INTO t2_a0021 (target) VALUES ('a');
INSERT INTO t2_a0021 (target) VALUES ('x');
INSERT INTO t2_a0021 (target) VALUES ('');
INSERT INTO t2_a0021 (target) VALUES ('a');
INSERT INTO t2_a0021 (target) VALUES ('zz');
INSERT INTO t2_a0021 (target) VALUES ('z');
INSERT INTO t2_a0021 (target) VALUES ('ww');
INSERT INTO t2_a0021 (target) VALUES ('');
INSERT INTO t2_a0021 (target) VALUES ('a');
INSERT INTO t2_a0021 (target) VALUES ('x');
SELECT 'TC-A0021' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0021
   WHERE id NOT IN (SELECT id FROM t2_a0021)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0021
   WHERE id NOT IN (SELECT id FROM t1_a0021)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0021 a JOIN t2_a0021 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0022
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0022, t2_a0022;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0022 (target) VALUES ('');
INSERT INTO t1_a0022 (target) VALUES ('a');
INSERT INTO t1_a0022 (target) VALUES ('x');
INSERT INTO t1_a0022 (target) VALUES ('');
INSERT INTO t1_a0022 (target) VALUES ('a');
INSERT INTO t1_a0022 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0022 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0022 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0022 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0022 (target) VALUES ('ww');
INSERT INTO t1_a0022 (target) VALUES ('');
INSERT INTO t1_a0022 (target) VALUES ('a');
INSERT INTO t1_a0022 (target) VALUES ('x');
INSERT INTO t1_a0022 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0022 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0022 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0022 (target) VALUES ('');
INSERT INTO t2_a0022 (target) VALUES ('a');
INSERT INTO t2_a0022 (target) VALUES ('x');
INSERT INTO t2_a0022 (target) VALUES ('');
INSERT INTO t2_a0022 (target) VALUES ('a');
INSERT INTO t2_a0022 (target) VALUES (NULL);
INSERT INTO t2_a0022 (target) VALUES ('zz');
INSERT INTO t2_a0022 (target) VALUES ('z');
INSERT INTO t2_a0022 (target) VALUES ('ww');
INSERT INTO t2_a0022 (target) VALUES ('');
INSERT INTO t2_a0022 (target) VALUES ('a');
INSERT INTO t2_a0022 (target) VALUES ('x');
INSERT INTO t2_a0022 (target) VALUES (NULL);
SELECT 'TC-A0022' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0022
   WHERE id NOT IN (SELECT id FROM t2_a0022)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0022
   WHERE id NOT IN (SELECT id FROM t1_a0022)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0022 a JOIN t2_a0022 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0023
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0023, t2_a0023;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0023 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0023 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0023 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0023 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0023 (target) VALUES ('ww');
INSERT INTO t1_a0023 (target) VALUES ('');
INSERT INTO t1_a0023 (target) VALUES ('a');
INSERT INTO t1_a0023 (target) VALUES ('x');
INSERT INTO t1_a0023 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0023 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0023 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0023 (target) VALUES (NULL);
INSERT INTO t2_a0023 (target) VALUES ('zz');
INSERT INTO t2_a0023 (target) VALUES ('z');
INSERT INTO t2_a0023 (target) VALUES ('ww');
INSERT INTO t2_a0023 (target) VALUES ('');
INSERT INTO t2_a0023 (target) VALUES ('a');
INSERT INTO t2_a0023 (target) VALUES ('x');
INSERT INTO t2_a0023 (target) VALUES (NULL);
SELECT 'TC-A0023' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0023
   WHERE id NOT IN (SELECT id FROM t2_a0023)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0023
   WHERE id NOT IN (SELECT id FROM t1_a0023)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0023 a JOIN t2_a0023 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0024
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0024, t2_a0024;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0024 (target) VALUES ('');
INSERT INTO t1_a0024 (target) VALUES ('a');
INSERT INTO t1_a0024 (target) VALUES ('x');
INSERT INTO t1_a0024 (target) VALUES ('');
INSERT INTO t1_a0024 (target) VALUES ('a');
INSERT INTO t1_a0024 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0024 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0024 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0024 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0024 (target) VALUES ('ww');
INSERT INTO t1_a0024 (target) VALUES ('');
INSERT INTO t1_a0024 (target) VALUES ('a');
INSERT INTO t1_a0024 (target) VALUES ('x');
INSERT INTO t1_a0024 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0024 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0024 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0024 (target) VALUES ('');
INSERT INTO t2_a0024 (target) VALUES ('a');
INSERT INTO t2_a0024 (target) VALUES ('x');
INSERT INTO t2_a0024 (target) VALUES ('');
INSERT INTO t2_a0024 (target) VALUES ('a');
INSERT INTO t2_a0024 (target) VALUES (NULL);
INSERT INTO t2_a0024 (target) VALUES ('zz');
INSERT INTO t2_a0024 (target) VALUES ('z');
INSERT INTO t2_a0024 (target) VALUES ('ww');
INSERT INTO t2_a0024 (target) VALUES ('');
INSERT INTO t2_a0024 (target) VALUES ('a');
INSERT INTO t2_a0024 (target) VALUES ('x');
INSERT INTO t2_a0024 (target) VALUES (NULL);
SELECT 'TC-A0024' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0024
   WHERE id NOT IN (SELECT id FROM t2_a0024)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0024
   WHERE id NOT IN (SELECT id FROM t1_a0024)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0024 a JOIN t2_a0024 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0025
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0025, t2_a0025;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0025 MODIFY target VARCHAR(2) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0025 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0025 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0025' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0025
   WHERE id NOT IN (SELECT id FROM t2_a0025)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0025
   WHERE id NOT IN (SELECT id FROM t1_a0025)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0025 a JOIN t2_a0025 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0026
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0026, t2_a0026;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0026 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0026 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0026 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0026' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0026
   WHERE id NOT IN (SELECT id FROM t2_a0026)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0026
   WHERE id NOT IN (SELECT id FROM t1_a0026)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0026 a JOIN t2_a0026 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0027
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0027, t2_a0027;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(1) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0027 MODIFY target VARCHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0027 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0027 (target) VALUES ('test');
-- Oracle table: VARCHAR(2)
CREATE TABLE t2_a0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0027' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0027
   WHERE id NOT IN (SELECT id FROM t2_a0027)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0027
   WHERE id NOT IN (SELECT id FROM t1_a0027)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0027 a JOIN t2_a0027 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0028
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0028, t2_a0028;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0028 (
  target VARCHAR(1) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0028 (target) VALUES ('');
INSERT INTO t1_a0028 (target) VALUES ('a');
INSERT INTO t1_a0028 (target) VALUES ('x');
INSERT INTO t1_a0028 (target) VALUES ('');
INSERT INTO t1_a0028 (target) VALUES ('a');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0028 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0028 (target) VALUES ('zz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0028 (target) VALUES ('z');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0028 (target) VALUES ('ww');
INSERT INTO t1_a0028 (target) VALUES ('');
INSERT INTO t1_a0028 (target) VALUES ('a');
INSERT INTO t1_a0028 (target) VALUES ('x');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0028 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0028 (target) VALUES ('test');
-- Oracle table: VARCHAR(1)
CREATE TABLE t2_a0028 (
  target VARCHAR(1) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0028 (target) VALUES ('');
INSERT INTO t2_a0028 (target) VALUES ('a');
INSERT INTO t2_a0028 (target) VALUES ('x');
INSERT INTO t2_a0028 (target) VALUES ('');
INSERT INTO t2_a0028 (target) VALUES ('a');
INSERT INTO t2_a0028 (target) VALUES ('zz');
INSERT INTO t2_a0028 (target) VALUES ('z');
INSERT INTO t2_a0028 (target) VALUES ('ww');
INSERT INTO t2_a0028 (target) VALUES ('');
INSERT INTO t2_a0028 (target) VALUES ('a');
INSERT INTO t2_a0028 (target) VALUES ('x');
SELECT 'TC-A0028' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0028
   WHERE id NOT IN (SELECT id FROM t2_a0028)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0028
   WHERE id NOT IN (SELECT id FROM t1_a0028)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0028 a JOIN t2_a0028 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0029
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0029, t2_tc_aa0029;
CREATE TABLE t1_tc_aa0029 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(1) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0029 (target) VALUES ('');
INSERT INTO t1_tc_aa0029 (target) VALUES ('a');
INSERT INTO t1_tc_aa0029 (target) VALUES ('x');
INSERT INTO t1_tc_aa0029 (target) VALUES ('');
INSERT INTO t1_tc_aa0029 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0029 MODIFY target VARCHAR(2) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0029 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0029 (target) VALUES ('z');
INSERT INTO t1_tc_aa0029 (target) VALUES ('ww');
SELECT 'TC-AA0029' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0029' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0030
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0030, t2_tc_aa0030;
CREATE TABLE t1_tc_aa0030 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(1) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0030 (target) VALUES ('');
INSERT INTO t1_tc_aa0030 (target) VALUES ('a');
INSERT INTO t1_tc_aa0030 (target) VALUES ('x');
INSERT INTO t1_tc_aa0030 (target) VALUES ('');
INSERT INTO t1_tc_aa0030 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0030 MODIFY target VARCHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
INSERT INTO t1_tc_aa0030 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0030 (target) VALUES ('z');
INSERT INTO t1_tc_aa0030 (target) VALUES ('ww');
SELECT 'TC-AA0030' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0030' AND column_name='target' AND character_set_name='latin1';

-- Test Case: TC-AA0031
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(1) -> VARCHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0031, t2_tc_aa0031;
CREATE TABLE t1_tc_aa0031 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(1) CHARACTER SET latin1 COLLATE latin1_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0031 (target) VALUES ('');
INSERT INTO t1_tc_aa0031 (target) VALUES ('a');
INSERT INTO t1_tc_aa0031 (target) VALUES ('x');
INSERT INTO t1_tc_aa0031 (target) VALUES ('');
INSERT INTO t1_tc_aa0031 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0031 MODIFY target VARCHAR(2) CHARACTER SET latin1 COLLATE latin1_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0031 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0031 (target) VALUES ('z');
INSERT INTO t1_tc_aa0031 (target) VALUES ('ww');
SELECT 'TC-AA0031' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0031' AND column_name='target' AND collation_name='latin1_bin';

-- Test Case: TC-A0032
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0032, t2_a0032;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0032 (target) VALUES ('');
INSERT INTO t1_a0032 (target) VALUES ('a');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES ('Hello');
INSERT INTO t1_a0032 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0032 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0032 (target) VALUES ('');
INSERT INTO t1_a0032 (target) VALUES ('a');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0032 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0032 (target) VALUES ('');
INSERT INTO t2_a0032 (target) VALUES ('a');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0032 (target) VALUES ('Hello');
INSERT INTO t2_a0032 (target) VALUES (NULL);
INSERT INTO t2_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0032 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0032 (target) VALUES ('');
INSERT INTO t2_a0032 (target) VALUES ('a');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0032 (target) VALUES (NULL);
SELECT 'TC-A0032' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0032
   WHERE id NOT IN (SELECT id FROM t2_a0032)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0032
   WHERE id NOT IN (SELECT id FROM t1_a0032)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0032 a JOIN t2_a0032 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0033
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0033, t2_a0033;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0033 (target) VALUES ('');
INSERT INTO t1_a0033 (target) VALUES ('a');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES ('Hello');
INSERT INTO t1_a0033 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0033 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0033 (target) VALUES ('');
INSERT INTO t1_a0033 (target) VALUES ('a');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0033 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0033 (target) VALUES ('');
INSERT INTO t2_a0033 (target) VALUES ('a');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0033 (target) VALUES ('Hello');
INSERT INTO t2_a0033 (target) VALUES (NULL);
INSERT INTO t2_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0033 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0033 (target) VALUES ('');
INSERT INTO t2_a0033 (target) VALUES ('a');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0033 (target) VALUES (NULL);
SELECT 'TC-A0033' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0033
   WHERE id NOT IN (SELECT id FROM t2_a0033)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0033
   WHERE id NOT IN (SELECT id FROM t1_a0033)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0033 a JOIN t2_a0033 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0034
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0034, t2_a0034;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0034 (target) VALUES ('');
INSERT INTO t1_a0034 (target) VALUES ('a');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES ('Hello');
INSERT INTO t1_a0034 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0034 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0034 (target) VALUES ('');
INSERT INTO t1_a0034 (target) VALUES ('a');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0034 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0034 (target) VALUES ('');
INSERT INTO t2_a0034 (target) VALUES ('a');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0034 (target) VALUES ('Hello');
INSERT INTO t2_a0034 (target) VALUES (NULL);
INSERT INTO t2_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0034 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0034 (target) VALUES ('');
INSERT INTO t2_a0034 (target) VALUES ('a');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0034 (target) VALUES (NULL);
SELECT 'TC-A0034' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0034
   WHERE id NOT IN (SELECT id FROM t2_a0034)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0034
   WHERE id NOT IN (SELECT id FROM t1_a0034)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0034 a JOIN t2_a0034 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0035
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0035, t2_a0035;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0035 (target) VALUES ('');
INSERT INTO t1_a0035 (target) VALUES ('a');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0035 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0035 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0035 (target) VALUES ('');
INSERT INTO t1_a0035 (target) VALUES ('a');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0035 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(254)
CREATE TABLE t2_a0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0035 (target) VALUES ('');
INSERT INTO t2_a0035 (target) VALUES ('a');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0035 (target) VALUES ('Hello');
INSERT INTO t2_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0035 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0035 (target) VALUES ('');
INSERT INTO t2_a0035 (target) VALUES ('a');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0035' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0035
   WHERE id NOT IN (SELECT id FROM t2_a0035)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0035
   WHERE id NOT IN (SELECT id FROM t1_a0035)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0035 a JOIN t2_a0035 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0036
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0036, t2_a0036;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0036 (target) VALUES ('');
INSERT INTO t1_a0036 (target) VALUES ('a');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES ('Hello');
INSERT INTO t1_a0036 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0036 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0036 (target) VALUES ('');
INSERT INTO t1_a0036 (target) VALUES ('a');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0036 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0036 (target) VALUES ('');
INSERT INTO t2_a0036 (target) VALUES ('a');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0036 (target) VALUES ('Hello');
INSERT INTO t2_a0036 (target) VALUES (NULL);
INSERT INTO t2_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0036 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0036 (target) VALUES ('');
INSERT INTO t2_a0036 (target) VALUES ('a');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0036 (target) VALUES (NULL);
SELECT 'TC-A0036' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0036
   WHERE id NOT IN (SELECT id FROM t2_a0036)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0036
   WHERE id NOT IN (SELECT id FROM t1_a0036)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0036 a JOIN t2_a0036 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0037
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0037, t2_a0037;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0037 (target) VALUES ('');
INSERT INTO t1_a0037 (target) VALUES ('a');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES ('Hello');
INSERT INTO t1_a0037 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0037 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0037 (target) VALUES ('');
INSERT INTO t1_a0037 (target) VALUES ('a');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0037 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0037 (target) VALUES ('');
INSERT INTO t2_a0037 (target) VALUES ('a');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0037 (target) VALUES ('Hello');
INSERT INTO t2_a0037 (target) VALUES (NULL);
INSERT INTO t2_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0037 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0037 (target) VALUES ('');
INSERT INTO t2_a0037 (target) VALUES ('a');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0037 (target) VALUES (NULL);
SELECT 'TC-A0037' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0037
   WHERE id NOT IN (SELECT id FROM t2_a0037)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0037
   WHERE id NOT IN (SELECT id FROM t1_a0037)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0037 a JOIN t2_a0037 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0038
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0038, t2_a0038;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0038 (target) VALUES ('');
INSERT INTO t1_a0038 (target) VALUES ('a');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES ('Hello');
INSERT INTO t1_a0038 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0038 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0038 (target) VALUES ('');
INSERT INTO t1_a0038 (target) VALUES ('a');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0038 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0038 (target) VALUES ('');
INSERT INTO t2_a0038 (target) VALUES ('a');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0038 (target) VALUES ('Hello');
INSERT INTO t2_a0038 (target) VALUES (NULL);
INSERT INTO t2_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0038 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0038 (target) VALUES ('');
INSERT INTO t2_a0038 (target) VALUES ('a');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0038 (target) VALUES (NULL);
SELECT 'TC-A0038' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0038
   WHERE id NOT IN (SELECT id FROM t2_a0038)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0038
   WHERE id NOT IN (SELECT id FROM t1_a0038)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0038 a JOIN t2_a0038 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0039
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0039, t2_a0039;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0039 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0039 (target) VALUES ('');
INSERT INTO t1_a0039 (target) VALUES ('a');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES ('Hello');
INSERT INTO t1_a0039 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0039 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0039 (target) VALUES ('');
INSERT INTO t1_a0039 (target) VALUES ('a');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0039 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0039 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0039 (target) VALUES ('');
INSERT INTO t2_a0039 (target) VALUES ('a');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0039 (target) VALUES ('Hello');
INSERT INTO t2_a0039 (target) VALUES (NULL);
INSERT INTO t2_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0039 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0039 (target) VALUES ('');
INSERT INTO t2_a0039 (target) VALUES ('a');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0039 (target) VALUES (NULL);
SELECT 'TC-A0039' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0039
   WHERE id NOT IN (SELECT id FROM t2_a0039)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0039
   WHERE id NOT IN (SELECT id FROM t1_a0039)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0039 a JOIN t2_a0039 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0040
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0040, t2_a0040;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0040 (target) VALUES ('');
INSERT INTO t1_a0040 (target) VALUES ('a');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES ('Hello');
INSERT INTO t1_a0040 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0040 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0040 (target) VALUES ('');
INSERT INTO t1_a0040 (target) VALUES ('a');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0040 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0040 (target) VALUES ('');
INSERT INTO t2_a0040 (target) VALUES ('a');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0040 (target) VALUES ('Hello');
INSERT INTO t2_a0040 (target) VALUES (NULL);
INSERT INTO t2_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0040 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0040 (target) VALUES ('');
INSERT INTO t2_a0040 (target) VALUES ('a');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0040 (target) VALUES (NULL);
SELECT 'TC-A0040' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0040
   WHERE id NOT IN (SELECT id FROM t2_a0040)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0040
   WHERE id NOT IN (SELECT id FROM t1_a0040)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0040 a JOIN t2_a0040 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0041
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0041, t2_a0041;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0041 (
  target VARCHAR(254) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0041 (target) VALUES ('');
INSERT INTO t1_a0041 (target) VALUES ('a');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES ('Hello');
INSERT INTO t1_a0041 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0041 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0041 (target) VALUES ('');
INSERT INTO t1_a0041 (target) VALUES ('a');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0041 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0041 (
  target VARCHAR(255) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0041 (target) VALUES ('');
INSERT INTO t2_a0041 (target) VALUES ('a');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0041 (target) VALUES ('Hello');
INSERT INTO t2_a0041 (target) VALUES (NULL);
INSERT INTO t2_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0041 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0041 (target) VALUES ('');
INSERT INTO t2_a0041 (target) VALUES ('a');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0041 (target) VALUES (NULL);
SELECT 'TC-A0041' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0041
   WHERE id NOT IN (SELECT id FROM t2_a0041)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0041
   WHERE id NOT IN (SELECT id FROM t1_a0041)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0041 a JOIN t2_a0041 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0042
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0042, t2_a0042;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(254) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0042 (target) VALUES ('');
INSERT INTO t1_a0042 (target) VALUES ('a');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES ('Hello');
INSERT INTO t1_a0042 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0042 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0042 (target) VALUES ('');
INSERT INTO t1_a0042 (target) VALUES ('a');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0042 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(255) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0042 (target) VALUES ('');
INSERT INTO t2_a0042 (target) VALUES ('a');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0042 (target) VALUES ('Hello');
INSERT INTO t2_a0042 (target) VALUES (NULL);
INSERT INTO t2_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0042 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0042 (target) VALUES ('');
INSERT INTO t2_a0042 (target) VALUES ('a');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0042 (target) VALUES (NULL);
SELECT 'TC-A0042' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0042
   WHERE id NOT IN (SELECT id FROM t2_a0042)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0042
   WHERE id NOT IN (SELECT id FROM t1_a0042)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0042 a JOIN t2_a0042 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0043
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0043, t2_a0043;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0043 (target) VALUES ('');
INSERT INTO t1_a0043 (target) VALUES ('a');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0043 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0043 MODIFY target VARCHAR(255) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0043 (target) VALUES ('');
INSERT INTO t1_a0043 (target) VALUES ('a');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0043 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0043 (target) VALUES ('');
INSERT INTO t2_a0043 (target) VALUES ('a');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0043 (target) VALUES ('Hello');
INSERT INTO t2_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0043 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0043 (target) VALUES ('');
INSERT INTO t2_a0043 (target) VALUES ('a');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0043' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0043
   WHERE id NOT IN (SELECT id FROM t2_a0043)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0043
   WHERE id NOT IN (SELECT id FROM t1_a0043)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0043 a JOIN t2_a0043 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0044
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0044, t2_a0044;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0044 (target) VALUES ('');
INSERT INTO t1_a0044 (target) VALUES ('a');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES ('Hello');
INSERT INTO t1_a0044 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0044 MODIFY target VARCHAR(255) CHARACTER SET latin1 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0044 (target) VALUES ('');
INSERT INTO t1_a0044 (target) VALUES ('a');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0044 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0044 (target) VALUES ('');
INSERT INTO t2_a0044 (target) VALUES ('a');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0044 (target) VALUES ('Hello');
INSERT INTO t2_a0044 (target) VALUES (NULL);
INSERT INTO t2_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0044 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0044 (target) VALUES ('');
INSERT INTO t2_a0044 (target) VALUES ('a');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0044 (target) VALUES (NULL);
SELECT 'TC-A0044' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0044
   WHERE id NOT IN (SELECT id FROM t2_a0044)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0044
   WHERE id NOT IN (SELECT id FROM t1_a0044)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0044 a JOIN t2_a0044 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0045
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0045, t2_a0045;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0045 (target) VALUES ('');
INSERT INTO t1_a0045 (target) VALUES ('a');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES ('Hello');
INSERT INTO t1_a0045 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0045 MODIFY target VARCHAR(255) CHARACTER SET latin1 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0045 (target) VALUES ('');
INSERT INTO t1_a0045 (target) VALUES ('a');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0045 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0045 (target) VALUES ('');
INSERT INTO t2_a0045 (target) VALUES ('a');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0045 (target) VALUES ('Hello');
INSERT INTO t2_a0045 (target) VALUES (NULL);
INSERT INTO t2_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0045 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0045 (target) VALUES ('');
INSERT INTO t2_a0045 (target) VALUES ('a');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0045 (target) VALUES (NULL);
SELECT 'TC-A0045' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0045
   WHERE id NOT IN (SELECT id FROM t2_a0045)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0045
   WHERE id NOT IN (SELECT id FROM t1_a0045)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0045 a JOIN t2_a0045 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0046
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0046, t2_a0046;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0046 (target) VALUES ('');
INSERT INTO t1_a0046 (target) VALUES ('a');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0046 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0046 MODIFY target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0046 (target) VALUES ('');
INSERT INTO t1_a0046 (target) VALUES ('a');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0046 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0046 (target) VALUES ('');
INSERT INTO t2_a0046 (target) VALUES ('a');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0046 (target) VALUES ('Hello');
INSERT INTO t2_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0046 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0046 (target) VALUES ('');
INSERT INTO t2_a0046 (target) VALUES ('a');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0046' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0046
   WHERE id NOT IN (SELECT id FROM t2_a0046)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0046
   WHERE id NOT IN (SELECT id FROM t1_a0046)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0046 a JOIN t2_a0046 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0047
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0047, t2_a0047;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0047 (target) VALUES ('');
INSERT INTO t1_a0047 (target) VALUES ('a');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES ('Hello');
INSERT INTO t1_a0047 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0047 MODIFY target VARCHAR(255) CHARACTER SET latin1 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0047 (target) VALUES ('');
INSERT INTO t1_a0047 (target) VALUES ('a');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0047 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0047 (target) VALUES ('');
INSERT INTO t2_a0047 (target) VALUES ('a');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0047 (target) VALUES ('Hello');
INSERT INTO t2_a0047 (target) VALUES (NULL);
INSERT INTO t2_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0047 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0047 (target) VALUES ('');
INSERT INTO t2_a0047 (target) VALUES ('a');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0047 (target) VALUES (NULL);
SELECT 'TC-A0047' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0047
   WHERE id NOT IN (SELECT id FROM t2_a0047)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0047
   WHERE id NOT IN (SELECT id FROM t1_a0047)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0047 a JOIN t2_a0047 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0048
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0048, t2_a0048;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0048 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0048 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0048' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0048
   WHERE id NOT IN (SELECT id FROM t2_a0048)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0048
   WHERE id NOT IN (SELECT id FROM t1_a0048)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0048 a JOIN t2_a0048 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0049
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0049, t2_a0049;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0049 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0049 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0049 (target) VALUES ('');
INSERT INTO t1_a0049 (target) VALUES ('a');
INSERT INTO t1_a0049 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0049 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0049 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0049 (target) VALUES ('');
INSERT INTO t2_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0049 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0049 (target) VALUES ('');
INSERT INTO t2_a0049 (target) VALUES ('a');
INSERT INTO t2_a0049 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0049 (target) VALUES (NULL);
SELECT 'TC-A0049' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0049
   WHERE id NOT IN (SELECT id FROM t2_a0049)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0049
   WHERE id NOT IN (SELECT id FROM t1_a0049)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0049 a JOIN t2_a0049 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0050
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0050, t2_a0050;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0050 (target) VALUES ('');
INSERT INTO t1_a0050 (target) VALUES ('a');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES ('Hello');
INSERT INTO t1_a0050 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0050 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0050 (target) VALUES ('');
INSERT INTO t1_a0050 (target) VALUES ('a');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0050 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0050 (target) VALUES ('');
INSERT INTO t2_a0050 (target) VALUES ('a');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0050 (target) VALUES ('Hello');
INSERT INTO t2_a0050 (target) VALUES (NULL);
INSERT INTO t2_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0050 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0050 (target) VALUES ('');
INSERT INTO t2_a0050 (target) VALUES ('a');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0050 (target) VALUES (NULL);
SELECT 'TC-A0050' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0050
   WHERE id NOT IN (SELECT id FROM t2_a0050)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0050
   WHERE id NOT IN (SELECT id FROM t1_a0050)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0050 a JOIN t2_a0050 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0051
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0051, t2_a0051;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0051 (target) VALUES ('');
INSERT INTO t1_a0051 (target) VALUES ('a');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES ('Hello');
INSERT INTO t1_a0051 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0051 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0051 (target) VALUES ('');
INSERT INTO t1_a0051 (target) VALUES ('a');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0051 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0051 (target) VALUES ('');
INSERT INTO t2_a0051 (target) VALUES ('a');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0051 (target) VALUES ('Hello');
INSERT INTO t2_a0051 (target) VALUES (NULL);
INSERT INTO t2_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0051 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0051 (target) VALUES ('');
INSERT INTO t2_a0051 (target) VALUES ('a');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0051 (target) VALUES (NULL);
SELECT 'TC-A0051' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0051
   WHERE id NOT IN (SELECT id FROM t2_a0051)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0051
   WHERE id NOT IN (SELECT id FROM t1_a0051)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0051 a JOIN t2_a0051 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0052
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0052, t2_a0052;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0052 (target) VALUES ('');
INSERT INTO t1_a0052 (target) VALUES ('a');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0052 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0052 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0052 (target) VALUES ('');
INSERT INTO t1_a0052 (target) VALUES ('a');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0052 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0052 (target) VALUES ('');
INSERT INTO t2_a0052 (target) VALUES ('a');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0052 (target) VALUES ('Hello');
INSERT INTO t2_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0052 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0052 (target) VALUES ('');
INSERT INTO t2_a0052 (target) VALUES ('a');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0052' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0052
   WHERE id NOT IN (SELECT id FROM t2_a0052)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0052
   WHERE id NOT IN (SELECT id FROM t1_a0052)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0052 a JOIN t2_a0052 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0053
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0053, t2_a0053;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0053 (target) VALUES ('');
INSERT INTO t1_a0053 (target) VALUES ('a');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES ('Hello');
INSERT INTO t1_a0053 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0053 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0053 (target) VALUES ('');
INSERT INTO t1_a0053 (target) VALUES ('a');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0053 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0053 (target) VALUES ('');
INSERT INTO t2_a0053 (target) VALUES ('a');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0053 (target) VALUES ('Hello');
INSERT INTO t2_a0053 (target) VALUES (NULL);
INSERT INTO t2_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0053 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0053 (target) VALUES ('');
INSERT INTO t2_a0053 (target) VALUES ('a');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0053 (target) VALUES (NULL);
SELECT 'TC-A0053' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0053
   WHERE id NOT IN (SELECT id FROM t2_a0053)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0053
   WHERE id NOT IN (SELECT id FROM t1_a0053)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0053 a JOIN t2_a0053 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0054
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0054, t2_a0054;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0054 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0054 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0054 (target) VALUES ('');
INSERT INTO t1_a0054 (target) VALUES ('a');
INSERT INTO t1_a0054 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0054 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0054 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0054 (target) VALUES (NULL);
INSERT INTO t2_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0054 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0054 (target) VALUES ('');
INSERT INTO t2_a0054 (target) VALUES ('a');
INSERT INTO t2_a0054 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0054 (target) VALUES (NULL);
SELECT 'TC-A0054' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0054
   WHERE id NOT IN (SELECT id FROM t2_a0054)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0054
   WHERE id NOT IN (SELECT id FROM t1_a0054)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0054 a JOIN t2_a0054 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0055
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0055, t2_a0055;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0055 (target) VALUES ('');
INSERT INTO t1_a0055 (target) VALUES ('a');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES ('Hello');
INSERT INTO t1_a0055 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0055 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0055 (target) VALUES ('');
INSERT INTO t1_a0055 (target) VALUES ('a');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0055 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0055 (target) VALUES ('');
INSERT INTO t2_a0055 (target) VALUES ('a');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0055 (target) VALUES ('Hello');
INSERT INTO t2_a0055 (target) VALUES (NULL);
INSERT INTO t2_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0055 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0055 (target) VALUES ('');
INSERT INTO t2_a0055 (target) VALUES ('a');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0055 (target) VALUES (NULL);
SELECT 'TC-A0055' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0055
   WHERE id NOT IN (SELECT id FROM t2_a0055)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0055
   WHERE id NOT IN (SELECT id FROM t1_a0055)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0055 a JOIN t2_a0055 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0056
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0056, t2_a0056;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0056 MODIFY target VARCHAR(255) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0056 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0056' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0056
   WHERE id NOT IN (SELECT id FROM t2_a0056)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0056
   WHERE id NOT IN (SELECT id FROM t1_a0056)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0056 a JOIN t2_a0056 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0057
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0057, t2_a0057;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0057 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0057 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0057 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0057 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0057' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0057
   WHERE id NOT IN (SELECT id FROM t2_a0057)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0057
   WHERE id NOT IN (SELECT id FROM t1_a0057)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0057 a JOIN t2_a0057 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0058
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0058, t2_a0058;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0058 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(254) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0058 MODIFY target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0058 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0058 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0058' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0058
   WHERE id NOT IN (SELECT id FROM t2_a0058)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0058
   WHERE id NOT IN (SELECT id FROM t1_a0058)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0058 a JOIN t2_a0058 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0059
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0059, t2_a0059;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0059 (
  target VARCHAR(254) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0059 (target) VALUES ('');
INSERT INTO t1_a0059 (target) VALUES ('a');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0059 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0059 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0059 (target) VALUES ('');
INSERT INTO t1_a0059 (target) VALUES ('a');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0059 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(254)
CREATE TABLE t2_a0059 (
  target VARCHAR(254) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0059 (target) VALUES ('');
INSERT INTO t2_a0059 (target) VALUES ('a');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0059 (target) VALUES ('Hello');
INSERT INTO t2_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0059 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0059 (target) VALUES ('');
INSERT INTO t2_a0059 (target) VALUES ('a');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0059' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0059
   WHERE id NOT IN (SELECT id FROM t2_a0059)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0059
   WHERE id NOT IN (SELECT id FROM t1_a0059)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0059 a JOIN t2_a0059 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0060
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0060, t2_tc_aa0060;
CREATE TABLE t1_tc_aa0060 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(254) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0060 (target) VALUES ('');
INSERT INTO t1_tc_aa0060 (target) VALUES ('a');
INSERT INTO t1_tc_aa0060 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0060 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0060 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0060 MODIFY target VARCHAR(255) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0060 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0060 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0060 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0060' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0060' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0061
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0061, t2_tc_aa0061;
CREATE TABLE t1_tc_aa0061 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(254) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0061 (target) VALUES ('');
INSERT INTO t1_tc_aa0061 (target) VALUES ('a');
INSERT INTO t1_tc_aa0061 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0061 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0061 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0061 MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=instant;
INSERT INTO t1_tc_aa0061 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0061 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0061 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0061' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0061' AND column_name='target' AND character_set_name='latin1';

-- Test Case: TC-AA0062
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0062, t2_tc_aa0062;
CREATE TABLE t1_tc_aa0062 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(254) CHARACTER SET latin1 COLLATE latin1_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0062 (target) VALUES ('');
INSERT INTO t1_tc_aa0062 (target) VALUES ('a');
INSERT INTO t1_tc_aa0062 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0062 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0062 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0062 MODIFY target VARCHAR(255) CHARACTER SET latin1 COLLATE latin1_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0062 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0062 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0062 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0062' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0062' AND column_name='target' AND collation_name='latin1_bin';

-- Test Case: TC-A0063
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0063, t2_a0063;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0063 (target) VALUES ('');
INSERT INTO t1_a0063 (target) VALUES ('a');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES ('Hello');
INSERT INTO t1_a0063 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0063 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0063 (target) VALUES ('');
INSERT INTO t1_a0063 (target) VALUES ('a');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0063 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0063 (target) VALUES ('');
INSERT INTO t2_a0063 (target) VALUES ('a');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0063 (target) VALUES ('Hello');
INSERT INTO t2_a0063 (target) VALUES (NULL);
INSERT INTO t2_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0063 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0063 (target) VALUES ('');
INSERT INTO t2_a0063 (target) VALUES ('a');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0063 (target) VALUES (NULL);
SELECT 'TC-A0063' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0063
   WHERE id NOT IN (SELECT id FROM t2_a0063)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0063
   WHERE id NOT IN (SELECT id FROM t1_a0063)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0063 a JOIN t2_a0063 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0064
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0064, t2_a0064;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0064 (target) VALUES ('');
INSERT INTO t1_a0064 (target) VALUES ('a');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES ('Hello');
INSERT INTO t1_a0064 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0064 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0064 (target) VALUES ('');
INSERT INTO t1_a0064 (target) VALUES ('a');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0064 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0064 (target) VALUES ('');
INSERT INTO t2_a0064 (target) VALUES ('a');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0064 (target) VALUES ('Hello');
INSERT INTO t2_a0064 (target) VALUES (NULL);
INSERT INTO t2_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0064 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0064 (target) VALUES ('');
INSERT INTO t2_a0064 (target) VALUES ('a');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0064 (target) VALUES (NULL);
SELECT 'TC-A0064' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0064
   WHERE id NOT IN (SELECT id FROM t2_a0064)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0064
   WHERE id NOT IN (SELECT id FROM t1_a0064)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0064 a JOIN t2_a0064 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0065
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0065, t2_a0065;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0065 (target) VALUES ('');
INSERT INTO t1_a0065 (target) VALUES ('a');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES ('Hello');
INSERT INTO t1_a0065 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0065 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0065 (target) VALUES ('');
INSERT INTO t1_a0065 (target) VALUES ('a');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0065 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t2_a0065 (target) VALUES ('');
INSERT INTO t2_a0065 (target) VALUES ('a');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0065 (target) VALUES ('Hello');
INSERT INTO t2_a0065 (target) VALUES (NULL);
INSERT INTO t2_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0065 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0065 (target) VALUES ('');
INSERT INTO t2_a0065 (target) VALUES ('a');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0065 (target) VALUES (NULL);
SELECT 'TC-A0065' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0065
   WHERE id NOT IN (SELECT id FROM t2_a0065)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0065
   WHERE id NOT IN (SELECT id FROM t1_a0065)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0065 a JOIN t2_a0065 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0066
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0066, t2_a0066;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0066 (target) VALUES ('');
INSERT INTO t1_a0066 (target) VALUES ('a');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0066 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0066 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0066 (target) VALUES ('');
INSERT INTO t1_a0066 (target) VALUES ('a');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0066 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0066 (target) VALUES ('');
INSERT INTO t2_a0066 (target) VALUES ('a');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0066 (target) VALUES ('Hello');
INSERT INTO t2_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0066 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0066 (target) VALUES ('');
INSERT INTO t2_a0066 (target) VALUES ('a');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0066' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0066
   WHERE id NOT IN (SELECT id FROM t2_a0066)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0066
   WHERE id NOT IN (SELECT id FROM t1_a0066)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0066 a JOIN t2_a0066 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0067
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0067, t2_a0067;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0067 (target) VALUES ('');
INSERT INTO t1_a0067 (target) VALUES ('a');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES ('Hello');
INSERT INTO t1_a0067 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0067 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0067 (target) VALUES ('');
INSERT INTO t1_a0067 (target) VALUES ('a');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0067 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0067 (target) VALUES ('');
INSERT INTO t2_a0067 (target) VALUES ('a');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0067 (target) VALUES ('Hello');
INSERT INTO t2_a0067 (target) VALUES (NULL);
INSERT INTO t2_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0067 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0067 (target) VALUES ('');
INSERT INTO t2_a0067 (target) VALUES ('a');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0067 (target) VALUES (NULL);
SELECT 'TC-A0067' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0067
   WHERE id NOT IN (SELECT id FROM t2_a0067)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0067
   WHERE id NOT IN (SELECT id FROM t1_a0067)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0067 a JOIN t2_a0067 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0068
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0068, t2_a0068;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0068 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0068 (target) VALUES ('');
INSERT INTO t1_a0068 (target) VALUES ('a');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES ('Hello');
INSERT INTO t1_a0068 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0068 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0068 (target) VALUES ('');
INSERT INTO t1_a0068 (target) VALUES ('a');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0068 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0068 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0068 (target) VALUES ('');
INSERT INTO t2_a0068 (target) VALUES ('a');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0068 (target) VALUES ('Hello');
INSERT INTO t2_a0068 (target) VALUES (NULL);
INSERT INTO t2_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0068 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0068 (target) VALUES ('');
INSERT INTO t2_a0068 (target) VALUES ('a');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0068 (target) VALUES (NULL);
SELECT 'TC-A0068' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0068
   WHERE id NOT IN (SELECT id FROM t2_a0068)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0068
   WHERE id NOT IN (SELECT id FROM t1_a0068)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0068 a JOIN t2_a0068 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0069
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0069, t2_a0069;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0069 (target) VALUES ('');
INSERT INTO t1_a0069 (target) VALUES ('a');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES ('Hello');
INSERT INTO t1_a0069 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0069 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0069 (target) VALUES ('');
INSERT INTO t1_a0069 (target) VALUES ('a');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0069 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0069 (target) VALUES ('');
INSERT INTO t2_a0069 (target) VALUES ('a');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0069 (target) VALUES ('Hello');
INSERT INTO t2_a0069 (target) VALUES (NULL);
INSERT INTO t2_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0069 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0069 (target) VALUES ('');
INSERT INTO t2_a0069 (target) VALUES ('a');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0069 (target) VALUES (NULL);
SELECT 'TC-A0069' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0069
   WHERE id NOT IN (SELECT id FROM t2_a0069)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0069
   WHERE id NOT IN (SELECT id FROM t1_a0069)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0069 a JOIN t2_a0069 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0070
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0070, t2_a0070;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0070 (target) VALUES ('');
INSERT INTO t1_a0070 (target) VALUES ('a');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES ('Hello');
INSERT INTO t1_a0070 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0070 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0070 (target) VALUES ('');
INSERT INTO t1_a0070 (target) VALUES ('a');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0070 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0070 (target) VALUES ('');
INSERT INTO t2_a0070 (target) VALUES ('a');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0070 (target) VALUES ('Hello');
INSERT INTO t2_a0070 (target) VALUES (NULL);
INSERT INTO t2_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0070 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0070 (target) VALUES ('');
INSERT INTO t2_a0070 (target) VALUES ('a');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0070 (target) VALUES (NULL);
SELECT 'TC-A0070' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0070
   WHERE id NOT IN (SELECT id FROM t2_a0070)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0070
   WHERE id NOT IN (SELECT id FROM t1_a0070)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0070 a JOIN t2_a0070 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0071
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0071, t2_a0071;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0071 (target) VALUES ('');
INSERT INTO t1_a0071 (target) VALUES ('a');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES ('Hello');
INSERT INTO t1_a0071 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0071 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0071 (target) VALUES ('');
INSERT INTO t1_a0071 (target) VALUES ('a');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0071 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0071 (target) VALUES ('');
INSERT INTO t2_a0071 (target) VALUES ('a');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0071 (target) VALUES ('Hello');
INSERT INTO t2_a0071 (target) VALUES (NULL);
INSERT INTO t2_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0071 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0071 (target) VALUES ('');
INSERT INTO t2_a0071 (target) VALUES ('a');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0071 (target) VALUES (NULL);
SELECT 'TC-A0071' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0071
   WHERE id NOT IN (SELECT id FROM t2_a0071)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0071
   WHERE id NOT IN (SELECT id FROM t1_a0071)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0071 a JOIN t2_a0071 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0072
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0072, t2_a0072;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0072 (
  target VARCHAR(255) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0072 (target) VALUES ('');
INSERT INTO t1_a0072 (target) VALUES ('a');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES ('Hello');
INSERT INTO t1_a0072 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0072 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0072 (target) VALUES ('');
INSERT INTO t1_a0072 (target) VALUES ('a');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0072 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0072 (
  target VARCHAR(256) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0072 (target) VALUES ('');
INSERT INTO t2_a0072 (target) VALUES ('a');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0072 (target) VALUES ('Hello');
INSERT INTO t2_a0072 (target) VALUES (NULL);
INSERT INTO t2_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0072 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0072 (target) VALUES ('');
INSERT INTO t2_a0072 (target) VALUES ('a');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0072 (target) VALUES (NULL);
SELECT 'TC-A0072' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0072
   WHERE id NOT IN (SELECT id FROM t2_a0072)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0072
   WHERE id NOT IN (SELECT id FROM t1_a0072)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0072 a JOIN t2_a0072 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0073
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0073, t2_a0073;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(255) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0073 (target) VALUES ('');
INSERT INTO t1_a0073 (target) VALUES ('a');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES ('Hello');
INSERT INTO t1_a0073 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0073 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0073 (target) VALUES ('');
INSERT INTO t1_a0073 (target) VALUES ('a');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0073 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(256) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0073 (target) VALUES ('');
INSERT INTO t2_a0073 (target) VALUES ('a');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0073 (target) VALUES ('Hello');
INSERT INTO t2_a0073 (target) VALUES (NULL);
INSERT INTO t2_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0073 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0073 (target) VALUES ('');
INSERT INTO t2_a0073 (target) VALUES ('a');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0073 (target) VALUES (NULL);
SELECT 'TC-A0073' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0073
   WHERE id NOT IN (SELECT id FROM t2_a0073)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0073
   WHERE id NOT IN (SELECT id FROM t1_a0073)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0073 a JOIN t2_a0073 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0074
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0074, t2_a0074;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0074 (target) VALUES ('');
INSERT INTO t1_a0074 (target) VALUES ('a');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0074 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0074 MODIFY target VARCHAR(256) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0074 (target) VALUES ('');
INSERT INTO t1_a0074 (target) VALUES ('a');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0074 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0074 (target) VALUES ('');
INSERT INTO t2_a0074 (target) VALUES ('a');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0074 (target) VALUES ('Hello');
INSERT INTO t2_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0074 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0074 (target) VALUES ('');
INSERT INTO t2_a0074 (target) VALUES ('a');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0074' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0074
   WHERE id NOT IN (SELECT id FROM t2_a0074)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0074
   WHERE id NOT IN (SELECT id FROM t1_a0074)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0074 a JOIN t2_a0074 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0075
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0075, t2_a0075;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0075 (target) VALUES ('');
INSERT INTO t1_a0075 (target) VALUES ('a');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES ('Hello');
INSERT INTO t1_a0075 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0075 MODIFY target VARCHAR(256) CHARACTER SET latin1 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0075 (target) VALUES ('');
INSERT INTO t1_a0075 (target) VALUES ('a');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0075 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0075 (target) VALUES ('');
INSERT INTO t2_a0075 (target) VALUES ('a');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0075 (target) VALUES ('Hello');
INSERT INTO t2_a0075 (target) VALUES (NULL);
INSERT INTO t2_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0075 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0075 (target) VALUES ('');
INSERT INTO t2_a0075 (target) VALUES ('a');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0075 (target) VALUES (NULL);
SELECT 'TC-A0075' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0075
   WHERE id NOT IN (SELECT id FROM t2_a0075)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0075
   WHERE id NOT IN (SELECT id FROM t1_a0075)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0075 a JOIN t2_a0075 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0076
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0076, t2_a0076;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0076 (target) VALUES ('');
INSERT INTO t1_a0076 (target) VALUES ('a');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES ('Hello');
INSERT INTO t1_a0076 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0076 MODIFY target VARCHAR(256) CHARACTER SET latin1 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0076 (target) VALUES ('');
INSERT INTO t1_a0076 (target) VALUES ('a');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0076 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0076 (target) VALUES ('');
INSERT INTO t2_a0076 (target) VALUES ('a');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0076 (target) VALUES ('Hello');
INSERT INTO t2_a0076 (target) VALUES (NULL);
INSERT INTO t2_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0076 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0076 (target) VALUES ('');
INSERT INTO t2_a0076 (target) VALUES ('a');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0076 (target) VALUES (NULL);
SELECT 'TC-A0076' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0076
   WHERE id NOT IN (SELECT id FROM t2_a0076)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0076
   WHERE id NOT IN (SELECT id FROM t1_a0076)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0076 a JOIN t2_a0076 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0077
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0077, t2_a0077;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0077 (target) VALUES ('');
INSERT INTO t1_a0077 (target) VALUES ('a');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0077 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0077 MODIFY target VARCHAR(256) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0077 (target) VALUES ('');
INSERT INTO t1_a0077 (target) VALUES ('a');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0077 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0077 (target) VALUES ('');
INSERT INTO t2_a0077 (target) VALUES ('a');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0077 (target) VALUES ('Hello');
INSERT INTO t2_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0077 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0077 (target) VALUES ('');
INSERT INTO t2_a0077 (target) VALUES ('a');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0077' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0077
   WHERE id NOT IN (SELECT id FROM t2_a0077)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0077
   WHERE id NOT IN (SELECT id FROM t1_a0077)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0077 a JOIN t2_a0077 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0078
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0078, t2_a0078;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0078 (target) VALUES ('');
INSERT INTO t1_a0078 (target) VALUES ('a');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES ('Hello');
INSERT INTO t1_a0078 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0078 MODIFY target VARCHAR(256) CHARACTER SET latin1 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0078 (target) VALUES ('');
INSERT INTO t1_a0078 (target) VALUES ('a');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0078 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0078 (target) VALUES ('');
INSERT INTO t2_a0078 (target) VALUES ('a');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0078 (target) VALUES ('Hello');
INSERT INTO t2_a0078 (target) VALUES (NULL);
INSERT INTO t2_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0078 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0078 (target) VALUES ('');
INSERT INTO t2_a0078 (target) VALUES ('a');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0078 (target) VALUES (NULL);
SELECT 'TC-A0078' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0078
   WHERE id NOT IN (SELECT id FROM t2_a0078)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0078
   WHERE id NOT IN (SELECT id FROM t1_a0078)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0078 a JOIN t2_a0078 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0079
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0079, t2_a0079;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0079 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0079 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0079' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0079
   WHERE id NOT IN (SELECT id FROM t2_a0079)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0079
   WHERE id NOT IN (SELECT id FROM t1_a0079)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0079 a JOIN t2_a0079 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0080
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0080, t2_a0080;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0080 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0080 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0080 (target) VALUES ('');
INSERT INTO t1_a0080 (target) VALUES ('a');
INSERT INTO t1_a0080 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0080 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0080 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0080 (target) VALUES ('');
INSERT INTO t2_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0080 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0080 (target) VALUES ('');
INSERT INTO t2_a0080 (target) VALUES ('a');
INSERT INTO t2_a0080 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0080 (target) VALUES (NULL);
SELECT 'TC-A0080' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0080
   WHERE id NOT IN (SELECT id FROM t2_a0080)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0080
   WHERE id NOT IN (SELECT id FROM t1_a0080)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0080 a JOIN t2_a0080 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0081
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0081, t2_a0081;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0081 (target) VALUES ('');
INSERT INTO t1_a0081 (target) VALUES ('a');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES ('Hello');
INSERT INTO t1_a0081 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0081 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0081 (target) VALUES ('');
INSERT INTO t1_a0081 (target) VALUES ('a');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0081 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0081 (target) VALUES ('');
INSERT INTO t2_a0081 (target) VALUES ('a');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0081 (target) VALUES ('Hello');
INSERT INTO t2_a0081 (target) VALUES (NULL);
INSERT INTO t2_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0081 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0081 (target) VALUES ('');
INSERT INTO t2_a0081 (target) VALUES ('a');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0081 (target) VALUES (NULL);
SELECT 'TC-A0081' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0081
   WHERE id NOT IN (SELECT id FROM t2_a0081)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0081
   WHERE id NOT IN (SELECT id FROM t1_a0081)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0081 a JOIN t2_a0081 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0082
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0082, t2_a0082;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0082 (target) VALUES ('');
INSERT INTO t1_a0082 (target) VALUES ('a');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES ('Hello');
INSERT INTO t1_a0082 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0082 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0082 (target) VALUES ('');
INSERT INTO t1_a0082 (target) VALUES ('a');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0082 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0082 (target) VALUES ('');
INSERT INTO t2_a0082 (target) VALUES ('a');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0082 (target) VALUES ('Hello');
INSERT INTO t2_a0082 (target) VALUES (NULL);
INSERT INTO t2_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0082 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0082 (target) VALUES ('');
INSERT INTO t2_a0082 (target) VALUES ('a');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0082 (target) VALUES (NULL);
SELECT 'TC-A0082' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0082
   WHERE id NOT IN (SELECT id FROM t2_a0082)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0082
   WHERE id NOT IN (SELECT id FROM t1_a0082)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0082 a JOIN t2_a0082 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0083
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0083, t2_a0083;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0083 (target) VALUES ('');
INSERT INTO t1_a0083 (target) VALUES ('a');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0083 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0083 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0083 (target) VALUES ('');
INSERT INTO t1_a0083 (target) VALUES ('a');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0083 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0083 (target) VALUES ('');
INSERT INTO t2_a0083 (target) VALUES ('a');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0083 (target) VALUES ('Hello');
INSERT INTO t2_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0083 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0083 (target) VALUES ('');
INSERT INTO t2_a0083 (target) VALUES ('a');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0083' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0083
   WHERE id NOT IN (SELECT id FROM t2_a0083)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0083
   WHERE id NOT IN (SELECT id FROM t1_a0083)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0083 a JOIN t2_a0083 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0084
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0084, t2_a0084;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0084 (target) VALUES ('');
INSERT INTO t1_a0084 (target) VALUES ('a');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES ('Hello');
INSERT INTO t1_a0084 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0084 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0084 (target) VALUES ('');
INSERT INTO t1_a0084 (target) VALUES ('a');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0084 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0084 (target) VALUES ('');
INSERT INTO t2_a0084 (target) VALUES ('a');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0084 (target) VALUES ('Hello');
INSERT INTO t2_a0084 (target) VALUES (NULL);
INSERT INTO t2_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0084 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0084 (target) VALUES ('');
INSERT INTO t2_a0084 (target) VALUES ('a');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0084 (target) VALUES (NULL);
SELECT 'TC-A0084' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0084
   WHERE id NOT IN (SELECT id FROM t2_a0084)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0084
   WHERE id NOT IN (SELECT id FROM t1_a0084)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0084 a JOIN t2_a0084 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0085
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0085, t2_a0085;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0085 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0085 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0085 (target) VALUES ('');
INSERT INTO t1_a0085 (target) VALUES ('a');
INSERT INTO t1_a0085 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0085 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0085 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0085 (target) VALUES (NULL);
INSERT INTO t2_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0085 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0085 (target) VALUES ('');
INSERT INTO t2_a0085 (target) VALUES ('a');
INSERT INTO t2_a0085 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0085 (target) VALUES (NULL);
SELECT 'TC-A0085' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0085
   WHERE id NOT IN (SELECT id FROM t2_a0085)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0085
   WHERE id NOT IN (SELECT id FROM t1_a0085)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0085 a JOIN t2_a0085 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0086
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0086, t2_a0086;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0086 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0086 (target) VALUES ('');
INSERT INTO t1_a0086 (target) VALUES ('a');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES ('Hello');
INSERT INTO t1_a0086 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0086 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0086 (target) VALUES ('');
INSERT INTO t1_a0086 (target) VALUES ('a');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0086 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0086 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0086 (target) VALUES ('');
INSERT INTO t2_a0086 (target) VALUES ('a');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0086 (target) VALUES ('Hello');
INSERT INTO t2_a0086 (target) VALUES (NULL);
INSERT INTO t2_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0086 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0086 (target) VALUES ('');
INSERT INTO t2_a0086 (target) VALUES ('a');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0086 (target) VALUES (NULL);
SELECT 'TC-A0086' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0086
   WHERE id NOT IN (SELECT id FROM t2_a0086)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0086
   WHERE id NOT IN (SELECT id FROM t1_a0086)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0086 a JOIN t2_a0086 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0087
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0087, t2_a0087;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0087 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0087 MODIFY target VARCHAR(256) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0087 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0087 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0087' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0087
   WHERE id NOT IN (SELECT id FROM t2_a0087)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0087
   WHERE id NOT IN (SELECT id FROM t1_a0087)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0087 a JOIN t2_a0087 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0088
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0088, t2_a0088;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0088 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0088 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0088' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0088
   WHERE id NOT IN (SELECT id FROM t2_a0088)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0088
   WHERE id NOT IN (SELECT id FROM t1_a0088)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0088 a JOIN t2_a0088 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0089
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0089, t2_a0089;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(255) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0089 MODIFY target VARCHAR(256) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0089 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(256)
CREATE TABLE t2_a0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(256) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
SELECT 'TC-A0089' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0089
   WHERE id NOT IN (SELECT id FROM t2_a0089)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0089
   WHERE id NOT IN (SELECT id FROM t1_a0089)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0089 a JOIN t2_a0089 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0090
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0090, t2_a0090;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0090 (
  target VARCHAR(255) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0090 (target) VALUES ('');
INSERT INTO t1_a0090 (target) VALUES ('a');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0090 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0090 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0090 (target) VALUES ('');
INSERT INTO t1_a0090 (target) VALUES ('a');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0090 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(255)
CREATE TABLE t2_a0090 (
  target VARCHAR(255) CHARACTER SET latin1,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t2_a0090 (target) VALUES ('');
INSERT INTO t2_a0090 (target) VALUES ('a');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0090 (target) VALUES ('Hello');
INSERT INTO t2_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0090 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0090 (target) VALUES ('');
INSERT INTO t2_a0090 (target) VALUES ('a');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0090' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0090
   WHERE id NOT IN (SELECT id FROM t2_a0090)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0090
   WHERE id NOT IN (SELECT id FROM t1_a0090)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0090 a JOIN t2_a0090 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0091
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0091, t2_tc_aa0091;
CREATE TABLE t1_tc_aa0091 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(255) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0091 (target) VALUES ('');
INSERT INTO t1_tc_aa0091 (target) VALUES ('a');
INSERT INTO t1_tc_aa0091 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0091 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0091 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0091 MODIFY target VARCHAR(256) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0091 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0091 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0091 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0091' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0091' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0092
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0092, t2_tc_aa0092;
CREATE TABLE t1_tc_aa0092 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0092 (target) VALUES ('');
INSERT INTO t1_tc_aa0092 (target) VALUES ('a');
INSERT INTO t1_tc_aa0092 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0092 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0092 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0092 MODIFY target VARCHAR(256) CHARACTER SET latin1, ALGORITHM=instant;
INSERT INTO t1_tc_aa0092 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0092 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0092 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0092' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0092' AND column_name='target' AND character_set_name='latin1';

-- Test Case: TC-AA0093
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(255) -> VARCHAR(256), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0093, t2_tc_aa0093;
CREATE TABLE t1_tc_aa0093 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(255) CHARACTER SET latin1 COLLATE latin1_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0093 (target) VALUES ('');
INSERT INTO t1_tc_aa0093 (target) VALUES ('a');
INSERT INTO t1_tc_aa0093 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0093 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0093 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0093 MODIFY target VARCHAR(256) CHARACTER SET latin1 COLLATE latin1_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0093 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0093 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0093 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0093' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0093' AND column_name='target' AND collation_name='latin1_bin';

-- Test Case: TC-A0094
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0094, t2_a0094;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0094 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0094 (target) VALUES ('');
INSERT INTO t1_a0094 (target) VALUES ('a');
INSERT INTO t1_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0094 (target) VALUES ('Hello');
INSERT INTO t1_a0094 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0094 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0094 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0094 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0094 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0094 (target) VALUES ('');
INSERT INTO t1_a0094 (target) VALUES ('a');
INSERT INTO t1_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0094 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0094 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0094 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0094 (target) VALUES ('');
INSERT INTO t2_a0094 (target) VALUES ('a');
INSERT INTO t2_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0094 (target) VALUES ('Hello');
INSERT INTO t2_a0094 (target) VALUES (NULL);
INSERT INTO t2_a0094 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0094 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0094 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0094 (target) VALUES ('');
INSERT INTO t2_a0094 (target) VALUES ('a');
INSERT INTO t2_a0094 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0094 (target) VALUES (NULL);
SELECT 'TC-A0094' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0094
   WHERE id NOT IN (SELECT id FROM t2_a0094)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0094
   WHERE id NOT IN (SELECT id FROM t1_a0094)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0094 a JOIN t2_a0094 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0095
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0095, t2_a0095;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0095 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8;
INSERT INTO t1_a0095 (target) VALUES ('');
INSERT INTO t1_a0095 (target) VALUES ('a');
INSERT INTO t1_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0095 (target) VALUES ('Hello');
INSERT INTO t1_a0095 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0095 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0095 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0095 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0095 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0095 (target) VALUES ('');
INSERT INTO t1_a0095 (target) VALUES ('a');
INSERT INTO t1_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0095 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0095 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0095 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8;
INSERT INTO t2_a0095 (target) VALUES ('');
INSERT INTO t2_a0095 (target) VALUES ('a');
INSERT INTO t2_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0095 (target) VALUES ('Hello');
INSERT INTO t2_a0095 (target) VALUES (NULL);
INSERT INTO t2_a0095 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0095 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0095 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0095 (target) VALUES ('');
INSERT INTO t2_a0095 (target) VALUES ('a');
INSERT INTO t2_a0095 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0095 (target) VALUES (NULL);
SELECT 'TC-A0095' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0095
   WHERE id NOT IN (SELECT id FROM t2_a0095)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0095
   WHERE id NOT IN (SELECT id FROM t1_a0095)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0095 a JOIN t2_a0095 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0096
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0096, t2_a0096;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0096 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8;
INSERT INTO t1_a0096 (target) VALUES ('');
INSERT INTO t1_a0096 (target) VALUES ('a');
INSERT INTO t1_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0096 (target) VALUES ('Hello');
INSERT INTO t1_a0096 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0096 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0096 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0096 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0096 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0096 (target) VALUES ('');
INSERT INTO t1_a0096 (target) VALUES ('a');
INSERT INTO t1_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0096 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0096 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0096 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8;
INSERT INTO t2_a0096 (target) VALUES ('');
INSERT INTO t2_a0096 (target) VALUES ('a');
INSERT INTO t2_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0096 (target) VALUES ('Hello');
INSERT INTO t2_a0096 (target) VALUES (NULL);
INSERT INTO t2_a0096 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0096 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0096 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0096 (target) VALUES ('');
INSERT INTO t2_a0096 (target) VALUES ('a');
INSERT INTO t2_a0096 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0096 (target) VALUES (NULL);
SELECT 'TC-A0096' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0096
   WHERE id NOT IN (SELECT id FROM t2_a0096)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0096
   WHERE id NOT IN (SELECT id FROM t1_a0096)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0096 a JOIN t2_a0096 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0097
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0097, t2_a0097;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0097 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0097 (target) VALUES ('');
INSERT INTO t1_a0097 (target) VALUES ('a');
INSERT INTO t1_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0097 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0097 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0097 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0097 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0097 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0097 (target) VALUES ('');
INSERT INTO t1_a0097 (target) VALUES ('a');
INSERT INTO t1_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0097 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(85)
CREATE TABLE t2_a0097 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0097 (target) VALUES ('');
INSERT INTO t2_a0097 (target) VALUES ('a');
INSERT INTO t2_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0097 (target) VALUES ('Hello');
INSERT INTO t2_a0097 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0097 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0097 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0097 (target) VALUES ('');
INSERT INTO t2_a0097 (target) VALUES ('a');
INSERT INTO t2_a0097 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0097' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0097
   WHERE id NOT IN (SELECT id FROM t2_a0097)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0097
   WHERE id NOT IN (SELECT id FROM t1_a0097)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0097 a JOIN t2_a0097 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0098
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0098, t2_a0098;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0098 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0098 (target) VALUES ('');
INSERT INTO t1_a0098 (target) VALUES ('a');
INSERT INTO t1_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0098 (target) VALUES ('Hello');
INSERT INTO t1_a0098 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0098 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0098 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0098 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0098 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0098 (target) VALUES ('');
INSERT INTO t1_a0098 (target) VALUES ('a');
INSERT INTO t1_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0098 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0098 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0098 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0098 (target) VALUES ('');
INSERT INTO t2_a0098 (target) VALUES ('a');
INSERT INTO t2_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0098 (target) VALUES ('Hello');
INSERT INTO t2_a0098 (target) VALUES (NULL);
INSERT INTO t2_a0098 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0098 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0098 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0098 (target) VALUES ('');
INSERT INTO t2_a0098 (target) VALUES ('a');
INSERT INTO t2_a0098 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0098 (target) VALUES (NULL);
SELECT 'TC-A0098' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0098
   WHERE id NOT IN (SELECT id FROM t2_a0098)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0098
   WHERE id NOT IN (SELECT id FROM t1_a0098)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0098 a JOIN t2_a0098 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0099
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0099, t2_a0099;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0099 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0099 (target) VALUES ('');
INSERT INTO t1_a0099 (target) VALUES ('a');
INSERT INTO t1_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0099 (target) VALUES ('Hello');
INSERT INTO t1_a0099 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0099 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0099 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0099 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0099 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0099 (target) VALUES ('');
INSERT INTO t1_a0099 (target) VALUES ('a');
INSERT INTO t1_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0099 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0099 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0099 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0099 (target) VALUES ('');
INSERT INTO t2_a0099 (target) VALUES ('a');
INSERT INTO t2_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0099 (target) VALUES ('Hello');
INSERT INTO t2_a0099 (target) VALUES (NULL);
INSERT INTO t2_a0099 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0099 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0099 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0099 (target) VALUES ('');
INSERT INTO t2_a0099 (target) VALUES ('a');
INSERT INTO t2_a0099 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0099 (target) VALUES (NULL);
SELECT 'TC-A0099' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0099
   WHERE id NOT IN (SELECT id FROM t2_a0099)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0099
   WHERE id NOT IN (SELECT id FROM t1_a0099)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0099 a JOIN t2_a0099 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0100
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0100, t2_a0100;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0100 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0100 (target) VALUES ('');
INSERT INTO t1_a0100 (target) VALUES ('a');
INSERT INTO t1_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0100 (target) VALUES ('Hello');
INSERT INTO t1_a0100 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0100 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0100 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0100 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0100 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0100 (target) VALUES ('');
INSERT INTO t1_a0100 (target) VALUES ('a');
INSERT INTO t1_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0100 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0100 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0100 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0100 (target) VALUES ('');
INSERT INTO t2_a0100 (target) VALUES ('a');
INSERT INTO t2_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0100 (target) VALUES ('Hello');
INSERT INTO t2_a0100 (target) VALUES (NULL);
INSERT INTO t2_a0100 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0100 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0100 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0100 (target) VALUES ('');
INSERT INTO t2_a0100 (target) VALUES ('a');
INSERT INTO t2_a0100 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0100 (target) VALUES (NULL);
SELECT 'TC-A0100' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0100
   WHERE id NOT IN (SELECT id FROM t2_a0100)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0100
   WHERE id NOT IN (SELECT id FROM t1_a0100)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0100 a JOIN t2_a0100 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0101
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0101, t2_a0101;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0101 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0101 (target) VALUES ('');
INSERT INTO t1_a0101 (target) VALUES ('a');
INSERT INTO t1_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0101 (target) VALUES ('Hello');
INSERT INTO t1_a0101 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0101 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0101 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0101 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0101 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0101 (target) VALUES ('');
INSERT INTO t1_a0101 (target) VALUES ('a');
INSERT INTO t1_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0101 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0101 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0101 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0101 (target) VALUES ('');
INSERT INTO t2_a0101 (target) VALUES ('a');
INSERT INTO t2_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0101 (target) VALUES ('Hello');
INSERT INTO t2_a0101 (target) VALUES (NULL);
INSERT INTO t2_a0101 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0101 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0101 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0101 (target) VALUES ('');
INSERT INTO t2_a0101 (target) VALUES ('a');
INSERT INTO t2_a0101 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0101 (target) VALUES (NULL);
SELECT 'TC-A0101' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0101
   WHERE id NOT IN (SELECT id FROM t2_a0101)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0101
   WHERE id NOT IN (SELECT id FROM t1_a0101)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0101 a JOIN t2_a0101 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0102
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0102, t2_a0102;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0102 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0102 (target) VALUES ('');
INSERT INTO t1_a0102 (target) VALUES ('a');
INSERT INTO t1_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0102 (target) VALUES ('Hello');
INSERT INTO t1_a0102 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0102 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0102 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0102 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0102 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0102 (target) VALUES ('');
INSERT INTO t1_a0102 (target) VALUES ('a');
INSERT INTO t1_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0102 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0102 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0102 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0102 (target) VALUES ('');
INSERT INTO t2_a0102 (target) VALUES ('a');
INSERT INTO t2_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0102 (target) VALUES ('Hello');
INSERT INTO t2_a0102 (target) VALUES (NULL);
INSERT INTO t2_a0102 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0102 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0102 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0102 (target) VALUES ('');
INSERT INTO t2_a0102 (target) VALUES ('a');
INSERT INTO t2_a0102 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0102 (target) VALUES (NULL);
SELECT 'TC-A0102' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0102
   WHERE id NOT IN (SELECT id FROM t2_a0102)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0102
   WHERE id NOT IN (SELECT id FROM t1_a0102)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0102 a JOIN t2_a0102 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0103
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0103, t2_a0103;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0103 (
  target VARCHAR(85) CHARACTER SET utf8,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0103 (target) VALUES ('');
INSERT INTO t1_a0103 (target) VALUES ('a');
INSERT INTO t1_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0103 (target) VALUES ('Hello');
INSERT INTO t1_a0103 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0103 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0103 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0103 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0103 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0103 (target) VALUES ('');
INSERT INTO t1_a0103 (target) VALUES ('a');
INSERT INTO t1_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0103 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0103 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0103 (
  target VARCHAR(86) CHARACTER SET utf8,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0103 (target) VALUES ('');
INSERT INTO t2_a0103 (target) VALUES ('a');
INSERT INTO t2_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0103 (target) VALUES ('Hello');
INSERT INTO t2_a0103 (target) VALUES (NULL);
INSERT INTO t2_a0103 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0103 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0103 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0103 (target) VALUES ('');
INSERT INTO t2_a0103 (target) VALUES ('a');
INSERT INTO t2_a0103 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0103 (target) VALUES (NULL);
SELECT 'TC-A0103' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0103
   WHERE id NOT IN (SELECT id FROM t2_a0103)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0103
   WHERE id NOT IN (SELECT id FROM t1_a0103)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0103 a JOIN t2_a0103 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0104
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0104, t2_a0104;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0104 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(85) CHARACTER SET utf8, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0104 (target) VALUES ('');
INSERT INTO t1_a0104 (target) VALUES ('a');
INSERT INTO t1_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0104 (target) VALUES ('Hello');
INSERT INTO t1_a0104 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0104 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0104 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0104 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0104 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0104 (target) VALUES ('');
INSERT INTO t1_a0104 (target) VALUES ('a');
INSERT INTO t1_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0104 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0104 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0104 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(86) CHARACTER SET utf8, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0104 (target) VALUES ('');
INSERT INTO t2_a0104 (target) VALUES ('a');
INSERT INTO t2_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0104 (target) VALUES ('Hello');
INSERT INTO t2_a0104 (target) VALUES (NULL);
INSERT INTO t2_a0104 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0104 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0104 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0104 (target) VALUES ('');
INSERT INTO t2_a0104 (target) VALUES ('a');
INSERT INTO t2_a0104 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0104 (target) VALUES (NULL);
SELECT 'TC-A0104' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0104
   WHERE id NOT IN (SELECT id FROM t2_a0104)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0104
   WHERE id NOT IN (SELECT id FROM t1_a0104)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0104 a JOIN t2_a0104 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0105
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0105, t2_a0105;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0105 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0105 (target) VALUES ('');
INSERT INTO t1_a0105 (target) VALUES ('a');
INSERT INTO t1_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0105 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0105 MODIFY target VARCHAR(86) CHARACTER SET utf8 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0105 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0105 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0105 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0105 (target) VALUES ('');
INSERT INTO t1_a0105 (target) VALUES ('a');
INSERT INTO t1_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0105 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0105 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0105 (target) VALUES ('');
INSERT INTO t2_a0105 (target) VALUES ('a');
INSERT INTO t2_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0105 (target) VALUES ('Hello');
INSERT INTO t2_a0105 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0105 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0105 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0105 (target) VALUES ('');
INSERT INTO t2_a0105 (target) VALUES ('a');
INSERT INTO t2_a0105 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0105' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0105
   WHERE id NOT IN (SELECT id FROM t2_a0105)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0105
   WHERE id NOT IN (SELECT id FROM t1_a0105)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0105 a JOIN t2_a0105 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0106
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0106, t2_a0106;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0106 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0106 (target) VALUES ('');
INSERT INTO t1_a0106 (target) VALUES ('a');
INSERT INTO t1_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0106 (target) VALUES ('Hello');
INSERT INTO t1_a0106 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0106 MODIFY target VARCHAR(86) CHARACTER SET utf8 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0106 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0106 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0106 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0106 (target) VALUES ('');
INSERT INTO t1_a0106 (target) VALUES ('a');
INSERT INTO t1_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0106 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0106 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0106 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0106 (target) VALUES ('');
INSERT INTO t2_a0106 (target) VALUES ('a');
INSERT INTO t2_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0106 (target) VALUES ('Hello');
INSERT INTO t2_a0106 (target) VALUES (NULL);
INSERT INTO t2_a0106 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0106 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0106 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0106 (target) VALUES ('');
INSERT INTO t2_a0106 (target) VALUES ('a');
INSERT INTO t2_a0106 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0106 (target) VALUES (NULL);
SELECT 'TC-A0106' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0106
   WHERE id NOT IN (SELECT id FROM t2_a0106)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0106
   WHERE id NOT IN (SELECT id FROM t1_a0106)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0106 a JOIN t2_a0106 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0107
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0107, t2_a0107;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0107 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0107 (target) VALUES ('');
INSERT INTO t1_a0107 (target) VALUES ('a');
INSERT INTO t1_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0107 (target) VALUES ('Hello');
INSERT INTO t1_a0107 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0107 MODIFY target VARCHAR(86) CHARACTER SET utf8 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0107 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0107 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0107 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0107 (target) VALUES ('');
INSERT INTO t1_a0107 (target) VALUES ('a');
INSERT INTO t1_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0107 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0107 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0107 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0107 (target) VALUES ('');
INSERT INTO t2_a0107 (target) VALUES ('a');
INSERT INTO t2_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0107 (target) VALUES ('Hello');
INSERT INTO t2_a0107 (target) VALUES (NULL);
INSERT INTO t2_a0107 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0107 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0107 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0107 (target) VALUES ('');
INSERT INTO t2_a0107 (target) VALUES ('a');
INSERT INTO t2_a0107 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0107 (target) VALUES (NULL);
SELECT 'TC-A0107' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0107
   WHERE id NOT IN (SELECT id FROM t2_a0107)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0107
   WHERE id NOT IN (SELECT id FROM t1_a0107)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0107 a JOIN t2_a0107 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0108
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0108, t2_a0108;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0108 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0108 (target) VALUES ('');
INSERT INTO t1_a0108 (target) VALUES ('a');
INSERT INTO t1_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0108 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0108 MODIFY target VARCHAR(86) CHARACTER SET utf8 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0108 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0108 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0108 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0108 (target) VALUES ('');
INSERT INTO t1_a0108 (target) VALUES ('a');
INSERT INTO t1_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0108 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0108 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0108 (target) VALUES ('');
INSERT INTO t2_a0108 (target) VALUES ('a');
INSERT INTO t2_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0108 (target) VALUES ('Hello');
INSERT INTO t2_a0108 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0108 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0108 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0108 (target) VALUES ('');
INSERT INTO t2_a0108 (target) VALUES ('a');
INSERT INTO t2_a0108 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0108' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0108
   WHERE id NOT IN (SELECT id FROM t2_a0108)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0108
   WHERE id NOT IN (SELECT id FROM t1_a0108)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0108 a JOIN t2_a0108 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0109
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0109, t2_a0109;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0109 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0109 (target) VALUES ('');
INSERT INTO t1_a0109 (target) VALUES ('a');
INSERT INTO t1_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0109 (target) VALUES ('Hello');
INSERT INTO t1_a0109 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0109 MODIFY target VARCHAR(86) CHARACTER SET utf8 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0109 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0109 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0109 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0109 (target) VALUES ('');
INSERT INTO t1_a0109 (target) VALUES ('a');
INSERT INTO t1_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0109 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0109 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0109 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0109 (target) VALUES ('');
INSERT INTO t2_a0109 (target) VALUES ('a');
INSERT INTO t2_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0109 (target) VALUES ('Hello');
INSERT INTO t2_a0109 (target) VALUES (NULL);
INSERT INTO t2_a0109 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0109 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0109 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0109 (target) VALUES ('');
INSERT INTO t2_a0109 (target) VALUES ('a');
INSERT INTO t2_a0109 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0109 (target) VALUES (NULL);
SELECT 'TC-A0109' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0109
   WHERE id NOT IN (SELECT id FROM t2_a0109)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0109
   WHERE id NOT IN (SELECT id FROM t1_a0109)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0109 a JOIN t2_a0109 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0110
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0110, t2_a0110;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0110 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0110 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0110 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0110 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
SELECT 'TC-A0110' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0110
   WHERE id NOT IN (SELECT id FROM t2_a0110)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0110
   WHERE id NOT IN (SELECT id FROM t1_a0110)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0110 a JOIN t2_a0110 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0111
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0111, t2_a0111;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0111 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0111 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0111 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0111 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0111 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0111 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0111 (target) VALUES ('');
INSERT INTO t1_a0111 (target) VALUES ('a');
INSERT INTO t1_a0111 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0111 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0111 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0111 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0111 (target) VALUES ('');
INSERT INTO t2_a0111 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0111 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0111 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0111 (target) VALUES ('');
INSERT INTO t2_a0111 (target) VALUES ('a');
INSERT INTO t2_a0111 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0111 (target) VALUES (NULL);
SELECT 'TC-A0111' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0111
   WHERE id NOT IN (SELECT id FROM t2_a0111)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0111
   WHERE id NOT IN (SELECT id FROM t1_a0111)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0111 a JOIN t2_a0111 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0112
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0112, t2_a0112;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0112 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0112 (target) VALUES ('');
INSERT INTO t1_a0112 (target) VALUES ('a');
INSERT INTO t1_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0112 (target) VALUES ('Hello');
INSERT INTO t1_a0112 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0112 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0112 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0112 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0112 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0112 (target) VALUES ('');
INSERT INTO t1_a0112 (target) VALUES ('a');
INSERT INTO t1_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0112 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0112 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0112 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0112 (target) VALUES ('');
INSERT INTO t2_a0112 (target) VALUES ('a');
INSERT INTO t2_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0112 (target) VALUES ('Hello');
INSERT INTO t2_a0112 (target) VALUES (NULL);
INSERT INTO t2_a0112 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0112 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0112 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0112 (target) VALUES ('');
INSERT INTO t2_a0112 (target) VALUES ('a');
INSERT INTO t2_a0112 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0112 (target) VALUES (NULL);
SELECT 'TC-A0112' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0112
   WHERE id NOT IN (SELECT id FROM t2_a0112)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0112
   WHERE id NOT IN (SELECT id FROM t1_a0112)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0112 a JOIN t2_a0112 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0113
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0113, t2_a0113;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0113 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0113 (target) VALUES ('');
INSERT INTO t1_a0113 (target) VALUES ('a');
INSERT INTO t1_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0113 (target) VALUES ('Hello');
INSERT INTO t1_a0113 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0113 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0113 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0113 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0113 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0113 (target) VALUES ('');
INSERT INTO t1_a0113 (target) VALUES ('a');
INSERT INTO t1_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0113 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0113 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0113 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0113 (target) VALUES ('');
INSERT INTO t2_a0113 (target) VALUES ('a');
INSERT INTO t2_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0113 (target) VALUES ('Hello');
INSERT INTO t2_a0113 (target) VALUES (NULL);
INSERT INTO t2_a0113 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0113 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0113 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0113 (target) VALUES ('');
INSERT INTO t2_a0113 (target) VALUES ('a');
INSERT INTO t2_a0113 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0113 (target) VALUES (NULL);
SELECT 'TC-A0113' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0113
   WHERE id NOT IN (SELECT id FROM t2_a0113)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0113
   WHERE id NOT IN (SELECT id FROM t1_a0113)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0113 a JOIN t2_a0113 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0114
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0114, t2_a0114;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0114 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0114 (target) VALUES ('');
INSERT INTO t1_a0114 (target) VALUES ('a');
INSERT INTO t1_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0114 (target) VALUES ('Hello');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0114 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0114 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0114 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0114 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0114 (target) VALUES ('');
INSERT INTO t1_a0114 (target) VALUES ('a');
INSERT INTO t1_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0114 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0114 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0114 (target) VALUES ('');
INSERT INTO t2_a0114 (target) VALUES ('a');
INSERT INTO t2_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0114 (target) VALUES ('Hello');
INSERT INTO t2_a0114 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0114 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0114 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0114 (target) VALUES ('');
INSERT INTO t2_a0114 (target) VALUES ('a');
INSERT INTO t2_a0114 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0114' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0114
   WHERE id NOT IN (SELECT id FROM t2_a0114)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0114
   WHERE id NOT IN (SELECT id FROM t1_a0114)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0114 a JOIN t2_a0114 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0115
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0115, t2_a0115;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0115 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0115 (target) VALUES ('');
INSERT INTO t1_a0115 (target) VALUES ('a');
INSERT INTO t1_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0115 (target) VALUES ('Hello');
INSERT INTO t1_a0115 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0115 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0115 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0115 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0115 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0115 (target) VALUES ('');
INSERT INTO t1_a0115 (target) VALUES ('a');
INSERT INTO t1_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0115 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0115 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0115 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0115 (target) VALUES ('');
INSERT INTO t2_a0115 (target) VALUES ('a');
INSERT INTO t2_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0115 (target) VALUES ('Hello');
INSERT INTO t2_a0115 (target) VALUES (NULL);
INSERT INTO t2_a0115 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0115 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0115 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0115 (target) VALUES ('');
INSERT INTO t2_a0115 (target) VALUES ('a');
INSERT INTO t2_a0115 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0115 (target) VALUES (NULL);
SELECT 'TC-A0115' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0115
   WHERE id NOT IN (SELECT id FROM t2_a0115)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0115
   WHERE id NOT IN (SELECT id FROM t1_a0115)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0115 a JOIN t2_a0115 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0116
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0116, t2_a0116;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0116 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0116 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0116 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0116 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0116 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0116 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0116 (target) VALUES ('');
INSERT INTO t1_a0116 (target) VALUES ('a');
INSERT INTO t1_a0116 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0116 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0116 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0116 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0116 (target) VALUES (NULL);
INSERT INTO t2_a0116 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0116 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0116 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0116 (target) VALUES ('');
INSERT INTO t2_a0116 (target) VALUES ('a');
INSERT INTO t2_a0116 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0116 (target) VALUES (NULL);
SELECT 'TC-A0116' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0116
   WHERE id NOT IN (SELECT id FROM t2_a0116)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0116
   WHERE id NOT IN (SELECT id FROM t1_a0116)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0116 a JOIN t2_a0116 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0117
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0117, t2_a0117;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0117 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0117 (target) VALUES ('');
INSERT INTO t1_a0117 (target) VALUES ('a');
INSERT INTO t1_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0117 (target) VALUES ('Hello');
INSERT INTO t1_a0117 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0117 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0117 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0117 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0117 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0117 (target) VALUES ('');
INSERT INTO t1_a0117 (target) VALUES ('a');
INSERT INTO t1_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0117 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0117 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0117 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0117 (target) VALUES ('');
INSERT INTO t2_a0117 (target) VALUES ('a');
INSERT INTO t2_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0117 (target) VALUES ('Hello');
INSERT INTO t2_a0117 (target) VALUES (NULL);
INSERT INTO t2_a0117 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0117 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0117 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0117 (target) VALUES ('');
INSERT INTO t2_a0117 (target) VALUES ('a');
INSERT INTO t2_a0117 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0117 (target) VALUES (NULL);
SELECT 'TC-A0117' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0117
   WHERE id NOT IN (SELECT id FROM t2_a0117)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0117
   WHERE id NOT IN (SELECT id FROM t1_a0117)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0117 a JOIN t2_a0117 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0118
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0118, t2_a0118;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0118 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0118 MODIFY target VARCHAR(86) CHARACTER SET utf8 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0118 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0118 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
SELECT 'TC-A0118' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0118
   WHERE id NOT IN (SELECT id FROM t2_a0118)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0118
   WHERE id NOT IN (SELECT id FROM t1_a0118)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0118 a JOIN t2_a0118 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0119
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0119, t2_a0119;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0119 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0119 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0119 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0119 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
SELECT 'TC-A0119' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0119
   WHERE id NOT IN (SELECT id FROM t2_a0119)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0119
   WHERE id NOT IN (SELECT id FROM t1_a0119)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0119 a JOIN t2_a0119 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0120
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0120, t2_a0120;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0120 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(85) CHARACTER SET utf8 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0120 MODIFY target VARCHAR(86) CHARACTER SET utf8 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0120 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(86)
CREATE TABLE t2_a0120 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(86) CHARACTER SET utf8 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
SELECT 'TC-A0120' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0120
   WHERE id NOT IN (SELECT id FROM t2_a0120)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0120
   WHERE id NOT IN (SELECT id FROM t1_a0120)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0120 a JOIN t2_a0120 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0121
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0121, t2_a0121;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0121 (
  target VARCHAR(85) CHARACTER SET utf8,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t1_a0121 (target) VALUES ('');
INSERT INTO t1_a0121 (target) VALUES ('a');
INSERT INTO t1_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0121 (target) VALUES ('Hello');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0121 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0121 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0121 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0121 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0121 (target) VALUES ('');
INSERT INTO t1_a0121 (target) VALUES ('a');
INSERT INTO t1_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0121 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(85)
CREATE TABLE t2_a0121 (
  target VARCHAR(85) CHARACTER SET utf8,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
INSERT INTO t2_a0121 (target) VALUES ('');
INSERT INTO t2_a0121 (target) VALUES ('a');
INSERT INTO t2_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0121 (target) VALUES ('Hello');
INSERT INTO t2_a0121 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0121 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0121 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0121 (target) VALUES ('');
INSERT INTO t2_a0121 (target) VALUES ('a');
INSERT INTO t2_a0121 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0121' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0121
   WHERE id NOT IN (SELECT id FROM t2_a0121)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0121
   WHERE id NOT IN (SELECT id FROM t1_a0121)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0121 a JOIN t2_a0121 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0122
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0122, t2_tc_aa0122;
CREATE TABLE t1_tc_aa0122 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(85) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0122 (target) VALUES ('');
INSERT INTO t1_tc_aa0122 (target) VALUES ('a');
INSERT INTO t1_tc_aa0122 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0122 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0122 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0122 MODIFY target VARCHAR(86) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0122 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0122 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0122 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0122' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0122' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0123
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0123, t2_tc_aa0123;
CREATE TABLE t1_tc_aa0123 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(85) CHARACTER SET utf8,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0123 (target) VALUES ('');
INSERT INTO t1_tc_aa0123 (target) VALUES ('a');
INSERT INTO t1_tc_aa0123 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0123 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0123 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0123 MODIFY target VARCHAR(86) CHARACTER SET utf8, ALGORITHM=instant;
INSERT INTO t1_tc_aa0123 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0123 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0123 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0123' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0123' AND column_name='target' AND character_set_name='utf8mb3';

-- Test Case: TC-AA0124
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(85) -> VARCHAR(86), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0124, t2_tc_aa0124;
CREATE TABLE t1_tc_aa0124 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(85) CHARACTER SET utf8 COLLATE utf8_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0124 (target) VALUES ('');
INSERT INTO t1_tc_aa0124 (target) VALUES ('a');
INSERT INTO t1_tc_aa0124 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0124 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0124 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0124 MODIFY target VARCHAR(86) CHARACTER SET utf8 COLLATE utf8_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0124 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0124 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0124 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0124' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0124' AND column_name='target' AND collation_name='utf8mb3_bin';

-- Test Case: TC-A0125
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0125, t2_a0125;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0125 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0125 (target) VALUES ('');
INSERT INTO t1_a0125 (target) VALUES ('a');
INSERT INTO t1_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0125 (target) VALUES ('Hello');
INSERT INTO t1_a0125 (target) VALUES ('你好');
INSERT INTO t1_a0125 (target) VALUES ('🎉');
INSERT INTO t1_a0125 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0125 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0125 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0125 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0125 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0125 (target) VALUES ('');
INSERT INTO t1_a0125 (target) VALUES ('a');
INSERT INTO t1_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0125 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0125 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0125 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0125 (target) VALUES ('');
INSERT INTO t2_a0125 (target) VALUES ('a');
INSERT INTO t2_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0125 (target) VALUES ('Hello');
INSERT INTO t2_a0125 (target) VALUES ('你好');
INSERT INTO t2_a0125 (target) VALUES ('🎉');
INSERT INTO t2_a0125 (target) VALUES (NULL);
INSERT INTO t2_a0125 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0125 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0125 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0125 (target) VALUES ('');
INSERT INTO t2_a0125 (target) VALUES ('a');
INSERT INTO t2_a0125 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0125 (target) VALUES (NULL);
SELECT 'TC-A0125' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0125
   WHERE id NOT IN (SELECT id FROM t2_a0125)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0125
   WHERE id NOT IN (SELECT id FROM t1_a0125)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0125 a JOIN t2_a0125 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0126
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0126, t2_a0126;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0126 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0126 (target) VALUES ('');
INSERT INTO t1_a0126 (target) VALUES ('a');
INSERT INTO t1_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0126 (target) VALUES ('Hello');
INSERT INTO t1_a0126 (target) VALUES ('你好');
INSERT INTO t1_a0126 (target) VALUES ('🎉');
INSERT INTO t1_a0126 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0126 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0126 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0126 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0126 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0126 (target) VALUES ('');
INSERT INTO t1_a0126 (target) VALUES ('a');
INSERT INTO t1_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0126 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0126 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0126 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0126 (target) VALUES ('');
INSERT INTO t2_a0126 (target) VALUES ('a');
INSERT INTO t2_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0126 (target) VALUES ('Hello');
INSERT INTO t2_a0126 (target) VALUES ('你好');
INSERT INTO t2_a0126 (target) VALUES ('🎉');
INSERT INTO t2_a0126 (target) VALUES (NULL);
INSERT INTO t2_a0126 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0126 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0126 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0126 (target) VALUES ('');
INSERT INTO t2_a0126 (target) VALUES ('a');
INSERT INTO t2_a0126 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0126 (target) VALUES (NULL);
SELECT 'TC-A0126' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0126
   WHERE id NOT IN (SELECT id FROM t2_a0126)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0126
   WHERE id NOT IN (SELECT id FROM t1_a0126)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0126 a JOIN t2_a0126 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0127
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0127, t2_a0127;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0127 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0127 (target) VALUES ('');
INSERT INTO t1_a0127 (target) VALUES ('a');
INSERT INTO t1_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0127 (target) VALUES ('Hello');
INSERT INTO t1_a0127 (target) VALUES ('你好');
INSERT INTO t1_a0127 (target) VALUES ('🎉');
INSERT INTO t1_a0127 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0127 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0127 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0127 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0127 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0127 (target) VALUES ('');
INSERT INTO t1_a0127 (target) VALUES ('a');
INSERT INTO t1_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0127 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0127 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0127 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0127 (target) VALUES ('');
INSERT INTO t2_a0127 (target) VALUES ('a');
INSERT INTO t2_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0127 (target) VALUES ('Hello');
INSERT INTO t2_a0127 (target) VALUES ('你好');
INSERT INTO t2_a0127 (target) VALUES ('🎉');
INSERT INTO t2_a0127 (target) VALUES (NULL);
INSERT INTO t2_a0127 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0127 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0127 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0127 (target) VALUES ('');
INSERT INTO t2_a0127 (target) VALUES ('a');
INSERT INTO t2_a0127 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0127 (target) VALUES (NULL);
SELECT 'TC-A0127' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0127
   WHERE id NOT IN (SELECT id FROM t2_a0127)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0127
   WHERE id NOT IN (SELECT id FROM t1_a0127)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0127 a JOIN t2_a0127 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0128
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0128, t2_a0128;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0128 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0128 (target) VALUES ('');
INSERT INTO t1_a0128 (target) VALUES ('a');
INSERT INTO t1_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0128 (target) VALUES ('Hello');
INSERT INTO t1_a0128 (target) VALUES ('你好');
INSERT INTO t1_a0128 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0128 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0128 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0128 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0128 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0128 (target) VALUES ('');
INSERT INTO t1_a0128 (target) VALUES ('a');
INSERT INTO t1_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0128 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(63)
CREATE TABLE t2_a0128 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0128 (target) VALUES ('');
INSERT INTO t2_a0128 (target) VALUES ('a');
INSERT INTO t2_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0128 (target) VALUES ('Hello');
INSERT INTO t2_a0128 (target) VALUES ('你好');
INSERT INTO t2_a0128 (target) VALUES ('🎉');
INSERT INTO t2_a0128 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0128 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0128 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0128 (target) VALUES ('');
INSERT INTO t2_a0128 (target) VALUES ('a');
INSERT INTO t2_a0128 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0128' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0128
   WHERE id NOT IN (SELECT id FROM t2_a0128)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0128
   WHERE id NOT IN (SELECT id FROM t1_a0128)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0128 a JOIN t2_a0128 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0129
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0129, t2_a0129;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0129 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0129 (target) VALUES ('');
INSERT INTO t1_a0129 (target) VALUES ('a');
INSERT INTO t1_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0129 (target) VALUES ('Hello');
INSERT INTO t1_a0129 (target) VALUES ('你好');
INSERT INTO t1_a0129 (target) VALUES ('🎉');
INSERT INTO t1_a0129 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0129 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0129 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0129 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0129 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0129 (target) VALUES ('');
INSERT INTO t1_a0129 (target) VALUES ('a');
INSERT INTO t1_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0129 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0129 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0129 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0129 (target) VALUES ('');
INSERT INTO t2_a0129 (target) VALUES ('a');
INSERT INTO t2_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0129 (target) VALUES ('Hello');
INSERT INTO t2_a0129 (target) VALUES ('你好');
INSERT INTO t2_a0129 (target) VALUES ('🎉');
INSERT INTO t2_a0129 (target) VALUES (NULL);
INSERT INTO t2_a0129 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0129 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0129 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0129 (target) VALUES ('');
INSERT INTO t2_a0129 (target) VALUES ('a');
INSERT INTO t2_a0129 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0129 (target) VALUES (NULL);
SELECT 'TC-A0129' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0129
   WHERE id NOT IN (SELECT id FROM t2_a0129)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0129
   WHERE id NOT IN (SELECT id FROM t1_a0129)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0129 a JOIN t2_a0129 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0130
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0130, t2_a0130;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0130 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0130 (target) VALUES ('');
INSERT INTO t1_a0130 (target) VALUES ('a');
INSERT INTO t1_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0130 (target) VALUES ('Hello');
INSERT INTO t1_a0130 (target) VALUES ('你好');
INSERT INTO t1_a0130 (target) VALUES ('🎉');
INSERT INTO t1_a0130 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0130 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0130 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0130 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0130 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0130 (target) VALUES ('');
INSERT INTO t1_a0130 (target) VALUES ('a');
INSERT INTO t1_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0130 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0130 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0130 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0130 (target) VALUES ('');
INSERT INTO t2_a0130 (target) VALUES ('a');
INSERT INTO t2_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0130 (target) VALUES ('Hello');
INSERT INTO t2_a0130 (target) VALUES ('你好');
INSERT INTO t2_a0130 (target) VALUES ('🎉');
INSERT INTO t2_a0130 (target) VALUES (NULL);
INSERT INTO t2_a0130 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0130 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0130 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0130 (target) VALUES ('');
INSERT INTO t2_a0130 (target) VALUES ('a');
INSERT INTO t2_a0130 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0130 (target) VALUES (NULL);
SELECT 'TC-A0130' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0130
   WHERE id NOT IN (SELECT id FROM t2_a0130)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0130
   WHERE id NOT IN (SELECT id FROM t1_a0130)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0130 a JOIN t2_a0130 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0131
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0131, t2_a0131;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0131 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0131 (target) VALUES ('');
INSERT INTO t1_a0131 (target) VALUES ('a');
INSERT INTO t1_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0131 (target) VALUES ('Hello');
INSERT INTO t1_a0131 (target) VALUES ('你好');
INSERT INTO t1_a0131 (target) VALUES ('🎉');
INSERT INTO t1_a0131 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0131 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0131 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0131 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0131 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0131 (target) VALUES ('');
INSERT INTO t1_a0131 (target) VALUES ('a');
INSERT INTO t1_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0131 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0131 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0131 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0131 (target) VALUES ('');
INSERT INTO t2_a0131 (target) VALUES ('a');
INSERT INTO t2_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0131 (target) VALUES ('Hello');
INSERT INTO t2_a0131 (target) VALUES ('你好');
INSERT INTO t2_a0131 (target) VALUES ('🎉');
INSERT INTO t2_a0131 (target) VALUES (NULL);
INSERT INTO t2_a0131 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0131 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0131 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0131 (target) VALUES ('');
INSERT INTO t2_a0131 (target) VALUES ('a');
INSERT INTO t2_a0131 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0131 (target) VALUES (NULL);
SELECT 'TC-A0131' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0131
   WHERE id NOT IN (SELECT id FROM t2_a0131)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0131
   WHERE id NOT IN (SELECT id FROM t1_a0131)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0131 a JOIN t2_a0131 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0132
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0132, t2_a0132;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0132 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0132 (target) VALUES ('');
INSERT INTO t1_a0132 (target) VALUES ('a');
INSERT INTO t1_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0132 (target) VALUES ('Hello');
INSERT INTO t1_a0132 (target) VALUES ('你好');
INSERT INTO t1_a0132 (target) VALUES ('🎉');
INSERT INTO t1_a0132 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0132 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0132 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0132 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0132 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0132 (target) VALUES ('');
INSERT INTO t1_a0132 (target) VALUES ('a');
INSERT INTO t1_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0132 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0132 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0132 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0132 (target) VALUES ('');
INSERT INTO t2_a0132 (target) VALUES ('a');
INSERT INTO t2_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0132 (target) VALUES ('Hello');
INSERT INTO t2_a0132 (target) VALUES ('你好');
INSERT INTO t2_a0132 (target) VALUES ('🎉');
INSERT INTO t2_a0132 (target) VALUES (NULL);
INSERT INTO t2_a0132 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0132 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0132 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0132 (target) VALUES ('');
INSERT INTO t2_a0132 (target) VALUES ('a');
INSERT INTO t2_a0132 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0132 (target) VALUES (NULL);
SELECT 'TC-A0132' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0132
   WHERE id NOT IN (SELECT id FROM t2_a0132)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0132
   WHERE id NOT IN (SELECT id FROM t1_a0132)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0132 a JOIN t2_a0132 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0133
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0133, t2_a0133;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0133 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0133 (target) VALUES ('');
INSERT INTO t1_a0133 (target) VALUES ('a');
INSERT INTO t1_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0133 (target) VALUES ('Hello');
INSERT INTO t1_a0133 (target) VALUES ('你好');
INSERT INTO t1_a0133 (target) VALUES ('🎉');
INSERT INTO t1_a0133 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0133 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0133 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0133 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0133 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0133 (target) VALUES ('');
INSERT INTO t1_a0133 (target) VALUES ('a');
INSERT INTO t1_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0133 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0133 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0133 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0133 (target) VALUES ('');
INSERT INTO t2_a0133 (target) VALUES ('a');
INSERT INTO t2_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0133 (target) VALUES ('Hello');
INSERT INTO t2_a0133 (target) VALUES ('你好');
INSERT INTO t2_a0133 (target) VALUES ('🎉');
INSERT INTO t2_a0133 (target) VALUES (NULL);
INSERT INTO t2_a0133 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0133 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0133 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0133 (target) VALUES ('');
INSERT INTO t2_a0133 (target) VALUES ('a');
INSERT INTO t2_a0133 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0133 (target) VALUES (NULL);
SELECT 'TC-A0133' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0133
   WHERE id NOT IN (SELECT id FROM t2_a0133)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0133
   WHERE id NOT IN (SELECT id FROM t1_a0133)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0133 a JOIN t2_a0133 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0134
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0134, t2_a0134;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0134 (
  target VARCHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0134 (target) VALUES ('');
INSERT INTO t1_a0134 (target) VALUES ('a');
INSERT INTO t1_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0134 (target) VALUES ('Hello');
INSERT INTO t1_a0134 (target) VALUES ('你好');
INSERT INTO t1_a0134 (target) VALUES ('🎉');
INSERT INTO t1_a0134 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0134 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0134 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0134 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0134 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0134 (target) VALUES ('');
INSERT INTO t1_a0134 (target) VALUES ('a');
INSERT INTO t1_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0134 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0134 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0134 (
  target VARCHAR(64) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0134 (target) VALUES ('');
INSERT INTO t2_a0134 (target) VALUES ('a');
INSERT INTO t2_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0134 (target) VALUES ('Hello');
INSERT INTO t2_a0134 (target) VALUES ('你好');
INSERT INTO t2_a0134 (target) VALUES ('🎉');
INSERT INTO t2_a0134 (target) VALUES (NULL);
INSERT INTO t2_a0134 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0134 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0134 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0134 (target) VALUES ('');
INSERT INTO t2_a0134 (target) VALUES ('a');
INSERT INTO t2_a0134 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0134 (target) VALUES (NULL);
SELECT 'TC-A0134' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0134
   WHERE id NOT IN (SELECT id FROM t2_a0134)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0134
   WHERE id NOT IN (SELECT id FROM t1_a0134)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0134 a JOIN t2_a0134 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0135
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0135, t2_a0135;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0135 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(63) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0135 (target) VALUES ('');
INSERT INTO t1_a0135 (target) VALUES ('a');
INSERT INTO t1_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0135 (target) VALUES ('Hello');
INSERT INTO t1_a0135 (target) VALUES ('你好');
INSERT INTO t1_a0135 (target) VALUES ('🎉');
INSERT INTO t1_a0135 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0135 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0135 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0135 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0135 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0135 (target) VALUES ('');
INSERT INTO t1_a0135 (target) VALUES ('a');
INSERT INTO t1_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0135 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0135 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0135 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(64) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0135 (target) VALUES ('');
INSERT INTO t2_a0135 (target) VALUES ('a');
INSERT INTO t2_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0135 (target) VALUES ('Hello');
INSERT INTO t2_a0135 (target) VALUES ('你好');
INSERT INTO t2_a0135 (target) VALUES ('🎉');
INSERT INTO t2_a0135 (target) VALUES (NULL);
INSERT INTO t2_a0135 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0135 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0135 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0135 (target) VALUES ('');
INSERT INTO t2_a0135 (target) VALUES ('a');
INSERT INTO t2_a0135 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0135 (target) VALUES (NULL);
SELECT 'TC-A0135' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0135
   WHERE id NOT IN (SELECT id FROM t2_a0135)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0135
   WHERE id NOT IN (SELECT id FROM t1_a0135)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0135 a JOIN t2_a0135 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0136
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0136, t2_a0136;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0136 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0136 (target) VALUES ('');
INSERT INTO t1_a0136 (target) VALUES ('a');
INSERT INTO t1_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0136 (target) VALUES ('Hello');
INSERT INTO t1_a0136 (target) VALUES ('你好');
INSERT INTO t1_a0136 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0136 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0136 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0136 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0136 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0136 (target) VALUES ('');
INSERT INTO t1_a0136 (target) VALUES ('a');
INSERT INTO t1_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0136 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0136 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0136 (target) VALUES ('');
INSERT INTO t2_a0136 (target) VALUES ('a');
INSERT INTO t2_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0136 (target) VALUES ('Hello');
INSERT INTO t2_a0136 (target) VALUES ('你好');
INSERT INTO t2_a0136 (target) VALUES ('🎉');
INSERT INTO t2_a0136 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0136 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0136 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0136 (target) VALUES ('');
INSERT INTO t2_a0136 (target) VALUES ('a');
INSERT INTO t2_a0136 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0136' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0136
   WHERE id NOT IN (SELECT id FROM t2_a0136)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0136
   WHERE id NOT IN (SELECT id FROM t1_a0136)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0136 a JOIN t2_a0136 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0137
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0137, t2_a0137;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0137 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0137 (target) VALUES ('');
INSERT INTO t1_a0137 (target) VALUES ('a');
INSERT INTO t1_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0137 (target) VALUES ('Hello');
INSERT INTO t1_a0137 (target) VALUES ('你好');
INSERT INTO t1_a0137 (target) VALUES ('🎉');
INSERT INTO t1_a0137 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0137 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0137 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0137 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0137 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0137 (target) VALUES ('');
INSERT INTO t1_a0137 (target) VALUES ('a');
INSERT INTO t1_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0137 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0137 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0137 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0137 (target) VALUES ('');
INSERT INTO t2_a0137 (target) VALUES ('a');
INSERT INTO t2_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0137 (target) VALUES ('Hello');
INSERT INTO t2_a0137 (target) VALUES ('你好');
INSERT INTO t2_a0137 (target) VALUES ('🎉');
INSERT INTO t2_a0137 (target) VALUES (NULL);
INSERT INTO t2_a0137 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0137 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0137 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0137 (target) VALUES ('');
INSERT INTO t2_a0137 (target) VALUES ('a');
INSERT INTO t2_a0137 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0137 (target) VALUES (NULL);
SELECT 'TC-A0137' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0137
   WHERE id NOT IN (SELECT id FROM t2_a0137)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0137
   WHERE id NOT IN (SELECT id FROM t1_a0137)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0137 a JOIN t2_a0137 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0138
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0138, t2_a0138;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0138 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0138 (target) VALUES ('');
INSERT INTO t1_a0138 (target) VALUES ('a');
INSERT INTO t1_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0138 (target) VALUES ('Hello');
INSERT INTO t1_a0138 (target) VALUES ('你好');
INSERT INTO t1_a0138 (target) VALUES ('🎉');
INSERT INTO t1_a0138 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0138 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0138 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0138 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0138 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0138 (target) VALUES ('');
INSERT INTO t1_a0138 (target) VALUES ('a');
INSERT INTO t1_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0138 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0138 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0138 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0138 (target) VALUES ('');
INSERT INTO t2_a0138 (target) VALUES ('a');
INSERT INTO t2_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0138 (target) VALUES ('Hello');
INSERT INTO t2_a0138 (target) VALUES ('你好');
INSERT INTO t2_a0138 (target) VALUES ('🎉');
INSERT INTO t2_a0138 (target) VALUES (NULL);
INSERT INTO t2_a0138 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0138 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0138 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0138 (target) VALUES ('');
INSERT INTO t2_a0138 (target) VALUES ('a');
INSERT INTO t2_a0138 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0138 (target) VALUES (NULL);
SELECT 'TC-A0138' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0138
   WHERE id NOT IN (SELECT id FROM t2_a0138)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0138
   WHERE id NOT IN (SELECT id FROM t1_a0138)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0138 a JOIN t2_a0138 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0139
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0139, t2_a0139;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0139 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0139 (target) VALUES ('');
INSERT INTO t1_a0139 (target) VALUES ('a');
INSERT INTO t1_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0139 (target) VALUES ('Hello');
INSERT INTO t1_a0139 (target) VALUES ('你好');
INSERT INTO t1_a0139 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0139 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0139 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0139 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0139 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0139 (target) VALUES ('');
INSERT INTO t1_a0139 (target) VALUES ('a');
INSERT INTO t1_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0139 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0139 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0139 (target) VALUES ('');
INSERT INTO t2_a0139 (target) VALUES ('a');
INSERT INTO t2_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0139 (target) VALUES ('Hello');
INSERT INTO t2_a0139 (target) VALUES ('你好');
INSERT INTO t2_a0139 (target) VALUES ('🎉');
INSERT INTO t2_a0139 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0139 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0139 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0139 (target) VALUES ('');
INSERT INTO t2_a0139 (target) VALUES ('a');
INSERT INTO t2_a0139 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0139' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0139
   WHERE id NOT IN (SELECT id FROM t2_a0139)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0139
   WHERE id NOT IN (SELECT id FROM t1_a0139)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0139 a JOIN t2_a0139 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0140
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0140, t2_a0140;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0140 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0140 (target) VALUES ('');
INSERT INTO t1_a0140 (target) VALUES ('a');
INSERT INTO t1_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0140 (target) VALUES ('Hello');
INSERT INTO t1_a0140 (target) VALUES ('你好');
INSERT INTO t1_a0140 (target) VALUES ('🎉');
INSERT INTO t1_a0140 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0140 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0140 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0140 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0140 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0140 (target) VALUES ('');
INSERT INTO t1_a0140 (target) VALUES ('a');
INSERT INTO t1_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0140 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0140 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0140 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0140 (target) VALUES ('');
INSERT INTO t2_a0140 (target) VALUES ('a');
INSERT INTO t2_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0140 (target) VALUES ('Hello');
INSERT INTO t2_a0140 (target) VALUES ('你好');
INSERT INTO t2_a0140 (target) VALUES ('🎉');
INSERT INTO t2_a0140 (target) VALUES (NULL);
INSERT INTO t2_a0140 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0140 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0140 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0140 (target) VALUES ('');
INSERT INTO t2_a0140 (target) VALUES ('a');
INSERT INTO t2_a0140 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0140 (target) VALUES (NULL);
SELECT 'TC-A0140' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0140
   WHERE id NOT IN (SELECT id FROM t2_a0140)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0140
   WHERE id NOT IN (SELECT id FROM t1_a0140)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0140 a JOIN t2_a0140 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0141
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0141, t2_a0141;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0141 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0141 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0141 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0141 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0141' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0141
   WHERE id NOT IN (SELECT id FROM t2_a0141)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0141
   WHERE id NOT IN (SELECT id FROM t1_a0141)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0141 a JOIN t2_a0141 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0142
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0142, t2_a0142;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0142 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0142 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0142 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0142 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0142 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0142 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0142 (target) VALUES ('');
INSERT INTO t1_a0142 (target) VALUES ('a');
INSERT INTO t1_a0142 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0142 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0142 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0142 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0142 (target) VALUES ('');
INSERT INTO t2_a0142 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0142 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0142 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0142 (target) VALUES ('');
INSERT INTO t2_a0142 (target) VALUES ('a');
INSERT INTO t2_a0142 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0142 (target) VALUES (NULL);
SELECT 'TC-A0142' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0142
   WHERE id NOT IN (SELECT id FROM t2_a0142)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0142
   WHERE id NOT IN (SELECT id FROM t1_a0142)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0142 a JOIN t2_a0142 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0143
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0143, t2_a0143;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0143 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0143 (target) VALUES ('');
INSERT INTO t1_a0143 (target) VALUES ('a');
INSERT INTO t1_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0143 (target) VALUES ('Hello');
INSERT INTO t1_a0143 (target) VALUES ('你好');
INSERT INTO t1_a0143 (target) VALUES ('🎉');
INSERT INTO t1_a0143 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0143 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0143 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0143 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0143 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0143 (target) VALUES ('');
INSERT INTO t1_a0143 (target) VALUES ('a');
INSERT INTO t1_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0143 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0143 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0143 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0143 (target) VALUES ('');
INSERT INTO t2_a0143 (target) VALUES ('a');
INSERT INTO t2_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0143 (target) VALUES ('Hello');
INSERT INTO t2_a0143 (target) VALUES ('你好');
INSERT INTO t2_a0143 (target) VALUES ('🎉');
INSERT INTO t2_a0143 (target) VALUES (NULL);
INSERT INTO t2_a0143 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0143 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0143 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0143 (target) VALUES ('');
INSERT INTO t2_a0143 (target) VALUES ('a');
INSERT INTO t2_a0143 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0143 (target) VALUES (NULL);
SELECT 'TC-A0143' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0143
   WHERE id NOT IN (SELECT id FROM t2_a0143)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0143
   WHERE id NOT IN (SELECT id FROM t1_a0143)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0143 a JOIN t2_a0143 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0144
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0144, t2_a0144;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0144 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0144 (target) VALUES ('');
INSERT INTO t1_a0144 (target) VALUES ('a');
INSERT INTO t1_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0144 (target) VALUES ('Hello');
INSERT INTO t1_a0144 (target) VALUES ('你好');
INSERT INTO t1_a0144 (target) VALUES ('🎉');
INSERT INTO t1_a0144 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0144 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0144 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0144 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0144 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0144 (target) VALUES ('');
INSERT INTO t1_a0144 (target) VALUES ('a');
INSERT INTO t1_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0144 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0144 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0144 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0144 (target) VALUES ('');
INSERT INTO t2_a0144 (target) VALUES ('a');
INSERT INTO t2_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0144 (target) VALUES ('Hello');
INSERT INTO t2_a0144 (target) VALUES ('你好');
INSERT INTO t2_a0144 (target) VALUES ('🎉');
INSERT INTO t2_a0144 (target) VALUES (NULL);
INSERT INTO t2_a0144 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0144 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0144 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0144 (target) VALUES ('');
INSERT INTO t2_a0144 (target) VALUES ('a');
INSERT INTO t2_a0144 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0144 (target) VALUES (NULL);
SELECT 'TC-A0144' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0144
   WHERE id NOT IN (SELECT id FROM t2_a0144)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0144
   WHERE id NOT IN (SELECT id FROM t1_a0144)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0144 a JOIN t2_a0144 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0145
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0145, t2_a0145;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0145 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0145 (target) VALUES ('');
INSERT INTO t1_a0145 (target) VALUES ('a');
INSERT INTO t1_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0145 (target) VALUES ('Hello');
INSERT INTO t1_a0145 (target) VALUES ('你好');
INSERT INTO t1_a0145 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0145 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0145 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0145 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0145 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0145 (target) VALUES ('');
INSERT INTO t1_a0145 (target) VALUES ('a');
INSERT INTO t1_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0145 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0145 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0145 (target) VALUES ('');
INSERT INTO t2_a0145 (target) VALUES ('a');
INSERT INTO t2_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0145 (target) VALUES ('Hello');
INSERT INTO t2_a0145 (target) VALUES ('你好');
INSERT INTO t2_a0145 (target) VALUES ('🎉');
INSERT INTO t2_a0145 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0145 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0145 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0145 (target) VALUES ('');
INSERT INTO t2_a0145 (target) VALUES ('a');
INSERT INTO t2_a0145 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0145' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0145
   WHERE id NOT IN (SELECT id FROM t2_a0145)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0145
   WHERE id NOT IN (SELECT id FROM t1_a0145)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0145 a JOIN t2_a0145 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0146
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0146, t2_a0146;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0146 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0146 (target) VALUES ('');
INSERT INTO t1_a0146 (target) VALUES ('a');
INSERT INTO t1_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0146 (target) VALUES ('Hello');
INSERT INTO t1_a0146 (target) VALUES ('你好');
INSERT INTO t1_a0146 (target) VALUES ('🎉');
INSERT INTO t1_a0146 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0146 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0146 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0146 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0146 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0146 (target) VALUES ('');
INSERT INTO t1_a0146 (target) VALUES ('a');
INSERT INTO t1_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0146 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0146 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0146 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0146 (target) VALUES ('');
INSERT INTO t2_a0146 (target) VALUES ('a');
INSERT INTO t2_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0146 (target) VALUES ('Hello');
INSERT INTO t2_a0146 (target) VALUES ('你好');
INSERT INTO t2_a0146 (target) VALUES ('🎉');
INSERT INTO t2_a0146 (target) VALUES (NULL);
INSERT INTO t2_a0146 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0146 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0146 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0146 (target) VALUES ('');
INSERT INTO t2_a0146 (target) VALUES ('a');
INSERT INTO t2_a0146 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0146 (target) VALUES (NULL);
SELECT 'TC-A0146' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0146
   WHERE id NOT IN (SELECT id FROM t2_a0146)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0146
   WHERE id NOT IN (SELECT id FROM t1_a0146)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0146 a JOIN t2_a0146 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0147
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0147, t2_a0147;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0147 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0147 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0147 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0147 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0147 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0147 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0147 (target) VALUES ('');
INSERT INTO t1_a0147 (target) VALUES ('a');
INSERT INTO t1_a0147 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0147 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0147 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0147 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0147 (target) VALUES (NULL);
INSERT INTO t2_a0147 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0147 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0147 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0147 (target) VALUES ('');
INSERT INTO t2_a0147 (target) VALUES ('a');
INSERT INTO t2_a0147 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0147 (target) VALUES (NULL);
SELECT 'TC-A0147' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0147
   WHERE id NOT IN (SELECT id FROM t2_a0147)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0147
   WHERE id NOT IN (SELECT id FROM t1_a0147)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0147 a JOIN t2_a0147 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0148
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0148, t2_a0148;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0148 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0148 (target) VALUES ('');
INSERT INTO t1_a0148 (target) VALUES ('a');
INSERT INTO t1_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0148 (target) VALUES ('Hello');
INSERT INTO t1_a0148 (target) VALUES ('你好');
INSERT INTO t1_a0148 (target) VALUES ('🎉');
INSERT INTO t1_a0148 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0148 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0148 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0148 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0148 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0148 (target) VALUES ('');
INSERT INTO t1_a0148 (target) VALUES ('a');
INSERT INTO t1_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0148 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0148 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0148 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0148 (target) VALUES ('');
INSERT INTO t2_a0148 (target) VALUES ('a');
INSERT INTO t2_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0148 (target) VALUES ('Hello');
INSERT INTO t2_a0148 (target) VALUES ('你好');
INSERT INTO t2_a0148 (target) VALUES ('🎉');
INSERT INTO t2_a0148 (target) VALUES (NULL);
INSERT INTO t2_a0148 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0148 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0148 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0148 (target) VALUES ('');
INSERT INTO t2_a0148 (target) VALUES ('a');
INSERT INTO t2_a0148 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0148 (target) VALUES (NULL);
SELECT 'TC-A0148' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0148
   WHERE id NOT IN (SELECT id FROM t2_a0148)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0148
   WHERE id NOT IN (SELECT id FROM t1_a0148)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0148 a JOIN t2_a0148 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0149
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0149, t2_a0149;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0149 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0149 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0149 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0149 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0149' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0149
   WHERE id NOT IN (SELECT id FROM t2_a0149)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0149
   WHERE id NOT IN (SELECT id FROM t1_a0149)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0149 a JOIN t2_a0149 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0150
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0150, t2_a0150;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0150 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0150 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0150 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0150 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0150' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0150
   WHERE id NOT IN (SELECT id FROM t2_a0150)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0150
   WHERE id NOT IN (SELECT id FROM t1_a0150)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0150 a JOIN t2_a0150 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0151
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0151, t2_a0151;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0151 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(63) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0151 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0151 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0151 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0151' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0151
   WHERE id NOT IN (SELECT id FROM t2_a0151)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0151
   WHERE id NOT IN (SELECT id FROM t1_a0151)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0151 a JOIN t2_a0151 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0152
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0152, t2_a0152;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0152 (
  target VARCHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0152 (target) VALUES ('');
INSERT INTO t1_a0152 (target) VALUES ('a');
INSERT INTO t1_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0152 (target) VALUES ('Hello');
INSERT INTO t1_a0152 (target) VALUES ('你好');
INSERT INTO t1_a0152 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0152 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0152 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0152 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0152 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0152 (target) VALUES ('');
INSERT INTO t1_a0152 (target) VALUES ('a');
INSERT INTO t1_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0152 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(63)
CREATE TABLE t2_a0152 (
  target VARCHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0152 (target) VALUES ('');
INSERT INTO t2_a0152 (target) VALUES ('a');
INSERT INTO t2_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0152 (target) VALUES ('Hello');
INSERT INTO t2_a0152 (target) VALUES ('你好');
INSERT INTO t2_a0152 (target) VALUES ('🎉');
INSERT INTO t2_a0152 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0152 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0152 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0152 (target) VALUES ('');
INSERT INTO t2_a0152 (target) VALUES ('a');
INSERT INTO t2_a0152 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0152' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0152
   WHERE id NOT IN (SELECT id FROM t2_a0152)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0152
   WHERE id NOT IN (SELECT id FROM t1_a0152)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0152 a JOIN t2_a0152 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0153
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0153, t2_tc_aa0153;
CREATE TABLE t1_tc_aa0153 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(63) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0153 (target) VALUES ('');
INSERT INTO t1_tc_aa0153 (target) VALUES ('a');
INSERT INTO t1_tc_aa0153 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0153 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0153 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0153 MODIFY target VARCHAR(64) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0153 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0153 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0153 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0153' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0153' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0154
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0154, t2_tc_aa0154;
CREATE TABLE t1_tc_aa0154 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(63) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0154 (target) VALUES ('');
INSERT INTO t1_tc_aa0154 (target) VALUES ('a');
INSERT INTO t1_tc_aa0154 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0154 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0154 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0154 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_aa0154 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0154 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0154 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0154' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0154' AND column_name='target' AND character_set_name='utf8mb4';

-- Test Case: TC-AA0155
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(63) -> VARCHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0155, t2_tc_aa0155;
CREATE TABLE t1_tc_aa0155 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(63) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0155 (target) VALUES ('');
INSERT INTO t1_tc_aa0155 (target) VALUES ('a');
INSERT INTO t1_tc_aa0155 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0155 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0155 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0155 MODIFY target VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0155 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0155 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0155 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0155' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0155' AND column_name='target' AND collation_name='utf8mb4_bin';

-- Test Case: TC-A0156
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0156, t2_a0156;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0156 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0156 (target) VALUES ('');
INSERT INTO t1_a0156 (target) VALUES ('a');
INSERT INTO t1_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0156 (target) VALUES ('Hello');
INSERT INTO t1_a0156 (target) VALUES ('你好');
INSERT INTO t1_a0156 (target) VALUES ('🎉');
INSERT INTO t1_a0156 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0156 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0156 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0156 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0156 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0156 (target) VALUES ('');
INSERT INTO t1_a0156 (target) VALUES ('a');
INSERT INTO t1_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0156 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0156 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0156 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0156 (target) VALUES ('');
INSERT INTO t2_a0156 (target) VALUES ('a');
INSERT INTO t2_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0156 (target) VALUES ('Hello');
INSERT INTO t2_a0156 (target) VALUES ('你好');
INSERT INTO t2_a0156 (target) VALUES ('🎉');
INSERT INTO t2_a0156 (target) VALUES (NULL);
INSERT INTO t2_a0156 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0156 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0156 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0156 (target) VALUES ('');
INSERT INTO t2_a0156 (target) VALUES ('a');
INSERT INTO t2_a0156 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0156 (target) VALUES (NULL);
SELECT 'TC-A0156' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0156
   WHERE id NOT IN (SELECT id FROM t2_a0156)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0156
   WHERE id NOT IN (SELECT id FROM t1_a0156)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0156 a JOIN t2_a0156 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0157
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0157, t2_a0157;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0157 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0157 (target) VALUES ('');
INSERT INTO t1_a0157 (target) VALUES ('a');
INSERT INTO t1_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0157 (target) VALUES ('Hello');
INSERT INTO t1_a0157 (target) VALUES ('你好');
INSERT INTO t1_a0157 (target) VALUES ('🎉');
INSERT INTO t1_a0157 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0157 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0157 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0157 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0157 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0157 (target) VALUES ('');
INSERT INTO t1_a0157 (target) VALUES ('a');
INSERT INTO t1_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0157 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0157 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0157 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0157 (target) VALUES ('');
INSERT INTO t2_a0157 (target) VALUES ('a');
INSERT INTO t2_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0157 (target) VALUES ('Hello');
INSERT INTO t2_a0157 (target) VALUES ('你好');
INSERT INTO t2_a0157 (target) VALUES ('🎉');
INSERT INTO t2_a0157 (target) VALUES (NULL);
INSERT INTO t2_a0157 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0157 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0157 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0157 (target) VALUES ('');
INSERT INTO t2_a0157 (target) VALUES ('a');
INSERT INTO t2_a0157 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0157 (target) VALUES (NULL);
SELECT 'TC-A0157' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0157
   WHERE id NOT IN (SELECT id FROM t2_a0157)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0157
   WHERE id NOT IN (SELECT id FROM t1_a0157)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0157 a JOIN t2_a0157 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0158
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0158, t2_a0158;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0158 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0158 (target) VALUES ('');
INSERT INTO t1_a0158 (target) VALUES ('a');
INSERT INTO t1_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0158 (target) VALUES ('Hello');
INSERT INTO t1_a0158 (target) VALUES ('你好');
INSERT INTO t1_a0158 (target) VALUES ('🎉');
INSERT INTO t1_a0158 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0158 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0158 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0158 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0158 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0158 (target) VALUES ('');
INSERT INTO t1_a0158 (target) VALUES ('a');
INSERT INTO t1_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0158 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0158 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0158 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0158 (target) VALUES ('');
INSERT INTO t2_a0158 (target) VALUES ('a');
INSERT INTO t2_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0158 (target) VALUES ('Hello');
INSERT INTO t2_a0158 (target) VALUES ('你好');
INSERT INTO t2_a0158 (target) VALUES ('🎉');
INSERT INTO t2_a0158 (target) VALUES (NULL);
INSERT INTO t2_a0158 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0158 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0158 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0158 (target) VALUES ('');
INSERT INTO t2_a0158 (target) VALUES ('a');
INSERT INTO t2_a0158 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0158 (target) VALUES (NULL);
SELECT 'TC-A0158' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0158
   WHERE id NOT IN (SELECT id FROM t2_a0158)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0158
   WHERE id NOT IN (SELECT id FROM t1_a0158)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0158 a JOIN t2_a0158 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0159
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0159, t2_a0159;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0159 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0159 (target) VALUES ('');
INSERT INTO t1_a0159 (target) VALUES ('a');
INSERT INTO t1_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0159 (target) VALUES ('Hello');
INSERT INTO t1_a0159 (target) VALUES ('你好');
INSERT INTO t1_a0159 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0159 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0159 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0159 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0159 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0159 (target) VALUES ('');
INSERT INTO t1_a0159 (target) VALUES ('a');
INSERT INTO t1_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0159 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0159 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0159 (target) VALUES ('');
INSERT INTO t2_a0159 (target) VALUES ('a');
INSERT INTO t2_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0159 (target) VALUES ('Hello');
INSERT INTO t2_a0159 (target) VALUES ('你好');
INSERT INTO t2_a0159 (target) VALUES ('🎉');
INSERT INTO t2_a0159 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0159 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0159 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0159 (target) VALUES ('');
INSERT INTO t2_a0159 (target) VALUES ('a');
INSERT INTO t2_a0159 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0159' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0159
   WHERE id NOT IN (SELECT id FROM t2_a0159)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0159
   WHERE id NOT IN (SELECT id FROM t1_a0159)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0159 a JOIN t2_a0159 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0160
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0160, t2_a0160;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0160 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0160 (target) VALUES ('');
INSERT INTO t1_a0160 (target) VALUES ('a');
INSERT INTO t1_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0160 (target) VALUES ('Hello');
INSERT INTO t1_a0160 (target) VALUES ('你好');
INSERT INTO t1_a0160 (target) VALUES ('🎉');
INSERT INTO t1_a0160 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0160 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0160 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0160 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0160 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0160 (target) VALUES ('');
INSERT INTO t1_a0160 (target) VALUES ('a');
INSERT INTO t1_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0160 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0160 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0160 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0160 (target) VALUES ('');
INSERT INTO t2_a0160 (target) VALUES ('a');
INSERT INTO t2_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0160 (target) VALUES ('Hello');
INSERT INTO t2_a0160 (target) VALUES ('你好');
INSERT INTO t2_a0160 (target) VALUES ('🎉');
INSERT INTO t2_a0160 (target) VALUES (NULL);
INSERT INTO t2_a0160 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0160 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0160 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0160 (target) VALUES ('');
INSERT INTO t2_a0160 (target) VALUES ('a');
INSERT INTO t2_a0160 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0160 (target) VALUES (NULL);
SELECT 'TC-A0160' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0160
   WHERE id NOT IN (SELECT id FROM t2_a0160)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0160
   WHERE id NOT IN (SELECT id FROM t1_a0160)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0160 a JOIN t2_a0160 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0161
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0161, t2_a0161;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0161 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0161 (target) VALUES ('');
INSERT INTO t1_a0161 (target) VALUES ('a');
INSERT INTO t1_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0161 (target) VALUES ('Hello');
INSERT INTO t1_a0161 (target) VALUES ('你好');
INSERT INTO t1_a0161 (target) VALUES ('🎉');
INSERT INTO t1_a0161 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0161 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0161 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0161 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0161 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0161 (target) VALUES ('');
INSERT INTO t1_a0161 (target) VALUES ('a');
INSERT INTO t1_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0161 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0161 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0161 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0161 (target) VALUES ('');
INSERT INTO t2_a0161 (target) VALUES ('a');
INSERT INTO t2_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0161 (target) VALUES ('Hello');
INSERT INTO t2_a0161 (target) VALUES ('你好');
INSERT INTO t2_a0161 (target) VALUES ('🎉');
INSERT INTO t2_a0161 (target) VALUES (NULL);
INSERT INTO t2_a0161 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0161 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0161 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0161 (target) VALUES ('');
INSERT INTO t2_a0161 (target) VALUES ('a');
INSERT INTO t2_a0161 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0161 (target) VALUES (NULL);
SELECT 'TC-A0161' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0161
   WHERE id NOT IN (SELECT id FROM t2_a0161)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0161
   WHERE id NOT IN (SELECT id FROM t1_a0161)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0161 a JOIN t2_a0161 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0162
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0162, t2_a0162;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0162 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0162 (target) VALUES ('');
INSERT INTO t1_a0162 (target) VALUES ('a');
INSERT INTO t1_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0162 (target) VALUES ('Hello');
INSERT INTO t1_a0162 (target) VALUES ('你好');
INSERT INTO t1_a0162 (target) VALUES ('🎉');
INSERT INTO t1_a0162 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0162 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0162 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0162 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0162 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0162 (target) VALUES ('');
INSERT INTO t1_a0162 (target) VALUES ('a');
INSERT INTO t1_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0162 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0162 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0162 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0162 (target) VALUES ('');
INSERT INTO t2_a0162 (target) VALUES ('a');
INSERT INTO t2_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0162 (target) VALUES ('Hello');
INSERT INTO t2_a0162 (target) VALUES ('你好');
INSERT INTO t2_a0162 (target) VALUES ('🎉');
INSERT INTO t2_a0162 (target) VALUES (NULL);
INSERT INTO t2_a0162 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0162 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0162 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0162 (target) VALUES ('');
INSERT INTO t2_a0162 (target) VALUES ('a');
INSERT INTO t2_a0162 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0162 (target) VALUES (NULL);
SELECT 'TC-A0162' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0162
   WHERE id NOT IN (SELECT id FROM t2_a0162)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0162
   WHERE id NOT IN (SELECT id FROM t1_a0162)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0162 a JOIN t2_a0162 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0163
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0163, t2_a0163;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0163 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0163 (target) VALUES ('');
INSERT INTO t1_a0163 (target) VALUES ('a');
INSERT INTO t1_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0163 (target) VALUES ('Hello');
INSERT INTO t1_a0163 (target) VALUES ('你好');
INSERT INTO t1_a0163 (target) VALUES ('🎉');
INSERT INTO t1_a0163 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0163 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0163 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0163 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0163 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0163 (target) VALUES ('');
INSERT INTO t1_a0163 (target) VALUES ('a');
INSERT INTO t1_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0163 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0163 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0163 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0163 (target) VALUES ('');
INSERT INTO t2_a0163 (target) VALUES ('a');
INSERT INTO t2_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0163 (target) VALUES ('Hello');
INSERT INTO t2_a0163 (target) VALUES ('你好');
INSERT INTO t2_a0163 (target) VALUES ('🎉');
INSERT INTO t2_a0163 (target) VALUES (NULL);
INSERT INTO t2_a0163 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0163 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0163 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0163 (target) VALUES ('');
INSERT INTO t2_a0163 (target) VALUES ('a');
INSERT INTO t2_a0163 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0163 (target) VALUES (NULL);
SELECT 'TC-A0163' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0163
   WHERE id NOT IN (SELECT id FROM t2_a0163)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0163
   WHERE id NOT IN (SELECT id FROM t1_a0163)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0163 a JOIN t2_a0163 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0164
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0164, t2_a0164;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0164 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0164 (target) VALUES ('');
INSERT INTO t1_a0164 (target) VALUES ('a');
INSERT INTO t1_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0164 (target) VALUES ('Hello');
INSERT INTO t1_a0164 (target) VALUES ('你好');
INSERT INTO t1_a0164 (target) VALUES ('🎉');
INSERT INTO t1_a0164 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0164 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0164 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0164 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0164 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0164 (target) VALUES ('');
INSERT INTO t1_a0164 (target) VALUES ('a');
INSERT INTO t1_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0164 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0164 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0164 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0164 (target) VALUES ('');
INSERT INTO t2_a0164 (target) VALUES ('a');
INSERT INTO t2_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0164 (target) VALUES ('Hello');
INSERT INTO t2_a0164 (target) VALUES ('你好');
INSERT INTO t2_a0164 (target) VALUES ('🎉');
INSERT INTO t2_a0164 (target) VALUES (NULL);
INSERT INTO t2_a0164 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0164 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0164 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0164 (target) VALUES ('');
INSERT INTO t2_a0164 (target) VALUES ('a');
INSERT INTO t2_a0164 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0164 (target) VALUES (NULL);
SELECT 'TC-A0164' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0164
   WHERE id NOT IN (SELECT id FROM t2_a0164)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0164
   WHERE id NOT IN (SELECT id FROM t1_a0164)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0164 a JOIN t2_a0164 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0165
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0165, t2_a0165;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0165 (
  target VARCHAR(64) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0165 (target) VALUES ('');
INSERT INTO t1_a0165 (target) VALUES ('a');
INSERT INTO t1_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0165 (target) VALUES ('Hello');
INSERT INTO t1_a0165 (target) VALUES ('你好');
INSERT INTO t1_a0165 (target) VALUES ('🎉');
INSERT INTO t1_a0165 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0165 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0165 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0165 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0165 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0165 (target) VALUES ('');
INSERT INTO t1_a0165 (target) VALUES ('a');
INSERT INTO t1_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0165 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0165 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0165 (
  target VARCHAR(65) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0165 (target) VALUES ('');
INSERT INTO t2_a0165 (target) VALUES ('a');
INSERT INTO t2_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0165 (target) VALUES ('Hello');
INSERT INTO t2_a0165 (target) VALUES ('你好');
INSERT INTO t2_a0165 (target) VALUES ('🎉');
INSERT INTO t2_a0165 (target) VALUES (NULL);
INSERT INTO t2_a0165 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0165 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0165 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0165 (target) VALUES ('');
INSERT INTO t2_a0165 (target) VALUES ('a');
INSERT INTO t2_a0165 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0165 (target) VALUES (NULL);
SELECT 'TC-A0165' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0165
   WHERE id NOT IN (SELECT id FROM t2_a0165)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0165
   WHERE id NOT IN (SELECT id FROM t1_a0165)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0165 a JOIN t2_a0165 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0166
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0166, t2_a0166;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0166 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(64) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0166 (target) VALUES ('');
INSERT INTO t1_a0166 (target) VALUES ('a');
INSERT INTO t1_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0166 (target) VALUES ('Hello');
INSERT INTO t1_a0166 (target) VALUES ('你好');
INSERT INTO t1_a0166 (target) VALUES ('🎉');
INSERT INTO t1_a0166 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0166 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0166 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0166 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0166 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0166 (target) VALUES ('');
INSERT INTO t1_a0166 (target) VALUES ('a');
INSERT INTO t1_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0166 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0166 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0166 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(65) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0166 (target) VALUES ('');
INSERT INTO t2_a0166 (target) VALUES ('a');
INSERT INTO t2_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0166 (target) VALUES ('Hello');
INSERT INTO t2_a0166 (target) VALUES ('你好');
INSERT INTO t2_a0166 (target) VALUES ('🎉');
INSERT INTO t2_a0166 (target) VALUES (NULL);
INSERT INTO t2_a0166 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0166 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0166 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0166 (target) VALUES ('');
INSERT INTO t2_a0166 (target) VALUES ('a');
INSERT INTO t2_a0166 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0166 (target) VALUES (NULL);
SELECT 'TC-A0166' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0166
   WHERE id NOT IN (SELECT id FROM t2_a0166)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0166
   WHERE id NOT IN (SELECT id FROM t1_a0166)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0166 a JOIN t2_a0166 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0167
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0167, t2_a0167;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0167 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0167 (target) VALUES ('');
INSERT INTO t1_a0167 (target) VALUES ('a');
INSERT INTO t1_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0167 (target) VALUES ('Hello');
INSERT INTO t1_a0167 (target) VALUES ('你好');
INSERT INTO t1_a0167 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0167 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0167 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0167 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0167 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0167 (target) VALUES ('');
INSERT INTO t1_a0167 (target) VALUES ('a');
INSERT INTO t1_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0167 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0167 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0167 (target) VALUES ('');
INSERT INTO t2_a0167 (target) VALUES ('a');
INSERT INTO t2_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0167 (target) VALUES ('Hello');
INSERT INTO t2_a0167 (target) VALUES ('你好');
INSERT INTO t2_a0167 (target) VALUES ('🎉');
INSERT INTO t2_a0167 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0167 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0167 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0167 (target) VALUES ('');
INSERT INTO t2_a0167 (target) VALUES ('a');
INSERT INTO t2_a0167 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0167' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0167
   WHERE id NOT IN (SELECT id FROM t2_a0167)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0167
   WHERE id NOT IN (SELECT id FROM t1_a0167)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0167 a JOIN t2_a0167 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0168
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0168, t2_a0168;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0168 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0168 (target) VALUES ('');
INSERT INTO t1_a0168 (target) VALUES ('a');
INSERT INTO t1_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0168 (target) VALUES ('Hello');
INSERT INTO t1_a0168 (target) VALUES ('你好');
INSERT INTO t1_a0168 (target) VALUES ('🎉');
INSERT INTO t1_a0168 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0168 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0168 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0168 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0168 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0168 (target) VALUES ('');
INSERT INTO t1_a0168 (target) VALUES ('a');
INSERT INTO t1_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0168 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0168 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0168 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0168 (target) VALUES ('');
INSERT INTO t2_a0168 (target) VALUES ('a');
INSERT INTO t2_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0168 (target) VALUES ('Hello');
INSERT INTO t2_a0168 (target) VALUES ('你好');
INSERT INTO t2_a0168 (target) VALUES ('🎉');
INSERT INTO t2_a0168 (target) VALUES (NULL);
INSERT INTO t2_a0168 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0168 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0168 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0168 (target) VALUES ('');
INSERT INTO t2_a0168 (target) VALUES ('a');
INSERT INTO t2_a0168 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0168 (target) VALUES (NULL);
SELECT 'TC-A0168' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0168
   WHERE id NOT IN (SELECT id FROM t2_a0168)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0168
   WHERE id NOT IN (SELECT id FROM t1_a0168)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0168 a JOIN t2_a0168 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0169
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0169, t2_a0169;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0169 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0169 (target) VALUES ('');
INSERT INTO t1_a0169 (target) VALUES ('a');
INSERT INTO t1_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0169 (target) VALUES ('Hello');
INSERT INTO t1_a0169 (target) VALUES ('你好');
INSERT INTO t1_a0169 (target) VALUES ('🎉');
INSERT INTO t1_a0169 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0169 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0169 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0169 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0169 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0169 (target) VALUES ('');
INSERT INTO t1_a0169 (target) VALUES ('a');
INSERT INTO t1_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0169 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0169 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0169 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0169 (target) VALUES ('');
INSERT INTO t2_a0169 (target) VALUES ('a');
INSERT INTO t2_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0169 (target) VALUES ('Hello');
INSERT INTO t2_a0169 (target) VALUES ('你好');
INSERT INTO t2_a0169 (target) VALUES ('🎉');
INSERT INTO t2_a0169 (target) VALUES (NULL);
INSERT INTO t2_a0169 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0169 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0169 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0169 (target) VALUES ('');
INSERT INTO t2_a0169 (target) VALUES ('a');
INSERT INTO t2_a0169 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0169 (target) VALUES (NULL);
SELECT 'TC-A0169' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0169
   WHERE id NOT IN (SELECT id FROM t2_a0169)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0169
   WHERE id NOT IN (SELECT id FROM t1_a0169)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0169 a JOIN t2_a0169 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0170
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0170, t2_a0170;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0170 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0170 (target) VALUES ('');
INSERT INTO t1_a0170 (target) VALUES ('a');
INSERT INTO t1_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0170 (target) VALUES ('Hello');
INSERT INTO t1_a0170 (target) VALUES ('你好');
INSERT INTO t1_a0170 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0170 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0170 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0170 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0170 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0170 (target) VALUES ('');
INSERT INTO t1_a0170 (target) VALUES ('a');
INSERT INTO t1_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0170 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0170 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0170 (target) VALUES ('');
INSERT INTO t2_a0170 (target) VALUES ('a');
INSERT INTO t2_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0170 (target) VALUES ('Hello');
INSERT INTO t2_a0170 (target) VALUES ('你好');
INSERT INTO t2_a0170 (target) VALUES ('🎉');
INSERT INTO t2_a0170 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0170 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0170 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0170 (target) VALUES ('');
INSERT INTO t2_a0170 (target) VALUES ('a');
INSERT INTO t2_a0170 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0170' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0170
   WHERE id NOT IN (SELECT id FROM t2_a0170)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0170
   WHERE id NOT IN (SELECT id FROM t1_a0170)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0170 a JOIN t2_a0170 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0171
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0171, t2_a0171;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0171 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0171 (target) VALUES ('');
INSERT INTO t1_a0171 (target) VALUES ('a');
INSERT INTO t1_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0171 (target) VALUES ('Hello');
INSERT INTO t1_a0171 (target) VALUES ('你好');
INSERT INTO t1_a0171 (target) VALUES ('🎉');
INSERT INTO t1_a0171 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0171 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0171 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0171 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0171 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0171 (target) VALUES ('');
INSERT INTO t1_a0171 (target) VALUES ('a');
INSERT INTO t1_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0171 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0171 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0171 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0171 (target) VALUES ('');
INSERT INTO t2_a0171 (target) VALUES ('a');
INSERT INTO t2_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0171 (target) VALUES ('Hello');
INSERT INTO t2_a0171 (target) VALUES ('你好');
INSERT INTO t2_a0171 (target) VALUES ('🎉');
INSERT INTO t2_a0171 (target) VALUES (NULL);
INSERT INTO t2_a0171 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0171 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0171 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0171 (target) VALUES ('');
INSERT INTO t2_a0171 (target) VALUES ('a');
INSERT INTO t2_a0171 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0171 (target) VALUES (NULL);
SELECT 'TC-A0171' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0171
   WHERE id NOT IN (SELECT id FROM t2_a0171)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0171
   WHERE id NOT IN (SELECT id FROM t1_a0171)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0171 a JOIN t2_a0171 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0172
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0172, t2_a0172;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0172 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0172 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0172 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0172 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0172' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0172
   WHERE id NOT IN (SELECT id FROM t2_a0172)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0172
   WHERE id NOT IN (SELECT id FROM t1_a0172)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0172 a JOIN t2_a0172 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0173
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0173, t2_a0173;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0173 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0173 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0173 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0173 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0173 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0173 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0173 (target) VALUES ('');
INSERT INTO t1_a0173 (target) VALUES ('a');
INSERT INTO t1_a0173 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0173 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0173 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0173 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0173 (target) VALUES ('');
INSERT INTO t2_a0173 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0173 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0173 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0173 (target) VALUES ('');
INSERT INTO t2_a0173 (target) VALUES ('a');
INSERT INTO t2_a0173 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0173 (target) VALUES (NULL);
SELECT 'TC-A0173' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0173
   WHERE id NOT IN (SELECT id FROM t2_a0173)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0173
   WHERE id NOT IN (SELECT id FROM t1_a0173)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0173 a JOIN t2_a0173 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0174
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0174, t2_a0174;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0174 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0174 (target) VALUES ('');
INSERT INTO t1_a0174 (target) VALUES ('a');
INSERT INTO t1_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0174 (target) VALUES ('Hello');
INSERT INTO t1_a0174 (target) VALUES ('你好');
INSERT INTO t1_a0174 (target) VALUES ('🎉');
INSERT INTO t1_a0174 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0174 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0174 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0174 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0174 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0174 (target) VALUES ('');
INSERT INTO t1_a0174 (target) VALUES ('a');
INSERT INTO t1_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0174 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0174 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0174 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0174 (target) VALUES ('');
INSERT INTO t2_a0174 (target) VALUES ('a');
INSERT INTO t2_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0174 (target) VALUES ('Hello');
INSERT INTO t2_a0174 (target) VALUES ('你好');
INSERT INTO t2_a0174 (target) VALUES ('🎉');
INSERT INTO t2_a0174 (target) VALUES (NULL);
INSERT INTO t2_a0174 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0174 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0174 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0174 (target) VALUES ('');
INSERT INTO t2_a0174 (target) VALUES ('a');
INSERT INTO t2_a0174 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0174 (target) VALUES (NULL);
SELECT 'TC-A0174' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0174
   WHERE id NOT IN (SELECT id FROM t2_a0174)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0174
   WHERE id NOT IN (SELECT id FROM t1_a0174)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0174 a JOIN t2_a0174 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0175
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0175, t2_a0175;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0175 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0175 (target) VALUES ('');
INSERT INTO t1_a0175 (target) VALUES ('a');
INSERT INTO t1_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0175 (target) VALUES ('Hello');
INSERT INTO t1_a0175 (target) VALUES ('你好');
INSERT INTO t1_a0175 (target) VALUES ('🎉');
INSERT INTO t1_a0175 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0175 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0175 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0175 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0175 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0175 (target) VALUES ('');
INSERT INTO t1_a0175 (target) VALUES ('a');
INSERT INTO t1_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0175 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0175 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0175 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0175 (target) VALUES ('');
INSERT INTO t2_a0175 (target) VALUES ('a');
INSERT INTO t2_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0175 (target) VALUES ('Hello');
INSERT INTO t2_a0175 (target) VALUES ('你好');
INSERT INTO t2_a0175 (target) VALUES ('🎉');
INSERT INTO t2_a0175 (target) VALUES (NULL);
INSERT INTO t2_a0175 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0175 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0175 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0175 (target) VALUES ('');
INSERT INTO t2_a0175 (target) VALUES ('a');
INSERT INTO t2_a0175 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0175 (target) VALUES (NULL);
SELECT 'TC-A0175' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0175
   WHERE id NOT IN (SELECT id FROM t2_a0175)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0175
   WHERE id NOT IN (SELECT id FROM t1_a0175)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0175 a JOIN t2_a0175 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0176
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0176, t2_a0176;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0176 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0176 (target) VALUES ('');
INSERT INTO t1_a0176 (target) VALUES ('a');
INSERT INTO t1_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0176 (target) VALUES ('Hello');
INSERT INTO t1_a0176 (target) VALUES ('你好');
INSERT INTO t1_a0176 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0176 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0176 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0176 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0176 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0176 (target) VALUES ('');
INSERT INTO t1_a0176 (target) VALUES ('a');
INSERT INTO t1_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0176 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0176 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0176 (target) VALUES ('');
INSERT INTO t2_a0176 (target) VALUES ('a');
INSERT INTO t2_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0176 (target) VALUES ('Hello');
INSERT INTO t2_a0176 (target) VALUES ('你好');
INSERT INTO t2_a0176 (target) VALUES ('🎉');
INSERT INTO t2_a0176 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0176 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0176 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0176 (target) VALUES ('');
INSERT INTO t2_a0176 (target) VALUES ('a');
INSERT INTO t2_a0176 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0176' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0176
   WHERE id NOT IN (SELECT id FROM t2_a0176)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0176
   WHERE id NOT IN (SELECT id FROM t1_a0176)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0176 a JOIN t2_a0176 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0177
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0177, t2_a0177;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0177 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0177 (target) VALUES ('');
INSERT INTO t1_a0177 (target) VALUES ('a');
INSERT INTO t1_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0177 (target) VALUES ('Hello');
INSERT INTO t1_a0177 (target) VALUES ('你好');
INSERT INTO t1_a0177 (target) VALUES ('🎉');
INSERT INTO t1_a0177 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0177 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0177 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0177 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0177 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0177 (target) VALUES ('');
INSERT INTO t1_a0177 (target) VALUES ('a');
INSERT INTO t1_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0177 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0177 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0177 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0177 (target) VALUES ('');
INSERT INTO t2_a0177 (target) VALUES ('a');
INSERT INTO t2_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0177 (target) VALUES ('Hello');
INSERT INTO t2_a0177 (target) VALUES ('你好');
INSERT INTO t2_a0177 (target) VALUES ('🎉');
INSERT INTO t2_a0177 (target) VALUES (NULL);
INSERT INTO t2_a0177 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0177 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0177 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0177 (target) VALUES ('');
INSERT INTO t2_a0177 (target) VALUES ('a');
INSERT INTO t2_a0177 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0177 (target) VALUES (NULL);
SELECT 'TC-A0177' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0177
   WHERE id NOT IN (SELECT id FROM t2_a0177)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0177
   WHERE id NOT IN (SELECT id FROM t1_a0177)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0177 a JOIN t2_a0177 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0178
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0178, t2_a0178;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0178 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0178 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0178 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0178 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0178 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0178 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0178 (target) VALUES ('');
INSERT INTO t1_a0178 (target) VALUES ('a');
INSERT INTO t1_a0178 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0178 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0178 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0178 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0178 (target) VALUES (NULL);
INSERT INTO t2_a0178 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0178 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0178 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0178 (target) VALUES ('');
INSERT INTO t2_a0178 (target) VALUES ('a');
INSERT INTO t2_a0178 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0178 (target) VALUES (NULL);
SELECT 'TC-A0178' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0178
   WHERE id NOT IN (SELECT id FROM t2_a0178)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0178
   WHERE id NOT IN (SELECT id FROM t1_a0178)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0178 a JOIN t2_a0178 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0179
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0179, t2_a0179;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0179 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0179 (target) VALUES ('');
INSERT INTO t1_a0179 (target) VALUES ('a');
INSERT INTO t1_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0179 (target) VALUES ('Hello');
INSERT INTO t1_a0179 (target) VALUES ('你好');
INSERT INTO t1_a0179 (target) VALUES ('🎉');
INSERT INTO t1_a0179 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0179 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0179 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0179 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0179 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0179 (target) VALUES ('');
INSERT INTO t1_a0179 (target) VALUES ('a');
INSERT INTO t1_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0179 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0179 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0179 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0179 (target) VALUES ('');
INSERT INTO t2_a0179 (target) VALUES ('a');
INSERT INTO t2_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0179 (target) VALUES ('Hello');
INSERT INTO t2_a0179 (target) VALUES ('你好');
INSERT INTO t2_a0179 (target) VALUES ('🎉');
INSERT INTO t2_a0179 (target) VALUES (NULL);
INSERT INTO t2_a0179 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0179 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0179 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0179 (target) VALUES ('');
INSERT INTO t2_a0179 (target) VALUES ('a');
INSERT INTO t2_a0179 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0179 (target) VALUES (NULL);
SELECT 'TC-A0179' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0179
   WHERE id NOT IN (SELECT id FROM t2_a0179)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0179
   WHERE id NOT IN (SELECT id FROM t1_a0179)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0179 a JOIN t2_a0179 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0180
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0180, t2_a0180;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0180 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0180 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0180 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0180 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0180' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0180
   WHERE id NOT IN (SELECT id FROM t2_a0180)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0180
   WHERE id NOT IN (SELECT id FROM t1_a0180)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0180 a JOIN t2_a0180 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0181
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0181, t2_a0181;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0181 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0181 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0181 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0181 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0181' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0181
   WHERE id NOT IN (SELECT id FROM t2_a0181)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0181
   WHERE id NOT IN (SELECT id FROM t1_a0181)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0181 a JOIN t2_a0181 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0182
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0182, t2_a0182;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0182 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0182 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0182 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(65)
CREATE TABLE t2_a0182 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(65) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0182' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0182
   WHERE id NOT IN (SELECT id FROM t2_a0182)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0182
   WHERE id NOT IN (SELECT id FROM t1_a0182)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0182 a JOIN t2_a0182 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0183
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0183, t2_a0183;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0183 (
  target VARCHAR(64) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0183 (target) VALUES ('');
INSERT INTO t1_a0183 (target) VALUES ('a');
INSERT INTO t1_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0183 (target) VALUES ('Hello');
INSERT INTO t1_a0183 (target) VALUES ('你好');
INSERT INTO t1_a0183 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0183 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0183 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0183 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0183 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0183 (target) VALUES ('');
INSERT INTO t1_a0183 (target) VALUES ('a');
INSERT INTO t1_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0183 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(64)
CREATE TABLE t2_a0183 (
  target VARCHAR(64) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0183 (target) VALUES ('');
INSERT INTO t2_a0183 (target) VALUES ('a');
INSERT INTO t2_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0183 (target) VALUES ('Hello');
INSERT INTO t2_a0183 (target) VALUES ('你好');
INSERT INTO t2_a0183 (target) VALUES ('🎉');
INSERT INTO t2_a0183 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0183 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0183 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0183 (target) VALUES ('');
INSERT INTO t2_a0183 (target) VALUES ('a');
INSERT INTO t2_a0183 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0183' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0183
   WHERE id NOT IN (SELECT id FROM t2_a0183)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0183
   WHERE id NOT IN (SELECT id FROM t1_a0183)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0183 a JOIN t2_a0183 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0184
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0184, t2_tc_aa0184;
CREATE TABLE t1_tc_aa0184 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(64) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0184 (target) VALUES ('');
INSERT INTO t1_tc_aa0184 (target) VALUES ('a');
INSERT INTO t1_tc_aa0184 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0184 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0184 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0184 MODIFY target VARCHAR(65) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0184 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0184 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0184 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0184' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0184' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0185
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0185, t2_tc_aa0185;
CREATE TABLE t1_tc_aa0185 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(64) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0185 (target) VALUES ('');
INSERT INTO t1_tc_aa0185 (target) VALUES ('a');
INSERT INTO t1_tc_aa0185 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0185 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0185 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0185 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_aa0185 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0185 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0185 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0185' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0185' AND column_name='target' AND character_set_name='utf8mb4';

-- Test Case: TC-AA0186
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0186, t2_tc_aa0186;
CREATE TABLE t1_tc_aa0186 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0186 (target) VALUES ('');
INSERT INTO t1_tc_aa0186 (target) VALUES ('a');
INSERT INTO t1_tc_aa0186 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0186 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0186 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0186 MODIFY target VARCHAR(65) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0186 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0186 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0186 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0186' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0186' AND column_name='target' AND collation_name='utf8mb4_bin';

-- Test Case: TC-A0187
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0187, t2_a0187;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0187 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0187 (target) VALUES ('');
INSERT INTO t1_a0187 (target) VALUES ('a');
INSERT INTO t1_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0187 (target) VALUES ('Hello');
INSERT INTO t1_a0187 (target) VALUES ('你好');
INSERT INTO t1_a0187 (target) VALUES ('🎉');
INSERT INTO t1_a0187 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0187 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0187 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0187 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0187 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0187 (target) VALUES ('');
INSERT INTO t1_a0187 (target) VALUES ('a');
INSERT INTO t1_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0187 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0187 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0187 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0187 (target) VALUES ('');
INSERT INTO t2_a0187 (target) VALUES ('a');
INSERT INTO t2_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0187 (target) VALUES ('Hello');
INSERT INTO t2_a0187 (target) VALUES ('你好');
INSERT INTO t2_a0187 (target) VALUES ('🎉');
INSERT INTO t2_a0187 (target) VALUES (NULL);
INSERT INTO t2_a0187 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0187 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0187 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0187 (target) VALUES ('');
INSERT INTO t2_a0187 (target) VALUES ('a');
INSERT INTO t2_a0187 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0187 (target) VALUES (NULL);
SELECT 'TC-A0187' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0187
   WHERE id NOT IN (SELECT id FROM t2_a0187)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0187
   WHERE id NOT IN (SELECT id FROM t1_a0187)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0187 a JOIN t2_a0187 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0188
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0188, t2_a0188;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0188 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0188 (target) VALUES ('');
INSERT INTO t1_a0188 (target) VALUES ('a');
INSERT INTO t1_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0188 (target) VALUES ('Hello');
INSERT INTO t1_a0188 (target) VALUES ('你好');
INSERT INTO t1_a0188 (target) VALUES ('🎉');
INSERT INTO t1_a0188 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0188 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0188 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0188 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0188 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0188 (target) VALUES ('');
INSERT INTO t1_a0188 (target) VALUES ('a');
INSERT INTO t1_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0188 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0188 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0188 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0188 (target) VALUES ('');
INSERT INTO t2_a0188 (target) VALUES ('a');
INSERT INTO t2_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0188 (target) VALUES ('Hello');
INSERT INTO t2_a0188 (target) VALUES ('你好');
INSERT INTO t2_a0188 (target) VALUES ('🎉');
INSERT INTO t2_a0188 (target) VALUES (NULL);
INSERT INTO t2_a0188 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0188 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0188 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0188 (target) VALUES ('');
INSERT INTO t2_a0188 (target) VALUES ('a');
INSERT INTO t2_a0188 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0188 (target) VALUES (NULL);
SELECT 'TC-A0188' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0188
   WHERE id NOT IN (SELECT id FROM t2_a0188)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0188
   WHERE id NOT IN (SELECT id FROM t1_a0188)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0188 a JOIN t2_a0188 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0189
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0189, t2_a0189;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0189 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0189 (target) VALUES ('');
INSERT INTO t1_a0189 (target) VALUES ('a');
INSERT INTO t1_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0189 (target) VALUES ('Hello');
INSERT INTO t1_a0189 (target) VALUES ('你好');
INSERT INTO t1_a0189 (target) VALUES ('🎉');
INSERT INTO t1_a0189 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0189 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0189 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0189 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0189 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0189 (target) VALUES ('');
INSERT INTO t1_a0189 (target) VALUES ('a');
INSERT INTO t1_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0189 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0189 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0189 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0189 (target) VALUES ('');
INSERT INTO t2_a0189 (target) VALUES ('a');
INSERT INTO t2_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0189 (target) VALUES ('Hello');
INSERT INTO t2_a0189 (target) VALUES ('你好');
INSERT INTO t2_a0189 (target) VALUES ('🎉');
INSERT INTO t2_a0189 (target) VALUES (NULL);
INSERT INTO t2_a0189 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0189 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0189 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0189 (target) VALUES ('');
INSERT INTO t2_a0189 (target) VALUES ('a');
INSERT INTO t2_a0189 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0189 (target) VALUES (NULL);
SELECT 'TC-A0189' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0189
   WHERE id NOT IN (SELECT id FROM t2_a0189)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0189
   WHERE id NOT IN (SELECT id FROM t1_a0189)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0189 a JOIN t2_a0189 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0190
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0190, t2_a0190;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0190 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0190 (target) VALUES ('');
INSERT INTO t1_a0190 (target) VALUES ('a');
INSERT INTO t1_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0190 (target) VALUES ('Hello');
INSERT INTO t1_a0190 (target) VALUES ('你好');
INSERT INTO t1_a0190 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0190 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0190 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0190 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0190 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0190 (target) VALUES ('');
INSERT INTO t1_a0190 (target) VALUES ('a');
INSERT INTO t1_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0190 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(100)
CREATE TABLE t2_a0190 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0190 (target) VALUES ('');
INSERT INTO t2_a0190 (target) VALUES ('a');
INSERT INTO t2_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0190 (target) VALUES ('Hello');
INSERT INTO t2_a0190 (target) VALUES ('你好');
INSERT INTO t2_a0190 (target) VALUES ('🎉');
INSERT INTO t2_a0190 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0190 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0190 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0190 (target) VALUES ('');
INSERT INTO t2_a0190 (target) VALUES ('a');
INSERT INTO t2_a0190 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0190' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0190
   WHERE id NOT IN (SELECT id FROM t2_a0190)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0190
   WHERE id NOT IN (SELECT id FROM t1_a0190)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0190 a JOIN t2_a0190 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0191
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0191, t2_a0191;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0191 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0191 (target) VALUES ('');
INSERT INTO t1_a0191 (target) VALUES ('a');
INSERT INTO t1_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0191 (target) VALUES ('Hello');
INSERT INTO t1_a0191 (target) VALUES ('你好');
INSERT INTO t1_a0191 (target) VALUES ('🎉');
INSERT INTO t1_a0191 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0191 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0191 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0191 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0191 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0191 (target) VALUES ('');
INSERT INTO t1_a0191 (target) VALUES ('a');
INSERT INTO t1_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0191 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0191 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0191 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0191 (target) VALUES ('');
INSERT INTO t2_a0191 (target) VALUES ('a');
INSERT INTO t2_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0191 (target) VALUES ('Hello');
INSERT INTO t2_a0191 (target) VALUES ('你好');
INSERT INTO t2_a0191 (target) VALUES ('🎉');
INSERT INTO t2_a0191 (target) VALUES (NULL);
INSERT INTO t2_a0191 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0191 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0191 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0191 (target) VALUES ('');
INSERT INTO t2_a0191 (target) VALUES ('a');
INSERT INTO t2_a0191 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0191 (target) VALUES (NULL);
SELECT 'TC-A0191' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0191
   WHERE id NOT IN (SELECT id FROM t2_a0191)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0191
   WHERE id NOT IN (SELECT id FROM t1_a0191)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0191 a JOIN t2_a0191 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0192
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0192, t2_a0192;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0192 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0192 (target) VALUES ('');
INSERT INTO t1_a0192 (target) VALUES ('a');
INSERT INTO t1_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0192 (target) VALUES ('Hello');
INSERT INTO t1_a0192 (target) VALUES ('你好');
INSERT INTO t1_a0192 (target) VALUES ('🎉');
INSERT INTO t1_a0192 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0192 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0192 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0192 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0192 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0192 (target) VALUES ('');
INSERT INTO t1_a0192 (target) VALUES ('a');
INSERT INTO t1_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0192 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0192 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0192 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0192 (target) VALUES ('');
INSERT INTO t2_a0192 (target) VALUES ('a');
INSERT INTO t2_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0192 (target) VALUES ('Hello');
INSERT INTO t2_a0192 (target) VALUES ('你好');
INSERT INTO t2_a0192 (target) VALUES ('🎉');
INSERT INTO t2_a0192 (target) VALUES (NULL);
INSERT INTO t2_a0192 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0192 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0192 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0192 (target) VALUES ('');
INSERT INTO t2_a0192 (target) VALUES ('a');
INSERT INTO t2_a0192 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0192 (target) VALUES (NULL);
SELECT 'TC-A0192' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0192
   WHERE id NOT IN (SELECT id FROM t2_a0192)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0192
   WHERE id NOT IN (SELECT id FROM t1_a0192)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0192 a JOIN t2_a0192 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0193
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0193, t2_a0193;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0193 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0193 (target) VALUES ('');
INSERT INTO t1_a0193 (target) VALUES ('a');
INSERT INTO t1_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0193 (target) VALUES ('Hello');
INSERT INTO t1_a0193 (target) VALUES ('你好');
INSERT INTO t1_a0193 (target) VALUES ('🎉');
INSERT INTO t1_a0193 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0193 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0193 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0193 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0193 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0193 (target) VALUES ('');
INSERT INTO t1_a0193 (target) VALUES ('a');
INSERT INTO t1_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0193 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0193 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0193 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0193 (target) VALUES ('');
INSERT INTO t2_a0193 (target) VALUES ('a');
INSERT INTO t2_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0193 (target) VALUES ('Hello');
INSERT INTO t2_a0193 (target) VALUES ('你好');
INSERT INTO t2_a0193 (target) VALUES ('🎉');
INSERT INTO t2_a0193 (target) VALUES (NULL);
INSERT INTO t2_a0193 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0193 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0193 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0193 (target) VALUES ('');
INSERT INTO t2_a0193 (target) VALUES ('a');
INSERT INTO t2_a0193 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0193 (target) VALUES (NULL);
SELECT 'TC-A0193' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0193
   WHERE id NOT IN (SELECT id FROM t2_a0193)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0193
   WHERE id NOT IN (SELECT id FROM t1_a0193)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0193 a JOIN t2_a0193 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0194
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0194, t2_a0194;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0194 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0194 (target) VALUES ('');
INSERT INTO t1_a0194 (target) VALUES ('a');
INSERT INTO t1_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0194 (target) VALUES ('Hello');
INSERT INTO t1_a0194 (target) VALUES ('你好');
INSERT INTO t1_a0194 (target) VALUES ('🎉');
INSERT INTO t1_a0194 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0194 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0194 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0194 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0194 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0194 (target) VALUES ('');
INSERT INTO t1_a0194 (target) VALUES ('a');
INSERT INTO t1_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0194 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0194 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0194 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0194 (target) VALUES ('');
INSERT INTO t2_a0194 (target) VALUES ('a');
INSERT INTO t2_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0194 (target) VALUES ('Hello');
INSERT INTO t2_a0194 (target) VALUES ('你好');
INSERT INTO t2_a0194 (target) VALUES ('🎉');
INSERT INTO t2_a0194 (target) VALUES (NULL);
INSERT INTO t2_a0194 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0194 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0194 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0194 (target) VALUES ('');
INSERT INTO t2_a0194 (target) VALUES ('a');
INSERT INTO t2_a0194 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0194 (target) VALUES (NULL);
SELECT 'TC-A0194' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0194
   WHERE id NOT IN (SELECT id FROM t2_a0194)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0194
   WHERE id NOT IN (SELECT id FROM t1_a0194)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0194 a JOIN t2_a0194 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0195
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0195, t2_a0195;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0195 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0195 (target) VALUES ('');
INSERT INTO t1_a0195 (target) VALUES ('a');
INSERT INTO t1_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0195 (target) VALUES ('Hello');
INSERT INTO t1_a0195 (target) VALUES ('你好');
INSERT INTO t1_a0195 (target) VALUES ('🎉');
INSERT INTO t1_a0195 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0195 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0195 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0195 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0195 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0195 (target) VALUES ('');
INSERT INTO t1_a0195 (target) VALUES ('a');
INSERT INTO t1_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0195 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0195 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0195 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0195 (target) VALUES ('');
INSERT INTO t2_a0195 (target) VALUES ('a');
INSERT INTO t2_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0195 (target) VALUES ('Hello');
INSERT INTO t2_a0195 (target) VALUES ('你好');
INSERT INTO t2_a0195 (target) VALUES ('🎉');
INSERT INTO t2_a0195 (target) VALUES (NULL);
INSERT INTO t2_a0195 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0195 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0195 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0195 (target) VALUES ('');
INSERT INTO t2_a0195 (target) VALUES ('a');
INSERT INTO t2_a0195 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0195 (target) VALUES (NULL);
SELECT 'TC-A0195' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0195
   WHERE id NOT IN (SELECT id FROM t2_a0195)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0195
   WHERE id NOT IN (SELECT id FROM t1_a0195)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0195 a JOIN t2_a0195 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0196
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0196, t2_a0196;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0196 (
  target VARCHAR(100) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0196 (target) VALUES ('');
INSERT INTO t1_a0196 (target) VALUES ('a');
INSERT INTO t1_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0196 (target) VALUES ('Hello');
INSERT INTO t1_a0196 (target) VALUES ('你好');
INSERT INTO t1_a0196 (target) VALUES ('🎉');
INSERT INTO t1_a0196 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0196 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0196 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0196 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0196 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0196 (target) VALUES ('');
INSERT INTO t1_a0196 (target) VALUES ('a');
INSERT INTO t1_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0196 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0196 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0196 (
  target VARCHAR(200) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0196 (target) VALUES ('');
INSERT INTO t2_a0196 (target) VALUES ('a');
INSERT INTO t2_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0196 (target) VALUES ('Hello');
INSERT INTO t2_a0196 (target) VALUES ('你好');
INSERT INTO t2_a0196 (target) VALUES ('🎉');
INSERT INTO t2_a0196 (target) VALUES (NULL);
INSERT INTO t2_a0196 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0196 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0196 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0196 (target) VALUES ('');
INSERT INTO t2_a0196 (target) VALUES ('a');
INSERT INTO t2_a0196 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0196 (target) VALUES (NULL);
SELECT 'TC-A0196' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0196
   WHERE id NOT IN (SELECT id FROM t2_a0196)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0196
   WHERE id NOT IN (SELECT id FROM t1_a0196)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0196 a JOIN t2_a0196 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0197
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0197, t2_a0197;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0197 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(100) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0197 (target) VALUES ('');
INSERT INTO t1_a0197 (target) VALUES ('a');
INSERT INTO t1_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0197 (target) VALUES ('Hello');
INSERT INTO t1_a0197 (target) VALUES ('你好');
INSERT INTO t1_a0197 (target) VALUES ('🎉');
INSERT INTO t1_a0197 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0197 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0197 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0197 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0197 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0197 (target) VALUES ('');
INSERT INTO t1_a0197 (target) VALUES ('a');
INSERT INTO t1_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0197 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0197 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0197 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target VARCHAR(200) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0197 (target) VALUES ('');
INSERT INTO t2_a0197 (target) VALUES ('a');
INSERT INTO t2_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0197 (target) VALUES ('Hello');
INSERT INTO t2_a0197 (target) VALUES ('你好');
INSERT INTO t2_a0197 (target) VALUES ('🎉');
INSERT INTO t2_a0197 (target) VALUES (NULL);
INSERT INTO t2_a0197 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0197 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0197 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0197 (target) VALUES ('');
INSERT INTO t2_a0197 (target) VALUES ('a');
INSERT INTO t2_a0197 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0197 (target) VALUES (NULL);
SELECT 'TC-A0197' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0197
   WHERE id NOT IN (SELECT id FROM t2_a0197)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0197
   WHERE id NOT IN (SELECT id FROM t1_a0197)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0197 a JOIN t2_a0197 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0198
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0198, t2_a0198;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0198 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0198 (target) VALUES ('');
INSERT INTO t1_a0198 (target) VALUES ('a');
INSERT INTO t1_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0198 (target) VALUES ('Hello');
INSERT INTO t1_a0198 (target) VALUES ('你好');
INSERT INTO t1_a0198 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0198 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0198 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0198 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0198 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0198 (target) VALUES ('');
INSERT INTO t1_a0198 (target) VALUES ('a');
INSERT INTO t1_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0198 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0198 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0198 (target) VALUES ('');
INSERT INTO t2_a0198 (target) VALUES ('a');
INSERT INTO t2_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0198 (target) VALUES ('Hello');
INSERT INTO t2_a0198 (target) VALUES ('你好');
INSERT INTO t2_a0198 (target) VALUES ('🎉');
INSERT INTO t2_a0198 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0198 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0198 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0198 (target) VALUES ('');
INSERT INTO t2_a0198 (target) VALUES ('a');
INSERT INTO t2_a0198 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0198' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0198
   WHERE id NOT IN (SELECT id FROM t2_a0198)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0198
   WHERE id NOT IN (SELECT id FROM t1_a0198)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0198 a JOIN t2_a0198 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0199
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0199, t2_a0199;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0199 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0199 (target) VALUES ('');
INSERT INTO t1_a0199 (target) VALUES ('a');
INSERT INTO t1_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0199 (target) VALUES ('Hello');
INSERT INTO t1_a0199 (target) VALUES ('你好');
INSERT INTO t1_a0199 (target) VALUES ('🎉');
INSERT INTO t1_a0199 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0199 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0199 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0199 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0199 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0199 (target) VALUES ('');
INSERT INTO t1_a0199 (target) VALUES ('a');
INSERT INTO t1_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0199 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0199 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0199 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0199 (target) VALUES ('');
INSERT INTO t2_a0199 (target) VALUES ('a');
INSERT INTO t2_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0199 (target) VALUES ('Hello');
INSERT INTO t2_a0199 (target) VALUES ('你好');
INSERT INTO t2_a0199 (target) VALUES ('🎉');
INSERT INTO t2_a0199 (target) VALUES (NULL);
INSERT INTO t2_a0199 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0199 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0199 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0199 (target) VALUES ('');
INSERT INTO t2_a0199 (target) VALUES ('a');
INSERT INTO t2_a0199 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0199 (target) VALUES (NULL);
SELECT 'TC-A0199' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0199
   WHERE id NOT IN (SELECT id FROM t2_a0199)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0199
   WHERE id NOT IN (SELECT id FROM t1_a0199)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0199 a JOIN t2_a0199 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0200
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0200, t2_a0200;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0200 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0200 (target) VALUES ('');
INSERT INTO t1_a0200 (target) VALUES ('a');
INSERT INTO t1_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0200 (target) VALUES ('Hello');
INSERT INTO t1_a0200 (target) VALUES ('你好');
INSERT INTO t1_a0200 (target) VALUES ('🎉');
INSERT INTO t1_a0200 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0200 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0200 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0200 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0200 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0200 (target) VALUES ('');
INSERT INTO t1_a0200 (target) VALUES ('a');
INSERT INTO t1_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0200 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0200 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0200 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0200 (target) VALUES ('');
INSERT INTO t2_a0200 (target) VALUES ('a');
INSERT INTO t2_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0200 (target) VALUES ('Hello');
INSERT INTO t2_a0200 (target) VALUES ('你好');
INSERT INTO t2_a0200 (target) VALUES ('🎉');
INSERT INTO t2_a0200 (target) VALUES (NULL);
INSERT INTO t2_a0200 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0200 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0200 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0200 (target) VALUES ('');
INSERT INTO t2_a0200 (target) VALUES ('a');
INSERT INTO t2_a0200 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0200 (target) VALUES (NULL);
SELECT 'TC-A0200' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0200
   WHERE id NOT IN (SELECT id FROM t2_a0200)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0200
   WHERE id NOT IN (SELECT id FROM t1_a0200)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0200 a JOIN t2_a0200 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0201
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0201, t2_a0201;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0201 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0201 (target) VALUES ('');
INSERT INTO t1_a0201 (target) VALUES ('a');
INSERT INTO t1_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0201 (target) VALUES ('Hello');
INSERT INTO t1_a0201 (target) VALUES ('你好');
INSERT INTO t1_a0201 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0201 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0201 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0201 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0201 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0201 (target) VALUES ('');
INSERT INTO t1_a0201 (target) VALUES ('a');
INSERT INTO t1_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0201 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0201 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0201 (target) VALUES ('');
INSERT INTO t2_a0201 (target) VALUES ('a');
INSERT INTO t2_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0201 (target) VALUES ('Hello');
INSERT INTO t2_a0201 (target) VALUES ('你好');
INSERT INTO t2_a0201 (target) VALUES ('🎉');
INSERT INTO t2_a0201 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0201 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0201 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0201 (target) VALUES ('');
INSERT INTO t2_a0201 (target) VALUES ('a');
INSERT INTO t2_a0201 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0201' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0201
   WHERE id NOT IN (SELECT id FROM t2_a0201)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0201
   WHERE id NOT IN (SELECT id FROM t1_a0201)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0201 a JOIN t2_a0201 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0202
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0202, t2_a0202;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0202 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0202 (target) VALUES ('');
INSERT INTO t1_a0202 (target) VALUES ('a');
INSERT INTO t1_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0202 (target) VALUES ('Hello');
INSERT INTO t1_a0202 (target) VALUES ('你好');
INSERT INTO t1_a0202 (target) VALUES ('🎉');
INSERT INTO t1_a0202 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0202 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0202 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0202 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0202 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0202 (target) VALUES ('');
INSERT INTO t1_a0202 (target) VALUES ('a');
INSERT INTO t1_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0202 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0202 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0202 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0202 (target) VALUES ('');
INSERT INTO t2_a0202 (target) VALUES ('a');
INSERT INTO t2_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0202 (target) VALUES ('Hello');
INSERT INTO t2_a0202 (target) VALUES ('你好');
INSERT INTO t2_a0202 (target) VALUES ('🎉');
INSERT INTO t2_a0202 (target) VALUES (NULL);
INSERT INTO t2_a0202 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0202 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0202 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0202 (target) VALUES ('');
INSERT INTO t2_a0202 (target) VALUES ('a');
INSERT INTO t2_a0202 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0202 (target) VALUES (NULL);
SELECT 'TC-A0202' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0202
   WHERE id NOT IN (SELECT id FROM t2_a0202)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0202
   WHERE id NOT IN (SELECT id FROM t1_a0202)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0202 a JOIN t2_a0202 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0203
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0203, t2_a0203;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0203 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0203 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0203 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0203 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0203' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0203
   WHERE id NOT IN (SELECT id FROM t2_a0203)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0203
   WHERE id NOT IN (SELECT id FROM t1_a0203)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0203 a JOIN t2_a0203 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0204
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0204, t2_a0204;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0204 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0204 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0204 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0204 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0204 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0204 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0204 (target) VALUES ('');
INSERT INTO t1_a0204 (target) VALUES ('a');
INSERT INTO t1_a0204 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0204 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0204 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0204 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0204 (target) VALUES ('');
INSERT INTO t2_a0204 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0204 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0204 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0204 (target) VALUES ('');
INSERT INTO t2_a0204 (target) VALUES ('a');
INSERT INTO t2_a0204 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0204 (target) VALUES (NULL);
SELECT 'TC-A0204' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0204
   WHERE id NOT IN (SELECT id FROM t2_a0204)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0204
   WHERE id NOT IN (SELECT id FROM t1_a0204)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0204 a JOIN t2_a0204 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0205
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0205, t2_a0205;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0205 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0205 (target) VALUES ('');
INSERT INTO t1_a0205 (target) VALUES ('a');
INSERT INTO t1_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0205 (target) VALUES ('Hello');
INSERT INTO t1_a0205 (target) VALUES ('你好');
INSERT INTO t1_a0205 (target) VALUES ('🎉');
INSERT INTO t1_a0205 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0205 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0205 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0205 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0205 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0205 (target) VALUES ('');
INSERT INTO t1_a0205 (target) VALUES ('a');
INSERT INTO t1_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0205 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0205 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0205 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0205 (target) VALUES ('');
INSERT INTO t2_a0205 (target) VALUES ('a');
INSERT INTO t2_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0205 (target) VALUES ('Hello');
INSERT INTO t2_a0205 (target) VALUES ('你好');
INSERT INTO t2_a0205 (target) VALUES ('🎉');
INSERT INTO t2_a0205 (target) VALUES (NULL);
INSERT INTO t2_a0205 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0205 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0205 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0205 (target) VALUES ('');
INSERT INTO t2_a0205 (target) VALUES ('a');
INSERT INTO t2_a0205 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0205 (target) VALUES (NULL);
SELECT 'TC-A0205' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0205
   WHERE id NOT IN (SELECT id FROM t2_a0205)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0205
   WHERE id NOT IN (SELECT id FROM t1_a0205)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0205 a JOIN t2_a0205 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0206
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0206, t2_a0206;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0206 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0206 (target) VALUES ('');
INSERT INTO t1_a0206 (target) VALUES ('a');
INSERT INTO t1_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0206 (target) VALUES ('Hello');
INSERT INTO t1_a0206 (target) VALUES ('你好');
INSERT INTO t1_a0206 (target) VALUES ('🎉');
INSERT INTO t1_a0206 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0206 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0206 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0206 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0206 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0206 (target) VALUES ('');
INSERT INTO t1_a0206 (target) VALUES ('a');
INSERT INTO t1_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0206 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0206 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0206 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0206 (target) VALUES ('');
INSERT INTO t2_a0206 (target) VALUES ('a');
INSERT INTO t2_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0206 (target) VALUES ('Hello');
INSERT INTO t2_a0206 (target) VALUES ('你好');
INSERT INTO t2_a0206 (target) VALUES ('🎉');
INSERT INTO t2_a0206 (target) VALUES (NULL);
INSERT INTO t2_a0206 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0206 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0206 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0206 (target) VALUES ('');
INSERT INTO t2_a0206 (target) VALUES ('a');
INSERT INTO t2_a0206 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0206 (target) VALUES (NULL);
SELECT 'TC-A0206' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0206
   WHERE id NOT IN (SELECT id FROM t2_a0206)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0206
   WHERE id NOT IN (SELECT id FROM t1_a0206)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0206 a JOIN t2_a0206 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0207
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0207, t2_a0207;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0207 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0207 (target) VALUES ('');
INSERT INTO t1_a0207 (target) VALUES ('a');
INSERT INTO t1_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0207 (target) VALUES ('Hello');
INSERT INTO t1_a0207 (target) VALUES ('你好');
INSERT INTO t1_a0207 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0207 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0207 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0207 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0207 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0207 (target) VALUES ('');
INSERT INTO t1_a0207 (target) VALUES ('a');
INSERT INTO t1_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0207 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0207 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0207 (target) VALUES ('');
INSERT INTO t2_a0207 (target) VALUES ('a');
INSERT INTO t2_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0207 (target) VALUES ('Hello');
INSERT INTO t2_a0207 (target) VALUES ('你好');
INSERT INTO t2_a0207 (target) VALUES ('🎉');
INSERT INTO t2_a0207 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0207 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0207 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0207 (target) VALUES ('');
INSERT INTO t2_a0207 (target) VALUES ('a');
INSERT INTO t2_a0207 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0207' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0207
   WHERE id NOT IN (SELECT id FROM t2_a0207)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0207
   WHERE id NOT IN (SELECT id FROM t1_a0207)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0207 a JOIN t2_a0207 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0208
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0208, t2_a0208;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0208 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0208 (target) VALUES ('');
INSERT INTO t1_a0208 (target) VALUES ('a');
INSERT INTO t1_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0208 (target) VALUES ('Hello');
INSERT INTO t1_a0208 (target) VALUES ('你好');
INSERT INTO t1_a0208 (target) VALUES ('🎉');
INSERT INTO t1_a0208 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0208 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0208 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0208 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0208 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0208 (target) VALUES ('');
INSERT INTO t1_a0208 (target) VALUES ('a');
INSERT INTO t1_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0208 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0208 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0208 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0208 (target) VALUES ('');
INSERT INTO t2_a0208 (target) VALUES ('a');
INSERT INTO t2_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0208 (target) VALUES ('Hello');
INSERT INTO t2_a0208 (target) VALUES ('你好');
INSERT INTO t2_a0208 (target) VALUES ('🎉');
INSERT INTO t2_a0208 (target) VALUES (NULL);
INSERT INTO t2_a0208 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0208 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0208 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0208 (target) VALUES ('');
INSERT INTO t2_a0208 (target) VALUES ('a');
INSERT INTO t2_a0208 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0208 (target) VALUES (NULL);
SELECT 'TC-A0208' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0208
   WHERE id NOT IN (SELECT id FROM t2_a0208)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0208
   WHERE id NOT IN (SELECT id FROM t1_a0208)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0208 a JOIN t2_a0208 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0209
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0209, t2_a0209;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0209 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0209 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0209 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0209 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0209 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0209 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0209 (target) VALUES ('');
INSERT INTO t1_a0209 (target) VALUES ('a');
INSERT INTO t1_a0209 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0209 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0209 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0209 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0209 (target) VALUES (NULL);
INSERT INTO t2_a0209 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0209 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0209 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0209 (target) VALUES ('');
INSERT INTO t2_a0209 (target) VALUES ('a');
INSERT INTO t2_a0209 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0209 (target) VALUES (NULL);
SELECT 'TC-A0209' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0209
   WHERE id NOT IN (SELECT id FROM t2_a0209)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0209
   WHERE id NOT IN (SELECT id FROM t1_a0209)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0209 a JOIN t2_a0209 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0210
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0210, t2_a0210;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0210 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0210 (target) VALUES ('');
INSERT INTO t1_a0210 (target) VALUES ('a');
INSERT INTO t1_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0210 (target) VALUES ('Hello');
INSERT INTO t1_a0210 (target) VALUES ('你好');
INSERT INTO t1_a0210 (target) VALUES ('🎉');
INSERT INTO t1_a0210 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0210 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0210 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0210 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0210 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0210 (target) VALUES ('');
INSERT INTO t1_a0210 (target) VALUES ('a');
INSERT INTO t1_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0210 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0210 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0210 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0210 (target) VALUES ('');
INSERT INTO t2_a0210 (target) VALUES ('a');
INSERT INTO t2_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0210 (target) VALUES ('Hello');
INSERT INTO t2_a0210 (target) VALUES ('你好');
INSERT INTO t2_a0210 (target) VALUES ('🎉');
INSERT INTO t2_a0210 (target) VALUES (NULL);
INSERT INTO t2_a0210 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0210 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0210 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0210 (target) VALUES ('');
INSERT INTO t2_a0210 (target) VALUES ('a');
INSERT INTO t2_a0210 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0210 (target) VALUES (NULL);
SELECT 'TC-A0210' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0210
   WHERE id NOT IN (SELECT id FROM t2_a0210)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0210
   WHERE id NOT IN (SELECT id FROM t1_a0210)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0210 a JOIN t2_a0210 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0211
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0211, t2_a0211;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0211 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0211 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0211 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0211 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0211' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0211
   WHERE id NOT IN (SELECT id FROM t2_a0211)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0211
   WHERE id NOT IN (SELECT id FROM t1_a0211)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0211 a JOIN t2_a0211 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0212
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0212, t2_a0212;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0212 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0212 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0212 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0212 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0212' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0212
   WHERE id NOT IN (SELECT id FROM t2_a0212)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0212
   WHERE id NOT IN (SELECT id FROM t1_a0212)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0212 a JOIN t2_a0212 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0213
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0213, t2_a0213;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0213 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(100) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0213 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0213 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(200)
CREATE TABLE t2_a0213 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target VARCHAR(200) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
SELECT 'TC-A0213' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0213
   WHERE id NOT IN (SELECT id FROM t2_a0213)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0213
   WHERE id NOT IN (SELECT id FROM t1_a0213)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0213 a JOIN t2_a0213 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-A0214
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0214, t2_a0214;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0214 (
  target VARCHAR(100) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0214 (target) VALUES ('');
INSERT INTO t1_a0214 (target) VALUES ('a');
INSERT INTO t1_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0214 (target) VALUES ('Hello');
INSERT INTO t1_a0214 (target) VALUES ('你好');
INSERT INTO t1_a0214 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0214 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0214 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0214 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0214 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0214 (target) VALUES ('');
INSERT INTO t1_a0214 (target) VALUES ('a');
INSERT INTO t1_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0214 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: VARCHAR(100)
CREATE TABLE t2_a0214 (
  target VARCHAR(100) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0214 (target) VALUES ('');
INSERT INTO t2_a0214 (target) VALUES ('a');
INSERT INTO t2_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0214 (target) VALUES ('Hello');
INSERT INTO t2_a0214 (target) VALUES ('你好');
INSERT INTO t2_a0214 (target) VALUES ('🎉');
INSERT INTO t2_a0214 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0214 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0214 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0214 (target) VALUES ('');
INSERT INTO t2_a0214 (target) VALUES ('a');
INSERT INTO t2_a0214 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
SELECT 'TC-A0214' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_a0214
   WHERE id NOT IN (SELECT id FROM t2_a0214)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_a0214
   WHERE id NOT IN (SELECT id FROM t1_a0214)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_a0214 a JOIN t2_a0214 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-AA0215
-- Column attribute preservation: COMMENT
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0215, t2_tc_aa0215;
CREATE TABLE t1_tc_aa0215 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(100) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0215 (target) VALUES ('');
INSERT INTO t1_tc_aa0215 (target) VALUES ('a');
INSERT INTO t1_tc_aa0215 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0215 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0215 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0215 MODIFY target VARCHAR(200) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0215 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0215 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0215 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0215' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0215' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0216
-- Column attribute preservation: CHARSET
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0216, t2_tc_aa0216;
CREATE TABLE t1_tc_aa0216 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(100) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0216 (target) VALUES ('');
INSERT INTO t1_tc_aa0216 (target) VALUES ('a');
INSERT INTO t1_tc_aa0216 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0216 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0216 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0216 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_aa0216 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0216 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0216 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0216' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0216' AND column_name='target' AND character_set_name='utf8mb4';

-- Test Case: TC-AA0217
-- Column attribute preservation: COLLATE
-- Type: VARCHAR(100) -> VARCHAR(200), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0217, t2_tc_aa0217;
CREATE TABLE t1_tc_aa0217 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0217 (target) VALUES ('');
INSERT INTO t1_tc_aa0217 (target) VALUES ('a');
INSERT INTO t1_tc_aa0217 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0217 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0217 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0217 MODIFY target VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0217 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0217 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0217 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0217' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0217' AND column_name='target' AND collation_name='utf8mb4_bin';

