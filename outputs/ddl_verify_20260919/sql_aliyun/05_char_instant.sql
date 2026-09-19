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

-- File 05: CHAR INSTANT

-- Test Case: TC-A0001
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0001, t2_a0001;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0001 (target) VALUES ('');
INSERT INTO t1_a0001 (target) VALUES ('a');
INSERT INTO t1_a0001 (target) VALUES ('x');
INSERT INTO t1_a0001 (target) VALUES ('');
INSERT INTO t1_a0001 (target) VALUES ('a');
INSERT INTO t1_a0001 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0001 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0001 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0002, t2_a0002;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0002 (target) VALUES ('');
INSERT INTO t1_a0002 (target) VALUES ('a');
INSERT INTO t1_a0002 (target) VALUES ('x');
INSERT INTO t1_a0002 (target) VALUES ('');
INSERT INTO t1_a0002 (target) VALUES ('a');
INSERT INTO t1_a0002 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0002 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0002 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0003, t2_a0003;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=latin1;
INSERT INTO t1_a0003 (target) VALUES ('');
INSERT INTO t1_a0003 (target) VALUES ('a');
INSERT INTO t1_a0003 (target) VALUES ('x');
INSERT INTO t1_a0003 (target) VALUES ('');
INSERT INTO t1_a0003 (target) VALUES ('a');
INSERT INTO t1_a0003 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0003 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0003 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0004, t2_a0004;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0004 (target) VALUES ('');
INSERT INTO t1_a0004 (target) VALUES ('a');
INSERT INTO t1_a0004 (target) VALUES ('x');
INSERT INTO t1_a0004 (target) VALUES ('');
INSERT INTO t1_a0004 (target) VALUES ('a');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0004 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(1)
CREATE TABLE t2_a0004 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0005, t2_a0005;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0005 (target) VALUES ('');
INSERT INTO t1_a0005 (target) VALUES ('a');
INSERT INTO t1_a0005 (target) VALUES ('x');
INSERT INTO t1_a0005 (target) VALUES ('');
INSERT INTO t1_a0005 (target) VALUES ('a');
INSERT INTO t1_a0005 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0005 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0005 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0006, t2_a0006;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0006 (target) VALUES ('');
INSERT INTO t1_a0006 (target) VALUES ('a');
INSERT INTO t1_a0006 (target) VALUES ('x');
INSERT INTO t1_a0006 (target) VALUES ('');
INSERT INTO t1_a0006 (target) VALUES ('a');
INSERT INTO t1_a0006 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0006 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0006 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0007, t2_a0007;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0007 (target) VALUES ('');
INSERT INTO t1_a0007 (target) VALUES ('a');
INSERT INTO t1_a0007 (target) VALUES ('x');
INSERT INTO t1_a0007 (target) VALUES ('');
INSERT INTO t1_a0007 (target) VALUES ('a');
INSERT INTO t1_a0007 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0007 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0007 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0008, t2_a0008;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0008 (target) VALUES ('');
INSERT INTO t1_a0008 (target) VALUES ('a');
INSERT INTO t1_a0008 (target) VALUES ('x');
INSERT INTO t1_a0008 (target) VALUES ('');
INSERT INTO t1_a0008 (target) VALUES ('a');
INSERT INTO t1_a0008 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0008 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0008 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0009, t2_a0009;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0009 (target) VALUES ('');
INSERT INTO t1_a0009 (target) VALUES ('a');
INSERT INTO t1_a0009 (target) VALUES ('x');
INSERT INTO t1_a0009 (target) VALUES ('');
INSERT INTO t1_a0009 (target) VALUES ('a');
INSERT INTO t1_a0009 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0009 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0009 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0010, t2_a0010;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0010 (
  target CHAR(1) CHARACTER SET latin1,
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
ALTER TABLE t1_a0010 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0010 (
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0011, t2_a0011;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(1) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0011 (target) VALUES ('');
INSERT INTO t1_a0011 (target) VALUES ('a');
INSERT INTO t1_a0011 (target) VALUES ('x');
INSERT INTO t1_a0011 (target) VALUES ('');
INSERT INTO t1_a0011 (target) VALUES ('a');
INSERT INTO t1_a0011 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0011 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0011 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(2) CHARACTER SET latin1, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0012, t2_a0012;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0012 (target) VALUES ('');
INSERT INTO t1_a0012 (target) VALUES ('a');
INSERT INTO t1_a0012 (target) VALUES ('x');
INSERT INTO t1_a0012 (target) VALUES ('');
INSERT INTO t1_a0012 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0012 MODIFY target CHAR(2) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0012 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 NOT NULL,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0013, t2_a0013;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0013 (target) VALUES ('');
INSERT INTO t1_a0013 (target) VALUES ('a');
INSERT INTO t1_a0013 (target) VALUES ('x');
INSERT INTO t1_a0013 (target) VALUES ('');
INSERT INTO t1_a0013 (target) VALUES ('a');
INSERT INTO t1_a0013 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0013 MODIFY target CHAR(2) CHARACTER SET latin1 DEFAULT '', ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0013 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 DEFAULT '',
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0014, t2_a0014;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0014 (target) VALUES ('');
INSERT INTO t1_a0014 (target) VALUES ('a');
INSERT INTO t1_a0014 (target) VALUES ('x');
INSERT INTO t1_a0014 (target) VALUES ('');
INSERT INTO t1_a0014 (target) VALUES ('a');
INSERT INTO t1_a0014 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0014 MODIFY target CHAR(2) CHARACTER SET latin1 DEFAULT NULL, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0014 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 DEFAULT NULL,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0015, t2_a0015;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0015 (target) VALUES ('');
INSERT INTO t1_a0015 (target) VALUES ('a');
INSERT INTO t1_a0015 (target) VALUES ('x');
INSERT INTO t1_a0015 (target) VALUES ('');
INSERT INTO t1_a0015 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0015 MODIFY target CHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0015 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '',
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0016, t2_a0016;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0016 (target) VALUES ('');
INSERT INTO t1_a0016 (target) VALUES ('a');
INSERT INTO t1_a0016 (target) VALUES ('x');
INSERT INTO t1_a0016 (target) VALUES ('');
INSERT INTO t1_a0016 (target) VALUES ('a');
INSERT INTO t1_a0016 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0016 MODIFY target CHAR(2) CHARACTER SET latin1 INVISIBLE, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0016 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 INVISIBLE,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0017, t2_a0017;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0017 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0017 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0017 (target) VALUES ('test');
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0017 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0018, t2_a0018;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0018 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0018 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0018 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0019, t2_a0019;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0019 (target) VALUES ('');
INSERT INTO t1_a0019 (target) VALUES ('a');
INSERT INTO t1_a0019 (target) VALUES ('x');
INSERT INTO t1_a0019 (target) VALUES ('');
INSERT INTO t1_a0019 (target) VALUES ('a');
INSERT INTO t1_a0019 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0019 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0019 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0020, t2_a0020;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0020 (target) VALUES ('');
INSERT INTO t1_a0020 (target) VALUES ('a');
INSERT INTO t1_a0020 (target) VALUES ('x');
INSERT INTO t1_a0020 (target) VALUES ('');
INSERT INTO t1_a0020 (target) VALUES ('a');
INSERT INTO t1_a0020 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0020 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0020 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0021, t2_a0021;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0021 (target) VALUES ('');
INSERT INTO t1_a0021 (target) VALUES ('a');
INSERT INTO t1_a0021 (target) VALUES ('x');
INSERT INTO t1_a0021 (target) VALUES ('');
INSERT INTO t1_a0021 (target) VALUES ('a');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0021 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0021 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0022, t2_a0022;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0022 (target) VALUES ('');
INSERT INTO t1_a0022 (target) VALUES ('a');
INSERT INTO t1_a0022 (target) VALUES ('x');
INSERT INTO t1_a0022 (target) VALUES ('');
INSERT INTO t1_a0022 (target) VALUES ('a');
INSERT INTO t1_a0022 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0022 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0022 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0023, t2_a0023;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0023 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0023 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0023 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0024, t2_a0024;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
INSERT INTO t1_a0024 (target) VALUES ('');
INSERT INTO t1_a0024 (target) VALUES ('a');
INSERT INTO t1_a0024 (target) VALUES ('x');
INSERT INTO t1_a0024 (target) VALUES ('');
INSERT INTO t1_a0024 (target) VALUES ('a');
INSERT INTO t1_a0024 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0024 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0024 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0025, t2_a0025;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0025 MODIFY target CHAR(2) CHARACTER SET latin1 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0025 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0025 (target) VALUES ('test');
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0025 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 NOT NULL,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0026, t2_a0026;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0026 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0026 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0026 (target) VALUES ('test');
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0026 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0027, t2_a0027;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(1) CHARACTER SET latin1 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=latin1;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0027 MODIFY target CHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0027 (target) VALUES ('qqq');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0027 (target) VALUES ('test');
-- Oracle table: CHAR(2)
CREATE TABLE t2_a0027 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(2) CHARACTER SET latin1 NOT NULL DEFAULT '',
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0028, t2_a0028;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0028 (
  target CHAR(1) CHARACTER SET latin1,
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
ALTER TABLE t1_a0028 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
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
-- Oracle table: CHAR(1)
CREATE TABLE t2_a0028 (
  target CHAR(1) CHARACTER SET latin1,
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
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0029, t2_tc_aa0029;
CREATE TABLE t1_tc_aa0029 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(1) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0029 (target) VALUES ('');
INSERT INTO t1_tc_aa0029 (target) VALUES ('a');
INSERT INTO t1_tc_aa0029 (target) VALUES ('x');
INSERT INTO t1_tc_aa0029 (target) VALUES ('');
INSERT INTO t1_tc_aa0029 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0029 MODIFY target CHAR(2) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0029 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0029 (target) VALUES ('z');
INSERT INTO t1_tc_aa0029 (target) VALUES ('ww');
SELECT 'TC-AA0029' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0029' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0030
-- Column attribute preservation: CHARSET
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0030, t2_tc_aa0030;
CREATE TABLE t1_tc_aa0030 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(1) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0030 (target) VALUES ('');
INSERT INTO t1_tc_aa0030 (target) VALUES ('a');
INSERT INTO t1_tc_aa0030 (target) VALUES ('x');
INSERT INTO t1_tc_aa0030 (target) VALUES ('');
INSERT INTO t1_tc_aa0030 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0030 MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=instant;
INSERT INTO t1_tc_aa0030 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0030 (target) VALUES ('z');
INSERT INTO t1_tc_aa0030 (target) VALUES ('ww');
SELECT 'TC-AA0030' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0030' AND column_name='target' AND character_set_name='latin1';

-- Test Case: TC-AA0031
-- Column attribute preservation: COLLATE
-- Type: CHAR(1) -> CHAR(2), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0031, t2_tc_aa0031;
CREATE TABLE t1_tc_aa0031 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(1) CHARACTER SET latin1 COLLATE latin1_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0031 (target) VALUES ('');
INSERT INTO t1_tc_aa0031 (target) VALUES ('a');
INSERT INTO t1_tc_aa0031 (target) VALUES ('x');
INSERT INTO t1_tc_aa0031 (target) VALUES ('');
INSERT INTO t1_tc_aa0031 (target) VALUES ('a');
ALTER TABLE t1_tc_aa0031 MODIFY target CHAR(2) CHARACTER SET latin1 COLLATE latin1_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0031 (target) VALUES ('zz');
INSERT INTO t1_tc_aa0031 (target) VALUES ('z');
INSERT INTO t1_tc_aa0031 (target) VALUES ('ww');
SELECT 'TC-AA0031' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0031' AND column_name='target' AND collation_name='latin1_bin';

-- Test Case: TC-A0032
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0032, t2_a0032;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0032 (target) VALUES ('');
INSERT INTO t1_a0032 (target) VALUES ('a');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES ('Hello');
INSERT INTO t1_a0032 (target) VALUES ('你好');
INSERT INTO t1_a0032 (target) VALUES ('🎉');
INSERT INTO t1_a0032 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0032 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0032 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0032 (target) VALUES ('');
INSERT INTO t1_a0032 (target) VALUES ('a');
INSERT INTO t1_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0032 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0032 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0032 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0032 (target) VALUES ('');
INSERT INTO t2_a0032 (target) VALUES ('a');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0032 (target) VALUES ('Hello');
INSERT INTO t2_a0032 (target) VALUES ('你好');
INSERT INTO t2_a0032 (target) VALUES ('🎉');
INSERT INTO t2_a0032 (target) VALUES (NULL);
INSERT INTO t2_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0032 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0032 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0032 (target) VALUES ('');
INSERT INTO t2_a0032 (target) VALUES ('a');
INSERT INTO t2_a0032 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0033, t2_a0033;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0033 (target) VALUES ('');
INSERT INTO t1_a0033 (target) VALUES ('a');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES ('Hello');
INSERT INTO t1_a0033 (target) VALUES ('你好');
INSERT INTO t1_a0033 (target) VALUES ('🎉');
INSERT INTO t1_a0033 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0033 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0033 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0033 (target) VALUES ('');
INSERT INTO t1_a0033 (target) VALUES ('a');
INSERT INTO t1_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0033 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0033 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0033 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0033 (target) VALUES ('');
INSERT INTO t2_a0033 (target) VALUES ('a');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0033 (target) VALUES ('Hello');
INSERT INTO t2_a0033 (target) VALUES ('你好');
INSERT INTO t2_a0033 (target) VALUES ('🎉');
INSERT INTO t2_a0033 (target) VALUES (NULL);
INSERT INTO t2_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0033 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0033 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0033 (target) VALUES ('');
INSERT INTO t2_a0033 (target) VALUES ('a');
INSERT INTO t2_a0033 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0034, t2_a0034;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0034 (target) VALUES ('');
INSERT INTO t1_a0034 (target) VALUES ('a');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES ('Hello');
INSERT INTO t1_a0034 (target) VALUES ('你好');
INSERT INTO t1_a0034 (target) VALUES ('🎉');
INSERT INTO t1_a0034 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0034 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0034 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0034 (target) VALUES ('');
INSERT INTO t1_a0034 (target) VALUES ('a');
INSERT INTO t1_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0034 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0034 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0034 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0034 (target) VALUES ('');
INSERT INTO t2_a0034 (target) VALUES ('a');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0034 (target) VALUES ('Hello');
INSERT INTO t2_a0034 (target) VALUES ('你好');
INSERT INTO t2_a0034 (target) VALUES ('🎉');
INSERT INTO t2_a0034 (target) VALUES (NULL);
INSERT INTO t2_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0034 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0034 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0034 (target) VALUES ('');
INSERT INTO t2_a0034 (target) VALUES ('a');
INSERT INTO t2_a0034 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0035, t2_a0035;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0035 (target) VALUES ('');
INSERT INTO t1_a0035 (target) VALUES ('a');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0035 (target) VALUES ('Hello');
INSERT INTO t1_a0035 (target) VALUES ('你好');
INSERT INTO t1_a0035 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0035 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0035 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0035 (target) VALUES ('');
INSERT INTO t1_a0035 (target) VALUES ('a');
INSERT INTO t1_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0035 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(63)
CREATE TABLE t2_a0035 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0035 (target) VALUES ('');
INSERT INTO t2_a0035 (target) VALUES ('a');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0035 (target) VALUES ('Hello');
INSERT INTO t2_a0035 (target) VALUES ('你好');
INSERT INTO t2_a0035 (target) VALUES ('🎉');
INSERT INTO t2_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0035 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0035 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0035 (target) VALUES ('');
INSERT INTO t2_a0035 (target) VALUES ('a');
INSERT INTO t2_a0035 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0036, t2_a0036;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0036 (target) VALUES ('');
INSERT INTO t1_a0036 (target) VALUES ('a');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES ('Hello');
INSERT INTO t1_a0036 (target) VALUES ('你好');
INSERT INTO t1_a0036 (target) VALUES ('🎉');
INSERT INTO t1_a0036 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0036 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0036 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0036 (target) VALUES ('');
INSERT INTO t1_a0036 (target) VALUES ('a');
INSERT INTO t1_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0036 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0036 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0036 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0036 (target) VALUES ('');
INSERT INTO t2_a0036 (target) VALUES ('a');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0036 (target) VALUES ('Hello');
INSERT INTO t2_a0036 (target) VALUES ('你好');
INSERT INTO t2_a0036 (target) VALUES ('🎉');
INSERT INTO t2_a0036 (target) VALUES (NULL);
INSERT INTO t2_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0036 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0036 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0036 (target) VALUES ('');
INSERT INTO t2_a0036 (target) VALUES ('a');
INSERT INTO t2_a0036 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0037, t2_a0037;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0037 (target) VALUES ('');
INSERT INTO t1_a0037 (target) VALUES ('a');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES ('Hello');
INSERT INTO t1_a0037 (target) VALUES ('你好');
INSERT INTO t1_a0037 (target) VALUES ('🎉');
INSERT INTO t1_a0037 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0037 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0037 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0037 (target) VALUES ('');
INSERT INTO t1_a0037 (target) VALUES ('a');
INSERT INTO t1_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0037 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0037 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0037 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0037 (target) VALUES ('');
INSERT INTO t2_a0037 (target) VALUES ('a');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0037 (target) VALUES ('Hello');
INSERT INTO t2_a0037 (target) VALUES ('你好');
INSERT INTO t2_a0037 (target) VALUES ('🎉');
INSERT INTO t2_a0037 (target) VALUES (NULL);
INSERT INTO t2_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0037 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0037 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0037 (target) VALUES ('');
INSERT INTO t2_a0037 (target) VALUES ('a');
INSERT INTO t2_a0037 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0038, t2_a0038;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0038 (target) VALUES ('');
INSERT INTO t1_a0038 (target) VALUES ('a');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES ('Hello');
INSERT INTO t1_a0038 (target) VALUES ('你好');
INSERT INTO t1_a0038 (target) VALUES ('🎉');
INSERT INTO t1_a0038 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0038 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0038 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0038 (target) VALUES ('');
INSERT INTO t1_a0038 (target) VALUES ('a');
INSERT INTO t1_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0038 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0038 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0038 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0038 (target) VALUES ('');
INSERT INTO t2_a0038 (target) VALUES ('a');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0038 (target) VALUES ('Hello');
INSERT INTO t2_a0038 (target) VALUES ('你好');
INSERT INTO t2_a0038 (target) VALUES ('🎉');
INSERT INTO t2_a0038 (target) VALUES (NULL);
INSERT INTO t2_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0038 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0038 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0038 (target) VALUES ('');
INSERT INTO t2_a0038 (target) VALUES ('a');
INSERT INTO t2_a0038 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0039, t2_a0039;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0039 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0039 (target) VALUES ('');
INSERT INTO t1_a0039 (target) VALUES ('a');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES ('Hello');
INSERT INTO t1_a0039 (target) VALUES ('你好');
INSERT INTO t1_a0039 (target) VALUES ('🎉');
INSERT INTO t1_a0039 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0039 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0039 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0039 (target) VALUES ('');
INSERT INTO t1_a0039 (target) VALUES ('a');
INSERT INTO t1_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0039 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0039 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0039 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0039 (target) VALUES ('');
INSERT INTO t2_a0039 (target) VALUES ('a');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0039 (target) VALUES ('Hello');
INSERT INTO t2_a0039 (target) VALUES ('你好');
INSERT INTO t2_a0039 (target) VALUES ('🎉');
INSERT INTO t2_a0039 (target) VALUES (NULL);
INSERT INTO t2_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0039 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0039 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0039 (target) VALUES ('');
INSERT INTO t2_a0039 (target) VALUES ('a');
INSERT INTO t2_a0039 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0040, t2_a0040;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0040 (target) VALUES ('');
INSERT INTO t1_a0040 (target) VALUES ('a');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES ('Hello');
INSERT INTO t1_a0040 (target) VALUES ('你好');
INSERT INTO t1_a0040 (target) VALUES ('🎉');
INSERT INTO t1_a0040 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0040 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0040 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0040 (target) VALUES ('');
INSERT INTO t1_a0040 (target) VALUES ('a');
INSERT INTO t1_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0040 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0040 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0040 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0040 (target) VALUES ('');
INSERT INTO t2_a0040 (target) VALUES ('a');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0040 (target) VALUES ('Hello');
INSERT INTO t2_a0040 (target) VALUES ('你好');
INSERT INTO t2_a0040 (target) VALUES ('🎉');
INSERT INTO t2_a0040 (target) VALUES (NULL);
INSERT INTO t2_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0040 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0040 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0040 (target) VALUES ('');
INSERT INTO t2_a0040 (target) VALUES ('a');
INSERT INTO t2_a0040 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0041, t2_a0041;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0041 (
  target CHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0041 (target) VALUES ('');
INSERT INTO t1_a0041 (target) VALUES ('a');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES ('Hello');
INSERT INTO t1_a0041 (target) VALUES ('你好');
INSERT INTO t1_a0041 (target) VALUES ('🎉');
INSERT INTO t1_a0041 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0041 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0041 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0041 (target) VALUES ('');
INSERT INTO t1_a0041 (target) VALUES ('a');
INSERT INTO t1_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0041 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0041 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0041 (
  target CHAR(64) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0041 (target) VALUES ('');
INSERT INTO t2_a0041 (target) VALUES ('a');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0041 (target) VALUES ('Hello');
INSERT INTO t2_a0041 (target) VALUES ('你好');
INSERT INTO t2_a0041 (target) VALUES ('🎉');
INSERT INTO t2_a0041 (target) VALUES (NULL);
INSERT INTO t2_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0041 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0041 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0041 (target) VALUES ('');
INSERT INTO t2_a0041 (target) VALUES ('a');
INSERT INTO t2_a0041 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0042, t2_a0042;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(63) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0042 (target) VALUES ('');
INSERT INTO t1_a0042 (target) VALUES ('a');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES ('Hello');
INSERT INTO t1_a0042 (target) VALUES ('你好');
INSERT INTO t1_a0042 (target) VALUES ('🎉');
INSERT INTO t1_a0042 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0042 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0042 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0042 (target) VALUES ('');
INSERT INTO t1_a0042 (target) VALUES ('a');
INSERT INTO t1_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0042 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0042 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0042 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(64) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0042 (target) VALUES ('');
INSERT INTO t2_a0042 (target) VALUES ('a');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0042 (target) VALUES ('Hello');
INSERT INTO t2_a0042 (target) VALUES ('你好');
INSERT INTO t2_a0042 (target) VALUES ('🎉');
INSERT INTO t2_a0042 (target) VALUES (NULL);
INSERT INTO t2_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0042 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0042 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0042 (target) VALUES ('');
INSERT INTO t2_a0042 (target) VALUES ('a');
INSERT INTO t2_a0042 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0043, t2_a0043;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0043 (target) VALUES ('');
INSERT INTO t1_a0043 (target) VALUES ('a');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0043 (target) VALUES ('Hello');
INSERT INTO t1_a0043 (target) VALUES ('你好');
INSERT INTO t1_a0043 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0043 MODIFY target CHAR(64) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0043 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0043 (target) VALUES ('');
INSERT INTO t1_a0043 (target) VALUES ('a');
INSERT INTO t1_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0043 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0043 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0043 (target) VALUES ('');
INSERT INTO t2_a0043 (target) VALUES ('a');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0043 (target) VALUES ('Hello');
INSERT INTO t2_a0043 (target) VALUES ('你好');
INSERT INTO t2_a0043 (target) VALUES ('🎉');
INSERT INTO t2_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0043 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0043 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0043 (target) VALUES ('');
INSERT INTO t2_a0043 (target) VALUES ('a');
INSERT INTO t2_a0043 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0044, t2_a0044;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0044 (target) VALUES ('');
INSERT INTO t1_a0044 (target) VALUES ('a');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES ('Hello');
INSERT INTO t1_a0044 (target) VALUES ('你好');
INSERT INTO t1_a0044 (target) VALUES ('🎉');
INSERT INTO t1_a0044 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0044 MODIFY target CHAR(64) CHARACTER SET utf8mb4 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0044 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0044 (target) VALUES ('');
INSERT INTO t1_a0044 (target) VALUES ('a');
INSERT INTO t1_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0044 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0044 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0044 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0044 (target) VALUES ('');
INSERT INTO t2_a0044 (target) VALUES ('a');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0044 (target) VALUES ('Hello');
INSERT INTO t2_a0044 (target) VALUES ('你好');
INSERT INTO t2_a0044 (target) VALUES ('🎉');
INSERT INTO t2_a0044 (target) VALUES (NULL);
INSERT INTO t2_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0044 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0044 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0044 (target) VALUES ('');
INSERT INTO t2_a0044 (target) VALUES ('a');
INSERT INTO t2_a0044 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0045, t2_a0045;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0045 (target) VALUES ('');
INSERT INTO t1_a0045 (target) VALUES ('a');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES ('Hello');
INSERT INTO t1_a0045 (target) VALUES ('你好');
INSERT INTO t1_a0045 (target) VALUES ('🎉');
INSERT INTO t1_a0045 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0045 MODIFY target CHAR(64) CHARACTER SET utf8mb4 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0045 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0045 (target) VALUES ('');
INSERT INTO t1_a0045 (target) VALUES ('a');
INSERT INTO t1_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0045 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0045 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0045 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0045 (target) VALUES ('');
INSERT INTO t2_a0045 (target) VALUES ('a');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0045 (target) VALUES ('Hello');
INSERT INTO t2_a0045 (target) VALUES ('你好');
INSERT INTO t2_a0045 (target) VALUES ('🎉');
INSERT INTO t2_a0045 (target) VALUES (NULL);
INSERT INTO t2_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0045 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0045 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0045 (target) VALUES ('');
INSERT INTO t2_a0045 (target) VALUES ('a');
INSERT INTO t2_a0045 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0046, t2_a0046;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0046 (target) VALUES ('');
INSERT INTO t1_a0046 (target) VALUES ('a');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0046 (target) VALUES ('Hello');
INSERT INTO t1_a0046 (target) VALUES ('你好');
INSERT INTO t1_a0046 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0046 MODIFY target CHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0046 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0046 (target) VALUES ('');
INSERT INTO t1_a0046 (target) VALUES ('a');
INSERT INTO t1_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0046 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0046 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0046 (target) VALUES ('');
INSERT INTO t2_a0046 (target) VALUES ('a');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0046 (target) VALUES ('Hello');
INSERT INTO t2_a0046 (target) VALUES ('你好');
INSERT INTO t2_a0046 (target) VALUES ('🎉');
INSERT INTO t2_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0046 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0046 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0046 (target) VALUES ('');
INSERT INTO t2_a0046 (target) VALUES ('a');
INSERT INTO t2_a0046 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0047, t2_a0047;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0047 (target) VALUES ('');
INSERT INTO t1_a0047 (target) VALUES ('a');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES ('Hello');
INSERT INTO t1_a0047 (target) VALUES ('你好');
INSERT INTO t1_a0047 (target) VALUES ('🎉');
INSERT INTO t1_a0047 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0047 MODIFY target CHAR(64) CHARACTER SET utf8mb4 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0047 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0047 (target) VALUES ('');
INSERT INTO t1_a0047 (target) VALUES ('a');
INSERT INTO t1_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0047 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0047 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0047 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0047 (target) VALUES ('');
INSERT INTO t2_a0047 (target) VALUES ('a');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0047 (target) VALUES ('Hello');
INSERT INTO t2_a0047 (target) VALUES ('你好');
INSERT INTO t2_a0047 (target) VALUES ('🎉');
INSERT INTO t2_a0047 (target) VALUES (NULL);
INSERT INTO t2_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0047 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0047 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0047 (target) VALUES ('');
INSERT INTO t2_a0047 (target) VALUES ('a');
INSERT INTO t2_a0047 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0048, t2_a0048;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0048 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0048 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0048 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0049, t2_a0049;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0049 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0049 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0049 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0049 (target) VALUES ('');
INSERT INTO t1_a0049 (target) VALUES ('a');
INSERT INTO t1_a0049 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0049 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0049 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0049 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0049 (target) VALUES ('');
INSERT INTO t2_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0049 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0049 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0049 (target) VALUES ('');
INSERT INTO t2_a0049 (target) VALUES ('a');
INSERT INTO t2_a0049 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0050, t2_a0050;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0050 (target) VALUES ('');
INSERT INTO t1_a0050 (target) VALUES ('a');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES ('Hello');
INSERT INTO t1_a0050 (target) VALUES ('你好');
INSERT INTO t1_a0050 (target) VALUES ('🎉');
INSERT INTO t1_a0050 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0050 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0050 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0050 (target) VALUES ('');
INSERT INTO t1_a0050 (target) VALUES ('a');
INSERT INTO t1_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0050 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0050 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0050 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0050 (target) VALUES ('');
INSERT INTO t2_a0050 (target) VALUES ('a');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0050 (target) VALUES ('Hello');
INSERT INTO t2_a0050 (target) VALUES ('你好');
INSERT INTO t2_a0050 (target) VALUES ('🎉');
INSERT INTO t2_a0050 (target) VALUES (NULL);
INSERT INTO t2_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0050 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0050 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0050 (target) VALUES ('');
INSERT INTO t2_a0050 (target) VALUES ('a');
INSERT INTO t2_a0050 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0051, t2_a0051;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0051 (target) VALUES ('');
INSERT INTO t1_a0051 (target) VALUES ('a');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES ('Hello');
INSERT INTO t1_a0051 (target) VALUES ('你好');
INSERT INTO t1_a0051 (target) VALUES ('🎉');
INSERT INTO t1_a0051 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0051 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0051 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0051 (target) VALUES ('');
INSERT INTO t1_a0051 (target) VALUES ('a');
INSERT INTO t1_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0051 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0051 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0051 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0051 (target) VALUES ('');
INSERT INTO t2_a0051 (target) VALUES ('a');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0051 (target) VALUES ('Hello');
INSERT INTO t2_a0051 (target) VALUES ('你好');
INSERT INTO t2_a0051 (target) VALUES ('🎉');
INSERT INTO t2_a0051 (target) VALUES (NULL);
INSERT INTO t2_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0051 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0051 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0051 (target) VALUES ('');
INSERT INTO t2_a0051 (target) VALUES ('a');
INSERT INTO t2_a0051 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0052, t2_a0052;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0052 (target) VALUES ('');
INSERT INTO t1_a0052 (target) VALUES ('a');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0052 (target) VALUES ('Hello');
INSERT INTO t1_a0052 (target) VALUES ('你好');
INSERT INTO t1_a0052 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0052 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0052 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0052 (target) VALUES ('');
INSERT INTO t1_a0052 (target) VALUES ('a');
INSERT INTO t1_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0052 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0052 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0052 (target) VALUES ('');
INSERT INTO t2_a0052 (target) VALUES ('a');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0052 (target) VALUES ('Hello');
INSERT INTO t2_a0052 (target) VALUES ('你好');
INSERT INTO t2_a0052 (target) VALUES ('🎉');
INSERT INTO t2_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0052 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0052 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0052 (target) VALUES ('');
INSERT INTO t2_a0052 (target) VALUES ('a');
INSERT INTO t2_a0052 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0053, t2_a0053;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0053 (target) VALUES ('');
INSERT INTO t1_a0053 (target) VALUES ('a');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES ('Hello');
INSERT INTO t1_a0053 (target) VALUES ('你好');
INSERT INTO t1_a0053 (target) VALUES ('🎉');
INSERT INTO t1_a0053 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0053 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0053 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0053 (target) VALUES ('');
INSERT INTO t1_a0053 (target) VALUES ('a');
INSERT INTO t1_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0053 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0053 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0053 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0053 (target) VALUES ('');
INSERT INTO t2_a0053 (target) VALUES ('a');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0053 (target) VALUES ('Hello');
INSERT INTO t2_a0053 (target) VALUES ('你好');
INSERT INTO t2_a0053 (target) VALUES ('🎉');
INSERT INTO t2_a0053 (target) VALUES (NULL);
INSERT INTO t2_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0053 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0053 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0053 (target) VALUES ('');
INSERT INTO t2_a0053 (target) VALUES ('a');
INSERT INTO t2_a0053 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0054, t2_a0054;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0054 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0054 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0054 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0054 (target) VALUES ('');
INSERT INTO t1_a0054 (target) VALUES ('a');
INSERT INTO t1_a0054 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0054 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0054 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0054 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0054 (target) VALUES (NULL);
INSERT INTO t2_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0054 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0054 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0054 (target) VALUES ('');
INSERT INTO t2_a0054 (target) VALUES ('a');
INSERT INTO t2_a0054 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0055, t2_a0055;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0055 (target) VALUES ('');
INSERT INTO t1_a0055 (target) VALUES ('a');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES ('Hello');
INSERT INTO t1_a0055 (target) VALUES ('你好');
INSERT INTO t1_a0055 (target) VALUES ('🎉');
INSERT INTO t1_a0055 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0055 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0055 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0055 (target) VALUES ('');
INSERT INTO t1_a0055 (target) VALUES ('a');
INSERT INTO t1_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0055 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0055 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0055 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0055 (target) VALUES ('');
INSERT INTO t2_a0055 (target) VALUES ('a');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0055 (target) VALUES ('Hello');
INSERT INTO t2_a0055 (target) VALUES ('你好');
INSERT INTO t2_a0055 (target) VALUES ('🎉');
INSERT INTO t2_a0055 (target) VALUES (NULL);
INSERT INTO t2_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0055 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0055 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0055 (target) VALUES ('');
INSERT INTO t2_a0055 (target) VALUES ('a');
INSERT INTO t2_a0055 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0056, t2_a0056;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0056 MODIFY target CHAR(64) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0056 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0056 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0057, t2_a0057;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0057 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0057 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0057 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0057 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0058, t2_a0058;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0058 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(63) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0058 MODIFY target CHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0058 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(64)
CREATE TABLE t2_a0058 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(64) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0059, t2_a0059;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0059 (
  target CHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0059 (target) VALUES ('');
INSERT INTO t1_a0059 (target) VALUES ('a');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0059 (target) VALUES ('Hello');
INSERT INTO t1_a0059 (target) VALUES ('你好');
INSERT INTO t1_a0059 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0059 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0059 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0059 (target) VALUES ('');
INSERT INTO t1_a0059 (target) VALUES ('a');
INSERT INTO t1_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0059 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(63)
CREATE TABLE t2_a0059 (
  target CHAR(63) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0059 (target) VALUES ('');
INSERT INTO t2_a0059 (target) VALUES ('a');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0059 (target) VALUES ('Hello');
INSERT INTO t2_a0059 (target) VALUES ('你好');
INSERT INTO t2_a0059 (target) VALUES ('🎉');
INSERT INTO t2_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0059 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0059 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0059 (target) VALUES ('');
INSERT INTO t2_a0059 (target) VALUES ('a');
INSERT INTO t2_a0059 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0060, t2_tc_aa0060;
CREATE TABLE t1_tc_aa0060 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(63) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0060 (target) VALUES ('');
INSERT INTO t1_tc_aa0060 (target) VALUES ('a');
INSERT INTO t1_tc_aa0060 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0060 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0060 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0060 MODIFY target CHAR(64) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0060 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0060 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0060 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0060' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0060' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0061
-- Column attribute preservation: CHARSET
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0061, t2_tc_aa0061;
CREATE TABLE t1_tc_aa0061 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(63) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0061 (target) VALUES ('');
INSERT INTO t1_tc_aa0061 (target) VALUES ('a');
INSERT INTO t1_tc_aa0061 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0061 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0061 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0061 MODIFY target CHAR(64) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_aa0061 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0061 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0061 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0061' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0061' AND column_name='target' AND character_set_name='utf8mb4';

-- Test Case: TC-AA0062
-- Column attribute preservation: COLLATE
-- Type: CHAR(63) -> CHAR(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0062, t2_tc_aa0062;
CREATE TABLE t1_tc_aa0062 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(63) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0062 (target) VALUES ('');
INSERT INTO t1_tc_aa0062 (target) VALUES ('a');
INSERT INTO t1_tc_aa0062 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0062 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0062 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0062 MODIFY target CHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0062 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0062 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0062 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0062' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0062' AND column_name='target' AND collation_name='utf8mb4_bin';

-- Test Case: TC-A0063
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0063, t2_a0063;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0063 (target) VALUES ('');
INSERT INTO t1_a0063 (target) VALUES ('a');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES ('Hello');
INSERT INTO t1_a0063 (target) VALUES ('你好');
INSERT INTO t1_a0063 (target) VALUES ('🎉');
INSERT INTO t1_a0063 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0063 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0063 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0063 (target) VALUES ('');
INSERT INTO t1_a0063 (target) VALUES ('a');
INSERT INTO t1_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0063 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0063 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0063 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0063 (target) VALUES ('');
INSERT INTO t2_a0063 (target) VALUES ('a');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0063 (target) VALUES ('Hello');
INSERT INTO t2_a0063 (target) VALUES ('你好');
INSERT INTO t2_a0063 (target) VALUES ('🎉');
INSERT INTO t2_a0063 (target) VALUES (NULL);
INSERT INTO t2_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0063 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0063 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0063 (target) VALUES ('');
INSERT INTO t2_a0063 (target) VALUES ('a');
INSERT INTO t2_a0063 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0064, t2_a0064;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0064 (target) VALUES ('');
INSERT INTO t1_a0064 (target) VALUES ('a');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES ('Hello');
INSERT INTO t1_a0064 (target) VALUES ('你好');
INSERT INTO t1_a0064 (target) VALUES ('🎉');
INSERT INTO t1_a0064 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0064 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0064 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0064 (target) VALUES ('');
INSERT INTO t1_a0064 (target) VALUES ('a');
INSERT INTO t1_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0064 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0064 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0064 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0064 (target) VALUES ('');
INSERT INTO t2_a0064 (target) VALUES ('a');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0064 (target) VALUES ('Hello');
INSERT INTO t2_a0064 (target) VALUES ('你好');
INSERT INTO t2_a0064 (target) VALUES ('🎉');
INSERT INTO t2_a0064 (target) VALUES (NULL);
INSERT INTO t2_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0064 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0064 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0064 (target) VALUES ('');
INSERT INTO t2_a0064 (target) VALUES ('a');
INSERT INTO t2_a0064 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0065, t2_a0065;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0065 (target) VALUES ('');
INSERT INTO t1_a0065 (target) VALUES ('a');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES ('Hello');
INSERT INTO t1_a0065 (target) VALUES ('你好');
INSERT INTO t1_a0065 (target) VALUES ('🎉');
INSERT INTO t1_a0065 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0065 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0065 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0065 (target) VALUES ('');
INSERT INTO t1_a0065 (target) VALUES ('a');
INSERT INTO t1_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0065 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0065 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0065 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0065 (target) VALUES ('');
INSERT INTO t2_a0065 (target) VALUES ('a');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0065 (target) VALUES ('Hello');
INSERT INTO t2_a0065 (target) VALUES ('你好');
INSERT INTO t2_a0065 (target) VALUES ('🎉');
INSERT INTO t2_a0065 (target) VALUES (NULL);
INSERT INTO t2_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0065 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0065 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0065 (target) VALUES ('');
INSERT INTO t2_a0065 (target) VALUES ('a');
INSERT INTO t2_a0065 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0066, t2_a0066;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0066 (target) VALUES ('');
INSERT INTO t1_a0066 (target) VALUES ('a');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0066 (target) VALUES ('Hello');
INSERT INTO t1_a0066 (target) VALUES ('你好');
INSERT INTO t1_a0066 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0066 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0066 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0066 (target) VALUES ('');
INSERT INTO t1_a0066 (target) VALUES ('a');
INSERT INTO t1_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0066 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(254)
CREATE TABLE t2_a0066 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0066 (target) VALUES ('');
INSERT INTO t2_a0066 (target) VALUES ('a');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0066 (target) VALUES ('Hello');
INSERT INTO t2_a0066 (target) VALUES ('你好');
INSERT INTO t2_a0066 (target) VALUES ('🎉');
INSERT INTO t2_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0066 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0066 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0066 (target) VALUES ('');
INSERT INTO t2_a0066 (target) VALUES ('a');
INSERT INTO t2_a0066 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0067, t2_a0067;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0067 (target) VALUES ('');
INSERT INTO t1_a0067 (target) VALUES ('a');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES ('Hello');
INSERT INTO t1_a0067 (target) VALUES ('你好');
INSERT INTO t1_a0067 (target) VALUES ('🎉');
INSERT INTO t1_a0067 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0067 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0067 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0067 (target) VALUES ('');
INSERT INTO t1_a0067 (target) VALUES ('a');
INSERT INTO t1_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0067 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0067 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0067 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0067 (target) VALUES ('');
INSERT INTO t2_a0067 (target) VALUES ('a');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0067 (target) VALUES ('Hello');
INSERT INTO t2_a0067 (target) VALUES ('你好');
INSERT INTO t2_a0067 (target) VALUES ('🎉');
INSERT INTO t2_a0067 (target) VALUES (NULL);
INSERT INTO t2_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0067 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0067 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0067 (target) VALUES ('');
INSERT INTO t2_a0067 (target) VALUES ('a');
INSERT INTO t2_a0067 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0068, t2_a0068;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0068 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0068 (target) VALUES ('');
INSERT INTO t1_a0068 (target) VALUES ('a');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES ('Hello');
INSERT INTO t1_a0068 (target) VALUES ('你好');
INSERT INTO t1_a0068 (target) VALUES ('🎉');
INSERT INTO t1_a0068 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0068 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0068 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0068 (target) VALUES ('');
INSERT INTO t1_a0068 (target) VALUES ('a');
INSERT INTO t1_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0068 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0068 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0068 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0068 (target) VALUES ('');
INSERT INTO t2_a0068 (target) VALUES ('a');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0068 (target) VALUES ('Hello');
INSERT INTO t2_a0068 (target) VALUES ('你好');
INSERT INTO t2_a0068 (target) VALUES ('🎉');
INSERT INTO t2_a0068 (target) VALUES (NULL);
INSERT INTO t2_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0068 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0068 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0068 (target) VALUES ('');
INSERT INTO t2_a0068 (target) VALUES ('a');
INSERT INTO t2_a0068 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0069, t2_a0069;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0069 (target) VALUES ('');
INSERT INTO t1_a0069 (target) VALUES ('a');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES ('Hello');
INSERT INTO t1_a0069 (target) VALUES ('你好');
INSERT INTO t1_a0069 (target) VALUES ('🎉');
INSERT INTO t1_a0069 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0069 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0069 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0069 (target) VALUES ('');
INSERT INTO t1_a0069 (target) VALUES ('a');
INSERT INTO t1_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0069 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0069 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0069 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0069 (target) VALUES ('');
INSERT INTO t2_a0069 (target) VALUES ('a');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0069 (target) VALUES ('Hello');
INSERT INTO t2_a0069 (target) VALUES ('你好');
INSERT INTO t2_a0069 (target) VALUES ('🎉');
INSERT INTO t2_a0069 (target) VALUES (NULL);
INSERT INTO t2_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0069 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0069 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0069 (target) VALUES ('');
INSERT INTO t2_a0069 (target) VALUES ('a');
INSERT INTO t2_a0069 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0070, t2_a0070;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0070 (target) VALUES ('');
INSERT INTO t1_a0070 (target) VALUES ('a');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES ('Hello');
INSERT INTO t1_a0070 (target) VALUES ('你好');
INSERT INTO t1_a0070 (target) VALUES ('🎉');
INSERT INTO t1_a0070 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0070 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0070 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0070 (target) VALUES ('');
INSERT INTO t1_a0070 (target) VALUES ('a');
INSERT INTO t1_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0070 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0070 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0070 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0070 (target) VALUES ('');
INSERT INTO t2_a0070 (target) VALUES ('a');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0070 (target) VALUES ('Hello');
INSERT INTO t2_a0070 (target) VALUES ('你好');
INSERT INTO t2_a0070 (target) VALUES ('🎉');
INSERT INTO t2_a0070 (target) VALUES (NULL);
INSERT INTO t2_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0070 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0070 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0070 (target) VALUES ('');
INSERT INTO t2_a0070 (target) VALUES ('a');
INSERT INTO t2_a0070 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0071, t2_a0071;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0071 (target) VALUES ('');
INSERT INTO t1_a0071 (target) VALUES ('a');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES ('Hello');
INSERT INTO t1_a0071 (target) VALUES ('你好');
INSERT INTO t1_a0071 (target) VALUES ('🎉');
INSERT INTO t1_a0071 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0071 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0071 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0071 (target) VALUES ('');
INSERT INTO t1_a0071 (target) VALUES ('a');
INSERT INTO t1_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0071 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0071 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0071 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0071 (target) VALUES ('');
INSERT INTO t2_a0071 (target) VALUES ('a');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0071 (target) VALUES ('Hello');
INSERT INTO t2_a0071 (target) VALUES ('你好');
INSERT INTO t2_a0071 (target) VALUES ('🎉');
INSERT INTO t2_a0071 (target) VALUES (NULL);
INSERT INTO t2_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0071 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0071 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0071 (target) VALUES ('');
INSERT INTO t2_a0071 (target) VALUES ('a');
INSERT INTO t2_a0071 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0072, t2_a0072;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0072 (
  target CHAR(254) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0072 (target) VALUES ('');
INSERT INTO t1_a0072 (target) VALUES ('a');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES ('Hello');
INSERT INTO t1_a0072 (target) VALUES ('你好');
INSERT INTO t1_a0072 (target) VALUES ('🎉');
INSERT INTO t1_a0072 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0072 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0072 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0072 (target) VALUES ('');
INSERT INTO t1_a0072 (target) VALUES ('a');
INSERT INTO t1_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0072 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0072 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0072 (
  target CHAR(255) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0072 (target) VALUES ('');
INSERT INTO t2_a0072 (target) VALUES ('a');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0072 (target) VALUES ('Hello');
INSERT INTO t2_a0072 (target) VALUES ('你好');
INSERT INTO t2_a0072 (target) VALUES ('🎉');
INSERT INTO t2_a0072 (target) VALUES (NULL);
INSERT INTO t2_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0072 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0072 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0072 (target) VALUES ('');
INSERT INTO t2_a0072 (target) VALUES ('a');
INSERT INTO t2_a0072 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_a0073, t2_a0073;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(254) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0073 (target) VALUES ('');
INSERT INTO t1_a0073 (target) VALUES ('a');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES ('Hello');
INSERT INTO t1_a0073 (target) VALUES ('你好');
INSERT INTO t1_a0073 (target) VALUES ('🎉');
INSERT INTO t1_a0073 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0073 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0073 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0073 (target) VALUES ('');
INSERT INTO t1_a0073 (target) VALUES ('a');
INSERT INTO t1_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0073 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0073 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0073 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target CHAR(255) CHARACTER SET utf8mb4, PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0073 (target) VALUES ('');
INSERT INTO t2_a0073 (target) VALUES ('a');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0073 (target) VALUES ('Hello');
INSERT INTO t2_a0073 (target) VALUES ('你好');
INSERT INTO t2_a0073 (target) VALUES ('🎉');
INSERT INTO t2_a0073 (target) VALUES (NULL);
INSERT INTO t2_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0073 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0073 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0073 (target) VALUES ('');
INSERT INTO t2_a0073 (target) VALUES ('a');
INSERT INTO t2_a0073 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0074, t2_a0074;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0074 (target) VALUES ('');
INSERT INTO t1_a0074 (target) VALUES ('a');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0074 (target) VALUES ('Hello');
INSERT INTO t1_a0074 (target) VALUES ('你好');
INSERT INTO t1_a0074 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0074 MODIFY target CHAR(255) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0074 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0074 (target) VALUES ('');
INSERT INTO t1_a0074 (target) VALUES ('a');
INSERT INTO t1_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0074 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0074 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0074 (target) VALUES ('');
INSERT INTO t2_a0074 (target) VALUES ('a');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0074 (target) VALUES ('Hello');
INSERT INTO t2_a0074 (target) VALUES ('你好');
INSERT INTO t2_a0074 (target) VALUES ('🎉');
INSERT INTO t2_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0074 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0074 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0074 (target) VALUES ('');
INSERT INTO t2_a0074 (target) VALUES ('a');
INSERT INTO t2_a0074 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0075, t2_a0075;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0075 (target) VALUES ('');
INSERT INTO t1_a0075 (target) VALUES ('a');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES ('Hello');
INSERT INTO t1_a0075 (target) VALUES ('你好');
INSERT INTO t1_a0075 (target) VALUES ('🎉');
INSERT INTO t1_a0075 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0075 MODIFY target CHAR(255) CHARACTER SET utf8mb4 DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0075 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0075 (target) VALUES ('');
INSERT INTO t1_a0075 (target) VALUES ('a');
INSERT INTO t1_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0075 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0075 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0075 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0075 (target) VALUES ('');
INSERT INTO t2_a0075 (target) VALUES ('a');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0075 (target) VALUES ('Hello');
INSERT INTO t2_a0075 (target) VALUES ('你好');
INSERT INTO t2_a0075 (target) VALUES ('🎉');
INSERT INTO t2_a0075 (target) VALUES (NULL);
INSERT INTO t2_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0075 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0075 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0075 (target) VALUES ('');
INSERT INTO t2_a0075 (target) VALUES ('a');
INSERT INTO t2_a0075 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0076, t2_a0076;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0076 (target) VALUES ('');
INSERT INTO t1_a0076 (target) VALUES ('a');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES ('Hello');
INSERT INTO t1_a0076 (target) VALUES ('你好');
INSERT INTO t1_a0076 (target) VALUES ('🎉');
INSERT INTO t1_a0076 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0076 MODIFY target CHAR(255) CHARACTER SET utf8mb4 DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0076 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0076 (target) VALUES ('');
INSERT INTO t1_a0076 (target) VALUES ('a');
INSERT INTO t1_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0076 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0076 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0076 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0076 (target) VALUES ('');
INSERT INTO t2_a0076 (target) VALUES ('a');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0076 (target) VALUES ('Hello');
INSERT INTO t2_a0076 (target) VALUES ('你好');
INSERT INTO t2_a0076 (target) VALUES ('🎉');
INSERT INTO t2_a0076 (target) VALUES (NULL);
INSERT INTO t2_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0076 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0076 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0076 (target) VALUES ('');
INSERT INTO t2_a0076 (target) VALUES ('a');
INSERT INTO t2_a0076 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0077, t2_a0077;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0077 (target) VALUES ('');
INSERT INTO t1_a0077 (target) VALUES ('a');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0077 (target) VALUES ('Hello');
INSERT INTO t1_a0077 (target) VALUES ('你好');
INSERT INTO t1_a0077 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0077 MODIFY target CHAR(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0077 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0077 (target) VALUES ('');
INSERT INTO t1_a0077 (target) VALUES ('a');
INSERT INTO t1_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0077 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0077 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0077 (target) VALUES ('');
INSERT INTO t2_a0077 (target) VALUES ('a');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0077 (target) VALUES ('Hello');
INSERT INTO t2_a0077 (target) VALUES ('你好');
INSERT INTO t2_a0077 (target) VALUES ('🎉');
INSERT INTO t2_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0077 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0077 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0077 (target) VALUES ('');
INSERT INTO t2_a0077 (target) VALUES ('a');
INSERT INTO t2_a0077 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0078, t2_a0078;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0078 (target) VALUES ('');
INSERT INTO t1_a0078 (target) VALUES ('a');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES ('Hello');
INSERT INTO t1_a0078 (target) VALUES ('你好');
INSERT INTO t1_a0078 (target) VALUES ('🎉');
INSERT INTO t1_a0078 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0078 MODIFY target CHAR(255) CHARACTER SET utf8mb4 INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0078 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0078 (target) VALUES ('');
INSERT INTO t1_a0078 (target) VALUES ('a');
INSERT INTO t1_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0078 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0078 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0078 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0078 (target) VALUES ('');
INSERT INTO t2_a0078 (target) VALUES ('a');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0078 (target) VALUES ('Hello');
INSERT INTO t2_a0078 (target) VALUES ('你好');
INSERT INTO t2_a0078 (target) VALUES ('🎉');
INSERT INTO t2_a0078 (target) VALUES (NULL);
INSERT INTO t2_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0078 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0078 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0078 (target) VALUES ('');
INSERT INTO t2_a0078 (target) VALUES ('a');
INSERT INTO t2_a0078 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0079, t2_a0079;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0079 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0079 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0079 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0080, t2_a0080;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0080 (target) VALUES ('');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0080 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0080 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0080 (target) VALUES ('');
INSERT INTO t1_a0080 (target) VALUES ('a');
INSERT INTO t1_a0080 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0080 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0080 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0080 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0080 (target) VALUES ('');
INSERT INTO t2_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0080 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0080 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0080 (target) VALUES ('');
INSERT INTO t2_a0080 (target) VALUES ('a');
INSERT INTO t2_a0080 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0081, t2_a0081;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0081 (target) VALUES ('');
INSERT INTO t1_a0081 (target) VALUES ('a');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES ('Hello');
INSERT INTO t1_a0081 (target) VALUES ('你好');
INSERT INTO t1_a0081 (target) VALUES ('🎉');
INSERT INTO t1_a0081 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0081 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0081 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0081 (target) VALUES ('');
INSERT INTO t1_a0081 (target) VALUES ('a');
INSERT INTO t1_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0081 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0081 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0081 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0081 (target) VALUES ('');
INSERT INTO t2_a0081 (target) VALUES ('a');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0081 (target) VALUES ('Hello');
INSERT INTO t2_a0081 (target) VALUES ('你好');
INSERT INTO t2_a0081 (target) VALUES ('🎉');
INSERT INTO t2_a0081 (target) VALUES (NULL);
INSERT INTO t2_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0081 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0081 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0081 (target) VALUES ('');
INSERT INTO t2_a0081 (target) VALUES ('a');
INSERT INTO t2_a0081 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0082, t2_a0082;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0082 (target) VALUES ('');
INSERT INTO t1_a0082 (target) VALUES ('a');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES ('Hello');
INSERT INTO t1_a0082 (target) VALUES ('你好');
INSERT INTO t1_a0082 (target) VALUES ('🎉');
INSERT INTO t1_a0082 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0082 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0082 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0082 (target) VALUES ('');
INSERT INTO t1_a0082 (target) VALUES ('a');
INSERT INTO t1_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0082 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0082 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0082 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0082 (target) VALUES ('');
INSERT INTO t2_a0082 (target) VALUES ('a');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0082 (target) VALUES ('Hello');
INSERT INTO t2_a0082 (target) VALUES ('你好');
INSERT INTO t2_a0082 (target) VALUES ('🎉');
INSERT INTO t2_a0082 (target) VALUES (NULL);
INSERT INTO t2_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0082 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0082 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0082 (target) VALUES ('');
INSERT INTO t2_a0082 (target) VALUES ('a');
INSERT INTO t2_a0082 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0083, t2_a0083;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0083 (target) VALUES ('');
INSERT INTO t1_a0083 (target) VALUES ('a');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0083 (target) VALUES ('Hello');
INSERT INTO t1_a0083 (target) VALUES ('你好');
INSERT INTO t1_a0083 (target) VALUES ('🎉');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0083 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0083 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0083 (target) VALUES ('');
INSERT INTO t1_a0083 (target) VALUES ('a');
INSERT INTO t1_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0083 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0083 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0083 (target) VALUES ('');
INSERT INTO t2_a0083 (target) VALUES ('a');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0083 (target) VALUES ('Hello');
INSERT INTO t2_a0083 (target) VALUES ('你好');
INSERT INTO t2_a0083 (target) VALUES ('🎉');
INSERT INTO t2_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0083 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0083 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0083 (target) VALUES ('');
INSERT INTO t2_a0083 (target) VALUES ('a');
INSERT INTO t2_a0083 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0084, t2_a0084;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0084 (target) VALUES ('');
INSERT INTO t1_a0084 (target) VALUES ('a');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES ('Hello');
INSERT INTO t1_a0084 (target) VALUES ('你好');
INSERT INTO t1_a0084 (target) VALUES ('🎉');
INSERT INTO t1_a0084 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0084 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0084 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0084 (target) VALUES ('');
INSERT INTO t1_a0084 (target) VALUES ('a');
INSERT INTO t1_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0084 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0084 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0084 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0084 (target) VALUES ('');
INSERT INTO t2_a0084 (target) VALUES ('a');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0084 (target) VALUES ('Hello');
INSERT INTO t2_a0084 (target) VALUES ('你好');
INSERT INTO t2_a0084 (target) VALUES ('🎉');
INSERT INTO t2_a0084 (target) VALUES (NULL);
INSERT INTO t2_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0084 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0084 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0084 (target) VALUES ('');
INSERT INTO t2_a0084 (target) VALUES ('a');
INSERT INTO t2_a0084 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0085, t2_a0085;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0085 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0085 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0085 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0085 (target) VALUES ('');
INSERT INTO t1_a0085 (target) VALUES ('a');
INSERT INTO t1_a0085 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0085 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0085 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0085 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0085 (target) VALUES (NULL);
INSERT INTO t2_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0085 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0085 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0085 (target) VALUES ('');
INSERT INTO t2_a0085 (target) VALUES ('a');
INSERT INTO t2_a0085 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0086, t2_a0086;
SET SESSION sql_mode = '';
CREATE TABLE t1_a0086 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0086 (target) VALUES ('');
INSERT INTO t1_a0086 (target) VALUES ('a');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES ('Hello');
INSERT INTO t1_a0086 (target) VALUES ('你好');
INSERT INTO t1_a0086 (target) VALUES ('🎉');
INSERT INTO t1_a0086 (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0086 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0086 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0086 (target) VALUES ('');
INSERT INTO t1_a0086 (target) VALUES ('a');
INSERT INTO t1_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0086 (target) VALUES (NULL);
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0086 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0086 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0086 (target) VALUES ('');
INSERT INTO t2_a0086 (target) VALUES ('a');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0086 (target) VALUES ('Hello');
INSERT INTO t2_a0086 (target) VALUES ('你好');
INSERT INTO t2_a0086 (target) VALUES ('🎉');
INSERT INTO t2_a0086 (target) VALUES (NULL);
INSERT INTO t2_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0086 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0086 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0086 (target) VALUES ('');
INSERT INTO t2_a0086 (target) VALUES ('a');
INSERT INTO t2_a0086 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0087, t2_a0087;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0087 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0087 MODIFY target CHAR(255) CHARACTER SET utf8mb4 NOT NULL, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0087 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0087 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0088, t2_a0088;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0088 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0088 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0088 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: SUCCESS
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_a0089, t2_a0089;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(254) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_a0089 MODIFY target CHAR(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '', ALGORITHM=instant;
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0089 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(255)
CREATE TABLE t2_a0089 (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target CHAR(255) CHARACTER SET utf8mb4 NOT NULL DEFAULT '',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant, Expected: FAIL
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_a0090, t2_a0090;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_a0090 (
  target CHAR(254) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t1_a0090 (target) VALUES ('');
INSERT INTO t1_a0090 (target) VALUES ('a');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_a0090 (target) VALUES ('Hello');
INSERT INTO t1_a0090 (target) VALUES ('你好');
INSERT INTO t1_a0090 (target) VALUES ('🎉');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_a0090 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_a0090 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t1_a0090 (target) VALUES ('');
INSERT INTO t1_a0090 (target) VALUES ('a');
INSERT INTO t1_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
-- Insert value exceeding new type (expected FAIL on both tables)
-- INSERT INTO t1_a0090 (target) VALUES ('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
-- Oracle table: CHAR(254)
CREATE TABLE t2_a0090 (
  target CHAR(254) CHARACTER SET utf8mb4,
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8mb4;
INSERT INTO t2_a0090 (target) VALUES ('');
INSERT INTO t2_a0090 (target) VALUES ('a');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t2_a0090 (target) VALUES ('Hello');
INSERT INTO t2_a0090 (target) VALUES ('你好');
INSERT INTO t2_a0090 (target) VALUES ('🎉');
INSERT INTO t2_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0090 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t2_a0090 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
INSERT INTO t2_a0090 (target) VALUES ('');
INSERT INTO t2_a0090 (target) VALUES ('a');
INSERT INTO t2_a0090 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
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
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0091, t2_tc_aa0091;
CREATE TABLE t1_tc_aa0091 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(254) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0091 (target) VALUES ('');
INSERT INTO t1_tc_aa0091 (target) VALUES ('a');
INSERT INTO t1_tc_aa0091 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0091 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0091 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0091 MODIFY target CHAR(255) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_aa0091 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0091 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0091 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0091' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0091' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-AA0092
-- Column attribute preservation: CHARSET
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0092, t2_tc_aa0092;
CREATE TABLE t1_tc_aa0092 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(254) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0092 (target) VALUES ('');
INSERT INTO t1_tc_aa0092 (target) VALUES ('a');
INSERT INTO t1_tc_aa0092 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0092 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0092 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0092 MODIFY target CHAR(255) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_aa0092 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0092 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0092 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0092' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0092' AND column_name='target' AND character_set_name='utf8mb4';

-- Test Case: TC-AA0093
-- Column attribute preservation: COLLATE
-- Type: CHAR(254) -> CHAR(255), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aa0093, t2_tc_aa0093;
CREATE TABLE t1_tc_aa0093 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target CHAR(254) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aa0093 (target) VALUES ('');
INSERT INTO t1_tc_aa0093 (target) VALUES ('a');
INSERT INTO t1_tc_aa0093 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0093 (target) VALUES ('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
INSERT INTO t1_tc_aa0093 (target) VALUES ('Hello');
ALTER TABLE t1_tc_aa0093 MODIFY target CHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=instant;
INSERT INTO t1_tc_aa0093 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0093 (target) VALUES ('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz');
INSERT INTO t1_tc_aa0093 (target) VALUES ('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww');
SELECT 'TC-AA0093' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aa0093' AND column_name='target' AND collation_name='utf8mb4_bin';

