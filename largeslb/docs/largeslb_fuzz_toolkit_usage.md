# LargeSLB Fuzz 工具启动与结果说明

## 文件组成

- `largeslb_fuzz.py`：长稳 fuzz 主程序。
- `largeslb_console.py`：本地 Web 控制台，用于填写参数、启动/停止 fuzz、查看实时日志和异常定位。
- `requirements-largeslb-fuzz.txt`：运行依赖，目前只需要 `PyMySQL`。
- `test_largeslb_fuzz.py`、`test_largeslb_console.py`：本地单元测试。

## 安装依赖

```bash
cd "/Users/yuyu/Documents/New project 7"
python3 -m pip install -r requirements-largeslb-fuzz.txt
```

## 方式一：启动 Web 控制台

```bash
cd "/Users/yuyu/Documents/New project 7"
python3 largeslb_console.py --host 127.0.0.1 --port 8765
```

浏览器打开：

```text
http://127.0.0.1:8765
```

控制台页面可填写：

- `primary-dsn`：主库连接串，例如 `mysql://user:pass@primary-host:3306/testdb?charset=utf8mb4`
- `readonly-dsn`：只读副本连接串。
- `state-dir`：结果文件目录，默认 `/tmp/largeslb_fuzz_console`。
- `seed`：随机种子，可空。
- `run-id`：逻辑运行 ID，可空。
- `workers`：并发写入 worker 数。
- `duration`：运行时长，`0` 表示一直跑，也支持 `60s`、`30m`、`72h`、`7d`。
- `target-fields`：本轮覆盖的大字段列，默认包含 `char_255,varchar_16383,text_col,mediumtext_col,longtext_col,blob_col,mediumblob_col,longblob_col`。
- `engine-metric-interval`：采样 `large_mtr`、`large_mtr_size` 等状态项的间隔秒数，`0` 表示关闭。

控制台只负责传参、启动、停止、展示日志和失败，不校验数据库参数，也不把数据库重启本身判为失败。

## 方式二：命令行直接启动 fuzz

```bash
cd "/Users/yuyu/Documents/New project 7"
python3 -u largeslb_fuzz.py \
  --primary-dsn 'mysql://user:pass@primary-host:3306/testdb?charset=utf8mb4' \
  --readonly-dsn 'mysql://user:pass@readonly-host:3306/testdb?charset=utf8mb4' \
  --state-dir /tmp/largeslb_fuzz_run \
  --seed 20260525 \
  --workers 4 \
  --duration 72h \
  --target-fields 'char_255,varchar_16383,text_col,mediumtext_col,longtext_col,blob_col,mediumblob_col,longblob_col'
```

只初始化表和种子数据，不启动长稳 worker：

```bash
python3 -u largeslb_fuzz.py \
  --primary-dsn 'mysql://user:pass@primary-host:3306/testdb?charset=utf8mb4' \
  --readonly-dsn 'mysql://user:pass@readonly-host:3306/testdb?charset=utf8mb4' \
  --state-dir /tmp/largeslb_fuzz_run \
  --init-only
```

## 覆盖的数据类型

默认会覆盖这些字段更新：

- `CHAR(255)`：`char_255`
- `VARCHAR(16383)`：`varchar_16383`
- `TEXT`：`text_col`
- `MEDIUMTEXT`：`mediumtext_col`
- `LONGTEXT`：`longtext_col`
- `BLOB`：`blob_col`
- `MEDIUMBLOB`：`mediumblob_col`
- `LONGBLOB`：`longblob_col`

每个 fuzz 操作会记录 `target_field`、`payload_len`、`payload_sha`。主库和只读副本校验会按目标列计算 `OCTET_LENGTH(target_col)` 和 `SHA2(target_col, 256)`，用于发现内容损坏、长度错误、半事务可见和主只不一致。

默认不会执行“单条 redo record 自身超过 2MB”的不支持场景。

## 结果文件位置

所有结果都写入 `--state-dir` 指定的目录。控制台默认目录是：

```text
/tmp/largeslb_fuzz_console
```

命令行示例目录是：

```text
/tmp/largeslb_fuzz_run
```

目录结构：

```text
<state-dir>/
  run.log
  ops.jsonl
  oracle.jsonl
  metrics.csv
  engine_metrics.jsonl
  config_snapshot.json
  failures/
    <timestamp>_<failure-kind>/
      failure.json
      reproducer.sql
```

文件含义：

- `run.log`：程序运行日志、连接异常、重连、失败摘要。
- `ops.jsonl`：每个 fuzz 操作的计划、状态、涉及行、主库 signature。
- `oracle.jsonl`：Python 侧预期数据状态，用于重建每行最终版本、字段、长度和 hash。
- `metrics.csv`：每个操作的场景、目标字段、行数、payload 长度、耗时、校验耗时。
- `engine_metrics.jsonl`：best-effort 内核状态采样，包含可查询到的 `large_mtr`、`large_mtr_size`、`cv_lsn`、`persist_lsn` 等。
- `config_snapshot.json`：启动时可查询到的配置快照。查询失败不会影响 fuzz。
- `failures/`：异常现场目录。
- `failure.json`：异常类型、异常信息、`scenario`、`target_field`、`payload_len`、`op_id`、`row_id`、mismatch 字段、最近操作。
- `reproducer.sql`：尽量生成的复现 SQL。

## 异常定位方式

Web 控制台的“异常定位”区域会展示最新 failure，包括：

- 异常类型，例如 `primary_oracle_mismatch`、`readonly_half_visible`、`readonly_signature_mismatch`。
- 异常发生的 `scenario`。
- 异常字段 `target_field`。
- payload 长度 `payload_len`。
- 操作 ID `op_id`。
- 行 ID `row_id`。
- mismatch 字段，例如 `payload_sha`、`actual_payload_sha`、`actual_payload_len`。
- failure 目录路径。

如果不用控制台，也可以直接查看：

```bash
ls -ltr <state-dir>/failures
cat <state-dir>/failures/<timestamp>_<failure-kind>/failure.json
cat <state-dir>/failures/<timestamp>_<failure-kind>/reproducer.sql
```

## 本地验证

```bash
cd "/Users/yuyu/Documents/New project 7"
python3 -m unittest test_largeslb_fuzz.py test_largeslb_console.py
python3 -m py_compile largeslb_fuzz.py largeslb_console.py test_largeslb_fuzz.py test_largeslb_console.py
```
