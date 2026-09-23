-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 8d806086fd8b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 28: 特殊模式 (连续ALTER + 多列ALTER)

-- Test Case: TC-28-SPE-0001-IT
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint alter_sha=a1a5463cd5db alter_sha=089dee523901 alter_sha=193ecaca4002 alter_sha=143a564ce971
DROP TABLE IF EXISTS t1_tc_28_spe_0001_it, t2_tc_28_spe_0001_it;
CREATE TABLE t1_tc_28_spe_0001_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (-128);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (0);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (1);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_28_spe_0001_it MODIFY target SMALLINT, ALGORITHM=instant;
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (128);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_28_spe_0001_it MODIFY target MEDIUMINT, ALGORITHM=instant;
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (32768);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_28_spe_0001_it MODIFY target INT, ALGORITHM=instant;
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (8388608);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_28_spe_0001_it MODIFY target BIGINT, ALGORITHM=instant;
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (2147483648);
INSERT INTO t1_tc_28_spe_0001_it (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_28_spe_0001_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (-128);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (0);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (1);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (127);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (128);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (32767);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (32768);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (8388607);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (8388608);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (2147483647);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (2147483648);
INSERT INTO t2_tc_28_spe_0001_it (target) VALUES (9223372036854775807);
SELECT 'TC-28-SPE-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_28_spe_0001_it
   WHERE id NOT IN (SELECT id FROM t2_tc_28_spe_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_28_spe_0001_it
   WHERE id NOT IN (SELECT id FROM t1_tc_28_spe_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_28_spe_0001_it a JOIN t2_tc_28_spe_0001_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-28-SPE-0001-IT#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0001_it' AND column_name='target';

-- Test Case: TC-28-SPE-0002-IP
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint alter_sha=88f0f6bdba55 alter_sha=e52a7f683ea9 alter_sha=87ae1830c9bb alter_sha=d468fc4fcc64
DROP TABLE IF EXISTS t1_tc_28_spe_0002_ip, t2_tc_28_spe_0002_ip;
CREATE TABLE t1_tc_28_spe_0002_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (-128);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (0);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (1);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_28_spe_0002_ip MODIFY target SMALLINT, ALGORITHM=inplace;
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (128);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_28_spe_0002_ip MODIFY target MEDIUMINT, ALGORITHM=inplace;
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (32768);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_28_spe_0002_ip MODIFY target INT, ALGORITHM=inplace;
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (8388608);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_28_spe_0002_ip MODIFY target BIGINT, ALGORITHM=inplace;
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (2147483648);
INSERT INTO t1_tc_28_spe_0002_ip (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_28_spe_0002_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (-128);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (0);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (1);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (127);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (128);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (32767);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (32768);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (8388607);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (8388608);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (2147483647);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (2147483648);
INSERT INTO t2_tc_28_spe_0002_ip (target) VALUES (9223372036854775807);
SELECT 'TC-28-SPE-0002-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_28_spe_0002_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_28_spe_0002_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_28_spe_0002_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_28_spe_0002_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_28_spe_0002_ip a JOIN t2_tc_28_spe_0002_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-28-SPE-0002-IP#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0002_ip' AND column_name='target';

-- Test Case: TC-28-SPE-0003-IT
-- Multi-column ALTER, Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=8 alter_sha=061aca3d46fa
DROP TABLE IF EXISTS t1_tc_28_spe_0003_it, t2_tc_28_spe_0003_it;
CREATE TABLE t1_tc_28_spe_0003_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4,
  col_decimal DECIMAL(10,2),
  col_binary BINARY(10),
  col_blob BLOB,
  col_bit BIT(8)
) ENGINE=InnoDB;
INSERT INTO t1_tc_28_spe_0003_it (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (42, 'hello', 'world', 1.23, 0x00000000000000000000, 0x000102, b'10101010');
ALTER TABLE t1_tc_28_spe_0003_it MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, MODIFY col_decimal DECIMAL(20,2), MODIFY col_binary BINARY(20), MODIFY col_blob MEDIUMBLOB, MODIFY col_bit BIT(16), ALGORITHM=instant;
INSERT INTO t1_tc_28_spe_0003_it (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (2147483648, 'hello_world_long', 'extended_string', 999.99, 0x0000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, b'1111111111111111');
CREATE TABLE t2_tc_28_spe_0003_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4,
  col_decimal DECIMAL(20,2),
  col_binary BINARY(20),
  col_blob MEDIUMBLOB,
  col_bit BIT(16)
) ENGINE=InnoDB;
INSERT INTO t2_tc_28_spe_0003_it (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (42, 'hello', 'world', 1.23, 0x00000000000000000000, 0x000102, b'10101010');
INSERT INTO t2_tc_28_spe_0003_it (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (2147483648, 'hello_world_long', 'extended_string', 999.99, 0x0000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, b'1111111111111111');
SELECT 'TC-28-SPE-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_28_spe_0003_it
   WHERE id NOT IN (SELECT id FROM t2_tc_28_spe_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_28_spe_0003_it
   WHERE id NOT IN (SELECT id FROM t1_tc_28_spe_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_28_spe_0003_it a JOIN t2_tc_28_spe_0003_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar AND a.col_decimal <=> b.col_decimal AND a.col_binary <=> b.col_binary AND a.col_blob <=> b.col_blob AND a.col_bit <=> b.col_bit)
) AS mismatches;
SELECT 'TC-28-SPE-0003-IT#META_COL_INT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_int';
SELECT 'TC-28-SPE-0003-IT#META_COL_CHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='char(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=char(20) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_char';
SELECT 'TC-28-SPE-0003-IT#META_COL_VARCHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=4,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=4]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_varchar';
SELECT 'TC-28-SPE-0003-IT#META_COL_DECIMAL' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(20,2)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=5,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=decimal(20,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=5]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_decimal';
SELECT 'TC-28-SPE-0003-IT#META_COL_BINARY' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=6,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=6]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_binary';
SELECT 'TC-28-SPE-0003-IT#META_COL_BLOB' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='mediumblob'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=7,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=mediumblob nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=7]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_blob';
SELECT 'TC-28-SPE-0003-IT#META_COL_BIT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bit(16)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=8,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bit(16) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=8]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0003_it' AND column_name='col_bit';

-- Test Case: TC-28-SPE-0004-IP
-- Multi-column ALTER, Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=8 alter_sha=5196fc37a623
DROP TABLE IF EXISTS t1_tc_28_spe_0004_ip, t2_tc_28_spe_0004_ip;
CREATE TABLE t1_tc_28_spe_0004_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4,
  col_decimal DECIMAL(10,2),
  col_binary BINARY(10),
  col_blob BLOB,
  col_bit BIT(8)
) ENGINE=InnoDB;
INSERT INTO t1_tc_28_spe_0004_ip (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (42, 'hello', 'world', 1.23, 0x00000000000000000000, 0x000102, b'10101010');
ALTER TABLE t1_tc_28_spe_0004_ip MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, MODIFY col_decimal DECIMAL(20,2), MODIFY col_binary BINARY(20), MODIFY col_blob MEDIUMBLOB, MODIFY col_bit BIT(16), ALGORITHM=inplace;
INSERT INTO t1_tc_28_spe_0004_ip (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (2147483648, 'hello_world_long', 'extended_string', 999.99, 0x0000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, b'1111111111111111');
CREATE TABLE t2_tc_28_spe_0004_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4,
  col_decimal DECIMAL(20,2),
  col_binary BINARY(20),
  col_blob MEDIUMBLOB,
  col_bit BIT(16)
) ENGINE=InnoDB;
INSERT INTO t2_tc_28_spe_0004_ip (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (42, 'hello', 'world', 1.23, 0x00000000000000000000, 0x000102, b'10101010');
INSERT INTO t2_tc_28_spe_0004_ip (col_int, col_char, col_varchar, col_decimal, col_binary, col_blob, col_bit)
VALUES (2147483648, 'hello_world_long', 'extended_string', 999.99, 0x0000000000000000000000000000000000000000, 0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, b'1111111111111111');
SELECT 'TC-28-SPE-0004-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_28_spe_0004_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_28_spe_0004_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_28_spe_0004_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_28_spe_0004_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_28_spe_0004_ip a JOIN t2_tc_28_spe_0004_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar AND a.col_decimal <=> b.col_decimal AND a.col_binary <=> b.col_binary AND a.col_blob <=> b.col_blob AND a.col_bit <=> b.col_bit)
) AS mismatches;
SELECT 'TC-28-SPE-0004-IP#META_COL_INT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_int';
SELECT 'TC-28-SPE-0004-IP#META_COL_CHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='char(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=char(20) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_char';
SELECT 'TC-28-SPE-0004-IP#META_COL_VARCHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=4,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=4]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_varchar';
SELECT 'TC-28-SPE-0004-IP#META_COL_DECIMAL' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='decimal(20,2)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=5,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=decimal(20,2) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=5]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_decimal';
SELECT 'TC-28-SPE-0004-IP#META_COL_BINARY' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='binary(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=6,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=binary(20) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=6]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_binary';
SELECT 'TC-28-SPE-0004-IP#META_COL_BLOB' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='mediumblob'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=7,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=mediumblob nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=7]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_blob';
SELECT 'TC-28-SPE-0004-IP#META_COL_BIT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bit(16)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=8,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bit(16) nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=8]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_28_spe_0004_ip' AND column_name='col_bit';

