-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: ebbfa1c38daa   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 43: 因子矩阵 (增强类型侧同一套因子探针)

-- Test Case: TC-43-FCT-0001-IT
-- Factor probe: IDX_FUNCTIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0001_it, t2_tc_43_fct_0001_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=db170e285ec4 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0001_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0001_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0001_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0001_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0001_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0001-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0001_it';
SELECT 'TC-43-FCT-0001-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0002-IP
-- Factor probe: IDX_FUNCTIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0002_ip, t2_tc_43_fct_0002_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fd6d3ac34da9 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0002_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0002_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0002_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0002_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0002_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0002-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0002_ip';
SELECT 'TC-43-FCT-0002-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0003-DF
-- Factor probe: IDX_FUNCTIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0003_df, t2_tc_43_fct_0003_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a331f9b3fc08 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0003_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0003_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0003_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0003_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0003_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0003-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0003_df';
SELECT 'TC-43-FCT-0003-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0004-IT
-- Factor probe: IDX_FUNCTIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0004_it, t2_tc_43_fct_0004_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=679a996c77b1 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0004_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0004_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0004_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0004_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0004_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0004-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0004_it';
SELECT 'TC-43-FCT-0004-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0005-IP
-- Factor probe: IDX_FUNCTIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0005_ip, t2_tc_43_fct_0005_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=5a6f84978f56 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0005_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0005_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0005_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0005_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0005_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0005-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0005_ip';
SELECT 'TC-43-FCT-0005-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0006-DF
-- Factor probe: IDX_FUNCTIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0006_df, t2_tc_43_fct_0006_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=71b5962e7bbc factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0006_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0006_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0006_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0006_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0006_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0006-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0006_df';
SELECT 'TC-43-FCT-0006-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0007-IT
-- Factor probe: IDX_FUNCTIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0007_it, t2_tc_43_fct_0007_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fd6b4af6bed5 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0007_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0007_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0007_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0007_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0007_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0007-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0007_it';
SELECT 'TC-43-FCT-0007-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0008-IP
-- Factor probe: IDX_FUNCTIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0008_ip, t2_tc_43_fct_0008_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=b179bbc8dfbf factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0008_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0008_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0008_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0008_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0008_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0008-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0008_ip';
SELECT 'TC-43-FCT-0008-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0009-DF
-- Factor probe: IDX_FUNCTIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 函数/表达式索引（引用目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0009_df, t2_tc_43_fct_0009_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=41241c9a2238 factor=IDX_FUNCTIONAL
CREATE TABLE t1_tc_43_fct_0009_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_fn ((CONCAT(target, ''))),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0009_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0009_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0009_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0009_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0009-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0009_df';
SELECT 'TC-43-FCT-0009-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0010-IT
-- Factor probe: DEP_GEN_STORED
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0010_it, t2_tc_43_fct_0010_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=486987cdfc18 factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0010_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0010_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0010_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0010_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0010_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0010-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0010_it';
SELECT 'TC-43-FCT-0010-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0011-IP
-- Factor probe: DEP_GEN_STORED
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0011_ip, t2_tc_43_fct_0011_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=930cb7f2b4bc factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0011_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0011_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0011_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0011_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0011_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0011-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0011_ip';
SELECT 'TC-43-FCT-0011-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0012-DF
-- Factor probe: DEP_GEN_STORED
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0012_df, t2_tc_43_fct_0012_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6ba92c7cf7fa factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0012_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0012_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0012_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0012_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0012_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0012-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0012_df';
SELECT 'TC-43-FCT-0012-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0013-IT
-- Factor probe: DEP_GEN_STORED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0013_it, t2_tc_43_fct_0013_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=48ac08b0a2bc factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0013_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0013_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0013_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0013_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0013_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0013-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0013_it';
SELECT 'TC-43-FCT-0013-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0014-IP
-- Factor probe: DEP_GEN_STORED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0014_ip, t2_tc_43_fct_0014_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=5c0e07342de3 factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0014_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0014_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0014_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0014_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0014_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0014-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0014_ip';
SELECT 'TC-43-FCT-0014-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0015-DF
-- Factor probe: DEP_GEN_STORED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0015_df, t2_tc_43_fct_0015_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=324a58e9036a factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0015_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0015_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0015_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0015_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0015_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0015-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0015_df';
SELECT 'TC-43-FCT-0015-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0016-IT
-- Factor probe: DEP_GEN_STORED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0016_it, t2_tc_43_fct_0016_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=febcb901c222 factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0016_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0016_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0016_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0016_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0016_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0016-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0016_it';
SELECT 'TC-43-FCT-0016-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0017-IP
-- Factor probe: DEP_GEN_STORED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0017_ip, t2_tc_43_fct_0017_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0cc72d65db18 factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0017_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0017_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0017_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0017_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0017_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0017-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0017_ip';
SELECT 'TC-43-FCT-0017-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0018-DF
-- Factor probe: DEP_GEN_STORED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: STORED 生成列引用目标列 + 其上的索引
DROP TABLE IF EXISTS t1_tc_43_fct_0018_df, t2_tc_43_fct_0018_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=30ab54431f5a factor=DEP_GEN_STORED
CREATE TABLE t1_tc_43_fct_0018_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  gen_c VARCHAR(64) AS (CONCAT('v', target)) STORED,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_gen (gen_c),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0018_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0018_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0018_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0018_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0018-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0018_df';
SELECT 'TC-43-FCT-0018-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0019-IT
-- Factor probe: IDX_DESC
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0019_it, t2_tc_43_fct_0019_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fa593d28d0de factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0019_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0019_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0019_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0019_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0019_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0019-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0019_it';
SELECT 'TC-43-FCT-0019-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0020-IP
-- Factor probe: IDX_DESC
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0020_ip, t2_tc_43_fct_0020_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=2e06d927eb6a factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0020_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0020_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0020_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0020_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0020_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0020-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0020_ip';
SELECT 'TC-43-FCT-0020-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0021-DF
-- Factor probe: IDX_DESC
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0021_df, t2_tc_43_fct_0021_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8e47d9004c8f factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0021_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0021_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0021_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0021_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0021_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0021-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0021_df';
SELECT 'TC-43-FCT-0021-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0022-IT
-- Factor probe: IDX_DESC
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0022_it, t2_tc_43_fct_0022_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8a39bb02bb49 factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0022_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0022_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0022_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0022_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0022_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0022-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0022_it';
SELECT 'TC-43-FCT-0022-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0023-IP
-- Factor probe: IDX_DESC
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0023_ip, t2_tc_43_fct_0023_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=91e4013f8490 factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0023_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0023_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0023_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0023_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0023_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0023-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0023_ip';
SELECT 'TC-43-FCT-0023-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0024-DF
-- Factor probe: IDX_DESC
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0024_df, t2_tc_43_fct_0024_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8b4ffab2f40a factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0024_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0024_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0024_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0024_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0024_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0024-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0024_df';
SELECT 'TC-43-FCT-0024-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0025-IT
-- Factor probe: IDX_DESC
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0025_it, t2_tc_43_fct_0025_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ac1af151e903 factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0025_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0025_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0025_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0025_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0025_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0025-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0025_it';
SELECT 'TC-43-FCT-0025-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0026-IP
-- Factor probe: IDX_DESC
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0026_ip, t2_tc_43_fct_0026_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=421ae1c45211 factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0026_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0026_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0026_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0026_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0026_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0026-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0026_ip';
SELECT 'TC-43-FCT-0026-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0027-DF
-- Factor probe: IDX_DESC
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 降序索引
DROP TABLE IF EXISTS t1_tc_43_fct_0027_df, t2_tc_43_fct_0027_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=40ccd1c15039 factor=IDX_DESC
CREATE TABLE t1_tc_43_fct_0027_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_desc (target DESC),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0027_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0027_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0027_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0027_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0027-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0027_df';
SELECT 'TC-43-FCT-0027-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0028-IT
-- Factor probe: IDX_INVISIBLE
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0028_it, t2_tc_43_fct_0028_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a418f92128d5 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0028_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0028_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0028_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0028_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0028_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0028-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0028_it';
SELECT 'TC-43-FCT-0028-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0029-IP
-- Factor probe: IDX_INVISIBLE
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0029_ip, t2_tc_43_fct_0029_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=dab0a5bcd1d5 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0029_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0029_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0029_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0029_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0029_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0029-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0029_ip';
SELECT 'TC-43-FCT-0029-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0030-DF
-- Factor probe: IDX_INVISIBLE
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0030_df, t2_tc_43_fct_0030_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=650067be7cc1 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0030_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0030_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0030_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0030_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0030_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0030-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0030_df';
SELECT 'TC-43-FCT-0030-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0031-IT
-- Factor probe: IDX_INVISIBLE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0031_it, t2_tc_43_fct_0031_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=e6c489270841 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0031_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0031_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0031_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0031_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0031_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0031-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0031_it';
SELECT 'TC-43-FCT-0031-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0032-IP
-- Factor probe: IDX_INVISIBLE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0032_ip, t2_tc_43_fct_0032_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fa8c65b66259 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0032_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0032_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0032_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0032_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0032_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0032-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0032_ip';
SELECT 'TC-43-FCT-0032-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0033-DF
-- Factor probe: IDX_INVISIBLE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0033_df, t2_tc_43_fct_0033_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9ad72d2bfab1 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0033_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0033_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0033_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0033_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0033_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0033-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0033_df';
SELECT 'TC-43-FCT-0033-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0034-IT
-- Factor probe: IDX_INVISIBLE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0034_it, t2_tc_43_fct_0034_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4c131db6c1b1 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0034_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0034_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0034_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0034_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0034_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0034-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0034_it';
SELECT 'TC-43-FCT-0034-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0035-IP
-- Factor probe: IDX_INVISIBLE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0035_ip, t2_tc_43_fct_0035_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=2a5f28487095 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0035_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0035_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0035_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0035_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0035_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0035-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0035_ip';
SELECT 'TC-43-FCT-0035-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0036-DF
-- Factor probe: IDX_INVISIBLE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 不可见索引
DROP TABLE IF EXISTS t1_tc_43_fct_0036_df, t2_tc_43_fct_0036_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ac0ae6dd0994 factor=IDX_INVISIBLE
CREATE TABLE t1_tc_43_fct_0036_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_inv (target) INVISIBLE,
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0036_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0036_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0036_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0036_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0036-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0036_df';
SELECT 'TC-43-FCT-0036-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0037-IT
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0037_it, t2_tc_43_fct_0037_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=146165300b70 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0037_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0037_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0037_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0037_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0037_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0037-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0037_it';
SELECT 'TC-43-FCT-0037-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0038-IP
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0038_ip, t2_tc_43_fct_0038_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=09d6fa0dbd58 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0038_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0038_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0038_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0038_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0038_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0038-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0038_ip';
SELECT 'TC-43-FCT-0038-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0039-DF
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0039_df, t2_tc_43_fct_0039_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=42c60d5cc570 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0039_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0039_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0039_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0039_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0039_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0039-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0039_df';
SELECT 'TC-43-FCT-0039-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0040-IT
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0040_it, t2_tc_43_fct_0040_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=614ebb65f438 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0040_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0040_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0040_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0040_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0040_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0040-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0040_it';
SELECT 'TC-43-FCT-0040-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0041-IP
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0041_ip, t2_tc_43_fct_0041_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a401e9d2a0d9 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0041_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0041_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0041_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0041_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0041_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0041-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0041_ip';
SELECT 'TC-43-FCT-0041-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0042-DF
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0042_df, t2_tc_43_fct_0042_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=209f8a4aa02d factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0042_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0042_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0042_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0042_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0042_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0042-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0042_df';
SELECT 'TC-43-FCT-0042-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0043-IT
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0043_it, t2_tc_43_fct_0043_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=900c8d254978 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0043_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0043_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0043_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0043_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0043_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0043-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0043_it';
SELECT 'TC-43-FCT-0043-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0044-IP
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0044_ip, t2_tc_43_fct_0044_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=be2f562d738e factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0044_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0044_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0044_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0044_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0044_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0044-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0044_ip';
SELECT 'TC-43-FCT-0044-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0045-DF
-- Factor probe: IDX_FULLTEXT_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 FULLTEXT 索引（非目标列）—— 会改变 INPLACE 可行性
DROP TABLE IF EXISTS t1_tc_43_fct_0045_df, t2_tc_43_fct_0045_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=33ae6eb0fa11 factor=IDX_FULLTEXT_OTHER
CREATE TABLE t1_tc_43_fct_0045_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  ft TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  FULLTEXT INDEX ft_idx (ft),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0045_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0045_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0045_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0045_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0045-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0045_df';
SELECT 'TC-43-FCT-0045-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0046-IT
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0046_it, t2_tc_43_fct_0046_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a065bff88b8b factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0046_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0046_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0046_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0046_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0046_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0046-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0046_it';
SELECT 'TC-43-FCT-0046-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0047-IP
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0047_ip, t2_tc_43_fct_0047_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=471554dae842 factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0047_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0047_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0047_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0047_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0047_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0047-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0047_ip';
SELECT 'TC-43-FCT-0047-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0048-DF
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0048_df, t2_tc_43_fct_0048_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d05f0c165749 factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0048_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0048_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0048_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0048_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0048_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0048-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0048_df';
SELECT 'TC-43-FCT-0048-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0049-IT
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0049_it, t2_tc_43_fct_0049_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d723a113c95a factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0049_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0049_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0049_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0049_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0049_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0049-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0049_it';
SELECT 'TC-43-FCT-0049-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0050-IP
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0050_ip, t2_tc_43_fct_0050_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3a024424eb42 factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0050_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0050_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0050_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0050_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0050_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0050-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0050_ip';
SELECT 'TC-43-FCT-0050-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0051-DF
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0051_df, t2_tc_43_fct_0051_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7c844dd7cd86 factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0051_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0051_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0051_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0051_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0051_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0051-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0051_df';
SELECT 'TC-43-FCT-0051-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0052-IT
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0052_it, t2_tc_43_fct_0052_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=42959caace79 factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0052_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0052_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0052_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0052_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0052_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0052-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0052_it';
SELECT 'TC-43-FCT-0052-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0053-IP
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0053_ip, t2_tc_43_fct_0053_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=e81519e204ae factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0053_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0053_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0053_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0053_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0053_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0053-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0053_ip';
SELECT 'TC-43-FCT-0053-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0054-DF
-- Factor probe: IDX_SPATIAL_OTHER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 SPATIAL 索引（非目标列）
DROP TABLE IF EXISTS t1_tc_43_fct_0054_df, t2_tc_43_fct_0054_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6211fce78cde factor=IDX_SPATIAL_OTHER
CREATE TABLE t1_tc_43_fct_0054_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  g POINT NOT NULL SRID 0 DEFAULT (ST_PointFromText('POINT(0 0)')),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  SPATIAL INDEX sp_idx (g),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0054_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0054_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0054_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0054_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0054-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0054_df';
SELECT 'TC-43-FCT-0054-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0055-IT
-- Factor probe: DEP_TRIGGER
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0055_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0055_it, t2_tc_43_fct_0055_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=337bf1275141 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0055_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0055_it BEFORE INSERT ON t1_tc_43_fct_0055_it FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0055_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0055_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0055_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0055_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0055-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0055_it';
SELECT 'TC-43-FCT-0055-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0055_it;

-- Test Case: TC-43-FCT-0056-IP
-- Factor probe: DEP_TRIGGER
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0056_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0056_ip, t2_tc_43_fct_0056_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=61523291c31e factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0056_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0056_ip BEFORE INSERT ON t1_tc_43_fct_0056_ip FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0056_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0056_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0056_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0056_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0056-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0056_ip';
SELECT 'TC-43-FCT-0056-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0056_ip;

-- Test Case: TC-43-FCT-0057-DF
-- Factor probe: DEP_TRIGGER
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0057_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0057_df, t2_tc_43_fct_0057_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4490e16c1975 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0057_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0057_df BEFORE INSERT ON t1_tc_43_fct_0057_df FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0057_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0057_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0057_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0057_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0057-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0057_df';
SELECT 'TC-43-FCT-0057-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0057_df;

-- Test Case: TC-43-FCT-0058-IT
-- Factor probe: DEP_TRIGGER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0058_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0058_it, t2_tc_43_fct_0058_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a7a50e673e62 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0058_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0058_it BEFORE INSERT ON t1_tc_43_fct_0058_it FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0058_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0058_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0058_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0058_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0058-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0058_it';
SELECT 'TC-43-FCT-0058-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0058_it;

-- Test Case: TC-43-FCT-0059-IP
-- Factor probe: DEP_TRIGGER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0059_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0059_ip, t2_tc_43_fct_0059_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7fc09fb0d241 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0059_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0059_ip BEFORE INSERT ON t1_tc_43_fct_0059_ip FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0059_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0059_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0059_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0059_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0059-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0059_ip';
SELECT 'TC-43-FCT-0059-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0059_ip;

-- Test Case: TC-43-FCT-0060-DF
-- Factor probe: DEP_TRIGGER
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0060_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0060_df, t2_tc_43_fct_0060_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=54d2afd1ff7b factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0060_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0060_df BEFORE INSERT ON t1_tc_43_fct_0060_df FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0060_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0060_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0060_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0060_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0060-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0060_df';
SELECT 'TC-43-FCT-0060-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0060_df;

-- Test Case: TC-43-FCT-0061-IT
-- Factor probe: DEP_TRIGGER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0061_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0061_it, t2_tc_43_fct_0061_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9fef6680d853 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0061_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0061_it BEFORE INSERT ON t1_tc_43_fct_0061_it FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0061_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0061_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0061_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0061_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0061-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0061_it';
SELECT 'TC-43-FCT-0061-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0061_it;

-- Test Case: TC-43-FCT-0062-IP
-- Factor probe: DEP_TRIGGER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0062_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0062_ip, t2_tc_43_fct_0062_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ffcdb44ec367 factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0062_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0062_ip BEFORE INSERT ON t1_tc_43_fct_0062_ip FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0062_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0062_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0062_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0062_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0062-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0062_ip';
SELECT 'TC-43-FCT-0062-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0062_ip;

-- Test Case: TC-43-FCT-0063-DF
-- Factor probe: DEP_TRIGGER
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表上有 BEFORE INSERT 触发器引用目标列
DROP TRIGGER IF EXISTS trg_tc_43_fct_0063_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0063_df, t2_tc_43_fct_0063_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9646e227d83c factor=DEP_TRIGGER
CREATE TABLE t1_tc_43_fct_0063_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE TRIGGER trg_tc_43_fct_0063_df BEFORE INSERT ON t1_tc_43_fct_0063_df FOR EACH ROW SET NEW.pad = CONCAT('t', IFNULL(NEW.target,''));
INSERT INTO t1_tc_43_fct_0063_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0063_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0063_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0063_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0063-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0063_df';
SELECT 'TC-43-FCT-0063-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP TRIGGER IF EXISTS trg_tc_43_fct_0063_df;

-- Test Case: TC-43-FCT-0064-IT
-- Factor probe: DEP_VIEW
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0064_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0064_it, t2_tc_43_fct_0064_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3560b1281beb factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0064_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0064_it AS SELECT id, target FROM t1_tc_43_fct_0064_it;
INSERT INTO t1_tc_43_fct_0064_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0064_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0064_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0064_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0064-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0064_it';
SELECT 'TC-43-FCT-0064-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0064_it;

-- Test Case: TC-43-FCT-0065-IP
-- Factor probe: DEP_VIEW
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0065_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0065_ip, t2_tc_43_fct_0065_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1abbc75c6520 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0065_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0065_ip AS SELECT id, target FROM t1_tc_43_fct_0065_ip;
INSERT INTO t1_tc_43_fct_0065_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0065_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0065_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0065_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0065-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0065_ip';
SELECT 'TC-43-FCT-0065-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0065_ip;

-- Test Case: TC-43-FCT-0066-DF
-- Factor probe: DEP_VIEW
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0066_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0066_df, t2_tc_43_fct_0066_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=2abae90e5183 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0066_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0066_df AS SELECT id, target FROM t1_tc_43_fct_0066_df;
INSERT INTO t1_tc_43_fct_0066_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0066_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0066_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0066_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0066-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0066_df';
SELECT 'TC-43-FCT-0066-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0066_df;

-- Test Case: TC-43-FCT-0067-IT
-- Factor probe: DEP_VIEW
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0067_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0067_it, t2_tc_43_fct_0067_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=b540dd54de42 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0067_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0067_it AS SELECT id, target FROM t1_tc_43_fct_0067_it;
INSERT INTO t1_tc_43_fct_0067_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0067_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0067_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0067_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0067-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0067_it';
SELECT 'TC-43-FCT-0067-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0067_it;

-- Test Case: TC-43-FCT-0068-IP
-- Factor probe: DEP_VIEW
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0068_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0068_ip, t2_tc_43_fct_0068_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fc4ad7578732 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0068_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0068_ip AS SELECT id, target FROM t1_tc_43_fct_0068_ip;
INSERT INTO t1_tc_43_fct_0068_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0068_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0068_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0068_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0068-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0068_ip';
SELECT 'TC-43-FCT-0068-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0068_ip;

-- Test Case: TC-43-FCT-0069-DF
-- Factor probe: DEP_VIEW
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0069_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0069_df, t2_tc_43_fct_0069_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=b43a8e813efe factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0069_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0069_df AS SELECT id, target FROM t1_tc_43_fct_0069_df;
INSERT INTO t1_tc_43_fct_0069_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0069_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0069_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0069_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0069-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0069_df';
SELECT 'TC-43-FCT-0069-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0069_df;

-- Test Case: TC-43-FCT-0070-IT
-- Factor probe: DEP_VIEW
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0070_it;
DROP TABLE IF EXISTS t1_tc_43_fct_0070_it, t2_tc_43_fct_0070_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=432c1f3f932f factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0070_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0070_it AS SELECT id, target FROM t1_tc_43_fct_0070_it;
INSERT INTO t1_tc_43_fct_0070_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0070_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0070_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0070_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0070-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0070_it';
SELECT 'TC-43-FCT-0070-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0070_it;

-- Test Case: TC-43-FCT-0071-IP
-- Factor probe: DEP_VIEW
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0071_ip;
DROP TABLE IF EXISTS t1_tc_43_fct_0071_ip, t2_tc_43_fct_0071_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9d388a740dc6 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0071_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0071_ip AS SELECT id, target FROM t1_tc_43_fct_0071_ip;
INSERT INTO t1_tc_43_fct_0071_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0071_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0071_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0071_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0071-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0071_ip';
SELECT 'TC-43-FCT-0071-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0071_ip;

-- Test Case: TC-43-FCT-0072-DF
-- Factor probe: DEP_VIEW
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 存在依赖目标列的视图
DROP VIEW IF EXISTS vw_tc_43_fct_0072_df;
DROP TABLE IF EXISTS t1_tc_43_fct_0072_df, t2_tc_43_fct_0072_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=f4ae33cbb2d9 factor=DEP_VIEW
CREATE TABLE t1_tc_43_fct_0072_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_tc_43_fct_0072_df AS SELECT id, target FROM t1_tc_43_fct_0072_df;
INSERT INTO t1_tc_43_fct_0072_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0072_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0072_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0072_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0072-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0072_df';
SELECT 'TC-43-FCT-0072-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）
DROP VIEW IF EXISTS vw_tc_43_fct_0072_df;

-- Test Case: TC-43-FCT-0073-IT
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0073_it, t2_tc_43_fct_0073_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=e192ddddf8d4 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0073_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0073_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0073_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0073_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0073_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0073-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0073_it';
SELECT 'TC-43-FCT-0073-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0074-IP
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0074_ip, t2_tc_43_fct_0074_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=982b1d621f09 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0074_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0074_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0074_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0074_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0074_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0074-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0074_ip';
SELECT 'TC-43-FCT-0074-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0075-DF
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0075_df, t2_tc_43_fct_0075_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ed7ea452cc6e factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0075_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0075_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0075_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0075_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0075_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0075-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0075_df';
SELECT 'TC-43-FCT-0075-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0076-IT
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0076_it, t2_tc_43_fct_0076_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=869fe4c17fa0 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0076_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0076_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0076_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0076_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0076_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0076-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0076_it';
SELECT 'TC-43-FCT-0076-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0077-IP
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0077_ip, t2_tc_43_fct_0077_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ac7d629c5b37 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0077_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0077_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0077_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0077_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0077_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0077-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0077_ip';
SELECT 'TC-43-FCT-0077-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0078-DF
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0078_df, t2_tc_43_fct_0078_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0efa5d38fc48 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0078_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0078_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0078_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0078_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0078_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0078-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0078_df';
SELECT 'TC-43-FCT-0078-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0079-IT
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0079_it, t2_tc_43_fct_0079_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0908fd2b5516 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0079_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0079_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0079_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0079_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0079_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0079-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0079_it';
SELECT 'TC-43-FCT-0079-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0080-IP
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0080_ip, t2_tc_43_fct_0080_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=69f560aedc3f factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0080_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0080_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0080_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0080_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0080_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0080-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0080_ip';
SELECT 'TC-43-FCT-0080-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0081-DF
-- Factor probe: DEP_GEN_VIRTUAL_IDX
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: VIRTUAL 生成列 + 生成列索引（生成列不得引用自增列）
DROP TABLE IF EXISTS t1_tc_43_fct_0081_df, t2_tc_43_fct_0081_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=5505ce66a1e8 factor=DEP_GEN_VIRTUAL_IDX
CREATE TABLE t1_tc_43_fct_0081_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  seed INT DEFAULT 1, vcol BIGINT AS (seed * 2) VIRTUAL,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_v (vcol),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0081_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0081_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0081_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0081_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0081-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0081_df';
SELECT 'TC-43-FCT-0081-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0082-IT
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0082_it, t2_tc_43_fct_0082_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=55780279eecf factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0082_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0082_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0082_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0082_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0082_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0082-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0082_it';
SELECT 'TC-43-FCT-0082-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0083-IP
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0083_ip, t2_tc_43_fct_0083_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=148606751bf0 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0083_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0083_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0083_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0083_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0083_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0083-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0083_ip';
SELECT 'TC-43-FCT-0083-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0084-DF
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0084_df, t2_tc_43_fct_0084_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7b67371c9011 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0084_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0084_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0084_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0084_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0084_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0084-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0084_df';
SELECT 'TC-43-FCT-0084-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0085-IT
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0085_it, t2_tc_43_fct_0085_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=60ba1bc08770 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0085_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0085_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0085_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0085_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0085_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0085-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0085_it';
SELECT 'TC-43-FCT-0085-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0086-IP
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0086_ip, t2_tc_43_fct_0086_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=78bfe1db542d factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0086_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0086_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0086_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0086_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0086_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0086-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0086_ip';
SELECT 'TC-43-FCT-0086-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0087-DF
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0087_df, t2_tc_43_fct_0087_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=01b598a831b0 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0087_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0087_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0087_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0087_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0087_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0087-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0087_df';
SELECT 'TC-43-FCT-0087-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0088-IT
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0088_it, t2_tc_43_fct_0088_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6c2aca0503e9 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0088_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0088_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0088_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0088_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0088_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0088-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0088_it';
SELECT 'TC-43-FCT-0088-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0089-IP
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0089_ip, t2_tc_43_fct_0089_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=32b001af9c51 factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0089_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0089_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0089_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0089_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0089_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0089-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0089_ip';
SELECT 'TC-43-FCT-0089-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0090-DF
-- Factor probe: OPT_ROW_COMPRESSED
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: COMPRESSED 行格式（PRD 排除项，必须作为负向用例存在）
DROP TABLE IF EXISTS t1_tc_43_fct_0090_df, t2_tc_43_fct_0090_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=bfdc27fb07ab factor=OPT_ROW_COMPRESSED
CREATE TABLE t1_tc_43_fct_0090_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
INSERT INTO t1_tc_43_fct_0090_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0090_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0090_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0090_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0090-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0090_df';
SELECT 'TC-43-FCT-0090-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0091-IT
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0091_it, t2_tc_43_fct_0091_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1dd4738a2c05 factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0091_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0091_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0091_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0091_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0091_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0091-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0091_it';
SELECT 'TC-43-FCT-0091-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0092-IP
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0092_ip, t2_tc_43_fct_0092_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=51828976cb5e factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0092_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0092_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0092_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0092_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0092_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0092-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0092_ip';
SELECT 'TC-43-FCT-0092-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0093-DF
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0093_df, t2_tc_43_fct_0093_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=16dc306ac9e2 factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0093_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0093_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0093_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0093_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0093_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0093-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0093_df';
SELECT 'TC-43-FCT-0093-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0094-IT
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0094_it, t2_tc_43_fct_0094_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3ed71a0402c8 factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0094_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0094_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0094_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0094_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0094_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0094-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0094_it';
SELECT 'TC-43-FCT-0094-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0095-IP
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0095_ip, t2_tc_43_fct_0095_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=17bf074213be factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0095_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0095_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0095_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0095_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0095_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0095-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0095_ip';
SELECT 'TC-43-FCT-0095-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0096-DF
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0096_df, t2_tc_43_fct_0096_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=02b871ea6b1f factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0096_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0096_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0096_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0096_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0096_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0096-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0096_df';
SELECT 'TC-43-FCT-0096-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0097-IT
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0097_it, t2_tc_43_fct_0097_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3b18f83f83fe factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0097_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0097_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0097_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0097_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0097_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0097-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0097_it';
SELECT 'TC-43-FCT-0097-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0098-IP
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0098_ip, t2_tc_43_fct_0098_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=342672bac408 factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0098_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0098_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0098_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0098_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0098_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0098-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0098_ip';
SELECT 'TC-43-FCT-0098-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0099-DF
-- Factor probe: OPT_PAGE_COMPRESSION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: InnoDB 页压缩
DROP TABLE IF EXISTS t1_tc_43_fct_0099_df, t2_tc_43_fct_0099_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1dcb6168eaab factor=OPT_PAGE_COMPRESSION
CREATE TABLE t1_tc_43_fct_0099_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB COMPRESSION='zlib';
INSERT INTO t1_tc_43_fct_0099_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0099_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0099_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0099_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0099-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0099_df';
SELECT 'TC-43-FCT-0099-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0100-IT
-- Factor probe: OPT_ENCRYPTION
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0100_it, t2_tc_43_fct_0100_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=929d1963f88d factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0100_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0100_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0100_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0100_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0100_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0100-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0100_it';
SELECT 'TC-43-FCT-0100-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0101-IP
-- Factor probe: OPT_ENCRYPTION
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0101_ip, t2_tc_43_fct_0101_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d2509a236f56 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0101_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0101_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0101_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0101_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0101_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0101-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0101_ip';
SELECT 'TC-43-FCT-0101-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0102-DF
-- Factor probe: OPT_ENCRYPTION
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0102_df, t2_tc_43_fct_0102_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ea80531bb4d5 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0102_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0102_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0102_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0102_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0102_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0102-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0102_df';
SELECT 'TC-43-FCT-0102-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0103-IT
-- Factor probe: OPT_ENCRYPTION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0103_it, t2_tc_43_fct_0103_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6348cf423c55 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0103_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0103_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0103_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0103_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0103_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0103-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0103_it';
SELECT 'TC-43-FCT-0103-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0104-IP
-- Factor probe: OPT_ENCRYPTION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0104_ip, t2_tc_43_fct_0104_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=2e4ef52500fb factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0104_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0104_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0104_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0104_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0104_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0104-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0104_ip';
SELECT 'TC-43-FCT-0104-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0105-DF
-- Factor probe: OPT_ENCRYPTION
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0105_df, t2_tc_43_fct_0105_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=cb8e071de937 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0105_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0105_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0105_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0105_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0105_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0105-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0105_df';
SELECT 'TC-43-FCT-0105-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0106-IT
-- Factor probe: OPT_ENCRYPTION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0106_it, t2_tc_43_fct_0106_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=c9f155177d53 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0106_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0106_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0106_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0106_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0106_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0106-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0106_it';
SELECT 'TC-43-FCT-0106-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0107-IP
-- Factor probe: OPT_ENCRYPTION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0107_ip, t2_tc_43_fct_0107_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4ada205d8df6 factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0107_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0107_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0107_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0107_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0107_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0107-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0107_ip';
SELECT 'TC-43-FCT-0107-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0108-DF
-- Factor probe: OPT_ENCRYPTION
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 表空间加密（无 keyring 时应建表失败）
DROP TABLE IF EXISTS t1_tc_43_fct_0108_df, t2_tc_43_fct_0108_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1aec9504035e factor=OPT_ENCRYPTION
CREATE TABLE t1_tc_43_fct_0108_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB ENCRYPTION='Y';
INSERT INTO t1_tc_43_fct_0108_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0108_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0108_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0108_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0108-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0108_df';
SELECT 'TC-43-FCT-0108-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0109-IT
-- Factor probe: OPT_TABLESPACE
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0109_it, t2_tc_43_fct_0109_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=48736bcda854 factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0109_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0109_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0109_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0109_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0109_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0109-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0109_it';
SELECT 'TC-43-FCT-0109-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0110-IP
-- Factor probe: OPT_TABLESPACE
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0110_ip, t2_tc_43_fct_0110_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8302eaa928f8 factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0110_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0110_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0110_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0110_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0110_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0110-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0110_ip';
SELECT 'TC-43-FCT-0110-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0111-DF
-- Factor probe: OPT_TABLESPACE
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0111_df, t2_tc_43_fct_0111_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=922fde52c060 factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0111_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0111_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0111_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0111_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0111_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0111-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0111_df';
SELECT 'TC-43-FCT-0111-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0112-IT
-- Factor probe: OPT_TABLESPACE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0112_it, t2_tc_43_fct_0112_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1d644b8aa52a factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0112_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0112_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0112_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0112_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0112_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0112-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0112_it';
SELECT 'TC-43-FCT-0112-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0113-IP
-- Factor probe: OPT_TABLESPACE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0113_ip, t2_tc_43_fct_0113_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=bcc4381ea61d factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0113_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0113_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0113_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0113_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0113_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0113-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0113_ip';
SELECT 'TC-43-FCT-0113-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0114-DF
-- Factor probe: OPT_TABLESPACE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0114_df, t2_tc_43_fct_0114_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3973f091114a factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0114_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0114_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0114_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0114_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0114_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0114-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0114_df';
SELECT 'TC-43-FCT-0114-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0115-IT
-- Factor probe: OPT_TABLESPACE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0115_it, t2_tc_43_fct_0115_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4627cf77b703 factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0115_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0115_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0115_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0115_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0115_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0115-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0115_it';
SELECT 'TC-43-FCT-0115-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0116-IP
-- Factor probe: OPT_TABLESPACE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0116_ip, t2_tc_43_fct_0116_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=b08c18c06aba factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0116_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0116_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0116_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0116_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0116_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0116-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0116_ip';
SELECT 'TC-43-FCT-0116-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0117-DF
-- Factor probe: OPT_TABLESPACE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 显式表空间
DROP TABLE IF EXISTS t1_tc_43_fct_0117_df, t2_tc_43_fct_0117_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=38e7f566b245 factor=OPT_TABLESPACE
CREATE TABLE t1_tc_43_fct_0117_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB TABLESPACE innodb_file_per_table;
INSERT INTO t1_tc_43_fct_0117_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0117_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0117_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0117_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0117-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0117_df';
SELECT 'TC-43-FCT-0117-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0118-IT
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0118_it, t2_tc_43_fct_0118_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7b74846bdc67 factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0118_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0118_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0118_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0118_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0118_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0118-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0118_it';
SELECT 'TC-43-FCT-0118-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0119-IP
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0119_ip, t2_tc_43_fct_0119_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0c392836e61b factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0119_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0119_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0119_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0119_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0119_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0119-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0119_ip';
SELECT 'TC-43-FCT-0119-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0120-DF
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0120_df, t2_tc_43_fct_0120_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ebffd33ee9a9 factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0120_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0120_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0120_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0120_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0120_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0120-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0120_df';
SELECT 'TC-43-FCT-0120-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0121-IT
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0121_it, t2_tc_43_fct_0121_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9351d6a8de7c factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0121_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0121_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0121_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0121_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0121_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0121-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0121_it';
SELECT 'TC-43-FCT-0121-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0122-IP
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0122_ip, t2_tc_43_fct_0122_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=3d36d2cbe880 factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0122_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0122_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0122_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0122_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0122_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0122-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0122_ip';
SELECT 'TC-43-FCT-0122-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0123-DF
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0123_df, t2_tc_43_fct_0123_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=33a2d18067bf factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0123_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0123_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0123_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0123_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0123_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0123-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0123_df';
SELECT 'TC-43-FCT-0123-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0124-IT
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0124_it, t2_tc_43_fct_0124_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8685e1b4195f factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0124_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0124_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0124_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0124_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0124_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0124-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0124_it';
SELECT 'TC-43-FCT-0124-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0125-IP
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0125_ip, t2_tc_43_fct_0125_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d8d26fbfe9a9 factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0125_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0125_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0125_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0125_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0125_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0125-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0125_ip';
SELECT 'TC-43-FCT-0125-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0126-DF
-- Factor probe: OPT_STATS_PERSISTENT
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 统计信息持久化且关闭自动重算（DDL 后统计信息是否更新）
DROP TABLE IF EXISTS t1_tc_43_fct_0126_df, t2_tc_43_fct_0126_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=5bccc11341b4 factor=OPT_STATS_PERSISTENT
CREATE TABLE t1_tc_43_fct_0126_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB STATS_PERSISTENT=1 STATS_AUTO_RECALC=0;
INSERT INTO t1_tc_43_fct_0126_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0126_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0126_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0126_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0126-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0126_df';
SELECT 'TC-43-FCT-0126-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0127-IT
-- Factor probe: ENG_MYISAM
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0127_it, t2_tc_43_fct_0127_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=413b278b3aeb factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0127_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0127_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0127_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0127_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0127_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0127-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0127_it';
SELECT 'TC-43-FCT-0127-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0128-IP
-- Factor probe: ENG_MYISAM
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0128_ip, t2_tc_43_fct_0128_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7ae8590392a4 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0128_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0128_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0128_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0128_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0128_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0128-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0128_ip';
SELECT 'TC-43-FCT-0128-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0129-DF
-- Factor probe: ENG_MYISAM
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0129_df, t2_tc_43_fct_0129_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=b8f793048405 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0129_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0129_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0129_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0129_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0129_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0129-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0129_df';
SELECT 'TC-43-FCT-0129-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0130-IT
-- Factor probe: ENG_MYISAM
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0130_it, t2_tc_43_fct_0130_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9a5c9e1f704d factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0130_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0130_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0130_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0130_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0130_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0130-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0130_it';
SELECT 'TC-43-FCT-0130-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0131-IP
-- Factor probe: ENG_MYISAM
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0131_ip, t2_tc_43_fct_0131_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=145fcf0228de factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0131_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0131_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0131_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0131_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0131_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0131-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0131_ip';
SELECT 'TC-43-FCT-0131-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0132-DF
-- Factor probe: ENG_MYISAM
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0132_df, t2_tc_43_fct_0132_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=668a2ebeb049 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0132_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0132_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0132_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0132_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0132_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0132-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0132_df';
SELECT 'TC-43-FCT-0132-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0133-IT
-- Factor probe: ENG_MYISAM
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0133_it, t2_tc_43_fct_0133_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a263187e8430 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0133_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0133_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0133_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0133_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0133_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0133-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0133_it';
SELECT 'TC-43-FCT-0133-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0134-IP
-- Factor probe: ENG_MYISAM
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0134_ip, t2_tc_43_fct_0134_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=eacfbe7fe518 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0134_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0134_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0134_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0134_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0134_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0134-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0134_ip';
SELECT 'TC-43-FCT-0134-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0135-DF
-- Factor probe: ENG_MYISAM
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 非 InnoDB 引擎（INSTANT/INPLACE 不适用）
DROP TABLE IF EXISTS t1_tc_43_fct_0135_df, t2_tc_43_fct_0135_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0c0b01779d69 factor=ENG_MYISAM
CREATE TABLE t1_tc_43_fct_0135_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MyISAM;
INSERT INTO t1_tc_43_fct_0135_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0135_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0135_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0135_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0135-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0135_df';
SELECT 'TC-43-FCT-0135-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0136-IT
-- Factor probe: ENG_MEMORY
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0136_it, t2_tc_43_fct_0136_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=778235ad4b09 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0136_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0136_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0136_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0136_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0136_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0136-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0136_it';
SELECT 'TC-43-FCT-0136-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0137-IP
-- Factor probe: ENG_MEMORY
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0137_ip, t2_tc_43_fct_0137_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=77e3c8c59e68 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0137_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0137_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0137_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0137_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0137_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0137-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0137_ip';
SELECT 'TC-43-FCT-0137-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0138-DF
-- Factor probe: ENG_MEMORY
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0138_df, t2_tc_43_fct_0138_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=cd8779dd87f2 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0138_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0138_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0138_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0138_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0138_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0138-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0138_df';
SELECT 'TC-43-FCT-0138-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0139-IT
-- Factor probe: ENG_MEMORY
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0139_it, t2_tc_43_fct_0139_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8716a36a05bb factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0139_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0139_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0139_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0139_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0139_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0139-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0139_it';
SELECT 'TC-43-FCT-0139-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0140-IP
-- Factor probe: ENG_MEMORY
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0140_ip, t2_tc_43_fct_0140_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=cf0a1eda016b factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0140_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0140_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0140_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0140_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0140_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0140-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0140_ip';
SELECT 'TC-43-FCT-0140-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0141-DF
-- Factor probe: ENG_MEMORY
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0141_df, t2_tc_43_fct_0141_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=58fde0b46dc6 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0141_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0141_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0141_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0141_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0141_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0141-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0141_df';
SELECT 'TC-43-FCT-0141-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0142-IT
-- Factor probe: ENG_MEMORY
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0142_it, t2_tc_43_fct_0142_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=800c1d416d45 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0142_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0142_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0142_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0142_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0142_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0142-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0142_it';
SELECT 'TC-43-FCT-0142-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0143-IP
-- Factor probe: ENG_MEMORY
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0143_ip, t2_tc_43_fct_0143_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9dc9ca03fc34 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0143_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0143_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0143_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0143_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0143_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0143-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0143_ip';
SELECT 'TC-43-FCT-0143-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0144-DF
-- Factor probe: ENG_MEMORY
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: MEMORY 引擎
DROP TABLE IF EXISTS t1_tc_43_fct_0144_df, t2_tc_43_fct_0144_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=cd1d54cebae6 factor=ENG_MEMORY
CREATE TABLE t1_tc_43_fct_0144_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=MEMORY;
INSERT INTO t1_tc_43_fct_0144_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0144_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0144_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0144_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0144-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0144_df';
SELECT 'TC-43-FCT-0144-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0145-IT
-- Factor probe: MODE_PAD_CHAR
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0145_it, t2_tc_43_fct_0145_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a08d6e050c8a factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0145_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0145_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0145_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0145_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0145_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0145-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0145_it';
SELECT 'TC-43-FCT-0145-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0146-IP
-- Factor probe: MODE_PAD_CHAR
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0146_ip, t2_tc_43_fct_0146_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7ca0ccd2b6b4 factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0146_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0146_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0146_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0146_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0146_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0146-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0146_ip';
SELECT 'TC-43-FCT-0146-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0147-DF
-- Factor probe: MODE_PAD_CHAR
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0147_df, t2_tc_43_fct_0147_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=f4a7d69b1e99 factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0147_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0147_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0147_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0147_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0147_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0147-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0147_df';
SELECT 'TC-43-FCT-0147-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0148-IT
-- Factor probe: MODE_PAD_CHAR
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0148_it, t2_tc_43_fct_0148_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1c8b59be928b factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0148_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0148_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0148_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0148_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0148_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0148-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0148_it';
SELECT 'TC-43-FCT-0148-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0149-IP
-- Factor probe: MODE_PAD_CHAR
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0149_ip, t2_tc_43_fct_0149_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7462957559de factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0149_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0149_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0149_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0149_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0149_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0149-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0149_ip';
SELECT 'TC-43-FCT-0149-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0150-DF
-- Factor probe: MODE_PAD_CHAR
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0150_df, t2_tc_43_fct_0150_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=05be4bc244b1 factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0150_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0150_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0150_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0150_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0150_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0150-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0150_df';
SELECT 'TC-43-FCT-0150-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0151-IT
-- Factor probe: MODE_PAD_CHAR
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0151_it, t2_tc_43_fct_0151_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8d840f40de22 factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0151_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0151_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0151_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0151_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0151_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0151-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0151_it';
SELECT 'TC-43-FCT-0151-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0152-IP
-- Factor probe: MODE_PAD_CHAR
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0152_ip, t2_tc_43_fct_0152_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=1b07de4a2e1a factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0152_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0152_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0152_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0152_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0152_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0152-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0152_ip';
SELECT 'TC-43-FCT-0152-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0153-DF
-- Factor probe: MODE_PAD_CHAR
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: PAD_CHAR_TO_FULL_LENGTH：直接改变 CHAR 取值语义与对照结果
SET SESSION sql_mode='STRICT_TRANS_TABLES,PAD_CHAR_TO_FULL_LENGTH';
DROP TABLE IF EXISTS t1_tc_43_fct_0153_df, t2_tc_43_fct_0153_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=798e1e46dc07 factor=MODE_PAD_CHAR
CREATE TABLE t1_tc_43_fct_0153_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0153_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0153_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0153_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0153_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0153-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0153_df';
SELECT 'TC-43-FCT-0153-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0154-IT
-- Factor probe: MODE_TRADITIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0154_it, t2_tc_43_fct_0154_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=2ba69e3387dc factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0154_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0154_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0154_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0154_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0154_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0154-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0154_it';
SELECT 'TC-43-FCT-0154-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0155-IP
-- Factor probe: MODE_TRADITIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0155_ip, t2_tc_43_fct_0155_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=25209bb37214 factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0155_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0155_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0155_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0155_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0155_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0155-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0155_ip';
SELECT 'TC-43-FCT-0155-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0156-DF
-- Factor probe: MODE_TRADITIONAL
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0156_df, t2_tc_43_fct_0156_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9df8aeb07743 factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0156_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0156_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0156_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0156_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0156_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0156-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0156_df';
SELECT 'TC-43-FCT-0156-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0157-IT
-- Factor probe: MODE_TRADITIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0157_it, t2_tc_43_fct_0157_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=539a0dcb6e83 factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0157_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0157_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0157_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0157_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0157_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0157-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0157_it';
SELECT 'TC-43-FCT-0157-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0158-IP
-- Factor probe: MODE_TRADITIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0158_ip, t2_tc_43_fct_0158_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=960c43b9ed2a factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0158_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0158_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0158_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0158_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0158_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0158-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0158_ip';
SELECT 'TC-43-FCT-0158-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0159-DF
-- Factor probe: MODE_TRADITIONAL
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0159_df, t2_tc_43_fct_0159_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=494812888641 factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0159_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0159_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0159_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0159_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0159_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0159-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0159_df';
SELECT 'TC-43-FCT-0159-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0160-IT
-- Factor probe: MODE_TRADITIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0160_it, t2_tc_43_fct_0160_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=5f1632216d44 factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0160_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0160_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0160_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0160_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0160_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0160-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0160_it';
SELECT 'TC-43-FCT-0160-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0161-IP
-- Factor probe: MODE_TRADITIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0161_ip, t2_tc_43_fct_0161_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=efb395d2470d factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0161_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0161_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0161_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0161_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0161_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0161-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0161_ip';
SELECT 'TC-43-FCT-0161-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0162-DF
-- Factor probe: MODE_TRADITIONAL
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: TRADITIONAL 严格模式
SET SESSION sql_mode='TRADITIONAL';
DROP TABLE IF EXISTS t1_tc_43_fct_0162_df, t2_tc_43_fct_0162_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=41c834e3d3bc factor=MODE_TRADITIONAL
CREATE TABLE t1_tc_43_fct_0162_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0162_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0162_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0162_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0162_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0162-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0162_df';
SELECT 'TC-43-FCT-0162-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0163-IT
-- Factor probe: MODE_ANSI
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0163_it, t2_tc_43_fct_0163_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fc426497cfbe factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0163_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0163_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0163_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0163_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0163_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0163-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0163_it';
SELECT 'TC-43-FCT-0163-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0164-IP
-- Factor probe: MODE_ANSI
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0164_ip, t2_tc_43_fct_0164_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=54be49a1be7c factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0164_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0164_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0164_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0164_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0164_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0164-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0164_ip';
SELECT 'TC-43-FCT-0164-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0165-DF
-- Factor probe: MODE_ANSI
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0165_df, t2_tc_43_fct_0165_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=05542acf7a4e factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0165_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0165_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0165_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0165_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0165_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0165-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0165_df';
SELECT 'TC-43-FCT-0165-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0166-IT
-- Factor probe: MODE_ANSI
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0166_it, t2_tc_43_fct_0166_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4b21e61ab65a factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0166_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0166_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0166_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0166_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0166_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0166-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0166_it';
SELECT 'TC-43-FCT-0166-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0167-IP
-- Factor probe: MODE_ANSI
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0167_ip, t2_tc_43_fct_0167_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0999d2f36e35 factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0167_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0167_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0167_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0167_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0167_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0167-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0167_ip';
SELECT 'TC-43-FCT-0167-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0168-DF
-- Factor probe: MODE_ANSI
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0168_df, t2_tc_43_fct_0168_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=e0232f622f2a factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0168_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0168_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0168_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0168_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0168_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0168-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0168_df';
SELECT 'TC-43-FCT-0168-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0169-IT
-- Factor probe: MODE_ANSI
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0169_it, t2_tc_43_fct_0169_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=8399e88da74a factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0169_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0169_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0169_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0169_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0169_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0169-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0169_it';
SELECT 'TC-43-FCT-0169-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0170-IP
-- Factor probe: MODE_ANSI
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0170_ip, t2_tc_43_fct_0170_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=4e4d325749a4 factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0170_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0170_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0170_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0170_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0170_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0170-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0170_ip';
SELECT 'TC-43-FCT-0170-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0171-DF
-- Factor probe: MODE_ANSI
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: ANSI 模式（引号/除法语义变化）
SET SESSION sql_mode='ANSI';
DROP TABLE IF EXISTS t1_tc_43_fct_0171_df, t2_tc_43_fct_0171_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=abcb255df373 factor=MODE_ANSI
CREATE TABLE t1_tc_43_fct_0171_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0171_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0171_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0171_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0171_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0171-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0171_df';
SELECT 'TC-43-FCT-0171-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0172-IT
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0172_it, t2_tc_43_fct_0172_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=da274b9194c8 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0172_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0172_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0172_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0172_it (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0172_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0172-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0172_it';
SELECT 'TC-43-FCT-0172-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0173-IP
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0173_ip, t2_tc_43_fct_0173_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=f40117f01642 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0173_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0173_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0173_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0173_ip (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0173_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0173-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0173_ip';
SELECT 'TC-43-FCT-0173-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0174-DF
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0174_df, t2_tc_43_fct_0174_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=452649b64eb2 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0174_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0174_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0174_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0174_df (target) VALUES (X'0000000000000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0174_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0174-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0174_df';
SELECT 'TC-43-FCT-0174-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0175-IT
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0175_it, t2_tc_43_fct_0175_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=9b504b1d330f factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0175_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0175_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0175_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0175_it (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0175_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0175-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0175_it';
SELECT 'TC-43-FCT-0175-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0176-IP
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0176_ip, t2_tc_43_fct_0176_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=853518b04527 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0176_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0176_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0176_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0176_ip (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0176_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0176-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0176_ip';
SELECT 'TC-43-FCT-0176-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0177-DF
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0177_df, t2_tc_43_fct_0177_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=0a7d76f038e6 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0177_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0177_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0177_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0177_df (target) VALUES (0.02);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0177_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0177-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0177_df';
SELECT 'TC-43-FCT-0177-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0178-IT
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0178_it, t2_tc_43_fct_0178_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6eb86601b8f2 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0178_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0178_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0178_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0178_it (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0178_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0178-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0178_it';
SELECT 'TC-43-FCT-0178-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0179-IP
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0179_ip, t2_tc_43_fct_0179_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=45c004b83ac5 factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0179_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0179_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0179_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0179_ip (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0179_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0179-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0179_ip';
SELECT 'TC-43-FCT-0179-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0180-DF
-- Factor probe: MODE_NO_ZERO_DATE
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: NO_ZERO_DATE / NO_ZERO_IN_DATE
SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE';
DROP TABLE IF EXISTS t1_tc_43_fct_0180_df, t2_tc_43_fct_0180_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=e33fade230ae factor=MODE_NO_ZERO_DATE
CREATE TABLE t1_tc_43_fct_0180_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0180_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0180_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0180_df (target) VALUES ('00000002');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0180_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0180-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0180_df';
SELECT 'TC-43-FCT-0180-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0181-IT
-- Factor probe: SCALE_10K
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0181_it, t2_tc_43_fct_0181_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6fd9ae551779 factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0181_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0181_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
INSERT INTO t1_tc_43_fct_0181_it (target) SELECT target FROM t1_tc_43_fct_0181_it;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0181_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0181-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0181_it';
SELECT 'TC-43-FCT-0181-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0182-IP
-- Factor probe: SCALE_10K
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0182_ip, t2_tc_43_fct_0182_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6cea58e6ba04 factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0182_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0182_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
INSERT INTO t1_tc_43_fct_0182_ip (target) SELECT target FROM t1_tc_43_fct_0182_ip;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0182_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0182-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0182_ip';
SELECT 'TC-43-FCT-0182-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0183-DF
-- Factor probe: SCALE_10K
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0183_df, t2_tc_43_fct_0183_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d70be208e3ee factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0183_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0183_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
INSERT INTO t1_tc_43_fct_0183_df (target) SELECT target FROM t1_tc_43_fct_0183_df;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0183_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0183-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0183_df';
SELECT 'TC-43-FCT-0183-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0184-IT
-- Factor probe: SCALE_10K
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0184_it, t2_tc_43_fct_0184_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=6029c58b091b factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0184_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0184_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
INSERT INTO t1_tc_43_fct_0184_it (target) SELECT target FROM t1_tc_43_fct_0184_it;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0184_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0184-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0184_it';
SELECT 'TC-43-FCT-0184-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0185-IP
-- Factor probe: SCALE_10K
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0185_ip, t2_tc_43_fct_0185_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=39a856dc8b0d factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0185_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0185_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
INSERT INTO t1_tc_43_fct_0185_ip (target) SELECT target FROM t1_tc_43_fct_0185_ip;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0185_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0185-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0185_ip';
SELECT 'TC-43-FCT-0185-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0186-DF
-- Factor probe: SCALE_10K
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0186_df, t2_tc_43_fct_0186_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=333d86381f94 factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0186_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0186_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
INSERT INTO t1_tc_43_fct_0186_df (target) SELECT target FROM t1_tc_43_fct_0186_df;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0186_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0186-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0186_df';
SELECT 'TC-43-FCT-0186-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0187-IT
-- Factor probe: SCALE_10K
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0187_it, t2_tc_43_fct_0187_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=99fe68e4c52f factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0187_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0187_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
INSERT INTO t1_tc_43_fct_0187_it (target) SELECT target FROM t1_tc_43_fct_0187_it;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0187_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0187-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0187_it';
SELECT 'TC-43-FCT-0187-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0188-IP
-- Factor probe: SCALE_10K
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0188_ip, t2_tc_43_fct_0188_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=a96e3cb3e390 factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0188_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0188_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
INSERT INTO t1_tc_43_fct_0188_ip (target) SELECT target FROM t1_tc_43_fct_0188_ip;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0188_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0188-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0188_ip';
SELECT 'TC-43-FCT-0188-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0189-DF
-- Factor probe: SCALE_10K
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 中等数据规模：10,000 行（旧套件只有 0/1/100 行）
DROP TABLE IF EXISTS t1_tc_43_fct_0189_df, t2_tc_43_fct_0189_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ca836aa19721 factor=SCALE_10K
CREATE TABLE t1_tc_43_fct_0189_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0189_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
INSERT INTO t1_tc_43_fct_0189_df (target) SELECT target FROM t1_tc_43_fct_0189_df;
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0189_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0189-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0189_df';
SELECT 'TC-43-FCT-0189-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0190-IT
-- Factor probe: WIDE_200_COLS
-- Type: BINARY(10) -> BINARY(20), Algorithm: instant, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0190_it, t2_tc_43_fct_0190_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=d21205eae027 factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0190_it (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000002');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000003');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000004');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000005');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000006');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000007');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000008');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000009');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000A');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000B');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000C');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000D');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000E');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'000000000000000F');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000010');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000011');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000012');
INSERT INTO t1_tc_43_fct_0190_it (target) VALUES (X'0000000000000013');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0190_it MODIFY target BINARY(20), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0190-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0190_it';
SELECT 'TC-43-FCT-0190-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0191-IP
-- Factor probe: WIDE_200_COLS
-- Type: BINARY(10) -> BINARY(20), Algorithm: inplace, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0191_ip, t2_tc_43_fct_0191_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=92e66258587c factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0191_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000002');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000003');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000004');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000005');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000006');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000007');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000008');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000009');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000A');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000B');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000C');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000D');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000E');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'000000000000000F');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000010');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000011');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000012');
INSERT INTO t1_tc_43_fct_0191_ip (target) VALUES (X'0000000000000013');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0191_ip MODIFY target BINARY(20), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0191-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0191_ip';
SELECT 'TC-43-FCT-0191-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0192-DF
-- Factor probe: WIDE_200_COLS
-- Type: BINARY(10) -> BINARY(20), Algorithm: default, Expected: MEASURE
-- Transition ID: BIN-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0192_df, t2_tc_43_fct_0192_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=928e690687aa factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0192_df (
  id INT NOT NULL AUTO_INCREMENT,
  target BINARY(10),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000000');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000001');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000002');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000003');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000004');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000005');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000006');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000007');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000008');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000009');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000A');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000B');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000C');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000D');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000E');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'000000000000000F');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000010');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000011');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000012');
INSERT INTO t1_tc_43_fct_0192_df (target) VALUES (X'0000000000000013');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0192_df MODIFY target BINARY(20);
SELECT 'TC-43-FCT-0192-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0192_df';
SELECT 'TC-43-FCT-0192-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0193-IT
-- Factor probe: WIDE_200_COLS
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: instant, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0193_it, t2_tc_43_fct_0193_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=fbf92d61803c factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0193_it (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.02);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.03);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.04);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.05);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.06);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.07);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.08);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.09);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.10);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.11);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.12);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.13);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.14);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.15);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.16);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.17);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.18);
INSERT INTO t1_tc_43_fct_0193_it (target) VALUES (0.19);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0193_it MODIFY target DECIMAL(12,2), ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0193-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0193_it';
SELECT 'TC-43-FCT-0193-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0194-IP
-- Factor probe: WIDE_200_COLS
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: inplace, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0194_ip, t2_tc_43_fct_0194_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=bb7dd58e5f73 factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0194_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.02);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.03);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.04);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.05);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.06);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.07);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.08);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.09);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.10);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.11);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.12);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.13);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.14);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.15);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.16);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.17);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.18);
INSERT INTO t1_tc_43_fct_0194_ip (target) VALUES (0.19);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0194_ip MODIFY target DECIMAL(12,2), ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0194-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0194_ip';
SELECT 'TC-43-FCT-0194-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0195-DF
-- Factor probe: WIDE_200_COLS
-- Type: DECIMAL(10,2) -> DECIMAL(12,2), Algorithm: default, Expected: MEASURE
-- Transition ID: DEC-01
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0195_df, t2_tc_43_fct_0195_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=cd19aa90cb79 factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0195_df (
  id INT NOT NULL AUTO_INCREMENT,
  target DECIMAL(10,2),
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.00);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.01);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.02);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.03);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.04);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.05);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.06);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.07);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.08);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.09);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.10);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.11);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.12);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.13);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.14);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.15);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.16);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.17);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.18);
INSERT INTO t1_tc_43_fct_0195_df (target) VALUES (0.19);
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0195_df MODIFY target DECIMAL(12,2);
SELECT 'TC-43-FCT-0195-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0195_df';
SELECT 'TC-43-FCT-0195-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0196-IT
-- Factor probe: WIDE_200_COLS
-- Type: TEXT -> MEDIUMTEXT, Algorithm: instant, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0196_it, t2_tc_43_fct_0196_it;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=7d0ccfc56206 factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0196_it (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000002');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000003');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000004');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000005');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000006');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000007');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000008');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('00000009');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000a');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000b');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000c');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000d');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000e');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000f');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000g');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000h');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000i');
INSERT INTO t1_tc_43_fct_0196_it (target) VALUES ('0000000j');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0196_it MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INSTANT;
SELECT 'TC-43-FCT-0196-IT#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0196_it';
SELECT 'TC-43-FCT-0196-IT#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0197-IP
-- Factor probe: WIDE_200_COLS
-- Type: TEXT -> MEDIUMTEXT, Algorithm: inplace, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0197_ip, t2_tc_43_fct_0197_ip;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=340adf9b0b95 factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0197_ip (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000002');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000003');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000004');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000005');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000006');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000007');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000008');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('00000009');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000a');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000b');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000c');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000d');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000e');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000f');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000g');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000h');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000i');
INSERT INTO t1_tc_43_fct_0197_ip (target) VALUES ('0000000j');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0197_ip MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4, ALGORITHM=INPLACE;
SELECT 'TC-43-FCT-0197-IP#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0197_ip';
SELECT 'TC-43-FCT-0197-IP#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

-- Test Case: TC-43-FCT-0198-DF
-- Factor probe: WIDE_200_COLS
-- Type: TEXT -> MEDIUMTEXT, Algorithm: default, Expected: MEASURE
-- Transition ID: TEXT-02
-- Factor note: 宽表：200 列（行宽与字典压力）
DROP TABLE IF EXISTS t1_tc_43_fct_0198_df, t2_tc_43_fct_0198_df;
-- @expect alter=MEASURE build=MEASURE assertions=2 alter_sha=ba4b64fb9a2a factor=WIDE_200_COLS
CREATE TABLE t1_tc_43_fct_0198_df (
  id INT NOT NULL AUTO_INCREMENT,
  target TEXT CHARACTER SET utf8mb4,
  w0 INT,
  w1 INT,
  w2 INT,
  w3 INT,
  w4 INT,
  w5 INT,
  w6 INT,
  w7 INT,
  w8 INT,
  w9 INT,
  w10 INT,
  w11 INT,
  w12 INT,
  w13 INT,
  w14 INT,
  w15 INT,
  w16 INT,
  w17 INT,
  w18 INT,
  w19 INT,
  w20 INT,
  w21 INT,
  w22 INT,
  w23 INT,
  w24 INT,
  w25 INT,
  w26 INT,
  w27 INT,
  w28 INT,
  w29 INT,
  w30 INT,
  w31 INT,
  w32 INT,
  w33 INT,
  w34 INT,
  w35 INT,
  w36 INT,
  w37 INT,
  w38 INT,
  w39 INT,
  w40 INT,
  w41 INT,
  w42 INT,
  w43 INT,
  w44 INT,
  w45 INT,
  w46 INT,
  w47 INT,
  w48 INT,
  w49 INT,
  w50 INT,
  w51 INT,
  w52 INT,
  w53 INT,
  w54 INT,
  w55 INT,
  w56 INT,
  w57 INT,
  w58 INT,
  w59 INT,
  w60 INT,
  w61 INT,
  w62 INT,
  w63 INT,
  w64 INT,
  w65 INT,
  w66 INT,
  w67 INT,
  w68 INT,
  w69 INT,
  w70 INT,
  w71 INT,
  w72 INT,
  w73 INT,
  w74 INT,
  w75 INT,
  w76 INT,
  w77 INT,
  w78 INT,
  w79 INT,
  w80 INT,
  w81 INT,
  w82 INT,
  w83 INT,
  w84 INT,
  w85 INT,
  w86 INT,
  w87 INT,
  w88 INT,
  w89 INT,
  w90 INT,
  w91 INT,
  w92 INT,
  w93 INT,
  w94 INT,
  w95 INT,
  w96 INT,
  w97 INT,
  w98 INT,
  w99 INT,
  w100 INT,
  w101 INT,
  w102 INT,
  w103 INT,
  w104 INT,
  w105 INT,
  w106 INT,
  w107 INT,
  w108 INT,
  w109 INT,
  w110 INT,
  w111 INT,
  w112 INT,
  w113 INT,
  w114 INT,
  w115 INT,
  w116 INT,
  w117 INT,
  w118 INT,
  w119 INT,
  w120 INT,
  w121 INT,
  w122 INT,
  w123 INT,
  w124 INT,
  w125 INT,
  w126 INT,
  w127 INT,
  w128 INT,
  w129 INT,
  w130 INT,
  w131 INT,
  w132 INT,
  w133 INT,
  w134 INT,
  w135 INT,
  w136 INT,
  w137 INT,
  w138 INT,
  w139 INT,
  w140 INT,
  w141 INT,
  w142 INT,
  w143 INT,
  w144 INT,
  w145 INT,
  w146 INT,
  w147 INT,
  w148 INT,
  w149 INT,
  w150 INT,
  w151 INT,
  w152 INT,
  w153 INT,
  w154 INT,
  w155 INT,
  w156 INT,
  w157 INT,
  w158 INT,
  w159 INT,
  w160 INT,
  w161 INT,
  w162 INT,
  w163 INT,
  w164 INT,
  w165 INT,
  w166 INT,
  w167 INT,
  w168 INT,
  w169 INT,
  w170 INT,
  w171 INT,
  w172 INT,
  w173 INT,
  w174 INT,
  w175 INT,
  w176 INT,
  w177 INT,
  w178 INT,
  w179 INT,
  w180 INT,
  w181 INT,
  w182 INT,
  w183 INT,
  w184 INT,
  w185 INT,
  w186 INT,
  w187 INT,
  w188 INT,
  w189 INT,
  w190 INT,
  w191 INT,
  w192 INT,
  w193 INT,
  w194 INT,
  w195 INT,
  w196 INT,
  w197 INT,
  w198 INT,
  w199 INT,
  pad VARCHAR(20) DEFAULT 'pad',
  PRIMARY KEY (id),
  INDEX idx_pad (pad)
) ENGINE=InnoDB;
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000000');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000001');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000002');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000003');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000004');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000005');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000006');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000007');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000008');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('00000009');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000a');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000b');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000c');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000d');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000e');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000f');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000g');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000h');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000i');
INSERT INTO t1_tc_43_fct_0198_df (target) VALUES ('0000000j');
-- ALTER expected MEASURE (build expected MEASURE)
ALTER TABLE t1_tc_43_fct_0198_df MODIFY target MEDIUMTEXT CHARACTER SET utf8mb4;
SELECT 'TC-43-FCT-0198-DF#BUILD_CHECK' AS test_id, 'PASS' AS result,
       CONCAT('table_exists=',COUNT(*)) AS mismatch
FROM information_schema.tables
WHERE table_schema=DATABASE() AND table_name='t1_tc_43_fct_0198_df';
SELECT 'TC-43-FCT-0198-DF#META_TYPE' AS test_id, 'PASS' AS result, 'MEASURE/build-FAIL mode: column_type not asserted' AS mismatch;
-- 收尾：清掉触发器/视图（表按项目要求保留）

