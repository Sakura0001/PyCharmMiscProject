-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 1186b16f779b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 41: 类型转换兼容矩阵 (增强类型侧同一套探针，用于内网实例)

-- Test Case: TC-41-CONV-0001-DF
-- Conversion probe: DEC-D-UP
-- Type: DECIMAL(10,2) -> DECIMAL(12,4), Algorithm: default, Expected: MEASURE
-- Probe note: D 增大：整数位容量从 8 位缩到 8 位，小数位扩展
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=be0da4bb77e0 conv_probe=DEC-D-UP conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0001_df, t2_tc_41_conv_0001_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0001_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0001_df (target) VALUES (12345678.12);
INSERT INTO t1_tc_41_conv_0001_df (target) VALUES (0.00);
INSERT INTO t1_tc_41_conv_0001_df (target) VALUES (-1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0001_df MODIFY target DECIMAL(12,4);
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0001_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0001_df (target) VALUES (12345678.12);
INSERT INTO t2_tc_41_conv_0001_df (target) VALUES (0.00);
INSERT INTO t2_tc_41_conv_0001_df (target) VALUES (-1.5);
SELECT 'TC-41-CONV-0001-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0001_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0001_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0001_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0001_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0001_df a JOIN t2_tc_41_conv_0001_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0001-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0002-IT
-- Conversion probe: DEC-D-UP
-- Type: DECIMAL(10,2) -> DECIMAL(12,4), Algorithm: instant, Expected: MEASURE
-- Probe note: D 增大：整数位容量从 8 位缩到 8 位，小数位扩展
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=af4736d7fc8c conv_probe=DEC-D-UP conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0002_it, t2_tc_41_conv_0002_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0002_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0002_it (target) VALUES (12345678.12);
INSERT INTO t1_tc_41_conv_0002_it (target) VALUES (0.00);
INSERT INTO t1_tc_41_conv_0002_it (target) VALUES (-1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0002_it MODIFY target DECIMAL(12,4), ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0002_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0002_it (target) VALUES (12345678.12);
INSERT INTO t2_tc_41_conv_0002_it (target) VALUES (0.00);
INSERT INTO t2_tc_41_conv_0002_it (target) VALUES (-1.5);
SELECT 'TC-41-CONV-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0002_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0002_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0002_it a JOIN t2_tc_41_conv_0002_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0002-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0003-IP
-- Conversion probe: DEC-D-UP
-- Type: DECIMAL(10,2) -> DECIMAL(12,4), Algorithm: inplace, Expected: MEASURE
-- Probe note: D 增大：整数位容量从 8 位缩到 8 位，小数位扩展
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1402b6ae21f2 conv_probe=DEC-D-UP conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0003_ip, t2_tc_41_conv_0003_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0003_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0003_ip (target) VALUES (12345678.12);
INSERT INTO t1_tc_41_conv_0003_ip (target) VALUES (0.00);
INSERT INTO t1_tc_41_conv_0003_ip (target) VALUES (-1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0003_ip MODIFY target DECIMAL(12,4), ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0003_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0003_ip (target) VALUES (12345678.12);
INSERT INTO t2_tc_41_conv_0003_ip (target) VALUES (0.00);
INSERT INTO t2_tc_41_conv_0003_ip (target) VALUES (-1.5);
SELECT 'TC-41-CONV-0003-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0003_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0003_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0003_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0003_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0003_ip a JOIN t2_tc_41_conv_0003_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0003-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0004-CP
-- Conversion probe: DEC-D-UP
-- Type: DECIMAL(10,2) -> DECIMAL(12,4), Algorithm: copy, Expected: MEASURE
-- Probe note: D 增大：整数位容量从 8 位缩到 8 位，小数位扩展
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=c3209ff111c9 conv_probe=DEC-D-UP conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0004_cp, t2_tc_41_conv_0004_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0004_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0004_cp (target) VALUES (12345678.12);
INSERT INTO t1_tc_41_conv_0004_cp (target) VALUES (0.00);
INSERT INTO t1_tc_41_conv_0004_cp (target) VALUES (-1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0004_cp MODIFY target DECIMAL(12,4), ALGORITHM=COPY;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0004_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0004_cp (target) VALUES (12345678.12);
INSERT INTO t2_tc_41_conv_0004_cp (target) VALUES (0.00);
INSERT INTO t2_tc_41_conv_0004_cp (target) VALUES (-1.5);
SELECT 'TC-41-CONV-0004-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0004_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0004_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0004_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0004_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0004_cp a JOIN t2_tc_41_conv_0004_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0004-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0005-DF
-- Conversion probe: DEC-D-DOWN
-- Type: DECIMAL(10,4) -> DECIMAL(10,2), Algorithm: default, Expected: MEASURE
-- Probe note: D 减小：既有小数位必须被舍入（strict 下可能报错）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=0e88d21cbe00 conv_probe=DEC-D-DOWN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0005_df, t2_tc_41_conv_0005_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0005_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0005_df (target) VALUES (1234.5678);
INSERT INTO t1_tc_41_conv_0005_df (target) VALUES (0.0001);
INSERT INTO t1_tc_41_conv_0005_df (target) VALUES (-9.9999);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0005_df MODIFY target DECIMAL(10,2);
-- Oracle table: DECIMAL(10,4)
CREATE TABLE t2_tc_41_conv_0005_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0005_df (target) VALUES (1234.5678);
INSERT INTO t2_tc_41_conv_0005_df (target) VALUES (0.0001);
INSERT INTO t2_tc_41_conv_0005_df (target) VALUES (-9.9999);
SELECT 'TC-41-CONV-0005-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0005_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0005_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0005_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0005_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0005_df a JOIN t2_tc_41_conv_0005_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0005-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0006-IT
-- Conversion probe: DEC-D-DOWN
-- Type: DECIMAL(10,4) -> DECIMAL(10,2), Algorithm: instant, Expected: MEASURE
-- Probe note: D 减小：既有小数位必须被舍入（strict 下可能报错）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=9a1d85dded25 conv_probe=DEC-D-DOWN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0006_it, t2_tc_41_conv_0006_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0006_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0006_it (target) VALUES (1234.5678);
INSERT INTO t1_tc_41_conv_0006_it (target) VALUES (0.0001);
INSERT INTO t1_tc_41_conv_0006_it (target) VALUES (-9.9999);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0006_it MODIFY target DECIMAL(10,2), ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(10,4)
CREATE TABLE t2_tc_41_conv_0006_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0006_it (target) VALUES (1234.5678);
INSERT INTO t2_tc_41_conv_0006_it (target) VALUES (0.0001);
INSERT INTO t2_tc_41_conv_0006_it (target) VALUES (-9.9999);
SELECT 'TC-41-CONV-0006-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0006_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0006_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0006_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0006_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0006_it a JOIN t2_tc_41_conv_0006_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0006-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0007-IP
-- Conversion probe: DEC-D-DOWN
-- Type: DECIMAL(10,4) -> DECIMAL(10,2), Algorithm: inplace, Expected: MEASURE
-- Probe note: D 减小：既有小数位必须被舍入（strict 下可能报错）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=81baedabd55f conv_probe=DEC-D-DOWN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0007_ip, t2_tc_41_conv_0007_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0007_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0007_ip (target) VALUES (1234.5678);
INSERT INTO t1_tc_41_conv_0007_ip (target) VALUES (0.0001);
INSERT INTO t1_tc_41_conv_0007_ip (target) VALUES (-9.9999);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0007_ip MODIFY target DECIMAL(10,2), ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(10,4)
CREATE TABLE t2_tc_41_conv_0007_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0007_ip (target) VALUES (1234.5678);
INSERT INTO t2_tc_41_conv_0007_ip (target) VALUES (0.0001);
INSERT INTO t2_tc_41_conv_0007_ip (target) VALUES (-9.9999);
SELECT 'TC-41-CONV-0007-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0007_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0007_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0007_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0007_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0007_ip a JOIN t2_tc_41_conv_0007_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0007-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0008-CP
-- Conversion probe: DEC-D-DOWN
-- Type: DECIMAL(10,4) -> DECIMAL(10,2), Algorithm: copy, Expected: MEASURE
-- Probe note: D 减小：既有小数位必须被舍入（strict 下可能报错）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1c2e9ad5b327 conv_probe=DEC-D-DOWN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0008_cp, t2_tc_41_conv_0008_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0008_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0008_cp (target) VALUES (1234.5678);
INSERT INTO t1_tc_41_conv_0008_cp (target) VALUES (0.0001);
INSERT INTO t1_tc_41_conv_0008_cp (target) VALUES (-9.9999);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0008_cp MODIFY target DECIMAL(10,2), ALGORITHM=COPY;
-- Oracle table: DECIMAL(10,4)
CREATE TABLE t2_tc_41_conv_0008_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,4),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0008_cp (target) VALUES (1234.5678);
INSERT INTO t2_tc_41_conv_0008_cp (target) VALUES (0.0001);
INSERT INTO t2_tc_41_conv_0008_cp (target) VALUES (-9.9999);
SELECT 'TC-41-CONV-0008-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0008_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0008_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0008_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0008_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0008_cp a JOIN t2_tc_41_conv_0008_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0008-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0009-DF
-- Conversion probe: DEC-M-DOWN
-- Type: DECIMAL(12,2) -> DECIMAL(10,2), Algorithm: default, Expected: MEASURE
-- Probe note: M 减小：整数位容量缩小，既有数据可能溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=704726849bcf conv_probe=DEC-M-DOWN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0009_df, t2_tc_41_conv_0009_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0009_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0009_df (target) VALUES (1234567890.12);
INSERT INTO t1_tc_41_conv_0009_df (target) VALUES (1.00);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0009_df MODIFY target DECIMAL(10,2);
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_tc_41_conv_0009_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0009_df (target) VALUES (1234567890.12);
INSERT INTO t2_tc_41_conv_0009_df (target) VALUES (1.00);
SELECT 'TC-41-CONV-0009-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0009_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0009_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0009_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0009_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0009_df a JOIN t2_tc_41_conv_0009_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0009-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0010-IT
-- Conversion probe: DEC-M-DOWN
-- Type: DECIMAL(12,2) -> DECIMAL(10,2), Algorithm: instant, Expected: MEASURE
-- Probe note: M 减小：整数位容量缩小，既有数据可能溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=199367e58c2f conv_probe=DEC-M-DOWN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0010_it, t2_tc_41_conv_0010_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0010_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0010_it (target) VALUES (1234567890.12);
INSERT INTO t1_tc_41_conv_0010_it (target) VALUES (1.00);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0010_it MODIFY target DECIMAL(10,2), ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_tc_41_conv_0010_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0010_it (target) VALUES (1234567890.12);
INSERT INTO t2_tc_41_conv_0010_it (target) VALUES (1.00);
SELECT 'TC-41-CONV-0010-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0010_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0010_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0010_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0010_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0010_it a JOIN t2_tc_41_conv_0010_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0010-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0011-IP
-- Conversion probe: DEC-M-DOWN
-- Type: DECIMAL(12,2) -> DECIMAL(10,2), Algorithm: inplace, Expected: MEASURE
-- Probe note: M 减小：整数位容量缩小，既有数据可能溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e36befdc29e3 conv_probe=DEC-M-DOWN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0011_ip, t2_tc_41_conv_0011_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0011_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0011_ip (target) VALUES (1234567890.12);
INSERT INTO t1_tc_41_conv_0011_ip (target) VALUES (1.00);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0011_ip MODIFY target DECIMAL(10,2), ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_tc_41_conv_0011_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0011_ip (target) VALUES (1234567890.12);
INSERT INTO t2_tc_41_conv_0011_ip (target) VALUES (1.00);
SELECT 'TC-41-CONV-0011-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0011_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0011_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0011_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0011_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0011_ip a JOIN t2_tc_41_conv_0011_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0011-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0012-CP
-- Conversion probe: DEC-M-DOWN
-- Type: DECIMAL(12,2) -> DECIMAL(10,2), Algorithm: copy, Expected: MEASURE
-- Probe note: M 减小：整数位容量缩小，既有数据可能溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b0cf5da8e92f conv_probe=DEC-M-DOWN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0012_cp, t2_tc_41_conv_0012_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0012_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0012_cp (target) VALUES (1234567890.12);
INSERT INTO t1_tc_41_conv_0012_cp (target) VALUES (1.00);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0012_cp MODIFY target DECIMAL(10,2), ALGORITHM=COPY;
-- Oracle table: DECIMAL(12,2)
CREATE TABLE t2_tc_41_conv_0012_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(12,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0012_cp (target) VALUES (1234567890.12);
INSERT INTO t2_tc_41_conv_0012_cp (target) VALUES (1.00);
SELECT 'TC-41-CONV-0012-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0012_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0012_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0012_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0012_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0012_cp a JOIN t2_tc_41_conv_0012_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0012-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0013-DF
-- Conversion probe: DEC-MD-BOTH
-- Type: DECIMAL(10,2) -> DECIMAL(12,6), Algorithm: default, Expected: MEASURE
-- Probe note: M 与 D 同时增大
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=cf18da2cbde2 conv_probe=DEC-MD-BOTH conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0013_df, t2_tc_41_conv_0013_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0013_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0013_df (target) VALUES (1234.56);
INSERT INTO t1_tc_41_conv_0013_df (target) VALUES (0.01);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0013_df MODIFY target DECIMAL(12,6);
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0013_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0013_df (target) VALUES (1234.56);
INSERT INTO t2_tc_41_conv_0013_df (target) VALUES (0.01);
SELECT 'TC-41-CONV-0013-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0013_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0013_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0013_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0013_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0013_df a JOIN t2_tc_41_conv_0013_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0013-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0014-IT
-- Conversion probe: DEC-MD-BOTH
-- Type: DECIMAL(10,2) -> DECIMAL(12,6), Algorithm: instant, Expected: MEASURE
-- Probe note: M 与 D 同时增大
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f353eee7a9b6 conv_probe=DEC-MD-BOTH conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0014_it, t2_tc_41_conv_0014_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0014_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0014_it (target) VALUES (1234.56);
INSERT INTO t1_tc_41_conv_0014_it (target) VALUES (0.01);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0014_it MODIFY target DECIMAL(12,6), ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0014_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0014_it (target) VALUES (1234.56);
INSERT INTO t2_tc_41_conv_0014_it (target) VALUES (0.01);
SELECT 'TC-41-CONV-0014-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0014_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0014_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0014_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0014_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0014_it a JOIN t2_tc_41_conv_0014_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0014-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0015-IP
-- Conversion probe: DEC-MD-BOTH
-- Type: DECIMAL(10,2) -> DECIMAL(12,6), Algorithm: inplace, Expected: MEASURE
-- Probe note: M 与 D 同时增大
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ea557fd15971 conv_probe=DEC-MD-BOTH conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0015_ip, t2_tc_41_conv_0015_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0015_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0015_ip (target) VALUES (1234.56);
INSERT INTO t1_tc_41_conv_0015_ip (target) VALUES (0.01);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0015_ip MODIFY target DECIMAL(12,6), ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0015_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0015_ip (target) VALUES (1234.56);
INSERT INTO t2_tc_41_conv_0015_ip (target) VALUES (0.01);
SELECT 'TC-41-CONV-0015-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0015_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0015_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0015_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0015_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0015_ip a JOIN t2_tc_41_conv_0015_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0015-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0016-CP
-- Conversion probe: DEC-MD-BOTH
-- Type: DECIMAL(10,2) -> DECIMAL(12,6), Algorithm: copy, Expected: MEASURE
-- Probe note: M 与 D 同时增大
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a4184926673f conv_probe=DEC-MD-BOTH conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0016_cp, t2_tc_41_conv_0016_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0016_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0016_cp (target) VALUES (1234.56);
INSERT INTO t1_tc_41_conv_0016_cp (target) VALUES (0.01);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0016_cp MODIFY target DECIMAL(12,6), ALGORITHM=COPY;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0016_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0016_cp (target) VALUES (1234.56);
INSERT INTO t2_tc_41_conv_0016_cp (target) VALUES (0.01);
SELECT 'TC-41-CONV-0016-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0016_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0016_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0016_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0016_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0016_cp a JOIN t2_tc_41_conv_0016_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0016-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0017-DF
-- Conversion probe: DEC-D-MAX
-- Type: DECIMAL(65,0) -> DECIMAL(65,30), Algorithm: default, Expected: MEASURE
-- Probe note: M 不变、D 从 0 到最大：整数位容量从 65 缩到 35
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=91a5052c4436 conv_probe=DEC-D-MAX conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0017_df, t2_tc_41_conv_0017_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0017_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0017_df (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t1_tc_41_conv_0017_df (target) VALUES (0);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0017_df MODIFY target DECIMAL(65,30);
-- Oracle table: DECIMAL(65,0)
CREATE TABLE t2_tc_41_conv_0017_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0017_df (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t2_tc_41_conv_0017_df (target) VALUES (0);
SELECT 'TC-41-CONV-0017-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0017_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0017_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0017_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0017_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0017_df a JOIN t2_tc_41_conv_0017_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0017-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0018-IT
-- Conversion probe: DEC-D-MAX
-- Type: DECIMAL(65,0) -> DECIMAL(65,30), Algorithm: instant, Expected: MEASURE
-- Probe note: M 不变、D 从 0 到最大：整数位容量从 65 缩到 35
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e6810d63caa0 conv_probe=DEC-D-MAX conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0018_it, t2_tc_41_conv_0018_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0018_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0018_it (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t1_tc_41_conv_0018_it (target) VALUES (0);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0018_it MODIFY target DECIMAL(65,30), ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(65,0)
CREATE TABLE t2_tc_41_conv_0018_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0018_it (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t2_tc_41_conv_0018_it (target) VALUES (0);
SELECT 'TC-41-CONV-0018-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0018_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0018_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0018_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0018_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0018_it a JOIN t2_tc_41_conv_0018_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0018-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0019-IP
-- Conversion probe: DEC-D-MAX
-- Type: DECIMAL(65,0) -> DECIMAL(65,30), Algorithm: inplace, Expected: MEASURE
-- Probe note: M 不变、D 从 0 到最大：整数位容量从 65 缩到 35
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b032b2699a1f conv_probe=DEC-D-MAX conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0019_ip, t2_tc_41_conv_0019_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0019_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0019_ip (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t1_tc_41_conv_0019_ip (target) VALUES (0);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0019_ip MODIFY target DECIMAL(65,30), ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(65,0)
CREATE TABLE t2_tc_41_conv_0019_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0019_ip (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t2_tc_41_conv_0019_ip (target) VALUES (0);
SELECT 'TC-41-CONV-0019-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0019_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0019_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0019_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0019_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0019_ip a JOIN t2_tc_41_conv_0019_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0019-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0020-CP
-- Conversion probe: DEC-D-MAX
-- Type: DECIMAL(65,0) -> DECIMAL(65,30), Algorithm: copy, Expected: MEASURE
-- Probe note: M 不变、D 从 0 到最大：整数位容量从 65 缩到 35
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b34ad9dd0b03 conv_probe=DEC-D-MAX conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0020_cp, t2_tc_41_conv_0020_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0020_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0020_cp (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t1_tc_41_conv_0020_cp (target) VALUES (0);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0020_cp MODIFY target DECIMAL(65,30), ALGORITHM=COPY;
-- Oracle table: DECIMAL(65,0)
CREATE TABLE t2_tc_41_conv_0020_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(65,0),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0020_cp (target) VALUES (12345678901234567890123456789012345);
INSERT INTO t2_tc_41_conv_0020_cp (target) VALUES (0);
SELECT 'TC-41-CONV-0020-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0020_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0020_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0020_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0020_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0020_cp a JOIN t2_tc_41_conv_0020_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0020-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0021-DF
-- Conversion probe: SIGN-S2U
-- Type: INT -> INT UNSIGNED, Algorithm: default, Expected: MEASURE
-- Probe note: 有符号 -> 无符号（数据里没有负数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=97a219593db2 conv_probe=SIGN-S2U conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0021_df, t2_tc_41_conv_0021_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0021_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0021_df (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0021_df (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0021_df (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0021_df MODIFY target INT UNSIGNED;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0021_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0021_df (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0021_df (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0021_df (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0021-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0021_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0021_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0021_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0021_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0021_df a JOIN t2_tc_41_conv_0021_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0021-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0022-IT
-- Conversion probe: SIGN-S2U
-- Type: INT -> INT UNSIGNED, Algorithm: instant, Expected: MEASURE
-- Probe note: 有符号 -> 无符号（数据里没有负数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a40fd4ffd2f4 conv_probe=SIGN-S2U conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0022_it, t2_tc_41_conv_0022_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0022_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0022_it (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0022_it (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0022_it (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0022_it MODIFY target INT UNSIGNED, ALGORITHM=INSTANT;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0022_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0022_it (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0022_it (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0022_it (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0022-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0022_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0022_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0022_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0022_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0022_it a JOIN t2_tc_41_conv_0022_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0022-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0023-IP
-- Conversion probe: SIGN-S2U
-- Type: INT -> INT UNSIGNED, Algorithm: inplace, Expected: MEASURE
-- Probe note: 有符号 -> 无符号（数据里没有负数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f2ea89d3e404 conv_probe=SIGN-S2U conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0023_ip, t2_tc_41_conv_0023_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0023_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0023_ip (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0023_ip (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0023_ip (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0023_ip MODIFY target INT UNSIGNED, ALGORITHM=INPLACE;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0023_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0023_ip (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0023_ip (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0023_ip (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0023-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0023_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0023_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0023_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0023_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0023_ip a JOIN t2_tc_41_conv_0023_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0023-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0024-CP
-- Conversion probe: SIGN-S2U
-- Type: INT -> INT UNSIGNED, Algorithm: copy, Expected: MEASURE
-- Probe note: 有符号 -> 无符号（数据里没有负数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=654d1f181d24 conv_probe=SIGN-S2U conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0024_cp, t2_tc_41_conv_0024_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0024_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0024_cp (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0024_cp (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0024_cp (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0024_cp MODIFY target INT UNSIGNED, ALGORITHM=COPY;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0024_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0024_cp (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0024_cp (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0024_cp (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0024-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0024_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0024_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0024_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0024_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0024_cp a JOIN t2_tc_41_conv_0024_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0024-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0025-DF
-- Conversion probe: SIGN-S2U-NEG
-- Type: INT -> INT UNSIGNED, Algorithm: default, Expected: MEASURE
-- Probe note: 有符号 -> 无符号且**含负数**：strict 下必须拒绝
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=90df7a63ce67 conv_probe=SIGN-S2U-NEG conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0025_df, t2_tc_41_conv_0025_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0025_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0025_df (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0025_df (target) VALUES (-2147483648);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0025_df MODIFY target INT UNSIGNED;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0025_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0025_df (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0025_df (target) VALUES (-2147483648);
SELECT 'TC-41-CONV-0025-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0025_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0025_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0025_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0025_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0025_df a JOIN t2_tc_41_conv_0025_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0025-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0026-IT
-- Conversion probe: SIGN-S2U-NEG
-- Type: INT -> INT UNSIGNED, Algorithm: instant, Expected: MEASURE
-- Probe note: 有符号 -> 无符号且**含负数**：strict 下必须拒绝
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=606985b31042 conv_probe=SIGN-S2U-NEG conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0026_it, t2_tc_41_conv_0026_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0026_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0026_it (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0026_it (target) VALUES (-2147483648);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0026_it MODIFY target INT UNSIGNED, ALGORITHM=INSTANT;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0026_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0026_it (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0026_it (target) VALUES (-2147483648);
SELECT 'TC-41-CONV-0026-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0026_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0026_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0026_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0026_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0026_it a JOIN t2_tc_41_conv_0026_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0026-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0027-IP
-- Conversion probe: SIGN-S2U-NEG
-- Type: INT -> INT UNSIGNED, Algorithm: inplace, Expected: MEASURE
-- Probe note: 有符号 -> 无符号且**含负数**：strict 下必须拒绝
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d45eff54e85c conv_probe=SIGN-S2U-NEG conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0027_ip, t2_tc_41_conv_0027_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0027_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0027_ip (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0027_ip (target) VALUES (-2147483648);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0027_ip MODIFY target INT UNSIGNED, ALGORITHM=INPLACE;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0027_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0027_ip (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0027_ip (target) VALUES (-2147483648);
SELECT 'TC-41-CONV-0027-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0027_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0027_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0027_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0027_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0027_ip a JOIN t2_tc_41_conv_0027_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0027-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0028-CP
-- Conversion probe: SIGN-S2U-NEG
-- Type: INT -> INT UNSIGNED, Algorithm: copy, Expected: MEASURE
-- Probe note: 有符号 -> 无符号且**含负数**：strict 下必须拒绝
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d111fac36e28 conv_probe=SIGN-S2U-NEG conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0028_cp, t2_tc_41_conv_0028_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0028_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0028_cp (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0028_cp (target) VALUES (-2147483648);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0028_cp MODIFY target INT UNSIGNED, ALGORITHM=COPY;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0028_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0028_cp (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0028_cp (target) VALUES (-2147483648);
SELECT 'TC-41-CONV-0028-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0028_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0028_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0028_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0028_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0028_cp a JOIN t2_tc_41_conv_0028_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0028-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0029-DF
-- Conversion probe: SIGN-U2S
-- Type: INT UNSIGNED -> BIGINT, Algorithm: default, Expected: MEASURE
-- Probe note: 无符号 -> 更宽的有符号（值域可容纳）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=82978fecfa7f conv_probe=SIGN-U2S conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0029_df, t2_tc_41_conv_0029_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0029_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0029_df (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0029_df (target) VALUES (4294967295);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0029_df MODIFY target BIGINT;
-- Oracle table: INT UNSIGNED
CREATE TABLE t2_tc_41_conv_0029_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0029_df (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0029_df (target) VALUES (4294967295);
SELECT 'TC-41-CONV-0029-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0029_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0029_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0029_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0029_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0029_df a JOIN t2_tc_41_conv_0029_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0029-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0030-IT
-- Conversion probe: SIGN-U2S
-- Type: INT UNSIGNED -> BIGINT, Algorithm: instant, Expected: MEASURE
-- Probe note: 无符号 -> 更宽的有符号（值域可容纳）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=4ec929d04c93 conv_probe=SIGN-U2S conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0030_it, t2_tc_41_conv_0030_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0030_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0030_it (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0030_it (target) VALUES (4294967295);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0030_it MODIFY target BIGINT, ALGORITHM=INSTANT;
-- Oracle table: INT UNSIGNED
CREATE TABLE t2_tc_41_conv_0030_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0030_it (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0030_it (target) VALUES (4294967295);
SELECT 'TC-41-CONV-0030-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0030_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0030_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0030_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0030_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0030_it a JOIN t2_tc_41_conv_0030_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0030-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0031-IP
-- Conversion probe: SIGN-U2S
-- Type: INT UNSIGNED -> BIGINT, Algorithm: inplace, Expected: MEASURE
-- Probe note: 无符号 -> 更宽的有符号（值域可容纳）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=9d2432b20f55 conv_probe=SIGN-U2S conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0031_ip, t2_tc_41_conv_0031_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0031_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0031_ip (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0031_ip (target) VALUES (4294967295);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0031_ip MODIFY target BIGINT, ALGORITHM=INPLACE;
-- Oracle table: INT UNSIGNED
CREATE TABLE t2_tc_41_conv_0031_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0031_ip (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0031_ip (target) VALUES (4294967295);
SELECT 'TC-41-CONV-0031-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0031_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0031_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0031_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0031_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0031_ip a JOIN t2_tc_41_conv_0031_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0031-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0032-CP
-- Conversion probe: SIGN-U2S
-- Type: INT UNSIGNED -> BIGINT, Algorithm: copy, Expected: MEASURE
-- Probe note: 无符号 -> 更宽的有符号（值域可容纳）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d7be87ff420a conv_probe=SIGN-U2S conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0032_cp, t2_tc_41_conv_0032_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0032_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0032_cp (target) VALUES (0);
INSERT INTO t1_tc_41_conv_0032_cp (target) VALUES (4294967295);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0032_cp MODIFY target BIGINT, ALGORITHM=COPY;
-- Oracle table: INT UNSIGNED
CREATE TABLE t2_tc_41_conv_0032_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0032_cp (target) VALUES (0);
INSERT INTO t2_tc_41_conv_0032_cp (target) VALUES (4294967295);
SELECT 'TC-41-CONV-0032-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0032_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0032_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0032_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0032_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0032_cp a JOIN t2_tc_41_conv_0032_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0032-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0033-DF
-- Conversion probe: SIGN-U2S-OVER
-- Type: BIGINT UNSIGNED -> BIGINT, Algorithm: default, Expected: MEASURE
-- Probe note: 无符号最大值 -> 有符号：必然溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=193253ec4692 conv_probe=SIGN-U2S-OVER conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0033_df, t2_tc_41_conv_0033_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0033_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0033_df (target) VALUES (18446744073709551615);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0033_df MODIFY target BIGINT;
-- Oracle table: BIGINT UNSIGNED
CREATE TABLE t2_tc_41_conv_0033_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0033_df (target) VALUES (18446744073709551615);
SELECT 'TC-41-CONV-0033-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0033_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0033_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0033_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0033_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0033_df a JOIN t2_tc_41_conv_0033_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0033-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0034-IT
-- Conversion probe: SIGN-U2S-OVER
-- Type: BIGINT UNSIGNED -> BIGINT, Algorithm: instant, Expected: MEASURE
-- Probe note: 无符号最大值 -> 有符号：必然溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=c5de67c547e0 conv_probe=SIGN-U2S-OVER conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0034_it, t2_tc_41_conv_0034_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0034_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0034_it (target) VALUES (18446744073709551615);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0034_it MODIFY target BIGINT, ALGORITHM=INSTANT;
-- Oracle table: BIGINT UNSIGNED
CREATE TABLE t2_tc_41_conv_0034_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0034_it (target) VALUES (18446744073709551615);
SELECT 'TC-41-CONV-0034-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0034_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0034_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0034_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0034_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0034_it a JOIN t2_tc_41_conv_0034_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0034-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0035-IP
-- Conversion probe: SIGN-U2S-OVER
-- Type: BIGINT UNSIGNED -> BIGINT, Algorithm: inplace, Expected: MEASURE
-- Probe note: 无符号最大值 -> 有符号：必然溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=00c0c5ce4c72 conv_probe=SIGN-U2S-OVER conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0035_ip, t2_tc_41_conv_0035_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0035_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0035_ip (target) VALUES (18446744073709551615);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0035_ip MODIFY target BIGINT, ALGORITHM=INPLACE;
-- Oracle table: BIGINT UNSIGNED
CREATE TABLE t2_tc_41_conv_0035_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0035_ip (target) VALUES (18446744073709551615);
SELECT 'TC-41-CONV-0035-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0035_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0035_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0035_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0035_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0035_ip a JOIN t2_tc_41_conv_0035_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0035-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0036-CP
-- Conversion probe: SIGN-U2S-OVER
-- Type: BIGINT UNSIGNED -> BIGINT, Algorithm: copy, Expected: MEASURE
-- Probe note: 无符号最大值 -> 有符号：必然溢出
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e57ed6bb9980 conv_probe=SIGN-U2S-OVER conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0036_cp, t2_tc_41_conv_0036_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0036_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0036_cp (target) VALUES (18446744073709551615);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0036_cp MODIFY target BIGINT, ALGORITHM=COPY;
-- Oracle table: BIGINT UNSIGNED
CREATE TABLE t2_tc_41_conv_0036_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0036_cp (target) VALUES (18446744073709551615);
SELECT 'TC-41-CONV-0036-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0036_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0036_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0036_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0036_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0036_cp a JOIN t2_tc_41_conv_0036_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0036-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0037-DF
-- Conversion probe: NARROW-BIG2INT
-- Type: BIGINT -> INT, Algorithm: default, Expected: MEASURE
-- Probe note: 整数缩窄，数据在新值域内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=797fa62b02c5 conv_probe=NARROW-BIG2INT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0037_df, t2_tc_41_conv_0037_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0037_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0037_df (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0037_df (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0037_df MODIFY target INT;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0037_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0037_df (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0037_df (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0037-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0037_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0037_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0037_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0037_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0037_df a JOIN t2_tc_41_conv_0037_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0037-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0038-IT
-- Conversion probe: NARROW-BIG2INT
-- Type: BIGINT -> INT, Algorithm: instant, Expected: MEASURE
-- Probe note: 整数缩窄，数据在新值域内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=99dd33a2fe56 conv_probe=NARROW-BIG2INT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0038_it, t2_tc_41_conv_0038_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0038_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0038_it (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0038_it (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0038_it MODIFY target INT, ALGORITHM=INSTANT;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0038_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0038_it (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0038_it (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0038-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0038_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0038_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0038_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0038_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0038_it a JOIN t2_tc_41_conv_0038_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0038-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0039-IP
-- Conversion probe: NARROW-BIG2INT
-- Type: BIGINT -> INT, Algorithm: inplace, Expected: MEASURE
-- Probe note: 整数缩窄，数据在新值域内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=0fe73f8a2a94 conv_probe=NARROW-BIG2INT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0039_ip, t2_tc_41_conv_0039_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0039_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0039_ip (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0039_ip (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0039_ip MODIFY target INT, ALGORITHM=INPLACE;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0039_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0039_ip (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0039_ip (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0039-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0039_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0039_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0039_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0039_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0039_ip a JOIN t2_tc_41_conv_0039_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0039-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0040-CP
-- Conversion probe: NARROW-BIG2INT
-- Type: BIGINT -> INT, Algorithm: copy, Expected: MEASURE
-- Probe note: 整数缩窄，数据在新值域内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1427f12ec6b7 conv_probe=NARROW-BIG2INT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0040_cp, t2_tc_41_conv_0040_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0040_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0040_cp (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0040_cp (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0040_cp MODIFY target INT, ALGORITHM=COPY;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0040_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0040_cp (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0040_cp (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0040-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0040_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0040_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0040_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0040_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0040_cp a JOIN t2_tc_41_conv_0040_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0040-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0041-DF
-- Conversion probe: NARROW-BIG2INT-OVER
-- Type: BIGINT -> INT, Algorithm: default, Expected: MEASURE
-- Probe note: 整数缩窄，数据**超出**新值域
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=733aa6a0da86 conv_probe=NARROW-BIG2INT-OVER conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0041_df, t2_tc_41_conv_0041_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0041_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0041_df (target) VALUES (2147483648);
INSERT INTO t1_tc_41_conv_0041_df (target) VALUES (9223372036854775807);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0041_df MODIFY target INT;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0041_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0041_df (target) VALUES (2147483648);
INSERT INTO t2_tc_41_conv_0041_df (target) VALUES (9223372036854775807);
SELECT 'TC-41-CONV-0041-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0041_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0041_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0041_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0041_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0041_df a JOIN t2_tc_41_conv_0041_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0041-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0042-IT
-- Conversion probe: NARROW-BIG2INT-OVER
-- Type: BIGINT -> INT, Algorithm: instant, Expected: MEASURE
-- Probe note: 整数缩窄，数据**超出**新值域
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=c0598453a3a6 conv_probe=NARROW-BIG2INT-OVER conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0042_it, t2_tc_41_conv_0042_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0042_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0042_it (target) VALUES (2147483648);
INSERT INTO t1_tc_41_conv_0042_it (target) VALUES (9223372036854775807);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0042_it MODIFY target INT, ALGORITHM=INSTANT;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0042_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0042_it (target) VALUES (2147483648);
INSERT INTO t2_tc_41_conv_0042_it (target) VALUES (9223372036854775807);
SELECT 'TC-41-CONV-0042-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0042_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0042_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0042_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0042_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0042_it a JOIN t2_tc_41_conv_0042_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0042-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0043-IP
-- Conversion probe: NARROW-BIG2INT-OVER
-- Type: BIGINT -> INT, Algorithm: inplace, Expected: MEASURE
-- Probe note: 整数缩窄，数据**超出**新值域
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=485e4d5b250f conv_probe=NARROW-BIG2INT-OVER conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0043_ip, t2_tc_41_conv_0043_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0043_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0043_ip (target) VALUES (2147483648);
INSERT INTO t1_tc_41_conv_0043_ip (target) VALUES (9223372036854775807);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0043_ip MODIFY target INT, ALGORITHM=INPLACE;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0043_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0043_ip (target) VALUES (2147483648);
INSERT INTO t2_tc_41_conv_0043_ip (target) VALUES (9223372036854775807);
SELECT 'TC-41-CONV-0043-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0043_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0043_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0043_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0043_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0043_ip a JOIN t2_tc_41_conv_0043_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0043-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0044-CP
-- Conversion probe: NARROW-BIG2INT-OVER
-- Type: BIGINT -> INT, Algorithm: copy, Expected: MEASURE
-- Probe note: 整数缩窄，数据**超出**新值域
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a0f83f17c843 conv_probe=NARROW-BIG2INT-OVER conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0044_cp, t2_tc_41_conv_0044_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0044_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0044_cp (target) VALUES (2147483648);
INSERT INTO t1_tc_41_conv_0044_cp (target) VALUES (9223372036854775807);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0044_cp MODIFY target INT, ALGORITHM=COPY;
-- Oracle table: BIGINT
CREATE TABLE t2_tc_41_conv_0044_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0044_cp (target) VALUES (2147483648);
INSERT INTO t2_tc_41_conv_0044_cp (target) VALUES (9223372036854775807);
SELECT 'TC-41-CONV-0044-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0044_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0044_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0044_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0044_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0044_cp a JOIN t2_tc_41_conv_0044_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0044-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0045-DF
-- Conversion probe: NARROW-VC
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(10) CHARACTER SET latin1, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据在新长度内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=049c20280b62 conv_probe=NARROW-VC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0045_df, t2_tc_41_conv_0045_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0045_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0045_df (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0045_df (target) VALUES ('0123456789');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0045_df MODIFY target VARCHAR(10) CHARACTER SET latin1;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0045_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0045_df (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0045_df (target) VALUES ('0123456789');
SELECT 'TC-41-CONV-0045-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0045_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0045_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0045_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0045_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0045_df a JOIN t2_tc_41_conv_0045_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0045-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0046-IT
-- Conversion probe: NARROW-VC
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(10) CHARACTER SET latin1, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据在新长度内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=6876d23595a2 conv_probe=NARROW-VC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0046_it, t2_tc_41_conv_0046_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0046_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0046_it (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0046_it (target) VALUES ('0123456789');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0046_it MODIFY target VARCHAR(10) CHARACTER SET latin1, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0046_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0046_it (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0046_it (target) VALUES ('0123456789');
SELECT 'TC-41-CONV-0046-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0046_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0046_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0046_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0046_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0046_it a JOIN t2_tc_41_conv_0046_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0046-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0047-IP
-- Conversion probe: NARROW-VC
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(10) CHARACTER SET latin1, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据在新长度内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=49bf5bc2f1cd conv_probe=NARROW-VC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0047_ip, t2_tc_41_conv_0047_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0047_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0047_ip (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0047_ip (target) VALUES ('0123456789');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0047_ip MODIFY target VARCHAR(10) CHARACTER SET latin1, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0047_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0047_ip (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0047_ip (target) VALUES ('0123456789');
SELECT 'TC-41-CONV-0047-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0047_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0047_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0047_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0047_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0047_ip a JOIN t2_tc_41_conv_0047_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0047-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0048-CP
-- Conversion probe: NARROW-VC
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(10) CHARACTER SET latin1, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据在新长度内
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=56a4ae3070a1 conv_probe=NARROW-VC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0048_cp, t2_tc_41_conv_0048_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0048_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0048_cp (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0048_cp (target) VALUES ('0123456789');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0048_cp MODIFY target VARCHAR(10) CHARACTER SET latin1, ALGORITHM=COPY;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0048_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0048_cp (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0048_cp (target) VALUES ('0123456789');
SELECT 'TC-41-CONV-0048-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0048_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0048_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0048_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0048_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0048_cp a JOIN t2_tc_41_conv_0048_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0048-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0049-DF
-- Conversion probe: NARROW-VC-OVER
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(3) CHARACTER SET latin1, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据**超出**新长度
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e3401bf81f9c conv_probe=NARROW-VC-OVER conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0049_df, t2_tc_41_conv_0049_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0049_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0049_df (target) VALUES ('abcdef');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0049_df MODIFY target VARCHAR(3) CHARACTER SET latin1;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0049_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0049_df (target) VALUES ('abcdef');
SELECT 'TC-41-CONV-0049-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0049_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0049_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0049_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0049_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0049_df a JOIN t2_tc_41_conv_0049_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0049-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0050-IT
-- Conversion probe: NARROW-VC-OVER
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(3) CHARACTER SET latin1, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据**超出**新长度
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=8f42504040db conv_probe=NARROW-VC-OVER conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0050_it, t2_tc_41_conv_0050_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0050_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0050_it (target) VALUES ('abcdef');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0050_it MODIFY target VARCHAR(3) CHARACTER SET latin1, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0050_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0050_it (target) VALUES ('abcdef');
SELECT 'TC-41-CONV-0050-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0050_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0050_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0050_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0050_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0050_it a JOIN t2_tc_41_conv_0050_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0050-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0051-IP
-- Conversion probe: NARROW-VC-OVER
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(3) CHARACTER SET latin1, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据**超出**新长度
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=5911afa551a3 conv_probe=NARROW-VC-OVER conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0051_ip, t2_tc_41_conv_0051_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0051_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0051_ip (target) VALUES ('abcdef');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0051_ip MODIFY target VARCHAR(3) CHARACTER SET latin1, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0051_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0051_ip (target) VALUES ('abcdef');
SELECT 'TC-41-CONV-0051-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0051_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0051_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0051_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0051_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0051_ip a JOIN t2_tc_41_conv_0051_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0051-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0052-CP
-- Conversion probe: NARROW-VC-OVER
-- Type: VARCHAR(255) CHARACTER SET latin1 -> VARCHAR(3) CHARACTER SET latin1, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR 缩窄，数据**超出**新长度
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=41cd050afcc2 conv_probe=NARROW-VC-OVER conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0052_cp, t2_tc_41_conv_0052_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0052_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0052_cp (target) VALUES ('abcdef');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0052_cp MODIFY target VARCHAR(3) CHARACTER SET latin1, ALGORITHM=COPY;
-- Oracle table: VARCHAR(255) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0052_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(255) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0052_cp (target) VALUES ('abcdef');
SELECT 'TC-41-CONV-0052-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0052_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0052_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0052_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0052_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0052_cp a JOIN t2_tc_41_conv_0052_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0052-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0053-DF
-- Conversion probe: NARROW-CHAR
-- Type: CHAR(255) CHARACTER SET utf8mb4 -> CHAR(254) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: CHAR 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=95cf9d3bce40 conv_probe=NARROW-CHAR conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0053_df, t2_tc_41_conv_0053_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0053_df (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0053_df (target) VALUES ('a');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0053_df MODIFY target CHAR(254) CHARACTER SET utf8mb4;
-- Oracle table: CHAR(255) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0053_df (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0053_df (target) VALUES ('a');
SELECT 'TC-41-CONV-0053-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0053_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0053_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0053_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0053_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0053_df a JOIN t2_tc_41_conv_0053_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0053-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0054-IT
-- Conversion probe: NARROW-CHAR
-- Type: CHAR(255) CHARACTER SET utf8mb4 -> CHAR(254) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: CHAR 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=5556ad6f5c1e conv_probe=NARROW-CHAR conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0054_it, t2_tc_41_conv_0054_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0054_it (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0054_it (target) VALUES ('a');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0054_it MODIFY target CHAR(254) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: CHAR(255) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0054_it (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0054_it (target) VALUES ('a');
SELECT 'TC-41-CONV-0054-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0054_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0054_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0054_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0054_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0054_it a JOIN t2_tc_41_conv_0054_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0054-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0055-IP
-- Conversion probe: NARROW-CHAR
-- Type: CHAR(255) CHARACTER SET utf8mb4 -> CHAR(254) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: CHAR 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2bfa2a69e5ce conv_probe=NARROW-CHAR conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0055_ip, t2_tc_41_conv_0055_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0055_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0055_ip (target) VALUES ('a');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0055_ip MODIFY target CHAR(254) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: CHAR(255) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0055_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0055_ip (target) VALUES ('a');
SELECT 'TC-41-CONV-0055-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0055_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0055_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0055_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0055_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0055_ip a JOIN t2_tc_41_conv_0055_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0055-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0056-CP
-- Conversion probe: NARROW-CHAR
-- Type: CHAR(255) CHARACTER SET utf8mb4 -> CHAR(254) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: CHAR 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7c8b29a9f884 conv_probe=NARROW-CHAR conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0056_cp, t2_tc_41_conv_0056_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0056_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0056_cp (target) VALUES ('a');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0056_cp MODIFY target CHAR(254) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: CHAR(255) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0056_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(255) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0056_cp (target) VALUES ('a');
SELECT 'TC-41-CONV-0056-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0056_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0056_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0056_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0056_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0056_cp a JOIN t2_tc_41_conv_0056_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0056-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0057-DF
-- Conversion probe: NARROW-BIN
-- Type: BINARY(20) -> BINARY(10), Algorithm: default, Expected: MEASURE
-- Probe note: BINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1f8614cf833b conv_probe=NARROW-BIN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0057_df, t2_tc_41_conv_0057_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0057_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0057_df (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0057_df MODIFY target BINARY(10);
-- Oracle table: BINARY(20)
CREATE TABLE t2_tc_41_conv_0057_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0057_df (target) VALUES (X'00');
SELECT 'TC-41-CONV-0057-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0057_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0057_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0057_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0057_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0057_df a JOIN t2_tc_41_conv_0057_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0057-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0058-IT
-- Conversion probe: NARROW-BIN
-- Type: BINARY(20) -> BINARY(10), Algorithm: instant, Expected: MEASURE
-- Probe note: BINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=288c7c033571 conv_probe=NARROW-BIN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0058_it, t2_tc_41_conv_0058_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0058_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0058_it (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0058_it MODIFY target BINARY(10), ALGORITHM=INSTANT;
-- Oracle table: BINARY(20)
CREATE TABLE t2_tc_41_conv_0058_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0058_it (target) VALUES (X'00');
SELECT 'TC-41-CONV-0058-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0058_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0058_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0058_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0058_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0058_it a JOIN t2_tc_41_conv_0058_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0058-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0059-IP
-- Conversion probe: NARROW-BIN
-- Type: BINARY(20) -> BINARY(10), Algorithm: inplace, Expected: MEASURE
-- Probe note: BINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2b0a0f07562f conv_probe=NARROW-BIN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0059_ip, t2_tc_41_conv_0059_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0059_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0059_ip (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0059_ip MODIFY target BINARY(10), ALGORITHM=INPLACE;
-- Oracle table: BINARY(20)
CREATE TABLE t2_tc_41_conv_0059_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0059_ip (target) VALUES (X'00');
SELECT 'TC-41-CONV-0059-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0059_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0059_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0059_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0059_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0059_ip a JOIN t2_tc_41_conv_0059_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0059-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0060-CP
-- Conversion probe: NARROW-BIN
-- Type: BINARY(20) -> BINARY(10), Algorithm: copy, Expected: MEASURE
-- Probe note: BINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=cb313cfd93cd conv_probe=NARROW-BIN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0060_cp, t2_tc_41_conv_0060_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0060_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0060_cp (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0060_cp MODIFY target BINARY(10), ALGORITHM=COPY;
-- Oracle table: BINARY(20)
CREATE TABLE t2_tc_41_conv_0060_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(20),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0060_cp (target) VALUES (X'00');
SELECT 'TC-41-CONV-0060-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0060_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0060_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0060_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0060_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0060_cp a JOIN t2_tc_41_conv_0060_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0060-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0061-DF
-- Conversion probe: NARROW-VBIN
-- Type: VARBINARY(40) -> VARBINARY(20), Algorithm: default, Expected: MEASURE
-- Probe note: VARBINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=63d4a736a9fc conv_probe=NARROW-VBIN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0061_df, t2_tc_41_conv_0061_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0061_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0061_df (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0061_df MODIFY target VARBINARY(20);
-- Oracle table: VARBINARY(40)
CREATE TABLE t2_tc_41_conv_0061_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0061_df (target) VALUES (X'00');
SELECT 'TC-41-CONV-0061-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0061_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0061_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0061_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0061_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0061_df a JOIN t2_tc_41_conv_0061_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0061-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0062-IT
-- Conversion probe: NARROW-VBIN
-- Type: VARBINARY(40) -> VARBINARY(20), Algorithm: instant, Expected: MEASURE
-- Probe note: VARBINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=fca5cb08b979 conv_probe=NARROW-VBIN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0062_it, t2_tc_41_conv_0062_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0062_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0062_it (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0062_it MODIFY target VARBINARY(20), ALGORITHM=INSTANT;
-- Oracle table: VARBINARY(40)
CREATE TABLE t2_tc_41_conv_0062_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0062_it (target) VALUES (X'00');
SELECT 'TC-41-CONV-0062-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0062_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0062_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0062_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0062_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0062_it a JOIN t2_tc_41_conv_0062_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0062-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0063-IP
-- Conversion probe: NARROW-VBIN
-- Type: VARBINARY(40) -> VARBINARY(20), Algorithm: inplace, Expected: MEASURE
-- Probe note: VARBINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b16b6aac87f1 conv_probe=NARROW-VBIN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0063_ip, t2_tc_41_conv_0063_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0063_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0063_ip (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0063_ip MODIFY target VARBINARY(20), ALGORITHM=INPLACE;
-- Oracle table: VARBINARY(40)
CREATE TABLE t2_tc_41_conv_0063_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0063_ip (target) VALUES (X'00');
SELECT 'TC-41-CONV-0063-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0063_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0063_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0063_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0063_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0063_ip a JOIN t2_tc_41_conv_0063_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0063-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0064-CP
-- Conversion probe: NARROW-VBIN
-- Type: VARBINARY(40) -> VARBINARY(20), Algorithm: copy, Expected: MEASURE
-- Probe note: VARBINARY 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=9d89f4ecd655 conv_probe=NARROW-VBIN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0064_cp, t2_tc_41_conv_0064_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0064_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0064_cp (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0064_cp MODIFY target VARBINARY(20), ALGORITHM=COPY;
-- Oracle table: VARBINARY(40)
CREATE TABLE t2_tc_41_conv_0064_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARBINARY(40),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0064_cp (target) VALUES (X'00');
SELECT 'TC-41-CONV-0064-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0064_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0064_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0064_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0064_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0064_cp a JOIN t2_tc_41_conv_0064_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0064-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0065-DF
-- Conversion probe: NARROW-BIT
-- Type: BIT(64) -> BIT(32), Algorithm: default, Expected: MEASURE
-- Probe note: BIT 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=94dd2d2ea94b conv_probe=NARROW-BIT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0065_df, t2_tc_41_conv_0065_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0065_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0065_df (target) VALUES (1);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0065_df MODIFY target BIT(32);
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_41_conv_0065_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0065_df (target) VALUES (1);
SELECT 'TC-41-CONV-0065-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0065_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0065_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0065_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0065_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0065_df a JOIN t2_tc_41_conv_0065_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0065-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0066-IT
-- Conversion probe: NARROW-BIT
-- Type: BIT(64) -> BIT(32), Algorithm: instant, Expected: MEASURE
-- Probe note: BIT 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1caea6a79bc0 conv_probe=NARROW-BIT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0066_it, t2_tc_41_conv_0066_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0066_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0066_it (target) VALUES (1);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0066_it MODIFY target BIT(32), ALGORITHM=INSTANT;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_41_conv_0066_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0066_it (target) VALUES (1);
SELECT 'TC-41-CONV-0066-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0066_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0066_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0066_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0066_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0066_it a JOIN t2_tc_41_conv_0066_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0066-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0067-IP
-- Conversion probe: NARROW-BIT
-- Type: BIT(64) -> BIT(32), Algorithm: inplace, Expected: MEASURE
-- Probe note: BIT 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=30f3b24a6898 conv_probe=NARROW-BIT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0067_ip, t2_tc_41_conv_0067_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0067_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0067_ip (target) VALUES (1);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0067_ip MODIFY target BIT(32), ALGORITHM=INPLACE;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_41_conv_0067_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0067_ip (target) VALUES (1);
SELECT 'TC-41-CONV-0067-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0067_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0067_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0067_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0067_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0067_ip a JOIN t2_tc_41_conv_0067_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0067-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0068-CP
-- Conversion probe: NARROW-BIT
-- Type: BIT(64) -> BIT(32), Algorithm: copy, Expected: MEASURE
-- Probe note: BIT 缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a0b32ab3a835 conv_probe=NARROW-BIT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0068_cp, t2_tc_41_conv_0068_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0068_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0068_cp (target) VALUES (1);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0068_cp MODIFY target BIT(32), ALGORITHM=COPY;
-- Oracle table: BIT(64)
CREATE TABLE t2_tc_41_conv_0068_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target BIT(64),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0068_cp (target) VALUES (1);
SELECT 'TC-41-CONV-0068-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0068_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0068_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0068_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0068_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0068_cp a JOIN t2_tc_41_conv_0068_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0068-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0069-DF
-- Conversion probe: NARROW-TEXT
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: TEXT 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=0bf2bdf1ec2e conv_probe=NARROW-TEXT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0069_df, t2_tc_41_conv_0069_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0069_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0069_df (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0069_df MODIFY target TEXT CHARACTER SET utf8mb4;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0069_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0069_df (target) VALUES ('abc');
SELECT 'TC-41-CONV-0069-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0069_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0069_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0069_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0069_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0069_df a JOIN t2_tc_41_conv_0069_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0069-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0070-IT
-- Conversion probe: NARROW-TEXT
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: TEXT 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d6343dad50f4 conv_probe=NARROW-TEXT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0070_it, t2_tc_41_conv_0070_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0070_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0070_it (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0070_it MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0070_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0070_it (target) VALUES ('abc');
SELECT 'TC-41-CONV-0070-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0070_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0070_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0070_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0070_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0070_it a JOIN t2_tc_41_conv_0070_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0070-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0071-IP
-- Conversion probe: NARROW-TEXT
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: TEXT 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2db38c7efb8b conv_probe=NARROW-TEXT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0071_ip, t2_tc_41_conv_0071_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0071_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0071_ip (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0071_ip MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0071_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0071_ip (target) VALUES ('abc');
SELECT 'TC-41-CONV-0071-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0071_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0071_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0071_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0071_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0071_ip a JOIN t2_tc_41_conv_0071_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0071-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0072-CP
-- Conversion probe: NARROW-TEXT
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: TEXT 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=bfd4a7674ceb conv_probe=NARROW-TEXT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0072_cp, t2_tc_41_conv_0072_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0072_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0072_cp (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0072_cp MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0072_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0072_cp (target) VALUES ('abc');
SELECT 'TC-41-CONV-0072-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0072_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0072_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0072_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0072_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0072_cp a JOIN t2_tc_41_conv_0072_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0072-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0073-DF
-- Conversion probe: NARROW-BLOB
-- Type: LONGBLOB -> BLOB, Algorithm: default, Expected: MEASURE
-- Probe note: BLOB 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=56a56589044e conv_probe=NARROW-BLOB conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0073_df, t2_tc_41_conv_0073_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0073_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0073_df (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0073_df MODIFY target BLOB;
-- Oracle table: LONGBLOB
CREATE TABLE t2_tc_41_conv_0073_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0073_df (target) VALUES (X'00');
SELECT 'TC-41-CONV-0073-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0073_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0073_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0073_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0073_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0073_df a JOIN t2_tc_41_conv_0073_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0073-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0074-IT
-- Conversion probe: NARROW-BLOB
-- Type: LONGBLOB -> BLOB, Algorithm: instant, Expected: MEASURE
-- Probe note: BLOB 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2f8d0f0f7279 conv_probe=NARROW-BLOB conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0074_it, t2_tc_41_conv_0074_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0074_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0074_it (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0074_it MODIFY target BLOB, ALGORITHM=INSTANT;
-- Oracle table: LONGBLOB
CREATE TABLE t2_tc_41_conv_0074_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0074_it (target) VALUES (X'00');
SELECT 'TC-41-CONV-0074-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0074_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0074_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0074_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0074_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0074_it a JOIN t2_tc_41_conv_0074_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0074-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0075-IP
-- Conversion probe: NARROW-BLOB
-- Type: LONGBLOB -> BLOB, Algorithm: inplace, Expected: MEASURE
-- Probe note: BLOB 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1f537b002271 conv_probe=NARROW-BLOB conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0075_ip, t2_tc_41_conv_0075_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0075_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0075_ip (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0075_ip MODIFY target BLOB, ALGORITHM=INPLACE;
-- Oracle table: LONGBLOB
CREATE TABLE t2_tc_41_conv_0075_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0075_ip (target) VALUES (X'00');
SELECT 'TC-41-CONV-0075-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0075_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0075_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0075_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0075_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0075_ip a JOIN t2_tc_41_conv_0075_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0075-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0076-CP
-- Conversion probe: NARROW-BLOB
-- Type: LONGBLOB -> BLOB, Algorithm: copy, Expected: MEASURE
-- Probe note: BLOB 族缩窄
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f53236f27a92 conv_probe=NARROW-BLOB conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0076_cp, t2_tc_41_conv_0076_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0076_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0076_cp (target) VALUES (X'00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0076_cp MODIFY target BLOB, ALGORITHM=COPY;
-- Oracle table: LONGBLOB
CREATE TABLE t2_tc_41_conv_0076_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGBLOB,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0076_cp (target) VALUES (X'00');
SELECT 'TC-41-CONV-0076-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0076_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0076_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0076_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0076_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0076_cp a JOIN t2_tc_41_conv_0076_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0076-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0077-DF
-- Conversion probe: CROSS-INT2DEC
-- Type: INT -> DECIMAL(10,0), Algorithm: default, Expected: MEASURE
-- Probe note: 整数 -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=823418a59edf conv_probe=CROSS-INT2DEC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0077_df, t2_tc_41_conv_0077_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0077_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0077_df (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0077_df (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0077_df (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0077_df MODIFY target DECIMAL(10,0);
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0077_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0077_df (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0077_df (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0077_df (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0077-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0077_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0077_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0077_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0077_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0077_df a JOIN t2_tc_41_conv_0077_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0077-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0078-IT
-- Conversion probe: CROSS-INT2DEC
-- Type: INT -> DECIMAL(10,0), Algorithm: instant, Expected: MEASURE
-- Probe note: 整数 -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=4e28ac056291 conv_probe=CROSS-INT2DEC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0078_it, t2_tc_41_conv_0078_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0078_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0078_it (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0078_it (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0078_it (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0078_it MODIFY target DECIMAL(10,0), ALGORITHM=INSTANT;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0078_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0078_it (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0078_it (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0078_it (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0078-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0078_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0078_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0078_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0078_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0078_it a JOIN t2_tc_41_conv_0078_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0078-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0079-IP
-- Conversion probe: CROSS-INT2DEC
-- Type: INT -> DECIMAL(10,0), Algorithm: inplace, Expected: MEASURE
-- Probe note: 整数 -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2335e5b1da72 conv_probe=CROSS-INT2DEC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0079_ip, t2_tc_41_conv_0079_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0079_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0079_ip (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0079_ip (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0079_ip (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0079_ip MODIFY target DECIMAL(10,0), ALGORITHM=INPLACE;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0079_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0079_ip (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0079_ip (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0079_ip (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0079-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0079_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0079_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0079_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0079_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0079_ip a JOIN t2_tc_41_conv_0079_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0079-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0080-CP
-- Conversion probe: CROSS-INT2DEC
-- Type: INT -> DECIMAL(10,0), Algorithm: copy, Expected: MEASURE
-- Probe note: 整数 -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7e1144cc7184 conv_probe=CROSS-INT2DEC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0080_cp, t2_tc_41_conv_0080_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0080_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0080_cp (target) VALUES (1);
INSERT INTO t1_tc_41_conv_0080_cp (target) VALUES (-1);
INSERT INTO t1_tc_41_conv_0080_cp (target) VALUES (2147483647);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0080_cp MODIFY target DECIMAL(10,0), ALGORITHM=COPY;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0080_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0080_cp (target) VALUES (1);
INSERT INTO t2_tc_41_conv_0080_cp (target) VALUES (-1);
INSERT INTO t2_tc_41_conv_0080_cp (target) VALUES (2147483647);
SELECT 'TC-41-CONV-0080-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0080_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0080_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0080_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0080_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0080_cp a JOIN t2_tc_41_conv_0080_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0080-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0081-DF
-- Conversion probe: CROSS-DEC2BIG
-- Type: DECIMAL(10,2) -> BIGINT, Algorithm: default, Expected: MEASURE
-- Probe note: DECIMAL -> 整数（含小数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=13fbb4755882 conv_probe=CROSS-DEC2BIG conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0081_df, t2_tc_41_conv_0081_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0081_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0081_df (target) VALUES (1.00);
INSERT INTO t1_tc_41_conv_0081_df (target) VALUES (-99.99);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0081_df MODIFY target BIGINT;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0081_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0081_df (target) VALUES (1.00);
INSERT INTO t2_tc_41_conv_0081_df (target) VALUES (-99.99);
SELECT 'TC-41-CONV-0081-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0081_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0081_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0081_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0081_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0081_df a JOIN t2_tc_41_conv_0081_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0081-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0082-IT
-- Conversion probe: CROSS-DEC2BIG
-- Type: DECIMAL(10,2) -> BIGINT, Algorithm: instant, Expected: MEASURE
-- Probe note: DECIMAL -> 整数（含小数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=14e63a99cbc2 conv_probe=CROSS-DEC2BIG conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0082_it, t2_tc_41_conv_0082_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0082_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0082_it (target) VALUES (1.00);
INSERT INTO t1_tc_41_conv_0082_it (target) VALUES (-99.99);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0082_it MODIFY target BIGINT, ALGORITHM=INSTANT;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0082_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0082_it (target) VALUES (1.00);
INSERT INTO t2_tc_41_conv_0082_it (target) VALUES (-99.99);
SELECT 'TC-41-CONV-0082-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0082_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0082_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0082_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0082_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0082_it a JOIN t2_tc_41_conv_0082_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0082-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0083-IP
-- Conversion probe: CROSS-DEC2BIG
-- Type: DECIMAL(10,2) -> BIGINT, Algorithm: inplace, Expected: MEASURE
-- Probe note: DECIMAL -> 整数（含小数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=dc1d49e5e809 conv_probe=CROSS-DEC2BIG conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0083_ip, t2_tc_41_conv_0083_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0083_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0083_ip (target) VALUES (1.00);
INSERT INTO t1_tc_41_conv_0083_ip (target) VALUES (-99.99);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0083_ip MODIFY target BIGINT, ALGORITHM=INPLACE;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0083_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0083_ip (target) VALUES (1.00);
INSERT INTO t2_tc_41_conv_0083_ip (target) VALUES (-99.99);
SELECT 'TC-41-CONV-0083-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0083_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0083_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0083_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0083_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0083_ip a JOIN t2_tc_41_conv_0083_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0083-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0084-CP
-- Conversion probe: CROSS-DEC2BIG
-- Type: DECIMAL(10,2) -> BIGINT, Algorithm: copy, Expected: MEASURE
-- Probe note: DECIMAL -> 整数（含小数）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f93acec07b7d conv_probe=CROSS-DEC2BIG conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0084_cp, t2_tc_41_conv_0084_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0084_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0084_cp (target) VALUES (1.00);
INSERT INTO t1_tc_41_conv_0084_cp (target) VALUES (-99.99);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0084_cp MODIFY target BIGINT, ALGORITHM=COPY;
-- Oracle table: DECIMAL(10,2)
CREATE TABLE t2_tc_41_conv_0084_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0084_cp (target) VALUES (1.00);
INSERT INTO t2_tc_41_conv_0084_cp (target) VALUES (-99.99);
SELECT 'TC-41-CONV-0084-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0084_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0084_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0084_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0084_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0084_cp a JOIN t2_tc_41_conv_0084_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0084-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0085-DF
-- Conversion probe: CROSS-VC2TEXT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR -> TEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3f249c0d8f50 conv_probe=CROSS-VC2TEXT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0085_df, t2_tc_41_conv_0085_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0085_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0085_df (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0085_df MODIFY target TEXT CHARACTER SET utf8mb4;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0085_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0085_df (target) VALUES ('abc');
SELECT 'TC-41-CONV-0085-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0085_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0085_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0085_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0085_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0085_df a JOIN t2_tc_41_conv_0085_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0085-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0086-IT
-- Conversion probe: CROSS-VC2TEXT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR -> TEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2362ed366962 conv_probe=CROSS-VC2TEXT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0086_it, t2_tc_41_conv_0086_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0086_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0086_it (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0086_it MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0086_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0086_it (target) VALUES ('abc');
SELECT 'TC-41-CONV-0086-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0086_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0086_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0086_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0086_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0086_it a JOIN t2_tc_41_conv_0086_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0086-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0087-IP
-- Conversion probe: CROSS-VC2TEXT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR -> TEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=9a568ec81792 conv_probe=CROSS-VC2TEXT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0087_ip, t2_tc_41_conv_0087_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0087_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0087_ip (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0087_ip MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0087_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0087_ip (target) VALUES ('abc');
SELECT 'TC-41-CONV-0087-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0087_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0087_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0087_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0087_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0087_ip a JOIN t2_tc_41_conv_0087_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0087-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0088-CP
-- Conversion probe: CROSS-VC2TEXT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> TEXT CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR -> TEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3b3c39b396d7 conv_probe=CROSS-VC2TEXT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0088_cp, t2_tc_41_conv_0088_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0088_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0088_cp (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0088_cp MODIFY target TEXT CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0088_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0088_cp (target) VALUES ('abc');
SELECT 'TC-41-CONV-0088-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0088_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0088_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0088_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0088_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0088_cp a JOIN t2_tc_41_conv_0088_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0088-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0089-DF
-- Conversion probe: CROSS-TEXT2VC
-- Type: TEXT CHARACTER SET utf8mb4 -> VARCHAR(100) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: TEXT -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=dbc593653b1b conv_probe=CROSS-TEXT2VC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0089_df, t2_tc_41_conv_0089_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0089_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0089_df (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0089_df MODIFY target VARCHAR(100) CHARACTER SET utf8mb4;
-- Oracle table: TEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0089_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0089_df (target) VALUES ('abc');
SELECT 'TC-41-CONV-0089-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0089_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0089_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0089_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0089_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0089_df a JOIN t2_tc_41_conv_0089_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0089-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0090-IT
-- Conversion probe: CROSS-TEXT2VC
-- Type: TEXT CHARACTER SET utf8mb4 -> VARCHAR(100) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: TEXT -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ce694583a398 conv_probe=CROSS-TEXT2VC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0090_it, t2_tc_41_conv_0090_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0090_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0090_it (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0090_it MODIFY target VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: TEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0090_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0090_it (target) VALUES ('abc');
SELECT 'TC-41-CONV-0090-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0090_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0090_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0090_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0090_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0090_it a JOIN t2_tc_41_conv_0090_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0090-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0091-IP
-- Conversion probe: CROSS-TEXT2VC
-- Type: TEXT CHARACTER SET utf8mb4 -> VARCHAR(100) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: TEXT -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=290635478893 conv_probe=CROSS-TEXT2VC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0091_ip, t2_tc_41_conv_0091_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0091_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0091_ip (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0091_ip MODIFY target VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: TEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0091_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0091_ip (target) VALUES ('abc');
SELECT 'TC-41-CONV-0091-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0091_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0091_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0091_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0091_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0091_ip a JOIN t2_tc_41_conv_0091_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0091-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0092-CP
-- Conversion probe: CROSS-TEXT2VC
-- Type: TEXT CHARACTER SET utf8mb4 -> VARCHAR(100) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: TEXT -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b9ca9838156b conv_probe=CROSS-TEXT2VC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0092_cp, t2_tc_41_conv_0092_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0092_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0092_cp (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0092_cp MODIFY target VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: TEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0092_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0092_cp (target) VALUES ('abc');
SELECT 'TC-41-CONV-0092-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0092_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0092_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0092_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0092_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0092_cp a JOIN t2_tc_41_conv_0092_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0092-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0093-DF
-- Conversion probe: CROSS-CHAR2VC
-- Type: CHAR(10) CHARACTER SET utf8mb4 -> VARCHAR(10) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: CHAR -> VARCHAR（尾空格语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=c80b7842a2a9 conv_probe=CROSS-CHAR2VC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0093_df, t2_tc_41_conv_0093_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0093_df (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0093_df (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0093_df MODIFY target VARCHAR(10) CHARACTER SET utf8mb4;
-- Oracle table: CHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0093_df (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0093_df (target) VALUES ('ab');
SELECT 'TC-41-CONV-0093-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0093_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0093_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0093_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0093_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0093_df a JOIN t2_tc_41_conv_0093_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0093-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0094-IT
-- Conversion probe: CROSS-CHAR2VC
-- Type: CHAR(10) CHARACTER SET utf8mb4 -> VARCHAR(10) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: CHAR -> VARCHAR（尾空格语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=5f562af0a493 conv_probe=CROSS-CHAR2VC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0094_it, t2_tc_41_conv_0094_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0094_it (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0094_it (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0094_it MODIFY target VARCHAR(10) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: CHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0094_it (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0094_it (target) VALUES ('ab');
SELECT 'TC-41-CONV-0094-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0094_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0094_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0094_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0094_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0094_it a JOIN t2_tc_41_conv_0094_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0094-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0095-IP
-- Conversion probe: CROSS-CHAR2VC
-- Type: CHAR(10) CHARACTER SET utf8mb4 -> VARCHAR(10) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: CHAR -> VARCHAR（尾空格语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=39126d10b188 conv_probe=CROSS-CHAR2VC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0095_ip, t2_tc_41_conv_0095_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0095_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0095_ip (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0095_ip MODIFY target VARCHAR(10) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: CHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0095_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0095_ip (target) VALUES ('ab');
SELECT 'TC-41-CONV-0095-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0095_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0095_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0095_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0095_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0095_ip a JOIN t2_tc_41_conv_0095_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0095-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0096-CP
-- Conversion probe: CROSS-CHAR2VC
-- Type: CHAR(10) CHARACTER SET utf8mb4 -> VARCHAR(10) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: CHAR -> VARCHAR（尾空格语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3d54a9f066de conv_probe=CROSS-CHAR2VC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0096_cp, t2_tc_41_conv_0096_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0096_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0096_cp (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0096_cp MODIFY target VARCHAR(10) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: CHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0096_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target CHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0096_cp (target) VALUES ('ab');
SELECT 'TC-41-CONV-0096-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0096_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0096_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0096_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0096_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0096_cp a JOIN t2_tc_41_conv_0096_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0096-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0097-DF
-- Conversion probe: CROSS-VC2CHAR
-- Type: VARCHAR(10) CHARACTER SET utf8mb4 -> CHAR(10) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR -> CHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ec20f2f98efd conv_probe=CROSS-VC2CHAR conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0097_df, t2_tc_41_conv_0097_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0097_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0097_df (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0097_df MODIFY target CHAR(10) CHARACTER SET utf8mb4;
-- Oracle table: VARCHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0097_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0097_df (target) VALUES ('ab');
SELECT 'TC-41-CONV-0097-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0097_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0097_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0097_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0097_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0097_df a JOIN t2_tc_41_conv_0097_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0097-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0098-IT
-- Conversion probe: CROSS-VC2CHAR
-- Type: VARCHAR(10) CHARACTER SET utf8mb4 -> CHAR(10) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR -> CHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ed4feb54dc84 conv_probe=CROSS-VC2CHAR conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0098_it, t2_tc_41_conv_0098_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0098_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0098_it (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0098_it MODIFY target CHAR(10) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0098_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0098_it (target) VALUES ('ab');
SELECT 'TC-41-CONV-0098-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0098_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0098_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0098_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0098_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0098_it a JOIN t2_tc_41_conv_0098_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0098-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0099-IP
-- Conversion probe: CROSS-VC2CHAR
-- Type: VARCHAR(10) CHARACTER SET utf8mb4 -> CHAR(10) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR -> CHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=639152c84d26 conv_probe=CROSS-VC2CHAR conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0099_ip, t2_tc_41_conv_0099_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0099_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0099_ip (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0099_ip MODIFY target CHAR(10) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0099_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0099_ip (target) VALUES ('ab');
SELECT 'TC-41-CONV-0099-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0099_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0099_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0099_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0099_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0099_ip a JOIN t2_tc_41_conv_0099_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0099-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0100-CP
-- Conversion probe: CROSS-VC2CHAR
-- Type: VARCHAR(10) CHARACTER SET utf8mb4 -> CHAR(10) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR -> CHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=94601f8c1723 conv_probe=CROSS-VC2CHAR conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0100_cp, t2_tc_41_conv_0100_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0100_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0100_cp (target) VALUES ('ab');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0100_cp MODIFY target CHAR(10) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: VARCHAR(10) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0100_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0100_cp (target) VALUES ('ab');
SELECT 'TC-41-CONV-0100-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0100_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0100_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0100_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0100_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0100_cp a JOIN t2_tc_41_conv_0100_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0100-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0101-DF
-- Conversion probe: CROSS-INT2VC
-- Type: INT -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: 整数 -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ca1c12e4cf34 conv_probe=CROSS-INT2VC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0101_df, t2_tc_41_conv_0101_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0101_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0101_df (target) VALUES (12);
INSERT INTO t1_tc_41_conv_0101_df (target) VALUES (-7);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0101_df MODIFY target VARCHAR(20) CHARACTER SET utf8mb4;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0101_df (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0101_df (target) VALUES (12);
INSERT INTO t2_tc_41_conv_0101_df (target) VALUES (-7);
SELECT 'TC-41-CONV-0101-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0101_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0101_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0101_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0101_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0101_df a JOIN t2_tc_41_conv_0101_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0101-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0102-IT
-- Conversion probe: CROSS-INT2VC
-- Type: INT -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: 整数 -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=add19a319c51 conv_probe=CROSS-INT2VC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0102_it, t2_tc_41_conv_0102_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0102_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0102_it (target) VALUES (12);
INSERT INTO t1_tc_41_conv_0102_it (target) VALUES (-7);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0102_it MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0102_it (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0102_it (target) VALUES (12);
INSERT INTO t2_tc_41_conv_0102_it (target) VALUES (-7);
SELECT 'TC-41-CONV-0102-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0102_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0102_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0102_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0102_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0102_it a JOIN t2_tc_41_conv_0102_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0102-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0103-IP
-- Conversion probe: CROSS-INT2VC
-- Type: INT -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: 整数 -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b0faead7770b conv_probe=CROSS-INT2VC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0103_ip, t2_tc_41_conv_0103_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0103_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0103_ip (target) VALUES (12);
INSERT INTO t1_tc_41_conv_0103_ip (target) VALUES (-7);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0103_ip MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0103_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0103_ip (target) VALUES (12);
INSERT INTO t2_tc_41_conv_0103_ip (target) VALUES (-7);
SELECT 'TC-41-CONV-0103-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0103_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0103_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0103_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0103_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0103_ip a JOIN t2_tc_41_conv_0103_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0103-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0104-CP
-- Conversion probe: CROSS-INT2VC
-- Type: INT -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: 整数 -> VARCHAR
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=41867ef83cd7 conv_probe=CROSS-INT2VC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0104_cp, t2_tc_41_conv_0104_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0104_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0104_cp (target) VALUES (12);
INSERT INTO t1_tc_41_conv_0104_cp (target) VALUES (-7);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0104_cp MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: INT
CREATE TABLE t2_tc_41_conv_0104_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target INT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0104_cp (target) VALUES (12);
INSERT INTO t2_tc_41_conv_0104_cp (target) VALUES (-7);
SELECT 'TC-41-CONV-0104-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0104_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0104_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0104_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0104_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0104_cp a JOIN t2_tc_41_conv_0104_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0104-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0105-DF
-- Conversion probe: CROSS-VC2INT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR -> 整数
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f84957b08f2f conv_probe=CROSS-VC2INT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0105_df, t2_tc_41_conv_0105_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0105_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0105_df (target) VALUES ('12');
INSERT INTO t1_tc_41_conv_0105_df (target) VALUES ('-7');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0105_df MODIFY target INT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0105_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0105_df (target) VALUES ('12');
INSERT INTO t2_tc_41_conv_0105_df (target) VALUES ('-7');
SELECT 'TC-41-CONV-0105-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0105_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0105_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0105_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0105_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0105_df a JOIN t2_tc_41_conv_0105_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0105-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0106-IT
-- Conversion probe: CROSS-VC2INT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR -> 整数
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f9798415ecb1 conv_probe=CROSS-VC2INT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0106_it, t2_tc_41_conv_0106_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0106_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0106_it (target) VALUES ('12');
INSERT INTO t1_tc_41_conv_0106_it (target) VALUES ('-7');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0106_it MODIFY target INT, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0106_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0106_it (target) VALUES ('12');
INSERT INTO t2_tc_41_conv_0106_it (target) VALUES ('-7');
SELECT 'TC-41-CONV-0106-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0106_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0106_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0106_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0106_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0106_it a JOIN t2_tc_41_conv_0106_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0106-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0107-IP
-- Conversion probe: CROSS-VC2INT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR -> 整数
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3c1054cb6db5 conv_probe=CROSS-VC2INT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0107_ip, t2_tc_41_conv_0107_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0107_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0107_ip (target) VALUES ('12');
INSERT INTO t1_tc_41_conv_0107_ip (target) VALUES ('-7');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0107_ip MODIFY target INT, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0107_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0107_ip (target) VALUES ('12');
INSERT INTO t2_tc_41_conv_0107_ip (target) VALUES ('-7');
SELECT 'TC-41-CONV-0107-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0107_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0107_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0107_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0107_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0107_ip a JOIN t2_tc_41_conv_0107_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0107-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0108-CP
-- Conversion probe: CROSS-VC2INT
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR -> 整数
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=45654ffd0320 conv_probe=CROSS-VC2INT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0108_cp, t2_tc_41_conv_0108_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0108_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0108_cp (target) VALUES ('12');
INSERT INTO t1_tc_41_conv_0108_cp (target) VALUES ('-7');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0108_cp MODIFY target INT, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0108_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0108_cp (target) VALUES ('12');
INSERT INTO t2_tc_41_conv_0108_cp (target) VALUES ('-7');
SELECT 'TC-41-CONV-0108-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0108_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0108_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0108_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0108_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0108_cp a JOIN t2_tc_41_conv_0108_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0108-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0109-DF
-- Conversion probe: CROSS-VC2INT-BAD
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: default, Expected: MEASURE
-- Probe note: VARCHAR -> 整数但数据非数字
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=40c97f8e4c20 conv_probe=CROSS-VC2INT-BAD conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0109_df, t2_tc_41_conv_0109_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0109_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0109_df (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0109_df MODIFY target INT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0109_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0109_df (target) VALUES ('abc');
SELECT 'TC-41-CONV-0109-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0109_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0109_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0109_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0109_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0109_df a JOIN t2_tc_41_conv_0109_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0109-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0110-IT
-- Conversion probe: CROSS-VC2INT-BAD
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: instant, Expected: MEASURE
-- Probe note: VARCHAR -> 整数但数据非数字
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=527591430eda conv_probe=CROSS-VC2INT-BAD conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0110_it, t2_tc_41_conv_0110_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0110_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0110_it (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0110_it MODIFY target INT, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0110_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0110_it (target) VALUES ('abc');
SELECT 'TC-41-CONV-0110-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0110_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0110_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0110_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0110_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0110_it a JOIN t2_tc_41_conv_0110_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0110-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0111-IP
-- Conversion probe: CROSS-VC2INT-BAD
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: inplace, Expected: MEASURE
-- Probe note: VARCHAR -> 整数但数据非数字
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2c47609c963b conv_probe=CROSS-VC2INT-BAD conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0111_ip, t2_tc_41_conv_0111_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0111_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0111_ip (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0111_ip MODIFY target INT, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0111_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0111_ip (target) VALUES ('abc');
SELECT 'TC-41-CONV-0111-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0111_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0111_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0111_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0111_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0111_ip a JOIN t2_tc_41_conv_0111_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0111-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0112-CP
-- Conversion probe: CROSS-VC2INT-BAD
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> INT, Algorithm: copy, Expected: MEASURE
-- Probe note: VARCHAR -> 整数但数据非数字
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=fc46559ba437 conv_probe=CROSS-VC2INT-BAD conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0112_cp, t2_tc_41_conv_0112_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0112_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0112_cp (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0112_cp MODIFY target INT, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0112_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0112_cp (target) VALUES ('abc');
SELECT 'TC-41-CONV-0112-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0112_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0112_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0112_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0112_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0112_cp a JOIN t2_tc_41_conv_0112_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0112-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0113-DF
-- Conversion probe: ENUM-APPEND
-- Type: ENUM('a','b') -> ENUM('a','b','c'), Algorithm: default, Expected: MEASURE
-- Probe note: ENUM 末尾追加成员（文档记载为 INPLACE 不重建）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=89e4b65b4ba1 conv_probe=ENUM-APPEND conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0113_df, t2_tc_41_conv_0113_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0113_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0113_df (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0113_df (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0113_df MODIFY target ENUM('a','b','c');
-- Oracle table: ENUM('a','b')
CREATE TABLE t2_tc_41_conv_0113_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0113_df (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0113_df (target) VALUES ('b');
SELECT 'TC-41-CONV-0113-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0113_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0113_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0113_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0113_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0113_df a JOIN t2_tc_41_conv_0113_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0113-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0114-IT
-- Conversion probe: ENUM-APPEND
-- Type: ENUM('a','b') -> ENUM('a','b','c'), Algorithm: instant, Expected: MEASURE
-- Probe note: ENUM 末尾追加成员（文档记载为 INPLACE 不重建）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=90fb76b63c66 conv_probe=ENUM-APPEND conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0114_it, t2_tc_41_conv_0114_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0114_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0114_it (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0114_it (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0114_it MODIFY target ENUM('a','b','c'), ALGORITHM=INSTANT;
-- Oracle table: ENUM('a','b')
CREATE TABLE t2_tc_41_conv_0114_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0114_it (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0114_it (target) VALUES ('b');
SELECT 'TC-41-CONV-0114-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0114_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0114_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0114_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0114_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0114_it a JOIN t2_tc_41_conv_0114_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0114-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0115-IP
-- Conversion probe: ENUM-APPEND
-- Type: ENUM('a','b') -> ENUM('a','b','c'), Algorithm: inplace, Expected: MEASURE
-- Probe note: ENUM 末尾追加成员（文档记载为 INPLACE 不重建）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=27f4ada6f12d conv_probe=ENUM-APPEND conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0115_ip, t2_tc_41_conv_0115_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0115_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0115_ip (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0115_ip (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0115_ip MODIFY target ENUM('a','b','c'), ALGORITHM=INPLACE;
-- Oracle table: ENUM('a','b')
CREATE TABLE t2_tc_41_conv_0115_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0115_ip (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0115_ip (target) VALUES ('b');
SELECT 'TC-41-CONV-0115-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0115_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0115_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0115_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0115_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0115_ip a JOIN t2_tc_41_conv_0115_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0115-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0116-CP
-- Conversion probe: ENUM-APPEND
-- Type: ENUM('a','b') -> ENUM('a','b','c'), Algorithm: copy, Expected: MEASURE
-- Probe note: ENUM 末尾追加成员（文档记载为 INPLACE 不重建）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=616c24927495 conv_probe=ENUM-APPEND conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0116_cp, t2_tc_41_conv_0116_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0116_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0116_cp (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0116_cp (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0116_cp MODIFY target ENUM('a','b','c'), ALGORITHM=COPY;
-- Oracle table: ENUM('a','b')
CREATE TABLE t2_tc_41_conv_0116_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0116_cp (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0116_cp (target) VALUES ('b');
SELECT 'TC-41-CONV-0116-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0116_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0116_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0116_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0116_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0116_cp a JOIN t2_tc_41_conv_0116_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0116-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0117-DF
-- Conversion probe: ENUM-REORDER
-- Type: ENUM('a','b','c') -> ENUM('a','c','b'), Algorithm: default, Expected: MEASURE
-- Probe note: ENUM 成员重排（必须重建，否则值会错乱）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3cef98a8e191 conv_probe=ENUM-REORDER conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0117_df, t2_tc_41_conv_0117_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0117_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0117_df (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0117_df (target) VALUES ('b');
INSERT INTO t1_tc_41_conv_0117_df (target) VALUES ('c');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0117_df MODIFY target ENUM('a','c','b');
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0117_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0117_df (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0117_df (target) VALUES ('b');
INSERT INTO t2_tc_41_conv_0117_df (target) VALUES ('c');
SELECT 'TC-41-CONV-0117-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0117_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0117_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0117_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0117_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0117_df a JOIN t2_tc_41_conv_0117_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0117-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0118-IT
-- Conversion probe: ENUM-REORDER
-- Type: ENUM('a','b','c') -> ENUM('a','c','b'), Algorithm: instant, Expected: MEASURE
-- Probe note: ENUM 成员重排（必须重建，否则值会错乱）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=73ef12f5339a conv_probe=ENUM-REORDER conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0118_it, t2_tc_41_conv_0118_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0118_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0118_it (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0118_it (target) VALUES ('b');
INSERT INTO t1_tc_41_conv_0118_it (target) VALUES ('c');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0118_it MODIFY target ENUM('a','c','b'), ALGORITHM=INSTANT;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0118_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0118_it (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0118_it (target) VALUES ('b');
INSERT INTO t2_tc_41_conv_0118_it (target) VALUES ('c');
SELECT 'TC-41-CONV-0118-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0118_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0118_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0118_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0118_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0118_it a JOIN t2_tc_41_conv_0118_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0118-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0119-IP
-- Conversion probe: ENUM-REORDER
-- Type: ENUM('a','b','c') -> ENUM('a','c','b'), Algorithm: inplace, Expected: MEASURE
-- Probe note: ENUM 成员重排（必须重建，否则值会错乱）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3455a4a0cdfc conv_probe=ENUM-REORDER conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0119_ip, t2_tc_41_conv_0119_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0119_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0119_ip (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0119_ip (target) VALUES ('b');
INSERT INTO t1_tc_41_conv_0119_ip (target) VALUES ('c');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0119_ip MODIFY target ENUM('a','c','b'), ALGORITHM=INPLACE;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0119_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0119_ip (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0119_ip (target) VALUES ('b');
INSERT INTO t2_tc_41_conv_0119_ip (target) VALUES ('c');
SELECT 'TC-41-CONV-0119-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0119_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0119_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0119_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0119_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0119_ip a JOIN t2_tc_41_conv_0119_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0119-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0120-CP
-- Conversion probe: ENUM-REORDER
-- Type: ENUM('a','b','c') -> ENUM('a','c','b'), Algorithm: copy, Expected: MEASURE
-- Probe note: ENUM 成员重排（必须重建，否则值会错乱）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a5c3d9404e4d conv_probe=ENUM-REORDER conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0120_cp, t2_tc_41_conv_0120_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0120_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0120_cp (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0120_cp (target) VALUES ('b');
INSERT INTO t1_tc_41_conv_0120_cp (target) VALUES ('c');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0120_cp MODIFY target ENUM('a','c','b'), ALGORITHM=COPY;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0120_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0120_cp (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0120_cp (target) VALUES ('b');
INSERT INTO t2_tc_41_conv_0120_cp (target) VALUES ('c');
SELECT 'TC-41-CONV-0120-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0120_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0120_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0120_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0120_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0120_cp a JOIN t2_tc_41_conv_0120_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0120-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0121-DF
-- Conversion probe: ENUM-REMOVE
-- Type: ENUM('a','b','c') -> ENUM('a','b'), Algorithm: default, Expected: MEASURE
-- Probe note: ENUM 删除末尾成员（数据里没有该成员）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e83e6e5e2e63 conv_probe=ENUM-REMOVE conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0121_df, t2_tc_41_conv_0121_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0121_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0121_df (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0121_df (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0121_df MODIFY target ENUM('a','b');
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0121_df (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0121_df (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0121_df (target) VALUES ('b');
SELECT 'TC-41-CONV-0121-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0121_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0121_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0121_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0121_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0121_df a JOIN t2_tc_41_conv_0121_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0121-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0122-IT
-- Conversion probe: ENUM-REMOVE
-- Type: ENUM('a','b','c') -> ENUM('a','b'), Algorithm: instant, Expected: MEASURE
-- Probe note: ENUM 删除末尾成员（数据里没有该成员）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=63db14d6173f conv_probe=ENUM-REMOVE conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0122_it, t2_tc_41_conv_0122_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0122_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0122_it (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0122_it (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0122_it MODIFY target ENUM('a','b'), ALGORITHM=INSTANT;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0122_it (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0122_it (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0122_it (target) VALUES ('b');
SELECT 'TC-41-CONV-0122-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0122_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0122_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0122_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0122_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0122_it a JOIN t2_tc_41_conv_0122_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0122-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0123-IP
-- Conversion probe: ENUM-REMOVE
-- Type: ENUM('a','b','c') -> ENUM('a','b'), Algorithm: inplace, Expected: MEASURE
-- Probe note: ENUM 删除末尾成员（数据里没有该成员）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f97542273483 conv_probe=ENUM-REMOVE conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0123_ip, t2_tc_41_conv_0123_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0123_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0123_ip (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0123_ip (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0123_ip MODIFY target ENUM('a','b'), ALGORITHM=INPLACE;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0123_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0123_ip (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0123_ip (target) VALUES ('b');
SELECT 'TC-41-CONV-0123-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0123_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0123_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0123_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0123_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0123_ip a JOIN t2_tc_41_conv_0123_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0123-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0124-CP
-- Conversion probe: ENUM-REMOVE
-- Type: ENUM('a','b','c') -> ENUM('a','b'), Algorithm: copy, Expected: MEASURE
-- Probe note: ENUM 删除末尾成员（数据里没有该成员）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=cbac5b5f7cc8 conv_probe=ENUM-REMOVE conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0124_cp, t2_tc_41_conv_0124_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0124_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0124_cp (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0124_cp (target) VALUES ('b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0124_cp MODIFY target ENUM('a','b'), ALGORITHM=COPY;
-- Oracle table: ENUM('a','b','c')
CREATE TABLE t2_tc_41_conv_0124_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target ENUM('a','b','c'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0124_cp (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0124_cp (target) VALUES ('b');
SELECT 'TC-41-CONV-0124-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0124_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0124_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0124_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0124_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0124_cp a JOIN t2_tc_41_conv_0124_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0124-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0125-DF
-- Conversion probe: SET-APPEND
-- Type: SET('a','b') -> SET('a','b','c'), Algorithm: default, Expected: MEASURE
-- Probe note: SET 末尾追加成员
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f492510188be conv_probe=SET-APPEND conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0125_df, t2_tc_41_conv_0125_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0125_df (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0125_df (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0125_df (target) VALUES ('a,b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0125_df MODIFY target SET('a','b','c');
-- Oracle table: SET('a','b')
CREATE TABLE t2_tc_41_conv_0125_df (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0125_df (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0125_df (target) VALUES ('a,b');
SELECT 'TC-41-CONV-0125-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0125_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0125_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0125_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0125_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0125_df a JOIN t2_tc_41_conv_0125_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0125-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0126-IT
-- Conversion probe: SET-APPEND
-- Type: SET('a','b') -> SET('a','b','c'), Algorithm: instant, Expected: MEASURE
-- Probe note: SET 末尾追加成员
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7a2ad1b21039 conv_probe=SET-APPEND conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0126_it, t2_tc_41_conv_0126_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0126_it (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0126_it (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0126_it (target) VALUES ('a,b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0126_it MODIFY target SET('a','b','c'), ALGORITHM=INSTANT;
-- Oracle table: SET('a','b')
CREATE TABLE t2_tc_41_conv_0126_it (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0126_it (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0126_it (target) VALUES ('a,b');
SELECT 'TC-41-CONV-0126-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0126_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0126_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0126_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0126_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0126_it a JOIN t2_tc_41_conv_0126_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0126-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0127-IP
-- Conversion probe: SET-APPEND
-- Type: SET('a','b') -> SET('a','b','c'), Algorithm: inplace, Expected: MEASURE
-- Probe note: SET 末尾追加成员
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a48c24dca04d conv_probe=SET-APPEND conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0127_ip, t2_tc_41_conv_0127_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0127_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0127_ip (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0127_ip (target) VALUES ('a,b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0127_ip MODIFY target SET('a','b','c'), ALGORITHM=INPLACE;
-- Oracle table: SET('a','b')
CREATE TABLE t2_tc_41_conv_0127_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0127_ip (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0127_ip (target) VALUES ('a,b');
SELECT 'TC-41-CONV-0127-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0127_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0127_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0127_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0127_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0127_ip a JOIN t2_tc_41_conv_0127_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0127-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0128-CP
-- Conversion probe: SET-APPEND
-- Type: SET('a','b') -> SET('a','b','c'), Algorithm: copy, Expected: MEASURE
-- Probe note: SET 末尾追加成员
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=514a3f289caa conv_probe=SET-APPEND conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0128_cp, t2_tc_41_conv_0128_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0128_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0128_cp (target) VALUES ('a');
INSERT INTO t1_tc_41_conv_0128_cp (target) VALUES ('a,b');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0128_cp MODIFY target SET('a','b','c'), ALGORITHM=COPY;
-- Oracle table: SET('a','b')
CREATE TABLE t2_tc_41_conv_0128_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target SET('a','b'),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0128_cp (target) VALUES ('a');
INSERT INTO t2_tc_41_conv_0128_cp (target) VALUES ('a,b');
SELECT 'TC-41-CONV-0128-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0128_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0128_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0128_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0128_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0128_cp a JOIN t2_tc_41_conv_0128_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0128-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0129-DF
-- Conversion probe: TIME-DT-FSP-UP
-- Type: DATETIME -> DATETIME(3), Algorithm: default, Expected: MEASURE
-- Probe note: DATETIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d4698a090079 conv_probe=TIME-DT-FSP-UP conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0129_df, t2_tc_41_conv_0129_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0129_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0129_df (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0129_df MODIFY target DATETIME(3);
-- Oracle table: DATETIME
CREATE TABLE t2_tc_41_conv_0129_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0129_df (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0129-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0129_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0129_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0129_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0129_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0129_df a JOIN t2_tc_41_conv_0129_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0129-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0130-IT
-- Conversion probe: TIME-DT-FSP-UP
-- Type: DATETIME -> DATETIME(3), Algorithm: instant, Expected: MEASURE
-- Probe note: DATETIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=74db7ed6cf9f conv_probe=TIME-DT-FSP-UP conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0130_it, t2_tc_41_conv_0130_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0130_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0130_it (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0130_it MODIFY target DATETIME(3), ALGORITHM=INSTANT;
-- Oracle table: DATETIME
CREATE TABLE t2_tc_41_conv_0130_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0130_it (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0130-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0130_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0130_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0130_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0130_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0130_it a JOIN t2_tc_41_conv_0130_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0130-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0131-IP
-- Conversion probe: TIME-DT-FSP-UP
-- Type: DATETIME -> DATETIME(3), Algorithm: inplace, Expected: MEASURE
-- Probe note: DATETIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=170ad3e5ac17 conv_probe=TIME-DT-FSP-UP conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0131_ip, t2_tc_41_conv_0131_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0131_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0131_ip (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0131_ip MODIFY target DATETIME(3), ALGORITHM=INPLACE;
-- Oracle table: DATETIME
CREATE TABLE t2_tc_41_conv_0131_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0131_ip (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0131-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0131_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0131_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0131_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0131_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0131_ip a JOIN t2_tc_41_conv_0131_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0131-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0132-CP
-- Conversion probe: TIME-DT-FSP-UP
-- Type: DATETIME -> DATETIME(3), Algorithm: copy, Expected: MEASURE
-- Probe note: DATETIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=985534598251 conv_probe=TIME-DT-FSP-UP conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0132_cp, t2_tc_41_conv_0132_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0132_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0132_cp (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0132_cp MODIFY target DATETIME(3), ALGORITHM=COPY;
-- Oracle table: DATETIME
CREATE TABLE t2_tc_41_conv_0132_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0132_cp (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0132-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0132_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0132_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0132_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0132_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0132_cp a JOIN t2_tc_41_conv_0132_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0132-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0133-DF
-- Conversion probe: TIME-DT-FSP-DOWN
-- Type: DATETIME(6) -> DATETIME(3), Algorithm: default, Expected: MEASURE
-- Probe note: DATETIME fsp 6 -> 3（精度丢失）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e44bcf5eb7ff conv_probe=TIME-DT-FSP-DOWN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0133_df, t2_tc_41_conv_0133_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0133_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0133_df (target) VALUES ('2026-09-23 10:00:00.123456');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0133_df MODIFY target DATETIME(3);
-- Oracle table: DATETIME(6)
CREATE TABLE t2_tc_41_conv_0133_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0133_df (target) VALUES ('2026-09-23 10:00:00.123456');
SELECT 'TC-41-CONV-0133-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0133_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0133_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0133_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0133_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0133_df a JOIN t2_tc_41_conv_0133_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0133-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0134-IT
-- Conversion probe: TIME-DT-FSP-DOWN
-- Type: DATETIME(6) -> DATETIME(3), Algorithm: instant, Expected: MEASURE
-- Probe note: DATETIME fsp 6 -> 3（精度丢失）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=04372c4d89ca conv_probe=TIME-DT-FSP-DOWN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0134_it, t2_tc_41_conv_0134_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0134_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0134_it (target) VALUES ('2026-09-23 10:00:00.123456');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0134_it MODIFY target DATETIME(3), ALGORITHM=INSTANT;
-- Oracle table: DATETIME(6)
CREATE TABLE t2_tc_41_conv_0134_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0134_it (target) VALUES ('2026-09-23 10:00:00.123456');
SELECT 'TC-41-CONV-0134-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0134_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0134_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0134_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0134_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0134_it a JOIN t2_tc_41_conv_0134_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0134-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0135-IP
-- Conversion probe: TIME-DT-FSP-DOWN
-- Type: DATETIME(6) -> DATETIME(3), Algorithm: inplace, Expected: MEASURE
-- Probe note: DATETIME fsp 6 -> 3（精度丢失）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3ae6b815b41f conv_probe=TIME-DT-FSP-DOWN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0135_ip, t2_tc_41_conv_0135_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0135_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0135_ip (target) VALUES ('2026-09-23 10:00:00.123456');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0135_ip MODIFY target DATETIME(3), ALGORITHM=INPLACE;
-- Oracle table: DATETIME(6)
CREATE TABLE t2_tc_41_conv_0135_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0135_ip (target) VALUES ('2026-09-23 10:00:00.123456');
SELECT 'TC-41-CONV-0135-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0135_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0135_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0135_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0135_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0135_ip a JOIN t2_tc_41_conv_0135_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0135-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0136-CP
-- Conversion probe: TIME-DT-FSP-DOWN
-- Type: DATETIME(6) -> DATETIME(3), Algorithm: copy, Expected: MEASURE
-- Probe note: DATETIME fsp 6 -> 3（精度丢失）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2928dd6c1b5c conv_probe=TIME-DT-FSP-DOWN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0136_cp, t2_tc_41_conv_0136_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0136_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0136_cp (target) VALUES ('2026-09-23 10:00:00.123456');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0136_cp MODIFY target DATETIME(3), ALGORITHM=COPY;
-- Oracle table: DATETIME(6)
CREATE TABLE t2_tc_41_conv_0136_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATETIME(6),
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0136_cp (target) VALUES ('2026-09-23 10:00:00.123456');
SELECT 'TC-41-CONV-0136-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0136_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0136_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0136_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0136_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0136_cp a JOIN t2_tc_41_conv_0136_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0136-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0137-DF
-- Conversion probe: TIME-TS2DT
-- Type: TIMESTAMP -> DATETIME, Algorithm: default, Expected: MEASURE
-- Probe note: TIMESTAMP -> DATETIME（时区语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=292de88b7cdc conv_probe=TIME-TS2DT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0137_df, t2_tc_41_conv_0137_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0137_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0137_df (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0137_df MODIFY target DATETIME;
-- Oracle table: TIMESTAMP
CREATE TABLE t2_tc_41_conv_0137_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0137_df (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0137-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0137_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0137_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0137_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0137_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0137_df a JOIN t2_tc_41_conv_0137_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0137-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0138-IT
-- Conversion probe: TIME-TS2DT
-- Type: TIMESTAMP -> DATETIME, Algorithm: instant, Expected: MEASURE
-- Probe note: TIMESTAMP -> DATETIME（时区语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=30d7f01ba002 conv_probe=TIME-TS2DT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0138_it, t2_tc_41_conv_0138_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0138_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0138_it (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0138_it MODIFY target DATETIME, ALGORITHM=INSTANT;
-- Oracle table: TIMESTAMP
CREATE TABLE t2_tc_41_conv_0138_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0138_it (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0138-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0138_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0138_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0138_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0138_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0138_it a JOIN t2_tc_41_conv_0138_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0138-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0139-IP
-- Conversion probe: TIME-TS2DT
-- Type: TIMESTAMP -> DATETIME, Algorithm: inplace, Expected: MEASURE
-- Probe note: TIMESTAMP -> DATETIME（时区语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=0be6e816e02d conv_probe=TIME-TS2DT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0139_ip, t2_tc_41_conv_0139_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0139_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0139_ip (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0139_ip MODIFY target DATETIME, ALGORITHM=INPLACE;
-- Oracle table: TIMESTAMP
CREATE TABLE t2_tc_41_conv_0139_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0139_ip (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0139-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0139_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0139_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0139_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0139_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0139_ip a JOIN t2_tc_41_conv_0139_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0139-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0140-CP
-- Conversion probe: TIME-TS2DT
-- Type: TIMESTAMP -> DATETIME, Algorithm: copy, Expected: MEASURE
-- Probe note: TIMESTAMP -> DATETIME（时区语义变化）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7102f9b53721 conv_probe=TIME-TS2DT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0140_cp, t2_tc_41_conv_0140_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0140_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0140_cp (target) VALUES ('2026-09-23 10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0140_cp MODIFY target DATETIME, ALGORITHM=COPY;
-- Oracle table: TIMESTAMP
CREATE TABLE t2_tc_41_conv_0140_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TIMESTAMP,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0140_cp (target) VALUES ('2026-09-23 10:00:00');
SELECT 'TC-41-CONV-0140-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0140_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0140_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0140_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0140_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0140_cp a JOIN t2_tc_41_conv_0140_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0140-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0141-DF
-- Conversion probe: TIME-DATE2DT
-- Type: DATE -> DATETIME, Algorithm: default, Expected: MEASURE
-- Probe note: DATE -> DATETIME
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=9baf0e729bd2 conv_probe=TIME-DATE2DT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0141_df, t2_tc_41_conv_0141_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0141_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0141_df (target) VALUES ('2026-09-23');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0141_df MODIFY target DATETIME;
-- Oracle table: DATE
CREATE TABLE t2_tc_41_conv_0141_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0141_df (target) VALUES ('2026-09-23');
SELECT 'TC-41-CONV-0141-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0141_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0141_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0141_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0141_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0141_df a JOIN t2_tc_41_conv_0141_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0141-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0142-IT
-- Conversion probe: TIME-DATE2DT
-- Type: DATE -> DATETIME, Algorithm: instant, Expected: MEASURE
-- Probe note: DATE -> DATETIME
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ecdcbda12708 conv_probe=TIME-DATE2DT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0142_it, t2_tc_41_conv_0142_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0142_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0142_it (target) VALUES ('2026-09-23');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0142_it MODIFY target DATETIME, ALGORITHM=INSTANT;
-- Oracle table: DATE
CREATE TABLE t2_tc_41_conv_0142_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0142_it (target) VALUES ('2026-09-23');
SELECT 'TC-41-CONV-0142-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0142_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0142_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0142_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0142_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0142_it a JOIN t2_tc_41_conv_0142_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0142-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0143-IP
-- Conversion probe: TIME-DATE2DT
-- Type: DATE -> DATETIME, Algorithm: inplace, Expected: MEASURE
-- Probe note: DATE -> DATETIME
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d4451205406f conv_probe=TIME-DATE2DT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0143_ip, t2_tc_41_conv_0143_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0143_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0143_ip (target) VALUES ('2026-09-23');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0143_ip MODIFY target DATETIME, ALGORITHM=INPLACE;
-- Oracle table: DATE
CREATE TABLE t2_tc_41_conv_0143_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0143_ip (target) VALUES ('2026-09-23');
SELECT 'TC-41-CONV-0143-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0143_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0143_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0143_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0143_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0143_ip a JOIN t2_tc_41_conv_0143_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0143-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0144-CP
-- Conversion probe: TIME-DATE2DT
-- Type: DATE -> DATETIME, Algorithm: copy, Expected: MEASURE
-- Probe note: DATE -> DATETIME
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=be7d8b9e77d1 conv_probe=TIME-DATE2DT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0144_cp, t2_tc_41_conv_0144_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0144_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0144_cp (target) VALUES ('2026-09-23');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0144_cp MODIFY target DATETIME, ALGORITHM=COPY;
-- Oracle table: DATE
CREATE TABLE t2_tc_41_conv_0144_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DATE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0144_cp (target) VALUES ('2026-09-23');
SELECT 'TC-41-CONV-0144-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0144_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0144_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0144_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0144_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0144_cp a JOIN t2_tc_41_conv_0144_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0144-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0145-DF
-- Conversion probe: TIME-TIME-FSP
-- Type: TIME -> TIME(3), Algorithm: default, Expected: MEASURE
-- Probe note: TIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=cac668ed8997 conv_probe=TIME-TIME-FSP conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0145_df, t2_tc_41_conv_0145_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0145_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0145_df (target) VALUES ('10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0145_df MODIFY target TIME(3);
-- Oracle table: TIME
CREATE TABLE t2_tc_41_conv_0145_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0145_df (target) VALUES ('10:00:00');
SELECT 'TC-41-CONV-0145-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0145_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0145_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0145_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0145_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0145_df a JOIN t2_tc_41_conv_0145_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0145-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0146-IT
-- Conversion probe: TIME-TIME-FSP
-- Type: TIME -> TIME(3), Algorithm: instant, Expected: MEASURE
-- Probe note: TIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=b84b4a66ed84 conv_probe=TIME-TIME-FSP conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0146_it, t2_tc_41_conv_0146_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0146_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0146_it (target) VALUES ('10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0146_it MODIFY target TIME(3), ALGORITHM=INSTANT;
-- Oracle table: TIME
CREATE TABLE t2_tc_41_conv_0146_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0146_it (target) VALUES ('10:00:00');
SELECT 'TC-41-CONV-0146-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0146_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0146_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0146_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0146_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0146_it a JOIN t2_tc_41_conv_0146_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0146-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0147-IP
-- Conversion probe: TIME-TIME-FSP
-- Type: TIME -> TIME(3), Algorithm: inplace, Expected: MEASURE
-- Probe note: TIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7a50e1d4b0c2 conv_probe=TIME-TIME-FSP conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0147_ip, t2_tc_41_conv_0147_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0147_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0147_ip (target) VALUES ('10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0147_ip MODIFY target TIME(3), ALGORITHM=INPLACE;
-- Oracle table: TIME
CREATE TABLE t2_tc_41_conv_0147_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0147_ip (target) VALUES ('10:00:00');
SELECT 'TC-41-CONV-0147-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0147_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0147_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0147_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0147_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0147_ip a JOIN t2_tc_41_conv_0147_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0147-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0148-CP
-- Conversion probe: TIME-TIME-FSP
-- Type: TIME -> TIME(3), Algorithm: copy, Expected: MEASURE
-- Probe note: TIME fsp 0 -> 3
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=818259cc0377 conv_probe=TIME-TIME-FSP conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0148_cp, t2_tc_41_conv_0148_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0148_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0148_cp (target) VALUES ('10:00:00');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0148_cp MODIFY target TIME(3), ALGORITHM=COPY;
-- Oracle table: TIME
CREATE TABLE t2_tc_41_conv_0148_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target TIME,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0148_cp (target) VALUES ('10:00:00');
SELECT 'TC-41-CONV-0148-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0148_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0148_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0148_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0148_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0148_cp a JOIN t2_tc_41_conv_0148_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0148-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0149-DF
-- Conversion probe: TIME-YEAR2INT
-- Type: YEAR -> SMALLINT, Algorithm: default, Expected: MEASURE
-- Probe note: YEAR -> SMALLINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d2472e7a0388 conv_probe=TIME-YEAR2INT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0149_df, t2_tc_41_conv_0149_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0149_df (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0149_df (target) VALUES (2026);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0149_df MODIFY target SMALLINT;
-- Oracle table: YEAR
CREATE TABLE t2_tc_41_conv_0149_df (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0149_df (target) VALUES (2026);
SELECT 'TC-41-CONV-0149-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0149_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0149_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0149_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0149_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0149_df a JOIN t2_tc_41_conv_0149_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0149-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0150-IT
-- Conversion probe: TIME-YEAR2INT
-- Type: YEAR -> SMALLINT, Algorithm: instant, Expected: MEASURE
-- Probe note: YEAR -> SMALLINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=f565e2955a88 conv_probe=TIME-YEAR2INT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0150_it, t2_tc_41_conv_0150_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0150_it (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0150_it (target) VALUES (2026);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0150_it MODIFY target SMALLINT, ALGORITHM=INSTANT;
-- Oracle table: YEAR
CREATE TABLE t2_tc_41_conv_0150_it (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0150_it (target) VALUES (2026);
SELECT 'TC-41-CONV-0150-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0150_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0150_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0150_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0150_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0150_it a JOIN t2_tc_41_conv_0150_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0150-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0151-IP
-- Conversion probe: TIME-YEAR2INT
-- Type: YEAR -> SMALLINT, Algorithm: inplace, Expected: MEASURE
-- Probe note: YEAR -> SMALLINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=5789bb7e62fd conv_probe=TIME-YEAR2INT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0151_ip, t2_tc_41_conv_0151_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0151_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0151_ip (target) VALUES (2026);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0151_ip MODIFY target SMALLINT, ALGORITHM=INPLACE;
-- Oracle table: YEAR
CREATE TABLE t2_tc_41_conv_0151_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0151_ip (target) VALUES (2026);
SELECT 'TC-41-CONV-0151-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0151_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0151_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0151_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0151_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0151_ip a JOIN t2_tc_41_conv_0151_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0151-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0152-CP
-- Conversion probe: TIME-YEAR2INT
-- Type: YEAR -> SMALLINT, Algorithm: copy, Expected: MEASURE
-- Probe note: YEAR -> SMALLINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=400cc59de7d5 conv_probe=TIME-YEAR2INT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0152_cp, t2_tc_41_conv_0152_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0152_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0152_cp (target) VALUES (2026);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0152_cp MODIFY target SMALLINT, ALGORITHM=COPY;
-- Oracle table: YEAR
CREATE TABLE t2_tc_41_conv_0152_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target YEAR,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0152_cp (target) VALUES (2026);
SELECT 'TC-41-CONV-0152-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0152_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0152_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0152_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0152_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0152_cp a JOIN t2_tc_41_conv_0152_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0152-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0153-DF
-- Conversion probe: FLT-2-DBL
-- Type: FLOAT -> DOUBLE, Algorithm: default, Expected: MEASURE
-- Probe note: FLOAT -> DOUBLE
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=71da9f3e3fa1 conv_probe=FLT-2-DBL conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0153_df, t2_tc_41_conv_0153_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0153_df (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0153_df (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0153_df (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0153_df MODIFY target DOUBLE;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0153_df (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0153_df (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0153_df (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0153-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0153_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0153_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0153_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0153_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0153_df a JOIN t2_tc_41_conv_0153_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0153-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0154-IT
-- Conversion probe: FLT-2-DBL
-- Type: FLOAT -> DOUBLE, Algorithm: instant, Expected: MEASURE
-- Probe note: FLOAT -> DOUBLE
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=28c7c1540833 conv_probe=FLT-2-DBL conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0154_it, t2_tc_41_conv_0154_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0154_it (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0154_it (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0154_it (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0154_it MODIFY target DOUBLE, ALGORITHM=INSTANT;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0154_it (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0154_it (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0154_it (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0154-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0154_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0154_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0154_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0154_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0154_it a JOIN t2_tc_41_conv_0154_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0154-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0155-IP
-- Conversion probe: FLT-2-DBL
-- Type: FLOAT -> DOUBLE, Algorithm: inplace, Expected: MEASURE
-- Probe note: FLOAT -> DOUBLE
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2be0fee98d20 conv_probe=FLT-2-DBL conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0155_ip, t2_tc_41_conv_0155_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0155_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0155_ip (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0155_ip (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0155_ip MODIFY target DOUBLE, ALGORITHM=INPLACE;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0155_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0155_ip (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0155_ip (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0155-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0155_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0155_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0155_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0155_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0155_ip a JOIN t2_tc_41_conv_0155_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0155-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0156-CP
-- Conversion probe: FLT-2-DBL
-- Type: FLOAT -> DOUBLE, Algorithm: copy, Expected: MEASURE
-- Probe note: FLOAT -> DOUBLE
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=12e28c500c3a conv_probe=FLT-2-DBL conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0156_cp, t2_tc_41_conv_0156_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0156_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0156_cp (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0156_cp (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0156_cp MODIFY target DOUBLE, ALGORITHM=COPY;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0156_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0156_cp (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0156_cp (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0156-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0156_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0156_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0156_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0156_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0156_cp a JOIN t2_tc_41_conv_0156_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0156-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0157-DF
-- Conversion probe: DBL-2-DEC
-- Type: DOUBLE -> DECIMAL(20,4), Algorithm: default, Expected: MEASURE
-- Probe note: DOUBLE -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e0436a193d11 conv_probe=DBL-2-DEC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0157_df, t2_tc_41_conv_0157_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0157_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0157_df (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0157_df (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0157_df MODIFY target DECIMAL(20,4);
-- Oracle table: DOUBLE
CREATE TABLE t2_tc_41_conv_0157_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0157_df (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0157_df (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0157-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0157_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0157_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0157_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0157_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0157_df a JOIN t2_tc_41_conv_0157_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0157-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0158-IT
-- Conversion probe: DBL-2-DEC
-- Type: DOUBLE -> DECIMAL(20,4), Algorithm: instant, Expected: MEASURE
-- Probe note: DOUBLE -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1cb9437bbaa3 conv_probe=DBL-2-DEC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0158_it, t2_tc_41_conv_0158_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0158_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0158_it (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0158_it (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0158_it MODIFY target DECIMAL(20,4), ALGORITHM=INSTANT;
-- Oracle table: DOUBLE
CREATE TABLE t2_tc_41_conv_0158_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0158_it (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0158_it (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0158-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0158_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0158_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0158_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0158_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0158_it a JOIN t2_tc_41_conv_0158_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0158-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0159-IP
-- Conversion probe: DBL-2-DEC
-- Type: DOUBLE -> DECIMAL(20,4), Algorithm: inplace, Expected: MEASURE
-- Probe note: DOUBLE -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=2f20cb2431e7 conv_probe=DBL-2-DEC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0159_ip, t2_tc_41_conv_0159_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0159_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0159_ip (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0159_ip (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0159_ip MODIFY target DECIMAL(20,4), ALGORITHM=INPLACE;
-- Oracle table: DOUBLE
CREATE TABLE t2_tc_41_conv_0159_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0159_ip (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0159_ip (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0159-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0159_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0159_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0159_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0159_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0159_ip a JOIN t2_tc_41_conv_0159_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0159-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0160-CP
-- Conversion probe: DBL-2-DEC
-- Type: DOUBLE -> DECIMAL(20,4), Algorithm: copy, Expected: MEASURE
-- Probe note: DOUBLE -> DECIMAL
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3a3db03c4e93 conv_probe=DBL-2-DEC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0160_cp, t2_tc_41_conv_0160_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0160_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0160_cp (target) VALUES (1.5);
INSERT INTO t1_tc_41_conv_0160_cp (target) VALUES (-0.25);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0160_cp MODIFY target DECIMAL(20,4), ALGORITHM=COPY;
-- Oracle table: DOUBLE
CREATE TABLE t2_tc_41_conv_0160_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target DOUBLE,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0160_cp (target) VALUES (1.5);
INSERT INTO t2_tc_41_conv_0160_cp (target) VALUES (-0.25);
SELECT 'TC-41-CONV-0160-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0160_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0160_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0160_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0160_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0160_cp a JOIN t2_tc_41_conv_0160_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0160-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0161-DF
-- Conversion probe: FLT-PREC
-- Type: FLOAT -> FLOAT(10,2), Algorithm: default, Expected: MEASURE
-- Probe note: FLOAT -> FLOAT(M,D)（8.0.17 起弃用）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=17db69943ebe conv_probe=FLT-PREC conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0161_df, t2_tc_41_conv_0161_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0161_df (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0161_df (target) VALUES (1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0161_df MODIFY target FLOAT(10,2);
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0161_df (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0161_df (target) VALUES (1.5);
SELECT 'TC-41-CONV-0161-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0161_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0161_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0161_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0161_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0161_df a JOIN t2_tc_41_conv_0161_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0161-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0162-IT
-- Conversion probe: FLT-PREC
-- Type: FLOAT -> FLOAT(10,2), Algorithm: instant, Expected: MEASURE
-- Probe note: FLOAT -> FLOAT(M,D)（8.0.17 起弃用）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=bb1030c497d0 conv_probe=FLT-PREC conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0162_it, t2_tc_41_conv_0162_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0162_it (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0162_it (target) VALUES (1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0162_it MODIFY target FLOAT(10,2), ALGORITHM=INSTANT;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0162_it (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0162_it (target) VALUES (1.5);
SELECT 'TC-41-CONV-0162-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0162_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0162_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0162_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0162_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0162_it a JOIN t2_tc_41_conv_0162_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0162-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0163-IP
-- Conversion probe: FLT-PREC
-- Type: FLOAT -> FLOAT(10,2), Algorithm: inplace, Expected: MEASURE
-- Probe note: FLOAT -> FLOAT(M,D)（8.0.17 起弃用）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a860d3031653 conv_probe=FLT-PREC conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0163_ip, t2_tc_41_conv_0163_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0163_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0163_ip (target) VALUES (1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0163_ip MODIFY target FLOAT(10,2), ALGORITHM=INPLACE;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0163_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0163_ip (target) VALUES (1.5);
SELECT 'TC-41-CONV-0163-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0163_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0163_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0163_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0163_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0163_ip a JOIN t2_tc_41_conv_0163_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0163-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0164-CP
-- Conversion probe: FLT-PREC
-- Type: FLOAT -> FLOAT(10,2), Algorithm: copy, Expected: MEASURE
-- Probe note: FLOAT -> FLOAT(M,D)（8.0.17 起弃用）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=425b3c045d6e conv_probe=FLT-PREC conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0164_cp, t2_tc_41_conv_0164_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0164_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0164_cp (target) VALUES (1.5);
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0164_cp MODIFY target FLOAT(10,2), ALGORITHM=COPY;
-- Oracle table: FLOAT
CREATE TABLE t2_tc_41_conv_0164_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target FLOAT,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0164_cp (target) VALUES (1.5);
SELECT 'TC-41-CONV-0164-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0164_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0164_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0164_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0164_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0164_cp a JOIN t2_tc_41_conv_0164_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0164-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0165-DF
-- Conversion probe: JSON-2-TEXT
-- Type: JSON -> LONGTEXT CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: JSON -> LONGTEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=257951ab335f conv_probe=JSON-2-TEXT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0165_df, t2_tc_41_conv_0165_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0165_df (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0165_df (target) VALUES (CAST('{"a":1}' AS JSON));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0165_df MODIFY target LONGTEXT CHARACTER SET utf8mb4;
-- Oracle table: JSON
CREATE TABLE t2_tc_41_conv_0165_df (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0165_df (target) VALUES (CAST('{"a":1}' AS JSON));
SELECT 'TC-41-CONV-0165-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0165_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0165_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0165_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0165_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0165_df a JOIN t2_tc_41_conv_0165_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0165-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0166-IT
-- Conversion probe: JSON-2-TEXT
-- Type: JSON -> LONGTEXT CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: JSON -> LONGTEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=716a5548775f conv_probe=JSON-2-TEXT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0166_it, t2_tc_41_conv_0166_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0166_it (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0166_it (target) VALUES (CAST('{"a":1}' AS JSON));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0166_it MODIFY target LONGTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: JSON
CREATE TABLE t2_tc_41_conv_0166_it (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0166_it (target) VALUES (CAST('{"a":1}' AS JSON));
SELECT 'TC-41-CONV-0166-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0166_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0166_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0166_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0166_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0166_it a JOIN t2_tc_41_conv_0166_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0166-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0167-IP
-- Conversion probe: JSON-2-TEXT
-- Type: JSON -> LONGTEXT CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: JSON -> LONGTEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=ffb2758cac9c conv_probe=JSON-2-TEXT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0167_ip, t2_tc_41_conv_0167_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0167_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0167_ip (target) VALUES (CAST('{"a":1}' AS JSON));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0167_ip MODIFY target LONGTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: JSON
CREATE TABLE t2_tc_41_conv_0167_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0167_ip (target) VALUES (CAST('{"a":1}' AS JSON));
SELECT 'TC-41-CONV-0167-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0167_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0167_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0167_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0167_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0167_ip a JOIN t2_tc_41_conv_0167_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0167-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0168-CP
-- Conversion probe: JSON-2-TEXT
-- Type: JSON -> LONGTEXT CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: JSON -> LONGTEXT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=7f07049b209d conv_probe=JSON-2-TEXT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0168_cp, t2_tc_41_conv_0168_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0168_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0168_cp (target) VALUES (CAST('{"a":1}' AS JSON));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0168_cp MODIFY target LONGTEXT CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: JSON
CREATE TABLE t2_tc_41_conv_0168_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target JSON,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0168_cp (target) VALUES (CAST('{"a":1}' AS JSON));
SELECT 'TC-41-CONV-0168-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0168_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0168_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0168_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0168_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0168_cp a JOIN t2_tc_41_conv_0168_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0168-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0169-DF
-- Conversion probe: TEXT-2-JSON
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: default, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据是合法 JSON）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a007070fbe8e conv_probe=TEXT-2-JSON conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0169_df, t2_tc_41_conv_0169_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0169_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0169_df (target) VALUES ('{"a":1}');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0169_df MODIFY target JSON;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0169_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0169_df (target) VALUES ('{"a":1}');
SELECT 'TC-41-CONV-0169-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0169_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0169_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0169_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0169_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0169_df a JOIN t2_tc_41_conv_0169_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0169-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0170-IT
-- Conversion probe: TEXT-2-JSON
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: instant, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据是合法 JSON）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a82154ec0b15 conv_probe=TEXT-2-JSON conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0170_it, t2_tc_41_conv_0170_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0170_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0170_it (target) VALUES ('{"a":1}');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0170_it MODIFY target JSON, ALGORITHM=INSTANT;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0170_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0170_it (target) VALUES ('{"a":1}');
SELECT 'TC-41-CONV-0170-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0170_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0170_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0170_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0170_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0170_it a JOIN t2_tc_41_conv_0170_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0170-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0171-IP
-- Conversion probe: TEXT-2-JSON
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: inplace, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据是合法 JSON）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1d50cd057a65 conv_probe=TEXT-2-JSON conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0171_ip, t2_tc_41_conv_0171_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0171_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0171_ip (target) VALUES ('{"a":1}');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0171_ip MODIFY target JSON, ALGORITHM=INPLACE;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0171_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0171_ip (target) VALUES ('{"a":1}');
SELECT 'TC-41-CONV-0171-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0171_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0171_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0171_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0171_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0171_ip a JOIN t2_tc_41_conv_0171_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0171-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0172-CP
-- Conversion probe: TEXT-2-JSON
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: copy, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据是合法 JSON）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=4ead8e9a51b7 conv_probe=TEXT-2-JSON conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0172_cp, t2_tc_41_conv_0172_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0172_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0172_cp (target) VALUES ('{"a":1}');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0172_cp MODIFY target JSON, ALGORITHM=COPY;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0172_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0172_cp (target) VALUES ('{"a":1}');
SELECT 'TC-41-CONV-0172-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0172_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0172_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0172_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0172_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0172_cp a JOIN t2_tc_41_conv_0172_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0172-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0173-DF
-- Conversion probe: TEXT-2-JSON-BAD
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: default, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据非法，必须拒绝）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e8499b30a046 conv_probe=TEXT-2-JSON-BAD conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0173_df, t2_tc_41_conv_0173_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0173_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0173_df (target) VALUES ('not-json');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0173_df MODIFY target JSON;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0173_df (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0173_df (target) VALUES ('not-json');
SELECT 'TC-41-CONV-0173-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0173_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0173_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0173_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0173_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0173_df a JOIN t2_tc_41_conv_0173_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0173-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0174-IT
-- Conversion probe: TEXT-2-JSON-BAD
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: instant, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据非法，必须拒绝）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=6f2d363739b4 conv_probe=TEXT-2-JSON-BAD conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0174_it, t2_tc_41_conv_0174_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0174_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0174_it (target) VALUES ('not-json');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0174_it MODIFY target JSON, ALGORITHM=INSTANT;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0174_it (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0174_it (target) VALUES ('not-json');
SELECT 'TC-41-CONV-0174-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0174_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0174_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0174_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0174_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0174_it a JOIN t2_tc_41_conv_0174_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0174-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0175-IP
-- Conversion probe: TEXT-2-JSON-BAD
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: inplace, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据非法，必须拒绝）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=77a54d24633e conv_probe=TEXT-2-JSON-BAD conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0175_ip, t2_tc_41_conv_0175_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0175_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0175_ip (target) VALUES ('not-json');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0175_ip MODIFY target JSON, ALGORITHM=INPLACE;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0175_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0175_ip (target) VALUES ('not-json');
SELECT 'TC-41-CONV-0175-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0175_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0175_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0175_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0175_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0175_ip a JOIN t2_tc_41_conv_0175_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0175-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0176-CP
-- Conversion probe: TEXT-2-JSON-BAD
-- Type: LONGTEXT CHARACTER SET utf8mb4 -> JSON, Algorithm: copy, Expected: MEASURE
-- Probe note: LONGTEXT -> JSON（数据非法，必须拒绝）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=5081b11b7ff9 conv_probe=TEXT-2-JSON-BAD conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0176_cp, t2_tc_41_conv_0176_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0176_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0176_cp (target) VALUES ('not-json');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0176_cp MODIFY target JSON, ALGORITHM=COPY;
-- Oracle table: LONGTEXT CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0176_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target LONGTEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0176_cp (target) VALUES ('not-json');
SELECT 'TC-41-CONV-0176-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0176_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0176_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0176_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0176_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0176_cp a JOIN t2_tc_41_conv_0176_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0176-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0177-DF
-- Conversion probe: GEO-2-POINT
-- Type: GEOMETRY -> POINT, Algorithm: default, Expected: MEASURE
-- Probe note: GEOMETRY -> POINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=68d3c4b500a2 conv_probe=GEO-2-POINT conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0177_df, t2_tc_41_conv_0177_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0177_df (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0177_df (target) VALUES (ST_GeomFromText('POINT(1 1)'));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0177_df MODIFY target POINT;
-- Oracle table: GEOMETRY
CREATE TABLE t2_tc_41_conv_0177_df (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0177_df (target) VALUES (ST_GeomFromText('POINT(1 1)'));
SELECT 'TC-41-CONV-0177-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0177_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0177_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0177_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0177_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0177_df a JOIN t2_tc_41_conv_0177_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0177-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0178-IT
-- Conversion probe: GEO-2-POINT
-- Type: GEOMETRY -> POINT, Algorithm: instant, Expected: MEASURE
-- Probe note: GEOMETRY -> POINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=71b0f44b8b62 conv_probe=GEO-2-POINT conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0178_it, t2_tc_41_conv_0178_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0178_it (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0178_it (target) VALUES (ST_GeomFromText('POINT(1 1)'));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0178_it MODIFY target POINT, ALGORITHM=INSTANT;
-- Oracle table: GEOMETRY
CREATE TABLE t2_tc_41_conv_0178_it (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0178_it (target) VALUES (ST_GeomFromText('POINT(1 1)'));
SELECT 'TC-41-CONV-0178-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0178_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0178_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0178_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0178_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0178_it a JOIN t2_tc_41_conv_0178_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0178-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0179-IP
-- Conversion probe: GEO-2-POINT
-- Type: GEOMETRY -> POINT, Algorithm: inplace, Expected: MEASURE
-- Probe note: GEOMETRY -> POINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=143062e747cc conv_probe=GEO-2-POINT conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0179_ip, t2_tc_41_conv_0179_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0179_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0179_ip (target) VALUES (ST_GeomFromText('POINT(1 1)'));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0179_ip MODIFY target POINT, ALGORITHM=INPLACE;
-- Oracle table: GEOMETRY
CREATE TABLE t2_tc_41_conv_0179_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0179_ip (target) VALUES (ST_GeomFromText('POINT(1 1)'));
SELECT 'TC-41-CONV-0179-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0179_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0179_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0179_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0179_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0179_ip a JOIN t2_tc_41_conv_0179_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0179-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0180-CP
-- Conversion probe: GEO-2-POINT
-- Type: GEOMETRY -> POINT, Algorithm: copy, Expected: MEASURE
-- Probe note: GEOMETRY -> POINT
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=c0b9d2528c71 conv_probe=GEO-2-POINT conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0180_cp, t2_tc_41_conv_0180_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0180_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0180_cp (target) VALUES (ST_GeomFromText('POINT(1 1)'));
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0180_cp MODIFY target POINT, ALGORITHM=COPY;
-- Oracle table: GEOMETRY
CREATE TABLE t2_tc_41_conv_0180_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target GEOMETRY,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0180_cp (target) VALUES (ST_GeomFromText('POINT(1 1)'));
SELECT 'TC-41-CONV-0180-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0180_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0180_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0180_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0180_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0180_cp a JOIN t2_tc_41_conv_0180_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0180-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0181-DF
-- Conversion probe: CS-L1-2-U4
-- Type: VARCHAR(10) CHARACTER SET latin1 -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: default, Expected: MEASURE
-- Probe note: latin1 -> utf8mb4 同时扩容
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=3130418a2867 conv_probe=CS-L1-2-U4 conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0181_df, t2_tc_41_conv_0181_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0181_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0181_df (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0181_df (target) VALUES ('a\u00e9');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0181_df MODIFY target VARCHAR(20) CHARACTER SET utf8mb4;
-- Oracle table: VARCHAR(10) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0181_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0181_df (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0181_df (target) VALUES ('a\u00e9');
SELECT 'TC-41-CONV-0181-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0181_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0181_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0181_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0181_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0181_df a JOIN t2_tc_41_conv_0181_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0181-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0182-IT
-- Conversion probe: CS-L1-2-U4
-- Type: VARCHAR(10) CHARACTER SET latin1 -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: instant, Expected: MEASURE
-- Probe note: latin1 -> utf8mb4 同时扩容
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=1ac225e3cca5 conv_probe=CS-L1-2-U4 conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0182_it, t2_tc_41_conv_0182_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0182_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0182_it (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0182_it (target) VALUES ('a\u00e9');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0182_it MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(10) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0182_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0182_it (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0182_it (target) VALUES ('a\u00e9');
SELECT 'TC-41-CONV-0182-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0182_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0182_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0182_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0182_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0182_it a JOIN t2_tc_41_conv_0182_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0182-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0183-IP
-- Conversion probe: CS-L1-2-U4
-- Type: VARCHAR(10) CHARACTER SET latin1 -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: inplace, Expected: MEASURE
-- Probe note: latin1 -> utf8mb4 同时扩容
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=03f31b13b725 conv_probe=CS-L1-2-U4 conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0183_ip, t2_tc_41_conv_0183_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0183_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0183_ip (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0183_ip (target) VALUES ('a\u00e9');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0183_ip MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(10) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0183_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0183_ip (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0183_ip (target) VALUES ('a\u00e9');
SELECT 'TC-41-CONV-0183-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0183_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0183_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0183_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0183_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0183_ip a JOIN t2_tc_41_conv_0183_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0183-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0184-CP
-- Conversion probe: CS-L1-2-U4
-- Type: VARCHAR(10) CHARACTER SET latin1 -> VARCHAR(20) CHARACTER SET utf8mb4, Algorithm: copy, Expected: MEASURE
-- Probe note: latin1 -> utf8mb4 同时扩容
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=8497cc9a13fe conv_probe=CS-L1-2-U4 conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0184_cp, t2_tc_41_conv_0184_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0184_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0184_cp (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0184_cp (target) VALUES ('a\u00e9');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0184_cp MODIFY target VARCHAR(20) CHARACTER SET utf8mb4, ALGORITHM=COPY;
-- Oracle table: VARCHAR(10) CHARACTER SET latin1
CREATE TABLE t2_tc_41_conv_0184_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(10) CHARACTER SET latin1,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0184_cp (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0184_cp (target) VALUES ('a\u00e9');
SELECT 'TC-41-CONV-0184-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0184_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0184_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0184_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0184_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0184_cp a JOIN t2_tc_41_conv_0184_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0184-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0185-DF
-- Conversion probe: CS-U4-SHRINK-CS
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> VARCHAR(20) CHARACTER SET latin1, Algorithm: default, Expected: MEASURE
-- Probe note: utf8mb4 -> latin1（长度不变，只改字符集）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=8c47c16e8e8b conv_probe=CS-U4-SHRINK-CS conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0185_df, t2_tc_41_conv_0185_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0185_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0185_df (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0185_df MODIFY target VARCHAR(20) CHARACTER SET latin1;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0185_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0185_df (target) VALUES ('abc');
SELECT 'TC-41-CONV-0185-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0185_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0185_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0185_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0185_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0185_df a JOIN t2_tc_41_conv_0185_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0185-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0186-IT
-- Conversion probe: CS-U4-SHRINK-CS
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> VARCHAR(20) CHARACTER SET latin1, Algorithm: instant, Expected: MEASURE
-- Probe note: utf8mb4 -> latin1（长度不变，只改字符集）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=648c323947d5 conv_probe=CS-U4-SHRINK-CS conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0186_it, t2_tc_41_conv_0186_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0186_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0186_it (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0186_it MODIFY target VARCHAR(20) CHARACTER SET latin1, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0186_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0186_it (target) VALUES ('abc');
SELECT 'TC-41-CONV-0186-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0186_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0186_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0186_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0186_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0186_it a JOIN t2_tc_41_conv_0186_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0186-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0187-IP
-- Conversion probe: CS-U4-SHRINK-CS
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> VARCHAR(20) CHARACTER SET latin1, Algorithm: inplace, Expected: MEASURE
-- Probe note: utf8mb4 -> latin1（长度不变，只改字符集）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=dce9dbd70718 conv_probe=CS-U4-SHRINK-CS conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0187_ip, t2_tc_41_conv_0187_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0187_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0187_ip (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0187_ip MODIFY target VARCHAR(20) CHARACTER SET latin1, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0187_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0187_ip (target) VALUES ('abc');
SELECT 'TC-41-CONV-0187-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0187_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0187_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0187_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0187_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0187_ip a JOIN t2_tc_41_conv_0187_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0187-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0188-CP
-- Conversion probe: CS-U4-SHRINK-CS
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 -> VARCHAR(20) CHARACTER SET latin1, Algorithm: copy, Expected: MEASURE
-- Probe note: utf8mb4 -> latin1（长度不变，只改字符集）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=d65582df7751 conv_probe=CS-U4-SHRINK-CS conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0188_cp, t2_tc_41_conv_0188_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0188_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0188_cp (target) VALUES ('abc');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0188_cp MODIFY target VARCHAR(20) CHARACTER SET latin1, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4
CREATE TABLE t2_tc_41_conv_0188_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0188_cp (target) VALUES ('abc');
SELECT 'TC-41-CONV-0188-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0188_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0188_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0188_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0188_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0188_cp a JOIN t2_tc_41_conv_0188_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0188-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0189-DF
-- Conversion probe: CO-GENERAL-2-BIN
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, Algorithm: default, Expected: MEASURE
-- Probe note: 改排序规则为区分大小写（影响唯一索引与比较语义）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=441ab950711c conv_probe=CO-GENERAL-2-BIN conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0189_df, t2_tc_41_conv_0189_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0189_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0189_df (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0189_df (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0189_df MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
CREATE TABLE t2_tc_41_conv_0189_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0189_df (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0189_df (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0189-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0189_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0189_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0189_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0189_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0189_df a JOIN t2_tc_41_conv_0189_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0189-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0190-IT
-- Conversion probe: CO-GENERAL-2-BIN
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, Algorithm: instant, Expected: MEASURE
-- Probe note: 改排序规则为区分大小写（影响唯一索引与比较语义）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=6709e9d6b4f7 conv_probe=CO-GENERAL-2-BIN conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0190_it, t2_tc_41_conv_0190_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0190_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0190_it (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0190_it (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0190_it MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
CREATE TABLE t2_tc_41_conv_0190_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0190_it (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0190_it (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0190-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0190_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0190_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0190_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0190_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0190_it a JOIN t2_tc_41_conv_0190_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0190-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0191-IP
-- Conversion probe: CO-GENERAL-2-BIN
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, Algorithm: inplace, Expected: MEASURE
-- Probe note: 改排序规则为区分大小写（影响唯一索引与比较语义）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=cd62a707edaa conv_probe=CO-GENERAL-2-BIN conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0191_ip, t2_tc_41_conv_0191_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0191_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0191_ip (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0191_ip (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0191_ip MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
CREATE TABLE t2_tc_41_conv_0191_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0191_ip (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0191_ip (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0191-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0191_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0191_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0191_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0191_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0191_ip a JOIN t2_tc_41_conv_0191_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0191-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0192-CP
-- Conversion probe: CO-GENERAL-2-BIN
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, Algorithm: copy, Expected: MEASURE
-- Probe note: 改排序规则为区分大小写（影响唯一索引与比较语义）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=00b55fd70e8e conv_probe=CO-GENERAL-2-BIN conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0192_cp, t2_tc_41_conv_0192_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0192_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0192_cp (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0192_cp (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0192_cp MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
CREATE TABLE t2_tc_41_conv_0192_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0192_cp (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0192_cp (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0192-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0192_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0192_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0192_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0192_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0192_cp a JOIN t2_tc_41_conv_0192_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0192-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0193-DF
-- Conversion probe: CO-BIN-2-AI
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, Algorithm: default, Expected: MEASURE
-- Probe note: 区分大小写 -> 不区分（唯一索引可能冲突）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=485cb52c2541 conv_probe=CO-BIN-2-AI conv_algo=default
DROP TABLE IF EXISTS t1_tc_41_conv_0193_df, t2_tc_41_conv_0193_df;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0193_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0193_df (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0193_df (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0193_df MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin
CREATE TABLE t2_tc_41_conv_0193_df (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0193_df (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0193_df (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0193-DF' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0193_df
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0193_df)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0193_df
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0193_df)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0193_df a JOIN t2_tc_41_conv_0193_df b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0193-DF#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0194-IT
-- Conversion probe: CO-BIN-2-AI
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, Algorithm: instant, Expected: MEASURE
-- Probe note: 区分大小写 -> 不区分（唯一索引可能冲突）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=a642398cc340 conv_probe=CO-BIN-2-AI conv_algo=instant
DROP TABLE IF EXISTS t1_tc_41_conv_0194_it, t2_tc_41_conv_0194_it;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0194_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0194_it (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0194_it (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0194_it MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, ALGORITHM=INSTANT;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin
CREATE TABLE t2_tc_41_conv_0194_it (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0194_it (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0194_it (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0194-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0194_it
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0194_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0194_it
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0194_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0194_it a JOIN t2_tc_41_conv_0194_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0194-IT#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0195-IP
-- Conversion probe: CO-BIN-2-AI
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, Algorithm: inplace, Expected: MEASURE
-- Probe note: 区分大小写 -> 不区分（唯一索引可能冲突）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=64a3a07df6c1 conv_probe=CO-BIN-2-AI conv_algo=inplace
DROP TABLE IF EXISTS t1_tc_41_conv_0195_ip, t2_tc_41_conv_0195_ip;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0195_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0195_ip (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0195_ip (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0195_ip MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, ALGORITHM=INPLACE;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin
CREATE TABLE t2_tc_41_conv_0195_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0195_ip (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0195_ip (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0195-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0195_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0195_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0195_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0195_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0195_ip a JOIN t2_tc_41_conv_0195_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0195-IP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

-- Test Case: TC-41-CONV-0196-CP
-- Conversion probe: CO-BIN-2-AI
-- Type: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin -> VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, Algorithm: copy, Expected: MEASURE
-- Probe note: 区分大小写 -> 不区分（唯一索引可能冲突）
-- Golden: MEASURE (未冻结，本轮只记录实测结果)
-- @expect alter=MEASURE build=SUCCESS assertions=2 alter_sha=e115b3381843 conv_probe=CO-BIN-2-AI conv_algo=copy
DROP TABLE IF EXISTS t1_tc_41_conv_0196_cp, t2_tc_41_conv_0196_cp;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_41_conv_0196_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t1_tc_41_conv_0196_cp (target) VALUES ('abc');
INSERT INTO t1_tc_41_conv_0196_cp (target) VALUES ('ABC');
-- ALTER expected MEASURE
ALTER TABLE t1_tc_41_conv_0196_cp MODIFY target VARCHAR(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci, ALGORITHM=COPY;
-- Oracle table: VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin
CREATE TABLE t2_tc_41_conv_0196_cp (
  id INT NOT NULL AUTO_INCREMENT,
  target VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,
  pad VARCHAR(20) DEFAULT 'pad', PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO t2_tc_41_conv_0196_cp (target) VALUES ('abc');
INSERT INTO t2_tc_41_conv_0196_cp (target) VALUES ('ABC');
SELECT 'TC-41-CONV-0196-CP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_41_conv_0196_cp
   WHERE id NOT IN (SELECT id FROM t2_tc_41_conv_0196_cp)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_41_conv_0196_cp
   WHERE id NOT IN (SELECT id FROM t1_tc_41_conv_0196_cp)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_41_conv_0196_cp a JOIN t2_tc_41_conv_0196_cp b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-41-CONV-0196-CP#META' AS test_id, 'PASS' AS result, 'MEASURE mode: column_type not asserted' AS mismatch;

