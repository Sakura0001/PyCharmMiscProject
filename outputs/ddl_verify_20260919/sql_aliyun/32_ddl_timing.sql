-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 0a9e21784c13   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 32: 秒级差分计时 (默认算法 vs 强制 COPY, 524288 行)

-- Test Case: TC-32-TMG-0001-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: TINYINT -> SMALLINT, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: INT-S-1-2
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=dd643ce755d1 column_type=smallint
DROP TABLE IF EXISTS t1_tc_32_tmg_0001_xx, t2_tc_32_tmg_0001_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0001_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TINYINT) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0001_xx (target) VALUES (-128);
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
INSERT INTO t1_tc_32_tmg_0001_xx (target) SELECT target FROM t1_tc_32_tmg_0001_xx;
ANALYZE TABLE t1_tc_32_tmg_0001_xx;
CREATE TABLE t2_tc_32_tmg_0001_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TINYINT) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0001_xx (target) VALUES (-128);
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
INSERT INTO t2_tc_32_tmg_0001_xx (target) SELECT target FROM t2_tc_32_tmg_0001_xx;
ANALYZE TABLE t2_tc_32_tmg_0001_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0001_xx MODIFY target SMALLINT;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0001_xx MODIFY target SMALLINT, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0001-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0001-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='smallint'
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
              'want[type=smallint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0001_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0002-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: SMALLINT -> MEDIUMINT, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: INT-S-2-3
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=34fa776d163d column_type=mediumint
DROP TABLE IF EXISTS t1_tc_32_tmg_0002_xx, t2_tc_32_tmg_0002_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0002_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target SMALLINT) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0002_xx (target) VALUES (-32768);
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
INSERT INTO t1_tc_32_tmg_0002_xx (target) SELECT target FROM t1_tc_32_tmg_0002_xx;
ANALYZE TABLE t1_tc_32_tmg_0002_xx;
CREATE TABLE t2_tc_32_tmg_0002_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target SMALLINT) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0002_xx (target) VALUES (-32768);
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
INSERT INTO t2_tc_32_tmg_0002_xx (target) SELECT target FROM t2_tc_32_tmg_0002_xx;
ANALYZE TABLE t2_tc_32_tmg_0002_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0002_xx MODIFY target MEDIUMINT;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0002_xx MODIFY target MEDIUMINT, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0002-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0002-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='mediumint'
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
              'want[type=mediumint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0002_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0003-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: MEDIUMINT -> BIGINT, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: INT-S-3-5
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=6000c63d8416 column_type=bigint
DROP TABLE IF EXISTS t1_tc_32_tmg_0003_xx, t2_tc_32_tmg_0003_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0003_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target MEDIUMINT) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0003_xx (target) VALUES (-8388608);
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
INSERT INTO t1_tc_32_tmg_0003_xx (target) SELECT target FROM t1_tc_32_tmg_0003_xx;
ANALYZE TABLE t1_tc_32_tmg_0003_xx;
CREATE TABLE t2_tc_32_tmg_0003_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target MEDIUMINT) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0003_xx (target) VALUES (-8388608);
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
INSERT INTO t2_tc_32_tmg_0003_xx (target) SELECT target FROM t2_tc_32_tmg_0003_xx;
ANALYZE TABLE t2_tc_32_tmg_0003_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0003_xx MODIFY target BIGINT;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0003_xx MODIFY target BIGINT, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0003-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0003-XX#META' AS test_id,
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
              'want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0003_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0004-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: TINYINT UNSIGNED -> INT UNSIGNED, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: INT-U-1-4
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=39acc2c4f954 column_type=int unsigned
DROP TABLE IF EXISTS t1_tc_32_tmg_0004_xx, t2_tc_32_tmg_0004_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0004_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TINYINT UNSIGNED) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0004_xx (target) VALUES (0);
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
INSERT INTO t1_tc_32_tmg_0004_xx (target) SELECT target FROM t1_tc_32_tmg_0004_xx;
ANALYZE TABLE t1_tc_32_tmg_0004_xx;
CREATE TABLE t2_tc_32_tmg_0004_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target TINYINT UNSIGNED) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0004_xx (target) VALUES (0);
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
INSERT INTO t2_tc_32_tmg_0004_xx (target) SELECT target FROM t2_tc_32_tmg_0004_xx;
ANALYZE TABLE t2_tc_32_tmg_0004_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0004_xx MODIFY target INT UNSIGNED;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0004_xx MODIFY target INT UNSIGNED, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0004-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0004-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='int unsigned'
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
              'want[type=int unsigned nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0004_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0005-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: SMALLINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: INT-U-2-5
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=9cfef3a4ad7b column_type=bigint unsigned
DROP TABLE IF EXISTS t1_tc_32_tmg_0005_xx, t2_tc_32_tmg_0005_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0005_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target SMALLINT UNSIGNED) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0005_xx (target) VALUES (0);
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
INSERT INTO t1_tc_32_tmg_0005_xx (target) SELECT target FROM t1_tc_32_tmg_0005_xx;
ANALYZE TABLE t1_tc_32_tmg_0005_xx;
CREATE TABLE t2_tc_32_tmg_0005_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target SMALLINT UNSIGNED) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0005_xx (target) VALUES (0);
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
INSERT INTO t2_tc_32_tmg_0005_xx (target) SELECT target FROM t2_tc_32_tmg_0005_xx;
ANALYZE TABLE t2_tc_32_tmg_0005_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0005_xx MODIFY target BIGINT UNSIGNED;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0005_xx MODIFY target BIGINT UNSIGNED, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0005-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0005-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint unsigned'
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
              'want[type=bigint unsigned nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0005_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0006-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: CHAR(1) -> CHAR(2), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: CHAR-01
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=1550b3b7e5ab column_type=char(2)
DROP TABLE IF EXISTS t1_tc_32_tmg_0006_xx, t2_tc_32_tmg_0006_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0006_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target CHAR(1) CHARACTER SET latin1) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0006_xx (target) VALUES ('');
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
INSERT INTO t1_tc_32_tmg_0006_xx (target) SELECT target FROM t1_tc_32_tmg_0006_xx;
ANALYZE TABLE t1_tc_32_tmg_0006_xx;
CREATE TABLE t2_tc_32_tmg_0006_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target CHAR(1) CHARACTER SET latin1) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0006_xx (target) VALUES ('');
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
INSERT INTO t2_tc_32_tmg_0006_xx (target) SELECT target FROM t2_tc_32_tmg_0006_xx;
ANALYZE TABLE t2_tc_32_tmg_0006_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0006_xx MODIFY target CHAR(2) CHARACTER SET latin1;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0006_xx MODIFY target CHAR(2) CHARACTER SET latin1, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0006-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0006-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='char(2)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
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
              'want[type=char(2) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0006_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0007-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: VARCHAR(254) -> VARCHAR(255), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: VC-02
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=8ccefad229d8 column_type=varchar(255)
DROP TABLE IF EXISTS t1_tc_32_tmg_0007_xx, t2_tc_32_tmg_0007_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0007_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARCHAR(254) CHARACTER SET latin1) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0007_xx (target) VALUES ('');
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
INSERT INTO t1_tc_32_tmg_0007_xx (target) SELECT target FROM t1_tc_32_tmg_0007_xx;
ANALYZE TABLE t1_tc_32_tmg_0007_xx;
CREATE TABLE t2_tc_32_tmg_0007_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARCHAR(254) CHARACTER SET latin1) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0007_xx (target) VALUES ('');
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
INSERT INTO t2_tc_32_tmg_0007_xx (target) SELECT target FROM t2_tc_32_tmg_0007_xx;
ANALYZE TABLE t2_tc_32_tmg_0007_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0007_xx MODIFY target VARCHAR(255) CHARACTER SET latin1;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0007_xx MODIFY target VARCHAR(255) CHARACTER SET latin1, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0007-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0007-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(255)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'latin1')
          AND (MAX(collation_name) <=> 'latin1_swedish_ci')
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
              'want[type=varchar(255) nullable=YES has_default=0 charset=latin1 collation=latin1_swedish_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0007_xx' AND column_name='target';

-- Test Case: TC-32-TMG-0008-XX
-- Timing: default-algorithm vs forced COPY, 524288 rows
-- Type: VARCHAR(64) -> VARCHAR(65), Algorithm: default_vs_copy, Expected: SUCCESS
-- Transition ID: VC-06
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=b26ad9751ec7 column_type=varchar(65)
DROP TABLE IF EXISTS t1_tc_32_tmg_0008_xx, t2_tc_32_tmg_0008_xx;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
CREATE TABLE t1_tc_32_tmg_0008_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARCHAR(64) CHARACTER SET utf8mb4) ENGINE=InnoDB;
INSERT INTO t1_tc_32_tmg_0008_xx (target) VALUES ('');
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
INSERT INTO t1_tc_32_tmg_0008_xx (target) SELECT target FROM t1_tc_32_tmg_0008_xx;
ANALYZE TABLE t1_tc_32_tmg_0008_xx;
CREATE TABLE t2_tc_32_tmg_0008_xx (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, target VARCHAR(64) CHARACTER SET utf8mb4) ENGINE=InnoDB;
INSERT INTO t2_tc_32_tmg_0008_xx (target) VALUES ('');
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
INSERT INTO t2_tc_32_tmg_0008_xx (target) SELECT target FROM t2_tc_32_tmg_0008_xx;
ANALYZE TABLE t2_tc_32_tmg_0008_xx;
SET @t0 = NOW(6);
ALTER TABLE t1_tc_32_tmg_0008_xx MODIFY target VARCHAR(65) CHARACTER SET utf8mb4;
SET @t1 = NOW(6);
SET @t2 = NOW(6);
ALTER TABLE t2_tc_32_tmg_0008_xx MODIFY target VARCHAR(65) CHARACTER SET utf8mb4, ALGORITHM=COPY;
SET @t3 = NOW(6);
SELECT 'TC-32-TMG-0008-XX#FAST_PATH' AS test_id,
       IF(TIMESTAMPDIFF(MICROSECOND,@t0,@t1) * 3 < TIMESTAMPDIFF(MICROSECOND,@t2,@t3)
          AND TIMESTAMPDIFF(MICROSECOND,@t0,@t1) < 2000000,'PASS','FAIL') AS result,
       CONCAT('default_us=',TIMESTAMPDIFF(MICROSECOND,@t0,@t1),' copy_us=',TIMESTAMPDIFF(MICROSECOND,@t2,@t3),' ratio=',ROUND(TIMESTAMPDIFF(MICROSECOND,@t2,@t3)/GREATEST(TIMESTAMPDIFF(MICROSECOND,@t0,@t1),1),1),' need_ratio>3 and default_us<2000000') AS mismatch;
SELECT 'TC-32-TMG-0008-XX#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(65)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
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
              'want[type=varchar(65) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_32_tmg_0008_xx' AND column_name='target';

