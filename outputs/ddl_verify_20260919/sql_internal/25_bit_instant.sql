-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 4dfbe1e59c0b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 25: BIT INSTANT

-- Test Case: TC-25-REG-0001-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: BASELINE
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0001_it, t2_tc_25_reg_0001_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0001_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0001_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0001_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0001_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0001_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0001_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0001_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0001_it a JOIN t2_tc_25_reg_0001_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0002-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=COMPACT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0002_it, t2_tc_25_reg_0002_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0002_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0002_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0002_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0002_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0002_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0002_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0002_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0002_it a JOIN t2_tc_25_reg_0002_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0003-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=REDUNDANT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0003_it, t2_tc_25_reg_0003_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0003_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0003_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0003_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0003_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0003_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0003_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0003_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0003_it a JOIN t2_tc_25_reg_0003_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0004-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: FAIL
-- Varied factor: primary_key=COMPOSITE_PK
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0004_it, t2_tc_25_reg_0004_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0004_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'0');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0004_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0004_it (target) VALUES (b'1010');
-- Oracle table: BIT(1)
CREATE TABLE t2_tc_25_reg_0004_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0004_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0004-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0004_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0004_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0004_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0004_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0004_it a JOIN t2_tc_25_reg_0004_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0005-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: primary_key=NO_EXPLICIT_PK
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0005_it, t2_tc_25_reg_0005_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0005_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0005_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0005_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0005_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0005_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0005-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0005_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0005_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0005_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0005_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0005_it a JOIN t2_tc_25_reg_0005_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0006-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=NONE
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0006_it, t2_tc_25_reg_0006_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0006_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0006_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0006_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0006_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0006_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0006-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0006_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0006_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0006_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0006_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0006_it a JOIN t2_tc_25_reg_0006_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0007-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=MULTIPLE_SECONDARY
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0007_it, t2_tc_25_reg_0007_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0007_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0007_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0007_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0007_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0007_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0007-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0007_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0007_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0007_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0007_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0007_it a JOIN t2_tc_25_reg_0007_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0008-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=UNIQUE
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0008_it, t2_tc_25_reg_0008_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0008_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0008_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0008_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0008_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0008_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0008-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0008_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0008_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0008_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0008_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0008_it a JOIN t2_tc_25_reg_0008_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0009-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=COMPOSITE_PREFIX
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0009_it, t2_tc_25_reg_0009_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0009_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0009_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0009_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0009_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0009_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0009-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0009_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0009_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0009_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0009_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0009_it a JOIN t2_tc_25_reg_0009_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0010-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=FIRST
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0010_it, t2_tc_25_reg_0010_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0010_it (
  target BIT(1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0010_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0010_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0010_it (
  target BIT(8),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0010_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0010-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0010_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0010_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0010_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0010_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0010_it a JOIN t2_tc_25_reg_0010_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0011-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=LAST
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_tc_25_reg_0011_it, t2_tc_25_reg_0011_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0011_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(1), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0011_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0011_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0011_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(8), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0011_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0011-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0011_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0011_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0011_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0011_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0011_it a JOIN t2_tc_25_reg_0011_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0012-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_NO_DEFAULT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0012_it, t2_tc_25_reg_0012_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0012_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0012_it MODIFY target BIT(8) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0012_it (target) VALUES (b'1010');
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0012_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0012_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0012-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0012_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0012_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0012_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0012_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0012_it a JOIN t2_tc_25_reg_0012_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0013-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=CONSTANT_DEFAULT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0013_it, t2_tc_25_reg_0013_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0013_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0013_it MODIFY target BIT(8) DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0013_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0013_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0013_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0013-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0013_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0013_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0013_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0013_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0013_it a JOIN t2_tc_25_reg_0013_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0014-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NULL_DEFAULT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0014_it, t2_tc_25_reg_0014_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0014_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0014_it MODIFY target BIT(8) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0014_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0014_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0014_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0014-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0014_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0014_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0014_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0014_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0014_it a JOIN t2_tc_25_reg_0014_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0015-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_DEFAULT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0015_it, t2_tc_25_reg_0015_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0015_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0015_it MODIFY target BIT(8) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0015_it (target) VALUES (b'1010');
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0015_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0015_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0015-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0015_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0015_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0015_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0015_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0015_it a JOIN t2_tc_25_reg_0015_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0016-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=INVISIBLE
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0016_it, t2_tc_25_reg_0016_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0016_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0016_it MODIFY target BIT(8) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0016_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0016_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0016_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0016-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0016_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0016_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0016_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0016_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0016_it a JOIN t2_tc_25_reg_0016_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0017-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S0
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0017_it, t2_tc_25_reg_0017_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0017_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0017_it MODIFY target BIT(8), ALGORITHM=instant;
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0017_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0017-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0017_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0017_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0017_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0017_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0017_it a JOIN t2_tc_25_reg_0017_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0018-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S1
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0018_it, t2_tc_25_reg_0018_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0018_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0018_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0018_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0018_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0018_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0018-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0018_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0018_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0018_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0018_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0018_it a JOIN t2_tc_25_reg_0018_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0019-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=UNIFORM
-- Transition ID: BIT-01
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0019_it, t2_tc_25_reg_0019_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0019_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0019_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0019_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0019_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0019_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0019-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0019_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0019_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0019_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0019_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0019_it a JOIN t2_tc_25_reg_0019_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0020-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=MONOTONIC
-- Transition ID: BIT-01
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0020_it, t2_tc_25_reg_0020_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0020_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0020_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0020_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0020_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0020_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0020-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0020_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0020_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0020_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0020_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0020_it a JOIN t2_tc_25_reg_0020_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0021-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ZERO
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0021_it, t2_tc_25_reg_0021_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0021_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0021_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0021_it (target) VALUES (b'1010');
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0021_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0021_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0021-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0021_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0021_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0021_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0021_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0021_it a JOIN t2_tc_25_reg_0021_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0022-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=SINGLE
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0022_it, t2_tc_25_reg_0022_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0022_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0022_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0022_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0022_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0022_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0022-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0022_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0022_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0022_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0022_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0022_it a JOIN t2_tc_25_reg_0022_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0023-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ALL
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0023_it, t2_tc_25_reg_0023_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0023_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0023_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0023_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0023_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0023_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0023-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0023_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0023_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0023_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0023_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0023_it a JOIN t2_tc_25_reg_0023_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0024-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: sql_mode=NON_STRICT
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0024_it, t2_tc_25_reg_0024_it;
SET SESSION sql_mode = '';
CREATE TABLE t1_tc_25_reg_0024_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0024_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0024_it (target) VALUES (NULL);
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0024_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0024_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0024-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0024_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0024_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0024_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0024_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0024_it a JOIN t2_tc_25_reg_0024_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0025-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-01
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0025_it, t2_tc_25_reg_0025_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0025_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0025_it MODIFY target BIT(8) NOT NULL, ALGORITHM=instant;
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0025_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0025-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0025_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0025_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0025_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0025_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0025_it a JOIN t2_tc_25_reg_0025_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0026-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-03
-- Transition ID: BIT-01
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0026_it, t2_tc_25_reg_0026_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0026_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0026_it MODIFY target BIT(8), ALGORITHM=instant;
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0026_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0026-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0026_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0026_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0026_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0026_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0026_it a JOIN t2_tc_25_reg_0026_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0027-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-04
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0027_it, t2_tc_25_reg_0027_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0027_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(1) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0027_it MODIFY target BIT(8) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0027_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0027-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0027_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0027_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0027_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0027_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0027_it a JOIN t2_tc_25_reg_0027_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0028-IT
-- Type: BIT(1) -> BIT(8), Algorithm: instant, Expected: FAIL
-- Varied factor: KP-05
-- Transition ID: BIT-01
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0028_it, t2_tc_25_reg_0028_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0028_it (
  target BIT(1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'0');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0028_it MODIFY target BIT(8), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'11111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'11');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0028_it (target) VALUES (b'1010');
-- Oracle table: BIT(1)
CREATE TABLE t2_tc_25_reg_0028_it (
  target BIT(1),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'11');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0028_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0028-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0028_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0028_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0028_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0028_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0028_it a JOIN t2_tc_25_reg_0028_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-ATR-0001-IT
-- Column attribute preservation: COMMENT
-- Type: BIT(1) -> BIT(8), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_25_atr_0001_it, t2_tc_25_atr_0001_it;
CREATE TABLE t1_tc_25_atr_0001_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIT(1) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'0');
ALTER TABLE t1_tc_25_atr_0001_it MODIFY target BIT(8) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'11');
INSERT INTO t1_tc_25_atr_0001_it (target) VALUES (b'1');
SELECT 'TC-25-ATR-0001-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_25_atr_0001_it' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-25-REG-0029-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: BASELINE
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0029_it, t2_tc_25_reg_0029_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0029_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0029_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0029_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0029_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0029_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0029-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0029_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0029_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0029_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0029_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0029_it a JOIN t2_tc_25_reg_0029_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0030-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=COMPACT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0030_it, t2_tc_25_reg_0030_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0030_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0030_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0030_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0030_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0030_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0030-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0030_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0030_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0030_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0030_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0030_it a JOIN t2_tc_25_reg_0030_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0031-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=REDUNDANT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0031_it, t2_tc_25_reg_0031_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0031_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0031_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0031_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0031_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0031_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0031-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0031_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0031_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0031_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0031_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0031_it a JOIN t2_tc_25_reg_0031_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0032-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: FAIL
-- Varied factor: primary_key=COMPOSITE_PK
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0032_it, t2_tc_25_reg_0032_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0032_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0032_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0032_it (target) VALUES (b'1010');
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0032_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0032_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0032-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0032_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0032_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0032_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0032_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0032_it a JOIN t2_tc_25_reg_0032_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0033-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: primary_key=NO_EXPLICIT_PK
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0033_it, t2_tc_25_reg_0033_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0033_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0033_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0033_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0033_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0033_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0033-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0033_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0033_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0033_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0033_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0033_it a JOIN t2_tc_25_reg_0033_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0034-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=NONE
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0034_it, t2_tc_25_reg_0034_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0034_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0034_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0034_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0034_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0034_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0034-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0034_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0034_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0034_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0034_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0034_it a JOIN t2_tc_25_reg_0034_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0035-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=MULTIPLE_SECONDARY
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0035_it, t2_tc_25_reg_0035_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0035_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0035_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0035_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0035_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0035_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0035-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0035_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0035_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0035_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0035_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0035_it a JOIN t2_tc_25_reg_0035_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0036-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=UNIQUE
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0036_it, t2_tc_25_reg_0036_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0036_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0036_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0036_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0036_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0036_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0036-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0036_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0036_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0036_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0036_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0036_it a JOIN t2_tc_25_reg_0036_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0037-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=COMPOSITE_PREFIX
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0037_it, t2_tc_25_reg_0037_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0037_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0037_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0037_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0037_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0037_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0037-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0037_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0037_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0037_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0037_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0037_it a JOIN t2_tc_25_reg_0037_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0038-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=FIRST
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0038_it, t2_tc_25_reg_0038_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0038_it (
  target BIT(8),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0038_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0038_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0038_it (
  target BIT(16),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0038_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0038-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0038_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0038_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0038_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0038_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0038_it a JOIN t2_tc_25_reg_0038_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0039-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=LAST
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_tc_25_reg_0039_it, t2_tc_25_reg_0039_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0039_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(8), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0039_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0039_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0039_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(16), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0039_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0039-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0039_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0039_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0039_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0039_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0039_it a JOIN t2_tc_25_reg_0039_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0040-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_NO_DEFAULT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0040_it, t2_tc_25_reg_0040_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0040_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0040_it MODIFY target BIT(16) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0040_it (target) VALUES (b'1010');
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0040_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0040_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0040-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0040_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0040_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0040_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0040_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0040_it a JOIN t2_tc_25_reg_0040_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0041-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=CONSTANT_DEFAULT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0041_it, t2_tc_25_reg_0041_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0041_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0041_it MODIFY target BIT(16) DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0041_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0041_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0041_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0041-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0041_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0041_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0041_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0041_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0041_it a JOIN t2_tc_25_reg_0041_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0042-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NULL_DEFAULT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0042_it, t2_tc_25_reg_0042_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0042_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0042_it MODIFY target BIT(16) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0042_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0042_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0042_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0042-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0042_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0042_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0042_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0042_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0042_it a JOIN t2_tc_25_reg_0042_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0043-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_DEFAULT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0043_it, t2_tc_25_reg_0043_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0043_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0043_it MODIFY target BIT(16) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0043_it (target) VALUES (b'1010');
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0043_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0043_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0043-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0043_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0043_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0043_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0043_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0043_it a JOIN t2_tc_25_reg_0043_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0044-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=INVISIBLE
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0044_it, t2_tc_25_reg_0044_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0044_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0044_it MODIFY target BIT(16) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0044_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0044_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0044_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0044-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0044_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0044_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0044_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0044_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0044_it a JOIN t2_tc_25_reg_0044_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0045-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S0
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0045_it, t2_tc_25_reg_0045_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0045_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0045_it MODIFY target BIT(16), ALGORITHM=instant;
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0045_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0045-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0045_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0045_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0045_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0045_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0045_it a JOIN t2_tc_25_reg_0045_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0046-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S1
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0046_it, t2_tc_25_reg_0046_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0046_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0046_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0046_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0046_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0046_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0046-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0046_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0046_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0046_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0046_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0046_it a JOIN t2_tc_25_reg_0046_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0047-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=UNIFORM
-- Transition ID: BIT-02
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0047_it, t2_tc_25_reg_0047_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0047_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0047_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0047_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0047_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0047_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0047-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0047_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0047_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0047_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0047_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0047_it a JOIN t2_tc_25_reg_0047_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0048-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=MONOTONIC
-- Transition ID: BIT-02
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0048_it, t2_tc_25_reg_0048_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0048_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0048_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0048_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0048_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0048_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0048-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0048_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0048_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0048_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0048_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0048_it a JOIN t2_tc_25_reg_0048_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0049-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ZERO
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0049_it, t2_tc_25_reg_0049_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0049_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0049_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0049_it (target) VALUES (b'1010');
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0049_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0049_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0049-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0049_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0049_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0049_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0049_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0049_it a JOIN t2_tc_25_reg_0049_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0050-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=SINGLE
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0050_it, t2_tc_25_reg_0050_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0050_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0050_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0050_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0050_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0050_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0050-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0050_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0050_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0050_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0050_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0050_it a JOIN t2_tc_25_reg_0050_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0051-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ALL
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0051_it, t2_tc_25_reg_0051_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0051_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0051_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0051_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0051_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0051_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0051-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0051_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0051_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0051_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0051_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0051_it a JOIN t2_tc_25_reg_0051_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0052-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: sql_mode=NON_STRICT
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0052_it, t2_tc_25_reg_0052_it;
SET SESSION sql_mode = '';
CREATE TABLE t1_tc_25_reg_0052_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0052_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0052_it (target) VALUES (NULL);
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0052_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0052_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0052-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0052_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0052_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0052_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0052_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0052_it a JOIN t2_tc_25_reg_0052_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0053-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-01
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0053_it, t2_tc_25_reg_0053_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0053_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0053_it MODIFY target BIT(16) NOT NULL, ALGORITHM=instant;
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0053_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0053-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0053_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0053_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0053_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0053_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0053_it a JOIN t2_tc_25_reg_0053_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0054-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-03
-- Transition ID: BIT-02
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0054_it, t2_tc_25_reg_0054_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0054_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0054_it MODIFY target BIT(16), ALGORITHM=instant;
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0054_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0054-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0054_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0054_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0054_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0054_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0054_it a JOIN t2_tc_25_reg_0054_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0055-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-04
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0055_it, t2_tc_25_reg_0055_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0055_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(8) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0055_it MODIFY target BIT(16) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0055_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0055-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0055_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0055_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0055_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0055_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0055_it a JOIN t2_tc_25_reg_0055_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0056-IT
-- Type: BIT(8) -> BIT(16), Algorithm: instant, Expected: FAIL
-- Varied factor: KP-05
-- Transition ID: BIT-02
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0056_it, t2_tc_25_reg_0056_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0056_it (
  target BIT(8),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0056_it MODIFY target BIT(16), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'1111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0056_it (target) VALUES (b'1010');
-- Oracle table: BIT(8)
CREATE TABLE t2_tc_25_reg_0056_it (
  target BIT(8),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'111111111');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0056_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0056-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0056_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0056_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0056_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0056_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0056_it a JOIN t2_tc_25_reg_0056_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-ATR-0002-IT
-- Column attribute preservation: COMMENT
-- Type: BIT(8) -> BIT(16), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_25_atr_0002_it, t2_tc_25_atr_0002_it;
CREATE TABLE t1_tc_25_atr_0002_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIT(8) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'1010');
ALTER TABLE t1_tc_25_atr_0002_it MODIFY target BIT(16) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'111111111');
INSERT INTO t1_tc_25_atr_0002_it (target) VALUES (b'1');
SELECT 'TC-25-ATR-0002-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_25_atr_0002_it' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-25-REG-0057-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: BASELINE
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0057_it, t2_tc_25_reg_0057_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0057_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0057_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0057_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0057_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0057_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0057-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0057_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0057_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0057_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0057_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0057_it a JOIN t2_tc_25_reg_0057_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0058-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=COMPACT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0058_it, t2_tc_25_reg_0058_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0058_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0058_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0058_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0058_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0058_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0058-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0058_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0058_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0058_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0058_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0058_it a JOIN t2_tc_25_reg_0058_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0059-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=REDUNDANT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0059_it, t2_tc_25_reg_0059_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0059_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0059_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0059_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0059_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0059_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0059-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0059_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0059_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0059_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0059_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0059_it a JOIN t2_tc_25_reg_0059_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0060-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: FAIL
-- Varied factor: primary_key=COMPOSITE_PK
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0060_it, t2_tc_25_reg_0060_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0060_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0060_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0060_it (target) VALUES (b'1010');
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0060_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0060_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0060-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0060_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0060_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0060_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0060_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0060_it a JOIN t2_tc_25_reg_0060_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0061-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: primary_key=NO_EXPLICIT_PK
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0061_it, t2_tc_25_reg_0061_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0061_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0061_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0061_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0061_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0061_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0061-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0061_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0061_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0061_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0061_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0061_it a JOIN t2_tc_25_reg_0061_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0062-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=NONE
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0062_it, t2_tc_25_reg_0062_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0062_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0062_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0062_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0062_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0062_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0062-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0062_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0062_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0062_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0062_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0062_it a JOIN t2_tc_25_reg_0062_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0063-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=MULTIPLE_SECONDARY
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0063_it, t2_tc_25_reg_0063_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0063_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0063_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0063_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0063_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0063_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0063-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0063_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0063_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0063_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0063_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0063_it a JOIN t2_tc_25_reg_0063_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0064-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=UNIQUE
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0064_it, t2_tc_25_reg_0064_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0064_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0064_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0064_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0064_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0064_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0064-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0064_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0064_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0064_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0064_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0064_it a JOIN t2_tc_25_reg_0064_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0065-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=COMPOSITE_PREFIX
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0065_it, t2_tc_25_reg_0065_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0065_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0065_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0065_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0065_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0065_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0065-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0065_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0065_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0065_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0065_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0065_it a JOIN t2_tc_25_reg_0065_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0066-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=FIRST
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0066_it, t2_tc_25_reg_0066_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0066_it (
  target BIT(16),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0066_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0066_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0066_it (
  target BIT(32),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0066_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0066-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0066_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0066_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0066_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0066_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0066_it a JOIN t2_tc_25_reg_0066_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0067-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=LAST
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_tc_25_reg_0067_it, t2_tc_25_reg_0067_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0067_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(16), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0067_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0067_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0067_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(32), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0067_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0067-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0067_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0067_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0067_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0067_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0067_it a JOIN t2_tc_25_reg_0067_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0068-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_NO_DEFAULT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0068_it, t2_tc_25_reg_0068_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0068_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0068_it MODIFY target BIT(32) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0068_it (target) VALUES (b'1010');
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0068_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0068_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0068-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0068_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0068_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0068_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0068_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0068_it a JOIN t2_tc_25_reg_0068_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0069-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=CONSTANT_DEFAULT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0069_it, t2_tc_25_reg_0069_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0069_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0069_it MODIFY target BIT(32) DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0069_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0069_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0069_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0069-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0069_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0069_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0069_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0069_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0069_it a JOIN t2_tc_25_reg_0069_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0070-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NULL_DEFAULT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0070_it, t2_tc_25_reg_0070_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0070_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0070_it MODIFY target BIT(32) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0070_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0070_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0070_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0070-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0070_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0070_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0070_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0070_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0070_it a JOIN t2_tc_25_reg_0070_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0071-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_DEFAULT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0071_it, t2_tc_25_reg_0071_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0071_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0071_it MODIFY target BIT(32) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0071_it (target) VALUES (b'1010');
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0071_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0071_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0071-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0071_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0071_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0071_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0071_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0071_it a JOIN t2_tc_25_reg_0071_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0072-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=INVISIBLE
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0072_it, t2_tc_25_reg_0072_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0072_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0072_it MODIFY target BIT(32) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0072_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0072_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0072_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0072-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0072_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0072_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0072_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0072_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0072_it a JOIN t2_tc_25_reg_0072_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0073-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S0
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0073_it, t2_tc_25_reg_0073_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0073_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0073_it MODIFY target BIT(32), ALGORITHM=instant;
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0073_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0073-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0073_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0073_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0073_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0073_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0073_it a JOIN t2_tc_25_reg_0073_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0074-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S1
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0074_it, t2_tc_25_reg_0074_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0074_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0074_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0074_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0074_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0074_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0074-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0074_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0074_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0074_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0074_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0074_it a JOIN t2_tc_25_reg_0074_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0075-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=UNIFORM
-- Transition ID: BIT-03
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0075_it, t2_tc_25_reg_0075_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0075_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0075_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0075_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0075_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0075_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0075-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0075_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0075_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0075_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0075_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0075_it a JOIN t2_tc_25_reg_0075_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0076-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=MONOTONIC
-- Transition ID: BIT-03
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0076_it, t2_tc_25_reg_0076_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0076_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0076_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0076_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0076_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0076_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0076-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0076_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0076_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0076_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0076_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0076_it a JOIN t2_tc_25_reg_0076_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0077-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ZERO
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0077_it, t2_tc_25_reg_0077_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0077_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0077_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0077_it (target) VALUES (b'1010');
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0077_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0077_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0077-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0077_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0077_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0077_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0077_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0077_it a JOIN t2_tc_25_reg_0077_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0078-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=SINGLE
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0078_it, t2_tc_25_reg_0078_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0078_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0078_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0078_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0078_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0078_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0078-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0078_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0078_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0078_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0078_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0078_it a JOIN t2_tc_25_reg_0078_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0079-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ALL
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0079_it, t2_tc_25_reg_0079_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0079_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0079_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0079_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0079_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0079_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0079-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0079_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0079_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0079_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0079_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0079_it a JOIN t2_tc_25_reg_0079_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0080-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: sql_mode=NON_STRICT
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0080_it, t2_tc_25_reg_0080_it;
SET SESSION sql_mode = '';
CREATE TABLE t1_tc_25_reg_0080_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0080_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0080_it (target) VALUES (NULL);
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0080_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0080_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0080-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0080_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0080_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0080_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0080_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0080_it a JOIN t2_tc_25_reg_0080_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0081-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-01
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0081_it, t2_tc_25_reg_0081_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0081_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0081_it MODIFY target BIT(32) NOT NULL, ALGORITHM=instant;
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0081_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0081-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0081_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0081_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0081_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0081_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0081_it a JOIN t2_tc_25_reg_0081_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0082-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-03
-- Transition ID: BIT-03
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0082_it, t2_tc_25_reg_0082_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0082_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0082_it MODIFY target BIT(32), ALGORITHM=instant;
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0082_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0082-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0082_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0082_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0082_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0082_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0082_it a JOIN t2_tc_25_reg_0082_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0083-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-04
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0083_it, t2_tc_25_reg_0083_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0083_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(16) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0083_it MODIFY target BIT(32) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0083_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0083-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0083_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0083_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0083_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0083_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0083_it a JOIN t2_tc_25_reg_0083_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0084-IT
-- Type: BIT(16) -> BIT(32), Algorithm: instant, Expected: FAIL
-- Varied factor: KP-05
-- Transition ID: BIT-03
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0084_it, t2_tc_25_reg_0084_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0084_it (
  target BIT(16),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0084_it MODIFY target BIT(32), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'11111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'11111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_reg_0084_it (target) VALUES (b'1010');
-- Oracle table: BIT(16)
CREATE TABLE t2_tc_25_reg_0084_it (
  target BIT(16),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'11111111111111111');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1111111111111111');
INSERT INTO t2_tc_25_reg_0084_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0084-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0084_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0084_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0084_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0084_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0084_it a JOIN t2_tc_25_reg_0084_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-ATR-0003-IT
-- Column attribute preservation: COMMENT
-- Type: BIT(16) -> BIT(32), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_25_atr_0003_it, t2_tc_25_atr_0003_it;
CREATE TABLE t1_tc_25_atr_0003_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIT(16) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'1111111111111111');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'1010');
ALTER TABLE t1_tc_25_atr_0003_it MODIFY target BIT(32) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'11111111111111111');
INSERT INTO t1_tc_25_atr_0003_it (target) VALUES (b'1');
SELECT 'TC-25-ATR-0003-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_25_atr_0003_it' AND column_name='target' AND column_comment='test_comment';

-- Test Case: TC-25-REG-0085-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: BASELINE
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0085_it, t2_tc_25_reg_0085_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0085_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0085_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0085_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0085_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0085_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0085-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0085_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0085_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0085_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0085_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0085_it a JOIN t2_tc_25_reg_0085_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0086-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=COMPACT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=COMPACT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0086_it, t2_tc_25_reg_0086_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0086_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0086_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0086_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0086_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=COMPACT;
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0086_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0086-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0086_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0086_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0086_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0086_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0086_it a JOIN t2_tc_25_reg_0086_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0087-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: row_format=REDUNDANT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=REDUNDANT, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0087_it, t2_tc_25_reg_0087_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0087_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0087_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0087_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0087_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=REDUNDANT;
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0087_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0087-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0087_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0087_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0087_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0087_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0087_it a JOIN t2_tc_25_reg_0087_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0088-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: FAIL
-- Varied factor: primary_key=COMPOSITE_PK
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0088_it, t2_tc_25_reg_0088_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0088_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0088_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0088_it (target) VALUES (b'1010');
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0088_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0088_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0088-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0088_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0088_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0088_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0088_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0088_it a JOIN t2_tc_25_reg_0088_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0089-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: primary_key=NO_EXPLICIT_PK
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=NO_EXPLICIT_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0089_it, t2_tc_25_reg_0089_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0089_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0089_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0089_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0089_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', INDEX idx_id (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0089_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0089-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0089_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0089_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0089_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0089_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0089_it a JOIN t2_tc_25_reg_0089_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0090-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=NONE
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=NONE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0090_it, t2_tc_25_reg_0090_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0090_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0090_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0090_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0090_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0090_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0090-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0090_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0090_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0090_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0090_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0090_it a JOIN t2_tc_25_reg_0090_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0091-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=MULTIPLE_SECONDARY
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=MULTIPLE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0091_it, t2_tc_25_reg_0091_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0091_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0091_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0091_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0091_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1), INDEX idx_pad2 (pad2)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0091_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0091-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0091_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0091_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0091_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0091_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0091_it a JOIN t2_tc_25_reg_0091_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0092-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=UNIQUE
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=UNIQUE, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0092_it, t2_tc_25_reg_0092_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0092_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0092_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0092_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0092_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), UNIQUE INDEX uq_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0092_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0092-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0092_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0092_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0092_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0092_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0092_it a JOIN t2_tc_25_reg_0092_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0093-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: non_target_index=COMPOSITE_PREFIX
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=COMPOSITE_PREFIX, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0093_it, t2_tc_25_reg_0093_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0093_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0093_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0093_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0093_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_composite (pad1(10), pad2(10))
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0093_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0093-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0093_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0093_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0093_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0093_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0093_it a JOIN t2_tc_25_reg_0093_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0094-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=FIRST
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0094_it, t2_tc_25_reg_0094_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0094_it (
  target BIT(32),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0094_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0094_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0094_it (
  target BIT(64),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0094_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0094-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0094_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0094_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0094_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0094_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0094_it a JOIN t2_tc_25_reg_0094_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0095-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_position=LAST
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=LAST
DROP TABLE IF EXISTS t1_tc_25_reg_0095_it, t2_tc_25_reg_0095_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0095_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(32), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0095_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0095_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0095_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2',
  target BIT(64), PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0095_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0095-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0095_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0095_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0095_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0095_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0095_it a JOIN t2_tc_25_reg_0095_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0096-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_NO_DEFAULT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0096_it, t2_tc_25_reg_0096_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0096_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0096_it MODIFY target BIT(64) NOT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0096_it (target) VALUES (b'1010');
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0096_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0096_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0096-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0096_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0096_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0096_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0096_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0096_it a JOIN t2_tc_25_reg_0096_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0097-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=CONSTANT_DEFAULT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=CONSTANT_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0097_it, t2_tc_25_reg_0097_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0097_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0097_it MODIFY target BIT(64) DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0097_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0097_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0097_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0097-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0097_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0097_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0097_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0097_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0097_it a JOIN t2_tc_25_reg_0097_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0098-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NULL_DEFAULT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0098_it, t2_tc_25_reg_0098_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0098_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0098_it MODIFY target BIT(64) DEFAULT NULL, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0098_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0098_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) DEFAULT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0098_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0098-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0098_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0098_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0098_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0098_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0098_it a JOIN t2_tc_25_reg_0098_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0099-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=NOT_NULL_DEFAULT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0099_it, t2_tc_25_reg_0099_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0099_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0099_it MODIFY target BIT(64) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0099_it (target) VALUES (b'1010');
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0099_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0099_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0099-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0099_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0099_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0099_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0099_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0099_it a JOIN t2_tc_25_reg_0099_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0100-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: target_attributes=INVISIBLE
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=INVISIBLE, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0100_it, t2_tc_25_reg_0100_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0100_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0100_it MODIFY target BIT(64) INVISIBLE, ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0100_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0100_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) INVISIBLE,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0100_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0100-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0100_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0100_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0100_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0100_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0100_it a JOIN t2_tc_25_reg_0100_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0101-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S0
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0101_it, t2_tc_25_reg_0101_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0101_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0101_it MODIFY target BIT(64), ALGORITHM=instant;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0101_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0101-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0101_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0101_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0101_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0101_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0101_it a JOIN t2_tc_25_reg_0101_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0102-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_scale=S1
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S1, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0102_it, t2_tc_25_reg_0102_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0102_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'0');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0102_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0102_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0102_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0102_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0102-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0102_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0102_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0102_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0102_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0102_it a JOIN t2_tc_25_reg_0102_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0103-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=UNIFORM
-- Transition ID: BIT-04
-- Factors: data_distribution=UNIFORM, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0103_it, t2_tc_25_reg_0103_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0103_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0103_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0103_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0103_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0103_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0103-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0103_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0103_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0103_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0103_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0103_it a JOIN t2_tc_25_reg_0103_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0104-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: data_distribution=MONOTONIC
-- Transition ID: BIT-04
-- Factors: data_distribution=MONOTONIC, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0104_it, t2_tc_25_reg_0104_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0104_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0104_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0104_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0104_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0104_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0104-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0104_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0104_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0104_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0104_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0104_it a JOIN t2_tc_25_reg_0104_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0105-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ZERO
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ZERO, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0105_it, t2_tc_25_reg_0105_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0105_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'11111111');
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0105_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0105_it (target) VALUES (b'1010');
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0105_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0105_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0105-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0105_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0105_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0105_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0105_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0105_it a JOIN t2_tc_25_reg_0105_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0106-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=SINGLE
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=SINGLE, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0106_it, t2_tc_25_reg_0106_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0106_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0106_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0106_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0106_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0106_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0106-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0106_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0106_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0106_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0106_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0106_it a JOIN t2_tc_25_reg_0106_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0107-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: null_ratio=ALL
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=ALL, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0107_it, t2_tc_25_reg_0107_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0107_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0107_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0107_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0107_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0107_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0107-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0107_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0107_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0107_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0107_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0107_it a JOIN t2_tc_25_reg_0107_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0108-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: sql_mode=NON_STRICT
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=NON_STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0108_it, t2_tc_25_reg_0108_it;
SET SESSION sql_mode = '';
CREATE TABLE t1_tc_25_reg_0108_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'11111111');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (NULL);
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0108_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0108_it (target) VALUES (NULL);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0108_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (NULL);
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0108_it (target) VALUES (NULL);
SELECT 'TC-25-REG-0108-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0108_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0108_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0108_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0108_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0108_it a JOIN t2_tc_25_reg_0108_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0109-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-01
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0109_it, t2_tc_25_reg_0109_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0109_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0109_it MODIFY target BIT(64) NOT NULL, ALGORITHM=instant;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0109_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) NOT NULL,
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0109-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0109_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0109_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0109_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0109_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0109_it a JOIN t2_tc_25_reg_0109_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0110-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-03
-- Transition ID: BIT-04
-- Factors: data_distribution=UNIFORM, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0110_it, t2_tc_25_reg_0110_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0110_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0110_it MODIFY target BIT(64), ALGORITHM=instant;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0110_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64),
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0110-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0110_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0110_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0110_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0110_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0110_it a JOIN t2_tc_25_reg_0110_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0111-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: SUCCESS
-- Varied factor: KP-04
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S0, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=CLUSTERED, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NOT_NULL_DEFAULT, target_position=MIDDLE
DROP TABLE IF EXISTS t1_tc_25_reg_0111_it, t2_tc_25_reg_0111_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0111_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(32) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
-- Expected: ALTER SUCCESS
ALTER TABLE t1_tc_25_reg_0111_it MODIFY target BIT(64) NOT NULL DEFAULT b'0', ALGORITHM=instant;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_25_reg_0111_it (
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  target BIT(64) NOT NULL DEFAULT b'0',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
SELECT 'TC-25-REG-0111-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0111_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0111_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0111_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0111_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0111_it a JOIN t2_tc_25_reg_0111_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-REG-0112-IT
-- Type: BIT(32) -> BIT(64), Algorithm: instant, Expected: FAIL
-- Varied factor: KP-05
-- Transition ID: BIT-04
-- Factors: data_distribution=TYPE_BOUNDARIES, data_scale=S100, dependencies=NONE, non_target_index=ONE_SECONDARY, null_ratio=TEN_PERCENT, primary_key=COMPOSITE_PK, row_format=DYNAMIC, sql_mode=STRICT, target_attributes=NULL_NO_DEFAULT, target_position=FIRST
DROP TABLE IF EXISTS t1_tc_25_reg_0112_it, t2_tc_25_reg_0112_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_25_reg_0112_it (
  target BIT(32),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'1010');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'11111111');
-- Expected: ALTER FAILS (table keeps old type)
ALTER TABLE t1_tc_25_reg_0112_it MODIFY target BIT(64), ALGORITHM=instant;
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'111111111111111111111111111111111');
-- Insert new-range value (may fail if ALTER failed)
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_reg_0112_it (target) VALUES (b'1010');
-- Oracle table: BIT(32)
CREATE TABLE t2_tc_25_reg_0112_it (
  target BIT(32),
  id INT NOT NULL AUTO_INCREMENT,
  pad1 VARCHAR(20) DEFAULT 'pad1',
  pad2 VARCHAR(20) DEFAULT 'pad2', PRIMARY KEY (id, target), INDEX idx_pad1 (pad1)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'1010');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'11111111');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'1');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'0');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t2_tc_25_reg_0112_it (target) VALUES (b'1010');
SELECT 'TC-25-REG-0112-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_25_reg_0112_it
   WHERE id NOT IN (SELECT id FROM t2_tc_25_reg_0112_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_25_reg_0112_it
   WHERE id NOT IN (SELECT id FROM t1_tc_25_reg_0112_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_25_reg_0112_it a JOIN t2_tc_25_reg_0112_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.pad1 <=> b.pad1 AND a.target <=> b.target AND a.pad2 <=> b.pad2)
) AS mismatches;

-- Test Case: TC-25-ATR-0004-IT
-- Column attribute preservation: COMMENT
-- Type: BIT(32) -> BIT(64), Algorithm: instant
DROP TABLE IF EXISTS t1_tc_25_atr_0004_it, t2_tc_25_atr_0004_it;
CREATE TABLE t1_tc_25_atr_0004_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIT(32) COMMENT 'test_comment',
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'11111111111111111111111111111111');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'1');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'0');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'1010');
ALTER TABLE t1_tc_25_atr_0004_it MODIFY target BIT(64) COMMENT 'test_comment', ALGORITHM=instant;
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'1111111111111111111111111111111111111111111111111111111111111111');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'111111111111111111111111111111111');
INSERT INTO t1_tc_25_atr_0004_it (target) VALUES (b'1');
SELECT 'TC-25-ATR-0004-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_25_atr_0004_it' AND column_name='target' AND column_comment='test_comment';

